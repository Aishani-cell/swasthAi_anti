# -*- coding: utf-8 -*-
"""SwasthAI CDSS – EvidenceGraph Explorer (Page 11)
Interactive exploration of the canonical, immutable EvidenceGraph (Section 3.7):
- Structured nodes (demographics, symptoms, vitals, labs, imaging, audio, alerts)
- Cryptographic SHA-256 integrity digest verification
- Clean prompt-text serialization view
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
from backend.app.db.session import get_db_connection
from backend.app.evidence.serializer import serialize_evidence_graph, compute_graph_hash

st.set_page_config(page_title="SwasthAI CDSS – EvidenceGraph Explorer", page_icon="🏥", layout="wide")

def require_login():
    if "user" not in st.session_state:
        st.session_state["user"] = {"id": "usr-doc-01", "username": "dr.sharma", "full_name": "Dr. Rajesh Sharma, MD", "role": "clinician"}

require_login()

st.title("🕸️ Verified EvidenceGraph Explorer")
st.caption("Immutable, cryptographic patient state representation grounding all multi-agent CDSS decisions.")

st.divider()

with get_db_connection() as conn:
    c = conn.cursor()
    c.execute("""
        SELECT e.encounter_id, p.pseudonym_id, c.primary_hypothesis, e.graph_hash, e.graph_json
        FROM evidence_graphs e
        JOIN consultations c ON e.encounter_id = c.id
        JOIN patients p ON c.patient_id = p.id
        ORDER BY e.created_at DESC LIMIT 50;
    """)
    graphs = c.fetchall()

if not graphs:
    st.info("No EvidenceGraphs recorded yet. Start a consultation via '07_New_Consultation'.")
    st.stop()

cur_enc_id = st.session_state.get("selected_encounter_id") or graphs[0]["encounter_id"]
graph_options = {g["encounter_id"]: f"{g['encounter_id']} | {g['pseudonym_id']} — {g['primary_hypothesis']}" for g in graphs}
selected_enc = st.selectbox(
    "Select EvidenceGraph Record",
    options=list(graph_options.keys()),
    index=list(graph_options.keys()).index(cur_enc_id) if cur_enc_id in graph_options else 0,
    format_func=lambda x: graph_options[x]
)

target_graph = next(g for g in graphs if g["encounter_id"] == selected_enc)
graph_data = json.loads(target_graph["graph_json"])
stored_hash = target_graph["graph_hash"]

# Recompute SHA-256 to verify integrity
serialized = serialize_evidence_graph(graph_data)
recomputed_hash = compute_graph_hash(serialized)
is_intact = (stored_hash == recomputed_hash)

colA, colB = st.columns([2, 1])
with colA:
    if is_intact:
        st.success(f"🔒 **Cryptographic Hash Verified**: `{stored_hash}`")
    else:
        st.error(f"❌ **Integrity Checksum Mismatch!** Tampering detected.")

with colB:
    st.metric("Graph Schema Version", graph_data.get("version", 1))

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🌳 Node Tree View", "📝 Raw JSON State", "🤖 Prompt-Formatted Text"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 1. Coarse Demographics")
        st.json(graph_data.get("demographics", {}))
        
        st.markdown("#### 2. Extracted Symptoms")
        st.json(graph_data.get("symptoms", []))
        
        st.markdown("#### 3. Vital Signs & Triage")
        st.json({
            "vitals": graph_data.get("vitals"),
            "classifications": graph_data.get("vitals_classification")
        })

    with col2:
        st.markdown("#### 4. Resolved Laboratories (LOINC)")
        st.json(graph_data.get("resolved_labs", []))

        st.markdown("#### 5. Safety Alerts & Circuit Breaker")
        st.json({
            "circuit_breaker_tripped": graph_data.get("circuit_breaker_tripped"),
            "safety_alerts": graph_data.get("safety_alerts")
        })

        st.markdown("#### 6. Missing Modalities")
        st.json(graph_data.get("missing_modalities", []))

with tab2:
    st.json(graph_data)

with tab3:
    from backend.app.schemas.evidence import EvidenceGraphModel
    from backend.app.evidence.builder import format_evidence_graph_text
    try:
        eg_model = EvidenceGraphModel(**graph_data)
        txt = format_evidence_graph_text(eg_model)
        st.code(txt, language="markdown")
    except Exception as e:
        st.warning(f"Could not render prompt format: {e}")
