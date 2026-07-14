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
    path('reportes/<int:pk>/reabrir/', views.reabrir_reporte, name='reabrir'),
    path('reportes/<int:pk>/editar/', views.editar_reporte, name='editar_reporte'),

    # Observaciones
    path('observaciones/<int:pk>/editar/', views.editar_observacion, name='editar_observacion'),
    path('observaciones/<int:pk>/eliminar/', views.eliminar_observacion, name='eliminar_observacion'),

    # Recomendaciones
    path('recomendaciones/<int:pk>/editar/', views.editar_recomendacion, name='editar_recomendacion'),
    path('recomendaciones/<int:pk>/eliminar/', views.eliminar_recomendacion, name='eliminar_recomendacion'),

    # Módulo de indicadores SGI
    path('indicadores/', views.indicadores_view, name='indicadores'),
    path('indicadores/informe/', views.informe_acompanamiento_view, name='informe'),

    # Administración de educadores (roles y permisos)
    path('admin-sai/educadores/', views.admin_educadores_view, name='admin_educadores'),

    # Simulador de vistas (solo super-admin)
    path('admin-sai/simulador/', views.simulator_view, name='simulator'),
    path('admin-sai/simulador/activar/', views.activate_simulation, name='activate_simulation'),
    path('admin-sai/simulador/salir/', views.stop_simulation, name='stop_simulation'),
]
