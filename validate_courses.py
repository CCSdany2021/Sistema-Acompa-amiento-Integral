import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.external_api import get_external_students
from src.database import SessionLocal
from src import models

def main():
    print("Fetching all students from external API to find unique courses...")
    response = get_external_students()
    
    if isinstance(response, dict):
        if "results" in response:
            students = response["results"]
        elif "data" in response:
            students = response["data"]
        else:
            students = []
    elif isinstance(response, list):
        students = response
    else:
        students = []

    courses_found = {}
    for student in students:
        course = student.get("curso")
        grade = student.get("grado")
        section = student.get("seccion")
        if course:
            if course not in courses_found:
                courses_found[course] = {"grade": grade, "section": section, "count": 1}
            else:
                courses_found[course]["count"] += 1

    print("\nUnique courses from API:")
    for course, info in sorted(courses_found.items()):
        print(f"Course: {course} | Grado: {info['grade']} | Sección: {info['section']} | Students: {info['count']}")

    print("\nLocal Courses in DB:")
    db = SessionLocal()
    local_courses = db.query(models.Course).all()
    
    local_course_names = set(c.name for c in local_courses)
    api_course_names = set(courses_found.keys())

    missing_in_db = api_course_names - local_course_names
    missing_in_api = local_course_names - api_course_names

    print(f"\nCourses in API but NOT in DB: {sorted(list(missing_in_db))}")
    print(f"Courses in DB but NOT in API: {sorted(list(missing_in_api))}")

    db.close()

if __name__ == "__main__":
    main()
