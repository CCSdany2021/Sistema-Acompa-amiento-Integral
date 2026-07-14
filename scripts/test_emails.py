"""
Script de prueba: envía los dos tipos de notificaciones (con las plantillas HTML
institucionales) a cap@calasanzsuba.edu.co
Ejecutar: python scripts/test_emails.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from acompanamiento.models import Report, Recommendation
from acompanamiento.email_notifications import build_report_assigned_email, build_recommendation_email, _send

DEST = "cap@calasanzsuba.edu.co"

# ══════════════════════════════════════════
# EMAIL 1 — Reporte asignado al educador
# ══════════════════════════════════════════
report = (Report.objects.select_related("student", "created_by", "assigned_to")
          .exclude(assigned_to=None).order_by("-created_at").first())
if not report:
    print("ERROR: No hay reportes con educador asignado en la BD.")
    sys.exit(1)

asunto1, html1 = build_report_assigned_email(report)
ok1 = _send(f"[TEST] {asunto1}", html1, [DEST], f"TEST reporte-asignado id={report.id}")
print(f"Email 1 — Reporte asignado  : {'ENVIADO OK' if ok1 else 'ERROR al enviar'}")


# ══════════════════════════════════════════
# EMAIL 2 — Recomendación a docentes del curso
# ══════════════════════════════════════════
rec = Recommendation.objects.select_related(
    "report__student__course", "created_by"
).order_by("-id").first()
if not rec:
    print("ERROR: No hay recomendaciones en la BD.")
    sys.exit(1)

asunto2, html2 = build_recommendation_email(rec)
ok2 = _send(f"[TEST] {asunto2}", html2, [DEST], f"TEST recomendacion-docentes id={rec.id}")
print(f"Email 2 — Recomendación docentes: {'ENVIADO OK' if ok2 else 'ERROR al enviar'}")

print()
print(f"Destino         : {DEST}")
print(f"Reporte usado   : {report.student.full_name} | id={report.id}")
print(f"Recomendación   : {rec.report.student.full_name} | id={rec.id}")
