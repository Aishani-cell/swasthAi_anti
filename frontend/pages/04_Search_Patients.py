# -*- coding: utf-8 -*-
"""
SwasthAI — Login an Existing Patient
=====================================
Implements Part 3.B of the Master Specification:
1. Displays a patient search/login field (by Phone number, Patient ID, or Pseudonym).
2. Searches using existing patient identifier and supported fields.
3. Retrieves the correct patient record.
4. Displays sufficient identifying information for operator verification.
5. Creates a NEW Consultation ID for the current visit.
6. Reuses the existing Patient ID (no duplicate patient records created).
7. Associates new consultation with existing patient and authenticated operator.
8. Opens the Clinical Encounter Form directly.
"""

import sys
import os
import uuid
import streamlit as st

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

st.set_page_config(
    page_title="Login Existing Patient · SwasthAI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from frontend.common import inject_css, init_session, get_current_operator, render_operator_header
from backend.app.db.session import get_db_connection
from backend.app.core.privacy import hash_identifier

inject_css()
init_session()

operator = get_current_operator()
if not operator:
    st.warning("Please sign in as a Healthpod Operator to access patient records.")
    if st.button("Go to Login", type="primary"):
        st.switch_page("pages/01_Login.py")
    st.stop()

render_operator_header("Login an Existing Patient", subtitle="SwasthAI — Satnavri Healthpod")

if st.button("← Back to Operator Hub"):
    st.switch_page("app.py")

st.markdown(
    """
    <div class="card" style="max-width:800px;margin:12px auto 24px auto;padding:24px;border-top:4px solid var(--primary);">
        <h2 style="color:#002244;font-size:22px;margin:0 0 4px 0;">🔐 Login an Existing Patient</h2>
        <p style="color:#5c6b7a;font-size:13px;margin:0 0 16px 0;">
            Search for an existing patient by mobile number, Patient ID, or pseudonym.
            Upon selection, a new Consultation ID will be issued for this encounter while preserving previous visit records.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_search_l, col_search_m, col_search_r = st.columns([1, 4, 1])

with col_search_m:
    with st.form("search_existing_patient_form"):
        query = st.text_input(
            "Search by Mobile Number, Patient ID or Pseudonym *",
            placeholder="e.g. 9876543210, pat-001, or SATNAVARI-DEMO",
            help="Enter phone number or patient identifier to retrieve the health record.",
        )
        search_submitted = st.form_submit_button("Search Patient", type="primary", use_container_width=True)

    if search_submitted and query:
        q_clean = query.strip()
        q_hash = hash_identifier(q_clean)
        q_like = f"%{q_clean}%"

        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT id, pseudonym_id, full_name, phone_number, age, sex, is_pregnant, created_at
                   FROM patients
                   WHERE id = ? OR pseudonym_id = ? OR phone_hash = ? OR phone_number = ? OR full_name LIKE ?
                   ORDER BY created_at DESC LIMIT 10;""",
                (q_clean, q_clean, q_hash, q_clean, q_like),
            )
            patients = [dict(r) for r in cur.fetchall()]

        if not patients:
            st.warning(f"No existing patient found matching '{q_clean}'. Please check the input or register as a new patient.")
            if st.button("➕ Register New Patient Instead"):
                st.switch_page("pages/03_Register_Patient.py")
        else:
            st.markdown(f"<h4 style='color:#002244;margin-top:20px;'>Found {len(patients)} matching patient record(s):</h4>", unsafe_allow_html=True)
            
            for p in patients:
                # Count prior consultations
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT COUNT(*) FROM consultations WHERE patient_id = ?;", (p["id"],))
                    prior_visits = cur.fetchone()[0]

                st.markdown(
                    f"""
                    <div class="card" style="padding:18px 22px;border:1px solid #cbd5e1;border-radius:10px;margin-bottom:14px;background:#ffffff;">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                            <div>
                                <div style="font-size:18px;font-weight:700;color:#002244;">{p.get('full_name') or 'Patient (Pseudonymized)'}</div>
                                <div style="font-size:13px;color:#0066b3;font-weight:600;margin:2px 0 6px 0;">Patient ID: <code>{p['id']}</code> · Pseudonym: <code>{p['pseudonym_id']}</code></div>
                                <div style="font-size:13px;color:#5c6b7a;">
                                    <b>Age:</b> {p.get('age', '—')} yrs &nbsp;·&nbsp; 
                                    <b>Sex:</b> {p.get('sex', '—')} &nbsp;·&nbsp; 
                                    <b>Pregnant:</b> {'Yes' if p.get('is_pregnant') else 'No'} &nbsp;·&nbsp; 
                                    <b>Prior Encounters:</b> {prior_visits}
                                </div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                btn_key = f"select_pat_{p['id']}"
                if st.button(f"✅ Select {p.get('full_name') or p['pseudonym_id']} & Start New Consultation", key=btn_key, type="primary", use_container_width=True):
                    # Generate a NEW Consultation ID for this visit
                    new_encounter_id = f"enc-{uuid.uuid4().hex[:10]}"
                    
                    with get_db_connection() as conn:
                        cur = conn.cursor()
                        cur.execute(
                            """INSERT INTO consultations (id, patient_id, operator_id, status)
                               VALUES (?, ?, ?, 'IN_PROGRESS');""",
                            (new_encounter_id, p["id"], operator["id"]),
                        )
                        conn.commit()

                    # Set session state
                    st.session_state["selected_patient_id"] = p["id"]
                    st.session_state["selected_encounter_id"] = new_encounter_id
                    
                    st.success(
                        f"New Consultation {new_encounter_id} created for existing patient {p['id']}. "
                        "Opening Clinical Encounter Form..."
                    )
                    st.switch_page("pages/05_Encounter_Form.py")
