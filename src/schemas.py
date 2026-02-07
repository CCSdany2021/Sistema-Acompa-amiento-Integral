from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from src.models import RoleEnum, SectionEnum, EduPurposeEnum, ReportStatus

class UserBase(BaseModel):
    id: Optional[int] = None
    email: EmailStr
    full_name: str
    role: RoleEnum

class UserCreate(UserBase):
    oid_sub: str
    assigned_section: Optional[SectionEnum] = None
    assigned_purpose: Optional[EduPurposeEnum] = None

class User(UserBase):
    id: int
    assigned_section: Optional[SectionEnum]
    assigned_purpose: Optional[EduPurposeEnum]
    
    class Config:
        from_attributes = True

class StudentBase(BaseModel):
    full_name: str
    code: str
    section: SectionEnum
    course: str
    email: Optional[EmailStr] = None

class Student(StudentBase):
    id: int
    class Config:
        from_attributes = True

class StudentReportSummary(BaseModel):
    id: int
    purpose: EduPurposeEnum
    status: ReportStatus
    
    class Config:
        from_attributes = True

class StudentWithReports(Student):
    active_reports: List[StudentReportSummary] = []

class ObservationBase(BaseModel):
    title: str
    content: str

class ObservationCreate(ObservationBase):
    date_log: Optional[datetime] = None

class Observation(ObservationBase):
    id: int
    report_id: int
    created_by_id: int
    date_log: datetime
    class Config:
        from_attributes = True

class RecommendationBase(BaseModel):
    content: str

class RecommendationCreate(RecommendationBase):
    date_log: Optional[datetime] = None

class Recommendation(RecommendationBase):
    id: int
    report_id: int
    created_by_id: int
    date_log: datetime
    class Config:
        from_attributes = True

class ReportBase(BaseModel):
    purpose: EduPurposeEnum
    objective: str
    academic_period: str
    assigned_to_id: Optional[int] = None

class ReportCreate(ReportBase):
    student_id: int

class Report(ReportBase):
    id: int
    status: ReportStatus
    created_by_id: int
    created_at: datetime
    closed_at: Optional[datetime]
    
    student: Optional[Student] = None
    assigned_to: Optional[UserBase] = None
    
    observations: List[Observation] = []
    recommendations: List[Recommendation] = []
    
    class Config:
        from_attributes = True
