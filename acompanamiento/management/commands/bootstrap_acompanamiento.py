from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from acompanamiento.models import Educador, Grado, Section, UserRole


class Command(BaseCommand):
    help = "Inicializa secciones base y perfiles Educador."

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-email",
            type=str,
            help="Email del usuario a configurar como ADMIN.",
        )
        parser.add_argument(
            "--coordinador-email",
            type=str,
            help="Email del usuario a configurar como COORDINADOR.",
        )
        parser.add_argument(
            "--coordinador-seccion",
            type=str,
            help="Nombre exacto de la sección del coordinador.",
        )
        parser.add_argument(
            "--docente-email",
            action="append",
            default=[],
            help="Email de usuario a configurar como DOCENTE. Puede repetirse.",
        )

    def handle(self, *args, **options):
        user_model = get_user_model()

        sections_seed = [
            ("Jardín a Tercero", Grado.PREESCOLAR),
            ("Cuarto a Séptimo", Grado.PRIMARIA),
            ("Octavo a Undécimo", Grado.BACHILLERATO),
        ]

        created_sections = 0
        for name, grado in sections_seed:
            _, created = Section.objects.get_or_create(name=name, defaults={"grado": grado})
            if created:
                created_sections += 1

        self.stdout.write(self.style.SUCCESS(f"Secciones creadas: {created_sections}"))

        # 1) Superusers -> ADMIN por defecto
        superusers = user_model.objects.filter(is_superuser=True)
        super_count = 0
        for user in superusers:
            _, _ = Educador.objects.update_or_create(
                user=user,
                defaults={"rol": UserRole.ADMIN, "is_active": True},
            )
            super_count += 1
        self.stdout.write(self.style.SUCCESS(f"Superusuarios configurados como ADMIN: {super_count}"))

        # 2) Admin por email (opcional)
        admin_email = options.get("admin_email")
        if admin_email:
            try:
                admin_user = user_model.objects.get(email=admin_email)
            except user_model.DoesNotExist as exc:
                raise CommandError(f"No existe usuario con email: {admin_email}") from exc

            Educador.objects.update_or_create(
                user=admin_user,
                defaults={"rol": UserRole.ADMIN, "is_active": True},
            )
            self.stdout.write(self.style.SUCCESS(f"ADMIN configurado: {admin_email}"))

        # 3) Coordinador por email + sección (opcional)
        coord_email = options.get("coordinador_email")
        coord_section_name = options.get("coordinador_seccion")
        if coord_email or coord_section_name:
            if not (coord_email and coord_section_name):
                raise CommandError("Debes enviar --coordinador-email y --coordinador-seccion juntos.")

            try:
                coord_user = user_model.objects.get(email=coord_email)
            except user_model.DoesNotExist as exc:
                raise CommandError(f"No existe usuario con email: {coord_email}") from exc

            try:
                coord_section = Section.objects.get(name=coord_section_name)
            except Section.DoesNotExist as exc:
                raise CommandError(f"No existe sección: {coord_section_name}") from exc

            Educador.objects.update_or_create(
                user=coord_user,
                defaults={
                    "rol": UserRole.COORDINADOR,
                    "seccion_asignada": coord_section,
                    "is_active": True,
                },
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"COORDINADOR configurado: {coord_email} -> {coord_section_name}"
                )
            )

        # 4) Docentes por email (opcional)
        docente_emails = options.get("docente_email", [])
        docentes_count = 0
        for email in docente_emails:
            try:
                docente_user = user_model.objects.get(email=email)
            except user_model.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Docente no encontrado, se omite: {email}"))
                continue

            Educador.objects.update_or_create(
                user=docente_user,
                defaults={"rol": UserRole.DOCENTE, "is_active": True},
            )
            docentes_count += 1

        if docentes_count:
            self.stdout.write(self.style.SUCCESS(f"DOCENTES configurados: {docentes_count}"))

        self.stdout.write(self.style.SUCCESS("Bootstrap de acompañamiento completado."))

