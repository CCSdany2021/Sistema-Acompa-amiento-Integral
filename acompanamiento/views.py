from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from django.db import IntegrityError, transaction  
from django.contrib import messages  
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Section, Course, Student, Report, Observation, Recommendation, Educador, UserRole, ReportStatus, ReportPurpose
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
        queryset = super().get_queryset()
        
        # Filtros
        search = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        purpose_filter = self.request.GET.get('purpose', '')
        period_filter = self.request.GET.get('period', '')
        grado_filter = self.request.GET.get('grado', '')
        
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
        if grado_filter:
            queryset = queryset.filter(student__grado=grado_filter)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = ReportStatus.choices
        context['purpose_choices'] = ReportPurpose.choices
        context['grado_choices'] = ['PREESCOLAR', 'PRIMARIA', 'BACHILLERATO']
        context['periodos'] = ['2026-1', '2026-2', '2025-1', '2025-2']
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


def indicadores_view(request):
    """Módulo de indicadores SGI — Eficiencia y Eficacia del acompañamiento."""
    from django.db.models import Q

    # Filtros GET
    periodo  = request.GET.get('periodo', '')
    seccion  = request.GET.get('seccion', '')
    fin      = request.GET.get('fin', '')
    anio     = request.GET.get('anio', '2026')

    qs = Report.objects.filter(year=int(anio) if anio.isdigit() else 2026)
    if periodo:
        qs = qs.filter(academic_period=periodo)
    if seccion:
        # basica_secundaria incluye también los estudiantes con section=media_academica
        if seccion == 'basica_secundaria':
            qs = qs.filter(student__section__in=['basica_secundaria', 'media_academica'])
        else:
            qs = qs.filter(student__section__iexact=seccion)
    if fin:
        qs = qs.filter(purpose=fin)

    periodos_disponibles = (Report.objects.filter(year=int(anio) if anio.isdigit() else 2026)
                            .exclude(academic_period='')
                            .values_list('academic_period', flat=True)
                            .distinct().order_by('academic_period'))

    stats = _calc_indicadores(qs)

    return render(request, 'acompanamiento/indicadores.html', {
        'stats': stats,
        'periodo': periodo,
        'seccion': seccion,
        'fin': fin,
        'anio': anio,
        'periodos': list(periodos_disponibles),
        'secciones': [
            ('preescolar',        'Jardín–Tercero'),
            ('basica_primaria',   'Cuarto–Séptimo'),
            ('basica_secundaria', 'Octavo–Undécimo'),
        ],
        'fines': [
            ('ACADEMICO', 'Académico'), ('PSICOAFECTIVO', 'Psicoafectivo'),
            ('ESPIRITUAL', 'Espiritual'), ('CONVIVENCIA', 'Convivencia'),
        ],
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

    # Tendencia mensual
    MESES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    monthly_raw = (qs.annotate(mes=TruncMonth('created_at'))
                     .values('mes')
                     .annotate(total=Count('id'),
                               academico=Count('id', filter=Q(purpose='ACADEMICO')),
                               convivencia=Count('id', filter=Q(purpose='CONVIVENCIA')),
                               espiritual=Count('id', filter=Q(purpose='ESPIRITUAL')),
                               psicoafectivo=Count('id', filter=Q(purpose='PSICOAFECTIVO')))
                     .order_by('mes'))
    monthly = [{'mes': MESES[m['mes'].month-1], **m} for m in monthly_raw if m['mes']]
    monthly_max = max((m['total'] for m in monthly), default=1)

    periodos = list(Report.objects.filter(year=int(anio) if anio.isdigit() else 2026)
                    .exclude(academic_period='')
                    .values_list('academic_period', flat=True)
                    .distinct().order_by('academic_period'))

    return render(request, 'acompanamiento/informe.html', {
        'stats': stats, 'por_fin_dist': por_fin_dist, 'estados': estados,
        'top_eds': top_eds, 'monthly': monthly, 'monthly_max': monthly_max,
        'anio': anio, 'periodo': periodo, 'seccion': seccion, 'fin': fin,
        'fecha': timezone.now(), 'periodos': periodos,
        'secciones': [('preescolar','Jardín–Tercero'),('basica_primaria','Cuarto–Séptimo'),
                      ('basica_secundaria','Octavo–Undécimo')],
        'fines': [('ACADEMICO','Académico'),('PSICOAFECTIVO','Psicoafectivo'),
                  ('ESPIRITUAL','Espiritual'),('CONVIVENCIA','Convivencia')],
    })


def admin_educadores_view(request):
    """Gestión de roles y permisos de educadores (solo acceso global)."""
    from .permissions import can_manage_educadores
    from django.contrib.auth import get_user_model
    import json

    # Mismo patrón de resolución de usuario que StudentListView
    actual_user = request.user
    User = get_user_model()
    if not actual_user or not actual_user.is_authenticated:
        actual_user = (
            User.objects.filter(is_superuser=True, is_active=True).first()
            or User.objects.filter(is_staff=True, is_active=True).first()
        )

    if not can_manage_educadores(actual_user):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('No tienes permiso. Requiere superuser o acceso_global=True.')

    User = get_user_model()

    if request.method == 'POST':
        action = request.POST.get('action', '')
        user_id = request.POST.get('user_id', '')
        if action == 'save_educador' and user_id:
            user = User.objects.filter(pk=user_id).first()
            if user:
                ed, _ = Educador.objects.get_or_create(user=user)
                ed.rol            = request.POST.get('rol', 'ADMIN_SECCION')
                ed.acceso_global  = request.POST.get('acceso_global') == '1'
                ed.is_active      = request.POST.get('is_active') == '1'
                fines = request.POST.getlist('fines_educativos')
                ed.fines_educativos = fines
                ed.save()
                sec_ids = request.POST.getlist('secciones')
                ed.secciones.set(Section.objects.filter(pk__in=sec_ids))
                messages.success(request, f'Perfil de {user.get_full_name()} actualizado.')
        return redirect('acompanamiento:admin_educadores')

    # Lista de todos los usuarios con su perfil educador
    all_users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    educadores_data = []
    for u in all_users:
        try:
            ed = u.educador
        except Exception:
            ed = None
        educadores_data.append({'user': u, 'educador': ed})

    sections = Section.objects.all().order_by('name')
    fines = [
        ('ACADEMICO', 'Académico'), ('PSICOAFECTIVO', 'Psicoafectivo'),
        ('ESPIRITUAL', 'Espiritual'), ('CONVIVENCIA', 'Convivencia'),
    ]

    return render(request, 'acompanamiento/admin_educadores.html', {
        'educadores_data': educadores_data,
        'sections': sections,
        'fines': fines,
        'rol_choices': UserRole.choices,
    })


def cerrar_report(request, pk):
    """Cierra un reporte con los criterios seleccionados"""
    report = Report.objects.get(pk=pk)
    
    # Obtener datos del formulario
    new_status = request.POST.get('status', ReportStatus.ATENDIDO)
    cumplimiento = request.POST.get('is_accomplished', 'false')
    
    # Actualizar reporte
    report.status = new_status
    report.is_accomplished = True if cumplimiento == 'true' else False
    report.fecha_cierre = timezone.now()
    report.save()
    
    from django.contrib import messages
    estado_texto = dict(ReportStatus.choices).get(new_status, new_status)
    messages.success(request, f'Reporte de {report.student.full_name} cerrado. Estado: {estado_texto}')
    return redirect('acompanamiento:detail', pk=pk)


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
