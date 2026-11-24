# -*- coding: utf-8 -*-
"""
SwasthAI — Healthpod Operator Hub
============================================================
Central dashboard for authorized Healthpod Operators.

POST-LOGIN FLOW:
  1. Operator logs in via /auth/login (FastAPI backend)
  2. Frontend stores operator session
  3. This hub shows ONLY TWO primary actions:
       1. Register a New Patient
       2. Login an Existing Patient
"""

import sys
import os
from pathlib import Path
import streamlit as st

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Ensure DB tables seeded
from backend.app.db.session import init_db
init_db()

st.set_page_config(
    page_title="Healthpod Operator Hub · SwasthAI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject myAadhaar-inspired theme
from frontend.common import inject_css, init_session, get_current_operator, render_operator_header
inject_css()
init_session()

# Authentication guard
operator = get_current_operator()
if not operator:
    st.warning("Please sign in as a Healthpod Operator to continue.")
    if st.button("Go to Login", type="primary"):
        st.switch_page("pages/01_Login.py")
    st.stop()

# Header banner
render_operator_header("Healthpod Operator Hub", subtitle="SwasthAI — Satnavri Healthpod")

st.markdown(
    f"""
    <div class="card" style="padding:16px 20px;border-left:4px solid var(--primary);margin-bottom:28px;">
        <div style="font-size:16px;font-weight:700;color:#002244;">Welcome, {operator.get('full_name', 'Healthpod Operator')}</div>
        <div style="font-size:13px;color:#5c6b7a;">Authorized Healthpod Operator · Select a patient workflow below to proceed.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# DISPLAY ONLY THE TWO PRIMARY OPTIONS (Part 3 requirement)
st.markdown("<h2 style='color:#002244;font-size:20px;font-weight:700;margin-bottom:6px;'>Primary Actions</h2>", unsafe_allow_html=True)
st.caption("Every Healthpod consultation begins with one of these two actions.")

col_a, col_b = st.columns(2, gap="medium")

with col_a:
    st.markdown(
        """
        <div class="card" style="text-align:center;padding:32px 24px;border:2px solid #0066b3;border-radius:12px;background:#ffffff;box-shadow:0 4px 16px rgba(0,102,179,0.08);">
            <div style="font-size:48px;margin-bottom:12px;">➕</div>
            <h3 style="color:#002244;font-size:20px;font-weight:700;margin:0 0 8px 0;">Register a New Patient</h3>
            <p style="color:#5c6b7a;font-size:13.5px;line-height:1.5;margin:0 0 20px 0;min-height:42px;">
                Enroll a new patient, generate a unique Patient ID, create an initial Consultation ID, and launch the Clinical Encounter Form.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Register a New Patient", key="btn_register_new_patient", type="primary", use_container_width=True):
        st.switch_page("pages/03_Register_Patient.py")

with col_b:
    st.markdown(
        """
        <div class="card" style="text-align:center;padding:32px 24px;border:2px solid #0066b3;border-radius:12px;background:#ffffff;box-shadow:0 4px 16px rgba(0,102,179,0.08);">
            <div style="font-size:48px;margin-bottom:12px;">🔐</div>
            <h3 style="color:#002244;font-size:20px;font-weight:700;margin:0 0 8px 0;">Login an Existing Patient</h3>
            <p style="color:#5c6b7a;font-size:13.5px;line-height:1.5;margin:0 0 20px 0;min-height:42px;">
                Look up an existing patient by mobile number or Patient ID, verify demographics, generate a NEW Consultation ID, and launch the Clinical Encounter Form.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Login an Existing Patient", key="btn_login_existing_patient", type="primary", use_container_width=True):
        st.switch_page("pages/04_Search_Patients.py")

st.markdown(
    """
    <div class="footer" style="margin-top:60px;">
        <p>SwasthAI — Clinical Decision Support System for Satnavari Healthpod Operators.<br/>
        Investigational CDSS tool. Not a substitute for licensed medical judgment.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
