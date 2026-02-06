import sys
import os
import pandas as pd
from sqlalchemy.orm import Session
from io import StringIO

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import models, database
from src.database import SessionLocal

CSV_DATA = """
"ID","Rol","Email","Nombre","FinEducativo","Puesto","Seccion"
"1","Admin espiritual","cap@calasanzsuba.edu.co","Cap","Espiritual","Cap","Sección Jardín Tercero"
"3","Admin global","mrodriguez@calasanzsuba.edu.co","Mireya Rodriguez Olarte",,"Mireya Rodríguez Olarte","Sección Cuarto Séptimo"
"8","Admin global","mmonroy@calasanzsuba.edu.co","María Angelica  Monroy",,"María Angelica  Monroy","Docente de Pastoral"
"41","Admin global","ngarzon@calasanzsuba.edu.co","Natalia Garzón",,"Natalia Garzón","Sección Octavo Undécimo"
"42","Admin global","ccastro@calasanzsuba.edu.co","Claudia Patricia Castro",,"Claudia Patricia Castro","Coordinadora Academica"
"43","Admin global","dhiguera@calasanzsuba.edu.co","Diana Higuera Guerrero",,"Diana Higuera Guerrero","Rectora"
"44","Admin de sección","mpedraza@calasanzsuba.edu.co","María Fernanda Pedraza",,"María Fernanda Pedraza","Sección Jardín Tercero"
"45","Admin de sección","itang@calasanzsuba.edu.co","Paola Tang","Psicoafectivo","Paola Tang","Sección Preescolar"
"46","Admin restringido","ncabrera@calasanzsuba.edu.co","Nancy Cabrera ",,"Nancy Cabrera ","Sección de Primaria 3-5"
"47","Admin restringido","Rarango@calasanzsuba.edu.co","Alejandro Arango",,"Alejandro Arango",
"48","Admin de sección","jgomez@calasanzsuba.edu.co","John Jairo Gómez",,"John Jairo Gómez","Sección de Primaria 3-5"
"49","Admin espiritual","mgordillo@calasanzsuba.edu.co","Mateo Gordillo","Espiritual","Mateo Gordillo",
"50","Admin espiritual","pmonsalve@calasanzsuba.edu.co","Paulo Monsalve","Espiritual","Paulo Monsalve",
"53","Admin restringido","royola@calasanzsuba.edu.co","Rodrigo Oyola",,"Rodrigo Oyola",
"55","Admin de sección","aardila@calasanzsuba.edu.co","Alejandra Ardila ","Psicoafectivo","Alejandra Ardila ","Sección de Bachillerato 6-8"
"56","Admin global","pvasquez@calasanzsuba.edu.co","Paola Andrea Vasquez Caballero",,"Coordinadora de calidad",
"57","Admin de sección ","yalejo@calasanzsuba.edu.co","Yury Alejo",,"Yury Alejo","Sección Octavo Undécimo"
"""

def import_users():
    print("Importing Users...")
    db = SessionLocal()
    
    try:
        # Read CSV logic
        df = pd.read_csv(StringIO(CSV_DATA.strip()))
        
        count = 0
        updated = 0
        
        for index, row in df.iterrows():
            email = row['Email'].strip()
            full_name = row['Nombre'].strip().title()
            rol_csv = row['Rol'].strip().lower()
            seccion_csv = str(row['Seccion']).strip()
            fin_csv = str(row['FinEducativo']).strip()
            
            # Map Roles
            role = models.RoleEnum.DOCENTE
            if "global" in rol_csv:
                role = models.RoleEnum.ADMIN_GLOBAL
            elif "sección" in rol_csv or "seccion" in rol_csv:
                role = models.RoleEnum.COORDINADOR
            
            # Map Section
            section = None
            if "jardín" in seccion_csv.lower() or "preescolar" in seccion_csv.lower():
                section = models.SectionEnum.PREESCOLAR_PRIMARIA
            elif "cuarto" in seccion_csv.lower() or "primaria" in seccion_csv.lower(): 
                 # "Sección de Primaria 3-5" maps to PREESCOLAR_PRIMARIA (grades 0-3) or MEDIA_BASICA (4-7)
                 # Re-evaluating: 3 is low, 5 is high. Let's start with PREESCOLAR_PRIMARIA as default for 'primaria' unless specified high.
                 # Actually, given current Enums, MEDIA_BASKICA covers 4-7. 
                 # Let's map "Sección Cuarto Séptimo" -> MEDIA_BASKICA
                 section = models.SectionEnum.MEDIA_BASKICA
            elif "octavo" in seccion_csv.lower() or "bachillerato" in seccion_csv.lower():
                section = models.SectionEnum.BACHILLERATO
            
            # Force exact matches from CSV
            if "jardín tercero" in seccion_csv.lower():
                section = models.SectionEnum.PREESCOLAR_PRIMARIA
            if "cuarto séptimo" in seccion_csv.lower():
                section = models.SectionEnum.MEDIA_BASKICA
                
            # Map Purpose
            purpose = None
            if fin_csv and fin_csv != "nan":
                if "espiritual" in fin_csv.lower():
                    purpose = models.EduPurposeEnum.ESPIRITUAL
                elif "psicoafectivo" in fin_csv.lower():
                    purpose = models.EduPurposeEnum.PSICOAFECTIVO
                elif "convivencia" in fin_csv.lower():
                    purpose = models.EduPurposeEnum.CONVIVENCIA
                elif "academico" in fin_csv.lower():
                    purpose = models.EduPurposeEnum.ACADEMICO

            # Check existence
            user = db.query(models.User).filter(models.User.email == email).first()
            
            if user:
                user.full_name = full_name
                user.role = role
                user.assigned_section = section
                user.assigned_purpose = purpose
                updated += 1
            else:
                user = models.User(
                    email=email,
                    full_name=full_name,
                    role=role,
                    assigned_section=section,
                    assigned_purpose=purpose
                )
                db.add(user)
                count += 1
        
        db.commit()
        print(f"Success! Created {count} users. Updated {updated} users.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_users()
