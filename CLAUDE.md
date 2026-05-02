# Sistema de Acompañamiento Integral (SAI)

## Descripción del Proyecto

Sistema web desarrollado en Django para gestionar el acompañamiento y seguimiento de estudiantes. Permite crear reportes, gestionar observaciones y recomendaciones, y hacer seguimiento de casos educativos.

## Estructura del Proyecto

```
Sistema_acompañamiento_integral/
├── archivos/              # Archivos multimedia y fotos de estudiantes
│   └── registro_fotografico/  # Fotos de perfil de estudiantes
├── config/                # Configuración de Django
│   ├── settings.py        # Configuración principal
│   ├── urls.py            # Rutas principales
│   ├── wsgi.py
│   └── asgi.py
├── estudiantes/           # App Django para gestión de estudiantes
│   ├── models.py          # Modelos de estudiantes
│   ├── views.py           # Vistas
│   ├── urls.py           # Rutas
│   └── ...
├── acompanamiento/       # App Django para reportes y acompañamiento
│   ├── models.py          # Modelos de Report, Observation, Recommendation
│   ├── views.py           # Vistas de reportes
│   ├── urls.py           # Rutas
│   └── serializers.py    # Serializers API
├── templates/             # Plantillas HTML
│   ├── base.html         # Plantilla base
│   ├── dashboard.html    # Dashboard principal
│   └── estudiantes/
│       └── student_list.html  # Lista de estudiantes con workspace
├── scripts/              # Scripts de gestión y mantenimiento
├── data/                 # Datos de ejemplo
└── venv/                 # Entorno virtual Python
```

## Tecnologías

- **Backend**: Django 5.x (Python 3.13)
- **Base de datos**: SQLite (configurable a PostgreSQL)
- **Frontend**: HTML + Tailwind CSS + JavaScript vanilla
- **Iconos**: Font Awesome 6.4
- **Fuentes**: Google Fonts (Outfit)

## Configuración del Proyecto

### Variables de Entorno (.env)

```env
SECRET_KEY=your-secret-key
DEBUG=True
DB_ENGINE=sqlite  # o postgresql
GESTOR_EDUCATIVO_URL=http://localhost:8000
GESTOR_EDUCATIVO_API_KEY=your-api-key
```

### Ejecutar el Proyecto

```bash
# Activar entorno virtual
cd Sistema_acompañamiento_integral
source venv/Scripts/activate

# Migrar base de datos
python manage.py migrate

# Iniciar servidor
python manage.py runserver 8005
```

## Rutas Principales

| Ruta | Descripción |
|------|-------------|
| `/` | Dashboard principal |
| `/students/` | Lista de estudiantes por curso/sección |
| `/students/?section=XXX&course=YYY` | Filtrar estudiantes por curso |
| `/reports/` | Lista de reportes |

## Modelos Principales

### StudentCache (estudiantes/models.py)
- `external_id`: ID externo del estudiante
- `full_name`: Nombre completo
- `code`: Código del estudiante
- `course`: Curso
- `section`: Sección

### Report (acompanamiento/models.py)
- `student`: Relación con estudiante
- `purpose`: Fin educativo (Académico, Convivencia, Espiritual, Psicoafectivo)
- `status`: Estado (PENDIENTE, EN_PROCESO, ATENDIDO)
- `objective`: Objetivo del acompañamiento
- `created_by`: Usuario que crea el reporte
- `assigned_to`: Usuario encargado

### Observation (acompanamiento/models.py)
- `report`: Relación con reporte
- `content`: Contenido de la observación
- `followup_date`: Fecha de seguimiento
- `created_by`: Creador

### Recommendation (acompanamiento/models.py)
- Similar a Observation pero para recomendaciones

## Características del UI

### student_list.html - Workspace de Reportes

El archivo `templates/estudiantes/student_list.html` contiene:

1. **Grid de Tarjetas de Estudiantes**
   - Muestra estudiantes en grid responsivo (1-5 columnas)
   - Foto de perfil (cargada desde `/archivos/registro_fotografico/`)
   - Información básica y reportes del estudiante

2. **Workspace Panel (detalle del reporte)**
   - Diseño de dos columnas:
     - Columna izquierda (3/12): Perfil del estudiante
     - Columna derecha (9/12): Detalles del reporte
   - Tipografía mejorada para accesibilidad
   - Mejor contraste y tamaños de fuente

3. **Modales**
   - Crear reporte
   - Editar observación
   - Editar recomendación

### Fotos de Perfil

Las fotos se cargan desde: `/archivos/registro_fotografico/{codigo}.jpg`

Si no existe la foto, se muestra la inicial del nombre del estudiante.

## Estilos y Accesibilidad

- Tipografía: Outfit (Google Fonts)
- Colores principales: #2256F2 (azul institucional)
- Contraste mejorado para accesibilidad
- Tamaños de fuente más grandes para mejor lectura
- Iconos de Font Awesome

## Notas de Desarrollo

- El proyecto usa Tailwind CSS vía CDN (no recomendado para producción)
- Las imágenes estáticas se sirven en DEBUG mode desde `/archivos/`
- El sistema está configurado para sincronizar estudiantes desde una API externa
- Los reportes tienen soporte para observaciones y recomendaciones con seguimiento