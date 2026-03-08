from fastapi import APIRouter, Depends, Request
from src.templates_config import templates
from sqlalchemy.orm import Session, joinedload
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
    # Fetch Data for Dashboard eager loading relationships used in UI
    db_user = crud.get_user_by_email(db, current_user['email'])
    nav_sections = db.query(models.Section).options(joinedload(models.Section.courses)).all()
    
    # Dashboard Statistics
    total_students = db.query(models.Student).count()
    active_reports = db.query(models.Report).filter(
        models.Report.status.in_([models.ReportStatus.PROGRAMADO, models.ReportStatus.SEGUIMIENTO])
    ).count()
    
    # Fetch recent reports with student eager loaded
    recent_reports = db.query(models.Report).options(
        joinedload(models.Report.student)
    ).order_by(models.Report.created_at.desc()).limit(5).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "user": current_user,
        "section": db_user.assigned_section if db_user else None,
        "nav_sections": nav_sections,
        "total_students": total_students,
        "active_reports": active_reports,
        "recent_reports": recent_reports
    })

@router.get("/reports")
def reports_list(
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    nav_sections = db.query(models.Section).options(joinedload(models.Section.courses)).all()
    return templates.TemplateResponse("reports_list.html", {
        "request": request,
        "user": current_user,
        "nav_sections": nav_sections
    })

@router.get("/reports/analytics")
def reports_analytics(
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    nav_sections = db.query(models.Section).options(joinedload(models.Section.courses)).all()
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
    # Eager load all relationships used in report_detail.html to avoid DetachedInstanceError
    report = db.query(models.Report).options(
        joinedload(models.Report.student).joinedload(models.Student.reports),
        joinedload(models.Report.observations).joinedload(models.Observation.created_by),
        joinedload(models.Report.recommendations).joinedload(models.Recommendation.created_by),
        joinedload(models.Report.created_by),
        joinedload(models.Report.assigned_to)
    ).filter(models.Report.id == report_id).first()

    nav_sections = db.query(models.Section).options(joinedload(models.Section.courses)).all()
    
    if not report:
        return templates.TemplateResponse("dashboard.html", {
            "request": request, 
            "user": current_user, 
            "error": "Reporte no encontrado",
            "nav_sections": nav_sections
        })
        
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
    nav_sections = db.query(models.Section).options(joinedload(models.Section.courses)).all()
    
    if not course:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": current_user,
            "error": "Curso no encontrado",
            "nav_sections": nav_sections
        })
        
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "user": current_user,
        "selected_course_name": course.name,
        "nav_sections": nav_sections
    })


