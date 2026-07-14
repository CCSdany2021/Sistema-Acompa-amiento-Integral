import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth import get_user_model
from acompanamiento.models import Educador, ReglaPermiso

User = get_user_model()

print("=== TODOS LOS USUARIOS Y SU ESTADO ===")
for u in User.objects.filter(is_active=True).order_by('email'):
    try:
        ed = u.educador
        reglas = list(ed.reglas.all())
        if reglas:
            reg_parts = []
            for r in reglas:
                fin = r.fin_educativo or '*'
                sec = r.seccion or '*'
                reg_parts.append(fin + '/' + sec + '=' + r.scope[:4])
            reg_str = ', '.join(reg_parts)
        else:
            reg_str = 'SIN REGLAS'
        status = 'GLOBAL' if ed.acceso_global else 'reglas'
        print(f"  {u.email} | {status} | {reg_str}")
    except Exception:
        print(f"  {u.email} | SIN PERFIL EDUCADOR")
