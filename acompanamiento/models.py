from django.db import models
from django.conf import settings
from django.utils import timezone

class Grado(models.TextChoices):
    """Grados/Niveles educativos"""
    PREESCOLAR = 'PREESCOLAR', 'Preescolar'
    PRIMARIA = 'PRIMARIA', 'Primaria (4°-7°)'
    BACHILLERATO = 'BACHILLERATO', 'Bachillerato (8°-11°)'

class Section(models.Model):
    """Secciones: Jardín a Tercero, Cuarto a Séptimo, Octavo a Undécimo"""
    name = models.CharField(max_length=100, unique=True, db_index=True)
    grado = models.CharField(max_length=20, choices=Grado.choices, default=Grado.PRIMARIA)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Sección'
        verbose_name_plural = 'Secciones'

    def __str__(self):
        return self.name

class Course(models.Model):
    """Cursos dentro de una sección (10A, 1102, etc)"""
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['section', 'name']
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'

    def __str__(self):
        return f"{self.section.name} - {self.name}"

class Student(models.Model):
    """Estudiantes de la institución"""
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')

    full_name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    email = models.EmailField(blank=True)
    section = models.CharField(max_length=100, blank=True)
    grado = models.CharField(
        max_length=20,
        choices=Grado.choices,
        default=Grado.PRIMARIA,
        verbose_name='Grado/Nivel'
    )

    # Imagen del estudiante
    imagen = models.ImageField(
        upload_to='estudiantes/',
        blank=True,
        null=True
    )

    # Para sincronización desde API
    external_id = models.CharField(max_length=100, blank=True, db_index=True)
    last_synced = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'

    def __str__(self):
        return f"{self.full_name} ({self.code})"

    @staticmethod
    def sync_from_api():
        """Sincroniza estudiantes desde Sistema Gestor Educativo"""
        import requests
        from django.conf import settings

        try:
            url = f"{settings.GESTOR_EDUCATIVO_URL}/api/v1/estudiantes/"
            headers = {'X-API-Key': settings.GESTOR_EDUCATIVO_API_KEY}
            params = {'estado': 'activo'}

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            students_data = data if isinstance(data, list) else data.get('results', [])

            count = 0
            for student in students_data:
                # Mapear grado desde API
                grado_api = student.get('grado', '').upper()
                grado_map = {
                    'PREESCOLAR': Grado.PREESCOLAR,
                    'PRIMARIA': Grado.PRIMARIA,
                    'BACHILLERATO': Grado.BACHILLERATO,
                }
                grado = grado_map.get(grado_api, Grado.PRIMARIA)

                Student.objects.update_or_create(
                    code=student.get('codigo_estudiante', ''),
                    defaults={
                        'full_name': student.get('nombre_completo', 'Sin Nombre'),
                        'email': student.get('email', ''),
                        'section': student.get('seccion', ''),
                        'grado': grado,
                        'external_id': str(student.get('uuid', student.get('id', ''))),
                    }
                )
                count += 1

            return count
        except Exception as e:
            print(f"Error sincronizando: {e}")
            return 0

class ReportStatus(models.TextChoices):
    PROGRAMADO = 'PROGRAMADO', 'Programado'
    SEGUIMIENTO = 'SEGUIMIENTO', 'En Seguimiento'
    ATENDIDO = 'ATENDIDO', 'Atendido'

class ReportPurpose(models.TextChoices):
    CONVIVENCIA = 'CONVIVENCIA', 'Convivencia'
    ACADEMICO = 'ACADEMICO', 'Académico'
    ESPIRITUAL = 'ESPIRITUAL', 'Espiritual'
    PSICOAFECTIVO = 'PSICOAFECTIVO', 'Psicoafectivo'


class UserRole(models.TextChoices):
    DOCENTE = "DOCENTE", "Docente"
    COORDINADOR = "COORDINADOR", "Coordinador"
    ADMIN = "ADMIN", "Administrador"


class Educador(models.Model):
    """Perfil de usuario con rol y alcance por sección."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='educador')
    rol = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.DOCENTE)
    seccion_asignada = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='educadores'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__first_name", "user__last_name", "user__username"]
        verbose_name = "Educador"
        verbose_name_plural = "Educadores"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_rol_display()}"

class Report(models.Model):
    """Reportes de acompañamiento integral del estudiante"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='reports')

    # Compatibilidad con versión previa (campo simple)
    purpose = models.CharField(max_length=50, choices=ReportPurpose.choices, blank=True)
    # Nueva estructura Power Apps: múltiples fines educativos
    fines_educativos = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=50, choices=ReportStatus.choices, default=ReportStatus.PROGRAMADO)
    objective = models.TextField(blank=True, help_text="Objetivo del acompañamiento")
    academic_period = models.CharField(max_length=50, blank=True, help_text="Período académico (ej: 2026-1)")
    is_accomplished = models.BooleanField(default=False, help_text="¿Se logró el objetivo?")
    cumple_acompanamiento = models.BooleanField(default=False)
    institucional_quien_atiende = models.EmailField(blank=True)
    datos_adjuntos = models.FileField(upload_to='adjuntos_reportes/', null=True, blank=True)

    # Campos adicionales de Power Apps
    imagen = models.ImageField(
        upload_to='reportes/',
        blank=True,
        null=True
    )
    recuento = models.IntegerField(default=0, help_text="Número de observaciones registradas")
    fecha_cierre = models.DateTimeField(null=True, blank=True, help_text="Fecha de cierre del reporte")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reports_created')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_assigned')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'purpose'],
                condition=models.Q(status__in=[ReportStatus.PROGRAMADO, ReportStatus.SEGUIMIENTO]),
                name='unique_active_report_per_student_purpose'
            )
        ]

    def __str__(self):
        return f"{self.purpose} - {self.student.full_name} ({self.status})"

    def close_report(self):
        """Cierra el reporte y registra la fecha de cierre"""
        self.status = ReportStatus.ATENDIDO
        self.fecha_cierre = timezone.now()
        self.save()

    def update_recuento(self):
        """Actualiza el contador de observaciones"""
        self.recuento = self.observations.count()
        self.save()

class Observation(models.Model):
    """Observaciones del acompañamiento"""
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='observations')
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(help_text="Descripción de la observación")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='observations_created')

    # Información adicional del usuario que observa
    correo_institucional = models.EmailField(blank=True, help_text="Email institucional de quien registra la observación")
    fin_educativo = models.CharField(max_length=50, choices=ReportPurpose.choices, blank=True)
    followup_date = models.DateField(null=True, blank=True, help_text="Fecha de seguimiento registrada manualmente")

    date_log = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_log']
        verbose_name = 'Observación'
        verbose_name_plural = 'Observaciones'

    def __str__(self):
        return f"Observación {self.id} - {self.report.student.full_name}"

    def save(self, *args, **kwargs):
        """Al crear observación, cambia estado de PROGRAMADO a SEGUIMIENTO"""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and self.report.status == ReportStatus.PROGRAMADO:
            self.report.status = ReportStatus.SEGUIMIENTO
            self.report.save()

        # Actualizar recuento de observaciones
        self.report.update_recuento()

class Recommendation(models.Model):
    """Recomendaciones pedagógicas"""
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='recommendations')
    content = models.TextField(help_text="Recomendación pedagógica")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='recommendations_created')

    # Información adicional del usuario que recomienda
    correo_institucional = models.EmailField(blank=True, help_text="Email institucional de quien registra la recomendación")
    fin_educativo = models.CharField(max_length=50, choices=ReportPurpose.choices, blank=True)
    followup_date = models.DateField(null=True, blank=True, help_text="Fecha de seguimiento registrada manualmente")

    date_log = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_log']
        verbose_name = 'Recomendación'
        verbose_name_plural = 'Recomendaciones'

    def __str__(self):
        return f"Recomendación {self.id} - {self.report.student.full_name}"
