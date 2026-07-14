#!/usr/bin/env python
"""
Script para actualizar todos los educadores con los fines educativos correctos
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from acompanamiento.models import Educador
from django.contrib.auth import get_user_model

User = get_user_model()

# Todos los fines disponibles
TODOS_LOS_FINES = ['ACADEMICO', 'CONVIVENCIA', 'ESPIRITUAL', 'PSICOAFECTIVO']

print("\n" + "="*80)
print("ACTUALIZACION DE EDUCADORES CON FINES EDUCATIVOS")
print("="*80 + "\n")

# 1. Primero, mostrar estado actual
print("ESTADO ACTUAL:\n")
educadores = Educador.objects.select_related('user').all().order_by('user__first_name')

for ed in educadores:
    print(f"[USER] {ed.user.get_full_name() or ed.user.username}")
    print(f"   Email: {ed.user.email}")
    print(f"   Educador Active: {ed.is_active} | User Active: {ed.user.is_active}")
    print(f"   Fines: {ed.fines_educativos if ed.fines_educativos else 'VACIO'}")
    print()

# 2. Actualizar educadores sin fines educativos
print("\nACTUALIZANDO EDUCADORES...\n")

educadores_actualizados = 0

for ed in educadores:
    # Si no tiene fines configurados, asignar TODOS
    if not ed.fines_educativos or len(ed.fines_educativos) == 0:
        ed.fines_educativos = TODOS_LOS_FINES.copy()
        ed.save()
        educadores_actualizados += 1
        print(f"[OK] {ed.user.get_full_name()}: Asignados todos los fines")
    # Si tiene algunos pero no todos, completar
    elif len(ed.fines_educativos) < len(TODOS_LOS_FINES):
        fines_faltantes = [f for f in TODOS_LOS_FINES if f not in ed.fines_educativos]
        ed.fines_educativos.extend(fines_faltantes)
        ed.save()
        educadores_actualizados += 1
        print(f"[OK] {ed.user.get_full_name()}: Agregados fines: {', '.join(fines_faltantes)}")
    else:
        print(f"[OK] {ed.user.get_full_name()}: Ya tiene todos los fines")

print(f"\n[OK] Educadores actualizados: {educadores_actualizados}")

# 3. Mostrar estado final
print("\nESTADO FINAL:\n")
educadores = Educador.objects.select_related('user').all().order_by('user__first_name')

for ed in educadores:
    print(f"[USER] {ed.user.get_full_name() or ed.user.username}")
    print(f"   Fines: {ed.fines_educativos}")
    print()

print("="*80)
print("[OK] ACTUALIZACION COMPLETADA")
print("="*80 + "\n")
print("PROXIMOS PASOS:")
print("1. Recarga la pagina del formulario en el navegador (Ctrl+F5)")
print("2. Crea un nuevo reporte y verifica que aparezcan todos los educadores")
print("3. El desplegable debe mostrar todos los que correspondan por fin educativo")
print()
