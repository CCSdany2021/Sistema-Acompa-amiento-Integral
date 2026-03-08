from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="src/templates")

def get_grade_name(course):
    if not course: return '---'
    c = str(course).upper()
    if c.startswith('TR'): return 'Transición'
    if len(c) == 3:
        grade = c[0]
        grades = { '1': 'Primero', '2': 'Segundo', '3': 'Tercero', '4': 'Cuarto', '5': 'Quinto', '6': 'Sexto', '7': 'Séptimo', '8': 'Octavo', '9': 'Noveno' }
        return grades.get(grade, course)
    if len(c) == 4:
        grade = c[:2]
        if grade == '10': return 'Décimo'
        if grade == '11': return 'Undécimo'
    return course

templates.env.filters['grade_name'] = get_grade_name
