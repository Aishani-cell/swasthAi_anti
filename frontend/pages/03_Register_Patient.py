# -*- coding: utf-8 -*-
"""
SwasthAI — Register a New Patient
==================================
Implements Part 3.A of the Master Specification:
1. Displays the patient registration form.
2. Collects fields required by existing patient schema (Full Name, Phone, Age, Sex, Pregnancy, DOB).
3. Validates required fields (valid 10-digit Indian phone number, age).
4. Creates new patient record with unique Patient ID (pat-xxxx).
5. Creates a new consultation record with unique Consultation ID (enc-xxxx).
6. Establishes the correct patient-consultation relationship.
7. Associates consultation with the authenticated Healthpod Operator.
8. Opens the Clinical Encounter Form directly.
"""

import sys
import os
import streamlit as st

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

st.set_page_config(
    page_title="Register Patient · SwasthAI",
    page_icon="➕",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from frontend.common import inject_css, init_session, get_current_operator, render_operator_header
from backend.app.ehr.patient_service import patient_ehr_service
from backend.app.schemas.patient import PatientCreate

inject_css()
init_session()

operator = get_current_operator()
if not operator:
    st.warning("Please sign in as a Healthpod Operator to register a patient.")
    if st.button("Go to Login", type="primary"):
        st.switch_page("pages/01_Login.py")
    st.stop()

render_operator_header("Register a New Patient", subtitle="SwasthAI — Satnavri Healthpod")

# Back button to Hub
if st.button("← Back to Operator Hub"):
    st.switch_page("app.py")

st.markdown(
    """
    <div class="card" style="max-width:760px;margin:12px auto 24px auto;padding:24px;border-top:4px solid var(--primary);">
        <h2 style="color:#002244;font-size:22px;margin:0 0 4px 0;">➕ Register a New Patient</h2>
        <p style="color:#5c6b7a;font-size:13px;margin:0 0 16px 0;">
            Enroll a new patient into the Satnavari Healthpod registry. A new Consultation ID will be generated automatically.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Form container
form_col_left, form_col_center, form_col_right = st.columns([1, 4, 1])

with form_col_center:
    with st.form("patient_registration_form", clear_on_submit=False):
        st.markdown("<h4 style='color:#002244;margin-bottom:12px;'>Patient Demographics</h4>", unsafe_allow_html=True)
        
        full_name = st.text_input(
            "Full Name *",
            placeholder="e.g. Bushra Ameen",
            help="Enter patient's legal full name.",
        )
        
        phone_number = st.text_input(
            "Mobile Number (10 digits) *",
            placeholder="e.g. 9876543210",
            max_chars=14,
            help="10-digit Indian phone number. Stored as SHA-256 hash for privacy preservation.",
        )
        
        c_age, c_sex = st.columns(2)
        with c_age:
            age = st.number_input(
                "Age (Years) *",
                min_value=0,
                max_value=125,
                value=25,
                step=1,
            )
        with c_sex:
            sex = st.selectbox(
                "Biological Sex *",
                options=["FEMALE", "MALE", "OTHER"],
                index=0,
            )
            
        c_dob, c_preg = st.columns(2)
        with c_dob:
            dob = st.text_input(
                "Date of Birth (YYYY-MM-DD, optional)",
                placeholder="e.g. 2001-05-14",
            )
        with c_preg:
            is_pregnant = False
            if sex == "FEMALE":
                is_pregnant = st.checkbox("Currently Pregnant", value=False)

        email = st.text_input(
            "Email Address (optional)",
            placeholder="e.g. patient@example.com",
        )

        st.markdown(
            """
            <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:10px 14px;font-size:12px;color:#1e40af;margin:14px 0;">
                ℹ️ <b>Privacy Guarantee</b>: Direct patient identifiers (phone, Aadhaar) are stored exclusively as one-way SHA-256 hashes.
                The clinical reasoning engine operates only on de-identified pseudonyms.
            </div>
            """,
            unsafe_allow_html=True,
        )

        submit_btn = st.form_submit_button(
            "Register Patient & Open Encounter Form",
            type="primary",
            use_container_width=True,
        )

    if submit_btn:
        name_clean = (full_name or "").strip()
        phone_clean = (phone_number or "").strip().replace(" ", "").replace("-", "")
        
        # Validation
        if not name_clean:
            st.error("Please enter the patient's full name.")
        elif not phone_clean or len(phone_clean) < 10 or not phone_clean.isdigit():
            st.error("Please enter a valid 10-digit mobile number.")
        elif age is None or age < 0:
            st.error("Please enter a valid age.")
        else:
            try:
                patient_in = PatientCreate(
                    phone_number=phone_clean,
                    full_name=name_clean,
                    age=int(age),
                    sex=sex,
                    is_pregnant=bool(is_pregnant),
                    email=email.strip() if email else None,
                    dob=dob.strip() if dob else None,
                )
                
                # Atomically register patient and create new consultation record
                result = patient_ehr_service.register_patient_and_start_consultation(
                    patient_in=patient_in,
                    operator_id=operator["id"],
                )
                
                patient_rec = result["patient"]
                encounter_id = result["encounter_id"]
                
                # Set session state for the active encounter
                st.session_state["selected_patient_id"] = patient_rec["id"]
                st.session_state["selected_encounter_id"] = encounter_id
                
                st.success(
                    f"✅ Patient registered: {patient_rec.get('full_name')} (ID: {patient_rec['id']}). "
                    f"New Consultation created: {encounter_id}."
                )
                
                # Redirect directly to Clinical Encounter Form
                st.switch_page("pages/05_Encounter_Form.py")
                
            except ValueError as ve:
                st.error(f"Registration note: {ve}")
            except Exception as e:
                st.error(f"Failed to register patient: {e}")
