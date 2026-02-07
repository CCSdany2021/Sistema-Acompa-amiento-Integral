from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src import database, models, auth, crud
import pandas as pd
import io

router = APIRouter(prefix="/api/import", tags=["import"])

@router.post("/students")
async def import_students(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Import students from Excel/CSV.
    Expected columns: SECCIÓN | NOMBRE ESTUDIANTE | CODIGO | GRADO | CURSO
    """
    if current_user['role'] not in [models.RoleEnum.COORDINADOR, models.RoleEnum.ADMIN_GLOBAL]:
        raise HTTPException(status_code=403, detail="Not authorized")

    contents = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid file format: {str(e)}")

    # Normalize columns
    df.columns = [c.strip().upper() for c in df.columns]
    
    required_cols = ['SECCIÓN', 'NOMBRE ESTUDIANTE', 'CODIGO', 'CURSO']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    success_count = 0
    errors = []

    for index, row in df.iterrows():
        try:
            code = str(row['CODIGO']).strip()
            name = str(row['NOMBRE ESTUDIANTE']).strip()
            course = str(row['CURSO']).strip()
            section_raw = str(row['SECCIÓN']).strip().upper()
            
            # Map Section
            section_enum = None
            if "PRIMARIA" in section_raw or "JARDIN" in section_raw:
                section_enum = models.SectionEnum.PREESCOLAR_PRIMARIA
            elif "MEDIA" in section_raw or "BÁSICA" in section_raw or "BASICA" in section_raw:
                section_enum = models.SectionEnum.MEDIA_BASKICA
            elif "BACHILLERATO" in section_raw:
                section_enum = models.SectionEnum.BACHILLERATO
            else:
                 # Fallback or skip? Let's try to infer from course if possible, 
                 # or defaults to BACHILLERATO as per previous dummy data logic, 
                 # but safer to log error.
                 # Let's try to match partials
                 pass

            # Update or Create
            student = db.query(models.Student).filter(models.Student.code == code).first()
            if not student:
                student = models.Student(
                    code=code,
                    full_name=name,
                    course=course,
                    section=section_enum or models.SectionEnum.BACHILLERATO # Fallback
                )
                db.add(student)
            else:
                student.full_name = name
                student.course = course
                if section_enum:
                    student.section = section_enum
            
            success_count += 1
            
        except Exception as e:
            errors.append(f"Row {index}: {str(e)}")

    db.commit()
    
    return {
        "message": f"Processed {len(df)} rows.",
        "success": success_count,
        "errors": errors[:10] # Top 10 errors
    }
