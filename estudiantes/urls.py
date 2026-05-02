from django.urls import path
from . import views

app_name = 'estudiantes'

urlpatterns = [
    path('', views.StudentListView.as_view(), name='list'),
    path('sync/', views.sync_students, name='sync'),
]
