from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from django.utils import timezone
from django.db.models import Count
from django.http import JsonResponse
from acompanamiento.models import Student, Report, Observation, Recommendation
from acompanamiento.views_sso import sso_login
import json
from collections import defaultdict

# ── Constantes compartidas ───────────────────────────────────────
DASH_FINES   = ['ACADEMICO', 'PSICOAFECTIVO', 'ESPIRITUAL', 'CONVIVENCIA']
DASH_FINES_L = ['Académico', 'Psicoafectivo', 'Espiritual', 'Convivencia']
DASH_SEC_MAP = {
    'preescolar':       'Jardín – Tercero',
    'basica_primaria':  'Cuarto – Séptimo',
    'basica_secundaria':'Octavo – Undécimo',
    'media_academica':  'Octavo – Undécimo',
}
_INFORME_EMAILS = {'cap@calasanzsuba.edu.co', 'mrodriguez@calasanzsuba.edu.co'}

# ── Estadísticas del dashboard ───────────────────────────────────
def _build_dash_stats(qs):
    total = qs.count()
    pct   = lambda n: round(n * 100 / total, 1) if total else 0
    seg   = qs.filter(status='SEGUIMIENTO').count()
    ate   = qs.filter(status='ATENDIDO').count()
    pro   = qs.filter(status='PROGRAMADO').count()
    obs   = Observation.objects.filter(report__in=qs).count()
    rec   = Recommendation.objects.filter(report__in=qs).count()
    per_q = (qs.exclude(academic_period='')
               .values('academic_period').annotate(n=Count('id')).order_by('-n')[:5])
    top_q = list(qs.exclude(assigned_to=None)
                   .values('assigned_to__id', 'assigned_to__first_name', 'assigned_to__last_name')
                   .annotate(t=Count('id')).order_by('-t')[:5])
    top_labels = [f"{e['assigned_to__first_name']} {e['assigned_to__last_name']}".strip() for e in top_q]
    def top_by(st):
        return [qs.filter(assigned_to_id=e['assigned_to__id'], status=st).count() for e in top_q]
    sec_q = (qs.values('student__section')
               .annotate(n=Count('id'))
               .filter(student__section__in=DASH_SEC_MAP)
               .order_by('-n'))
    sec_merged = defaultdict(int)
    for s in sec_q:
        sec_merged[DASH_SEC_MAP[s['student__section']]] += s['n']
    return {
        'total': total, 'obs': obs, 'rec': rec,
        'seg': seg, 'ate': ate, 'pro': pro,
        'pct_ate': pct(ate), 'pct_seg': pct(seg), 'pct_pro': pct(pro),
        'fin_totals': [qs.filter(purpose=f).count() for f in DASH_FINES],
        'fin_seg':    [qs.filter(purpose=f, status='SEGUIMIENTO').count() for f in DASH_FINES],
        'fin_ate':    [qs.filter(purpose=f, status='ATENDIDO').count()    for f in DASH_FINES],
        'fin_pro':    [qs.filter(purpose=f, status='PROGRAMADO').count()  for f in DASH_FINES],
        'per_labels': [p['academic_period'] for p in per_q],
        'per_data':   [p['n'] for p in per_q],
        'top_labels': top_labels,
        'top_seg': top_by('SEGUIMIENTO'),
        'top_ate': top_by('ATENDIDO'),
        'top_pro': top_by('PROGRAMADO'),
        'estados':    [seg, ate, pro],
        'sec_labels': list(sec_merged.keys()),
        'sec_data':   list(sec_merged.values()),
    }

def _apply_dash_filters(qs, fin, assigned_to_id, section, period, status=''):
    if fin:
        qs = qs.filter(purpose=fin)
    if assigned_to_id:
        qs = qs.filter(assigned_to_id=assigned_to_id)
    if section:
        if section == 'basica_secundaria':
            qs = qs.filter(student__section__in=['basica_secundaria', 'media_academica'])
        else:
            qs = qs.filter(student__section=section)
    if period:
        qs = qs.filter(academic_period=period)
    if status:
        qs = qs.filter(status=status)
    return qs

# ── Endpoint AJAX ────────────────────────────────────────────────
def dashboard_api(request):
    from acompanamiento.permissions import filter_reports_for_user, resolve_viewer
    viewer  = resolve_viewer(request)
    base_qs = filter_reports_for_user(
        Report.objects.select_related('student', 'student__course', 'assigned_to').all(), viewer
    )
    fin            = request.GET.get('fin', '')
    assigned_to_id = request.GET.get('assigned_to', '')
    section        = request.GET.get('section', '')
    period         = request.GET.get('period', '')
    status         = request.GET.get('status', '')

    filtered = _apply_dash_filters(base_qs, fin, assigned_to_id, section, period, status)

    # p1/p2: mismos filtros pero cambian el período (sin filtro de período del dropdown)
    p1_base = _apply_dash_filters(base_qs, fin, assigned_to_id, section, 'Primer Periodo', status)
    p2_base = _apply_dash_filters(base_qs, fin, assigned_to_id, section, 'Segundo Periodo', status)

    # Tabla de programados: si hay filtro de estado, mostrar los de ese estado; si no, PROGRAMADO
    tabla_status = status if status else 'PROGRAMADO'
    recientes_qs = filtered.filter(status=tabla_status).order_by('-created_at')[:10]
    recientes = [{
        'student_name':   r.student.full_name,
        'course':         r.student.course.name if r.student.course else '—',
        'purpose':        r.purpose,
        'purpose_display': r.get_purpose_display(),
        'assigned_to':    r.assigned_to.get_full_name() if r.assigned_to else '—',
    } for r in recientes_qs]

    return JsonResponse({
        'all': _build_dash_stats(filtered),
        'p1':  _build_dash_stats(p1_base),
        'p2':  _build_dash_stats(p2_base),
        'recientes': recientes,
        'tabla_status': tabla_status,
    })

# ── Vista principal ──────────────────────────────────────────────
def home(request):
    from acompanamiento.permissions import (
        filter_reports_for_user, resolve_viewer, has_global_access,
        get_allowed_fines, get_viewer_sections,
    )
    from django.contrib.auth import get_user_model
    User   = get_user_model()
    viewer = resolve_viewer(request)

    base_qs = filter_reports_for_user(
        Report.objects.select_related('student', 'student__course', 'assigned_to').all(), viewer
    )
    d = _build_dash_stats(base_qs)

    # ── Opciones de filtros (respetan permisos del viewer) ──
    all_fins = [
        ('ACADEMICO','Académico'), ('PSICOAFECTIVO','Psicoafectivo'),
        ('ESPIRITUAL','Espiritual'), ('CONVIVENCIA','Convivencia'),
    ]
    allowed_fines = get_allowed_fines(viewer)
    fins_filter = [(k, l) for k, l in all_fins if k in allowed_fines] if allowed_fines else all_fins

    all_secs = [
        ('preescolar',       'Jardín – Tercero'),
        ('basica_primaria',  'Cuarto – Séptimo'),
        ('basica_secundaria','Octavo – Undécimo'),
    ]
    viewer_secs = get_viewer_sections(viewer)
    if viewer_secs:
        visible = set(viewer_secs)
        if 'media_academica' in visible:
            visible.add('basica_secundaria')
        secs_filter = [(k, l) for k, l in all_secs if k in visible]
    else:
        secs_filter = all_secs

    educator_ids    = base_qs.exclude(assigned_to=None).values_list('assigned_to_id', flat=True).distinct()
    educators_filter = User.objects.filter(pk__in=educator_ids).order_by('first_name', 'last_name')
    periods_filter  = list(
        base_qs.exclude(academic_period='')
               .values_list('academic_period', flat=True)
               .distinct().order_by('academic_period')
    )

    can_export = (viewer and viewer.is_authenticated and viewer.email in _INFORME_EMAILS)

    return render(request, 'dashboard.html', {
        'today':            timezone.now(),
        'students_count':   Student.objects.count(),
        'fines_labels':     json.dumps(DASH_FINES_L),
        'j_all':            json.dumps(d),
        'j_p1':             json.dumps(_build_dash_stats(base_qs.filter(academic_period='Primer Periodo'))),
        'j_p2':             json.dumps(_build_dash_stats(base_qs.filter(academic_period='Segundo Periodo'))),
        'recientes':        base_qs.filter(status='PROGRAMADO').order_by('-created_at')[:10],
        'd':                d,
        'current_user':     viewer,
        'viewer_is_global': has_global_access(viewer),
        'can_export':       can_export,
        'fins_filter':      fins_filter,
        'secs_filter':      secs_filter,
        'educators_filter': educators_filter,
        'periods_filter':   periods_filter,
    })


def serve_sw(request):
    import os
    from django.http import HttpResponse
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    with open(sw_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return HttpResponse(content, content_type='application/javascript')


urlpatterns = [
    path("admin/", admin.site.urls),
    path("sw.js", serve_sw, name='sw'),
    path("auth/sso/", sso_login, name='sso_login'),
    path("", home, name='home'),
    path("dashboard-api/", dashboard_api, name='dashboard_api'),
    path("reports/", include('acompanamiento.urls')),
    path("students/", include('estudiantes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static('/archivos/', document_root=settings.BASE_DIR / 'archivos')
