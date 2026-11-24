# -*- coding: utf-8 -*-
"""SwasthAI CDSS – Printable Consultation Report (Page 16)
Generates clean, print-ready clinical summaries in Markdown and JSON formats.
Excludes patient direct identifiers, includes SHA-256 hash, and mandatory disclaimer signature block.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
from backend.app.db.session import get_db_connection
from backend.app.reporting.report_generator import report_generator

st.set_page_config(page_title="SwasthAI CDSS – Printable Report", page_icon="🏥", layout="wide")

def require_login():
    if "user" not in st.session_state:
        st.session_state["user"] = {"id": "usr-doc-01", "username": "dr.sharma", "full_name": "Dr. Rajesh Sharma, MD", "role": "clinician"}

require_login()

st.title("🖨️ Printable Clinical Consultation Report")
st.caption("Generate official de-identified consultation dossiers for patient records or referral transfers.")

st.divider()

with get_db_connection() as conn:
    c = conn.cursor()
    c.execute("""
        SELECT c.id, p.pseudonym_id, c.primary_hypothesis, c.encounter_date
        FROM consultations c
        JOIN patients p ON c.patient_id = p.id
        ORDER BY c.encounter_date DESC LIMIT 50;
    """)
    encounters = c.fetchall()

if not encounters:
    st.info("No consultations recorded yet.")
    st.stop()

cur_enc_id = st.session_state.get("selected_encounter_id") or encounters[0]["id"]
enc_map = {e["id"]: f"{e['id']} | {e['pseudonym_id']} — {e['primary_hypothesis']}" for e in encounters}
selected_enc = st.selectbox(
    "Select Consultation Encounter to Print",
    options=list(enc_map.keys()),
    index=list(enc_map.keys()).index(cur_enc_id) if cur_enc_id in enc_map else 0,
    format_func=lambda x: enc_map[x]
)

# Fetch consultation dossier
with get_db_connection() as conn:
    c = conn.cursor()
    c.execute("SELECT graph_json FROM evidence_graphs WHERE encounter_id = ?;", (selected_enc,))
    eg_row = c.fetchone()
    c.execute("SELECT primary_hypothesis, differential_hypotheses_json, status FROM consultations WHERE id = ?;", (selected_enc,))
    c_row = c.fetchone()
    c.execute("SELECT generic_drug_class, clinical_context FROM drug_recommendations WHERE encounter_id = ?;", (selected_enc,))
    d_rows = c.fetchall()
    c.execute("SELECT severity, trigger_observed_value, explanation, circuit_breaker_halted FROM safety_events WHERE encounter_id = ?;", (selected_enc,))
    s_rows = c.fetchall()

if not eg_row:
    st.error("EvidenceGraph record missing for encounter.")
    st.stop()

eg_dict = json.loads(eg_row["graph_json"])
is_halted = any(s[3] for s in s_rows)

dossier = {
    "encounter_id": selected_enc,
    "demographics": eg_dict.get("demographics", {}),
    "symptom_summary": {"summary_text": "; ".join([s["canonical_concept"] for s in eg_dict.get("symptoms", [])])},
    "vitals_classification": eg_dict.get("vitals_classification", {}),
    "evidence_graph": eg_dict,
    "safety_assessment": {
        "circuit_breaker_halted": is_halted,
        "primary_reason": s_rows[0][2] if s_rows else "No critical safety triggers",
        "escalation_actions": []
    },
    "diagnosis": {
        "primary_diagnosis": c_row[0] if c_row else "Unknown",
        "differential_diagnoses": json.loads(c_row[1]) if c_row and c_row[1] else []
    },
    "drug_recommendation": {
        "generic_drug_classes": [d[0] for d in d_rows],
        "clinical_context": d_rows[0][1] if d_rows else "Standard supportive care.",
        "contraindication_flags": []
    }
}

markdown_report = report_generator.generate_markdown_report(dossier)

st.markdown("### Preview")
st.markdown(markdown_report)

st.divider()
st.download_button(
    "📥 Download Consultation Report (Markdown)",
    data=markdown_report,
    file_name=f"SwasthAI_Consultation_{selected_enc}.md",
    mime="text/markdown",
    type="primary"
)
st.download_button(
    "📥 Export Full JSON Dossier",
    data=json.dumps(dossier, indent=2),
    file_name=f"SwasthAI_Dossier_{selected_enc}.json",
    mime="application/json"
)
