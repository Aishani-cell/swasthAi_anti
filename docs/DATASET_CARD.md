# SwasthAI Synthetic Clinical Encounters Dataset Card

## 1. Dataset Summary
- **Dataset Name**: SwasthAI-Synthetic-Encounters-500
- **Version**: 1.0.0
- **Domain**: Rural Primary Healthpod Clinical Decision Support (ITU-T Y.4218)
- **Target Location**: Satnavari, Maharashtra, India
- **Size**: 500 clinical encounter records (`encounters.jsonl`), with 25 records committed for demonstration (`encounters_demo.jsonl`).
- **Modalities Represented**:
  - Multilingual Symptoms (English, Devanagari Hindi, Romanized Hinglish) with negation handling.
  - Vital signs with physiological triage flags.
  - Laboratory reports mapped to LOINC standard codes.
  - Respiratory acoustics (ICBHI 2017 classes: normal, crackle, wheeze, both).
  - Explicitly logged missing modalities.
  - Deterministic safety outcomes (Approved vs Rejected).
  - Diagnostic hypotheses and generic-only drug classes.

---

## 2. Dataset Structure & Splits
- **Total Records**: 500
- **Split Breakdown**:
  - `train`: 350 records (70.0%)
  - `validation`: 75 records (15.0%)
  - `test`: 75 records (15.0%)
- **Distribution Strategy**: Stratified across all 25 disease categories (Cardiac, Infectious, Endocrine, Respiratory, Other) to prevent diagnostic and patient leakage.

---

## 3. Data Fields

| Field Name | Type | Description |
|---|---|---|
| `case_id` | string | Unique synthetic case identifier (`CASE-0001` to `CASE-0500`) |
| `synthetic_patient_id` | string | Synthetic patient identifier to test longitudinal re-identification |
| `encounter_id` | string | Unique encounter record identifier (`enc-0001`...) |
| `age` | integer | Patient age in years [18, 78] |
| `sex` | string | Biological sex (`MALE`, `FEMALE`) |
| `pregnancy_status` | boolean | Active pregnancy indicator for contraindication checks |
| `symptoms_original` | string | Free-text symptom chief complaint in EN, HI, or Hinglish |
| `symptom_language` | string | Language code (`en`, `hi`, `hinglish`) |
| `symptoms_normalized` | list[str] | Canonical concepts extracted by lexicon / fuzzy matcher |
| `negated_symptoms` | list[str] | Symptoms confirmed as absent / denied |
| `vital_signs` | object | Systolic BP, Diastolic BP, HR, RR, SpO2, Temp, Glucose |
| `laboratory_test_name`| string | Primary extracted analyte name |
| `laboratory_value` | float | Measured numeric value |
| `laboratory_unit` | string | Extracted measurement unit |
| `loinc_code` | string | Mapped official LOINC standard code |
| `laboratory_validation_status` | string | Triplet verification status (`VERIFIED`, `IMPLAUSIBLE`, etc.) |
| `missing_modalities`| list[str] | Uncollected modalities explicitly flagged |
| `safety_status` | string | Circuit breaker triage (`Approved`, `Rejected`) |
| `emergency_escalation_status` | boolean | True if life-threatening emergency rule tripped |
| `predicted_primary_diagnosis` | string | Output of the diagnosis agent |
| `predicted_drug_classes` | list[str] | Generic-only recommended drug classes |
| `gold_diagnosis` | string | Clinically annotated gold standard diagnosis |
| `gold_safety_status`| string | Expected safety status (`Approved`, `Rejected`) |
| `gold_drug_classes` | list[str] | Expected guideline-directed drug classes |
| `data_provenance` | string | Traceability signature |
| `split` | string | Dataset partition (`train`, `validation`, `test`) |

---

## 4. Intended Use & Ethical Safeguards
- **Purpose**: Software testing, deterministic safety engine validation, LOINC resolver auditing, and local RAG evaluation.
- **Safety Boundary**: All cases are purely synthetic simulations created for research benchmarking. They do NOT represent real human patients and must NOT be used for direct commercial marketing or unvalidated clinical care.
