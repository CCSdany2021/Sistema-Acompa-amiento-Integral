# -*- coding: utf-8 -*-
"""
Corrige created_by y assigned_to en reportes importados del CSV de Power Apps.
El CSV tiene nombre en 'Quien Remite' (no email), entonces se construye un mapa
nombre→email cruzando 'Quien Atiende' con 'Institucional Quien Atiende'.

Uso:
    python scripts/fix_report_users.py
"""
import os, sys, csv, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Q
from acompanamiento.models import Report

User = get_user_model()


def build_name_map(rows):
    """Construye {nombre_normalizado: email} desde Quien Atiende + Institucional Quien Atiende."""
    name_map = {}
    for r in rows:
        name = (r.get('Quien Atiende') or '').strip()
        email = (r.get('Institucional Quien Atiende') or '').strip().lower()
        if name and email and '@' in email:
            name_map[name.lower()] = email
            # Indexar también por apellidos (últimas 1-2 palabras) para match parcial
            parts = name.lower().split()
            if len(parts) >= 2:
                name_map[parts[-1]] = email
                name_map[' '.join(parts[-2:])] = email
    return name_map


def fuzzy_name_lookup(full_name, name_map):
    """Busca email por nombre completo usando intersección de palabras."""
    if not full_name:
        return None
    words = set(full_name.lower().split())
    best_email, best_score = None, 0
    for stored_name, email in name_map.items():
        stored_words = set(stored_name.split())
        score = len(words & stored_words)
        if score > best_score:
            best_score, best_email = score, email
    return best_email if best_score >= 2 else None


def lookup_user_by_email(email_raw):
    if not email_raw:
        return None
    email = email_raw.strip().lower()
    return (
        User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email))
        .filter(is_active=True)
        .first()
    )


files = sorted(glob.glob('C:/Users/LENOVO/Downloads/Reportes*.csv'))
if not files:
    print('ERROR: No se encontró el CSV en Downloads.')
    sys.exit(1)

fname = files[-1]
print(f'Leyendo: {fname}')

with open(fname, encoding='latin-1') as f:
    rows = list(csv.DictReader(f))

print(f'Filas en CSV: {len(rows)}')

name_map = build_name_map(rows)
print(f'Mapa nombre-email construido: {len(name_map)} entradas')

# Mostrar mapa para diagnóstico
print('\nMapa nombre→email:')
seen = set()
for k, v in name_map.items():
    if v not in seen:
        print(f'  {k!r} : {v}')
        seen.add(v)

updated = skipped = not_found = no_remite = 0

print('\nProcesando reportes...')
for raw in rows:
    ext_id = raw.get('ID', '').strip()
    if not ext_id:
        continue

    report = Report.objects.filter(external_id=ext_id).first()
    if not report:
        not_found += 1
        continue

    # --- Quien Remite: nombre → buscar email en mapa ---
    nombre_remite = (raw.get('Quien Remite') or '').strip()
    email_remite = fuzzy_name_lookup(nombre_remite, name_map)
    if not email_remite:
        # Si el campo ya parece un email, usarlo directo
        if '@' in nombre_remite:
            email_remite = nombre_remite
        else:
            no_remite += 1

    # --- Quien Atiende: ya tiene email institucional ---
    email_atiende = (raw.get('Institucional Quien Atiende') or '').strip()

    user_remite  = lookup_user_by_email(email_remite)
    user_atiende = lookup_user_by_email(email_atiende)

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
print(f'Sin remitente: {no_remite}  (nombre no matcheó ningún usuario)')
