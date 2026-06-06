from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'acompanamiento'

# Router para API REST
router = DefaultRouter()
router.register(r'api/secciones', views.SectionViewSet, basename='section')
router.register(r'api/cursos', views.CourseViewSet, basename='course')
router.register(r'api/estudiantes', views.StudentViewSet, basename='student')
router.register(r'api/observaciones', views.ObservationViewSet, basename='observation')
router.register(r'api/recomendaciones', views.RecommendationViewSet, basename='recommendation')
router.register(r'api/reportes', views.ReportViewSet, basename='report')
router.register(r'api/educadores', views.EducadorViewSet, basename='educador')

urlpatterns = [
    # API REST
    path('', include(router.urls)),

    # Vistas HTML
    path('reportes/', views.ReportListView.as_view(), name='list'),
    path('reportes/create/', views.ReportCreateView.as_view(), name='create'),
    path('reportes/<int:pk>/', views.ReportDetailView.as_view(), name='detail'),
    path('reportes/<int:pk>/cerrar/', views.cerrar_report, name='cerrar'),

    # Módulo de indicadores SGI
    path('indicadores/', views.indicadores_view, name='indicadores'),
    path('indicadores/informe/', views.informe_acompanamiento_view, name='informe'),

    # Administración de educadores (roles y permisos)
    path('admin-sai/educadores/', views.admin_educadores_view, name='admin_educadores'),
]
