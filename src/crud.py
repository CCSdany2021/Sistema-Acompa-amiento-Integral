from sqlalchemy.orm import Session
from src import models, schemas
from src.models import ReportStatus
from datetime import datetime

# --- User ---
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_staff_users(db: Session):
    # Return users who can be assigned (Coordinators, Admins, etc.)
    # Or just all users for now? 
    # Let's filter out students if we had them in same table (we don't).
    # Maybe exclude normal teachers if they don't receive referrals?
    # User asked for "integrantes que acompañan", so we return all imported users.
    return db.query(models.User).all()

# --- Student ---
def get_students(db: Session, skip: int = 0, limit: int = 100, section: models.SectionEnum = None, course: str = None):
    query = db.query(models.Student)
    if section:
        query = query.filter(models.Student.section == section)
    if course:
        query = query.filter(models.Student.course == course)
    return query.offset(skip).limit(limit).all()

def get_courses(db: Session, section: models.SectionEnum = None):
    query = db.query(models.Student.course).distinct()
    if section:
        query = query.filter(models.Student.section == section)
    return [c[0] for c in query.all()]

def create_student(db: Session, student: schemas.StudentBase):
    db_student = models.Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

# --- Report ---
def get_active_report(db: Session, student_id: int, purpose: models.EduPurposeEnum):
    return db.query(models.Report).filter(
        models.Report.student_id == student_id, 
        models.Report.purpose == purpose,
        models.Report.status.in_([ReportStatus.PROGRAMADO, ReportStatus.SEGUIMIENTO])
    ).first()

def get_reports(db: Session, user_role: models.RoleEnum, user: dict, skip: int = 0, limit: int = 50):
    query = db.query(models.Report)
    
    # Permission Logic
    if user_role == models.RoleEnum.DOCENTE:
        # Teachers only see reports they created OR are assigned to
        # Or maybe they see all reports for their Section?
        # User constraint: "Docente pertenece a seccion... solo atiende esta seccion"
        # We need the user object from DB to get assigned_section
        db_user = db.query(models.User).filter(models.User.id == user['id']).first()
        if db_user and db_user.assigned_section:
             query = query.join(models.Student).filter(models.Student.section == db_user.assigned_section)
    
    elif user_role == models.RoleEnum.COORDINADOR:
        db_user = db.query(models.User).filter(models.User.id == user['id']).first()
        if db_user and db_user.assigned_section:
            query = query.join(models.Student).filter(models.Student.section == db_user.assigned_section)
    
    # Admin sees all (no filter)
    
    return query.order_by(models.Report.created_at.desc()).offset(skip).limit(limit).all()

def create_report(db: Session, report: schemas.ReportCreate, user_id: int):
    # Constraint Check
    existing = get_active_report(db, report.student_id, report.purpose)
    if existing:
        raise ValueError(f"Student already has an active report for {report.purpose.value}. Add an observation instead.")
    
    db_report = models.Report(
        student_id=report.student_id,
        purpose=report.purpose,
        objective=report.objective,
        academic_period=report.academic_period,
        created_by_id=user_id,
        assigned_to_id=report.assigned_to_id,  # Can be None
        status=ReportStatus.PROGRAMADO
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

# --- Observation ---
def create_observation(db: Session, observation: schemas.ObservationCreate, report_id: int, user_id: int):
    obs_data = observation.dict()
    # If date_log is provided, uses it. If not, remove it so default func.now() triggers (or set it manually to now)
    # Actually, if it's None in schema, passing None to model might set it to NULL if column allows it, or fail if not nullable default.
    # Model: date_log = Column(..., server_default=func.now())
    # SQLAlchemy: if we pass None, it might try to insert NULL.
    # Better logic:
    if obs_data.get('date_log') is None:
        del obs_data['date_log']
        
    db_obs = models.Observation(
        **obs_data,
        report_id=report_id,
        created_by_id=user_id
    )
    db.add(db_obs)
    
    # Auto-update Report Status to SEGUIMIENTO if it was PROGRAMADO
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if report and report.status == ReportStatus.PROGRAMADO:
        report.status = ReportStatus.SEGUIMIENTO
        db.add(report)
        
    db.commit()
    db.commit()
    db.refresh(db_obs)
    return db_obs

def create_recommendation(db: Session, recommendation: schemas.RecommendationCreate, report_id: int, user_id: int):
    rec_data = recommendation.dict()
    if rec_data.get('date_log') is None:
        del rec_data['date_log']
        
    db_rec = models.Recommendation(
        **rec_data,
        report_id=report_id,
        created_by_id=user_id
    )
    db.add(db_rec)
    db.commit()
    db.refresh(db_rec)
    return db_rec

def get_analytics_data(db: Session):
    from sqlalchemy import func
    
    # 1. Total Reports
    total_reports = db.query(func.count(models.Report.id)).scalar()
    
    # 2. Total Students with Reports
    total_students_distinct = db.query(func.count(func.distinct(models.Report.student_id))).scalar()
    
    # 3. By Status
    # Result: [('PROGRAMADO', 5), ('ATENDIDO', 10)...]
    status_counts = db.query(models.Report.status, func.count(models.Report.id))\
                      .group_by(models.Report.status).all()
                      
    # 4. By Purpose
    purpose_counts = db.query(models.Report.purpose, func.count(models.Report.id))\
                       .group_by(models.Report.purpose).all()
                       
    # 5. By Course
    # Join Report -> Student to get Course
    course_counts = db.query(models.Student.course, func.count(models.Report.id))\
                      .join(models.Report, models.Report.student_id == models.Student.id)\
                      .group_by(models.Student.course).all()
                      
    # 6. Detailed List (Student Name, Course, Active Reports Count, Total Reports Count)
    # This might be heavy if many students. Limit to top 50 or so? 
    # Or just return all for now (assuming school size < 2000 students and not all have reports)
    # Let's get top 100 students by report count
    
    student_stats = db.query(
        models.Student.full_name,
        models.Student.course,
        func.count(models.Report.id).label('total_reports')
    ).join(models.Report, models.Report.student_id == models.Student.id)\
     .group_by(models.Student.id)\
     .order_by(func.count(models.Report.id).desc())\
     .limit(100).all()
     
    return {
        "total_reports": total_reports,
        "total_students": total_students_distinct,
        "by_status": {s.value: c for s, c in status_counts},
        "by_purpose": {p.value: c for p, c in purpose_counts},
        "by_course": {c: count for c, count in course_counts},
        "student_ranking": [
            {"name": name, "course": course, "count": count} 
            for name, course, count in student_stats
        ]
    }
