"""
Patient Registration and Longitudinal EHR Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.app.schemas.patient import PatientCreate, PatientResponse
from backend.app.ehr.patient_service import patient_ehr_service
from backend.app.db.session import get_db_connection
from backend.app.core.privacy import hash_identifier

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.post("", response_model=PatientResponse)
def register_patient(patient_in: PatientCreate):
    pat = patient_ehr_service.register_patient(patient_in)
    return PatientResponse(**pat)

@router.get("", response_model=List[PatientResponse])
def list_patients(limit: int = 50, offset: int = 0):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, pseudonym_id, age, sex, is_pregnant, created_at FROM patients ORDER BY created_at DESC LIMIT ? OFFSET ?;", (limit, offset))
        rows = cursor.fetchall()
        return [PatientResponse(**dict(r)) for r in rows]

@router.get("/search")
def search_patients(q: str = Query(..., description="Phone number, patient ID or pseudonym")):
    """Search existing patients for the 'Login an Existing Patient' workflow."""
    query = (q or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Search query is required")

    q_hash = hash_identifier(query)
    like = f"%{query}%"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, pseudonym_id, full_name, phone_number, age, sex, is_pregnant, created_at
               FROM patients
               WHERE id = ? OR pseudonym_id = ? OR phone_hash = ? OR phone_number LIKE ? OR full_name LIKE ?
               ORDER BY created_at DESC LIMIT 20;""",
            (query, query, q_hash, like, like),
        )
        rows = cursor.fetchall()
    return [dict(r) for r in rows]

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str):
    pat = patient_ehr_service.get_patient_by_id(patient_id)
    if not pat:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse(**pat)

@router.get("/{patient_id}/history")
def get_patient_history(patient_id: str):
    history = patient_ehr_service.get_patient_history(patient_id)
    if not history:
        raise HTTPException(status_code=404, detail="Patient not found")
    return history
