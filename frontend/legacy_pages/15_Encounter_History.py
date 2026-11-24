# -*- coding: utf-8 -*-
"""SwasthAI CDSS – Encounter History Timeline (Page 15)
Chronological patient encounter timeline and longitudinal tracking.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
import pandas as pd
from backend.app.db.session import get_db_connection

st.set_page_config(page_title="SwasthAI CDSS – Encounter History", page_icon="🏥", layout="wide")

def require_login():
    if "user" not in st.session_state:
        st.session_state["user"] = {"id": "usr-doc-01", "username": "dr.sharma", "full_name": "Dr. Rajesh Sharma, MD", "role": "clinician"}

require_login()

st.title("⏳ Longitudinal Encounter History Timeline")
st.caption("Chronological consultation log for healthpod patients.")

st.divider()

with get_db_connection() as conn:
    c = conn.cursor()
    c.execute("""
        SELECT c.id, p.pseudonym_id, c.encounter_date, c.primary_hypothesis, c.status, c.reviewed_by_clinician, c.clinician_notes
        FROM consultations c
        JOIN patients p ON c.patient_id = p.id
        ORDER BY c.encounter_date DESC;
    """)
    rows = c.fetchall()

if rows:
    st.markdown(f"**Total Encounters Logged**: {len(rows)}")
    df = pd.DataFrame([{
        "Encounter ID": r[0],
        "Patient ID": r[1],
        "Date & Time": r[2],
        "Diagnostic Hypothesis": r[3],
        "Status": r[4],
        "Attested": "✅ Yes" if r[5] else "⏳ Pending",
        "Clinician Notes": r[6] or ""
    } for r in rows])
    st.dataframe(df, use_container_width=True)
else:
    st.info("No encounters logged yet.")
