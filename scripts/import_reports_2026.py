# -*- coding: utf-8 -*-
"""
Script de importacion de reportes desde CSV Power Apps 2026.
Ejecutar con: python manage.py shell < scripts/import_reports_2026.py
O: python scripts/import_reports_2026.py (desde directorio raiz con venv activo)
"""
import os, sys, csv, glob
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from datetime import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
from acompanamiento.models import Student, Report, ReportStatus

User = get_user_model()

FIN_MAP = {
    'Espiritual':   'ESPIRITUAL',
    'Psicoafectivo':'PSICOAFECTIVO',
    'Convivencia':  'CONVIVENCIA',
    'Acad\xe9mico': 'ACADEMICO',  # latin-1 Académico
    'Academico':    'ACADEMICO',
}

STATUS_MAP = {
    'Seguimiento': ReportStatus.SEGUIMIENTO,
    'Programado':  ReportStatus.PROGRAMADO,
    'Atendido':    ReportStatus.ATENDIDO,
}

files = glob.glob('C:/Users/LENOVO/Downloads/Reportes*.csv')
if not files:
    print('ERROR: No se encontro el archivo CSV')
    sys.exit(1)

fname = files[0]
print('Importando:', fname)

with open(fname, encoding='latin-1') as f:
    rows = list(csv.DictReader(f))

print('Filas en CSV:', len(rows))
print('Columnas:', list(rows[0].keys()))

# Normalizar claves (quitar caracteres especiales)
def clean_key(k):
    return k.encode('latin-1', errors='replace').decode('latin-1')

def lookup_user(email_raw, fallback):
    if not email_raw:
        return fallback
    email = email_raw.strip().lower()
    from django.db.models import Q
    return (
        User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email))
        .filter(is_active=True).first()
        or fallback
    )

created = skipped = errors = 0
not_found_students = []
fallback_user = User.objects.filter(is_superuser=True).first()

for i, raw in enumerate(rows):
    # Normalizar claves a utf-8
    r = {k: v for k, v in raw.items()}

    ext_id = r.get('ID', '').strip()

    # Evitar duplicados por ID externo
    if ext_id and Report.objects.filter(external_id=ext_id).exists():
        skipped += 1
        continue

    # Buscar estudiante por codigo
    codigo = r.get('Codigo', '').strip()
    student = Student.objects.filter(code=codigo).first()
    if not student:
        not_found_students.append(codigo)
        errors += 1
        continue

    # Fin educativo
    fin_raw = r.get('Fines Educativos', '').strip()
    purpose = FIN_MAP.get(fin_raw, '')
    if not purpose:
        # Intento por contenido parcial
        fin_upper = fin_raw.upper()
        if 'SPIRIT' in fin_upper or 'SPIRI' in fin_upper:
            purpose = 'ESPIRITUAL'
        elif 'PSICO' in fin_upper:
            purpose = 'PSICOAFECTIVO'
        elif 'CONVIV' in fin_upper:
            purpose = 'CONVIVENCIA'
        elif 'ACAD' in fin_upper:
            purpose = 'ACADEMICO'
        else:
            print(f'  Fila {i+2}: fin no reconocido -> [{fin_raw}]')
            errors += 1
            continue

    # Estado
    status = STATUS_MAP.get(r.get('Estado', '').strip(), ReportStatus.PROGRAMADO)

    # Usuarios: quien remite y quien atiende
    email_remite  = (r.get('Institucional Quien Remite', '') or
                     r.get('Quien Remite', '') or r.get('Remitente', '')).strip()
    email_atiende = (r.get('Institucional Quien Atiende', '') or
                     r.get('Quien Atiende', '') or r.get('Asignado', '')).strip().lower()
    remite_user  = lookup_user(email_remite, fallback_user)
    assigned_to  = lookup_user(email_atiende, fallback_user)

    # Fecha creacion
    fecha_str = r.get('Creado', '').strip()
    try:
        naive_dt = datetime.strptime(fecha_str, '%d/%m/%Y %H:%M')
        created_at = timezone.make_aware(naive_dt)
    except Exception:
        created_at = timezone.now()

    # Fecha cierre
    fecha_cierre = None
    fc_str = r.get('Fecha de Cierre', '').strip()
    if fc_str:
        try:
            fecha_cierre = timezone.make_aware(datetime.strptime(fc_str, '%d/%m/%Y %H:%M'))
        except Exception:
            pass

    # Periodo y objetivo (columnas con acentos en latin-1)
    objetivo = ''
    periodo  = ''
    for k, v in r.items():
        ku = k.upper()
        if 'OBJETIVO' in ku or 'ACOMPA' in ku:
            objetivo = v.strip()
        if 'PERIODO' in ku or 'ACAD' in ku:
            periodo = v.strip()

    is_accomplished = r.get('Cumple', r.get('Cumpli', '')).strip().lower() in ['si', 'sí', 'yes', '1', 'true']

    try:
        report = Report(
            student=student,
            purpose=purpose,
            fines_educativos=[purpose],
            status=status,
            objective=objetivo,
            academic_period=periodo,
            year=2026,
            external_id=ext_id,
            created_by=remite_user,
            assigned_to=assigned_to,
            institucional_quien_atiende=email_atiende,
            is_accomplished=is_accomplished,
            fecha_cierre=fecha_cierre,
        )
        # Saltamos auto_now_add usando save + update
        report.save()
        Report.objects.filter(pk=report.pk).update(created_at=created_at)
        created += 1
    except Exception as e:
        print(f'  Fila {i+2}: ERROR guardando -> {e}')
        errors += 1

print()
print('=' * 40)
print(f'Importados  : {created}')
print(f'Duplicados  : {skipped}')
print(f'Errores     : {errors}')
print(f'Total en BD : {Report.objects.count()}')
if not_found_students:
    print(f'Estudiantes no encontrados ({len(not_found_students)}): {not_found_students[:10]}')
