from .permissions import (
    resolve_viewer, resolve_real_user, has_global_access,
    can_manage_educadores, can_simulate, sees_global_indicators,
    get_viewer_sections, can_delete_content,
)


def sai_viewer(request):
    """Inyecta el usuario resuelto (SSO-aware + simulación) en todos los templates."""
    real_user = resolve_real_user(request)
    viewer    = resolve_viewer(request)

    is_simulating = False
    if can_simulate(real_user):
        sim_id = getattr(request, 'session', {}).get('simulated_user_id')
        if sim_id and viewer != real_user:
            is_simulating = True

    # can_manage_educadores (gestión de educadores) solo es True para CAP.
    # can_simulate es más amplio: CAP + coordinadoras habilitadas (ver can_simulate()).
    is_cap = can_manage_educadores(real_user)

    return {
        'viewer':                viewer,
        'real_user':             real_user,
        'is_simulating':         is_simulating,
        'viewer_is_global':      has_global_access(viewer) and not is_simulating,
        # Durante simulación ocultamos los controles de CAP para mostrar la vista fiel del docente
        'viewer_can_manage':     is_cap and not is_simulating,
        # can_simulate usa viewer (no real_user): durante la simulación debe reflejar
        # fielmente si la cuenta simulada tiene acceso real al Simulador (ya no es
        # exclusivo de CAP — ver _SIMULATOR_COORDINATOR_EMAILS en permissions.py).
        'can_simulate':          can_simulate(viewer),
        'viewer_sees_global_ind': sees_global_indicators(viewer) and not is_simulating,
        # Secciones visibles en el sidebar (None = todas, lista = solo esas)
        'viewer_sections':       get_viewer_sections(viewer),
        # Solo las cuentas autorizadas (ver _DELETE_AUTHORIZED_EMAILS) pueden
        # eliminar observaciones/recomendaciones — independiente de si pueden editar.
        'viewer_can_delete':     can_delete_content(viewer),
    }
