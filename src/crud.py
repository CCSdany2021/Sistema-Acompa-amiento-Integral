from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from src import models, schemas
from src.models import ReportStatus
from datetime import datetime

# --- User ---
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_staff_users(db: Session):
    # Return users who can be assigned (Coordinators, Admins, etc.)
    return db.query(models.User).all()

# --- Student ---
def get_students(db: Session, skip: int = 0, limit: int = 100, section: models.SectionEnum = None, course: str = None):
    query = db.query(models.Student)
    if section:
        query = query.filter(models.Student.section == section)
    if course:
        query = query.filter(models.Student.course == course)
    return query.offset(skip).limit(limit).all()


def get_periods(db: Session):
    """Return list of distinct academic periods from reports."""
    periods = db.query(models.Report.academic_period).distinct().all()
    return [p[0] for p in periods if p[0] is not None]

def get_sections(db: Session):
    """Return list of distinct sections from students."""
    sections = db.query(models.Student.section).distinct().all()
    return [s[0] for s in sections if s[0] is not None]

def get_courses(db: Session, section: models.SectionEnum = None):
    query = db.query(models.Student.course).distinct()
    if section:
        query = query.filter(models.Student.section == section)
    return [c[0] for c in query.all() if c[0] is not None]

def create_student(db: Session, student: schemas.StudentBase):
    db_student = models.Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def get_or_create_student_by_code(db: Session, student_data: dict):
    """
    Checks if a student exists by code. If not, creates it.
    Updates name/course/section if they changed.
    """
    db_student = db.query(models.Student).filter(models.Student.code == str(student_data['code'])).first()
    
    if not db_student:
        db_student = models.Student(
            full_name=student_data['full_name'],
            code=str(student_data['code']),
            course=student_data.get('course'),
            section=student_data.get('section')
        )
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
    else:
        # Update existing info to stay in sync with master
        changed = False
        if db_student.full_name != student_data['full_name']:
            db_student.full_name = student_data['full_name']
            changed = True
        if db_student.course != student_data.get('course'):
            db_student.course = student_data.get('course')
            changed = True
        if db_student.section != student_data.get('section'):
            db_student.section = student_data.get('section')
            changed = True
        
        if changed:
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
    
    # Add eager loading for serialization
    query = query.options(
        joinedload(models.Report.student),
        joinedload(models.Report.assigned_to),
        joinedload(models.Report.created_by),
        joinedload(models.Report.observations).joinedload(models.Observation.created_by),
        joinedload(models.Report.recommendations).joinedload(models.Recommendation.created_by)
    )
    
    return query.order_by(models.Report.created_at.desc()).offset(skip).limit(limit).all()

def create_report(db: Session, report: schemas.ReportCreate, user_id: int):
    # Strict Constraint Check: Only 1 report per purpose per student (Ever)
    existing = db.query(models.Report).filter(
        models.Report.student_id == report.student_id, 
        models.Report.purpose == report.purpose
    ).first()
    
    if existing:
        raise ValueError(f"El estudiante ya cuenta con un reporte de tipo {report.purpose.value}. No se pueden duplicar reportes del mismo fin educativo.")
    
    db_report = models.Report(
        student_id=report.student_id,
        purpose=report.purpose,
        objective=report.objective,
        academic_period=report.academic_period,
        created_by_id=user_id,
        assigned_to_id=report.assigned_to_id, 
        status=models.ReportStatus.PROGRAMADO
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

def close_report(db: Session, report_id: int, close_data: schemas.ReportClose):
    db_report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not db_report:
        return None
    
    db_report.status = models.ReportStatus.ATENDIDO
    db_report.closed_at = func.now()
    db_report.is_accomplished = close_data.is_accomplished
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_analytics_data(db: Session, period: str = None, section: str = None, course: str = None, status: str = None, educator_id: int = None):
    # Base query for reports
    query = db.query(models.Report).join(models.Student)
    
    # Apply Filters
    if period:
        query = query.filter(models.Report.academic_period == period)
    if section:
        query = query.filter(models.Student.section == section)
    if course:
        query = query.filter(models.Student.course == course)
    if status:
        query = query.filter(models.Report.status == status)
    if educator_id:
        query = query.filter(models.Report.assigned_to_id == educator_id)

    # 1. KPIs
    total_reports = query.count()
    total_students = query.with_entities(func.count(func.distinct(models.Report.student_id))).scalar() or 0
    
    # 2. Status Distribution
    status_counts = query.with_entities(models.Report.status, func.count(models.Report.id))\
                       .group_by(models.Report.status).all()
                       
    # 3. Purpose Distribution
    purpose_counts = query.with_entities(models.Report.purpose, func.count(models.Report.id))\
                        .group_by(models.Report.purpose).all()
                       
    # 4. Course Distribution (Top 10)
    course_counts = query.with_entities(models.Student.course, func.count(models.Report.id))\
                       .group_by(models.Student.course)\
                       .order_by(func.count(models.Report.id).desc()).limit(10).all()
                       
    # 5. Student vs Educator Ranking (Matrix Data)
    # We'll get the distribution of assignments for the top 15 students
    top_students_ids = query.with_entities(models.Report.student_id)\
                            .group_by(models.Report.student_id)\
                            .order_by(func.count(models.Report.id).desc()).limit(15).all()
    top_ids = [s[0] for s in top_students_ids]
    
    matrix_data = []
    if top_ids:
        matrix_query = db.query(
            models.Student.full_name,
            models.User.full_name.label('educator'),
            func.count(models.Report.id)
        ).join(models.Report, models.Report.student_id == models.Student.id)\
         .outerjoin(models.User, models.Report.assigned_to_id == models.User.id)\
         .filter(models.Student.id.in_(top_ids))\
         .group_by(models.Student.id, models.User.id).with_entities(models.Student.id, models.Student.full_name, models.Student.code, models.User.id, models.User.full_name, func.count(models.Report.id)).all()
         
        for s_id, s_name, s_code, e_id, e_name, count in matrix_query:
            # For each pair, get status and purpose breakdown
            details = db.query(models.Report.status, models.Report.purpose)\
                        .filter(models.Report.student_id == s_id, models.Report.assigned_to_id == e_id).all()
            
            statuses = {}
            purposes = []
            for d_status, d_purpose in details:
                statuses[d_status] = statuses.get(d_status, 0) + 1
                if d_purpose and d_purpose not in purposes:
                    purposes.append(d_purpose)

            matrix_data.append({
                "student": s_name,
                "student_code": s_code,
                "educator": e_name or "Sin Asignar",
                "count": count,
                "statuses": statuses,
                "purposes": purposes
            })

    return {
        "total_reports": total_reports,
        "total_students": total_students,
        "by_status": {s.value: c for s, c in status_counts},
        "by_purpose": {p.value: c for p, c in purpose_counts},
        "by_course": {c: count for c, count in course_counts if c},
        "matrix": matrix_data
    }
