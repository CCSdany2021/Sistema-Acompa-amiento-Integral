from django.urls import path
from . import views

app_name = 'estudiantes'

urlpatterns = [
    path('', views.StudentListView.as_view(), name='list'),
    path('sync/', views.sync_students, name='sync'),
    path('<int:student_id>/ficha/', views.ficha_estudiante_view, name='ficha_estudiante'),
]
