# -*- coding: utf-8 -*-
"""SwasthAI CDSS – Longitudinal EHR & Medical History (Page 06)
Manage chronic disease history, active medications, and drug allergies.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
import pandas as pd
from backend.app.db.session import get_db_connection

st.set_page_config(page_title="SwasthAI CDSS – Medical History", page_icon="🏥", layout="wide")

def require_login():
    if "user" not in st.session_state:
        st.session_state["user"] = {"id": "usr-doc-01", "username": "dr.sharma", "full_name": "Dr. Rajesh Sharma, MD", "role": "clinician"}

require_login()

st.title("📁 Longitudinal EHR & Medical History")
st.caption("Update chronic illnesses, past surgeries, active medications, and drug allergies.")

st.divider()

with get_db_connection() as conn:
    c = conn.cursor()
    c.execute("SELECT id, pseudonym_id FROM patients ORDER BY created_at DESC LIMIT 50;")
    patients = c.fetchall()

if not patients:
    st.warning("No patients registered.")
    st.stop()

pat_id = st.session_state.get("selected_patient_id") or patients[0]["id"]
patient_options = {p["id"]: p["pseudonym_id"] for p in patients}
selected_pat = st.selectbox("Select Patient", options=list(patient_options.keys()), index=list(patient_options.keys()).index(pat_id) if pat_id in patient_options else 0, format_func=lambda x: patient_options[x])
st.session_state["selected_patient_id"] = selected_pat

# Fetch existing medical history
with get_db_connection() as conn:
    c = conn.cursor()
    c.execute("SELECT id, condition_name, icd10_code, status, allergies_json, current_medications_json, diagnosed_date FROM medical_history WHERE patient_id = ?;", (selected_pat,))
    records = c.fetchall()

st.subheader("Current Recorded History")
if records:
    df = pd.DataFrame([{
        "Condition": r["condition_name"],
        "ICD-10": r["icd10_code"] or "N/A",
        "Status": r["status"],
        "Allergies": ", ".join(json.loads(r["allergies_json"])) if r["allergies_json"] else "None",
        "Medications": ", ".join(json.loads(r["current_medications_json"])) if r["current_medications_json"] else "None",
        "Diagnosed": r["diagnosed_date"] or "Unknown"
    } for r in records])
    st.dataframe(df, use_container_width=True)
else:
    st.info("No medical history recorded for this patient.")

st.markdown("---")
st.subheader("➕ Add New Medical History Entry")

with st.form("add_med_history_form"):
    cond_name = st.text_input("Condition Name *", placeholder="e.g. Type 2 Diabetes Mellitus, Essential Hypertension")
    icd10 = st.text_input("ICD-10 Code (Optional)", placeholder="e.g. E11.9, I10")
    status = st.selectbox("Clinical Status", ["ACTIVE", "MANAGED", "RESOLVED"])
    allergies = st.text_input("Known Drug Allergies (comma separated)", placeholder="e.g. Penicillin, Sulfa drugs")
    meds = st.text_input("Current Medications (comma separated)", placeholder="e.g. Metformin 500mg, Amlodipine 5mg")
    diagnosed = st.date_input("Diagnosis Date")

    if st.form_submit_button("💾 Save Medical History Entry", type="primary"):
        if not cond_name:
            st.error("Condition name is required.")
        else:
            allergies_list = [a.strip() for a in allergies.split(",") if a.strip()]
            meds_list = [m.strip() for m in meds.split(",") if m.strip()]
            with get_db_connection() as conn:
                c = conn.cursor()
                import uuid
                entry_id = f"hist-{uuid.uuid4().hex[:8]}"
                c.execute("""
                    INSERT INTO medical_history 
                    (id, patient_id, condition_name, icd10_code, status, allergies_json, current_medications_json, diagnosed_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (entry_id, selected_pat, cond_name, icd10, status, json.dumps(allergies_list), json.dumps(meds_list), str(diagnosed)))
            st.success(f"Added '{cond_name}' to patient record.")
            st.rerun()
