"""
Management command: Valida que todos los educadores estén correctamente configurados
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from acompanamiento.models import Educador, Report, Observation, Recommendation
from acompanamiento.permissions import can_create_reports

User = get_user_model()

class Command(BaseCommand):
    help = 'Valida la configuración de educadores y el desplegable "Quién atenderá"'

    def print_header(self, text):
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"  {text}")
        self.stdout.write(f"{'='*80}\n")

    def print_section(self, text):
        self.stdout.write(f"\n► {text}")
        self.stdout.write("-" * 60)

    def handle(self, *args, **options):
        self.print_header("VALIDACIÓN DE EDUCADORES - SISTEMA DE ACOMPAÑAMIENTO INTEGRAL")

        self.print_section("1. USUARIOS ACTIVOS CON PERFIL EDUCADOR")

        educadores = Educador.objects.select_related('user').all()

        if not educadores.exists():
            self.stdout.write(self.style.ERROR("❌ NO HAY EDUCADORES CONFIGURADOS"))
            self.stdout.write("   → Crea perfiles de Educador en /admin/acompanamiento/educador/")
            return

        self.stdout.write(f"Total de Educadores: {educadores.count()}\n")

        active_count = 0
        inactive_count = 0
        issues = []

        for ed in educadores:
            user_status = self.style.SUCCESS("✅ ACTIVO") if ed.user.is_active else self.style.ERROR("❌ INACTIVO")
            ed_status = self.style.SUCCESS("✅") if ed.is_active else self.style.ERROR("❌")
            can_create = self.style.SUCCESS("✅") if can_create_reports(ed.user) else self.style.ERROR("❌")

            self.stdout.write(f"  {ed_status} {ed.user.get_full_name() or ed.user.username}")
            self.stdout.write(f"     Email: {ed.user.email}")
            self.stdout.write(f"     User: {user_status} | Educador: {'✅ ACTIVO' if ed.is_active else '❌ INACTIVO'}")
            self.stdout.write(f"     Puede crear reportes: {can_create}")
            self.stdout.write(f"     Rol: {ed.get_rol_display()}")
            self.stdout.write(f"     Fines educativos: {ed.fines_educativos if ed.fines_educativos else '(ninguno configurado)'}")

            # Contar reportes asignados
            reports = Report.objects.filter(assigned_to=ed.user).count()
            obs = Observation.objects.filter(created_by=ed.user).count()
            recs = Recommendation.objects.filter(created_by=ed.user).count()
            self.stdout.write(f"     Reportes asignados: {reports} | Observaciones: {obs} | Recomendaciones: {recs}")

            if ed.user.is_active and ed.is_active:
                active_count += 1
            else:
                inactive_count += 1
                issues.append(f"{ed.user.get_full_name()} no está completamente activo")

            if not ed.fines_educativos:
                issues.append(f"{ed.user.get_full_name()} no tiene fines educativos configurados")

            self.stdout.write()

        self.print_section("2. RESUMEN DE ESTADO")
        self.stdout.write(self.style.SUCCESS(f"✅ Educadores ACTIVOS: {active_count}"))
        self.stdout.write(self.style.ERROR(f"❌ Educadores INACTIVOS: {inactive_count}"))

        if issues:
            self.print_section("3. ⚠️  PROBLEMAS DETECTADOS")
            for i, issue in enumerate(issues, 1):
                self.stdout.write(self.style.WARNING(f"  {i}. {issue}"))
        else:
            self.print_section("3. ✅ TODO ESTÁ BIEN CONFIGURADO")
            self.stdout.write("   Todos los educadores están activos y listos para usar")

        self.print_section("4. USUARIOS QUE APARECERÁN EN EL DESPLEGABLE 'QUIÉN ATENDERÁ'")

        eligible = Educador.objects.filter(
            is_active=True,
            user__is_active=True
        ).select_related('user').order_by('user__first_name', 'user__last_name')

        if not eligible.exists():
            self.stdout.write(self.style.ERROR("❌ NO HAY EDUCADORES ELEGIBLES PARA ASIGNAR"))
            self.stdout.write("   → Verifica que al menos un educador tenga is_active=True\n")
            return

        self.stdout.write(self.style.SUCCESS(f"Total que aparecerán: {eligible.count()}\n"))
        for ed in eligible:
            self.stdout.write(self.style.SUCCESS(f"  ✅ {ed.user.get_full_name() or ed.user.username}"))
            self.stdout.write(f"     ID: {ed.user.id} | Email: {ed.user.email}")
            self.stdout.write(f"     Fines: {', '.join(ed.fines_educativos) if ed.fines_educativos else '(todos)'}")
            self.stdout.write()

        self.print_section("5. VERIFICACIÓN DE PERMISOS")

        all_ok = True
        for ed in eligible:
            can_create = can_create_reports(ed.user)
            if not can_create:
                self.stdout.write(self.style.ERROR(f"❌ {ed.user.get_full_name()}: NO PUEDE crear reportes"))
                all_ok = False
            else:
                self.stdout.write(self.style.SUCCESS(f"✅ {ed.user.get_full_name()}: Puede crear reportes, observaciones y recomendaciones"))

        if all_ok:
            self.print_section(self.style.SUCCESS("✅ SISTEMA LISTO"))
            self.stdout.write("Todos los educadores están correctamente configurados:")
            self.stdout.write("• Usuarios activos")
            self.stdout.write("• Perfiles Educador activos")
            self.stdout.write("• Pueden crear/editar reportes, observaciones y recomendaciones")
            self.stdout.write("• Aparecerán en el desplegable 'Quién atenderá'")
        else:
            self.print_section(self.style.ERROR("❌ SE ENCONTRARON PROBLEMAS"))
            self.stdout.write("Revisa los problemas indicados arriba y ejecuta este comando nuevamente")

        self.stdout.write()
