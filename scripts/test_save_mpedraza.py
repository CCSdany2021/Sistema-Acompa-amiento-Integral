"""Simula exactamente lo que hace la vista al guardar perfil de mpedraza."""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth import get_user_model
from acompanamiento.models import Educador
from acompanamiento.models import Section

User = get_user_model()

u = User.objects.get(email='mpedraza@calasanzsuba.edu.co')
print(f"Usuario: {u.get_full_name()} (id={u.id})")

try:
    ed, created = Educador.objects.get_or_create(user=u)
    print(f"Educador: id={ed.id} created={created}")
    print(f"  rol={ed.rol} global={ed.acceso_global} active={ed.is_active}")
    print(f"  fines_educativos={ed.fines_educativos!r}")

    # Simular el POST del formulario
    ed.rol = 'ADMIN_SECCION'
    ed.acceso_global = False
    ed.is_active = True
    ed.fines_educativos = []  # getlist vacío
    ed.save()
    ed.secciones.set(Section.objects.none())
    print("  GUARDADO OK")

    print()
    print("Reglas actuales:")
    for r in ed.reglas.all():
        print(f"  id={r.id} fin={r.fin_educativo!r} sec={r.seccion!r} scope={r.scope}")

except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
