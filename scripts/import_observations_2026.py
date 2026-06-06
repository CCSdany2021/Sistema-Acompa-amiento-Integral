# -*- coding: utf-8 -*-
import os, sys, csv, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()

from datetime import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
from acompanamiento.models import Student, Report, Observation

User = get_user_model()

FINES_MAP = {
    'Espiritual':    'ESPIRITUAL',
    'Psicoafectivo': 'PSICOAFECTIVO',
    'Convivencia':   'CONVIVENCIA',
    'Acad\xe9mico':  'ACADEMICO',
    'Academico':     'ACADEMICO',
}

def get(row, *keys):
    for k in row:
        ku = k.strip().lstrip('﻿').upper()
        for kk in keys:
            if kk.upper() in ku:
                return row[k].strip()
    return ''

files = glob.glob('C:/Users/LENOVO/Downloads/Observaciones*.csv')
fname = files[0]
print('Importando:', fname)

with open(fname, encoding='latin-1') as f:
    rows = list(csv.DictReader(f))

print(f'Total filas: {len(rows)}')

fallback_user = User.objects.filter(is_superuser=True).first()
created = skipped = errors = 0
omitidas = []

for i, row in enumerate(rows):
    codigo   = get(row, 'CODIGO')
    fin_raw  = get(row, 'FIN_EDU', 'FIN')
    contenido = get(row, 'OBSERVA')
    fecha_str = get(row, 'FECHA')
    correo   = get(row, 'CORREO', 'QUIEN_AT', 'QUIENA')
    creado_str = get(row, 'CREADO')
    titulo   = get(row, 'TITUL')

    fin = FINES_MAP.get(fin_raw, '')
    if not fin:
        for k, v in FINES_MAP.items():
            if k.upper() in fin_raw.upper():
                fin = v
                break

    if not codigo or not fin or not contenido:
        errors += 1
        continue

    student = Student.objects.filter(code=codigo).first()
    if not student:
        errors += 1
        continue

    report = Report.objects.filter(student=student, purpose=fin).first()
    if not report:
        omitidas.append(f'{codigo} | {student.full_name} | {fin}')
        skipped += 1
        continue

    # Fecha de seguimiento
    followup = None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d/%m/%Y %H:%M'):
        try:
            followup = datetime.strptime(fecha_str, fmt).date()
            break
        except Exception:
            pass

    # Fecha de creacion
    date_log = timezone.now()
    for fmt in ('%d/%m/%Y %H:%M', '%d/%m/%Y'):
        try:
            date_log = timezone.make_aware(datetime.strptime(creado_str, fmt))
            break
        except Exception:
            pass

    # Usuario
    assigned = None
    if correo:
        assigned = User.objects.filter(username=correo.lower()).first()

    obs = Observation(
        report=report,
        title=titulo[:200] if titulo else '',
        content=contenido,
        correo_institucional=correo.lower() if correo else '',
        fin_educativo=fin,
        followup_date=followup,
        created_by=assigned or fallback_user,
    )
    obs.save()
    Observation.objects.filter(pk=obs.pk).update(date_log=date_log)
    created += 1

print()
print('=' * 45)
print(f'Importadas  : {created}')
print(f'Omitidas    : {skipped}  (sin reporte en BD)')
print(f'Errores     : {errors}')
print(f'Total en BD : {Observation.objects.count()}')
if omitidas:
    print(f'\nOmitidas ({len(omitidas)}):')
    for o in omitidas:
        print(f'  {o}')
