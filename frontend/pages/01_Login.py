# -*- coding: utf-8 -*-
"""
SwasthAI — Healthpod Operator Authentication
=============================================
Two-panel login page layout matching Screenshot 1 and the myAadhaar visual theme.
Collectively presents all authorized operators as "Healthpod Operator".
Authenticates against the FastAPI backend /auth/login and /auth/register.
"""

import sys
import os
from pathlib import Path
import streamlit as st

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

st.set_page_config(
    page_title="Healthpod Operator Login · SwasthAI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from frontend.common import inject_css, init_session
from backend.app.db.session import init_db, get_db_connection
from backend.app.core.security import verify_password, create_access_token, hash_password
import uuid

# Ensure database tables initialized
init_db()
inject_css()
init_session()

# If operator already logged in, provide direct access to the Hub
if st.session_state.get("operator_user"):
    op = st.session_state["operator_user"]
    st.markdown(
        f"""
        <div class="card" style="max-width:650px;margin:40px auto;text-align:center;padding:32px;">
            <div style="font-size:48px;margin-bottom:12px;">✅</div>
            <h3 style="color:#002244;margin-bottom:6px;">Already Signed In</h3>
            <p style="color:#5c6b7a;">Signed in as <b>{op.get('full_name', 'Healthpod Operator')}</b> ({op.get('username', '')})</p>
            <p style="color:#0066b3;font-weight:600;font-size:13px;">Role: Healthpod Operator</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📋 Open Healthpod Operator Hub", use_container_width=True, type="primary"):
            st.switch_page("app.py")
    with col2:
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state["operator_user"] = None
            st.session_state["selected_patient_id"] = None
            st.session_state["selected_encounter_id"] = None
            st.rerun()
    st.stop()

# Mode selection: Login or Register
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"

# Custom container styling matching Screenshot 1
st.markdown(
    """
    <style>
    /* Hide default streamlit header/footer on login */
    header { visibility: hidden; }
    footer { visibility: hidden; }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1040px;
    }
    .panel-left-container {
        background: linear-gradient(150deg, #022038 0%, #003666 50%, #0066b3 100%);
        border-radius: 16px 0 0 16px;
        padding: 48px 36px;
        color: #ffffff;
        min-height: 520px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
        overflow: hidden;
    }
    .panel-left-container::after {
        content: "";
        position: absolute;
        top: -50px;
        right: -50px;
        width: 200px;
        height: 200px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    .panel-right-container {
        background: #ffffff;
        border-radius: 0 16px 16px 0;
        padding: 40px 36px;
        min-height: 520px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.06);
        border: 1px solid #e2e8f0;
        border-left: none;
    }
    @media (max-width: 768px) {
        .panel-left-container { border-radius: 16px 16px 0 0; min-height: auto; }
        .panel-right-container { border-radius: 0 0 16px 16px; border-left: 1px solid #e2e8f0; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

left_col, right_col = st.columns([1.1, 1], gap="small")

with left_col:
    st.markdown(
        """
        <div class="panel-left-container">
            <div>
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:28px;">
                    <div style="background:#ffffff;color:#0066b3;font-size:22px;font-weight:900;width:38px;height:38px;border-radius:8px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.2);">🏥</div>
                    <div>
                        <div style="font-size:11px;letter-spacing:1px;font-weight:700;color:#93c5fd;text-transform:uppercase;">RURAL HEALTHPOD INITIATIVE</div>
                        <div style="font-size:12px;font-weight:600;color:#e2e8f0;">ITU-T Y.4218 · SATNAVARI VILLAGE</div>
                    </div>
                </div>
                
                <h1 style="color:#ffffff !important;font-size:30px;font-weight:800;line-height:1.2;margin:0 0 10px 0;">SwasthAI</h1>
                <h3 style="color:#60a5fa !important;font-size:14px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;margin:0 0 20px 0;">Satnavri Healthpod AI Assistant</h3>
                
                <p style="color:#cbd5e1;font-size:13.5px;line-height:1.65;margin:0 0 24px 0;">
                    Hardware-optimized, offline-capable, multimodal Clinical Decision Support System (CDSS) with independent deterministic emergency circuit breakers, bilingual symptom extraction, and guideline-directed drug recommendations.
                </p>
            </div>
            
            <div style="border-top:1px solid rgba(255,255,255,0.15);padding-top:18px;">
                <div style="display:flex;align-items:center;gap:12px;font-size:12px;color:#94a3b8;">
                    <span>🔒 Privacy Preserved (Zero Plaintext PHI)</span>
                    <span>·</span>
                    <span>⚡ Offline Guaranteed</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right_col:
    st.markdown(
        """
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div style="font-size:12px;font-weight:700;color:#0066b3;letter-spacing:0.5px;">HEALTHPOD ACCESS</div>
            <div style="font-size:14px;color:#64748b;">🌙 &nbsp; 🌐</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state["auth_mode"] == "login":
        st.markdown(
            """
            <h2 style="color:#002244;font-size:24px;font-weight:700;margin:0 0 4px 0;">Login</h2>
            <p style="color:#64748b;font-size:13px;margin:0 0 20px 0;">Welcome back! Sign in to your Healthpod Operator account</p>
            """,
            unsafe_allow_html=True,
        )

        with st.form("operator_login_form"):
            username = st.text_input(
                "Mobile Number / Username",
                placeholder="e.g. tech.rahul or dr.sharma",
                help="Enter your registered operator username or mobile identifier.",
            )
            password = st.text_input(
                "Enter MPIN / Password",
                type="password",
                placeholder="••••••••",
                help="Enter your operator security password or MPIN.",
            )
            
            col_remember, col_forgot = st.columns([1, 1])
            with col_forgot:
                st.markdown(
                    '<div style="text-align:right;font-size:12px;color:#0066b3;padding-top:4px;">Authorized Personnel Only</div>',
                    unsafe_allow_html=True,
                )

            submit_login = st.form_submit_button(
                "Login as Healthpod Operator",
                use_container_width=True,
                type="primary",
            )

        if submit_login:
            u_clean = (username or "").strip()
            p_clean = password or ""
            if not u_clean or not p_clean:
                st.error("Please enter both username and password.")
            else:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id, username, hashed_password, full_name, role FROM users WHERE username = ?;",
                        (u_clean,),
                    )
                    user = cursor.fetchone()

                if not user or not verify_password(p_clean, user["hashed_password"]):
                    st.error("Invalid username or password. Please try again.")
                else:
                    token = create_access_token({
                        "sub": user["id"],
                        "username": user["username"],
                        "role": user["role"],
                        "full_name": user["full_name"],
                    })
                    # Set session state
                    st.session_state["operator_user"] = {
                        "id": user["id"],
                        "username": user["username"],
                        "full_name": user["full_name"],
                        "role": user["role"],
                        "token": token,
                    }
                    st.success(f"Welcome back, {user['full_name']}! Redirecting to Hub...")
                    st.switch_page("app.py")

        st.markdown("<hr style='margin:20px 0;border:none;border-top:1px solid #e2e8f0;'/>", unsafe_allow_html=True)
        if st.button("New Healthpod Operator? Register here", use_container_width=True):
            st.session_state["auth_mode"] = "register"
            st.rerun()

    else:
        # REGISTRATION MODE
        st.markdown(
            """
            <h2 style="color:#002244;font-size:24px;font-weight:700;margin:0 0 4px 0;">Register Operator</h2>
            <p style="color:#64748b;font-size:13px;margin:0 0 20px 0;">Create a new Healthpod Operator credential</p>
            """,
            unsafe_allow_html=True,
        )

        with st.form("operator_register_form"):
            new_fullname = st.text_input("Full Name *", placeholder="e.g. Ramesh Kumar")
            new_username = st.text_input("Username / Operator ID *", placeholder="e.g. op.ramesh")
            new_password = st.text_input("Password (min 6 chars) *", type="password", placeholder="••••••••")
            
            submit_reg = st.form_submit_button(
                "Register as Healthpod Operator",
                use_container_width=True,
                type="primary",
            )

        if submit_reg:
            fn = (new_fullname or "").strip()
            un = (new_username or "").strip()
            pw = new_password or ""
            if not fn or not un or len(pw) < 6:
                st.error("Full name, username, and password (at least 6 characters) are required.")
            else:
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM users WHERE username = ?;", (un,))
                    if cur.fetchone():
                        st.error("An operator with this username already exists.")
                    else:
                        op_id = f"usr-op-{uuid.uuid4().hex[:8]}"
                        cur.execute(
                            "INSERT INTO users (id, username, hashed_password, full_name, role) VALUES (?, ?, ?, ?, 'technician');",
                            (op_id, un, hash_password(pw), fn),
                        )
                        conn.commit()

                        token = create_access_token({
                            "sub": op_id,
                            "username": un,
                            "role": "technician",
                            "full_name": fn,
                        })
                        st.session_state["operator_user"] = {
                            "id": op_id,
                            "username": un,
                            "full_name": fn,
                            "role": "technician",
                            "token": token,
                        }
                        st.success("Operator registered successfully! Opening Hub...")
                        st.switch_page("app.py")

        st.markdown("<hr style='margin:20px 0;border:none;border-top:1px solid #e2e8f0;'/>", unsafe_allow_html=True)
        if st.button("Already have an account? Sign in", use_container_width=True):
            st.session_state["auth_mode"] = "login"
            st.rerun()
