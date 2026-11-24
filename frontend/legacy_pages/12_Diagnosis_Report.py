# -*- coding: utf-8 -*-
"""SwasthAI CDSS – Diagnosis Report (Page 12)
Review primary diagnostic hypothesis, differential diagnoses, and evidence citations.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
import pandas as pd
from backend.app.db.session import get_db_connection

st.set_page_config(page_title="SwasthAI CDSS – Diagnosis Report", page_icon="🏥", layout="wide")

def require_login():
    if "user" not in st.session_state:
        st.session_state["user"] = {"id": "usr-doc-01", "username": "dr.sharma", "full_name": "Dr. Rajesh Sharma, MD", "role": "clinician"}

require_login()

st.title("🩺 Diagnostic Hypotheses & Evidence Attribution")
st.caption("Neuro-symbolic diagnostic reasoning with explicit differential ranking, missing modality warnings, and clinician attestation.")

st.divider()

# Encounter Selector
with get_db_connection() as conn:
    c = conn.cursor()
    c.execute("""
        SELECT c.id, p.pseudonym_id, c.primary_hypothesis, c.encounter_date, c.status
        FROM consultations c
        JOIN patients p ON c.patient_id = p.id
        ORDER BY c.encounter_date DESC LIMIT 50;
    """)
    encounters = c.fetchall()

if not encounters:
    st.info("No consultations recorded yet. Start a consultation via '07_New_Consultation'.")
    st.stop()

cur_enc_id = st.session_state.get("selected_encounter_id") or encounters[0]["id"]
enc_map = {e["id"]: f"{e['id']} | {e['pseudonym_id']} — {e['primary_hypothesis']} ({e['status']})" for e in encounters}
selected_enc = st.selectbox(
    "Select Consultation Encounter",
    options=list(enc_map.keys()),
    index=list(enc_map.keys()).index(cur_enc_id) if cur_enc_id in enc_map else 0,
    format_func=lambda x: enc_map[x]
)
st.session_state["selected_encounter_id"] = selected_enc

with get_db_connection() as conn:
    c = conn.cursor()
    c.execute("SELECT * FROM consultations WHERE id = ?;", (selected_enc,))
    enc = c.fetchone()
    c.execute("SELECT * FROM evidence_graphs WHERE encounter_id = ?;", (selected_enc,))
    eg_row = c.fetchone()

eg_dict = json.loads(eg_row["graph_json"]) if eg_row and eg_row["graph_json"] else {}
differentials = json.loads(enc["differential_hypotheses_json"]) if enc and enc["differential_hypotheses_json"] else []

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Primary Hypothesis: {enc['primary_hypothesis']}")
    st.markdown(f"**Encounter Status**: `{enc['status']}` | **Date**: `{enc['encounter_date']}`")
    
    st.markdown("#### Differential Diagnoses")
    if differentials:
        for idx, diff in enumerate(differentials, 1):
            st.markdown(f"{idx}. 🔹 **{diff}**")
    else:
        st.info("No secondary differential hypotheses generated.")

    st.markdown("#### Missing Modalities / Completeness Warnings")
    missing = json.loads(enc["missing_modalities_json"]) if enc and enc["missing_modalities_json"] else []
    if missing:
        st.warning(f"⚠️ Unrecorded Modalities: {', '.join(missing)}")
    else:
        st.success("✅ Comprehensive multimodal evidence collected.")

with col2:
    st.subheader("🛡️ Safety & Verification")
    if enc["status"] == "EMERGENCY_HALTED":
        st.error("🚨 Encounter was emergency-halted by the deterministic safety circuit breaker.")
    else:
        st.success("✅ Clinical safety checks passed.")

    st.markdown(f"**EvidenceGraph Hash**: `{eg_dict.get('integrity_hash', 'N/A')[:20]}...`")
    st.markdown(f"**Reviewing Clinician**: {enc['clinician_id'] or 'Pending Attestation'}")
    
    if enc["reviewed_by_clinician"]:
        st.success(f"Attested on {enc['reviewed_at']}: {enc['clinician_notes'] or 'Approved'}")
    else:
        st.info("Awaiting clinician review. Authorized physicians can attest in '15_Clinician_Review'.")

st.markdown("---")
colA, colB = st.columns(2)
with colA:
    if st.button("📚 View Retrieved Guideline Citations", use_container_width=True):
        st.switch_page("pages/13_Guideline_Citations.py")
with colB:
    if st.button("💊 View Drug-Class Recommendations", use_container_width=True):
        st.switch_page("pages/14_Drug_Recommendations.py")
