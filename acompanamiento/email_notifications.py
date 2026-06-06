import logging
import requests
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

FINES_LABELS = {
    'ACADEMICO':    'Académico',
    'CONVIVENCIA':  'Convivencia',
    'ESPIRITUAL':   'Espiritual',
    'PSICOAFECTIVO':'Psicoafectivo',
}


# ─────────────────────────────────────────────
# 1. Notificación: reporte asignado
# ─────────────────────────────────────────────

def notify_report_assigned(report):
    """Envía correo al educador asignado cuando se crea un reporte."""
    assigned = report.assigned_to
    if not assigned or not assigned.email:
        return

    remite = report.created_by
    remite_nombre = remite.get_full_name() or remite.username if remite else 'Sistema'
    fin = FINES_LABELS.get(report.purpose, report.purpose)
    estudiante = report.student.full_name
    objetivo = report.objective or 'Sin objetivo especificado'
    es_auto = remite and assigned and remite.id == assigned.id

    asunto = f'[SAI] Nuevo reporte asignado: {estudiante} — {fin}'
    intro = 'Has creado y asignado un reporte a ti mismo.' if es_auto \
            else f'{remite_nombre} te ha asignado un reporte de acompañamiento.'

    cuerpo = f"""Hola {assigned.get_full_name() or assigned.username},

{intro}

━━━━━━━━━━━━━━━━━━━━━━━━━━
  REPORTE DE ACOMPAÑAMIENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━
  Estudiante : {estudiante}
  Tipo       : {fin}
  Estado     : Programado
  Remite     : {remite_nombre}

  Objetivo:
  {objetivo}
━━━━━━━━━━━━━━━━━━━━━━━━━━

Ingresa al SAI para gestionar este reporte:
http://127.0.0.1:8005/students/

---
Sistema de Acompañamiento Integral – Calasanz Suba
Correo automático, por favor no responder.
"""
    _send(asunto, cuerpo, [assigned.email], f'reporte {report.id}')


# ─────────────────────────────────────────────
# 2. Notificación: recomendación a docentes del curso
# ─────────────────────────────────────────────

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

    fin = FINES_LABELS.get(
        recommendation.fin_educativo or recommendation.report.purpose, 'General'
    )
    autor = recommendation.created_by
    autor_nombre = autor.get_full_name() or autor.username if autor else 'Sistema'

    asunto = f'[SAI] Recomendación pedagógica: {student.full_name} – {course.name}'
    cuerpo = f"""Estimado/a docente,

El equipo de acompañamiento ha registrado una recomendación pedagógica
para un estudiante de su curso. Por favor, téngala en cuenta en su práctica.

━━━━━━━━━━━━━━━━━━━━━━━━━━
  RECOMENDACIÓN PEDAGÓGICA
━━━━━━━━━━━━━━━━━━━━━━━━━━
  Estudiante   : {student.full_name} ({student.code})
  Curso        : {course.name}
  Tipo         : {fin}
  Registrado por: {autor_nombre}

  Recomendación:
  {recommendation.content}
━━━━━━━━━━━━━━━━━━━━━━━━━━

Esta recomendación aplica para todos los docentes del curso {course.name}.

---
Sistema de Acompañamiento Integral – Calasanz Suba
Correo automático, por favor no responder.
"""

    sent = 0
    for t in teachers:
        email = t.get('email', '').strip()
        if not email:
            continue
        ok = _send(asunto, cuerpo, [email], f'recomendación {recommendation.id} a {email}')
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


def _send(subject: str, body: str, recipients: list, label: str = '') -> bool:
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
        logger.info(f'Notificación enviada [{label}] → {recipients}')
        return True
    except Exception as exc:
        logger.warning(f'Error enviando notificación [{label}]: {exc}')
        return False
