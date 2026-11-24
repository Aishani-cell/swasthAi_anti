"""
Patient & Longitudinal EHR Service
Manages patient registration, phone hashing, medical history, and consultation persistence.
"""
import uuid
import json
from typing import Dict, Any, Optional, List
from backend.app.core.privacy import hash_identifier
from backend.app.db.session import get_db_connection
from backend.app.schemas.patient import PatientCreate, PatientResponse, MedicalHistoryEntry

class PatientEHRService:
    @staticmethod
    def register_patient(patient_in: PatientCreate) -> Dict[str, Any]:
        """Registers a patient, storing phone number ONLY as a one-way SHA-256 hash."""
        p_id = f"pat-{uuid.uuid4().hex[:10]}"
        pseudonym_id = f"SATNAVARI-{uuid.uuid4().hex[:6].upper()}"
        p_hash = hash_identifier(patient_in.phone_number)
        a_hash = hash_identifier(patient_in.aadhaar_number) if patient_in.aadhaar_number else None

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check if phone hash already exists
            cursor.execute("SELECT id, pseudonym_id, age, sex, is_pregnant, created_at FROM patients WHERE phone_hash = ?;", (p_hash,))
            existing = cursor.fetchone()
            if existing:
                return dict(existing)

            cursor.execute(
                """INSERT INTO patients (id, phone_hash, aadhaar_hash, pseudonym_id, age, sex, is_pregnant)
                   VALUES (?, ?, ?, ?, ?, ?, ?);""",
                (p_id, p_hash, a_hash, pseudonym_id, patient_in.age, patient_in.sex, int(patient_in.is_pregnant))
            )
            cursor.execute("SELECT id, pseudonym_id, age, sex, is_pregnant, created_at FROM patients WHERE id = ?;", (p_id,))
            new_pat = cursor.fetchone()
            return dict(new_pat)

    @staticmethod
    def register_patient_and_start_consultation(
        patient_in: "PatientCreate",
        operator_id: str,
    ) -> Dict[str, Any]:
        """Registers a new patient and creates its initial consultation
        inside a single database transaction so the two records can never
        be left inconsistent.

        Returns a dict with the patient record and the new encounter id.
        """
        p_id = f"pat-{uuid.uuid4().hex[:10]}"
        pseudonym_id = f"SATNAVARI-{uuid.uuid4().hex[:6].upper()}"
        p_hash = hash_identifier(patient_in.phone_number)
        a_hash = hash_identifier(patient_in.aadhaar_number) if patient_in.aadhaar_number else None
        enc_id = f"enc-{uuid.uuid4().hex[:10]}"

        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(
                    "SELECT id FROM patients WHERE phone_hash = ? OR phone_number = ?;",
                    (p_hash, patient_in.phone_number.strip()),
                )
                if cursor.fetchone():
                    raise ValueError("A patient with this phone number is already registered")

                cursor.execute(
                    """INSERT INTO patients (id, phone_hash, aadhaar_hash, pseudonym_id, full_name, phone_number, email, dob, hashed_password, age, sex, is_pregnant)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                    (
                        p_id,
                        p_hash,
                        a_hash,
                        pseudonym_id,
                        patient_in.full_name.strip() if patient_in.full_name else None,
                        patient_in.phone_number.strip(),
                        patient_in.email.strip() if patient_in.email else None,
                        patient_in.dob.strip() if patient_in.dob else None,
                        None,
                        int(patient_in.age) if patient_in.age is not None else None,
                        patient_in.sex.upper(),
                        int(patient_in.is_pregnant),
                    ),
                )
                cursor.execute(
                    """INSERT INTO consultations (id, patient_id, operator_id, status)
                       VALUES (?, ?, ?, 'IN_PROGRESS');""",
                    (enc_id, p_id, operator_id),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, pseudonym_id, full_name, phone_number, email, dob, age, sex, is_pregnant, created_at FROM patients WHERE id = ?;",
                (p_id,),
            )
            patient_record = dict(cursor.fetchone())

        return {"patient": patient_record, "encounter_id": enc_id}

    @staticmethod
    def get_patient_by_id(patient_id: str) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, pseudonym_id, age, sex, is_pregnant, created_at FROM patients WHERE id = ?;", (patient_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_patient_history(patient_id: str) -> Dict[str, Any]:
        """Retrieves longitudinal record: past consultations, chronic conditions, and allergies."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Patient details
            cursor.execute("SELECT id, pseudonym_id, age, sex, is_pregnant FROM patients WHERE id = ?;", (patient_id,))
            pat = cursor.fetchone()
            if not pat:
                return {}

            # Medical history
            cursor.execute("SELECT condition_name, icd10_code, status, allergies_json, current_medications_json FROM medical_history WHERE patient_id = ?;", (patient_id,))
            hist_rows = cursor.fetchall()
            conditions = []
            allergies = set()
            medications = set()
            for r in hist_rows:
                conditions.append(r["condition_name"])
                if r["allergies_json"]:
                    for a in json.loads(r["allergies_json"]):
                        allergies.add(a)
                if r["current_medications_json"]:
                    for m in json.loads(r["current_medications_json"]):
                        medications.add(m)

            # Past consultations
            cursor.execute(
                """SELECT id, encounter_date, status, primary_hypothesis, differential_hypotheses_json, reviewed_by_clinician
                   FROM consultations WHERE patient_id = ? ORDER BY encounter_date DESC;""",
                (patient_id,)
            )
            encounters = [dict(r) for r in cursor.fetchall()]

            return {
                "patient": dict(pat),
                "chronic_conditions": conditions,
                "allergies": sorted(list(allergies)),
                "active_medications": sorted(list(medications)),
                "past_consultations": encounters
            }

    @staticmethod
    def persist_full_encounter(pipeline_dossier: Dict[str, Any], patient_id: str, operator_id: str = "usr-asha-01") -> str:
        """Persists all outputs of the consultation pipeline into relational SQLite tables."""
        enc_id = pipeline_dossier["encounter_id"]
        eg = pipeline_dossier["evidence_graph"]
        diag = pipeline_dossier["diagnosis"]
        safety = pipeline_dossier["safety_assessment"]
        drug = pipeline_dossier["drug_recommendation"]

        status = "EMERGENCY_HALTED" if safety["circuit_breaker_halted"] else "DIAGNOSED"

        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Consultations table
            cursor.execute(
                """INSERT OR REPLACE INTO consultations 
                   (id, patient_id, operator_id, status, missing_modalities_json, primary_hypothesis, differential_hypotheses_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?);""",
                (enc_id, patient_id, operator_id, status, json.dumps(pipeline_dossier["missing_modalities"]), diag["primary_diagnosis"], json.dumps(diag["differential_diagnoses"]))
            )

            # Vitals table
            if eg.get("vitals"):
                v = eg["vitals"]
                cursor.execute(
                    """INSERT OR REPLACE INTO vitals (id, encounter_id, systolic_bp, diastolic_bp, heart_rate, respiratory_rate, temperature_c, spo2, blood_glucose_mg_dl)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                    (f"vit-{enc_id}", enc_id, v.get("systolic_bp"), v.get("diastolic_bp"), v.get("heart_rate"), v.get("respiratory_rate"), v.get("temperature_c"), v.get("spo2"), v.get("blood_glucose_mg_dl"))
                )

            # Extracted Symptoms table
            for idx, s in enumerate(eg.get("symptoms", []) + eg.get("negated_symptoms", [])):
                cursor.execute(
                    """INSERT OR REPLACE INTO extracted_symptoms (id, encounter_id, canonical_concept, original_phrase, language, is_negated, extraction_method, confidence_score, source_span)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                    (f"sym-{enc_id}-{idx}", enc_id, s["canonical_concept"], s["original_phrase"], s["language"], int(s["is_negated"]), s["extraction_method"], s["confidence_score"], s.get("source_span"))
                )

            # Resolved Labs table
            for idx, l in enumerate(eg.get("resolved_labs", [])):
                cursor.execute(
                    """INSERT OR REPLACE INTO lab_results (id, encounter_id, analyte_name, raw_value, numeric_value, unit, reference_interval, loinc_code, verification_status, plausibility_flag)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                    (f"lab-{enc_id}-{idx}", enc_id, l["canonical_name"], l["raw_value"], l["numeric_value"], l["canonical_unit"], l["reference_interval"], l["loinc_code"], l["verification_status"], l.get("plausibility_flag"))
                )

            # EvidenceGraph snapshot
            cursor.execute(
                """INSERT OR REPLACE INTO evidence_graphs (id, encounter_id, version, graph_hash, graph_json, is_locked)
                   VALUES (?, ?, ?, ?, ?, ?);""",
                (f"eg-{enc_id}", enc_id, 1, eg.get("integrity_hash", ""), json.dumps(eg), 1)
            )

            # Safety events
            for idx, alert in enumerate(safety.get("alerts", [])):
                cursor.execute(
                    """INSERT OR REPLACE INTO safety_events (id, encounter_id, rule_id, ruleset_version, severity, trigger_observed_value, trigger_threshold, action_taken, circuit_breaker_halted, escalation_instructions)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                    (f"safe-{enc_id}-{idx}", enc_id, alert["rule_id"], alert["ruleset_version"], alert["severity"], alert["observed_value"], alert["threshold"], "ESCALATION" if alert["circuit_breaker_halted"] else "REVIEW", int(alert["circuit_breaker_halted"]), alert.get("escalation_instructions"))
                )

            # Drug Recommendations
            for idx, d_class in enumerate(drug.get("generic_drug_classes", [])):
                cursor.execute(
                    """INSERT OR REPLACE INTO drug_recommendations (id, encounter_id, generic_drug_class, clinical_context, guideline_citation, contraindication_status)
                       VALUES (?, ?, ?, ?, ?, ?);""",
                    (f"drug-{enc_id}-{idx}", enc_id, d_class, drug.get("clinical_context"), "; ".join(drug.get("guideline_citations", [])), "APPROVED_FOR_REVIEW")
                )

        return enc_id

patient_ehr_service = PatientEHRService()
