# -*- coding: utf-8 -*-
"""
SwasthAI Frontend Shared Utilities & Navigation
Healthpod Operator mode. Authentication, session management, theming helpers.
"""
import sys
from pathlib import Path
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.core.config import settings
from backend.app.db.session import get_db_connection

_CSS_PATH = REPO_ROOT / "frontend" / "assets" / "style.css"
CSS = _CSS_PATH.read_text(encoding="utf-8") if _CSS_PATH.exists() else ""

def inject_css():
    if CSS:
        st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
    st.markdown(
        '<style>.css-1d391kg, .css-10trblm, .stApp, .stVerticalBlock { font-family: "Segoe UI", "Roboto", "Inter", sans-serif; }</style>',
        unsafe_allow_html=True,
    )
    # Global JS helper for programmatic page navigation
    st.markdown(
        '<script>'
        'window.changePage = function(page) { window.location.href = page; };'
        '</script>',
        unsafe_allow_html=True,
    )

def init_session():
    if "operator_user" not in st.session_state:
        st.session_state["operator_user"] = None
    if "selected_patient_id" not in st.session_state:
        st.session_state["selected_patient_id"] = None
    if "selected_encounter_id" not in st.session_state:
        st.session_state["selected_encounter_id"] = None
    if "encounter_step" not in st.session_state:
        st.session_state["encounter_step"] = 0

def get_current_operator():
    init_session()
    return st.session_state.get("operator_user")

def get_current_patient():
    init_session()
    pid = st.session_state.get("selected_patient_id")
    if not pid:
        return None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, pseudonym_id, full_name, phone_number, email, dob, age, sex, is_pregnant FROM patients WHERE id = ?;",
            (pid,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0], "pseudonym_id": row[1], "full_name": row[2],
            "phone_number": row[3], "email": row[4], "dob": row[5],
            "age": row[6], "sex": row[7], "is_pregnant": bool(row[8]),
        }

def require_operator_auth(redirect="pages/01_Login.py"):
    init_session()
    if not st.session_state.get("operator_user"):
        st.warning("Please log in to access the SwasthAI Healthpod portal.")
        st.info("Authorized Healthpod Operators only.")
        if st.button("Go to Login", type="primary"):
            st.switch_page(redirect)
        st.stop()
    return st.session_state["operator_user"]

def render_operator_header(title, subtitle=None):
    init_session()
    user = st.session_state.get("operator_user", {})
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            '<div class="top-banner"><h1>SwasthAI &#10003; Satnavri Healthpod</h1>'
            '<p>Clinical Decision Support &#183; Authorized Healthpod Operator</p></div>',
            unsafe_allow_html=True,
        )
    with col2:
        name = user.get("full_name", "Healthpod Operator")
        st.markdown(
            f'<div style="text-align:right;padding:12px;border-radius:8px;background:rgba(0,102,179,0.1);">'
            f'<span style="font-size:0.8em;color:#5c6b7a;">Role: Healthpod Operator</span><br/>'
            f'<b>{name}</b><br/>'
            f'<span style="font-size:0.75em;background:#0066b3;color:#ffffff;padding:2px 8px;border-radius:4px;font-weight:600;">ACTIVE SESSION</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.divider()

def read_file_with_progress(uploaded_files):
    data = {}
    for f in uploaded_files:
        data[f.filename] = f.getvalue()
    return data
