import sys
import os
import pandas as pd
from sqlalchemy.orm import Session

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import models, database
from src.database import SessionLocal, engine

def import_students(file_path):
    print(f"Reading file: {file_path}")
    
    # Init DB Session
    db = SessionLocal()
    
    try:
        df = pd.read_excel(file_path)
        
        # Verify Columns
        required_cols = ['NOMBRE ESTUDIANTE', 'CODIGO', 'CURSO', 'CORREO']
        for col in required_cols:
            if col not in df.columns:
                print(f"Error: Column '{col}' not found in Excel. Found: {list(df.columns)}")
                return

        print(f"Found {len(df)} records. Processing...")
        
        count = 0
        updated = 0
        
        for index, row in df.iterrows():
            # Apply Title Case to Name
            raw_name = str(row['NOMBRE ESTUDIANTE'])
            full_name = raw_name.title() 
            
            code = str(row['CODIGO'])
            course = str(row['CURSO']) # Ensure string
            email = row['CORREO']
            
            # Map Section
            # Logic: Input file is explicitly "Grados Jardín - Tercero"
            section = models.SectionEnum.PREESCOLAR_PRIMARIA
            
            # Check if exists
            student = db.query(models.Student).filter(models.Student.code == code).first()
            
            if student:
                # Update info if needed
                student.full_name = full_name
                student.course = course
                student.email = email
                student.section = section
                updated += 1
            else:
                # Create new
                student = models.Student(
                    full_name=full_name,
                    code=code,
                    course=course,
                    email=email,
                    section=section
                )
                db.add(student)
                count += 1
                
        db.commit()
        print(f"Success! Created {count} new students. Updated {updated} existing students.")
        
    except Exception as e:
        print(f"Error importing data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    file_path = "archivos/Grados Jardín - Tercero.xlsx"
    if os.path.exists(file_path):
        import_students(file_path)
    else:
        print(f"File not found: {file_path}")
