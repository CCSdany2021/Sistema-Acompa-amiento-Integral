# -*- coding: utf-8 -*-
"""
Carga las ReglaPermiso iniciales según la configuración del Colegio Calasanz Suba.
Ejecutar: python scripts/seed_reglas_permiso.py

Reglas aplicadas:
  cap / dhiguera / mrodriguez / jgomez  → acceso_global=True (sin reglas)
  pmonsalve / mgordillo / royola        → Espiritual / todas secciones / FIN_EQUIPO
  rarango                               → Espiritual / todas secciones / FIN_COMPLETO
  ncabrera                              → Espiritual / todas secciones / FIN_COMPLETO
                                        + * / todas secciones / SOLO_ASIGNADO
  mpedraza                              → * / preescolar / FIN_COMPLETO
  yalejo                                → * / basica_secundaria / FIN_COMPLETO
  aardila                               → Psico+Acad+Conv / basica_primaria / FIN_COMPLETO
  itang                                 → Psico+Acad+Conv / preescolar / FIN_COMPLETO
  mmonroy                               → Espiritual / basica_secundaria / FIN_COMPLETO
  ngarzon                               → Psico / todas / FIN_COMPLETO
                                        + Academico / basica_secundaria / SOLO_ASIGNADO
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()

from django.contrib.auth import get_user_model
from acompanamiento.models import Educador, ReglaPermiso, ScopePermiso

User = get_user_model()

FC = ScopePermiso.FIN_COMPLETO
SA = ScopePermiso.SOLO_ASIGNADO
FE = ScopePermiso.FIN_EQUIPO

# username → lista de (fin_educativo, seccion, scope)
# fin vacío = todos los fines | sección vacía = todas las secciones
REGLAS = {
    # Globales: sin reglas, tienen acceso_global=True
    'cap@calasanzsuba.edu.co':       None,
    'dhiguera@calasanzsuba.edu.co':  None,
    'mrodriguez@calasanzsuba.edu.co':None,
    'jgomez@calasanzsuba.edu.co':    None,

    # Espiritual – equipo (ven lo asignado a ellos y a sus compañeros de espiritual)
    'pmonsalve@calasanzsuba.edu.co': [('ESPIRITUAL', '',               FE)],
    'mgordillo@calasanzsuba.edu.co': [('ESPIRITUAL', '',               FE)],
    'royola@calasanzsuba.edu.co':    [('ESPIRITUAL', '',               FE)],

    # Espiritual – coordinador (ve todo lo espiritual sin importar asignación)
    'rarango@calasanzsuba.edu.co':   [('ESPIRITUAL', '',               FC)],

    # Espiritual completo + lo que le asignen de otros fines
    'ncabrera@calasanzsuba.edu.co':  [
        ('ESPIRITUAL', '', FC),   # todo lo espiritual
        ('',            '', SA),  # lo demás solo si está asignado a ella
    ],

    # Coordinadores de sección – todos los fines de su sección
    'mpedraza@calasanzsuba.edu.co':  [('', 'preescolar',        FC)],
    'yalejo@calasanzsuba.edu.co':    [('', 'basica_secundaria',  FC)],

    # Docentes de sección con fines específicos
    'aardila@calasanzsuba.edu.co':   [
        ('PSICOAFECTIVO', 'basica_primaria', FC),
        ('ACADEMICO',     'basica_primaria', FC),
        ('CONVIVENCIA',   'basica_primaria', FC),
    ],
    'itang@calasanzsuba.edu.co':     [
        ('PSICOAFECTIVO', 'preescolar', FC),
        ('ACADEMICO',     'preescolar', FC),
        ('CONVIVENCIA',   'preescolar', FC),
    ],
    'mmonroy@calasanzsuba.edu.co':   [('ESPIRITUAL', 'basica_secundaria', FC)],

    # Psicoafectivo en todas las secciones + Académico solo asignado en su sección
    'ngarzon@calasanzsuba.edu.co':   [
        ('PSICOAFECTIVO', '',                FC),
        ('ACADEMICO',     'basica_secundaria', SA),
    ],
}

created = updated = skipped = 0

for username, reglas in REGLAS.items():
    user = User.objects.filter(username=username).first()
    if not user:
        print(f'[!] Usuario no encontrado: {username}')
        continue

    ed = Educador.objects.filter(user=user).first()
    if not ed:
        print(f'[!] Sin perfil Educador: {username}')
        continue

    # Asegurar acceso_global correcto
    if reglas is None:
        if not ed.acceso_global:
            ed.acceso_global = True
            ed.save(update_fields=['acceso_global'])
            print(f'[OK] {username}: acceso_global=True')
        else:
            print(f'[--] {username}: ya era global')
        skipped += 1
        continue

    # Para no-globales: quitar acceso_global y reemplazar reglas
    if ed.acceso_global:
        ed.acceso_global = False
        ed.save(update_fields=['acceso_global'])

    # Borrar reglas anteriores y crear las nuevas
    deleted, _ = ReglaPermiso.objects.filter(educador=ed).delete()
    for fin, sec, scope in reglas:
        ReglaPermiso.objects.create(
            educador=ed,
            fin_educativo=fin,
            seccion=sec,
            scope=scope,
        )
    resumen = ' | '.join(f'{r[0] or "*"}/{r[1] or "*"}/{r[2]}' for r in reglas)
    print(f'[OK] {username}: {deleted} borradas, {len(reglas)} creadas | {resumen}')
    created += len(reglas)

print()
print('='*50)
print(f'Reglas creadas  : {created}')
print(f'Globales conf.  : {skipped}')
print()

# Verificar resultado
print('Verificación final:')
print('-'*60)
from acompanamiento.models import Report
from acompanamiento.permissions import filter_reports_for_user, has_global_access

total = Report.objects.count()
for ed in Educador.objects.select_related('user').prefetch_related('reglas').order_by('user__username'):
    u = ed.user
    count = filter_reports_for_user(Report.objects.all(), u).count()
    modo = 'GLOBAL' if has_global_access(u) else f'{ed.reglas.count()} reglas'
    print(f'  {u.username:<35} {modo:<12} {count}/{total} reportes')
