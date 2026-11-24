"""
Consultation & Multimodal Pipeline Endpoints
"""
import uuid
import json
import hashlib
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from backend.app.schemas.vitals import VitalsInput
from backend.app.services.pipeline import pipeline
from backend.app.ehr.patient_service import patient_ehr_service
from backend.app.reporting.report_generator import report_generator
from backend.app.db.session import get_db_connection
from backend.app.agents.lab_agent.service import lab_agent_service

router = APIRouter(prefix="/consultations", tags=["Consultations"])

class CreateConsultationRequest(BaseModel):
    patient_id: str
    symptoms_text: Optional[str] = None
    vitals: Optional[Dict[str, Any]] = None
    labs: Optional[List[Dict[str, Any]]] = None
    imaging_findings: Optional[str] = None
    respiratory_audio_path: Optional[str] = None
    patient_allergies: Optional[List[str]] = []

class NewConsultationRequest(BaseModel):
    patient_id: str
    operator_id: str


@router.post("/create")
def create_consultation_record(req: NewConsultationRequest):
    """Create a new IN_PROGRESS consultation for an existing patient.

    The consultation is owned by the authenticated Healthpod Operator and
    linked to exactly one existing patient. No patient record is created
    here; use /patients for patient registration.
    """
    pat = patient_ehr_service.get_patient_by_id(req.patient_id)
    if not pat:
        raise HTTPException(status_code=404, detail="Patient record not found")

    enc_id = f"enc-{uuid.uuid4().hex[:10]}"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO consultations (id, patient_id, operator_id, status)
               VALUES (?, ?, ?, 'IN_PROGRESS');""",
            (enc_id, req.patient_id, req.operator_id),
        )
        conn.commit()

    return {"encounter_id": enc_id, "patient_id": req.patient_id, "operator_id": req.operator_id, "status": "IN_PROGRESS"}


@router.post("")
def create_consultation(req: CreateConsultationRequest):
    pat = patient_ehr_service.get_patient_by_id(req.patient_id)
    if not pat:
        raise HTTPException(status_code=404, detail="Patient record not found")

    enc_id = f"enc-{uuid.uuid4().hex[:10]}"
    dossier = pipeline.execute_consultation_pipeline(
        encounter_id=enc_id,
        patient_info=pat,
        symptom_text=req.symptoms_text,
        vitals_data=req.vitals,
        lab_items_raw=req.labs,
        imaging_report_text=req.imaging_findings,
        respiratory_file_path=req.respiratory_audio_path,
        patient_allergies=req.patient_allergies
    )

    # Persist in SQLite EHR
    patient_ehr_service.persist_full_encounter(dossier, patient_id=req.patient_id)
    return dossier


@router.post("/{encounter_id}/extract-labs")
def extract_laboratory_documents(encounter_id: str, files: List[UploadFile] = File(...)):
    """Extract laboratory analytes from uploaded report files.

    Runs existing OCR/PDF extraction and deterministic lab parser,
    stores raw OCR text for audit, and returns parsed items for review.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM consultations WHERE id = ?;", (encounter_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Encounter not found")

    extracted_items = []
    extracted_files = []

    for file in files:
        if not file.filename:
            continue
        raw_text = lab_agent_service.extract_text_from_file(file.file, filename=file.filename)
        file_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        doc_id = f"labdoc-{uuid.uuid4().hex[:10]}"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO lab_documents (id, encounter_id, file_name, file_hash, raw_text) VALUES (?, ?, ?, ?, ?);",
                (doc_id, encounter_id, file.filename, file_hash, raw_text),
            )
            conn.commit()
        extracted_items.extend(lab_agent_service.extract_from_file(file.file, file.filename))
        extracted_files.append({"filename": file.filename, "raw_text": raw_text})

    return {
        "extracted_items": [item.model_dump() for item in extracted_items],
        "files": extracted_files,
        "count": len(extracted_items),
    }


@router.get("/{encounter_id}")
def get_consultation(encounter_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM consultations WHERE id = ?;", (encounter_id,))
        enc = cursor.fetchone()
        if not enc:
            raise HTTPException(status_code=404, detail="Consultation not found")
        
        # Fetch vitals
        cursor.execute("SELECT * FROM vitals WHERE encounter_id = ?;", (encounter_id,))
        v_row = cursor.fetchone()
        # Fetch symptoms
        cursor.execute("SELECT * FROM extracted_symptoms WHERE encounter_id = ?;", (encounter_id,))
        s_rows = cursor.fetchall()
        # Fetch labs
        cursor.execute("SELECT * FROM lab_results WHERE encounter_id = ?;", (encounter_id,))
        l_rows = cursor.fetchall()
        # Fetch safety events
        cursor.execute("SELECT * FROM safety_events WHERE encounter_id = ?;", (encounter_id,))
        safe_rows = cursor.fetchall()
        # Fetch drug recommendations
        cursor.execute("SELECT * FROM drug_recommendations WHERE encounter_id = ?;", (encounter_id,))
        drug_rows = cursor.fetchall()

        return {
            "consultation": dict(enc),
            "vitals": dict(v_row) if v_row else None,
            "symptoms": [dict(s) for s in s_rows],
            "labs": [dict(l) for l in l_rows],
            "safety_events": [dict(s) for s in safe_rows],
            "drug_recommendations": [dict(d) for d in drug_rows]
        }

@router.get("/{encounter_id}/report")
def get_consultation_report(encounter_id: str, format: str = "markdown"):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT graph_json FROM evidence_graphs WHERE encounter_id = ?;", (encounter_id,))
        eg_row = cursor.fetchone()
        if not eg_row:
            raise HTTPException(status_code=404, detail="EvidenceGraph not found for encounter")
        eg_dict = json.loads(eg_row["graph_json"])

        cursor.execute("SELECT primary_hypothesis, differential_hypotheses_json FROM consultations WHERE id = ?;", (encounter_id,))
        c_row = cursor.fetchone()
        cursor.execute("SELECT severity, trigger_observed_value, explanation, circuit_breaker_halted FROM safety_events WHERE encounter_id = ?;", (encounter_id,))
        s_rows = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT generic_drug_class FROM drug_recommendations WHERE encounter_id = ?;", (encounter_id,))
        d_rows = [r["generic_drug_class"] for r in cursor.fetchall()]

        dossier = {
            "encounter_id": encounter_id,
            "demographics": eg_dict.get("demographics", {}),
            "symptom_summary": {"summary_text": "; ".join([s["canonical_concept"] for s in eg_dict.get("symptoms", [])])},
            "evidence_graph": eg_dict,
            "safety_assessment": {
                "circuit_breaker_halted": any(s.get("circuit_breaker_halted") for s in s_rows),
                "primary_reason": s_rows[0]["explanation"] if s_rows else "No safety triggers",
                "escalation_actions": []
            },
            "diagnosis": {
                "primary_diagnosis": c_row["primary_hypothesis"] if c_row else "Pending",
                "differential_diagnoses": json.loads(c_row["differential_hypotheses_json"]) if c_row and c_row["differential_hypotheses_json"] else []
            },
            "drug_recommendation": {
                "generic_drug_classes": d_rows,
                "clinical_context": "Guideline-directed generic guidance.",
                "contraindication_flags": []
            }
        }

        if format == "json":
            return dossier
        else:
            return {"report_markdown": report_generator.generate_markdown_report(dossier)}

@router.post("/{encounter_id}/review")
def review_consultation(encounter_id: str, clinician_id: str, notes: str, approved: bool = True):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE consultations 
               SET reviewed_by_clinician = ?, clinician_id = ?, clinician_notes = ?, reviewed_at = CURRENT_TIMESTAMP, status = 'CLINICIAN_REVIEWED'
               WHERE id = ?;""",
            (int(approved), clinician_id, notes, encounter_id)
        )
        return {"status": "SUCCESS", "encounter_id": encounter_id, "reviewed_by": clinician_id}
