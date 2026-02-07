import sys
import os
sys.path.append(os.getcwd())
from src import database, models, crud
from sqlalchemy.orm import Session

def sync_structure():
    db = next(database.get_db())
    
    # 1. Get all distinct courses/sections from Students
    students = db.query(models.Student).all()
    
    # Map section enum to string for easier check
    section_map = {}
    
    # Ensure Sections exist
    for section_enum in models.SectionEnum:
        print(f"Checking Section: {section_enum.value}")
        sec = db.query(models.Section).filter(models.Section.name == section_enum.value).first()
        if not sec:
            print(f"Creating Section: {section_enum.value}")
            sec = models.Section(name=section_enum.value)
            db.add(sec)
            db.commit()
            db.refresh(sec)
        section_map[section_enum] = sec.id
        
    # Ensure Courses exist
    # Group students by course
    course_list = {} # name -> section_enum
    for s in students:
        if s.course:
            course_list[s.course] = s.section
            
    print(f"Found {len(course_list)} distinct courses in Students table.")
    
    for course_name, section_enum in course_list.items():
        # Check if course exists
        course = db.query(models.Course).filter(models.Course.name == course_name).first()
        if not course:
            print(f"Creating Course: {course_name}")
            sec_id = section_map.get(section_enum)
            course = models.Course(name=course_name, section_id=sec_id)
            db.add(course)
        else:
            # Update section if needed
            sec_id = section_map.get(section_enum)
            if course.section_id != sec_id:
                 print(f"Updating Course Section: {course_name}")
                 course.section_id = sec_id
                 
    db.commit()
    print("Sync Complete.")

if __name__ == "__main__":
    sync_structure()
