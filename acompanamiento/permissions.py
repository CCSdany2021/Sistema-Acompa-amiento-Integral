"""
Helpers de permisos para el SAI.
El acceso de cada educador se determina por sus ReglaPermiso (OR de todas las reglas).
Si no tiene reglas, cae en lógica legacy (seccion_asignada + fines_educativos).
"""
from django.db.models import Q, QuerySet


# Mapea cualquier nombre de sección → valores reales de Student.section
SECTION_NAME_TO_STUDENT_SECTION = {
    'preescolar':        ['preescolar'],
    'basica_primaria':   ['basica_primaria'],
    'basica_secundaria': ['basica_secundaria', 'media_academica'],
    'media_academica':   ['basica_secundaria', 'media_academica'],
    # Nombres legacy en Section.name
    'Jardin Tercero':    ['preescolar'],
    'Jardin–Tercero':    ['preescolar'],
    'Jardín–Tercero':    ['preescolar'],
    'Cuarto Septimo':    ['basica_primaria'],
    'Cuarto–Séptimo':    ['basica_primaria'],
    'Cuarto Séptimo':    ['basica_primaria'],
    'Octavo Undecimo':   ['basica_secundaria', 'media_academica'],
    'Octavo–Undécimo':   ['basica_secundaria', 'media_academica'],
    'Octavo Undécimo':   ['basica_secundaria', 'media_academica'],
}

SECTION_KEY_MAP = {k: v for k, v in SECTION_NAME_TO_STUDENT_SECTION.items()}

# Cursos que integran cada una de las 3 secciones institucionales del SAI
# (Jardín a Tercero, Cuarto a Séptimo, Octavo a Undécimo). Es la fuente única de
# verdad — estudiantes/views.py la reutiliza para armar INSTITUTIONAL_STRUCTURE.
# No coincide 1:1 con Student.section (clasificación del sistema externo, que
# separa preescolar/basica_primaria/basica_secundaria/media_academica): los
# cursos 101-302 llegan sincronizados como 'basica_primaria' y 601-703 como
# 'basica_secundaria', aunque institucionalmente sean parte de otra sección.
SECTION_KEY_COURSES = {
    'preescolar':        ['JR01', 'TR01', 'TR02', '101', '102', '201', '202', '301', '302'],
    'basica_primaria':   ['401', '402', '501', '502', '503', '601', '602', '603', '701', '702', '703'],
    'basica_secundaria': ['801', '802', '803', '901', '902', '903', '1001', '1002', '1003', '1101', '1102', '1103'],
}


def _get_educador(user):
    if not user or not user.is_authenticated:
        return None
    try:
        return user.educador
    except Exception:
        return None


def has_global_access(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    if user.email in _CAP_ONLY:
        # Garantiza acceso global de CAP (crear/editar/eliminar en todo el sistema)
        # sin depender de que el flag acceso_global esté marcado en el perfil Educador.
        return True
    ed = _get_educador(user)
    return ed is not None and ed.acceso_global


_SUPER_ADMIN_EMAILS = {'cap@calasanzsuba.edu.co'}
_CAP_ONLY           = {'cap@calasanzsuba.edu.co'}
_GLOBAL_INDICATOR_EMAILS = {'cap@calasanzsuba.edu.co', 'mrodriguez@calasanzsuba.edu.co', 'dhiguera@calasanzsuba.edu.co', 'pvasquez@calasanzsuba.edu.co'}

# Coordinadoras de sección con potestad para reabrir/cerrar/editar reportes y
# editar/eliminar observaciones o recomendaciones de otros educadores — pero
# SOLO dentro de su propia sección. cap y mrodriguez ya tienen acceso_global=True
# y no necesitan estar aquí. Ninguna otra cuenta (aunque tenga una ReglaPermiso
# amplia) obtiene esta potestad.
_SECTION_COORDINATOR_SECTIONS = {
    'mpedraza@calasanzsuba.edu.co': ['preescolar'],
    'yalejo@calasanzsuba.edu.co':   ['basica_secundaria', 'media_academica'],
}

# Cuentas con acceso completo al Simulador de Vistas (además de super-admin/cap):
# pueden entrar y activar la simulación para ver el sistema como otro usuario.
_SIMULATOR_COORDINATOR_EMAILS = {
    'mrodriguez@calasanzsuba.edu.co',
    'mpedraza@calasanzsuba.edu.co',
    'yalejo@calasanzsuba.edu.co',
    'dhiguera@calasanzsuba.edu.co',
    'pvasquez@calasanzsuba.edu.co',
}

# Únicas cuentas habilitadas para ELIMINAR observaciones, recomendaciones o
# reportes. Ser el creador o coordinador de sección (can_manage_report) ya no
# habilita para eliminar, solo para editar — esa es la diferencia clave con
# _check_can_edit. Ninguna otra cuenta puede eliminar, sin excepción.
_DELETE_AUTHORIZED_EMAILS = {
    'mrodriguez@calasanzsuba.edu.co',
    'yalejo@calasanzsuba.edu.co',
    'mpedraza@calasanzsuba.edu.co',
    'cap@calasanzsuba.edu.co',
    'dhiguera@calasanzsuba.edu.co',
}


def resolve_real_user(request):
    """Siempre devuelve el usuario Django real de la sesión (nunca el simulado)."""
    from django.contrib.auth import get_user_model
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        return user
    User = get_user_model()
    return (
        User.objects.filter(is_superuser=True, is_active=True).first()
        or User.objects.filter(is_staff=True, is_active=True).first()
        or User.objects.filter(is_active=True).first()
    )


def can_simulate(user) -> bool:
    """Super-admin y coordinadoras/es habilitados pueden activar la simulación."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.email in _SUPER_ADMIN_EMAILS or user.email in _SIMULATOR_COORDINATOR_EMAILS


def get_simulator_allowed_sections(user) -> list | None:
    """
    Restringe el listado de usuarios que se muestra en el Simulador de Vistas.
    - None  → sin restricción, ve el listado completo.
    - lista → solo ve educadores asignados a estas secciones (valores reales de Student.section).
    Reutiliza el mismo mapeo de _SECTION_COORDINATOR_SECTIONS (mpedraza, yalejo).
    """
    if not user or not user.is_authenticated:
        return []
    return _SECTION_COORDINATOR_SECTIONS.get(user.email)


def _educador_student_sections(ed) -> set:
    names = list(ed.secciones.values_list('name', flat=True))
    if not names and ed.seccion_asignada_id:
        names = [ed.seccion_asignada.name]
    student_secs = set()
    for n in names:
        student_secs.update(SECTION_NAME_TO_STUDENT_SECTION.get(n, [n]))
    return student_secs


def can_simulate_target(real_user, target_user) -> bool:
    """
    True si real_user puede activar la simulación como target_user.
    Refuerza en el backend la misma restricción de sección que se aplica
    al listado del Simulador (mpedraza/yalejo solo su sección).
    """
    if not can_simulate(real_user):
        return False
    allowed_sections = get_simulator_allowed_sections(real_user)
    if allowed_sections is None:
        return True
    ed = _get_educador(target_user)
    if not ed:
        return False
    return bool(_educador_student_sections(ed) & set(allowed_sections))


def resolve_viewer(request):
    """
    Resuelve el usuario activo para filtros y vistas.
    Si hay simulación activa Y el usuario real es super-admin, devuelve el usuario simulado.
    """
    from django.contrib.auth import get_user_model
    real_user = resolve_real_user(request)

    # Simulación activa: solo si el usuario real tiene permiso
    if can_simulate(real_user):
        sim_id = getattr(request, 'session', {}).get('simulated_user_id')
        if sim_id:
            User = get_user_model()
            sim_user = User.objects.filter(pk=sim_id, is_active=True).first()
            if sim_user:
                return sim_user

    return real_user


def _section_q(seccion_value: str) -> Q:
    """Construye Q de sección. Prioriza la lista de cursos de la sección
    institucional (SECTION_KEY_COURSES); si seccion_value no es una de esas 3
    claves, cae al campo legacy Student.section."""
    if not seccion_value:
        return Q()
    courses = SECTION_KEY_COURSES.get(seccion_value)
    if courses:
        return Q(student__course__name__in=courses)
    student_sections = SECTION_NAME_TO_STUDENT_SECTION.get(seccion_value, [seccion_value])
    return Q(student__section__in=student_sections)


def _fin_team_users(fin_educativo: str):
    """Retorna IDs de usuarios que tienen ReglaPermiso para ese fin."""
    from .models import ReglaPermiso
    return list(
        ReglaPermiso.objects
        .filter(fin_educativo=fin_educativo)
        .values_list('educador__user_id', flat=True)
        .distinct()
    )


def _q_for_regla(regla, user) -> Q:
    """Construye el Q para una sola ReglaPermiso."""
    q = Q()

    # Filtro de sección
    if regla.seccion:
        q &= _section_q(regla.seccion)

    # Filtro de fin educativo
    if regla.fin_educativo:
        q &= Q(purpose=regla.fin_educativo)

    # Filtro de scope
    if regla.scope == 'SOLO_ASIGNADO':
        q &= Q(assigned_to=user)
    elif regla.scope == 'FIN_EQUIPO':
        fin = regla.fin_educativo
        if fin:
            team_ids = _fin_team_users(fin)
            q &= Q(assigned_to__in=team_ids)
        # Sin fin específico → no restringir por assigned_to (equivale a FIN_COMPLETO)
    # FIN_COMPLETO → no filtro adicional en assigned_to

    return q


def can_manage_report(user, report) -> bool:
    """True si el usuario puede reabrir/cerrar/editar este reporte puntual, o
    editar/eliminar observaciones y recomendaciones de otros educadores en él.

    Solo: acceso_global (cap, mrodriguez) O coordinadoras de sección explícitas
    (mpedraza, yalejo) actuando dentro de su propia sección. Ninguna otra cuenta
    —aunque tenga una ReglaPermiso amplia (ej: fin_educativo sin sección)— tiene
    esta potestad.
    """
    if not user or not user.is_authenticated:
        return False
    if has_global_access(user):
        return True
    sections = _SECTION_COORDINATOR_SECTIONS.get(user.email)
    if not sections:
        return False
    courses = set()
    for sec in sections:
        courses.update(SECTION_KEY_COURSES.get(sec, []))
    if courses:
        return bool(report.student.course_id and report.student.course.name in courses)
    return bool(report.student.section in sections)


def can_delete_content(user) -> bool:
    """True solo si el usuario es una de las cuentas explícitamente autorizadas
    para eliminar observaciones, recomendaciones o reportes (_DELETE_AUTHORIZED_EMAILS).

    A diferencia de can_manage_report/_check_can_edit, ser el creador del
    contenido o coordinador de sección NO habilita para eliminar — solo para
    editar. Eliminar es una potestad aparte, reservada a estas cuentas.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.email in _DELETE_AUTHORIZED_EMAILS


def filter_reports_for_user(qs: QuerySet, user) -> QuerySet:
    """
    Filtra un QuerySet de Report según el perfil del educador.

    Prioridad:
      1. acceso_global / superuser → todo sin restricción
      2. Tiene ReglaPermiso → OR de todas las reglas
      3. Legacy (seccion_asignada + fines_educativos) → compatibilidad
      4. Sin nada → solo assigned_to = user
    """
    if not user or not user.is_authenticated:
        return qs.none()

    if has_global_access(user):
        return qs

    ed = _get_educador(user)
    if not ed:
        return qs.filter(assigned_to=user)

    # ── Modo ReglaPermiso ──────────────────────────────────────────────────────
    reglas = list(ed.reglas.all())
    if reglas:
        combined = Q(pk__in=[])  # vacío inicial
        for regla in reglas:
            combined |= _q_for_regla(regla, user)
        return qs.filter(combined).distinct()

    # ── Modo legacy (sin reglas configuradas) ─────────────────────────────────
    section_names = list(ed.secciones.values_list('name', flat=True))
    if not section_names and ed.seccion_asignada:
        section_names = [ed.seccion_asignada.name]

    if section_names:
        student_sections = set()
        for name in section_names:
            student_sections.update(SECTION_NAME_TO_STUDENT_SECTION.get(name, [name]))
        qs = qs.filter(student__section__in=list(student_sections))
        if ed.fines_educativos:
            qs = qs.filter(purpose__in=ed.fines_educativos)
        return qs

    return qs.filter(assigned_to=user)


# ── Helpers legacy (usados en otros lugares) ──────────────────────────────────

def get_allowed_section_names(user) -> list | None:
    if has_global_access(user):
        return None
    ed = _get_educador(user)
    if not ed:
        return []
    secs = list(ed.secciones.values_list('name', flat=True))
    if not secs and ed.seccion_asignada:
        secs = [ed.seccion_asignada.name]
    return secs if secs else []


def get_allowed_fines(user) -> list | None:
    """
    Devuelve los fines educativos que el viewer puede ver.
    - None       → todos (acceso global o regla sin fin específico)
    - lista      → solo esos fines (ej: ['CONVIVENCIA', 'PSICOAFECTIVO'])
    - lista vacía → sin perfil educador
    """
    if has_global_access(user):
        return None
    ed = _get_educador(user)
    if not ed:
        return []
    reglas = list(ed.reglas.all())
    if reglas:
        fines = set()
        for r in reglas:
            if not r.fin_educativo:
                return None  # Regla sin fin = acceso a todos los fines
            fines.add(r.fin_educativo)
        return list(fines)
    # Legacy: usar campo fines_educativos
    return list(ed.fines_educativos) if ed.fines_educativos else None


def can_create_reports(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    ed = _get_educador(user)
    return ed is not None and ed.is_active


def get_viewer_sections(user) -> list | None:
    """
    Devuelve las secciones que el viewer puede ver.
    - None  → todas (acceso global o regla sin sección)
    - lista → solo esas secciones (ej: ['basica_primaria'])
    """
    if has_global_access(user):
        return None
    ed = _get_educador(user)
    if not ed:
        return []
    reglas = list(ed.reglas.all())
    if not reglas:
        return None  # Sin reglas: legacy, mostrar todo
    secciones = set()
    for r in reglas:
        if not r.seccion:
            return None  # Regla sin sección = acceso a todas
        secciones.add(r.seccion)
    return list(secciones)


def can_manage_educadores(user) -> bool:
    """Solo la cuenta CAP puede gestionar educadores y ver el simulador."""
    if not user or not user.is_authenticated:
        return False
    return user.email in _CAP_ONLY or user.is_superuser


def sees_global_indicators(user) -> bool:
    """CAP, mrodriguez, dhiguera y pvasquez ven los indicadores globales; los demás ven solo los suyos."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.email in _GLOBAL_INDICATOR_EMAILS
