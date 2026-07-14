import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth import get_user_model
from acompanamiento.models import Report, Student, Educador, ReglaPermiso
from acompanamiento.permissions import filter_reports_for_user
from django.db.models import Count

User = get_user_model()
u = User.objects.get(email='aardila@calasanzsuba.edu.co')

total = filter_reports_for_user(Report.objects.all(), u).count()
asignados = Report.objects.filter(assigned_to=u).count()
print(f'Reportes visibles aardila: {total}')
print(f'Reportes asignados a ella: {asignados}')

print()
print('Reglas de aardila:')
for r in u.educador.reglas.all():
    print(f'  fin={r.fin_educativo!r} sec={r.seccion!r} scope={r.scope}')

print()
print('Distribucion de estudiantes por seccion:')
for row in Student.objects.values('section').annotate(n=Count('id')).order_by('section'):
    print(f"  {row['section']!r}: {row['n']}")

print()
print('Reportes visibles por seccion de estudiante:')
qs = filter_reports_for_user(Report.objects.all(), u)
for row in qs.values('student__section').annotate(n=Count('id')).order_by('student__section'):
    print(f"  {row['student__section']!r}: {row['n']}")
