# -*- coding: utf-8 -*-
"""
Corrige created_by y assigned_to en reportes importados del CSV de Power Apps.
El script original asignaba siempre el superuser (cap@...) como created_by.

Uso:
    python scripts/fix_report_users.py
    python manage.py shell < scripts/fix_report_users.py
"""
import os, sys, csv, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Q
from acompanamiento.models import Report

User = get_user_model()


def lookup_user(email_raw):
    """Busca usuario por username o email, case-insensitive."""
    if not email_raw:
        return None
    email = email_raw.strip().lower()
    return (
        User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email))
        .filter(is_active=True)
        .first()
    )


files = glob.glob('C:/Users/LENOVO/Downloads/Reportes*.csv')
if not files:
    print('ERROR: No se encontró el CSV en Downloads. Coloca el archivo Reportes*.csv ahí.')
    sys.exit(1)

fname = files[0]
print(f'Leyendo: {fname}')

with open(fname, encoding='latin-1') as f:
    rows = list(csv.DictReader(f))

print(f'Filas en CSV: {len(rows)}')

# Mostrar columnas disponibles para diagnóstico
if rows:
    cols = list(rows[0].keys())
    print(f'Columnas: {cols}')

updated = skipped = not_found = 0

for raw in rows:
    ext_id = raw.get('ID', '').strip()
    if not ext_id:
        continue

    report = Report.objects.filter(external_id=ext_id).first()
    if not report:
        not_found += 1
        continue

    # Buscar quien remite (varios nombres posibles de columna)
    email_remite = (
        raw.get('Institucional Quien Remite', '') or
        raw.get('Quien Remite', '') or
        raw.get('Remitente', '') or
        raw.get('Email Remite', '') or
        ''
    ).strip()

    email_atiende = (
        raw.get('Institucional Quien Atiende', '') or
        raw.get('Quien Atiende', '') or
        raw.get('Asignado', '') or
        ''
    ).strip()

    user_remite  = lookup_user(email_remite)
    user_atiende = lookup_user(email_atiende)

    changed = False
    if user_remite and report.created_by != user_remite:
        report.created_by = user_remite
        changed = True
    if user_atiende and report.assigned_to != user_atiende:
        report.assigned_to = user_atiende
        changed = True

    if changed:
        report.save(update_fields=['created_by', 'assigned_to'])
        updated += 1
    else:
        skipped += 1

print()
print('=' * 45)
print(f'Actualizados : {updated}')
print(f'Sin cambio   : {skipped}')
print(f'No en BD     : {not_found}')
print()

# Diagnóstico: mostrar columnas de remite/atiende del primer registro
if rows:
    r = rows[0]
    print('--- Diagnóstico primera fila ---')
    for k, v in r.items():
        ku = k.upper()
        if any(x in ku for x in ['REMIT', 'ATIEN', 'ASIGN', 'EMAIL', 'QUIEN']):
            print(f'  {k!r}: {v!r}')
