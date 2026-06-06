"""
Helpers de permisos para el SAI.
Uso: importar en vistas para filtrar QuerySets según el rol del usuario.
"""
from django.db.models import QuerySet


SECTION_KEY_MAP = {
    'preescolar':        ['preescolar', 'Jardín a Tercero', 'Jardin a Tercero', 'Jardín–Tercero'],
    'basica_primaria':   ['basica_primaria', 'Cuarto a Séptimo', 'Cuarto a Septimo', 'Cuarto–Séptimo'],
    'basica_secundaria': ['basica_secundaria', 'media_academica', 'Octavo a Undécimo',
                         'Octavo a Undecimo', 'Octavo–Undécimo', 'Media Académica', 'Media Academica'],
}


def _get_educador(user):
    if not user or not user.is_authenticated:
        return None
    try:
        return user.educador
    except Exception:
        return None


def has_global_access(user) -> bool:
    """True si el usuario tiene acceso a toda la plataforma (superuser o acceso_global)."""
    if user.is_superuser or user.is_staff:
        return True
    ed = _get_educador(user)
    return ed is not None and ed.acceso_global


def get_allowed_section_names(user) -> list | None:
    """
    Retorna lista de nombres de sección a los que el usuario tiene acceso.
    None significa acceso a todo.
    """
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
    Retorna lista de fines educativos permitidos.
    None significa todos.
    """
    if has_global_access(user):
        return None
    ed = _get_educador(user)
    if not ed:
        return []
    return list(ed.fines_educativos) if ed.fines_educativos else None


def filter_reports_for_user(qs: QuerySet, user) -> QuerySet:
    """
    Filtra un QuerySet de Report según el perfil del usuario.
    """
    if has_global_access(user):
        return qs

    allowed_sections = get_allowed_section_names(user)
    allowed_fines = get_allowed_fines(user)

    if allowed_sections is not None:
        qs = qs.filter(student__section__in=allowed_sections)
    if allowed_fines is not None:
        qs = qs.filter(purpose__in=allowed_fines)
    return qs


def can_create_reports(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    ed = _get_educador(user)
    if not ed:
        return False
    return ed.is_active


def can_manage_educadores(user) -> bool:
    """Solo el superuser CAP puede gestionar perfiles de educadores."""
    if not user or not user.is_authenticated:
        return False
    return bool(user.is_superuser)
