from django.shortcuts import redirect
from django.views.generic import ListView
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db import OperationalError
from django.urls import reverse
from urllib.parse import urlencode
from acompanamiento.models import Student, Report, ReportPurpose, ReportStatus


INSTITUTIONAL_STRUCTURE = [
    {
        "name": "Jardín–Tercero",
        "key": "preescolar",
        "courses": ["JR01", "TR01", "TR02", "101", "102", "201", "202", "301", "302"],
    },
    {
        "name": "Cuarto–Séptimo",
        "key": "basica_primaria",
        "courses": ["401", "402", "501", "502", "503", "601", "602", "603", "701", "702", "703"],
    },
    {
        "name": "Octavo–Undécimo",
        "key": "basica_secundaria",
        "courses": ["801", "802", "803", "901", "902", "903", "1001", "1002", "1003", "1101", "1102", "1103"],
    },
]


class StudentListView(ListView):
    model = Student
    template_name = 'estudiantes/student_list.html'
    context_object_name = 'students'
    paginate_by = 50

    def get_queryset(self):
        queryset = (
            Student.objects
            .select_related("course", "course__section")
            .prefetch_related("reports__observations", "reports__recommendations")
            .order_by("full_name")
        )
        selected_course = (self.request.GET.get("course") or "").strip()
        selected_section = (self.request.GET.get("section") or "").strip()

        if selected_course:
            queryset = queryset.filter(
                Q(course__name__iexact=selected_course) | Q(section__iexact=selected_course)
            )

        if selected_section:
            queryset = queryset.filter(
                Q(course__section__name__iexact=selected_section) | Q(section__iexact=selected_section)
            )

        return queryset

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "create_report").strip()
        if action in {"add_observation", "add_recommendation", "close_report"}:
            return self._handle_report_actions(action)

        student_id = request.POST.get("student_id")
        objective = (request.POST.get("objective") or "").strip()
        purpose = (request.POST.get("purpose") or "").strip()
        fines_educativos = request.POST.getlist("fines_educativos")
        assigned_to_id = request.POST.get("assigned_to")

        if not student_id or not objective or not purpose:
            messages.error(request, "Debes completar estudiante, fin educativo y objetivo.")
            return redirect(self._build_redirect_url())

        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            messages.error(request, "No se encontró el estudiante seleccionado.")
            return redirect(self._build_redirect_url())

        remite_user_id = request.POST.get("remite_user_id")
        actor_user = None
        if remite_user_id:
            actor_user = get_user_model().objects.filter(pk=remite_user_id, is_active=True).first()
        if not actor_user:
            actor_user = self._resolve_actor_user()
        if not actor_user:
            messages.error(
                request,
                "No hay usuarios disponibles para registrar el reporte. Crea un usuario en /admin/ primero."
            )
            return redirect(self._build_redirect_url())

        assigned_to = None
        if assigned_to_id:
            assigned_to = get_user_model().objects.filter(pk=assigned_to_id).first()

        # Validar: el estudiante no puede tener dos acompañamientos activos del mismo fin educativo
        duplicate = Report.objects.filter(
            student=student,
            purpose=purpose,
        ).exclude(status=ReportStatus.ATENDIDO).first()
        if duplicate:
            purpose_label = dict(ReportPurpose.choices).get(purpose, purpose)
            messages.error(
                request,
                f"{student.full_name} ya tiene un acompañamiento activo de '{purpose_label}'. "
                "Ciérralo o cámbialo a ATENDIDO antes de crear uno nuevo del mismo fin."
            )
            return redirect(self._build_redirect_url())

        report = Report.objects.create(
            student=student,
            purpose=purpose,
            fines_educativos=fines_educativos or [purpose],
            status=ReportStatus.PROGRAMADO,
            objective=objective,
            academic_period=(request.POST.get("academic_period") or "").strip(),
            created_by=actor_user,
            assigned_to=assigned_to or actor_user,
            institucional_quien_atiende=(request.POST.get("institucional_quien_atiende") or "").strip(),
        )

        # Enviar notificación por correo al asignado
        from acompanamiento.email_notifications import notify_report_assigned
        notify_report_assigned(report)

        messages.success(request, f"Reporte creado para {student.full_name}.")
        return redirect(self._build_redirect_url())

    def _handle_report_actions(self, action):
        report_id = self.request.POST.get("report_id")
        if not report_id:
            messages.error(self.request, "No se recibió el reporte a actualizar.")
            return redirect(self._build_redirect_url())

        report = Report.objects.filter(pk=report_id).first()
        if not report:
            messages.error(self.request, "Reporte no encontrado.")
            return redirect(self._build_redirect_url())

        actor_user = self._resolve_actor_user()
        if not actor_user:
            messages.error(self.request, "No hay usuario disponible para registrar la acción.")
            return redirect(self._build_redirect_url())

        if action == "add_observation":
            content = (self.request.POST.get("observation_content") or "").strip()
            followup_date = (self.request.POST.get("observation_followup_date") or "").strip() or None
            if not content:
                messages.error(self.request, "La observación no puede quedar vacía.")
                return redirect(self._build_redirect_url())
            base_data = {
                "content": content,
                "title": (self.request.POST.get("observation_title") or "").strip(),
                "created_by": actor_user,
                "correo_institucional": (self.request.POST.get("correo_institucional") or actor_user.email or "").strip(),
                "fin_educativo": report.purpose,
            }
            try:
                report.observations.create(**base_data, followup_date=followup_date)
            except OperationalError:
                # Fallback defensivo cuando la BD activa está desincronizada.
                report.observations.create(**base_data)
                messages.warning(
                    self.request,
                    "Se guardó la observación sin fecha de seguimiento. Ejecuta migraciones para sincronizar la base de datos activa."
                )
            messages.success(self.request, "Observación registrada correctamente.")

        elif action == "add_recommendation":
            content = (self.request.POST.get("recommendation_content") or "").strip()
            followup_date = (self.request.POST.get("recommendation_followup_date") or "").strip() or None
            if not content:
                messages.error(self.request, "La recomendación no puede quedar vacía.")
                return redirect(self._build_redirect_url())
            base_data = {
                "content": content,
                "created_by": actor_user,
                "correo_institucional": (self.request.POST.get("correo_institucional") or actor_user.email or "").strip(),
                "fin_educativo": report.purpose,
            }
            try:
                rec = report.recommendations.create(**base_data, followup_date=followup_date)
            except OperationalError:
                rec = report.recommendations.create(**base_data)
                messages.warning(
                    self.request,
                    "Se guardó la recomendación sin fecha de seguimiento. Ejecuta migraciones para sincronizar la base de datos activa."
                )
            # Notificar a los docentes del curso
            from acompanamiento.email_notifications import notify_recommendation_to_teachers
            notify_recommendation_to_teachers(rec)
            messages.success(self.request, "Recomendación registrada correctamente.")

        elif action == "close_report":
            close_status = (self.request.POST.get("close_status") or "").strip()
            cumple = (self.request.POST.get("cumple_acompanamiento") or "").strip()
            
            if close_status:
                report.status = close_status
            
            if cumple:
                report.cumple_acompanamiento = True if cumple == "true" else False
            
            if close_status == ReportStatus.ATENDIDO:
                from django.utils import timezone
                report.fecha_cierre = timezone.now()
            
            report.is_accomplished = True
            report.save()
            
            estado_texto = dict(ReportStatus.choices).get(close_status, close_status) if close_status else "Atendido"
            messages.success(self.request, f"Caso cerrado correctamente. Estado: {estado_texto}")

        return redirect(self._build_redirect_url())

    def _resolve_actor_user(self):
        if getattr(self.request, "user", None) and self.request.user.is_authenticated:
            return self.request.user

        user_model = get_user_model()
        return (
            user_model.objects.filter(is_superuser=True, is_active=True).first()
            or user_model.objects.filter(is_staff=True, is_active=True).first()
            or user_model.objects.filter(is_active=True).first()
        )

    def _build_redirect_url(self):
        params = {}
        if self.request.GET.get("section"):
            params["section"] = self.request.GET.get("section")
        if self.request.GET.get("course"):
            params["course"] = self.request.GET.get("course")
        query = f"?{urlencode(params)}" if params else ""
        return f"{reverse('estudiantes:list')}{query}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sections_menu"] = INSTITUTIONAL_STRUCTURE
        context["selected_course"] = (self.request.GET.get("course") or "").strip()
        context["selected_section"] = (self.request.GET.get("section") or "").strip()
        context["students_count"] = self.get_queryset().count()
        context["report_purposes"] = list(ReportPurpose.choices)
        # Educadores activos con sus fines para filtrado dinámico en el modal
        from acompanamiento.models import Educador
        import json
        educadores = Educador.objects.filter(is_active=True).select_related('user')
        staff_users = []
        educadores_json = []
        for ed in educadores:
            staff_users.append(ed.user)
            educadores_json.append({
                'id': ed.user.id,
                'nombre': ed.user.get_full_name() or ed.user.username,
                'fines': ed.fines_educativos,
            })
        context["staff_users"] = staff_users
        context["educadores_json"] = json.dumps(educadores_json)
        context["cuarto_septimo_courses"] = [
            {'code': '401', 'section': 'basica_primaria'},
            {'code': '402', 'section': 'basica_primaria'},
            {'code': '501', 'section': 'basica_primaria'},
            {'code': '502', 'section': 'basica_primaria'},
            {'code': '503', 'section': 'basica_primaria'},
            {'code': '601', 'section': 'basica_secundaria'},
            {'code': '602', 'section': 'basica_secundaria'},
            {'code': '603', 'section': 'basica_secundaria'},
            {'code': '701', 'section': 'basica_secundaria'},
            {'code': '702', 'section': 'basica_secundaria'},
            {'code': '703', 'section': 'basica_secundaria'},
        ]
        context["octavo_once_courses"] = [
            {'code': '801',  'section': 'basica_secundaria'},
            {'code': '802',  'section': 'basica_secundaria'},
            {'code': '803',  'section': 'basica_secundaria'},
            {'code': '901',  'section': 'basica_secundaria'},
            {'code': '902',  'section': 'basica_secundaria'},
            {'code': '903',  'section': 'basica_secundaria'},
            {'code': '1001', 'section': 'basica_secundaria'},
            {'code': '1002', 'section': 'basica_secundaria'},
            {'code': '1003', 'section': 'basica_secundaria'},
            {'code': '1101', 'section': 'basica_secundaria'},
            {'code': '1102', 'section': 'basica_secundaria'},
            {'code': '1103', 'section': 'basica_secundaria'},
        ]
        return context

def sync_students(request):
    count = Student.sync_from_api()
    messages.success(request, f'[OK] {count} estudiantes sincronizados desde API')
    return redirect('estudiantes:list')
