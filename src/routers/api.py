from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src import crud, schemas, models, database, auth

router = APIRouter(prefix="/api", tags=["api"])

@router.get("/students", response_model=List[schemas.Student])
def read_students(
    skip: int = 0, 
    limit: int = 100, 
    section: models.SectionEnum = None, 
    course: str = None, 
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    # Logic: Teachers/Coordinators should only see their section
    # This logic is partly in CRUD, strictly enforcing here if needed
    return crud.get_students(db, skip=skip, limit=limit, section=section, course=course)

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
