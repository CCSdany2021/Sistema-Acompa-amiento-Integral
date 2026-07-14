# -*- coding: utf-8 -*-
"""
Actualiza reportes existentes desde archivos/registro_actualizado.xlsx:
  - assigned_to / institucional_quien_atiende
  - cumple_acompanamiento / fecha_cierre / status
Importa los 15 reportes nuevos que no existen aún.

Ejecutar: python scripts/update_from_xlsx.py
"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
django.setup()

import openpyxl
from datetime import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
from acompanamiento.models import Report, Student, ReportStatus

User = get_user_model()

XLSX_PATH = 'archivos/registro_actualizado.xlsx'
CAP_EMAIL  = 'cap@calasanzsuba.edu.co'

FIN_MAP = {
    'Espiritual':    'ESPIRITUAL',
    'Psicoafectivo': 'PSICOAFECTIVO',
    'Convivencia':   'CONVIVENCIA',
    'Académico':     'ACADEMICO',
    'Academico':     'ACADEMICO',
    'Acad\xe9mico':  'ACADEMICO',
}

STATUS_MAP = {
    'Seguimiento': ReportStatus.SEGUIMIENTO,
    'Programado':  ReportStatus.PROGRAMADO,
    'Atendido':    ReportStatus.ATENDIDO,
}


def resolve_purpose(raw):
    p = FIN_MAP.get(raw, '')
    if not p:
        u = raw.upper()
        if 'SPIRIT' in u:   p = 'ESPIRITUAL'
        elif 'PSICO' in u:  p = 'PSICOAFECTIVO'
        elif 'CONVIV' in u: p = 'CONVIVENCIA'
        elif 'ACAD' in u:   p = 'ACADEMICO'
    return p


def lookup_user(email_raw):
    """Devuelve User o None. CAP nunca se asigna como atendedor."""
    if not email_raw:
        return None
    email = email_raw.strip().lower()
    if email == CAP_EMAIL:
        return None
    from django.db.models import Q
    return (
        User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email))
        .filter(is_active=True).first()
    )


def to_aware(dt_val):
    """Convierte datetime de openpyxl (naive) a aware en la zona del sistema."""
    if dt_val is None:
        return None
    if isinstance(dt_val, datetime):
        return timezone.make_aware(dt_val) if dt_val.tzinfo is None else dt_val
    return None


print(f"Abriendo {XLSX_PATH} …")
wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)
ws = wb.active

rows = list(ws.iter_rows(min_row=2, values_only=True))
print(f"Filas en Excel: {len(rows)}")

updated = inserted = skipped = errors = 0
cap_fixed = 0
fallback_user = User.objects.filter(is_superuser=True).first()
not_found_users = set()

for i, row in enumerate(rows, start=2):
    nombre   = (row[0] or '').strip()
    codigo   = str(row[1]).strip() if row[1] else ''
    fin_raw  = (row[6] or '').strip()
    tipo     = (row[7] or '').strip()
    estado   = (row[8] or '').strip()
    email_remite  = (row[13] or '').strip().lower() if len(row) > 13 else ''  # "Creado por" no, usamos col 11
    email_atiende = (row[11] or '').strip().lower() if len(row) > 11 else ''  # "Institucional Quien Atiende"
    objetivo = (row[12] or '').strip() if len(row) > 12 else ''
    periodo  = (row[13] or '').strip() if len(row) > 13 else ''
    creado_dt   = to_aware(row[14]) if len(row) > 14 else None
    cumple_raw  = (row[15] or '') if len(row) > 15 else ''
    cierre_dt   = to_aware(row[16]) if len(row) > 16 else None

    # Columna correcta: índices 0-based desde openpyxl values_only
    # 0: Nombre, 1: Codigo, 2: Curso, 3: Grado, 4: Sección, 5: Institucional_Alumno
    # 6: Fines, 7: Tipo, 8: Estado, 9: Quien Remite, 10: Quien Atiende,
    # 11: Institucional Quien Atiende, 12: Objetivo, 13: Periodo, 14: Creado,
    # 15: Cumplió, 16: Fecha Cierre, 17: Notificacion, 18: Creado por

    purpose = resolve_purpose(fin_raw)
    if not purpose:
        print(f"  Fila {i}: fin no reconocido [{fin_raw}] — omitido")
        errors += 1
        continue

    status = STATUS_MAP.get(estado, ReportStatus.PROGRAMADO)
    cumple = str(cumple_raw).strip().lower() in ('si', 'sí', 'yes', '1', 'true')

    student = Student.objects.filter(code=codigo).first()
    if not student:
        print(f"  Fila {i}: estudiante {codigo} no encontrado")
        errors += 1
        continue

    assigned_to = lookup_user(email_atiende)
    if email_atiende and not assigned_to:
        not_found_users.add(email_atiende)

    # --- Buscar reporte existente ---
    fecha_solo = creado_dt.date() if creado_dt else None
    if fecha_solo:
        qs = Report.objects.filter(student=student, purpose=purpose, created_at__date=fecha_solo)
        cnt = qs.count()
    else:
        qs = Report.objects.none()
        cnt = 0

    if cnt == 1:
        r = qs.first()

        # Detectar si CAP estaba mal asignado
        old_assigned = r.assigned_to
        if old_assigned and old_assigned.email == CAP_EMAIL:
            cap_fixed += 1

        changed = []
        if assigned_to and r.assigned_to != assigned_to:
            r.assigned_to = assigned_to
            changed.append('assigned_to')
        if email_atiende and r.institucional_quien_atiende != email_atiende:
            r.institucional_quien_atiende = email_atiende
            changed.append('institucional_quien_atiende')
        if r.cumple_acompanamiento != cumple:
            r.cumple_acompanamiento = cumple
            changed.append('cumple_acompanamiento')
        if r.fecha_cierre != cierre_dt:
            r.fecha_cierre = cierre_dt
            changed.append('fecha_cierre')
        if r.status != status:
            r.status = status
            changed.append('status')
        if objetivo and r.objective != objetivo:
            r.objective = objetivo
            changed.append('objective')
        if periodo and r.academic_period != periodo:
            r.academic_period = periodo
            changed.append('academic_period')

        if changed:
            r.save(update_fields=changed + ['updated_at'])
            updated += 1
        else:
            skipped += 1

    elif cnt == 0:
        # Reporte nuevo — insertar
        remite_user = lookup_user(email_remite) or fallback_user
        try:
            nr = Report(
                student=student,
                purpose=purpose,
                fines_educativos=[purpose],
                status=status,
                objective=objetivo,
                academic_period=periodo,
                year=2026,
                created_by=remite_user,
                assigned_to=assigned_to or remite_user,
                institucional_quien_atiende=email_atiende,
                cumple_acompanamiento=cumple,
                fecha_cierre=cierre_dt,
            )
            nr.save()
            if creado_dt:
                Report.objects.filter(pk=nr.pk).update(created_at=creado_dt)
            inserted += 1
            print(f"  NUEVO: {codigo} {fin_raw} -> {email_atiende}")
        except Exception as exc:
            print(f"  Fila {i}: ERROR insertando -> {exc}")
            errors += 1
    else:
        print(f"  Fila {i}: MULTI-MATCH {cnt} para {codigo}/{purpose}/{fecha_solo}")
        errors += 1

wb.close()

print()
print("=" * 50)
print(f"Actualizados : {updated}")
print(f"Sin cambios  : {skipped}")
print(f"Insertados   : {inserted}")
print(f"CAP corregidos: {cap_fixed}")
print(f"Errores      : {errors}")
print(f"Total en BD  : {Report.objects.count()}")
if not_found_users:
    print(f"\nEmails en Excel sin cuenta SAI ({len(not_found_users)}):")
    for e in sorted(not_found_users):
        print(f"  {e}")
