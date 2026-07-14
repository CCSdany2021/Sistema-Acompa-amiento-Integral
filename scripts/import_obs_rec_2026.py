# -*- coding: utf-8 -*-
"""
Importa Observaciones y Recomendaciones desde los CSVs de Power Apps 2026.
Limpia los registros sin external_id (importados antes sin trazabilidad),
luego inserta los del CSV usando el campo ID como clave de deduplicación.

Ejecutar: python scripts/import_obs_rec_2026.py
"""
import os, sys, csv, glob
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from acompanamiento.models import Report, Observation, Recommendation, ReportPurpose

User = get_user_model()

OBS_FILE = glob.glob('archivos/*Observaciones*.csv')[0]
REC_FILE = glob.glob('archivos/*Recomendaciones*.csv')[0]

FIN_MAP = {
    'Espiritual':    'ESPIRITUAL',
    'Psicoafectivo': 'PSICOAFECTIVO',
    'Convivencia':   'CONVIVENCIA',
    'Academico':     'ACADEMICO',
    'Ac\xe9dmico':   'ACADEMICO',
    'Acad\xe9mico':  'ACADEMICO',
}

def resolve_fin(raw):
    p = FIN_MAP.get(raw.strip(), '')
    if not p:
        u = raw.upper()
        if 'SPIRIT' in u:   p = 'ESPIRITUAL'
        elif 'PSICO' in u:  p = 'PSICOAFECTIVO'
        elif 'CONVIV' in u: p = 'CONVIVENCIA'
        elif 'ACAD' in u:   p = 'ACADEMICO'
    return p


def to_aware(dt_str, fmt='%d/%m/%Y %H:%M'):
    try:
        return timezone.make_aware(datetime.strptime(dt_str.strip(), fmt))
    except Exception:
        return timezone.now()


def to_date(dt_str):
    for fmt in ('%d/%m/%Y %H:%M', '%d/%m/%Y'):
        try:
            return datetime.strptime(dt_str.strip(), fmt).date()
        except Exception:
            pass
    return None


def find_user(email_raw):
    if not email_raw or '@' not in email_raw:
        return None
    email = email_raw.strip().lower()
    from django.db.models import Q
    return User.objects.filter(
        Q(username__iexact=email) | Q(email__iexact=email)
    ).filter(is_active=True).first()


def find_report(codigo, purpose):
    """Devuelve el reporte más reciente del estudiante con ese fin."""
    return (Report.objects
            .filter(student__code=codigo.strip(), purpose=purpose)
            .order_by('-created_at')
            .first())


# ── PASO 1: Limpiar registros sin external_id (importados previamente sin ID) ──
print("Limpiando registros sin external_id...")
obs_deleted = Observation.objects.filter(external_id='').delete()[0]
rec_deleted = Recommendation.objects.filter(external_id='').delete()[0]
print(f"  Observaciones eliminadas: {obs_deleted}")
print(f"  Recomendaciones eliminadas: {rec_deleted}")
print()

# ── PASO 2: Importar OBSERVACIONES ─────────────────────────────────────────────
print(f"Importando observaciones desde: {OBS_FILE}")
with open(OBS_FILE, encoding='utf-8-sig') as f:
    obs_rows = list(csv.DictReader(f))

print(f"Total filas en CSV: {len(obs_rows)}")

obs_created = obs_skipped = obs_no_report = obs_no_fin = 0
obs_bulk = []

existing_obs_ids = set(Observation.objects.exclude(external_id='').values_list('external_id', flat=True))

for i, row in enumerate(obs_rows):
    ext_id   = (row.get('ID') or '').strip()
    codigo   = (row.get('Codigo') or '').strip()
    fin_raw  = (row.get('Fin_educativo') or '').strip()
    content  = (row.get('Observaciones') or '').strip()
    creado   = (row.get('Creado') or '').strip()
    fecha    = (row.get('Fecha') or '').strip()
    email_at = (row.get('Quien_Atiende') or '').strip().lower()
    email_al = (row.get('Correo_institucional') or '').strip().lower()

    if not content:
        obs_skipped += 1
        continue

    if ext_id and ext_id in existing_obs_ids:
        obs_skipped += 1
        continue

    purpose = resolve_fin(fin_raw)
    if not purpose:
        obs_no_fin += 1
        continue

    report = find_report(codigo, purpose)
    if not report:
        obs_no_report += 1
        continue

    creator = find_user(email_at)
    created_dt = to_aware(creado) if creado else timezone.now()
    followup   = to_date(fecha)

    obs = Observation(
        report=report,
        content=content,
        created_by=creator,
        correo_institucional=email_at,
        fin_educativo=purpose,
        followup_date=followup,
        external_id=ext_id,
    )
    obs_bulk.append((obs, created_dt))
    if ext_id:
        existing_obs_ids.add(ext_id)
    obs_created += 1

# Insertar en bloque
print(f"Insertando {len(obs_bulk)} observaciones...")
CHUNK = 200
for i in range(0, len(obs_bulk), CHUNK):
    chunk = obs_bulk[i:i+CHUNK]
    objs = [o for o, _ in chunk]
    Observation.objects.bulk_create(objs, ignore_conflicts=False)
    # Actualizar date_log con la fecha real del CSV
    for obs_obj, created_dt in chunk:
        if obs_obj.pk:
            Observation.objects.filter(pk=obs_obj.pk).update(date_log=created_dt)

# Re-fetch PKs after bulk_create (needed for date_log update if not returned)
# Simpler: update date_log by external_id
print("Actualizando fechas de observaciones...")
for obs_obj, created_dt in obs_bulk:
    if obs_obj.external_id:
        Observation.objects.filter(external_id=obs_obj.external_id).update(date_log=created_dt)

print(f"OBSERVACIONES:")
print(f"  Creadas       : {obs_created}")
print(f"  Duplicadas    : {obs_skipped}")
print(f"  Sin reporte   : {obs_no_report}")
print(f"  Sin fin educ  : {obs_no_fin}")
print()

# ── PASO 3: Importar RECOMENDACIONES ───────────────────────────────────────────
print(f"Importando recomendaciones desde: {REC_FILE}")
with open(REC_FILE, encoding='utf-8-sig') as f:
    rec_rows = list(csv.DictReader(f))

print(f"Total filas en CSV: {len(rec_rows)}")

rec_created = rec_skipped = rec_no_report = 0
rec_bulk = []

existing_rec_ids = set(Recommendation.objects.exclude(external_id='').values_list('external_id', flat=True))

for row in rec_rows:
    ext_id   = (row.get('ID') or '').strip()
    codigo   = (row.get('Codigo') or '').strip()
    fin_raw  = (row.get('Fin_educativo') or '').strip()
    content  = (row.get('Recomendaciones') or '').strip()
    creado   = (row.get('Creado') or '').strip()
    fecha    = (row.get('Fecha') or '').strip()
    email_at = (row.get('QuienAtiende') or '').strip().lower()

    if not content:
        rec_skipped += 1
        continue

    if ext_id and ext_id in existing_rec_ids:
        rec_skipped += 1
        continue

    purpose = resolve_fin(fin_raw)
    if not purpose:
        rec_skipped += 1
        continue

    report = find_report(codigo, purpose)
    if not report:
        rec_no_report += 1
        continue

    creator = find_user(email_at)
    created_dt = to_aware(creado) if creado else timezone.now()
    followup   = to_date(fecha)

    rec = Recommendation(
        report=report,
        content=content,
        created_by=creator,
        correo_institucional=email_at,
        fin_educativo=purpose,
        followup_date=followup,
        external_id=ext_id,
    )
    rec_bulk.append((rec, created_dt))
    if ext_id:
        existing_rec_ids.add(ext_id)
    rec_created += 1

print(f"Insertando {len(rec_bulk)} recomendaciones...")
for i in range(0, len(rec_bulk), CHUNK):
    chunk = rec_bulk[i:i+CHUNK]
    Recommendation.objects.bulk_create([r for r, _ in chunk], ignore_conflicts=False)

print("Actualizando fechas de recomendaciones...")
for rec_obj, created_dt in rec_bulk:
    if rec_obj.external_id:
        Recommendation.objects.filter(external_id=rec_obj.external_id).update(date_log=created_dt)

print(f"RECOMENDACIONES:")
print(f"  Creadas     : {rec_created}")
print(f"  Duplicadas  : {rec_skipped}")
print(f"  Sin reporte : {rec_no_report}")
print()

# ── PASO 4: Recalcular recuento de observaciones en todos los reportes ─────────
print("Recalculando recuento de observaciones...")
from acompanamiento.models import Report as R
from django.db.models import Count
reports_qs = R.objects.annotate(obs_count=Count('observations'))
updated = 0
for rep in reports_qs:
    if rep.recuento != rep.obs_count:
        rep.recuento = rep.obs_count
        rep.save(update_fields=['recuento'])
        updated += 1
print(f"  Reportes con recuento actualizado: {updated}")

print()
print("=" * 50)
print(f"Observaciones totales en BD : {Observation.objects.count()}")
print(f"Recomendaciones totales en BD: {Recommendation.objects.count()}")
print("IMPORTACION COMPLETADA")
