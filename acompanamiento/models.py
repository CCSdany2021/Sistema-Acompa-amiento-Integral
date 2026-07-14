from django.db import models
from django.conf import settings
from django.utils import timezone


def _user_display(user):
    """Nombre para mostrar de un usuario que puede ser None (ej: cuenta eliminada, on_delete=SET_NULL)."""
    if not user:
        return ''
    return user.get_full_name() or user.username


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
        """Sincroniza estudiantes desde Sistema Gestor Educativo (con paginación)"""
        import requests
        from django.conf import settings

        try:
            url = f"{settings.GESTOR_EDUCATIVO_URL}/api/v1/estudiantes/"
            headers = {'X-API-Key': settings.GESTOR_EDUCATIVO_API_KEY}
            params = {'estado': 'activo'}

            count = 0
            page = 1

            while url:
                response = requests.get(url, headers=headers, params=params, timeout=10, verify=False)
                response.raise_for_status()

                data = response.json()
                students_data = data if isinstance(data, list) else data.get('results', [])

                for student in students_data:
                    grado_api = (student.get('grado') or '').upper()
                    grado_map = {
                        'PREESCOLAR': Grado.PREESCOLAR,
                        'PRIMARIA': Grado.PRIMARIA,
                        'BACHILLERATO': Grado.BACHILLERATO,
                        'JARDIN': Grado.PREESCOLAR,
                        'TRANSICION': Grado.PREESCOLAR,
                    }
                    grado = grado_map.get(grado_api, Grado.PRIMARIA)

                    # Obtener o crear la seccion
                    seccion_name = student.get('seccion', '')
                    section_obj = None
                    if seccion_name:
                        section_obj, _ = Section.objects.get_or_create(
                            name=seccion_name,
                            defaults={'grado': grado}
                        )

                    # Obtener o crear el curso
                    course_obj = None
                    curso_code = student.get('curso', '')
                    if curso_code and section_obj:
                        course_obj, _ = Course.objects.get_or_create(
                            section=section_obj,
                            name=curso_code
                        )

                    # Construir nombre en formato "Apellidos Nombres"
                    p_ap = student.get('primer_apellido', '').strip()
                    s_ap = student.get('segundo_apellido', '').strip()
                    p_nm = student.get('primer_nombre', '').strip()
                    s_nm = student.get('segundo_nombre', '').strip()
                    apellidos = ' '.join(filter(None, [p_ap, s_ap]))
                    nombres = ' '.join(filter(None, [p_nm, s_nm]))
                    if apellidos and nombres:
                        full_name = f"{apellidos} {nombres}"
                    else:
                        full_name = student.get('nombre_completo', 'Sin Nombre')

                    Student.objects.update_or_create(
                        code=student.get('codigo_estudiante', ''),
                        defaults={
                            'full_name': full_name,
                            'email': student.get('email', ''),
                            'section': student.get('seccion', ''),
                            'grado': grado,
                            'course': course_obj,
                            'external_id': str(student.get('uuid', student.get('id', ''))),
                        }
                    )
                    count += 1

                    # Si el API ya trae foto de perfil, guardarla donde el template la espera.
                    foto_url = student.get('foto_perfil')
                    codigo = student.get('codigo_estudiante', '')
                    if foto_url and codigo:
                        Student._guardar_foto_perfil(codigo, foto_url)

                # Ir a la siguiente página
                url = data.get('next') if isinstance(data, dict) else None
                if url:
                    page += 1
                    print(f"Sincronizando pagina {page}... ({count} estudiantes procesados)")
                    # Usar la URL directa del siguiente link, sin params adicionales
                    params = {}

            print(f"[OK] Sincronizacion completada: {count} estudiantes")
            return count
        except Exception as e:
            print(f"[ERROR] Error sincronizando: {e}")
            import traceback
            traceback.print_exc()
            return 0

    @staticmethod
    def _guardar_foto_perfil(codigo, foto_url):
        """Descarga la foto de perfil del API y la guarda como {codigo}.jpg,
        que es la ruta que ya sirven las plantillas (/archivos/registro_fotografico/)."""
        import os
        import requests
        from PIL import Image
        from io import BytesIO
        from django.conf import settings

        try:
            resp = requests.get(foto_url, timeout=10, verify=False)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content)).convert('RGB')
            dest_dir = os.path.join(settings.BASE_DIR, 'archivos', 'registro_fotografico')
            os.makedirs(dest_dir, exist_ok=True)
            img.save(os.path.join(dest_dir, f'{codigo}.jpg'), 'JPEG', quality=85)
        except Exception as e:
            print(f"[WARN] No se pudo descargar la foto de {codigo}: {e}")

class ReportStatus(models.TextChoices):
    PROGRAMADO = 'PROGRAMADO', 'Programado'
    SEGUIMIENTO = 'SEGUIMIENTO', 'En Seguimiento'
    ATENDIDO = 'ATENDIDO', 'Atendido'

class ReportPurpose(models.TextChoices):
    CONVIVENCIA = 'CONVIVENCIA', 'Convivencia'
    ACADEMICO = 'ACADEMICO', 'Académico'
    ESPIRITUAL = 'ESPIRITUAL', 'Espiritual'
    PSICOAFECTIVO = 'PSICOAFECTIVO', 'Psicoafectivo'


class PeriodoAcademico(models.Model):
    """
    Los 4 períodos académicos del año con su rango de fechas. El período vigente
    se asigna automáticamente a cada reporte, observación y recomendación nueva
    según la fecha del día — el usuario NUNCA lo selecciona manualmente, para
    evitar errores. Se edita solo desde el panel de Educadores (exclusivo CAP).
    """
    NOMBRE_CHOICES = [
        ('Primer Periodo', 'Primer Periodo'),
        ('Segundo Periodo', 'Segundo Periodo'),
        ('Tercer Periodo', 'Tercer Periodo'),
        ('Cuarto Periodo', 'Cuarto Periodo'),
    ]
    nombre = models.CharField(max_length=50, choices=NOMBRE_CHOICES, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        ordering = ['fecha_inicio']
        verbose_name = "Período académico"
        verbose_name_plural = "Períodos académicos"

    def __str__(self):
        return f"{self.nombre} ({self.fecha_inicio:%d/%m/%Y} – {self.fecha_fin:%d/%m/%Y})"

    @classmethod
    def get_periodo_para_fecha(cls, fecha) -> str:
        """
        Período vigente para una fecha dada (hoy, o una fecha pasada para evidencia histórica):
        1. Si la fecha cae dentro del rango de un período, ese.
        2. Si cae en un vacío entre rangos (ej: vacaciones), el último período que ya empezó.
        3. Si nada se ha configurado todavía, 'Tercer Periodo' (valor de arranque).
        """
        periodos = list(cls.objects.order_by('fecha_inicio'))
        if not periodos:
            return 'Tercer Periodo'

        vigente = next((p for p in periodos if p.fecha_inicio <= fecha <= p.fecha_fin), None)
        if vigente:
            return vigente.nombre

        ya_empezados = [p for p in periodos if p.fecha_inicio <= fecha]
        if ya_empezados:
            return ya_empezados[-1].nombre

        return periodos[0].nombre

    @classmethod
    def get_periodo_actual(cls) -> str:
        """Período vigente hoy."""
        return cls.get_periodo_para_fecha(timezone.localdate())


class UserRole(models.TextChoices):
    ADMIN_GLOBAL = "ADMIN_GLOBAL", "Admin Global"
    ADMIN_SECCION = "ADMIN_SECCION", "Admin de Sección"


class Educador(models.Model):
    """Perfil de usuario con rol y alcance por sección."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='educador')
    rol = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.ADMIN_SECCION)
    seccion_asignada = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='educadores'
    )
    # Soporte multi-sección: reemplaza seccion_asignada (se mantiene por compatibilidad)
    secciones = models.ManyToManyField(
        Section,
        blank=True,
        related_name='educadores_m2m',
        verbose_name='Secciones asignadas'
    )
    fines_educativos = models.JSONField(default=list, blank=True)
    acceso_global = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__first_name", "user__last_name", "user__username"]
        verbose_name = "Educador"
        verbose_name_plural = "Educadores"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_rol_display()}"

class ScopePermiso(models.TextChoices):
    FIN_COMPLETO  = 'FIN_COMPLETO',  'Todo el fin (sin importar asignación)'
    SOLO_ASIGNADO = 'SOLO_ASIGNADO', 'Solo donde está asignado a mí'
    FIN_EQUIPO    = 'FIN_EQUIPO',    'Lo asignado a mí y a mi equipo del mismo fin'


class ReglaPermiso(models.Model):
    """
    Una regla de visibilidad para un educador.
    Cada educador puede tener N reglas; el acceso final es la UNIÓN (OR) de todas.

    fin_educativo vacío  = aplica a todos los fines
    seccion vacío        = aplica a todas las secciones
    """
    educador       = models.ForeignKey(
        Educador, on_delete=models.CASCADE, related_name='reglas'
    )
    fin_educativo  = models.CharField(
        max_length=20, blank=True,
        choices=[('', 'Todos los fines')] + [(c, l) for c, l in [
            ('ACADEMICO','Académico'), ('PSICOAFECTIVO','Psicoafectivo'),
            ('ESPIRITUAL','Espiritual'), ('CONVIVENCIA','Convivencia'),
        ]],
        help_text='Vacío = todos los fines'
    )
    seccion        = models.CharField(
        max_length=30, blank=True,
        choices=[('', 'Todas las secciones'),
                 ('preescolar',       'Jardín – Tercero'),
                 ('basica_primaria',  'Cuarto – Séptimo'),
                 ('basica_secundaria','Octavo – Undécimo')],
        help_text='Vacío = todas las secciones'
    )
    scope          = models.CharField(
        max_length=20, choices=ScopePermiso.choices, default=ScopePermiso.FIN_COMPLETO
    )

    class Meta:
        ordering  = ['educador', 'fin_educativo', 'seccion']
        verbose_name = 'Regla de permiso'
        verbose_name_plural = 'Reglas de permiso'

    def __str__(self):
        fin = self.fin_educativo or '*'
        sec = self.seccion or '*'
        return f"{self.educador.user.username} | fin={fin} sec={sec} scope={self.scope}"


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

    # Trazabilidad histórica
    year = models.IntegerField(default=2026, db_index=True)
    external_id = models.CharField(max_length=50, blank=True, db_index=True, help_text="ID del sistema origen (Power Apps)")

    created_at = models.DateTimeField(default=timezone.now)
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

    @property
    def created_by_display(self):
        return _user_display(self.created_by) or '—'

    @property
    def assigned_to_display(self):
        return _user_display(self.assigned_to) or 'Sin asignar'

    @property
    def is_closed(self):
        """True cuando el reporte ha sido atendido y tiene fecha de cierre."""
        return self.status == ReportStatus.ATENDIDO and self.fecha_cierre is not None

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
    academic_period = models.CharField(
        max_length=50, blank=True,
        help_text="Período académico vigente al momento de registrar esta observación (evidencia histórica)."
    )

    external_id = models.CharField(max_length=50, blank=True, db_index=True, help_text="ID origen Power Apps")
    date_log = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_log']
        verbose_name = 'Observación'
        verbose_name_plural = 'Observaciones'

    def __str__(self):
        return f"Observación {self.id} - {self.report.student.full_name}"

    @property
    def created_by_display(self):
        return _user_display(self.created_by) or 'Usuario'

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
    academic_period = models.CharField(
        max_length=50, blank=True,
        help_text="Período académico vigente al momento de registrar esta recomendación (evidencia histórica)."
    )
    external_id = models.CharField(max_length=50, blank=True, db_index=True, help_text="ID origen Power Apps")

    date_log = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_log']
        verbose_name = 'Recomendación'
        verbose_name_plural = 'Recomendaciones'

    def __str__(self):
        return f"Recomendación {self.id} - {self.report.student.full_name}"

    @property
    def created_by_display(self):
        return _user_display(self.created_by) or 'Usuario'


class AtencionHistorial(models.Model):
    """Historial de ciclos de atención. Cada vez que un coordinador reabre un
    caso cerrado se guarda aquí el ciclo anterior antes de resetear el reporte."""
    report        = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='historial_atenciones')
    atendido_por  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='historial_atenciones'
    )
    objetivo      = models.TextField(blank=True)
    periodo       = models.CharField(max_length=50, blank=True)
    fecha_inicio  = models.DateTimeField(null=True, blank=True)
    fecha_cierre  = models.DateTimeField(null=True, blank=True)
    cumple        = models.BooleanField(default=False)

    reabierto_por   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='casos_reabiertos'
    )
    fecha_reapertura = models.DateTimeField(auto_now_add=True)
    notas_reapertura = models.TextField(blank=True)

    class Meta:
        ordering = ['fecha_reapertura']
        verbose_name = 'Historial de atención'
        verbose_name_plural = 'Historial de atenciones'

    def __str__(self):
        atendido = self.atendido_por.get_full_name() if self.atendido_por else '—'
        return f"{self.report} | {atendido} | {self.fecha_cierre}"


class AuditoriaAccion(models.Model):
    """Evidencia para auditorías: quién cerró/reabrió/editó un reporte, o editó/eliminó
    una observación o recomendación — especialmente cuando actúa sobre trabajo de otro
    educador (ej: una coordinadora de sección editando una observación de su equipo)."""
    ACCION_CHOICES = [
        ('CERRAR',                 'Cerrar caso'),
        ('REABRIR',                'Reabrir caso'),
        ('EDITAR_REPORTE',         'Editar reporte'),
        ('EDITAR_OBSERVACION',     'Editar observación'),
        ('ELIMINAR_OBSERVACION',   'Eliminar observación'),
        ('EDITAR_RECOMENDACION',   'Editar recomendación'),
        ('ELIMINAR_RECOMENDACION', 'Eliminar recomendación'),
    ]
    report = models.ForeignKey(
        Report, on_delete=models.SET_NULL, null=True, blank=True, related_name='auditoria'
    )
    accion = models.CharField(max_length=30, choices=ACCION_CHOICES)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='acciones_auditoria'
    )
    autor_original = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
        help_text='Quién había creado el registro modificado o eliminado, si aplica'
    )
    estudiante_nombre = models.CharField(max_length=255, blank=True, help_text='Snapshot por si el reporte se elimina')
    detalle = models.TextField(blank=True, help_text='Contenido/estado antes del cambio')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Auditoría de acción'
        verbose_name_plural = 'Auditoría de acciones'

    def __str__(self):
        return f"{self.get_accion_display()} · {_user_display(self.actor)} · {self.creado_en:%Y-%m-%d %H:%M}"
