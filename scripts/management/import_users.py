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
"ID","Activo","SeccionNuevo","RolNuevo","Email","FinesEducativos","Puesto"
"1","Verdadero","Sección Jardín Tercero","Admin global","cap@calasanzsuba.edu.co","[""Psicoafectivo"",""Académico"",""Espiritual"",""Convivencia""]","Cap"
"3","Verdadero",,"Admin global","mrodriguez@calasanzsuba.edu.co",,"Mireya Rodríguez Olarte"
"8","Verdadero","Sección Octavo Undécimo","Admin de sección","mmonroy@calasanzsuba.edu.co","[""Espiritual"",""Académico""]","María Angelica  Monroy"
"41","Verdadero","Sección Octavo Undécimo","Admin de sección","ngarzon@calasanzsuba.edu.co","[""Académico"",""Convivencia"",""Psicoafectivo""]","Natalia Garzón"
"42","Verdadero",,"Admin global","ccastro@calasanzsuba.edu.co","[""Académico"",""Convivencia"",""Psicoafectivo"",""Espiritual""]","Claudia Patricia Castro"
"43","Verdadero",,"Admin global","dhiguera@calasanzsuba.edu.co","[""Académico"",""Convivencia"",""Psicoafectivo"",""Espiritual""]","Diana Higuera Guerrero"
"44","Verdadero","Sección Jardín Tercero","Admin de sección","mpedraza@calasanzsuba.edu.co","[""Psicoafectivo"",""Académico"",""Espiritual"",""Convivencia""]","María Fernanda Pedraza"
"45","Verdadero","Sección Jardín Tercero","Admin de sección","itang@calasanzsuba.edu.co","[""Psicoafectivo"",""Académico"",""Espiritual"",""Convivencia""]","Paola Tang"
"46","Verdadero","Sección Jardín Tercero","Admin de sección","ncabrera@calasanzsuba.edu.co",,"Nancy Cabrera"
"47","Verdadero",,"Admin restringido","Rarango@calasanzsuba.edu.co",,"Alejandro Arango"
"48","Verdadero","Sección Jardín Tercero","Admin de sección","jgomez@calasanzsuba.edu.co",,"John Jairo Gómez"
"49","Verdadero",,"Admin espiritual","mgordillo@calasanzsuba.edu.co",,"Mateo Gordillo"
"50","Verdadero",,"Admin espiritual","pmonsalve@calasanzsuba.edu.co",,"Paulo Monsalve"
"53","Verdadero",,"Admin restringido","royola@calasanzsuba.edu.co",,"Rodrigo Oyola"
"55","Verdadero","Sección Octavo Undécimo","Admin de sección","aardila@calasanzsuba.edu.co","[""Psicoafectivo""]","Alejandra Ardila"
"56","Verdadero",,"Admin global","pvasquez@calasanzsuba.edu.co",,"Paola Andrea Vasquez Caballero"
"57","Verdadero","Sección Octavo Undécimo","Admin de sección","yalejo@calasanzsuba.edu.co",,"Yury Alejo"
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
            email = str(row['Email']).strip()
            full_name = str(row['Puesto']).strip().title()
            rol_csv = str(row['RolNuevo']).strip().lower()
            seccion_csv = str(row['SeccionNuevo']).strip().lower()
            fin_csv = str(row['FinesEducativos']).strip()
            
            # Map Roles
            role = models.RoleEnum.DOCENTE
            if "global" in rol_csv:
                role = models.RoleEnum.ADMIN_GLOBAL
            elif "sección" in rol_csv or "seccion" in rol_csv:
                role = models.RoleEnum.COORDINADOR
            
            # Map Section
            section = None
            if "jardín" in seccion_csv or "jardin" in seccion_csv or "preescolar" in seccion_csv:
                section = models.SectionEnum.PREESCOLAR_PRIMARIA
            elif "cuarto" in seccion_csv or "séptimo" in seccion_csv or "septimo" in seccion_csv:
                section = models.SectionEnum.MEDIA_BASKICA
            elif "octavo" in seccion_csv or "undécimo" in seccion_csv or "undecimo" in seccion_csv or "bachillerato" in seccion_csv:
                section = models.SectionEnum.BACHILLERATO
            
            # Map Purpose (If multiple, we take the first one or logic based on role)
            purpose = None
            if fin_csv and fin_csv != "nan":
                # Clean clean brackets and quotes if it's a list string
                fin_csv = fin_csv.replace("[", "").replace("]", "").replace('"', '').replace("'", "")
                fines = [f.strip() for f in fin_csv.split(',')]
                
                if fines:
                    first_fine = fines[0].lower()
                    if "espiritual" in first_fine:
                        purpose = models.EduPurposeEnum.ESPIRITUAL
                    elif "psicoafectivo" in first_fine:
                        purpose = models.EduPurposeEnum.PSICOAFECTIVO
                    elif "convivencia" in first_fine:
                        purpose = models.EduPurposeEnum.CONVIVENCIA
                    elif "académico" in first_fine or "academico" in first_fine:
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
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_users()
