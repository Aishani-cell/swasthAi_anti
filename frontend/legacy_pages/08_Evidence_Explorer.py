"""
SwasthAI — Evidence Explorer
==============================
View the full EvidenceGraph JSON tree for any encounter, verify integrity
hash, and inspect each evidence node.
"""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Evidence Explorer · SwasthAI", page_icon="🔬", layout="wide")

from backend.app.db.session import get_db_connection, init_db

init_db()


def require_login():
    if "user" not in st.session_state:
        st.warning("🔒 Please log in first.")
        st.stop()

require_login()


# ── Header ──────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="background:linear-gradient(135deg,#2C3E50,#34495E);
                padding:24px 32px;border-radius:12px;color:#fff;
                margin-bottom:24px;">
        <h2 style="margin:0;color:#fff;">🔬 Evidence Explorer</h2>
        <p style="margin:6px 0 0;opacity:0.9;">
            EvidenceGraph Viewer · Integrity Verification · Audit Trail
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Load available encounters ───────────────────────────────────────────────
with get_db_connection() as conn:
    cur = conn.cursor()
    cur.execute(
        """SELECT eg.encounter_id, eg.graph_hash, eg.version, eg.is_locked, eg.created_at
           FROM evidence_graphs eg
           ORDER BY eg.created_at DESC
           LIMIT 100;"""
    )
    eg_rows = [dict(r) for r in cur.fetchall()]


if not eg_rows:
    st.info("No EvidenceGraphs recorded yet. Complete a consultation to generate one.")
    st.stop()


# ── Encounter selector ─────────────────────────────────────────────────────
default_enc = st.session_state.get("selected_encounter_id", "")
enc_ids = [r["encounter_id"] for r in eg_rows]

# If a default is set and exists, use it
default_idx = 0
if default_enc and default_enc in enc_ids:
    default_idx = enc_ids.index(default_enc)

selected_enc = st.selectbox(
    "Select Encounter",
    enc_ids,
    index=default_idx,
    help="Choose an encounter to explore its EvidenceGraph.",
)


# ── Load full EvidenceGraph ─────────────────────────────────────────────────
with get_db_connection() as conn:
    cur = conn.cursor()
    cur.execute(
        """SELECT encounter_id, version, graph_hash, graph_json, is_locked, created_at
           FROM evidence_graphs
           WHERE encounter_id = ?;""",
        (selected_enc,),
    )
    eg_row = cur.fetchone()

if not eg_row:
    st.error(f"No EvidenceGraph found for encounter `{selected_enc}`.")
    st.stop()

eg_data = dict(eg_row)
try:
    graph = json.loads(eg_data["graph_json"])
except (json.JSONDecodeError, TypeError):
    graph = {}


# ── Integrity & Metadata ───────────────────────────────────────────────────
st.markdown("### Integrity Verification")

ic1, ic2, ic3, ic4 = st.columns(4)
ic1.metric("Encounter", eg_data["encounter_id"])
ic2.metric("Version", eg_data["version"])
ic3.metric("Locked", "🔒 Yes" if eg_data["is_locked"] else "🔓 No")
ic4.metric("Created", eg_data["created_at"])

stored_hash = eg_data.get("graph_hash", "—")
graph_hash = graph.get("integrity_hash", "—")

st.markdown("#### SHA-256 Integrity Hash")
st.code(f"Stored DB Hash:      {stored_hash}\nEvidenceGraph Hash:  {graph_hash}", language="text")

if stored_hash and graph_hash and stored_hash == graph_hash:
    st.success("✅ **Integrity Verified** — Stored hash matches the EvidenceGraph hash.")
else:
    st.warning("⚠️ Hash mismatch or unavailable — manual audit recommended.")


st.markdown("---")


# ── Node-by-node breakdown ─────────────────────────────────────────────────
st.markdown("### Evidence Nodes")

# Demographics
with st.expander("👤 Demographics"):
    dem = graph.get("demographics", {})
    if dem:
        st.json(dem)
    else:
        st.caption("No demographics data.")

# Vitals
with st.expander("🩺 Vital Signs"):
    vitals = graph.get("vitals", {})
    if vitals:
        st.json(vitals)
    else:
        st.caption("No vitals data.")

# Vitals Classification
with st.expander("📊 Vitals Classification"):
    vc = graph.get("vitals_classification", {})
    if vc:
        st.json(vc)
    else:
        st.caption("No classification data.")

# Symptoms
with st.expander("🤒 Extracted Symptoms"):
    symptoms = graph.get("symptoms", [])
    if symptoms:
        df = pd.DataFrame(symptoms)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No symptoms extracted.")

# Negated Symptoms
with st.expander("🚫 Negated Symptoms"):
    neg = graph.get("negated_symptoms", [])
    if neg:
        df = pd.DataFrame(neg)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No negated symptoms.")

# Resolved Labs
with st.expander("🧪 Resolved Laboratory Values"):
    labs = graph.get("resolved_labs", [])
    if labs:
        df = pd.DataFrame(labs)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No lab results.")

# Imaging
with st.expander("🩻 Imaging Findings"):
    img = graph.get("imaging_findings", [])
    if img:
        st.json(img)
    else:
        st.caption("No imaging data.")

# Respiratory
with st.expander("🫁 Respiratory Acoustic Analysis"):
    resp = graph.get("respiratory_finding")
    if resp:
        st.json(resp)
    else:
        st.caption("No respiratory audio data.")

# Safety Alerts
with st.expander("🛡️ Safety Alerts"):
    alerts = graph.get("safety_alerts", [])
    if alerts:
        for a in alerts:
            sev = a.get("severity", "INFO")
            if sev == "CRITICAL":
                st.error(f"🔴 `{a.get('rule_id', '?')}` — {a.get('observed_value', '?')}")
            elif sev == "WARNING":
                st.warning(f"🟡 `{a.get('rule_id', '?')}` — {a.get('observed_value', '?')}")
            else:
                st.info(f"ℹ️ `{a.get('rule_id', '?')}` — {a.get('observed_value', '?')}")
        st.json(alerts)
    else:
        st.caption("No safety alerts.")

# Missing Modalities
with st.expander("❓ Missing Modalities"):
    mm = graph.get("missing_modalities", [])
    if mm:
        for m in mm:
            st.markdown(f"- ⚠️ {m}")
    else:
        st.success("All modalities were provided.")

# Circuit Breaker
with st.expander("⛔ Circuit Breaker Status"):
    cb = graph.get("circuit_breaker_tripped", False)
    if cb:
        st.error("⛔ **Circuit breaker was TRIPPED** for this encounter.")
    else:
        st.success("✅ Circuit breaker was NOT tripped.")


st.markdown("---")


# ── Full JSON tree ──────────────────────────────────────────────────────────
st.markdown("### Full EvidenceGraph JSON")

with st.expander("📜 View Raw JSON", expanded=False):
    st.json(graph)

# Download
json_str = json.dumps(graph, indent=2, ensure_ascii=False)
st.download_button(
    "📥 Download EvidenceGraph JSON",
    data=json_str,
    file_name=f"evidence_graph_{selected_enc}.json",
    mime="application/json",
    use_container_width=True,
)
