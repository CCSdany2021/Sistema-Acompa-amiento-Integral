from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import ListView
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db import OperationalError
from django.urls import reverse
from django.http import Http404
from django.utils import timezone
from urllib.parse import urlencode
from django.db.models import Prefetch
from acompanamiento.models import Student, Report, ReportPurpose, ReportStatus, PeriodoAcademico
from acompanamiento.permissions import (
    filter_reports_for_user, resolve_viewer, resolve_real_user, has_global_access, sees_global_indicators,
    SECTION_NAME_TO_STUDENT_SECTION, SECTION_KEY_COURSES,
)


INSTITUTIONAL_STRUCTURE = [
    {"name": "Jardín–Tercero", "key": "preescolar", "courses": SECTION_KEY_COURSES['preescolar']},
    {"name": "Cuarto–Séptimo", "key": "basica_primaria", "courses": SECTION_KEY_COURSES['basica_primaria']},
    {"name": "Octavo–Undécimo", "key": "basica_secundaria", "courses": SECTION_KEY_COURSES['basica_secundaria']},
]


class StudentListView(ListView):
    model = Student
    template_name = 'estudiantes/student_list.html'
    context_object_name = 'students'
    paginate_by = 50

    def get_queryset(self):
        viewer = resolve_viewer(self.request)

        report_qs = filter_reports_for_user(
            Report.objects
            .select_related('assigned_to', 'created_by')
            .prefetch_related('observations', 'recommendations'),
            viewer
        )

        queryset = (
            Student.objects
            .select_related("course", "course__section")
            .prefetch_related(Prefetch("reports", queryset=report_qs))
            .order_by("full_name")
        )

        selected_course = (self.request.GET.get("course") or "").strip()
        selected_section = (self.request.GET.get("section") or "").strip()

        if selected_course:
            # El código de curso ya identifica al estudiante sin ambigüedad; no
            # se exige además que coincida section, porque el campo Student.section
            # (sincronizado del sistema externo) no siempre coincide con la
            # agrupación institucional del SAI para el mismo curso (ver JR01-302).
            queryset = queryset.filter(
                Q(course__name__iexact=selected_course) | Q(section__iexact=selected_course)
            )
        elif selected_section:
            section_values = SECTION_NAME_TO_STUDENT_SECTION.get(selected_section, [selected_section])
            queryset = queryset.filter(
                Q(course__section__name__in=section_values) | Q(section__in=section_values)
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

        # El remitente siempre es el usuario realmente logueado, nunca un valor enviado por el cliente.
        actor_user = self._resolve_actor_user()
        if not actor_user:
            messages.error(
                request,
                "No hay usuarios disponibles para registrar el reporte. Crea un usuario en /admin/ primero."
            )
            return redirect(self._build_redirect_url())

        # Validar assigned_to: debe ser usuario activo con perfil Educador válido
        assigned_to = None
        if assigned_to_id:
            from acompanamiento.models import Educador
            try:
                assigned_user = get_user_model().objects.get(pk=assigned_to_id, is_active=True)
                # Verificar que el usuario tenga perfil Educador y esté activo
                educador = Educador.objects.filter(user=assigned_user, is_active=True).first()
                if educador:
                    assigned_to = assigned_user
                else:
                    messages.warning(
                        request,
                        f"El usuario seleccionado no tiene un perfil de Educador activo. "
                        f"Se asignará a {actor_user.get_full_name()}."
                    )
            except get_user_model().DoesNotExist:
                messages.warning(
                    request,
                    "El usuario seleccionado no existe o no está activo. "
                    f"Se asignará a {actor_user.get_full_name()}."
                )

        # Si no hay assigned_to válido, asignar al actor_user
        if not assigned_to:
            assigned_to = actor_user

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
            academic_period=PeriodoAcademico.get_periodo_actual(),
            created_by=actor_user,
            assigned_to=assigned_to,
            institucional_quien_atiende=(request.POST.get("institucional_quien_atiende") or "").strip(),
        )

        # Enviar notificación por correo al asignado
        from acompanamiento.email_notifications import notify_report_assigned
        notify_report_assigned(report)

        messages.success(request, f"Reporte creado para {student.full_name} y asignado a {assigned_to.get_full_name()}.")
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

        if action in ("add_observation", "add_recommendation") and report.status == "ATENDIDO":
            messages.error(
                self.request,
                "Este caso ya fue atendido. No se pueden agregar más observaciones ni recomendaciones — solo se puede ver el historial."
            )
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
                "academic_period": PeriodoAcademico.get_periodo_actual(),
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
                "academic_period": PeriodoAcademico.get_periodo_actual(),
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
        viewer = resolve_viewer(self.request)
        context["sections_menu"] = INSTITUTIONAL_STRUCTURE
        context["selected_course"] = (self.request.GET.get("course") or "").strip()
        context["selected_section"] = (self.request.GET.get("section") or "").strip()
        context["students_count"] = self.get_queryset().count()
        context["report_purposes"] = list(ReportPurpose.choices)
        context["current_user"] = viewer
        context["viewer_is_global"] = has_global_access(viewer)
        context["can_export_ficha"] = sees_global_indicators(viewer)
        context["periodo_actual"] = PeriodoAcademico.get_periodo_actual()
        # Educadores con sus fines para filtrado dinámico en el modal
        # Incluir TODOS los educadores (activos e inactivos) que tengan perfil configurado
        from acompanamiento.models import Educador
        import json
        educadores = (
            Educador.objects
            .select_related('user')
            .filter(is_active=True)  # Solo mostrar educadores ACTIVOS en el desplegable
            .order_by('user__first_name', 'user__last_name')
        )
        staff_users = []
        educadores_json = []
        for ed in educadores:
            # Validar que el usuario también esté activo
            if ed.user.is_active:
                staff_users.append(ed.user)
                educadores_json.append({
                    'id': ed.user.id,
                    'nombre': ed.user.get_full_name() or ed.user.username,
                    'email': ed.user.email,
                    'fines': ed.fines_educativos,
                    'active': True,
                })
        context["staff_users"] = staff_users
        context["educadores_json"] = json.dumps(educadores_json)
        context["real_user"] = resolve_real_user(self.request)
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


def ficha_estudiante_view(request, student_id):
    """Ficha imprimible con el historial completo de acompañamiento de un estudiante.
    Solo CAP, mrodriguez y dhiguera pueden generarla (mismos permisos que indicadores globales)."""
    viewer = resolve_viewer(request)
    if not sees_global_indicators(viewer):
        raise Http404()

    student = get_object_or_404(Student, pk=student_id)

    reports = (
        Report.objects
        .filter(student=student)
        .select_related('created_by', 'assigned_to')
        .prefetch_related('observations__created_by', 'recommendations__created_by')
        .order_by('created_at')
    )

    eventos = []
    for r in reports:
        eventos.append({
            'fecha': r.created_at,
            'tipo': 'Apertura de caso',
            'fin': r.get_purpose_display(),
            'quien': (r.created_by.get_full_name() if r.created_by else '') or r.institucional_quien_atiende or '—',
            'detalle': r.objective or '—',
            'estado': r.get_status_display(),
            'periodo': r.academic_period or '—',
        })
        for obs in r.observations.all():
            eventos.append({
                'fecha': obs.date_log,
                'tipo': 'Observación',
                'fin': r.get_purpose_display(),
                'quien': (obs.created_by.get_full_name() if obs.created_by else '') or obs.correo_institucional or '—',
                'detalle': obs.content,
                'estado': r.get_status_display(),
                'periodo': obs.academic_period or '—',
            })
        for rec in r.recommendations.all():
            eventos.append({
                'fecha': rec.date_log,
                'tipo': 'Recomendación',
                'fin': r.get_purpose_display(),
                'quien': (rec.created_by.get_full_name() if rec.created_by else '') or rec.correo_institucional or '—',
                'detalle': rec.content,
                'estado': r.get_status_display(),
                'periodo': rec.academic_period or '—',
            })
        if r.fecha_cierre:
            eventos.append({
                'fecha': r.fecha_cierre,
                'tipo': 'Cierre de caso',
                'fin': r.get_purpose_display(),
                'quien': (r.assigned_to.get_full_name() if r.assigned_to else '') or '—',
                'detalle': 'Caso cumplido' if r.cumple_acompanamiento else 'Caso cerrado sin cumplimiento',
                'estado': r.get_status_display(),
                'periodo': r.academic_period or '—',
            })

    eventos.sort(key=lambda e: e['fecha'])

    return render(request, 'acompanamiento/ficha_estudiante.html', {
        'student': student,
        'eventos': eventos,
        'total_casos': reports.count(),
        'generado_en': timezone.now(),
        'generado_por': viewer,
    })
