"""
Revisa y limpia reglas duplicadas para todos los usuarios.
Detecta si el backend puede guardar el perfil de cada uno.
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth import get_user_model
from acompanamiento.models import Educador, ReglaPermiso, Section

User = get_user_model()

print("=== VERIFICANDO Y LIMPIANDO REGLAS DUPLICADAS ===\n")

for u in User.objects.filter(is_active=True).order_by('email'):
    try:
        ed = u.educador
    except Exception:
        # Sin perfil - crear uno
        ed = Educador.objects.create(user=u)
        print(f"  CREADO perfil para: {u.email}")
        continue

    # Detectar duplicados: misma combo fin+sec+scope
    reglas = list(ed.reglas.all())
    seen = set()
    dups = []
    for r in reglas:
        key = (r.fin_educativo, r.seccion, r.scope)
        if key in seen:
            dups.append(r)
        else:
            seen.add(key)

    if dups:
        print(f"  {u.email} — {len(dups)} regla(s) duplicada(s) eliminada(s):")
        for d in dups:
            print(f"    Eliminando id={d.id} fin={d.fin_educativo!r} sec={d.seccion!r} scope={d.scope}")
            d.delete()

    # Verificar que el save funciona
    try:
        ed.save()
        # Probar set de secciones vacías
        ed.secciones.set(Section.objects.none())
    except Exception as e:
        print(f"  ERROR guardando {u.email}: {e}")
        continue

print()
print("=== ESTADO FINAL DE REGLAS ===\n")
for u in User.objects.filter(is_active=True).order_by('email'):
    try:
        ed = u.educador
        reglas = list(ed.reglas.all())
        if ed.acceso_global:
            estado = "GLOBAL"
        elif reglas:
            parts = []
            for r in reglas:
                fin = r.fin_educativo or '*'
                sec = r.seccion or '*'
                parts.append(fin + '/' + sec + '=' + r.scope[:4])
            estado = ', '.join(parts)
        else:
            estado = 'SIN REGLAS'
        print(f"  {u.email} | {estado}")
    except Exception:
        print(f"  {u.email} | SIN PERFIL")

print()
print("Verificacion completada.")
