from django.db import models
import requests
from django.conf import settings

class StudentCache(models.Model):
    """Cache de estudiantes desde API de Sistema Gestor Educativo"""
    external_id = models.CharField(max_length=100, unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    grade = models.CharField(max_length=50)
    course = models.CharField(max_length=50)
    section = models.CharField(max_length=50, blank=True)
    estado = models.CharField(max_length=50, default='activo')

    # Control de sincronización
    last_synced = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Cache de Estudiante'
        verbose_name_plural = 'Cache de Estudiantes'

    def __str__(self):
        return f"{self.full_name} ({self.code})"

    @staticmethod
    def sync_from_api():
        """Sincroniza estudiantes desde la API del Sistema Gestor Educativo"""
        try:
            url = f"{settings.GESTOR_EDUCATIVO_URL}/api/v1/estudiantes/"
            headers = {
                'X-API-Key': settings.GESTOR_EDUCATIVO_API_KEY
            }
            params = {'estado': 'activo'}

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            students_data = response.json()
            if isinstance(students_data, dict):
                students_data = students_data.get('results', [])

            count = 0
            for student in students_data:
                p_ap = (student.get('primer_apellido') or '').strip()
                s_ap = (student.get('segundo_apellido') or '').strip()
                p_nm = (student.get('primer_nombre') or '').strip()
                s_nm = (student.get('segundo_nombre') or '').strip()
                apellidos = ' '.join(filter(None, [p_ap, s_ap]))
                nombres = ' '.join(filter(None, [p_nm, s_nm]))
                full_name = f"{apellidos} {nombres}" if apellidos and nombres else student.get('nombre_completo', 'Sin Nombre')

                StudentCache.objects.update_or_create(
                    external_id=str(student.get('uuid', student.get('id', ''))),
                    defaults={
                        'full_name': full_name,
                        'code': student.get('codigo_estudiante', ''),
                        'email': student.get('email', ''),
                        'grade': student.get('grado', ''),
                        'course': student.get('curso', ''),
                        'section': student.get('seccion', ''),
                        'estado': student.get('estado', 'activo'),
                    }
                )
                count += 1

            return count
        except Exception as e:
            print(f"Error sincronizando estudiantes: {e}")
            return 0
