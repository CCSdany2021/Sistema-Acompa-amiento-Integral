"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from django.utils import timezone
from django.db.models import Count
from acompanamiento.models import Student, Report, Observation, Recommendation
import json

def home(request):
    FINES   = ['ACADEMICO','PSICOAFECTIVO','ESPIRITUAL','CONVIVENCIA']
    FINES_L = ['Académico','Psicoafectivo','Espiritual','Convivencia']
    SEC_MAP = {'preescolar':'Jardín - Tercero','basica_primaria':'Cuarto - Séptimo',
               'basica_secundaria':'Octavo - Undécimo','media_academica':'Octavo - Undécimo'}

    def build_stats(qs):
        total = qs.count()
        pct   = lambda n: round(n*100/total, 1) if total else 0
        seg   = qs.filter(status='SEGUIMIENTO').count()
        ate   = qs.filter(status='ATENDIDO').count()
        pro   = qs.filter(status='PROGRAMADO').count()
        obs   = Observation.objects.filter(report__in=qs).count()
        rec   = Recommendation.objects.filter(report__in=qs).count()
        per_q = (qs.exclude(academic_period='')
                   .values('academic_period').annotate(n=Count('id')).order_by('-n')[:5])
        top_q = list(qs.values('assigned_to__first_name','assigned_to__last_name')
                       .annotate(t=Count('id')).order_by('-t')[:5])
        top_labels = [f"{e['assigned_to__first_name']} {e['assigned_to__last_name']}" for e in top_q]
        def top_by(st):
            return [qs.filter(assigned_to__first_name=e['assigned_to__first_name'],
                              assigned_to__last_name=e['assigned_to__last_name'],
                              status=st).count() for e in top_q]
        # Contar REPORTES por sección (no estudiantes únicos) para que sume igual que total
        sec_q = (qs.values('student__section')
                   .annotate(n=Count('id'))
                   .filter(student__section__in=SEC_MAP)
                   .order_by('-n'))
        from collections import defaultdict
        sec_merged = defaultdict(int)
        for s in sec_q:
            sec_merged[SEC_MAP[s['student__section']]] += s['n']
        return {
            'total':total,'obs':obs,'rec':rec,
            'seg':seg,'ate':ate,'pro':pro,
            'pct_ate':pct(ate),'pct_seg':pct(seg),
            'fin_totals':[qs.filter(purpose=f).count() for f in FINES],
            'fin_seg':[qs.filter(purpose=f,status='SEGUIMIENTO').count() for f in FINES],
            'fin_ate':[qs.filter(purpose=f,status='ATENDIDO').count()    for f in FINES],
            'fin_pro':[qs.filter(purpose=f,status='PROGRAMADO').count()  for f in FINES],
            'per_labels':[p['academic_period'] for p in per_q],
            'per_data':[p['n'] for p in per_q],
            'top_labels': top_labels,
            'top_seg':    top_by('SEGUIMIENTO'),
            'top_ate':    top_by('ATENDIDO'),
            'top_pro':    top_by('PROGRAMADO'),
            'estados':[seg,ate,pro],
            'sec_labels': list(sec_merged.keys()),
            'sec_data':   list(sec_merged.values()),
        }

    d = build_stats(Report.objects.all())

    return render(request, 'dashboard.html', {
        'today':          timezone.now(),
        'students_count': Student.objects.count(),
        'fines_labels':   json.dumps(FINES_L),
        'j_all':          json.dumps(d),
        'j_p1':           json.dumps(build_stats(Report.objects.filter(academic_period='Primer Periodo'))),
        'j_p2':           json.dumps(build_stats(Report.objects.filter(academic_period='Segundo Periodo'))),
        'recientes':      Report.objects.select_related('student','assigned_to').order_by('-created_at')[:8],
        'd':              d,
    })

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name='home'),
    path("reports/", include('acompanamiento.urls')),
    path("students/", include('estudiantes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static('/archivos/', document_root=settings.BASE_DIR / 'archivos')
