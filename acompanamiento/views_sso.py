"""
SSO desde portalcalasanzsuba.com → SAI.

Flujo:
  1. El portal genera un JWT firmado con su SECRET_KEY y redirige a:
     https://sai.portalcalasanzsuba.com/auth/sso/?token=<JWT>
  2. Este endpoint valida el JWT, crea/actualiza el usuario Django y
     crea/vincula su perfil Educador, luego hace login y redirige al dashboard.
"""
import logging
from django.contrib.auth import login, get_user_model
from django.shortcuts import redirect
from django.conf import settings
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)
User = get_user_model()


def _validar_token(token: str) -> dict | None:
    """Valida el JWT firmado por el portal con su SECRET_KEY compartida."""
    try:
        import jwt
        secret = getattr(settings, 'PORTAL_SECRET_KEY', settings.SECRET_KEY)
        return jwt.decode(token, secret, algorithms=['HS256'])
    except Exception as e:
        logger.warning("[SSO] Token inválido: %s", e)
        return None


def _get_o_crear_educador(user):
    """Busca o crea el Educador vinculado al usuario Django."""
    from acompanamiento.models import Educador
    educador, creado = Educador.objects.get_or_create(
        user=user,
        defaults={
            'acceso_global': user.is_staff or user.is_superuser,
            'is_active': True,
        }
    )
    if creado:
        logger.info("[SSO] Educador creado para: %s", user.email)
    return educador


@csrf_exempt
@require_GET
def sso_login(request):
    """
    GET /auth/sso/?token=<JWT>
    Autentica al usuario via token JWT del portal y redirige al dashboard.
    """
    token = request.GET.get('token', '').strip()

    if not token:
        logger.warning("[SSO] Acceso sin token desde IP: %s",
                       request.META.get('REMOTE_ADDR'))
        return redirect('/?sso_error=1')

    payload = _validar_token(token)
    if not payload:
        logger.warning("[SSO] Token inválido o expirado")
        return redirect('/?sso_error=1')

    email = payload.get('email', '').strip().lower()
    nombre = payload.get('nombre', '')
    rol_portal = payload.get('rol', '')

    if not email:
        logger.warning("[SSO] Token sin email")
        return redirect('/?sso_error=1')

    # Obtener o crear el usuario Django
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        # Crear usuario nuevo (sin contraseña — solo puede entrar por SSO)
        username = email.split('@')[0]
        # Asegurar username único
        base = username
        n = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{n}"
            n += 1

        partes = nombre.strip().split()
        first = partes[0] if partes else username
        last  = ' '.join(partes[1:]) if len(partes) > 1 else ''

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first,
            last_name=last,
            password=None,  # Sin contraseña — SSO only
        )
        logger.info("[SSO] Usuario creado: %s (%s)", email, rol_portal)

    # Actualizar nombre si cambió
    if nombre:
        partes = nombre.strip().split()
        user.first_name = partes[0] if partes else user.first_name
        user.last_name  = ' '.join(partes[1:]) if len(partes) > 1 else user.last_name
        user.save(update_fields=['first_name', 'last_name'])

    # Crear/vincular perfil Educador
    _get_o_crear_educador(user)

    # Login
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    logger.info("[SSO] Login exitoso: %s (rol portal: %s)", email, rol_portal)

    next_url = request.GET.get('next', '/')
    return redirect(next_url)
