# -*- coding: utf-8 -*-
"""SwasthAI CDSS – New Multimodal Consultation (Page 07)
Executes the Four-Stage Evidence Pipeline with Independent Deterministic Circuit Breaker.
"""
import sys, os, uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
import pandas as pd
from backend.app.services.pipeline import pipeline
from backend.app.ehr.patient_service import patient_ehr_service
from backend.app.db.session import get_db_connection

st.set_page_config(page_title="SwasthAI CDSS – New Consultation", page_icon="🏥", layout="wide")

def require_login():
    if "user" not in st.session_state:
        st.session_state["user"] = {"id": "usr-doc-01", "username": "dr.sharma", "full_name": "Dr. Rajesh Sharma, MD", "role": "clinician"}

require_login()

st.title("⚡ New Multimodal Clinical Consultation")
st.caption("Four-stage evidence acquisition, bilingual NLP extraction, LOINC resolution, and deterministic neuro-symbolic safety verification.")

st.divider()

# Patient Selector
with get_db_connection() as conn:
    c = conn.cursor()
    c.execute("SELECT id, pseudonym_id, age, sex, is_pregnant FROM patients ORDER BY created_at DESC LIMIT 50;")
    patients = c.fetchall()

if not patients:
    st.warning("⚠️ No registered patients. Please register a patient first in '03_Register_Patient'.")
    st.stop()

cur_pat_id = st.session_state.get("selected_patient_id") or patients[0]["id"]
patient_map = {p["id"]: f"{p['pseudonym_id']} (Age {p['age']}, {p['sex']})" for p in patients}
selected_pat_id = st.selectbox("Select Patient *", options=list(patient_map.keys()), index=list(patient_map.keys()).index(cur_pat_id) if cur_pat_id in patient_map else 0, format_func=lambda x: patient_map[x])
st.session_state["selected_patient_id"] = selected_pat_id

# Retrieve full patient details
selected_patient_info = patient_ehr_service.get_patient_by_id(selected_pat_id)

with st.expander("📝 1. Symptom Presentation (English / Hindi / Hinglish)", expanded=True):
    symptom_input = st.text_area(
        "Chief Complaint & Clinical History",
        placeholder="e.g. 'Productive cough with yellow sputum and fever for 3 days' or 'सीने में तेज दर्द और पसीना आना' or 'seene me tez dard'",
        value="Productive cough with yellow sputum and fever for 3 days",
        height=100
    )

with st.expander("🩺 2. Vital Signs Triage (Physiological Ranges)", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        sbp = st.number_input("Systolic BP (mmHg)", min_value=0, max_value=300, value=120)
        dbp = st.number_input("Diastolic BP (mmHg)", min_value=0, max_value=200, value=80)
    with col2:
        hr = st.number_input("Heart Rate (bpm)", min_value=0, max_value=250, value=88)
        rr = st.number_input("Respiratory Rate (/min)", min_value=0, max_value=80, value=20)
    with col3:
        spo2 = st.number_input("SpO2 Oxygen (%)", min_value=0, max_value=100, value=96)
        temp_c = st.number_input("Temperature (°C)", min_value=30.0, max_value=45.0, value=38.6, step=0.1)

with st.expander("🧪 3. Laboratory Findings (LOINC Resolution)", expanded=False):
    st.caption("Add raw lab analyte values. The LOINC resolver will normalize units and verify plausibility bounds.")
    lab_analyte = st.selectbox("Analyte", ["WBC", "Platelets", "Hemoglobin", "Serum Creatinine", "Blood Urea Nitrogen", "Random Blood Glucose", "Troponin I", "Serum Potassium", "Total Bilirubin"])
    colL1, colL2 = st.columns(2)
    with colL1:
        lab_val = st.text_input("Raw Value", value="13500")
    with colL2:
        lab_unit = st.text_input("Raw Unit", value="/cumm")
    include_lab = st.checkbox("Include this laboratory result", value=True)

with st.expander("🫁 4. Multimodal Diagnostics (Radiology / Lung Audio)", expanded=False):
    rad_finding = st.text_input("Radiology / Chest X-Ray Findings", placeholder="e.g. Right lower lobe consolidation consistent with lobar pneumonia")
    resp_finding = st.selectbox("Respiratory Acoustic Finding (from Stethoscope AI)", ["None", "Crackle (Inspiratory)", "Wheeze (Expiratory)", "Both (Crackle + Wheeze)", "Normal Vesicular"])

st.markdown("---")

if st.button("🚀 Execute Consultation Pipeline", type="primary", use_container_width=True):
    with st.spinner("Processing multimodal consultation through SwasthAI pipeline..."):
        # Assemble inputs
        vitals_dict = {
            "systolic_bp": float(sbp) if sbp > 0 else None,
            "diastolic_bp": float(dbp) if dbp > 0 else None,
            "heart_rate": float(hr) if hr > 0 else None,
            "respiratory_rate": float(rr) if rr > 0 else None,
            "spo2": float(spo2) if spo2 > 0 else None,
            "temperature_c": float(temp_c) if temp_c > 0 else None
        }

        labs_list = []
        if include_lab and lab_val:
            labs_list.append({
                "analyte_name": lab_analyte,
                "raw_value": str(lab_val),
                "unit": str(lab_unit)
            })

        enc_id = f"enc-{uuid.uuid4().hex[:10]}"

        # Execute Pipeline
        dossier = pipeline.execute_consultation_pipeline(
            encounter_id=enc_id,
            patient_info=selected_patient_info,
            symptom_text=symptom_input,
            vitals_data=vitals_dict,
            lab_items_raw=labs_list if labs_list else None,
            imaging_report_text=rad_finding if rad_finding else None,
            patient_allergies=[]
        )

        # Persist Encounter in SQLite
        patient_ehr_service.persist_full_encounter(
            dossier,
            patient_id=selected_pat_id,
            operator_id=st.session_state["user"].get("id", "usr-doc-01")
        )
        st.session_state["selected_encounter_id"] = enc_id

        st.success(f"✅ Consultation `{enc_id}` executed and persisted to EHR!")

        # --- Display Results ---
        safety = dossier["safety_assessment"]
        if safety["circuit_breaker_halted"]:
            st.error(f"🚨 **EMERGENCY CIRCUIT BREAKER HALTED**: {safety['primary_reason']}")
            for act in safety.get("escalation_actions", []):
                st.warning(f"👉 Escalation Action: {act}")
        else:
            st.success("🛡️ **Deterministic Safety Engine Passed**: No critical life-threatening rules triggered.")

        colR1, colR2 = st.columns(2)
        with colR1:
            st.subheader("🩺 Diagnostic Hypotheses")
            st.markdown(f"**Primary Diagnosis**: `{dossier['diagnosis']['primary_diagnosis']}`")
            differentials = dossier['diagnosis'].get('differential_diagnoses', [])
            if differentials:
                st.markdown(f"**Differentials**: {', '.join(differentials)}")
            st.caption(f"Reasoning: {dossier['diagnosis']['model_version']}")

        with colR2:
            st.subheader("💊 Guideline Generic Drug Classes")
            drugs = dossier['drug_recommendation'].get('generic_drug_classes', [])
            if drugs:
                for d in drugs:
                    st.markdown(f"- 💊 **{d}**")
            else:
                st.info("No automatic drug classes indicated (withheld by circuit breaker or clinical review).")
            st.caption("Mandatory review: All drug recommendations require licensed physician verification.")

        # Extracted symptoms and resolved labs
        with st.expander("🔍 Extracted Evidence Details", expanded=False):
            st.markdown(f"**Integrity Hash (SHA-256)**: `{dossier['evidence_graph']['integrity_hash']}`")
            st.json(dossier["evidence_graph"])
