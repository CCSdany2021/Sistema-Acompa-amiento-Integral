from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from src import models, database, auth
from src.templates_config import templates
from pydantic import BaseModel

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_current_user)] # Protect all admin routes
)

# --- Pydantic Schemas for Request Body ---
class SectionCreate(BaseModel):
    name: str

class CourseCreate(BaseModel):
    name: str
    section_id: int

# --- Admin Setup View (Frontend) ---
@router.get("/setup")
def admin_setup_view(request: Request, db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    if current_user['role'] not in [models.RoleEnum.ADMIN_GLOBAL, models.RoleEnum.COORDINADOR]:
         raise HTTPException(status_code=403, detail="Not authorized")
    
    sections = db.query(models.Section).all()
    # Fetch navigation data (all sections for the sidebar)
    nav_sections = db.query(models.Section).all()
    
    return templates.TemplateResponse("admin_setup.html", {
        "request": request,
        "user": current_user, 
        "sections": sections,
        "nav_sections": nav_sections # For the sidebar
    })

# --- CRUD Endpoints (API) ---

@router.post("/sections")
def create_section(section: SectionCreate, db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    if current_user['role'] not in [models.RoleEnum.ADMIN_GLOBAL]:
        raise HTTPException(status_code=403, detail="Only Global Admins can create sections")
    
    existing = db.query(models.Section).filter(models.Section.name == section.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Section already exists")
    
    new_section = models.Section(name=section.name)
    db.add(new_section)
    db.commit()
    db.refresh(new_section)
    return new_section

@router.delete("/sections/{section_id}")
@router.delete("/sections/{section_id}")
def delete_section(section_id: int, db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    if current_user['role'] not in [models.RoleEnum.ADMIN_GLOBAL]:
        raise HTTPException(status_code=403, detail="Only Global Admins can delete sections")
        
    section = db.query(models.Section).filter(models.Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    db.delete(section)
    db.commit()
    return {"message": "Section deleted"}

@router.post("/courses")
@router.post("/courses")
def create_course(course: CourseCreate, db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    if current_user['role'] not in [models.RoleEnum.ADMIN_GLOBAL, models.RoleEnum.COORDINADOR]:
         raise HTTPException(status_code=403, detail="Not authorized")

    new_course = models.Course(name=course.name, section_id=course.section_id)
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course

@router.delete("/courses/{course_id}")
@router.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    if current_user['role'] not in [models.RoleEnum.ADMIN_GLOBAL, models.RoleEnum.COORDINADOR]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db.delete(course)
    db.commit()
    return {"message": "Course deleted"}
