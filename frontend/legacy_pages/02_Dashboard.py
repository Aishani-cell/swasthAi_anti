"""
SwasthAI — Dashboard
====================
Summary cards, recent consultations, system health, and quick actions.
Uses direct SQLite queries via get_db_connection().
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard · SwasthAI", page_icon="📊", layout="wide")

from backend.app.db.session import get_db_connection, init_db

init_db()


# ── Auth gate ───────────────────────────────────────────────────────────────
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
        <h2 style="margin:0;color:#fff;">📊 Dashboard</h2>
        <p style="margin:6px 0 0;opacity:0.9;">
            System overview · Satnavari Primary Healthpod
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Fetch summary stats ────────────────────────────────────────────────────
def _fetch_stats() -> dict:
    with get_db_connection() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM patients;")
        total_patients = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM consultations;")
        total_consults = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM consultations WHERE reviewed_by_clinician = 0 AND status != 'IN_PROGRESS';")
        pending_reviews = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM safety_events;")
        safety_events = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM safety_events WHERE severity = 'CRITICAL';")
        critical_events = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM safety_events WHERE circuit_breaker_halted = 1;")
        cb_halts = cur.fetchone()[0]

        # Recent consultations
        cur.execute(
            """SELECT c.id, c.patient_id, c.encounter_date, c.status,
                      c.primary_hypothesis, c.reviewed_by_clinician
               FROM consultations c
               ORDER BY c.encounter_date DESC LIMIT 20;"""
        )
        recent = [dict(r) for r in cur.fetchall()]

    return {
        "total_patients": total_patients,
        "total_consults": total_consults,
        "pending_reviews": pending_reviews,
        "safety_events": safety_events,
        "critical_events": critical_events,
        "cb_halts": cb_halts,
        "recent_consultations": recent,
    }


stats = _fetch_stats()


# ── Metric cards ────────────────────────────────────────────────────────────
st.markdown("### System Summary")
m1, m2, m3, m4 = st.columns(4)
m1.metric("👥 Total Patients", stats["total_patients"])
m2.metric("📋 Total Consultations", stats["total_consults"])
m3.metric("⏳ Pending Reviews", stats["pending_reviews"])
m4.metric("🛡️ Safety Events", stats["safety_events"])

st.markdown("")
m5, m6, m7, m8 = st.columns(4)
m5.metric("🔴 Critical Events", stats["critical_events"])
m6.metric("⛔ Circuit Breaker Halts", stats["cb_halts"])

# System Health
try:
    with get_db_connection() as conn:
        conn.execute("SELECT 1;")
    db_ok = True
except Exception:
    db_ok = False

m7.metric("💾 Database", "Online ✅" if db_ok else "Offline ❌")

try:
    from backend.app.rag.service import rag_service  # noqa: E402
    rag_ready = True
except Exception:
    rag_ready = False

m8.metric("📚 RAG Engine", "Ready ✅" if rag_ready else "Unavailable ⚠️")


# ── Recent consultations table ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### Recent Consultations")

if stats["recent_consultations"]:
    df = pd.DataFrame(stats["recent_consultations"])
    df.columns = ["Encounter ID", "Patient ID", "Date", "Status", "Primary Hypothesis", "Clinician Reviewed"]
    df["Clinician Reviewed"] = df["Clinician Reviewed"].map({0: "❌ No", 1: "✅ Yes"})

    # Color-code status
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Encounter ID": st.column_config.TextColumn("Encounter ID", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Primary Hypothesis": st.column_config.TextColumn("Primary Dx", width="large"),
        },
    )
else:
    st.info("No consultations recorded yet. Start a new consultation to see data here.")


# ── Quick actions ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Quick Actions")

qa1, qa2, qa3, qa4 = st.columns(4)
with qa1:
    if st.button("📋 New Consultation", use_container_width=True, type="primary"):
        st.switch_page("pages/06_New_Consultation.py")
with qa2:
    if st.button("🆕 Register Patient", use_container_width=True):
        st.switch_page("pages/03_Register_Patient.py")
with qa3:
    if st.button("🔍 Search Patients", use_container_width=True):
        st.switch_page("pages/04_Search_Patients.py")
with qa4:
    if st.button("🛡️ Safety Dashboard", use_container_width=True):
        st.switch_page("pages/07_Safety_Dashboard.py")
