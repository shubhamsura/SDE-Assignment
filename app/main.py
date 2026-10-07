import os
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import (
    SessionLocal,
    init_db,
    create_job,
    get_job_by_id,
    update_certificate_status,
    JobCreateRequest,
    JobStatus,
    CertStatus,
    Certificate,
    Job
)
from app.generator import generate_single_certificate, build_test_template

# Ensure output directory exists
OUTPUT_DIR = "generated_certs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="Certificate Generator API")

@app.on_event("startup")
def startup_event():
    init_db()
    build_test_template("templates/base_template.png")

# --- Database Dependency Injection ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Background Worker ---
async def process_certificate_job(job_id: str, recipients: list, db_session: Session = None):
    owned_session = False
    if db_session is None:
        db_session = SessionLocal()
        owned_session = True

    try:
        job = get_job_by_id(db_session, job_id)
        if not job:
            return

        job.status = JobStatus.PROCESSING
        db_session.commit()

        template_path = os.path.join("templates", "base_template.png")

        for cert in job.certificates:
            result = generate_single_certificate(
                recipient_name=cert.recipient_name,
                template_path=template_path,
                output_dir=OUTPUT_DIR,
                course_name=job.course_name
            )
            
            if result["status"] == "GENERATED":
                update_certificate_status(
                    db_session, cert.id, CertStatus.GENERATED, file_path=result["file_path"]
                )
                job.completed_certificates += 1
            else:
                update_certificate_status(
                    db_session, cert.id, CertStatus.FAILED, error=result["error_reason"]
                )
                job.failed_certificates += 1
                
            db_session.commit()

        job.status = JobStatus.COMPLETED
        db_session.commit()
    finally:
        if owned_session:
            db_session.close()

# --- Endpoints ---

@app.post("/api/v1/jobs", status_code=202)
async def create_new_job(request: JobCreateRequest, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Save to real database
    new_job = create_job(db, request)
    
    # 2. Trigger real background task
    bg_tasks.add_task(process_certificate_job, new_job.id, request.recipients)
    
    return {"job_id": new_job.id, "message": "Processing in background"}


@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "course_name": job.course_name,
        "status": job.status.value if hasattr(job.status, "value") else job.status,
        "total_certificates": job.total_certificates,
        "completed_certificates": job.completed_certificates,
        "failed_certificates": job.failed_certificates,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "certificates": [
            {
                "id": cert.id,
                "recipient_name": cert.recipient_name,
                "recipient_email": cert.recipient_email,
                "status": cert.status.value if hasattr(cert.status, "value") else cert.status,
                "file_path": cert.file_path,
                "error_reason": cert.error_reason
            }
            for cert in job.certificates
        ]
    }


@app.get("/api/v1/certificates/{cert_id}/download")
async def download_certificate(cert_id: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    status_val = cert.status.value if hasattr(cert.status, "value") else cert.status
    if status_val != "GENERATED":
        raise HTTPException(status_code=400, detail="Certificate generation not yet complete or failed")

    if not cert.file_path or not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="File missing from disk")

    filename = os.path.basename(cert.file_path)
    return FileResponse(
        path=cert.file_path,
        filename=filename,
        media_type="image/png"
    )
