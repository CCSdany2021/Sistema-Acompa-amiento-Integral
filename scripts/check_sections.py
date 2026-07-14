import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from acompanamiento.models import Student, Report
from django.db.models import Count

# Ver el modelo Course para entender la estructura
from acompanamiento.models import Course
c = Course.objects.first()
print("Campos de Course:", [f.name for f in Course._meta.get_fields()])
print()

# Ver cursos unicos con su seccion
print("=== Cursos unicos y seccion en BD ===")
for row in Course.objects.values('name', 'section').annotate(n=Count('id')).order_by('section', 'name'):
    print(f"  course_name={row['name']!r}  section={row['section']!r}  n={row['n']}")

print()
# Cursos con grade 6 y 7 (600-799) que estan en basica_secundaria
print("=== Estudiantes con cursos 6xx y 7xx ===")
for s in Student.objects.filter(course__name__in=['601','602','603','604','605','701','702','703','704','705']).values('course__name','section').annotate(n=Count('id')):
    print(f"  course={s['course__name']!r}  section={s['section']!r}  n={s['n']}")
