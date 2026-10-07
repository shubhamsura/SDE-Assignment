# Bulk Certificate Generator API

A high-performance, asynchronous RESTful API built with **FastAPI**, **SQLAlchemy**, and **Pillow** designed to handle bulk certificate generation for large events, courses, and educational organizations.

---

## 📌 Features

- **Bulk Certificate Processing**: Submit batch requests containing dozens or hundreds of recipients in a single API call.
- **Asynchronous Background Execution**: API immediately returns a `202 Accepted` status with a `job_id`, delegating image generation to non-blocking background workers.
- **Resilient Failure Isolation**: Individual recipient validation or rendering failures do not halt or crash the overall batch job.
- **Real-Time Job Status Tracking**: Retrieve progress (total, completed, failed count) and per-certificate breakdown.
- **High-Quality Certificate Rendering**: Custom 1920x1350 image engine with dynamic text scaling, multi-layer borders, and official seal artwork.
- **Certificate Downloading Endpoint**: Download generated `.png` certificates directly via REST endpoint.

---

## 🛠️ Technology Stack

- **Language**: Python 3.10+
- **Web Framework**: FastAPI (Asynchronous REST API)
- **Database / ORM**: SQLite + SQLAlchemy 2.0 (Relational persistence)
- **Image Processing**: Pillow (PIL)
- **Validation**: Pydantic v2 + email-validator
- **Testing**: pytest + FastAPI TestClient (httpx)

---

## 📁 Project Structure

```text
bulk_cert_generator/
├── app/
│   ├── __init__.py
│   ├── database.py       # SQLAlchemy models, Pydantic schemas, and CRUD handlers
│   ├── generator.py      # High-resolution Pillow image rendering engine
│   └── main.py           # FastAPI routes, background workers, and dependency injection
├── templates/
│   └── base_template.png # High-res certificate base template
├── tests/
│   └── test_main.py      # Pytest suite covering all assignment requirements
├── generated_certs/      # Output directory for generated certificate PNG files
├── standalone.db         # SQLite relational database storage
├── requirements.txt      # Project dependencies
└── README.md             # Documentation
```

---

## 🏗️ Design & Architecture Decisions

### 1. Asynchronous Background Processing
- **Decision**: Used FastAPI's `BackgroundTasks` to decouple certificate image generation from the HTTP request/response cycle.
- **Reasoning**: Generating high-resolution image files for large batches (e.g., 50+ certificates) can take several seconds. Executing synchronously would cause HTTP timeouts and degrade client responsiveness. By processing asynchronously, the client receives an instant HTTP 202 response containing a `job_id` and can poll status asynchronously.

### 2. Relational Database Schema (`standalone.db`)
- **`Job` Model**: Stores overall batch metadata (`total_certificates`, `completed_certificates`, `failed_certificates`, `status`, `course_name`, `created_at`).
- **`Certificate` Model**: Foreign-key linked to `Job`. Stores recipient details (`recipient_name`, `recipient_email`), individual status (`PENDING`, `GENERATED`, `FAILED`), output `file_path`, and `error_reason`.

### 3. Fault Isolation & Resiliency
- Each certificate in a job loop is wrapped in isolated exception handling. If a single recipient's data fails rendering, `failed_certificates` counter increments, `error_reason` is recorded in SQLite, and the loop proceeds uninterrupted for remaining recipients.

---

## 🚀 Setup & Installation

### 1. Clone & Navigate
```bash
git clone https://github.com/shubham/SDE-Assignment.git
cd bulk_cert_generator
```

### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 3. Initialize Database
```bash
python -c "from app.database import init_db; init_db()"
```

---

## 💻 Running the Application

Start the Uvicorn development server from the root directory:

```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`. You can access the interactive Swagger API documentation at `http://127.0.0.1:8000/docs`.

---

## 🧪 Running Tests

Run the full pytest suite:

```bash
pytest
```

**Tested Scenarios**:
1. Creating a bulk certificate job (`POST /api/v1/jobs`)
2. Input validation for invalid names/emails (`HTTP 422`)
3. Background job progress tracking (`GET /api/v1/jobs/{job_id}`)
4. Certificate rendering & image output verification
5. Certificate retrieval & download (`GET /api/v1/certificates/{cert_id}/download`)
6. Failure isolation on invalid recipient data

---

## 📡 API Reference

### 1. Create Certificate Generation Job
- **Endpoint**: `POST /api/v1/jobs`
- **Status Code**: `202 Accepted`
- **Request Body**:
```json
{
  "course_name": "Fullstack Web Development",
  "date": "2026-10-07",
  "recipients": [
    { "name": "Alice Johnson", "email": "alice@example.com" },
    { "name": "Bob Smith", "email": "bob@example.com" }
  ]
}
```
- **Response**:
```json
{
  "job_id": "ac5840f8-a9a7-42cf-9420-3041f8bb25f2",
  "message": "Processing in background"
}
```

---

### 2. Retrieve Job Status
- **Endpoint**: `GET /api/v1/jobs/{job_id}`
- **Response**:
```json
{
  "job_id": "ac5840f8-a9a7-42cf-9420-3041f8bb25f2",
  "course_name": "Fullstack Web Development",
  "status": "COMPLETED",
  "total_certificates": 2,
  "completed_certificates": 2,
  "failed_certificates": 0,
  "created_at": "2026-10-07T09:15:20.123456",
  "certificates": [
    {
      "id": "27137535-19c7-4d51-8874-ef7098a0e35e",
      "recipient_name": "Alice Johnson",
      "recipient_email": "alice@example.com",
      "status": "GENERATED",
      "file_path": "generated_certs/Alice_Johnson_d98ec35f.png",
      "error_reason": null
    }
  ]
}
```

---

### 3. Download Certificate File
- **Endpoint**: `GET /api/v1/certificates/{cert_id}/download`
- **Response**: Binary PNG file stream (`image/png`).
