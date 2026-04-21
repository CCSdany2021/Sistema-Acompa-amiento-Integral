from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src import crud, schemas, models, database, auth

router = APIRouter(prefix="/api", tags=["api"])

@router.get("/students", response_model=List[schemas.StudentWithReports])
def read_students(
    skip: int = 0, 
    limit: int = 100, 
    section: models.SectionEnum = None, 
    course: str = None, 
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        # 1. Sync from External API if course or section is provided
        from src.external_api import get_external_students, map_external_section
        
        if course:
            # Fetch from Master DB
            ext_response = get_external_students(course=course)
            # The API returns a dict: {'count': X, 'results': [...]} 
            # based on the user's manual and the error found
            ext_students = ext_response.get('results', []) if isinstance(ext_response, dict) else ext_response
            
            for ext in ext_students:
                # Map external fields to internal structure
                student_data = {
                    "full_name": ext.get("nombre_completo", "Sin Nombre"),
                    "code": ext.get("codigo_estudiante"),
                    "course": ext.get("curso"),
                    "section": map_external_section(ext.get("seccion", ""))
                }
                if student_data["code"]:
                    crud.get_or_create_student_by_code(db, student_data)
    except Exception as e:
        # Print for logs but don't crash if external sync fails
        import traceback
        traceback.print_exc()
        print(f"Sync error: {e}")

    # 2. Now query from our local DB (which is now synced)
    students = crud.get_students(db, skip=skip, limit=limit, section=section, course=course)
    
    result = []
    for s in students:
        s_dict = {
            "id": s.id,
            "full_name": s.full_name,
            "code": s.code,
            "email": s.email,
            "section": s.section,
            "course": s.course,
            "active_reports": [
                {
                    "id": r.id,
                    "purpose": r.purpose,
                    "status": r.status,
                    "created_at": r.created_at
                } for r in s.reports if r.status in [models.ReportStatus.PROGRAMADO, models.ReportStatus.SEGUIMIENTO]
            ]
        }
        result.append(s_dict)
        
    return result

@router.get("/courses", response_model=List[str])
def read_courses(
    section: models.SectionEnum = None,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    return crud.get_courses(db, section=section)

@router.get("/reports", response_model=List[schemas.Report])
def read_reports(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    try:
        role = models.RoleEnum(current_user['role'])
        return crud.get_reports(db, user_role=role, user=current_user, skip=skip, limit=limit)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users", response_model=List[schemas.User])
def read_users(db: Session = Depends(database.get_db)):
    return crud.get_staff_users(db)

@router.post("/reports", response_model=schemas.Report)
def create_report(
    report: schemas.ReportCreate, 
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    # Solo bloqueamos si existe un reporte VIGENTE (No cerrado)
    existing = db.query(models.Report).filter(
        models.Report.student_id == report.student_id,
        models.Report.purpose == report.purpose,
        models.Report.status != models.ReportStatus.ATENDIDO
    ).first()
    
    if existing:
        creator_name = existing.created_by.full_name if existing.created_by else "Desconocido"
        raise HTTPException(
            status_code=409, 
            detail={
                "message": f"El estudiante ya cuenta con un proceso de {report.purpose.value} VIGENTE.",
                "report_id": existing.id,
                "created_by": creator_name,
                "created_at": existing.created_at.isoformat()
            }
        )

    try:
        return crud.create_report(db, report, user_id=current_user['id'])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reports/{report_id}/observations", response_model=schemas.Observation)
def create_observation(
    report_id: int, 
    observation: schemas.ObservationCreate, 
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    return crud.create_observation(db, observation, report_id, current_user['id'])

@router.post("/reports/{report_id}/recommendations", response_model=schemas.Recommendation)
def create_recommendation(
    report_id: int, 
    recommendation: schemas.RecommendationCreate, 
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    return crud.create_recommendation(db, recommendation, report_id, current_user['id'])


@router.post("/reports/{report_id}/close", response_model=schemas.Report)
def close_report_endpoint(
    report_id: int, 
    close_data: schemas.ReportClose, 
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    report = crud.close_report(db, report_id, close_data)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.get("/filters/periods", response_model=List[str])
def get_periods_endpoint(db: Session = Depends(database.get_db)):
    """Return distinct academic periods for filter dropdowns."""
    return crud.get_periods(db)

@router.get("/filters/sections", response_model=List[str])
def get_sections_endpoint(db: Session = Depends(database.get_db)):
    """Return distinct sections for filter dropdowns."""
    return crud.get_sections(db)

@router.get("/filters/courses", response_model=List[str])
def get_courses_endpoint(db: Session = Depends(database.get_db)):
    """Return distinct courses for filter dropdowns."""
    return crud.get_courses(db)

@router.get("/stats/analytics")
def get_analytics(
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user),
    period: str = None,
    section: str = None,
    course: str = None,
    status: str = None,
    educator_id: int = None
):
    """Return analytics data, optionally filtered by period, section, course, status or educator."""
    return crud.get_analytics_data(
        db, 
        period=period, 
        section=section, 
        course=course, 
        status=status, 
        educator_id=educator_id
    )
