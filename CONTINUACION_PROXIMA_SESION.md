# 📋 CONTINUACIÓN PRÓXIMA SESIÓN - SAI (Sistema de Acompañamiento Integral)

## 📍 ESTADO ACTUAL (29 Abril 2026)

### ✅ LO QUE YA ESTÁ HECHO

**FASE 1: Estructura Base Django**
- ✅ Proyecto Django creado con 2 apps (acompanamiento, estudiantes)
- ✅ Migraciones completadas sin errores
- ✅ Base de datos SQLite lista (db.sqlite3)
- ✅ Admin Django configurado

**FASE 2: Modelos Expandidos**
- ✅ Modelos replicados del Power Apps original:
  - Section (con grado: Preescolar, Primaria, Bachillerato)
  - Course
  - Student (con imagen, grado, created_at, sincronización desde API)
  - Report (con imagen, recuento, fecha_cierre, validación de reportes activos)
  - Observation (con correo_institucional, cambio automático de estado)
  - Recommendation (con correo_institucional)

**FASE 3: API REST Completa**
- ✅ Serializers completos (DRF)
- ✅ ViewSets para todos los modelos
- ✅ Endpoints REST listos para consumir
- ✅ Filtros, búsqueda, paginación implementados
- ✅ Validaciones de negocio

**FASE 4: Configuración**
- ✅ PostgreSQL configurado (comentado, listo para activar)
- ✅ `.env` con variables de configuración
- ✅ REST Framework configurado
- ✅ CORS configurado

---

## 🎯 PRÓXIMOS PASOS (ORDEN RECOMENDADO)

### **PASO 1: AUTENTICACIÓN + ROLES** ⭐ PRIORIDAD 1
Este es el siguiente paso CRÍTICO que debes hacer en la próxima sesión.

**Qué hacer:**
1. Crear modelo `Rol` (DOCENTE, COORDINADOR, ADMIN_GLOBAL)
2. Extender modelo `User` con campos:
   - `role` (Rol del usuario)
   - `assigned_section` (Sección asignada - para coordinadores/docentes)
   - `assigned_purpose` (Fin educativo específico - opcional para docentes)
3. Actualizar `ReportViewSet.get_queryset()` para filtrar por rol/sección
4. Implementar permisos personalizados

**Archivos a modificar:**
- `acompanamiento/models.py` → Agregar modelo Rol
- `acompanamiento/views.py` → Actualizar `ReportViewSet.get_queryset()`
- `acompanamiento/serializers.py` → Agregar `RolSerializer`

**Resultado esperado:**
- Los docentes solo ven reportes de su sección
- Los coordinadores solo ven su sección
- Los admins ven todo
- Las observaciones/recomendaciones se crean automáticamente con el usuario actual

---

### **PASO 2: AUTENTICACIÓN OAUTH MICROSOFT** ⭐ PRIORIDAD 2
Después que roles esté listo.

**Qué hacer:**
1. Instalar `django-allauth` o `python-social-auth`
2. Configurar OAuth endpoints de Microsoft
3. Crear vistas de login/logout
4. Crear superusuario automáticamente si no existe

**Resultado esperado:**
- Login con Microsoft 365
- Usuario se crea automáticamente con su rol
- Token de sesión

---

### **PASO 3: FRONTEND REACT/HTMX** ⭐ PRIORIDAD 3
Interfaz para consumir la API.

**Pantallas a crear:**
1. Login (si es OAuth)
2. Dashboard (estadísticas, selector de sección)
3. Lista de Reportes (filtrable por estado, fin educativo)
4. Crear Reporte (modal o página)
5. Detalle de Reporte (con observaciones/recomendaciones anidadas)
6. Agregar Observación/Recomendación
7. Admin (gestionar secciones, cursos, estudiantes)

**Stack sugerido:**
- React + TypeScript
- Axios para consumir API
- React Query para estado
- Tailwind CSS para estilos
- React Router para navegación

---

### **PASO 4: INTEGRACIONES ADICIONALES** ⭐ PRIORIDAD 4

- Email notifications
- Export a PDF/Excel
- Historial de cambios (audit log)
- Búsqueda avanzada
- Reportes/analytics

---

## 📋 CHECKLIST PARA PRÓXIMA SESIÓN

### Antes de empezar
- [ ] Verificar que PostgreSQL esté disponible (si quieres usarlo)
- [ ] Ejecutar servidor: `python manage.py runserver 0.0.0.0:8005`
- [ ] Crear superusuario: `python manage.py createsuperuser`
- [ ] Acceder a admin: http://localhost:8005/admin/

### Paso 1: Roles (DEBE HACERSE)
- [ ] Crear modelo `Rol` en `models.py`
- [ ] Extender modelo `User` (o crear modelo `UserProfile`)
- [ ] Actualizar `ReportViewSet.get_queryset()`
- [ ] Hacer migraciones: `python manage.py makemigrations && python manage.py migrate`
- [ ] Probar API con filtros

### Paso 2: OAuth Microsoft (OPCIONAL, pero recomendado)
- [ ] Instalar `django-allauth`
- [ ] Configurar en `settings.py`
- [ ] Crear vistas de login/logout
- [ ] Registrar app en Azure

### Paso 3: Frontend (CUANDO ESTÉ LISTO)
- [ ] Crear proyecto React
- [ ] Consumir API
- [ ] Crear pantallas

---

## 🛠️ COMANDOS ÚTILES PARA PRÓXIMA SESIÓN

```bash
# Activar ambiente virtual
.\venv\Scripts\activate

# Instalar dependencias (si es necesario)
pip install -r requirements.txt

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver 0.0.0.0:8005

# Acceder a API
# http://localhost:8005/acompanamiento/api/

# Ver admin
# http://localhost:8005/admin/

# Crear datos de prueba (si lo necesitas)
python manage.py shell
```

---

## 📂 ESTRUCTURA ACTUAL DEL PROYECTO

```
Sistema_acompañamiento_integral/
├── config/                          # Configuración principal
│   ├── settings.py                  # ✅ Actualizado con PostgreSQL + REST Framework
│   ├── urls.py                      # URLs principales
│   ├── wsgi.py
│   └── asgi.py
├── acompanamiento/                  # App principal
│   ├── models.py                    # ✅ Modelos expandidos
│   ├── views.py                     # ✅ ViewSets REST
│   ├── serializers.py               # ✅ NUEVO - Serializers DRF
│   ├── urls.py                      # ✅ Router API
│   ├── admin.py                     # Admin Django
│   └── migrations/
├── estudiantes/                     # App de estudiantes
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
├── templates/                       # Templates HTML
├── static/                          # Static files
├── manage.py                        # Django CLI
├── requirements.txt                 # ✅ Dependencias actualizadas
├── .env                             # ✅ NUEVO - Variables de entorno
├── db.sqlite3                       # Base de datos actual
├── IMPLEMENTACION_DJANGO.md         # ✅ Documentación de lo hecho
└── CONTINUACION_PROXIMA_SESION.md   # ✅ Este archivo

```

---

## 📱 ENDPOINTS ACTUALES (YA FUNCIONALES)

### Reportes
```
GET    /acompanamiento/api/reportes/
POST   /acompanamiento/api/reportes/
GET    /acompanamiento/api/reportes/{id}/
PATCH  /acompanamiento/api/reportes/{id}/
DELETE /acompanamiento/api/reportes/{id}/
POST   /acompanamiento/api/reportes/{id}/cerrar/
GET    /acompanamiento/api/reportes/{id}/observaciones/
POST   /acompanamiento/api/reportes/{id}/observaciones/
GET    /acompanamiento/api/reportes/{id}/recomendaciones/
POST   /acompanamiento/api/reportes/{id}/recomendaciones/
```

### Estudiantes
```
GET    /acompanamiento/api/estudiantes/
GET    /acompanamiento/api/estudiantes/{id}/
POST   /acompanamiento/api/estudiantes/sync_from_api/
```

### Observaciones
```
GET    /acompanamiento/api/observaciones/
POST   /acompanamiento/api/observaciones/
GET    /acompanamiento/api/observaciones/{id}/
PATCH  /acompanamiento/api/observaciones/{id}/
DELETE /acompanamiento/api/observaciones/{id}/
```

### Recomendaciones
```
GET    /acompanamiento/api/recomendaciones/
POST   /acompanamiento/api/recomendaciones/
GET    /acompanamiento/api/recomendaciones/{id}/
PATCH  /acompanamiento/api/recomendaciones/{id}/
DELETE /acompanamiento/api/recomendaciones/{id}/
```

---

## 🔐 NOTAS IMPORTANTES

### PostgreSQL
- Actualmente en SQLite (para desarrollo rápido)
- Para cambiar a PostgreSQL:
  1. Descomentar sección `DATABASES` en `settings.py` (línea ~61)
  2. Actualizar `.env` con credenciales reales
  3. Crear BD: `CREATE DATABASE sai_db;`
  4. Ejecutar: `python manage.py migrate`

### Validaciones Implementadas
- ✅ Un reporte ACTIVO por estudiante + fin educativo (constraint en DB)
- ✅ Cambio automático de estado PROGRAMADO → SEGUIMIENTO
- ✅ Auto-actualización de recuento de observaciones
- ✅ Email institucional registrado en observaciones/recomendaciones

### Sincronización de Estudiantes
- ✅ Endpoint: `POST /acompanamiento/api/estudiantes/sync_from_api/`
- ✅ Conecta con: `http://localhost:8000/api/v1/estudiantes/`
- ✅ API Key: `9eCn5gSX.x4Lmirq095PCBQIWPDqKtlsF494B2J98`

---

## 🎓 REFERENCIA RÁPIDA - PRÓXIMA SESIÓN

**Si vas a implementar ROLES (PASO 1):**

```python
# En models.py agregar:
class Rol(models.TextChoices):
    DOCENTE = 'DOCENTE', 'Docente'
    COORDINADOR = 'COORDINADOR', 'Coordinador'
    ADMIN_GLOBAL = 'ADMIN_GLOBAL', 'Admin Global'

# Extender User (opción 1: UserProfile)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Rol.choices)
    assigned_section = models.ForeignKey(Section, null=True, blank=True)
    assigned_purpose = models.CharField(max_length=50, blank=True)

# O extender User (opción 2: uso directo con AbstractUser)
# Depende de si ya hay usuarios en BD
```

```python
# En views.py actualizar ReportViewSet:
def get_queryset(self):
    user = self.request.user
    if user.is_staff or user.is_superuser:
        return Report.objects.all()

    # Si tiene rol asignado
    profile = user.userprofile
    if profile.role == Rol.ADMIN_GLOBAL:
        return Report.objects.all()
    elif profile.role in [Rol.COORDINADOR, Rol.DOCENTE]:
        return Report.objects.filter(
            student__course__section=profile.assigned_section
        )
    return Report.objects.none()
```

---

## 💾 COPIA DE SEGURIDAD

**Archivos clave a respaldar:**
- `acompanamiento/models.py` ✅
- `acompanamiento/views.py` ✅
- `acompanamiento/serializers.py` ✅
- `acompanamiento/urls.py` ✅
- `config/settings.py` ✅
- `.env` (NO compartir)
- `db.sqlite3` (opcional, se puede regenerar)

**Git status actual:**
```
M  requirements.txt
M  config/settings.py
M  acompanamiento/models.py
M  acompanamiento/views.py
M  acompanamiento/urls.py
A  acompanamiento/serializers.py
A  .env
A  IMPLEMENTACION_DJANGO.md
A  CONTINUACION_PROXIMA_SESION.md (este archivo)
```

**Sugiero hacer commit antes de cerrar:**
```bash
git add .
git commit -m "feat: Implementar API REST completa con modelos expandidos para PostgreSQL"
```

---

## 📞 TROUBLESHOOTING RÁPIDO

### Si PostgreSQL no conecta
→ Cambiar a SQLite (ya configurado)

### Si las migraciones fallan
→ Ejecutar `python manage.py migrate --fake-initial`

### Si hay conflicto de puertos
→ Cambiar puerto: `python manage.py runserver 0.0.0.0:8006`

### Si falta superusuario
→ `python manage.py createsuperuser`

### Si falta alguna dependencia
→ `pip install -r requirements.txt`

---

## 📊 PRÓXIMA SESIÓN - TIMELINE ESTIMADO

| Tarea | Tiempo Estimado | Complejidad |
|-------|-----------------|------------|
| Roles + Permisos | ~45 min | Media |
| OAuth Microsoft | ~60 min | Alta |
| Frontend React (básico) | ~120+ min | Alta |
| Testing | ~30 min | Media |

---

## ✨ RESUMEN EN UNA LÍNEA

**Ya tienes:** API REST 100% funcional con modelos replicados del Power Apps original.
**Siguiente:** Agregar autenticación + roles para control de acceso.

---

**Actualizado:** 29 Abril 2026
**Autor:** Claude (Haiku 4.5)
**Estado:** Listo para continuar en próxima sesión ✅
