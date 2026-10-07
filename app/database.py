import uuid
import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# --- Pydantic Validation Models ---

class RecipientInput(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr

class JobCreateRequest(BaseModel):
    course_name: str = Field(..., min_length=1)
    date: datetime.date
    recipients: list[RecipientInput]

# --- Database Setup & Enums ---

Base = declarative_base()

class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class CertStatus(str, Enum):
    PENDING = "PENDING"
    GENERATED = "GENERATED"
    FAILED = "FAILED"

# --- SQLAlchemy Models ---

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    course_name = Column(String, nullable=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    total_certificates = Column(Integer, nullable=False)
    completed_certificates = Column(Integer, default=0)
    failed_certificates = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    certificates = relationship("Certificate", back_populates="job", cascade="all, delete-orphan")

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    recipient_name = Column(String, nullable=False)
    recipient_email = Column(String, nullable=False)
    status = Column(SQLEnum(CertStatus), default=CertStatus.PENDING)
    file_path = Column(String, nullable=True)
    error_reason = Column(String, nullable=True)

    job = relationship("Job", back_populates="certificates")

# --- Database Config ---

DATABASE_URL = "sqlite:///./standalone.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

# --- CRUD Operations ---

def create_job(db_session, validated_data: JobCreateRequest) -> Job:
    total_certs = len(validated_data.recipients)
    new_job = Job(
        total_certificates=total_certs,
        course_name=validated_data.course_name
    )
    db_session.add(new_job)
    db_session.flush()

    certs_to_insert = [
        Certificate(
            job_id=new_job.id,
            recipient_name=rec.name,
            recipient_email=rec.email
        )
        for rec in validated_data.recipients
    ]
    db_session.bulk_save_objects(certs_to_insert)
    db_session.commit()
    db_session.refresh(new_job)
    return new_job

def update_certificate_status(db_session, cert_id: str, status: CertStatus, file_path: str = None, error: str = None):
    cert = db_session.query(Certificate).filter(Certificate.id == cert_id).first()
    if cert:
        cert.status = status
        if file_path:
            cert.file_path = file_path
        if error:
            cert.error_reason = error
        db_session.commit()
        return True
    return False

def get_job_by_id(db_session, job_id: str) -> Job:
    return db_session.query(Job).filter(Job.id == job_id).first()

if __name__ == "__main__":
    init_db()
    print("Database schema initialized.")