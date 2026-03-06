import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import database, crud, models
from src.external_api import get_external_students, map_external_section
import requests

def sync_all_students():
    print("Iniciando sincronización completa de estudiantes...")
    db = database.SessionLocal()
    
    try:
        from src.config import settings
        url = settings.API_ESTUDIANTES_URL
        headers = {
            "X-API-Key": settings.API_ESTUDIANTES_KEY
        }
        params = {"estado": "activo"}
        
        total_synced = 0
        
        while url:
            print(f"Obteniendo datos de: {url}")
            response = requests.get(url, headers=headers, params=params if '?' not in url else None, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # API can return a paginated dictionary or a direct list
            if isinstance(data, dict):
                results = data.get("results", [])
                url = data.get("next") # URL to next page
            else:
                results = data
                url = None
                
            for ext in results:
                student_data = {
                    "full_name": ext.get("nombre_completo", "Sin Nombre"),
                    "code": ext.get("codigo_estudiante"),
                    "course": ext.get("curso"),
                    "section": map_external_section(ext.get("seccion", ""))
                }
                if student_data["code"]:
                    crud.get_or_create_student_by_code(db, student_data)
                    total_synced += 1
            
            # Commit processing of current page
            db.commit()
            
            # Optional: Remove params on next iterations if next URL comes fully formulated
            params = {} 

        print(f"\n¡Sincronización finalizada con éxito! Total estudiantes en la DB local: {total_synced}")
        
    except Exception as e:
        print(f"\nError durante la sincronización: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sync_all_students()
