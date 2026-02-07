from fastapi import APIRouter, Depends, Request
from src.templates_config import templates
from sqlalchemy.orm import Session
from src import database, auth, crud, models

router = APIRouter(include_in_schema=False)

@router.get("/")
def index(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/dashboard")
def dashboard(
    request: Request, 
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    # Fetch Data for Dashboard
    # For now, just render the template
    # We might want to pass initial lists like 'Courses' based on Section
    
    # Get user details from DB to know Section
    db_user = crud.get_user_by_email(db, current_user['email'])
    
    # Simple logic: If user is teacher, pass their section courses?
    # For now just render.
    # Get nav sections for sidebar
    nav_sections = db.query(models.Section).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "user": current_user,
        "section": db_user.assigned_section if db_user else None,
        "nav_sections": nav_sections
    })

@router.get("/reports")
def reports_analytics(
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    nav_sections = db.query(models.Section).all()
    return templates.TemplateResponse("reports_analytics.html", {
        "request": request,
        "user": current_user,
        "nav_sections": nav_sections
    })

@router.get("/reports/{report_id}")
def report_detail(
    report_id: int,
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        # Handle 404 nicely? For now, dashboard.
        nav_sections = db.query(models.Section).all()
        return templates.TemplateResponse("dashboard.html", {
            "request": request, 
            "user": current_user, 
            "error": "Reporte no encontrado",
            "nav_sections": nav_sections
        })
        
    nav_sections = db.query(models.Section).all()
    
    return templates.TemplateResponse("report_detail.html", {
        "request": request,
        "user": current_user,
        "report": report,
        "nav_sections": nav_sections
    })

@router.get("/courses/{course_id}")
def course_detail(
    course_id: int,
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        # Fallback if not found
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": current_user,
            "error": "Curso no encontrado",
            "nav_sections": db.query(models.Section).all()
        })
        
    nav_sections = db.query(models.Section).all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "user": current_user,
        "selected_course_name": course.name, # Pass name for JS
        "nav_sections": nav_sections
    })
