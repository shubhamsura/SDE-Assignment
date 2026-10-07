import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import init_db

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()

client = TestClient(app)

def test_create_generation_job():
    payload = {
        "course_name": "Pytest Certification",
        "date": "2026-10-07",
        "recipients": [
            {"name": "Alice Testing", "email": "alice@test.com"},
            {"name": "Bob Testing", "email": "bob@test.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["message"] == "Processing in background"

def test_input_validation():
    # Empty recipient name should trigger HTTP 422 Unprocessable Entity
    invalid_payload = {
        "course_name": "Validation Test",
        "date": "2026-10-07",
        "recipients": [
            {"name": "", "email": "invalid-email"}
        ]
    }
    response = client.post("/api/v1/jobs", json=invalid_payload)
    assert response.status_code == 422

def test_job_status_and_certificate_retrieval():
    payload = {
        "course_name": "Retrieval Test",
        "date": "2026-10-07",
        "recipients": [
            {"name": "Charlie Test", "email": "charlie@test.com"}
        ]
    }
    res = client.post("/api/v1/jobs", json=payload)
    job_id = res.json()["job_id"]

    # Retrieve status
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    job_data = status_res.json()
    assert job_data["total_certificates"] == 1
    assert len(job_data["certificates"]) == 1

    cert_id = job_data["certificates"][0]["id"]
    
    # Test certificate download retrieval
    dl_res = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "image/png"

def test_handling_individual_certificate_failure():
    from app.generator import generate_single_certificate
    # Test empty recipient name failure in engine
    result = generate_single_certificate("", "templates/base_template.png", "generated_certs")
    assert result["status"] == "FAILED"
    assert "Empty recipient name" in result["error_reason"]
