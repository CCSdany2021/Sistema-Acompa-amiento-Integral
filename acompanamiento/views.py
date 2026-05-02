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
