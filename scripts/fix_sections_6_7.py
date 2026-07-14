"""
Corrige la seccion de estudiantes de grado 6 y 7.
El colegio los agrupa en 'Cuarto-Septimo' (basica_primaria),
pero la API externa los clasifica como 'basica_secundaria'.

Mapeo correcto segun agrupacion institucional:
  JR, TR, 1xx, 2xx, 3xx  -> preescolar
  4xx, 5xx, 6xx, 7xx     -> basica_primaria   (Cuarto-Septimo)
  8xx, 9xx               -> basica_secundaria  (Octavo-Undecimo)
  10xx, 11xx             -> media_academica    (Octavo-Undecimo)
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from acompanamiento.models import Student, Course

def grade_from_course_name(name):
    """Extrae el grado del nombre del curso (ej: '703' -> 7, '1002' -> 10)."""
    try:
        n = int(name)
        if n < 200:   return 1
        elif n < 300: return 2
        elif n < 400: return 3
        elif n < 500: return 4
        elif n < 600: return 5
        elif n < 700: return 6
        elif n < 800: return 7
        elif n < 900: return 8
        elif n < 1000: return 9
        elif n < 1100: return 10
        else:          return 11
    except ValueError:
        name_up = name.upper()
        if 'JR' in name_up or 'JAR' in name_up: return 0
        if 'TR' in name_up or 'TRANS' in name_up: return 0
        return None

def section_for_grade(g):
    if g is None: return None
    if g <= 3:  return 'preescolar'
    if g <= 7:  return 'basica_primaria'
    if g <= 9:  return 'basica_secundaria'
    return 'media_academica'

print("=== Diagnostico antes del fix ===")
from django.db.models import Count
for row in Student.objects.values('section').annotate(n=Count('id')).order_by('section'):
    print(f"  section={row['section']!r}  n={row['n']}")

print()
print("Corrigiendo secciones...")

fixed = 0
errors = []

for student in Student.objects.select_related('course').all():
    if not student.course:
        continue
    grade = grade_from_course_name(student.course.name)
    correct_section = section_for_grade(grade)
    if correct_section and student.section != correct_section:
        old = student.section
        student.section = correct_section
        student.save(update_fields=['section'])
        fixed += 1
        if fixed <= 20:
            print(f"  Fixed: {student.full_name} | course={student.course.name!r} | {old!r} -> {correct_section!r}")

print()
print(f"Total estudiantes corregidos: {fixed}")

print()
print("=== Distribucion despues del fix ===")
for row in Student.objects.values('section').annotate(n=Count('id')).order_by('section'):
    print(f"  section={row['section']!r}  n={row['n']}")

print()
# Verificar los estudiantes reportados
codigos = ['31036', '19042', '30465', '31026', '19088', '30868']
print("=== Verificacion de estudiantes reportados ===")
from acompanamiento.models import Report
for code in codigos:
    r = Report.objects.filter(student__code=code).first()
    if r:
        s = r.student
        print(f"  {s.full_name} | course={s.course.name!r} | section={s.section!r} -> OK")
