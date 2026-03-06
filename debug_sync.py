import requests

def debug_api():
    # Attempting to hit the local server with a test course as a logged in user would (mimicking with no auth if possible or looking at logs)
    # Since I don't have a session, I'll use a script that calls the function directly in the app context
    pass

if __name__ == "__main__":
    from src.database import SessionLocal
    from src.routers.api import read_students
    from src import models
    
    db = SessionLocal()
    # Mock current_user
    user = {"id": 1, "role": "Admin Global", "email": "admin@calasanz.edu.co"}
    
    print("Iniciando depuración de sincronización para JR01...")
    try:
        results = read_students(course="JR01", db=db, current_user=user)
        print(f"Estudiantes encontrados: {len(results)}")
        if len(results) > 0:
            for s in results[:3]:
                print(f"- {s['full_name']} (Curso: {s['course']}, Sección: {s['section']})")
        else:
            print("LA LISTA VOLVIÓ VACÍA.")
            # Check if they were at least created in DB
            count = db.query(models.Student).filter(models.Student.course == "JR01").count()
            print(f"Número de estudiantes en DB local para JR01: {count}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
    finally:
        db.close()
