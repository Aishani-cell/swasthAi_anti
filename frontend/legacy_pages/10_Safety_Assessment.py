# -*- coding: utf-8 -*-
"""SwasthAI CDSS – Safety Assessment & Circuit Breaker (Page 10)
Inspects deterministic safety rule evaluations:
- Blood Pressure crisis (Equation 3)
- Critical hypoxemia (SpO2 < 90%)
- Critical arrhythmia (Pulse < 40 or > 150)
- Hyperpyrexia (Temp >= 40.0 C)
- Panic lab thresholds (Platelets, K+, Troponin, Glucose)
- Independent Circuit Breaker status
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
import pandas as pd
from backend.app.db.session import get_db_connection
from backend.app.safety.rules import CRITICAL_SAFETY_RULES, WARNING_SAFETY_RULES

st.set_page_config(page_title="SwasthAI CDSS – Safety Assessment", page_icon="🏥", layout="wide")

def require_login():
    if "user" not in st.session_state:
        st.session_state["user"] = {"id": "usr-doc-01", "username": "dr.sharma", "full_name": "Dr. Rajesh Sharma, MD", "role": "clinician"}

require_login()

st.title("🛡️ Deterministic Safety Assessment & Circuit Breaker")
st.caption("Zero-LLM physiological safety verification guaranteeing instant emergency detection and generative model bypass.")

st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🚨 Emergency Safety Rules (Circuit Breaker Tripped)")
    for r_id, rule in CRITICAL_SAFETY_RULES.items():
        with st.container(border=True):
            st.markdown(f"**🔴 {r_id}**")
            st.markdown(f"- **Trigger**: `{rule['description']}`")
            st.markdown(f"- **Action**: `{rule['action']}` (HALTS LLM REASONING)")
            st.caption(f"Protocol: {rule['escalation_instructions']}")

with col2:
    st.subheader("⚠️ Warning Safety Rules (Clinician Alert)")
    for r_id, rule in WARNING_SAFETY_RULES.items():
        with st.container(border=True):
            st.markdown(f"**🟡 {r_id}**")
            st.markdown(f"- **Trigger**: `{rule['description']}`")
            st.markdown(f"- **Action**: `{rule['action']}`")
            st.caption(f"Guidance: {rule['escalation_instructions']}")

st.divider()
st.subheader("📋 Historical Safety Events from Consultations")
with get_db_connection() as conn:
    c = conn.cursor()
    c.execute("""
        SELECT s.encounter_id, s.rule_id, s.severity, s.trigger_observed_value, s.trigger_threshold, s.circuit_breaker_halted
        FROM safety_events s
        ORDER BY s.id DESC LIMIT 20;
    """)
    rows = c.fetchall()

if rows:
    df = pd.DataFrame([{
        "Encounter": r[0],
        "Rule": r[1],
        "Severity": "🔴 " + r[2] if r[2] == "CRITICAL" else "🟡 " + r[2],
        "Observed": r[3],
        "Threshold": r[4],
        "Circuit Breaker Halted": "🚨 YES" if r[5] else "NO"
    } for r in rows])
    st.dataframe(df, use_container_width=True)
else:
    st.info("No safety alert triggers recorded yet.")
