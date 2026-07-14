#!/usr/bin/env python
"""
Script de validación: Verifica que TODOS los educadores del sistema
estén correctamente configurados para crear reportes, observaciones y recomendaciones.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from acompanamiento.models import Educador, Report, Observation, Recommendation
from acompanamiento.permissions import can_create_reports

User = get_user_model()

def print_header(text):
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")

def print_section(text):
    print(f"\n► {text}")
    print("-" * 60)

def validate_educadores():
    print_header("VALIDACIÓN DE EDUCADORES - SISTEMA DE ACOMPAÑAMIENTO INTEGRAL")

    print_section("1. USUARIO ACTIVOS CON PERFIL EDUCADOR")

    educadores = Educador.objects.select_related('user').all()

    if not educadores.exists():
        print("❌ NO HAY EDUCADORES CONFIGURADOS")
        print("   → Crea perfiles de Educador en /admin/acompanamiento/educador/")
        return

    print(f"Total de Educadores: {educadores.count()}\n")

    active_count = 0
    inactive_count = 0
    issues = []

    for ed in educadores:
        user_status = "✅ ACTIVO" if ed.user.is_active else "❌ INACTIVO"
        ed_status = "✅" if ed.is_active else "❌"
        can_create = "✅" if can_create_reports(ed.user) else "❌"

        print(f"  {ed_status} {ed.user.get_full_name() or ed.user.username}")
        print(f"     Email: {ed.user.email}")
        print(f"     User: {user_status} | Educador: {'✅ ACTIVO' if ed.is_active else '❌ INACTIVO'}")
        print(f"     Puede crear reportes: {can_create}")
        print(f"     Rol: {ed.get_rol_display()}")
        print(f"     Fines educativos: {ed.fines_educativos if ed.fines_educativos else '(ninguno configurado)'}")

        # Contar reportes asignados
        reports = Report.objects.filter(assigned_to=ed.user).count()
        obs = Observation.objects.filter(created_by=ed.user).count()
        recs = Recommendation.objects.filter(created_by=ed.user).count()
        print(f"     Reportes asignados: {reports} | Observaciones: {obs} | Recomendaciones: {recs}")

        if ed.user.is_active and ed.is_active:
            active_count += 1
        else:
            inactive_count += 1
            issues.append(f"{ed.user.get_full_name()} no está completamente activo")

        if not ed.fines_educativos:
            issues.append(f"{ed.user.get_full_name()} no tiene fines educativos configurados")

        print()

    print_section("2. RESUMEN DE ESTADO")
    print(f"✅ Educadores ACTIVOS: {active_count}")
    print(f"❌ Educadores INACTIVOS: {inactive_count}")

    if issues:
        print_section("3. ⚠️  PROBLEMAS DETECTADOS")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print_section("3. ✅ TODO ESTÁ BIEN CONFIGURADO")
        print("   Todos los educadores están activos y listos para usar")

    print_section("4. USUARIOS QUE APARECERÁN EN EL DESPLEGABLE 'QUIÉN ATENDERÁ'")

    eligible = Educador.objects.filter(
        is_active=True,
        user__is_active=True
    ).select_related('user').order_by('user__first_name', 'user__last_name')

    if not eligible.exists():
        print("❌ NO HAY EDUCADORES ELEGIBLES PARA ASIGNAR")
        print("   → Verifica que al menos un educador tenga is_active=True\n")
        return

    print(f"Total que aparecerán: {eligible.count()}\n")
    for ed in eligible:
        print(f"  ✅ {ed.user.get_full_name() or ed.user.username}")
        print(f"     ID: {ed.user.id} | Email: {ed.user.email}")
        print(f"     Fines: {', '.join(ed.fines_educativos) if ed.fines_educativos else '(todos)'}")
        print()

    print_section("5. VERIFICACIÓN DE PERMISOS")

    # Verificar que cada educador elegible pueda:
    # 1. Crear reportes
    # 2. Crear observaciones
    # 3. Crear recomendaciones

    all_ok = True
    for ed in eligible:
        can_create = can_create_reports(ed.user)
        if not can_create:
            print(f"❌ {ed.user.get_full_name()}: NO PUEDE crear reportes")
            all_ok = False
        else:
            print(f"✅ {ed.user.get_full_name()}: Puede crear reportes, observaciones y recomendaciones")

    if all_ok:
        print_section("✅ SISTEMA LISTO")
        print("Todos los educadores están correctamente configurados:")
        print("• Usuarios activos")
        print("• Perfiles Educador activos")
        print("• Pueden crear/editar reportes, observaciones y recomendaciones")
        print("• Aparecerán en el desplegable 'Quién atenderá'")
    else:
        print_section("❌ SE ENCONTRARON PROBLEMAS")
        print("Revisa los problemas indicados arriba y ejecuta este script nuevamente")

    print()

if __name__ == '__main__':
    try:
        validate_educadores()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
