import logging
import time
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Cache simple del token de Microsoft Graph en memoria del proceso (evita pedir
# un token nuevo por cada correo; se renueva solo cuando está por expirar).
_graph_token_cache = {'token': None, 'expires_at': 0}

FINES_LABELS = {
    'ACADEMICO':    'Académico',
    'CONVIVENCIA':  'Convivencia',
    'ESPIRITUAL':   'Espiritual',
    'PSICOAFECTIVO':'Psicoafectivo',
}

# Plantillas HTML institucionales (mismo diseño usado en las demás notificaciones del colegio)
REPORT_ASSIGNED_HTML = """
<div style='max-width:600px;margin:0 auto;font-family:Segoe UI, Arial, sans-serif;'>

    <!-- Encabezado -->
    <div style='background:#153459;color:white;padding:15px;text-align:center;border-radius:5px 5px 0 0;'>
        <h2 style='margin:0;font-size:17px;font-weight:600;'>Reporte de Acompañamiento Asignado</h2>
    </div>

    <!-- Cuerpo -->
    <div style='background:#ffffff;padding:25px;border:1px solid #e0e0e0;'>

        <p style='font-size:15px;margin:0 0 20px 0;'>
            Hola <strong>{CAMPO_DESTINATARIO}</strong>,
        </p>

        <p style='font-size:14px;margin:0 0 20px 0;color:#555;'>
            <strong>{CAMPO_QUIEN_ASIGNA}</strong> te ha asignado un reporte de acompañamiento.
        </p>

        <!-- Información del reporte -->
        <div style='background:#f8f9fa;padding:15px;border-radius:5px;margin-bottom:20px;border-left:4px solid #153459;'>
            <table style='width:100%;font-size:14px;border-collapse:collapse;'>
                <tr>
                    <td style='padding:8px 0;color:#666;width:35%;vertical-align:top;'><strong>Estudiante:</strong></td>
                    <td style='padding:8px 0;'>{CAMPO_ESTUDIANTE}</td>
                </tr>
                <tr>
                    <td style='padding:8px 0;color:#666;vertical-align:top;'><strong>Fin educativo:</strong></td>
                    <td style='padding:8px 0;'>{CAMPO_TIPO}</td>
                </tr>
                <tr>
                    <td style='padding:8px 0;color:#666;vertical-align:top;'><strong>Estado:</strong></td>
                    <td style='padding:8px 0;'><span style='background:#ff9800;color:white;padding:3px 10px;border-radius:3px;font-size:12px;'>{CAMPO_ESTADO}</span></td>
                </tr>
                <tr>
                    <td style='padding:8px 0;color:#666;vertical-align:top;'><strong>Remite:</strong></td>
                    <td style='padding:8px 0;'>{CAMPO_REMITE}</td>
                </tr>
            </table>
        </div>


    </div>

    <!-- Footer -->
    <div style='background:#f8f9fa;padding:12px;text-align:center;border-radius:0 0 5px 5px;border:1px solid #e0e0e0;border-top:none;'>
        <p style='margin:0;font-size:10px;color:#999;'>Notificación enviada desde la Gestión de Acompañamiento Integral</p>
        <p style='margin:4px 0 0 0;font-size:10px;color:#bbb;'>Colegio San José de Calasanz - Suba</p>
    </div>

</div>
"""

RECOMMENDATION_HTML = """
<div style='max-width:600px;margin:0 auto;font-family:Segoe UI, Arial, sans-serif;'>

    <!-- Encabezado -->
    <div style='background:#153459;color:white;padding:15px;text-align:center;border-radius:5px 5px 0 0;'>
        <h2 style='margin:0;font-size:17px;font-weight:600;'>Recomendación</h2>
    </div>

    <!-- Cuerpo -->
    <div style='background:#ffffff;padding:25px;border:1px solid #e0e0e0;'>

        <p style='font-size:14px;margin:0 0 20px 0;line-height:1.6;'>
            Estimado/a docente,
        </p>

        <p style='font-size:14px;margin:0 0 20px 0;color:#555;line-height:1.6;'>
            El equipo de acompañamiento ha registrado una recomendación para un estudiante de su curso. Por favor, téngala en cuenta en su práctica.
        </p>

        <!-- Información de la recomendación -->
        <div style='background:#f8f9fa;padding:15px;border-radius:5px;margin-bottom:20px;border-left:4px solid #153459;'>
            <table style='width:100%;font-size:14px;border-collapse:collapse;'>
                <tr>
                    <td style='padding:8px 0;color:#666;width:40%;vertical-align:top;'><strong>Estudiante:</strong></td>
                    <td style='padding:8px 0;'>{CAMPO_ESTUDIANTE} ({CAMPO_CODIGO})</td>
                </tr>
                <tr>
                    <td style='padding:8px 0;color:#666;vertical-align:top;'><strong>Curso:</strong></td>
                    <td style='padding:8px 0;'>{CAMPO_CURSO}</td>
                </tr>
                <tr>
                    <td style='padding:8px 0;color:#666;vertical-align:top;'><strong>Fin educativo:</strong></td>
                    <td style='padding:8px 0;'><span style='background:#2196F3;color:white;padding:3px 10px;border-radius:3px;font-size:12px;'>{CAMPO_TIPO}</span></td>
                </tr>
                <tr>
                    <td style='padding:8px 0;color:#666;vertical-align:top;'><strong>Registrado por:</strong></td>
                    <td style='padding:8px 0;'>{CAMPO_REGISTRADO_POR}</td>
                </tr>
            </table>
        </div>

        <!-- Recomendación -->
        <div style='background:#f0f7ff;padding:15px;border-radius:5px;margin-bottom:15px;border:1px solid #b8daff;'>
            <h3 style='margin:0 0 12px 0;color:#153459;font-size:14px;'>Recomendación</h3>
            <p style='margin:0;font-size:14px;color:#333;line-height:1.6;text-align:justify;'>
                {CAMPO_RECOMENDACION}
            </p>
        </div>

    </div>

    <!-- Footer -->
    <div style='background:#f8f9fa;padding:12px;text-align:center;border-radius:0 0 5px 5px;border:1px solid #e0e0e0;border-top:none;'>
        <p style='margin:0;font-size:10px;color:#999;'>Notificación enviada desde la Gestión de Acompañamiento Integral</p>
        <p style='margin:4px 0 0 0;font-size:10px;color:#bbb;'>Colegio San José de Calasanz - Suba</p>
    </div>

</div>
"""


# ─────────────────────────────────────────────
# 1. Notificación: reporte asignado
# ─────────────────────────────────────────────

def build_report_assigned_email(report):
    """Arma (asunto, html) para la notificación de reporte asignado."""
    assigned = report.assigned_to
    remite = report.created_by
    remite_nombre = remite.get_full_name() or remite.username if remite else 'Sistema'
    fin = FINES_LABELS.get(report.purpose, report.purpose)
    estudiante = report.student.full_name

    asunto = f'Nuevo reporte asignado: {estudiante} — {fin}'
    html = REPORT_ASSIGNED_HTML.format(
        CAMPO_DESTINATARIO=assigned.get_full_name() or assigned.username,
        CAMPO_QUIEN_ASIGNA=remite_nombre,
        CAMPO_ESTUDIANTE=estudiante,
        CAMPO_TIPO=fin,
        # Esta notificación siempre se envía justo al crear el reporte, cuando
        # todavía no ha entrado a Seguimiento — por eso queda fijo en "Programado".
        CAMPO_ESTADO='Programado',
        CAMPO_REMITE=remite_nombre,
    )
    return asunto, html


def notify_report_assigned(report):
    """Envía correo al educador asignado cuando se crea un reporte."""
    assigned = report.assigned_to
    if not assigned or not assigned.email:
        return
    asunto, html = build_report_assigned_email(report)
    _send(asunto, html, [assigned.email], f'reporte {report.id}')


# ─────────────────────────────────────────────
# 2. Notificación: recomendación a docentes del curso
# ─────────────────────────────────────────────

def build_recommendation_email(recommendation):
    """Arma (asunto, html) para la notificación de recomendación pedagógica."""
    student = recommendation.report.student
    course = student.course
    fin = FINES_LABELS.get(
        recommendation.fin_educativo or recommendation.report.purpose, 'General'
    )
    autor = recommendation.created_by
    autor_nombre = autor.get_full_name() or autor.username if autor else 'Sistema'
    course_name = course.name if course else 'Sin curso'

    asunto = f'Recomendación: {student.full_name} – {course_name}'
    html = RECOMMENDATION_HTML.format(
        CAMPO_ESTUDIANTE=student.full_name,
        CAMPO_CODIGO=student.code,
        CAMPO_CURSO=course_name,
        CAMPO_TIPO=fin,
        CAMPO_REGISTRADO_POR=autor_nombre,
        CAMPO_RECOMENDACION=recommendation.content,
    )
    return asunto, html


def notify_recommendation_to_teachers(recommendation):
    """
    Cuando se crea una recomendación, notifica a todos los docentes
    que dictan clase en el curso del estudiante.

    Consulta: GET {GESTOR_EDUCATIVO_URL}/api/v1/asignacion-academica/?curso={code}
    Respuesta esperada: [{"email": "...", "nombre": "..."}, ...]
    """
    student = recommendation.report.student
    course  = student.course
    if not course:
        logger.info(f'Recomendación {recommendation.id}: estudiante sin curso asignado, sin notificación.')
        return

    teachers = _get_course_teachers(course.name)
    if not teachers:
        logger.info(f'Recomendación {recommendation.id}: no se encontraron docentes para curso {course.name}.')
        return

    asunto, html = build_recommendation_email(recommendation)

    sent = 0
    for t in teachers:
        email = t.get('email', '').strip()
        if not email:
            continue
        ok = _send(asunto, html, [email], f'recomendación {recommendation.id} a {email}')
        if ok:
            sent += 1

    logger.info(
        f'Recomendación {recommendation.id} (curso {course.name}): '
        f'{sent}/{len(teachers)} notificaciones enviadas.'
    )


# ─────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────

def _get_course_teachers(course_name: str) -> list:
    """
    Consulta la API del Gestor Educativo para obtener los docentes
    que tienen asignado el curso dado en su horario académico.

    Endpoint: GET /api/v1/asignacion-academica/?curso={course_name}
    """
    try:
        url     = f"{settings.GESTOR_EDUCATIVO_URL}/api/v1/asignacion-academica/"
        headers = {'X-API-Key': settings.GESTOR_EDUCATIVO_API_KEY}
        resp = requests.get(url, headers=headers, params={'curso': course_name},
                            timeout=10, verify=False)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get('results', data.get('docentes', []))
        return []
    except Exception as exc:
        logger.warning(f'No se pudo consultar docentes del curso {course_name}: {exc}')
        return []


def _get_graph_token() -> str:
    """Token OAuth2 (client credentials) de la App registrada en Azure. Se cachea
    en memoria y se renueva automáticamente cuando está por expirar."""
    now = time.time()
    if _graph_token_cache['token'] and now < _graph_token_cache['expires_at'] - 60:
        return _graph_token_cache['token']

    url = f"https://login.microsoftonline.com/{settings.MS_TENANT_ID}/oauth2/v2.0/token"
    data = {
        'client_id': settings.MS_CLIENT_ID,
        'client_secret': settings.MS_CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/.default',
        'grant_type': 'client_credentials',
    }
    resp = requests.post(url, data=data, timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    _graph_token_cache['token'] = payload['access_token']
    _graph_token_cache['expires_at'] = now + payload.get('expires_in', 3600)
    return _graph_token_cache['token']


def _send(subject: str, body: str, recipients: list, label: str = '', content_type: str = 'HTML') -> bool:
    """Envía el correo vía Microsoft Graph (App registrada en Azure), en nombre
    de la cuenta institucional configurada en DEFAULT_FROM_EMAIL (ccs@calasanzsuba.edu.co)."""
    try:
        token = _get_graph_token()
        sender = settings.DEFAULT_FROM_EMAIL
        url = f"https://graph.microsoft.com/v1.0/users/{sender}/sendMail"
        payload = {
            'message': {
                'subject': subject,
                'body': {'contentType': content_type, 'content': body},
                'toRecipients': [{'emailAddress': {'address': r}} for r in recipients],
            },
            'saveToSentItems': 'false',
        }
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        logger.info(f'Notificación enviada [{label}] → {recipients}')
        return True
    except Exception as exc:
        logger.warning(f'Error enviando notificación [{label}]: {exc}')
        return False
