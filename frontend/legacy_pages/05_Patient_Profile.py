"""
SwasthAI — Patient Profile
============================
Displays demographics, medical history, and past consultations for a
selected patient.  Links to start a new consultation.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Patient Profile · SwasthAI", page_icon="👤", layout="wide")

from backend.app.db.session import init_db
from backend.app.ehr.patient_service import patient_ehr_service

init_db()


def require_login():
    if "user" not in st.session_state:
        st.warning("🔒 Please log in first.")
        st.stop()

require_login()

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="background:linear-gradient(135deg,#0D6E6E,#148F77);
                padding:24px 32px;border-radius:12px;color:#fff;
                margin-bottom:24px;">
        <h2 style="margin:0;color:#fff;">👤 Patient Profile</h2>
        <p style="margin:6px 0 0;opacity:0.9;">
            Demographics · Medical History · Consultation Timeline
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Patient ID input ───────────────────────────────────────────────────────
default_pid = st.session_state.get("selected_patient_id", "")

patient_id = st.text_input(
    "Patient ID",
    value=default_pid,
    placeholder="e.g. pat-abc1234567",
    help="Enter the patient ID to view their full profile.",
)

if not patient_id:
    st.info("Enter a Patient ID above, or navigate here from Search Patients.")
    st.stop()

# ── Load patient data ──────────────────────────────────────────────────────
patient = patient_ehr_service.get_patient_by_id(patient_id.strip())

if not patient:
    st.error(f"❌ Patient `{patient_id}` not found.")
    st.stop()

history = patient_ehr_service.get_patient_history(patient_id.strip())


# ── Demographics card ──────────────────────────────────────────────────────
st.markdown("### Demographics")
d1, d2, d3, d4, d5 = st.columns(5)
d1.metric("Patient ID", patient.get("id", "—"))
d2.metric("Pseudonym", patient.get("pseudonym_id", "—"))
d3.metric("Age", f"{patient.get('age', '—')} yrs")
d4.metric("Sex", patient.get("sex", "—"))
d5.metric("Pregnant", "Yes" if patient.get("is_pregnant") else "No")

st.caption(f"Registered: {patient.get('created_at', '—')}")

# Quick action
st.markdown("")
if st.button("📋 Start New Consultation", type="primary", use_container_width=False):
    st.session_state["selected_patient_id"] = patient_id
    st.switch_page("pages/06_New_Consultation.py")


# ── Medical history ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Medical History")

conditions = history.get("chronic_conditions", [])
allergies = history.get("allergies", [])
medications = history.get("active_medications", [])

col_cond, col_allergy, col_meds = st.columns(3)

with col_cond:
    st.markdown("#### Chronic Conditions")
    if conditions:
        for c in conditions:
            st.markdown(f"- {c}")
    else:
        st.caption("No chronic conditions recorded.")

with col_allergy:
    st.markdown("#### Known Allergies")
    if allergies:
        for a in allergies:
            st.markdown(f"- ⚠️ {a}")
    else:
        st.caption("No known drug/food allergies.")

with col_meds:
    st.markdown("#### Active Medications")
    if medications:
        for m in medications:
            st.markdown(f"- 💊 {m}")
    else:
        st.caption("No active medications.")


# ── Past consultations ──────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Past Consultations")

encounters = history.get("past_consultations", [])
if encounters:
    df = pd.DataFrame(encounters)
    display_cols = {
        "id": "Encounter ID",
        "encounter_date": "Date",
        "status": "Status",
        "primary_hypothesis": "Primary Hypothesis",
        "reviewed_by_clinician": "Clinician Reviewed",
    }
    # Only keep columns that exist
    available = [c for c in display_cols if c in df.columns]
    df = df[available].rename(columns=display_cols)
    if "Clinician Reviewed" in df.columns:
        df["Clinician Reviewed"] = df["Clinician Reviewed"].map({0: "❌ No", 1: "✅ Yes"})

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Detail expanders
    for enc in encounters:
        with st.expander(f"📋 {enc.get('id', '?')} — {enc.get('status', '?')}"):
            st.markdown(f"**Date**: {enc.get('encounter_date', '—')}")
            st.markdown(f"**Status**: `{enc.get('status', '—')}`")
            st.markdown(f"**Primary Hypothesis**: {enc.get('primary_hypothesis', '—')}")

            diff_json = enc.get("differential_hypotheses_json")
            if diff_json:
                import json
                try:
                    diffs = json.loads(diff_json) if isinstance(diff_json, str) else diff_json
                    if diffs:
                        st.markdown("**Differentials**: " + ", ".join(str(d) for d in diffs))
                except Exception:
                    pass

            reviewed = enc.get("reviewed_by_clinician", 0)
            if reviewed:
                st.success("✅ Reviewed by clinician")
            else:
                st.warning("⏳ Awaiting clinician review")

            ec1, ec2 = st.columns(2)
            with ec1:
                if st.button("🔬 View Evidence", key=f"ev_{enc.get('id')}"):
                    st.session_state["selected_encounter_id"] = enc.get("id")
                    st.switch_page("pages/08_Evidence_Explorer.py")
else:
    st.info("No consultations recorded for this patient yet.")
