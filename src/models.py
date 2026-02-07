from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from src.database import Base

# Enums
class RoleEnum(str, enum.Enum):
    DOCENTE = "Docente"
    COORDINADOR = "Coordinador"
    ADMIN_GLOBAL = "Admin Global"

class SectionEnum(str, enum.Enum):
    PREESCOLAR_PRIMARIA = "Jardín a Tercero"
    MEDIA_BASKICA = "Cuarto a Séptimo"
    BACHILLERATO = "Octavo a Undécimo"

class EduPurposeEnum(str, enum.Enum):
    CONVIVENCIA = "Convivencia"
    ACADEMICO = "Académico"
    ESPIRITUAL = "Espiritual"
    PSICOAFECTIVO = "Psicoafectivo"

class ReportStatus(str, enum.Enum):
    PROGRAMADO = "PROGRAMADO"
    SEGUIMIENTO = "SEGUIMIENTO"
    ATENDIDO = "ATENDIDO"

# Dynamic Menu Models
class Section(Base):
    __tablename__ = "sections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    courses = relationship("Course", back_populates="section", cascade="all, delete-orphan")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String) # e.g. "10A"
    
    section_id = Column(Integer, ForeignKey("sections.id"))
    section = relationship("Section", back_populates="courses")
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    oid_sub = Column(String, unique=True, index=True, nullable=True) # Microsoft ID
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    
    role = Column(Enum(RoleEnum), default=RoleEnum.DOCENTE)
    
    # Permissions
    assigned_section = Column(Enum(SectionEnum), nullable=True) # For Coordinators/Teachers
    assigned_purpose = Column(Enum(EduPurposeEnum), nullable=True) # For Teachers
    
    reports_created = relationship("Report", back_populates="created_by", foreign_keys="Report.created_by_id")
    reports_assigned = relationship("Report", back_populates="assigned_to", foreign_keys="Report.assigned_to_id")
    observations_created = relationship("Observation", back_populates="created_by")
    recommendations_created = relationship("Recommendation", back_populates="created_by")

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    code = Column(String, unique=True, index=True) # Codigo estudiantil
    email = Column(String, nullable=True)
    
    section = Column(Enum(SectionEnum))
    course = Column(String) # "401", "1102", etc.
    
    reports = relationship("Report", back_populates="student")

    @property
    def active_reports(self):
        return [r for r in self.reports if r.status in [ReportStatus.PROGRAMADO, ReportStatus.SEGUIMIENTO]]

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    
    student_id = Column(Integer, ForeignKey("students.id"))
    student = relationship("Student", back_populates="reports")
    
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="reports_created")
    
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], back_populates="reports_assigned")
    
    purpose = Column(Enum(EduPurposeEnum)) # Fin Educativo
    status = Column(Enum(ReportStatus), default=ReportStatus.PROGRAMADO)
    
    objective = Column(Text)
    academic_period = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    observations = relationship("Observation", back_populates="report", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="report", cascade="all, delete-orphan")

    # Constraint: Only one ACTIVE report (Programado/Seguimiento) per Student per Purpose
    # Note: SQLite doesn't support partial indexes easily, but Postgres does.
    # We will enforce this via application logic, but here is the args for Postgres.
    __table_args__ = (
        Index('ix_unique_active_report', 'student_id', 'purpose', unique=True, postgresql_where=(status.in_([ReportStatus.PROGRAMADO, ReportStatus.SEGUIMIENTO]))),
    )

class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    
    report_id = Column(Integer, ForeignKey("reports.id"))
    report = relationship("Report", back_populates="observations")
    
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User", back_populates="observations_created")
    
    title = Column(String)
    content = Column(Text) # Observaciones / Recomendaciones
    date_log = Column(DateTime(timezone=True), server_default=func.now())

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    
    report_id = Column(Integer, ForeignKey("reports.id"))
    report = relationship("Report", back_populates="recommendations")
    
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User", back_populates="recommendations_created")
    
    content = Column(Text) # Recomendaciones
    date_log = Column(DateTime(timezone=True), server_default=func.now())
