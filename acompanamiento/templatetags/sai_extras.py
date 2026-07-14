from django import template

register = template.Library()


@register.filter
def can_edit_report(report, viewer):
    """True si viewer puede editar/eliminar observaciones y recomendaciones de este reporte."""
    from acompanamiento.permissions import can_manage_report
    if not report or not viewer:
        return False
    return can_manage_report(viewer, report) and not report.is_closed


@register.filter
def can_reopen_report(report, viewer):
    """True si viewer puede reabrir este reporte cuando está cerrado (mismo alcance que can_manage_report)."""
    from acompanamiento.permissions import can_manage_report
    if not report or not viewer:
        return False
    return can_manage_report(viewer, report)
