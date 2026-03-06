import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import models, database
from src.database import SessionLocal

def init_nav():
    db = SessionLocal()
    
    # Define standard structure for Calasanz Suba
    data = {
        "Jardín a Tercero": ["TR01", "TR02", "JR01", "101", "102", "201", "202", "301", "302"],
        "Cuarto a Séptimo": ["401", "402", "501", "502", "601", "602", "701", "702"],
        "Octavo a Undécimo": ["801", "802", "901", "902", "1001", "1002", "1101", "1102", "1103"]
    }
    
    try:
        for sec_name, courses in data.items():
            # Get or create section
            sec = db.query(models.Section).filter(models.Section.name == sec_name).first()
            if not sec:
                sec = models.Section(name=sec_name)
                db.add(sec)
                db.flush()
                print(f"Creada sección: {sec_name}")
            
            for c_name in courses:
                # Get or create course
                course = db.query(models.Course).filter(
                    models.Course.name == c_name, 
                    models.Course.section_id == sec.id
                ).first()
                if not course:
                    course = models.Course(name=c_name, section_id=sec.id)
                    db.add(course)
                    print(f"  - Creado curso: {c_name}")
        
        db.commit()
        print("\n¡Navegación inicializada correctamente!")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_nav()
