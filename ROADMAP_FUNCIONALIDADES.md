# Roadmap de Funcionalidades - SAI

## ✅ Mejoras UI Completadas

### Sidebar Mejorado
- [x] Color más claro (blanco en vez de azul oscuro)
- [x] Menús de sección colapsables (cerrados por defecto)
- [x] Sidebar colapsable a 80px con tooltips
- [x] Diseño más limpio y profesional
- [x] Un solo menú abierto a la vez (UX mejorado)

## 🎯 Funcionalidades Pendientes

### 1. Sistema de Reportería y Analytics

#### 1.1 Dashboard de Reportes (Nueva Vista)
**Ruta:** `/reports/analytics/`

**Filtros Principales:**
- Por Fin Educativo: Académico, Convivencia, Espiritual, Psicoafectivo
- Por Sección: Jardín a Tercero, Cuarto a Séptimo, Octavo a Undécimo
- Por Grado: Jardín, Transición, 1°, 2°, 3°, 4°, 5°, 6°, 7°, 8°, 9°, 10°, 11°
- Por Curso: JR01, TR01, 101, 102, ... 1103
- Por Docente: Todos los usuarios con reportes asignados
- Por Estado: PROGRAMADO, SEGUIMIENTO, ATENDIDO
- Por Rango de Fechas

**Visualizaciones:**
1. **Cards Principales:**
   - Total Reportes
   - Reportes Activos (PROGRAMADO + SEGUIMIENTO)
   - Reportes Atendidos
   - Estudiantes con Reportes
   - Promedio de Días de Atención

2. **Gráficos:**
   - Gráfico de barras: Reportes por Fin Educativo
   - Gráfico de pastel: Distribución por Estado
   - Gráfico de línea: Evolución de reportes en el tiempo
   - Tabla de calor: Reportes por Sección y Grado
   - Tabla: Top 10 Docentes con más reportes atendidos

3. **Exportación:**
   - Excel detallado (similar a Informe_Detallado_Acompañamiento_2026.xlsx)
   - PDF con gráficos
   - CSV para análisis externo

#### 1.2 Estructura del Reporte Excel
```
Columnas:
- ID Reporte
- Estudiante (Nombre completo)
- Código Estudiante
- Curso
- Sección
- Grado
- Fin Educativo
- Objetivo
- Estado
- Fecha Creación
- Fecha Última Actualización
- Días Activo
- Remitente (Docente)
- Encargado (Docente)
- N° Observaciones
- N° Recomendaciones
- Cumplió Objetivo (Sí/No)
```

### 2. Sistema de Alertas y Notificaciones

#### 2.1 Alertas Automáticas
**Tipos de Alertas:**

1. **Alerta de Inactividad (3 días):**
   - Cuando un reporte es creado pero pasan 3 días sin observaciones/recomendaciones
   - Notificar al docente encargado
   - Notificar al coordinador/administrador

2. **Alerta de Seguimiento Prolongado (15 días):**
   - Cuando un reporte está en SEGUIMIENTO por más de 15 días
   - Sugerir revisión del caso

3. **Alerta de Reporte Sin Asignar:**
   - Cuando un reporte no tiene docente encargado
   - Notificar inmediatamente a coordinación

#### 2.2 Centro de Notificaciones
**Ubicación:** Icono de campana en navbar

**Características:**
- Badge con número de notificaciones sin leer
- Panel desplegable con lista de notificaciones
- Tipos de notificación:
  - 🔴 Urgente (reporte sin atender por 3+ días)
  - 🟡 Recordatorio (seguimiento prolongado)
  - 🔵 Información (nuevo reporte asignado)
- Marcar como leída
- Ver todas las notificaciones
- Filtrar por tipo

#### 2.3 Modelo de Notificación
```python
# acompanamiento/models.py
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('INACTIVITY', 'Reporte Inactivo'),
        ('PROLONGED', 'Seguimiento Prolongado'),
        ('UNASSIGNED', 'Sin Asignar'),
        ('NEW_ASSIGNMENT', 'Nueva Asignación'),
    ]

    PRIORITY = [
        ('HIGH', 'Alta'),
        ('MEDIUM', 'Media'),
        ('LOW', 'Baja'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 2.4 Tarea Programada (Celery)
```python
# acompanamiento/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task
def check_inactive_reports():
    """
    Ejecutar diariamente para detectar reportes inactivos
    """
    three_days_ago = timezone.now() - timedelta(days=3)

    # Reportes creados hace 3+ días sin observaciones
    inactive_reports = Report.objects.filter(
        created_at__lte=three_days_ago,
        observations__isnull=True,
        recommendations__isnull=True
    ).exclude(status='ATENDIDO')

    for report in inactive_reports:
        # Crear notificación para encargado
        Notification.objects.create(
            user=report.assigned_to,
            report=report,
            notification_type='INACTIVITY',
            priority='HIGH',
            message=f'El reporte del estudiante {report.student.full_name} lleva {(timezone.now() - report.created_at).days} días sin seguimiento.'
        )
```

### 3. Mejoras Adicionales UX

#### 3.1 Búsqueda Avanzada
- Buscador global en navbar
- Búsqueda por nombre de estudiante, código, curso
- Búsqueda por contenido de observaciones/recomendaciones
- Filtros rápidos combinables

#### 3.2 Vista de Calendario
- Ver reportes en calendario mensual
- Marcar fechas de seguimiento programadas
- Vista de agenda del docente

#### 3.3 Historial de Actividad
- Log de todos los cambios en un reporte
- Quién hizo qué cambio y cuándo
- Auditoría completa

#### 3.4 Exportación Individual
- Generar PDF del reporte individual
- Incluir foto del estudiante
- Incluir todas las observaciones/recomendaciones
- Formato profesional para entregar a padres

### 4. Reportes Específicos por Rol

#### 4.1 Vista de Docente
- Mis reportes asignados
- Mis reportes pendientes
- Mis reportes atendidos
- Estadísticas personales

#### 4.2 Vista de Coordinador
- Todos los reportes de su sección
- Resumen de docentes y desempeño
- Casos críticos que requieren atención

#### 4.3 Vista de Administrador
- Vista global de toda la institución
- Comparativas entre secciones
- Tendencias y análisis predictivo

## 🔧 Implementación Técnica

### Fase 1: Reportería Básica (2-3 días)
1. Crear vista `/reports/analytics/`
2. Implementar filtros básicos
3. Cards con estadísticas principales
4. Exportación a Excel básica

### Fase 2: Sistema de Notificaciones (3-4 días)
1. Crear modelo Notification
2. Implementar centro de notificaciones en navbar
3. Crear tarea Celery para alertas automáticas
4. Configurar Celery Beat para ejecutar diariamente

### Fase 3: Visualizaciones Avanzadas (2-3 días)
1. Integrar librería de gráficos (Chart.js o Plotly)
2. Implementar gráficos interactivos
3. Mejorar exportación Excel con formato

### Fase 4: Mejoras UX (2-3 días)
1. Búsqueda avanzada global
2. Vista de calendario
3. Exportación PDF individual
4. Historial de actividad

## 📊 Métricas de Éxito

- Reducir tiempo promedio de atención de reportes
- Aumentar tasa de reportes atendidos a tiempo
- Mejorar satisfacción de docentes (encuesta)
- Reducir reportes sin seguimiento a 0%

## 🚀 Próximos Pasos Inmediatos

1. ¿Quieres que empiece con el **Sistema de Reportería** o el **Sistema de Alertas**?
2. ¿Necesitas alguna funcionalidad adicional no mencionada aquí?
3. ¿Tienes alguna preferencia sobre el orden de implementación?
