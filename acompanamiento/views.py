from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Section, Course, Student, Report, Observation, Recommendation, Educador, UserRole, ReportStatus, ReportPurpose, AtencionHistorial
from .serializers import (
    SectionSerializer, CourseSerializer, StudentSerializer,
    ReportListSerializer, ReportDetailSerializer, ReportCreateUpdateSerializer,
    ObservationSerializer, RecommendationSerializer, UserSerializer, EducadorSerializer
)


# ============================================================================
# VISTAS DJANGO ORIGINALES (para templates HTML)
# ============================================================================

class ReportListView(ListView):
    model = Report
    template_name = 'acompanamiento/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        from .permissions import filter_reports_for_user, resolve_viewer
        viewer = resolve_viewer(self.request)
        queryset = filter_reports_for_user(
            super().get_queryset().select_related('student', 'assigned_to', 'created_by'),
            viewer
        )

        search        = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        purpose_filter= self.request.GET.get('purpose', '')
        period_filter = self.request.GET.get('period', '')
        seccion_filter= self.request.GET.get('grado', '')
        assigned_to_filter = self.request.GET.get('assigned_to', '')

        if search:
            queryset = queryset.filter(
                Q(student__full_name__icontains=search) |
                Q(student__code__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if purpose_filter:
            queryset = queryset.filter(purpose=purpose_filter)
        if period_filter:
            queryset = queryset.filter(academic_period=period_filter)
        if seccion_filter:
            if seccion_filter == 'basica_secundaria':
                queryset = queryset.filter(student__section__in=['basica_secundaria', 'media_academica'])
            else:
                queryset = queryset.filter(student__section=seccion_filter)
        if assigned_to_filter:
            queryset = queryset.filter(assigned_to_id=assigned_to_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .permissions import resolve_viewer, get_allowed_fines, get_viewer_sections, filter_reports_for_user
        from django.contrib.auth import get_user_model

        viewer = resolve_viewer(self.request)

        # Educadores con "Quien atendió": solo los que aparecen dentro de lo que el viewer puede ver
        visible_qs = filter_reports_for_user(Report.objects.all(), viewer)
        educator_ids = visible_qs.exclude(assigned_to=None).values_list('assigned_to_id', flat=True).distinct()
        context['educators_filter'] = (
            get_user_model().objects.filter(pk__in=educator_ids).order_by('first_name', 'last_name')
        )

        # Fins: solo mostrar los que el viewer puede ver
        all_purposes = list(ReportPurpose.choices)
        allowed_fines = get_allowed_fines(viewer)
        if allowed_fines:  # lista no vacía → filtrar
            context['purpose_choices'] = [(k, l) for k, l in all_purposes if k in allowed_fines]
        else:
            context['purpose_choices'] = all_purposes  # None o [] → todos

        # Secciones: solo mostrar las que el viewer puede ver
        all_secciones = [
            ('preescolar',       'Jardín – Tercero'),
            ('basica_primaria',  'Cuarto – Séptimo'),
            ('basica_secundaria','Octavo – Undécimo'),
        ]
        viewer_secs = get_viewer_sections(viewer)
        if viewer_secs:  # lista no vacía → filtrar
            visible = set(viewer_secs)
            if 'media_academica' in visible:
                visible.add('basica_secundaria')
            context['seccion_choices'] = [(k, l) for k, l in all_secciones if k in visible]
        else:
            context['seccion_choices'] = all_secciones  # None o [] → todas

        context['status_choices'] = ReportStatus.choices
        context['periodos'] = (Report.objects
                                .exclude(academic_period='')
                                .values_list('academic_period', flat=True)
                                .distinct()
                                .order_by('academic_period'))
        return context

class ReportCreateView(CreateView):
    model = Report
    template_name = 'acompanamiento/report_form.html'
    fields = ['student', 'purpose', 'objective', 'status', 'academic_period']
    success_url = reverse_lazy('acompanamiento:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class ReportDetailView(DetailView):
    model = Report
    template_name = 'acompanamiento/report_detail.html'

    def get_context_data(self, **kwargs):
        from .permissions import resolve_viewer, can_manage_report, resolve_real_user
        context = super().get_context_data(**kwargs)
        report  = self.object
        viewer  = resolve_viewer(self.request)
        real_user = resolve_real_user(self.request)
        context['viewer']       = viewer
        context['can_edit_all'] = can_manage_report(viewer, report) and not report.is_closed
        context['can_reopen']   = can_manage_report(real_user, report) and report.is_closed
        context['historial']    = report.historial_atenciones.select_related('atendido_por', 'reabierto_por').all()
        # Selector de educadores para modal de reapertura
        from django.contrib.auth import get_user_model
        User = get_user_model()
        context['educadores_select'] = (
            User.objects.filter(educador__isnull=False, is_active=True)
            .exclude(email='cap@calasanzsuba.edu.co')
            .order_by('first_name', 'last_name')
        )
        return context

def _calc_indicadores(qs):
    """Calcula indicadores de eficiencia y eficacia sobre un QuerySet de Report."""
    from django.db.models import Count
    total     = qs.count()
    atendidos = qs.filter(status='ATENDIDO').count()
    eficiencia = round(atendidos * 100 / total, 1) if total else 0

    eficacia_num = qs.filter(status='ATENDIDO', cumple_acompanamiento=True).count()
    eficacia     = round(eficacia_num * 100 / atendidos, 1) if atendidos else 0

    FINES = ['ACADEMICO', 'PSICOAFECTIVO', 'ESPIRITUAL', 'CONVIVENCIA']
    FINES_L = {'ACADEMICO': 'Académico', 'PSICOAFECTIVO': 'Psicoafectivo',
               'ESPIRITUAL': 'Espiritual', 'CONVIVENCIA': 'Convivencia'}
    # 3 secciones institucionales — basica_secundaria agrupa también media_academica
    SEC_GROUPS = [
        ('preescolar',        'Jardín–Tercero',    ['preescolar']),
        ('basica_primaria',   'Cuarto–Séptimo',    ['basica_primaria']),
        ('basica_secundaria', 'Octavo–Undécimo',   ['basica_secundaria', 'media_academica']),
    ]

    # Desglose por fin educativo
    por_fin = []
    for f in FINES:
        fqs  = qs.filter(purpose=f)
        ftot = fqs.count()
        fate = fqs.filter(status='ATENDIDO').count()
        fef  = fqs.filter(status='ATENDIDO', cumple_acompanamiento=True).count()
        por_fin.append({
            'fin': FINES_L[f], 'key': f,
            'total': ftot,
            'atendidos': fate,
            'eficiencia': round(fate * 100 / ftot, 1) if ftot else 0,
            'eficacia_num': fef,
            'eficacia': round(fef * 100 / fate, 1) if fate else 0,
        })

    # Desglose por sección
    por_seccion = []
    for key, label, sec_keys in SEC_GROUPS:
        sqs  = qs.filter(student__section__in=sec_keys)
        stot = sqs.count()
        sate = sqs.filter(status='ATENDIDO').count()
        sef  = sqs.filter(status='ATENDIDO', cumple_acompanamiento=True).count()
        if stot > 0:
            por_seccion.append({
                'seccion': label,
                'total': stot,
                'atendidos': sate,
                'eficiencia': round(sate * 100 / stot, 1) if stot else 0,
                'eficacia_num': sef,
                'eficacia': round(sef * 100 / sate, 1) if sate else 0,
            })

    return {
        'total': total, 'atendidos': atendidos,
        'eficiencia': eficiencia, 'cumple_ef': eficiencia >= 80,
        'eficacia_num': eficacia_num, 'eficacia': eficacia, 'cumple_ec': eficacia >= 80,
        'por_fin': por_fin, 'por_seccion': por_seccion,
    }


_ALL_FINES = [
    ('ACADEMICO', 'Académico'), ('PSICOAFECTIVO', 'Psicoafectivo'),
    ('ESPIRITUAL', 'Espiritual'), ('CONVIVENCIA', 'Convivencia'),
]
_ALL_SECCIONES = [
    ('preescolar',        'Jardín–Tercero'),
    ('basica_primaria',   'Cuarto–Séptimo'),
    ('basica_secundaria', 'Octavo–Undécimo'),
]

def _build_fin_choices(viewer):
    from .permissions import get_allowed_fines
    allowed = get_allowed_fines(viewer)
    if allowed:  # lista no vacía → filtrar
        return [(k, l) for k, l in _ALL_FINES if k in allowed]
    return _ALL_FINES  # None o [] → todos

def _build_seccion_choices(viewer):
    from .permissions import get_viewer_sections
    secs = get_viewer_sections(viewer)
    if secs:  # lista no vacía → filtrar
        visible = set(secs)
        if 'media_academica' in visible:
            visible.add('basica_secundaria')
        return [(k, l) for k, l in _ALL_SECCIONES if k in visible]
    return _ALL_SECCIONES  # None o [] → todas


def indicadores_view(request):
    """Módulo de indicadores SGI — Eficiencia y Eficacia del acompañamiento."""
    from .permissions import resolve_viewer, sees_global_indicators, filter_reports_for_user, get_allowed_fines, get_viewer_sections

    viewer = resolve_viewer(request)
    es_global = sees_global_indicators(viewer)

    # Filtros GET
    periodo  = request.GET.get('periodo', '')
    seccion  = request.GET.get('seccion', '')
    fin      = request.GET.get('fin', '')
    anio     = request.GET.get('anio', '2026')

    anio_int = int(anio) if anio.isdigit() else 2026
    base_qs  = Report.objects.filter(year=anio_int)

    # Educadores no-globales ven solo sus reportes asignados
    if not es_global:
        base_qs = base_qs.filter(assigned_to=viewer)

    qs = base_qs
    if periodo:
        qs = qs.filter(academic_period=periodo)
    if seccion:
        if seccion == 'basica_secundaria':
            qs = qs.filter(student__section__in=['basica_secundaria', 'media_academica'])
        else:
            qs = qs.filter(student__section__iexact=seccion)
    if fin:
        qs = qs.filter(purpose=fin)

    periodos_disponibles = (base_qs
                            .exclude(academic_period='')
                            .values_list('academic_period', flat=True)
                            .distinct().order_by('academic_period'))

    stats = _calc_indicadores(qs)

    return render(request, 'acompanamiento/indicadores.html', {
        'stats':      stats,
        'periodo':    periodo,
        'seccion':    seccion,
        'fin':        fin,
        'anio':       anio,
        'es_global':  es_global,
        'viewer':     viewer,
        'periodos':   list(periodos_disponibles),
        'secciones':  _build_seccion_choices(viewer),
        'fines':      _build_fin_choices(viewer),
    })


def informe_acompanamiento_view(request):
    """Informe ejecutivo imprimible de acompañamiento integral (2 páginas, estilo SGI)."""
    from django.db.models import Count, Q
    from django.db.models.functions import TruncMonth
    from django.utils import timezone

    anio    = request.GET.get('anio', '2026')
    periodo = request.GET.get('periodo', '')
    seccion = request.GET.get('seccion', '')
    fin     = request.GET.get('fin', '')

    qs = Report.objects.filter(year=int(anio) if anio.isdigit() else 2026)
    if periodo: qs = qs.filter(academic_period=periodo)
    if seccion: qs = qs.filter(student__section__iexact=seccion)
    if fin:     qs = qs.filter(purpose=fin)

    stats = _calc_indicadores(qs)
    total = stats['total']

    FINES_COLORS = {
        'ACADEMICO':    '#2563eb',
        'CONVIVENCIA':  '#f59e0b',
        'ESPIRITUAL':   '#7c3aed',
        'PSICOAFECTIVO':'#db2777',
    }

    # Distribución por fin con %
    por_fin_dist = []
    for row in stats['por_fin']:
        pct = round(row['total'] * 100 / total, 1) if total else 0
        por_fin_dist.append({**row, 'pct': pct, 'color': FINES_COLORS.get(row['key'], '#64748b')})

    # Estado de casos
    seg = qs.filter(status='SEGUIMIENTO').count()
    pro = qs.filter(status='PROGRAMADO').count()
    estados = [
        {'label': 'Atendidos',       'valor': stats['atendidos'], 'pct': stats['eficiencia'], 'color': '#16a34a'},
        {'label': 'En Seguimiento',  'valor': seg, 'pct': round(seg*100/total,1) if total else 0, 'color': '#d97706'},
        {'label': 'Programados',     'valor': pro, 'pct': round(pro*100/total,1) if total else 0, 'color': '#dc2626'},
    ]

    # Top 5 educadores
    top_q = (qs.filter(assigned_to__isnull=False)
               .values('assigned_to__first_name','assigned_to__last_name','assigned_to__email')
               .annotate(total=Count('id'), atendidos=Count('id', filter=Q(status='ATENDIDO')))
               .order_by('-total')[:5])
    top_eds = []
    for i, ed in enumerate(top_q):
        nombre = f"{ed['assigned_to__first_name']} {ed['assigned_to__last_name']}".strip()
        fines_ed = sorted(set(qs.filter(
            assigned_to__first_name=ed['assigned_to__first_name'],
            assigned_to__last_name=ed['assigned_to__last_name']
        ).values_list('purpose', flat=True)))
        top_eds.append({
            'rank': i + 1, 'nombre': nombre or ed['assigned_to__email'] or '-',
            'total': ed['total'], 'atendidos': ed['atendidos'], 'fines': fines_ed,
        })

    # Tendencia mensual con desglose por fin (con alturas precomputadas)
    MESES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    monthly_raw = (qs.annotate(mes=TruncMonth('created_at'))
                     .values('mes')
                     .annotate(total=Count('id'),
                               academico=Count('id', filter=Q(purpose='ACADEMICO')),
                               convivencia=Count('id', filter=Q(purpose='CONVIVENCIA')),
                               espiritual=Count('id', filter=Q(purpose='ESPIRITUAL')),
                               psicoafectivo=Count('id', filter=Q(purpose='PSICOAFECTIVO')))
                     .order_by('mes'))
    monthly_max = max((m['total'] for m in monthly_raw if m['mes']), default=1)
    monthly = []
    for m in monthly_raw:
        if not m['mes']:
            continue
        def _h(v, mx=monthly_max): return round(v * 76 / mx) if mx else 0
        h_ac = _h(m['academico'])
        h_co = _h(m['convivencia'])
        h_es = _h(m['espiritual'])
        h_ps = _h(m['psicoafectivo'])
        monthly.append({
            'mes': MESES[m['mes'].month - 1],
            'total': m['total'],
            'academico': m['academico'],
            'convivencia': m['convivencia'],
            'espiritual': m['espiritual'],
            'psicoafectivo': m['psicoafectivo'],
            'h_ac': h_ac,
            'h_co': h_co,
            'h_es': h_es,
            'h_ps': h_ps,
            'h_total': h_ac + h_co + h_es + h_ps,
        })

    # Fines por período — para tabla detallada
    periodos_con_datos = list(
        qs.exclude(academic_period='')
          .values_list('academic_period', flat=True)
          .distinct().order_by('academic_period')
    )
    por_periodo_fin = []
    per_fin_max = 1
    for p in periodos_con_datos:
        qs_p = qs.filter(academic_period=p)
        tot = qs_p.count()
        ac = qs_p.filter(purpose='ACADEMICO').count()
        ps = qs_p.filter(purpose='PSICOAFECTIVO').count()
        es = qs_p.filter(purpose='ESPIRITUAL').count()
        co = qs_p.filter(purpose='CONVIVENCIA').count()
        per_fin_max = max(per_fin_max, tot)
        por_periodo_fin.append({
            'periodo': p, 'total': tot,
            'academico': ac, 'psicoafectivo': ps, 'espiritual': es, 'convivencia': co,
            'pct_ac': round(ac * 100 / tot, 0) if tot else 0,
            'pct_ps': round(ps * 100 / tot, 0) if tot else 0,
            'pct_es': round(es * 100 / tot, 0) if tot else 0,
            'pct_co': round(co * 100 / tot, 0) if tot else 0,
        })

    # Fines por sección — para tabla detallada
    SEC_ITER = [
        ('preescolar',       'Jardín–Tercero',   ['preescolar']),
        ('basica_primaria',  'Cuarto–Séptimo',   ['basica_primaria']),
        ('basica_secundaria','Octavo–Undécimo',  ['basica_secundaria', 'media_academica']),
    ]
    por_seccion_fin = []
    sec_fin_max = 1
    for _key, label, svals in SEC_ITER:
        qs_s = qs.filter(student__section__in=svals)
        tot = qs_s.count()
        if tot == 0:
            continue
        ac = qs_s.filter(purpose='ACADEMICO').count()
        ps = qs_s.filter(purpose='PSICOAFECTIVO').count()
        es = qs_s.filter(purpose='ESPIRITUAL').count()
        co = qs_s.filter(purpose='CONVIVENCIA').count()
        sec_fin_max = max(sec_fin_max, tot)
        por_seccion_fin.append({
            'seccion': label, 'total': tot,
            'academico': ac, 'psicoafectivo': ps, 'espiritual': es, 'convivencia': co,
            'pct_ac': round(ac * 100 / tot, 0) if tot else 0,
            'pct_ps': round(ps * 100 / tot, 0) if tot else 0,
            'pct_es': round(es * 100 / tot, 0) if tot else 0,
            'pct_co': round(co * 100 / tot, 0) if tot else 0,
        })

    periodos = periodos_con_datos

    return render(request, 'acompanamiento/informe.html', {
        'stats': stats, 'por_fin_dist': por_fin_dist, 'estados': estados,
        'top_eds': top_eds, 'monthly': monthly, 'monthly_max': monthly_max,
        'por_periodo_fin': por_periodo_fin, 'per_fin_max': per_fin_max,
        'por_seccion_fin': por_seccion_fin, 'sec_fin_max': sec_fin_max,
        'anio': anio, 'periodo': periodo, 'seccion': seccion, 'fin': fin,
        'fecha': timezone.now(), 'periodos': periodos,
        'secciones': _ALL_SECCIONES,
        'fines':     _ALL_FINES,
    })


def simulator_view(request):
    """Pantalla del Simulador de Vistas — super-admin y coordinadoras habilitadas."""
    from .permissions import (
        resolve_real_user, can_simulate, get_simulator_allowed_sections,
        _educador_student_sections,
    )
    from django.contrib.auth import get_user_model

    real_user = resolve_real_user(request)
    if not can_simulate(real_user):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Acceso restringido al super-administrador.')

    User = get_user_model()
    # Todos los usuarios activos con perfil Educador
    educadores = (Educador.objects
                  .filter(is_active=True)
                  .select_related('user', 'seccion_asignada')
                  .prefetch_related('secciones', 'reglas')
                  .order_by('user__first_name', 'user__last_name'))

    # Usuarios sin perfil educador (admin/staff)
    educador_user_ids = educadores.values_list('user_id', flat=True)
    others = (User.objects
              .filter(is_active=True)
              .exclude(pk__in=educador_user_ids)
              .exclude(pk=real_user.pk)
              .order_by('first_name', 'last_name'))

    # Coordinadoras de sección (mpedraza, yalejo) solo ven en el simulador a los
    # usuarios asignados a su propia sección. El resto (mrodriguez, dhiguera,
    # pvasquez, cap) ve el listado completo.
    allowed_sections = get_simulator_allowed_sections(real_user)
    if allowed_sections is not None:
        allowed_set = set(allowed_sections)
        educadores = [ed for ed in educadores if _educador_student_sections(ed) & allowed_set]
        others = []

    current_sim_id = request.session.get('simulated_user_id')
    simulated_user = User.objects.filter(pk=current_sim_id).first() if current_sim_id else None

    # Calcular cuántos reportes ve cada usuario con sus permisos reales
    from .permissions import filter_reports_for_user
    all_reports = Report.objects.all()

    educadores_info = []
    for ed in educadores:
        ve  = filter_reports_for_user(all_reports, ed.user).count()
        asig = Report.objects.filter(assigned_to=ed.user).count()
        educadores_info.append({'ed': ed, 've': ve, 'asig': asig})

    others_info = []
    for u in others:
        ve  = filter_reports_for_user(all_reports, u).count()
        asig = Report.objects.filter(assigned_to=u).count()
        others_info.append({'user': u, 've': ve, 'asig': asig})

    return render(request, 'acompanamiento/simulator.html', {
        'educadores_info': educadores_info,
        'others_info':     others_info,
        'real_user':       real_user,
        'simulated_user':  simulated_user,
    })


@require_POST
def activate_simulation(request):
    """Activa la simulación para un usuario — super-admin y coordinadoras habilitadas."""
    from .permissions import resolve_real_user, can_simulate, can_simulate_target
    real_user = resolve_real_user(request)
    if not can_simulate(real_user):
        return JsonResponse({'error': 'Sin permiso'}, status=403)

    user_id = request.POST.get('user_id', '').strip()
    if not user_id:
        return JsonResponse({'error': 'user_id requerido'}, status=400)

    from django.contrib.auth import get_user_model
    User = get_user_model()
    target = User.objects.filter(pk=user_id, is_active=True).first()
    if not target:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    if not can_simulate_target(real_user, target):
        return JsonResponse({'error': 'No puedes simular a un usuario fuera de tu sección'}, status=403)

    request.session['simulated_user_id'] = int(user_id)
    request.session.modified = True
    return JsonResponse({
        'ok': True,
        'user': {
            'id': target.pk,
            'name': target.get_full_name() or target.username,
            'email': target.email,
        }
    })


@require_POST
def stop_simulation(request):
    """Detiene la simulación activa."""
    from .permissions import resolve_real_user, can_simulate
    real_user = resolve_real_user(request)
    if not can_simulate(real_user):
        return JsonResponse({'error': 'Sin permiso'}, status=403)

    request.session.pop('simulated_user_id', None)
    request.session.modified = True

    # Si es llamada vía JS (fetch/XHR), devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
       request.headers.get('Accept', '').startswith('application/json'):
        return JsonResponse({'ok': True})

    # Si es un form POST normal, redirigir al simulador
    return redirect('acompanamiento:simulator')


def admin_educadores_view(request):
    """Gestión de roles y permisos de educadores — SOLO CAP."""
    from .permissions import can_manage_educadores, resolve_real_user
    from django.contrib.auth import get_user_model
    from .models import ReglaPermiso, PeriodoAcademico

    real_user = resolve_real_user(request)
    if not can_manage_educadores(real_user):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Acceso restringido. Solo la cuenta CAP puede administrar educadores.')

    User = get_user_model()

    if request.method == 'POST':
        action  = request.POST.get('action', '')
        user_id = request.POST.get('user_id', '')

        if action == 'save_educador' and user_id:
            user = User.objects.filter(pk=user_id).first()
            if user:
                ed, _ = Educador.objects.get_or_create(user=user)
                ed.rol           = request.POST.get('rol', 'ADMIN_SECCION')
                ed.acceso_global = request.POST.get('acceso_global') == '1'
                ed.is_active     = request.POST.get('is_active') == '1'
                ed.fines_educativos = request.POST.getlist('fines_educativos')
                ed.save()
                sec_ids = request.POST.getlist('secciones')
                ed.secciones.set(Section.objects.filter(pk__in=sec_ids))
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'ok': True, 'msg': f'Perfil de {user.get_full_name()} actualizado.'})
                messages.success(request, f'Perfil de {user.get_full_name()} actualizado.')

        elif action == 'add_regla' and user_id:
            user = User.objects.filter(pk=user_id).first()
            if user:
                ed, _ = Educador.objects.get_or_create(user=user)
                # Soporte multi-fin y multi-sección: crear una regla por cada combinación
                fines    = request.POST.getlist('fin_educativo') or ['']
                secciones = request.POST.getlist('seccion') or ['']
                scope    = request.POST.get('scope', 'SOLO_ASIGNADO')
                created_count = 0
                for fin in fines:
                    for sec in secciones:
                        # Evitar duplicados
                        exists = ReglaPermiso.objects.filter(
                            educador=ed, fin_educativo=fin, seccion=sec, scope=scope
                        ).exists()
                        if not exists:
                            ReglaPermiso.objects.create(
                                educador=ed, fin_educativo=fin, seccion=sec, scope=scope
                            )
                            created_count += 1
                msg = f'{created_count} regla(s) agregada(s) a {user.get_full_name()}.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    reglas = list(ed.reglas.values('id', 'fin_educativo', 'seccion', 'scope'))
                    return JsonResponse({'ok': True, 'msg': msg, 'reglas': reglas})
                messages.success(request, msg)

        elif action == 'delete_regla':
            regla_id = request.POST.get('regla_id', '')
            ReglaPermiso.objects.filter(pk=regla_id).delete()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': True})
            messages.success(request, 'Regla eliminada.')

        elif action == 'reset_reglas' and user_id:
            # Eliminar todas las reglas de un educador y poner SOLO_ASIGNADO por defecto
            user = User.objects.filter(pk=user_id).first()
            if user:
                ed, _ = Educador.objects.get_or_create(user=user)
                ed.reglas.all().delete()
                ReglaPermiso.objects.create(educador=ed, fin_educativo='', seccion='', scope='SOLO_ASIGNADO')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'ok': True, 'msg': 'Reglas reseteadas a SOLO_ASIGNADO.'})
                messages.success(request, 'Reglas reseteadas.')

        elif action == 'save_periodos':
            errores = []
            for nombre, _ in PeriodoAcademico.NOMBRE_CHOICES:
                slug = nombre.lower().replace(' ', '_')
                inicio = request.POST.get(f'{slug}_inicio', '').strip()
                fin    = request.POST.get(f'{slug}_fin', '').strip()
                if not inicio or not fin:
                    errores.append(f'{nombre}: faltan fechas.')
                    continue
                if fin < inicio:
                    errores.append(f'{nombre}: la fecha fin no puede ser anterior al inicio.')
                    continue
                PeriodoAcademico.objects.update_or_create(
                    nombre=nombre, defaults={'fecha_inicio': inicio, 'fecha_fin': fin}
                )
            if errores:
                messages.error(request, 'No se guardaron algunos períodos: ' + ' '.join(errores))
            else:
                messages.success(request, 'Fechas de los períodos actualizadas correctamente.')

        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return redirect('acompanamiento:admin_educadores')

    # Lista de todos los usuarios con su perfil educador + reglas
    from .models import ReglaPermiso
    all_users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    educadores_data = []
    for u in all_users:
        try:
            ed = u.educador
            reglas = list(ed.reglas.all())
        except Exception:
            ed = None
            reglas = []
        educadores_data.append({'user': u, 'educador': ed, 'reglas': reglas})

    sections = Section.objects.all().order_by('name')
    fines = [
        ('ACADEMICO', 'Académico'), ('PSICOAFECTIVO', 'Psicoafectivo'),
        ('ESPIRITUAL', 'Espiritual'), ('CONVIVENCIA', 'Convivencia'),
    ]

    # Períodos académicos: 4 filas fijas, se crean vacías si aún no existen
    periodos_existentes = {p.nombre: p for p in PeriodoAcademico.objects.all()}
    periodos = []
    for nombre, _ in PeriodoAcademico.NOMBRE_CHOICES:
        p = periodos_existentes.get(nombre)
        periodos.append({
            'nombre': nombre,
            'slug': nombre.lower().replace(' ', '_'),
            'fecha_inicio': p.fecha_inicio if p else '',
            'fecha_fin': p.fecha_fin if p else '',
        })

    return render(request, 'acompanamiento/admin_educadores.html', {
        'educadores_data': educadores_data,
        'sections': sections,
        'fines': fines,
        'rol_choices': UserRole.choices,
        'periodos': periodos,
        'periodo_actual': PeriodoAcademico.get_periodo_actual(),
    })


def cerrar_report(request, pk):
    """Cierra un reporte (lo marca como ATENDIDO)."""
    from .permissions import resolve_real_user, can_manage_report
    real_user = resolve_real_user(request)
    report = get_object_or_404(Report, pk=pk)
    if not can_manage_report(real_user, report):
        messages.error(request, 'Sin permiso para cerrar reportes.')
        return redirect('acompanamiento:detail', pk=pk)

    if report.is_closed:
        messages.warning(request, 'El reporte ya está cerrado.')
        return redirect('acompanamiento:detail', pk=pk)

    cumple = request.POST.get('cumple_acompanamiento', 'false') in ('true', '1', 'on', 'si', 'yes')
    report.status                = ReportStatus.ATENDIDO
    report.is_accomplished       = cumple
    report.cumple_acompanamiento = cumple
    report.fecha_cierre          = timezone.now()
    report.save()

    _log_auditoria(report, 'CERRAR', real_user, detalle=f"Cumple acompañamiento: {'Sí' if cumple else 'No'}")
    messages.success(request, f'Reporte de {report.student.full_name} cerrado correctamente.')
    return redirect('acompanamiento:detail', pk=pk)


# ============================================================================
# VISTAS DE EDICIÓN / ELIMINACIÓN (Observaciones, Recomendaciones, Reporte)
# ============================================================================

def _log_auditoria(report, accion, actor, autor_original=None, detalle=''):
    """Deja evidencia de una acción sensible (cerrar/reabrir/editar reporte,
    editar/eliminar observación o recomendación) para futuras auditorías."""
    from .models import AuditoriaAccion
    AuditoriaAccion.objects.create(
        report=report,
        accion=accion,
        actor=actor,
        autor_original=autor_original,
        estudiante_nombre=report.student.full_name if report and report.student_id else '',
        detalle=detalle,
    )


def _check_can_edit(viewer, created_by_user, report=None):
    """True si el viewer puede editar/eliminar: acceso global, es el creador,
    o el reporte cae dentro de su alcance como coordinador de sección."""
    from .permissions import has_global_access, can_manage_report
    if has_global_access(viewer):
        return True
    if viewer and created_by_user and viewer.pk == created_by_user.pk:
        return True
    if report is not None and can_manage_report(viewer, report):
        return True
    return False


def _report_is_closed(report):
    return report.status == ReportStatus.ATENDIDO and report.fecha_cierre is not None


@require_POST
def editar_observacion(request, pk):
    from .permissions import resolve_viewer
    obs = get_object_or_404(Observation, pk=pk)
    if _report_is_closed(obs.report):
        return JsonResponse({'error': 'El reporte está cerrado. Solo lectura.'}, status=403)
    viewer = resolve_viewer(request)
    if not _check_can_edit(viewer, obs.created_by, obs.report):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    content_anterior = obs.content
    content = request.POST.get('content', '').strip()
    followup_date = request.POST.get('followup_date', '').strip() or None
    if not content:
        return JsonResponse({'error': 'El contenido no puede estar vacío'}, status=400)
    obs.content = content
    obs.followup_date = followup_date
    obs.save()
    if not (viewer and obs.created_by and viewer.pk == obs.created_by.pk):
        _log_auditoria(obs.report, 'EDITAR_OBSERVACION', viewer, autor_original=obs.created_by,
                        detalle=f"Contenido anterior: {content_anterior}")
    return JsonResponse({
        'ok': True,
        'content': obs.content,
        'followup_date': str(obs.followup_date) if obs.followup_date else '',
    })


@require_POST
def eliminar_observacion(request, pk):
    from .permissions import resolve_viewer
    obs = get_object_or_404(Observation, pk=pk)
    if _report_is_closed(obs.report):
        return JsonResponse({'error': 'El reporte está cerrado. Solo lectura.'}, status=403)
    viewer = resolve_viewer(request)
    if not _check_can_edit(viewer, obs.created_by, obs.report):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    report_pk = obs.report.pk
    report_obj = obs.report
    if not (viewer and obs.created_by and viewer.pk == obs.created_by.pk):
        _log_auditoria(report_obj, 'ELIMINAR_OBSERVACION', viewer, autor_original=obs.created_by,
                        detalle=f"Contenido eliminado: {obs.content}")
    obs.delete()
    report_obj.update_recuento()
    return JsonResponse({'ok': True, 'report_pk': report_pk})


@require_POST
def editar_recomendacion(request, pk):
    from .permissions import resolve_viewer
    rec = get_object_or_404(Recommendation, pk=pk)
    if _report_is_closed(rec.report):
        return JsonResponse({'error': 'El reporte está cerrado. Solo lectura.'}, status=403)
    viewer = resolve_viewer(request)
    if not _check_can_edit(viewer, rec.created_by, rec.report):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    content_anterior = rec.content
    content = request.POST.get('content', '').strip()
    followup_date = request.POST.get('followup_date', '').strip() or None
    if not content:
        return JsonResponse({'error': 'El contenido no puede estar vacío'}, status=400)
    rec.content = content
    rec.followup_date = followup_date
    rec.save()
    if not (viewer and rec.created_by and viewer.pk == rec.created_by.pk):
        _log_auditoria(rec.report, 'EDITAR_RECOMENDACION', viewer, autor_original=rec.created_by,
                        detalle=f"Contenido anterior: {content_anterior}")
    return JsonResponse({
        'ok': True,
        'content': rec.content,
        'followup_date': str(rec.followup_date) if rec.followup_date else '',
    })


@require_POST
def eliminar_recomendacion(request, pk):
    from .permissions import resolve_viewer
    rec = get_object_or_404(Recommendation, pk=pk)
    if _report_is_closed(rec.report):
        return JsonResponse({'error': 'El reporte está cerrado. Solo lectura.'}, status=403)
    viewer = resolve_viewer(request)
    if not _check_can_edit(viewer, rec.created_by, rec.report):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    if not (viewer and rec.created_by and viewer.pk == rec.created_by.pk):
        _log_auditoria(rec.report, 'ELIMINAR_RECOMENDACION', viewer, autor_original=rec.created_by,
                        detalle=f"Contenido eliminado: {rec.content}")
    rec.delete()
    return JsonResponse({'ok': True})


@require_POST
def editar_reporte(request, pk):
    from .permissions import resolve_viewer, can_manage_report
    report = get_object_or_404(Report, pk=pk)
    if _report_is_closed(report):
        return JsonResponse({'error': 'El reporte está cerrado. Solo lectura.'}, status=403)
    viewer = resolve_viewer(request)
    if not can_manage_report(viewer, report):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    objetivo = request.POST.get('objective', '').strip()
    new_status = request.POST.get('status', '').strip()
    purpose = request.POST.get('purpose', '').strip()
    academic_period = request.POST.get('academic_period', '').strip()

    detalle_previo = (f"objective={report.objective!r}, status={report.status!r}, "
                       f"purpose={report.purpose!r}, academic_period={report.academic_period!r}")
    if objetivo:
        report.objective = objetivo
    if new_status and new_status in [s for s, _ in ReportStatus.choices]:
        report.status = new_status
    if purpose and purpose in [p for p, _ in ReportPurpose.choices]:
        report.purpose = purpose
    if academic_period:
        report.academic_period = academic_period
    report.save()
    _log_auditoria(report, 'EDITAR_REPORTE', viewer, detalle=f"Antes: {detalle_previo}")
    return JsonResponse({
        'ok': True,
        'objective': report.objective,
        'status': report.status,
        'status_display': report.get_status_display(),
        'purpose': report.purpose,
        'purpose_display': report.get_purpose_display(),
        'academic_period': report.academic_period,
    })


@require_POST
def reabrir_reporte(request, pk):
    """Reabre un caso cerrado. Solo coordinadores con control sobre ese reporte (su sección) o acceso global."""
    from .permissions import resolve_real_user, can_manage_report
    real_user = resolve_real_user(request)
    report = get_object_or_404(Report, pk=pk)
    if not can_manage_report(real_user, report):
        return JsonResponse({'error': 'Sin permiso para reabrir casos.'}, status=403)

    if not report.is_closed:
        return JsonResponse({'error': 'El reporte no está cerrado.'}, status=400)

    nuevo_objetivo   = request.POST.get('objetivo', '').strip()
    notas_reapertura = request.POST.get('notas', '').strip()
    nuevo_asignado_id= request.POST.get('assigned_to_id', '').strip()

    # Guardar historial del ciclo que se cierra
    from django.contrib.auth import get_user_model
    User = get_user_model()
    AtencionHistorial.objects.create(
        report       = report,
        atendido_por = report.assigned_to,
        objetivo     = report.objective,
        periodo      = report.academic_period,
        fecha_inicio = report.created_at,
        fecha_cierre = report.fecha_cierre,
        cumple       = report.cumple_acompanamiento,
        reabierto_por    = real_user,
        notas_reapertura = notas_reapertura,
    )
    _log_auditoria(report, 'REABRIR', real_user, detalle=notas_reapertura or 'Sin notas adicionales')

    # Resetear el reporte para el nuevo ciclo
    report.status                = ReportStatus.SEGUIMIENTO
    report.fecha_cierre          = None
    report.cumple_acompanamiento = False
    report.is_accomplished       = False
    if nuevo_objetivo:
        report.objective = nuevo_objetivo
    if nuevo_asignado_id:
        nuevo_asig = User.objects.filter(pk=nuevo_asignado_id, is_active=True).first()
        if nuevo_asig:
            report.assigned_to = nuevo_asig
            report.institucional_quien_atiende = nuevo_asig.email
    report.save()

    return JsonResponse({
        'ok': True,
        'message': f'Caso reabierto. Historial guardado ({report.historial_atenciones.count()} ciclos anteriores).',
        'redirect': request.build_absolute_uri(f'/reports/reportes/{pk}/'),
    })


# ============================================================================
# API REST VIEWSETS (para consumo por frontend React/JavaScript)
# ============================================================================

class SectionViewSet(viewsets.ReadOnlyModelViewSet):
    """API para listar secciones"""
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class CourseViewSet(viewsets.ModelViewSet):
    """API para listar y crear cursos"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['section']
    search_fields = ['name']


class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    """API para listar estudiantes"""
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['course', 'grado', 'section']
    search_fields = ['full_name', 'code', 'email']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Student.objects.all()

        educador = Educador.objects.filter(user=user, is_active=True).first()
        if educador and educador.rol == UserRole.COORDINADOR and educador.seccion_asignada:
            return Student.objects.filter(course__section=educador.seccion_asignada)
        return Student.objects.all()

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def sync_from_api(self, request):
        """Endpoint para sincronizar estudiantes desde API externa"""
        count = Student.sync_from_api()
        return Response({
            'status': 'success',
            'message': f'{count} estudiantes sincronizados exitosamente',
            'count': count
        })


class ObservationViewSet(viewsets.ModelViewSet):
    """API para crear y listar observaciones"""
    queryset = Observation.objects.all()
    serializer_class = ObservationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['report']

    def perform_create(self, serializer):
        """Automáticamente asigna el usuario actual como creador"""
        serializer.save(created_by=self.request.user)


class RecommendationViewSet(viewsets.ModelViewSet):
    """API para crear y listar recomendaciones"""
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['report']

    def perform_create(self, serializer):
        """Automáticamente asigna el usuario actual como creador"""
        serializer.save(created_by=self.request.user)


class ReportViewSet(viewsets.ModelViewSet):
    """
    API para reportes de acompañamiento.

    Acciones disponibles:
    - GET /api/reportes/ → Lista de reportes
    - POST /api/reportes/ → Crear nuevo reporte
    - GET /api/reportes/{id}/ → Detalle del reporte
    - PATCH /api/reportes/{id}/ → Actualizar reporte
    - DELETE /api/reportes/{id}/ → Eliminar reporte
    - POST /api/reportes/{id}/cerrar/ → Cerrar reporte
    - GET /api/reportes/{id}/observaciones/ → Ver observaciones
    - POST /api/reportes/{id}/observaciones/ → Agregar observación
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'status', 'purpose', 'assigned_to']
    search_fields = ['student__full_name', 'student__code', 'objective']
    ordering_fields = ['created_at', 'status', 'purpose']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filtra reportes según el usuario actual"""
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Report.objects.all()
        educador = Educador.objects.filter(user=user, is_active=True).first()

        if not educador:
            return Report.objects.filter(Q(created_by=user) | Q(assigned_to=user)).distinct()

        if educador.rol == UserRole.ADMIN:
            return Report.objects.all()

        if educador.rol == UserRole.COORDINADOR and educador.seccion_asignada:
            return Report.objects.filter(student__course__section=educador.seccion_asignada).distinct()

        return Report.objects.filter(Q(created_by=user) | Q(assigned_to=user)).distinct()

    def get_serializer_class(self):
        """Usa diferentes serializers para diferentes acciones"""
        if self.action == 'retrieve':
            return ReportDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ReportCreateUpdateSerializer
        return ReportListSerializer

    def perform_create(self, serializer):
        """Automáticamente asigna el usuario actual como creador"""
        serializer.save(created_by=self.request.user)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        fines = self.request.query_params.getlist('fines_educativos')
        if fines:
            for fin in fines:
                queryset = queryset.filter(fines_educativos__contains=[fin])
        return queryset

    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        """Acción para cerrar un reporte"""
        report = self.get_object()
        report.close_report()
        return Response({
            'status': 'success',
            'message': f'Reporte {report.id} cerrado exitosamente',
            'fecha_cierre': report.fecha_cierre
        })

    @action(detail=True, methods=['get', 'post'])
    def observaciones(self, request, pk=None):
        """Ver/agregar observaciones a un reporte"""
        report = self.get_object()

        if request.method == 'GET':
            observaciones = report.observations.all()
            serializer = ObservationSerializer(observaciones, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            serializer = ObservationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(created_by=request.user, report=report)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EducadorViewSet(viewsets.ModelViewSet):
    """API de gestión de Educadores/Roles."""
    queryset = Educador.objects.select_related('user', 'seccion_asignada').all()
    serializer_class = EducadorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['rol', 'is_active', 'seccion_asignada']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'user__username']

    @action(detail=True, methods=['get', 'post'])
    def recomendaciones(self, request, pk=None):
        """Ver/agregar recomendaciones a un reporte"""
        report = self.get_object()

        if request.method == 'GET':
            recomendaciones = report.recommendations.all()
            serializer = RecommendationSerializer(recomendaciones, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            serializer = RecommendationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(created_by=request.user, report=report)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
