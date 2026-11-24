"""
SwasthAI SQLite Database Schema Definitions
Faithfully implements the paper's 7 foundational tables:
1. patients
2. medical_history
3. consultations
4. vitals
5. lab_results
6. imaging_scans
7. extracted_symptoms

Extended with:
- respiratory_recordings
- evidence_graphs
- safety_events
- drug_recommendations
- audit_logs
- users
"""

CREATE_TABLES_SQL = """
PRAGMA foreign_keys = ON;

-- Users (ASHAs, ANMs, Technicians, Clinicians, Admins)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('asha', 'anm', 'technician', 'clinician', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 1: Patients (Foundational)
CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    phone_hash TEXT UNIQUE NOT NULL,
    aadhaar_hash TEXT,
    pseudonym_id TEXT UNIQUE NOT NULL,
    full_name TEXT,
    phone_number TEXT,
    email TEXT,
    dob TEXT,
    hashed_password TEXT,
    age INTEGER,
    sex TEXT CHECK(sex IN ('MALE', 'FEMALE', 'OTHER', 'UNKNOWN')),
    is_pregnant BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Medical History (Foundational)
CREATE TABLE IF NOT EXISTS medical_history (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    condition_name TEXT NOT NULL,
    icd10_code TEXT,
    status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'RESOLVED', 'MANAGED')),
    allergies_json TEXT, -- JSON array of known drug/food allergies
    current_medications_json TEXT, -- JSON array of active medications
    diagnosed_date TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- Table 3: Consultations / Encounters (Foundational)
CREATE TABLE IF NOT EXISTS consultations (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    operator_id TEXT,
    encounter_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'IN_PROGRESS' CHECK(status IN ('IN_PROGRESS', 'EXTRACTED', 'VERIFIED', 'EMERGENCY_HALTED', 'DIAGNOSED', 'RECOMMENDED', 'CLINICIAN_REVIEWED', 'COMPLETED')),
    missing_modalities_json TEXT, -- JSON array of uncollected modalities
    primary_hypothesis TEXT,
    differential_hypotheses_json TEXT,
    clinician_notes TEXT,
    reviewed_by_clinician BOOLEAN DEFAULT 0,
    clinician_id TEXT,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- Table 4: Vitals (Foundational)
CREATE TABLE IF NOT EXISTS vitals (
    id TEXT PRIMARY KEY,
    encounter_id TEXT NOT NULL,
    systolic_bp REAL,
    diastolic_bp REAL,
    heart_rate REAL,
    respiratory_rate REAL,
    temperature_c REAL,
    spo2 REAL,
    blood_glucose_mg_dl REAL,
    is_valid BOOLEAN DEFAULT 1,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (encounter_id) REFERENCES consultations(id) ON DELETE CASCADE
);

-- Table 5: Lab Results (Foundational)
CREATE TABLE IF NOT EXISTS lab_results (
    id TEXT PRIMARY KEY,
    encounter_id TEXT NOT NULL,
    analyte_name TEXT NOT NULL,
    raw_value TEXT NOT NULL,
    numeric_value REAL,
    unit TEXT,
    reference_interval TEXT,
    loinc_code TEXT,
    verification_status TEXT DEFAULT 'UNRESOLVED' CHECK(verification_status IN ('VERIFIED', 'NEEDS_REVIEW', 'UNRESOLVED', 'INVALID_UNIT', 'IMPLAUSIBLE', 'INCOMPLETE')),
    plausibility_flag TEXT,
    specimen TEXT,
    source_file_ref TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (encounter_id) REFERENCES consultations(id) ON DELETE CASCADE
);

-- Table 5b: Laboratory Documents (raw OCR text + filenames for audit)
CREATE TABLE IF NOT EXISTS lab_documents (
    id TEXT PRIMARY KEY,
    encounter_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (encounter_id) REFERENCES consultations(id) ON DELETE CASCADE
);

-- Table 6: Imaging Scans (Foundational)
CREATE TABLE IF NOT EXISTS imaging_scans (
    id TEXT PRIMARY KEY,
    encounter_id TEXT NOT NULL,
    modality TEXT CHECK(modality IN ('CR', 'DX', 'CT', 'XR', 'UNKNOWN')),
    body_part TEXT,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    metadata_verified BOOLEAN DEFAULT 0,
    dicom_patient_id_scrubbed BOOLEAN DEFAULT 0,
    reported_findings TEXT,
    human_review_required BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (encounter_id) REFERENCES consultations(id) ON DELETE CASCADE
);

-- Table 7: Extracted Symptoms (Foundational)
CREATE TABLE IF NOT EXISTS extracted_symptoms (
    id TEXT PRIMARY KEY,
    encounter_id TEXT NOT NULL,
    canonical_concept TEXT NOT NULL,
    original_phrase TEXT NOT NULL,
    language TEXT CHECK(language IN ('en', 'hi', 'hinglish')),
    is_negated BOOLEAN DEFAULT 0,
    extraction_method TEXT CHECK(extraction_method IN ('LEXICON_EXACT', 'RATCLIFF_OBERSHELP', 'LLM_FALLBACK')),
    confidence_score REAL,
    source_span TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (encounter_id) REFERENCES consultations(id) ON DELETE CASCADE
);

-- Extended: Respiratory Audio Recordings
CREATE TABLE IF NOT EXISTS respiratory_recordings (
    id TEXT PRIMARY KEY,
    encounter_id TEXT NOT NULL,
    audio_file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    duration_seconds REAL,
    sample_rate INTEGER,
    predicted_class TEXT CHECK(predicted_class IN ('normal', 'crackle', 'wheeze', 'both', 'unverified')),
    confidence REAL,
    cycle_count INTEGER,
    acoustic_embedding_ref TEXT,
    human_review_required BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (encounter_id) REFERENCES consultations(id) ON DELETE CASCADE
);

-- Extended: EvidenceGraph Snapshots
CREATE TABLE IF NOT EXISTS evidence_graphs (
    id TEXT PRIMARY KEY,
    encounter_id TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    graph_hash TEXT NOT NULL,
    graph_json TEXT NOT NULL,
    is_locked BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (encounter_id) REFERENCES consultations(id) ON DELETE CASCADE
);

-- Extended: Safety Events & Circuit Breaker Logs
CREATE TABLE IF NOT EXISTS safety_events (
    id TEXT PRIMARY KEY,
    encounter_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    ruleset_version TEXT NOT NULL,
    severity TEXT CHECK(severity IN ('CRITICAL', 'WARNING', 'INFO')),
    trigger_observed_value TEXT NOT NULL,
    trigger_threshold TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    circuit_breaker_halted BOOLEAN DEFAULT 0,
    escalation_instructions TEXT,
    clinician_acknowledged BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (encounter_id) REFERENCES consultations(id) ON DELETE CASCADE
);

-- Extended: Drug Recommendations
CREATE TABLE IF NOT EXISTS drug_recommendations (
    id TEXT PRIMARY KEY,
    encounter_id TEXT NOT NULL,
    generic_drug_class TEXT NOT NULL,
    clinical_context TEXT,
    guideline_citation TEXT,
    contraindication_status TEXT,
    physician_review_mandatory BOOLEAN DEFAULT 1,
    approved_by_clinician BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (encounter_id) REFERENCES consultations(id) ON DELETE CASCADE
);

-- Extended: Audit Logs (Least Privilege & Tamper Traceability)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    details TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone_hash);
CREATE INDEX IF NOT EXISTS idx_consultations_patient ON consultations(patient_id);
CREATE INDEX IF NOT EXISTS idx_vitals_encounter ON vitals(encounter_id);
CREATE INDEX IF NOT EXISTS idx_labs_encounter ON lab_results(encounter_id);
CREATE INDEX IF NOT EXISTS idx_symptoms_encounter ON extracted_symptoms(encounter_id);
CREATE INDEX IF NOT EXISTS idx_safety_encounter ON safety_events(encounter_id);
"""
