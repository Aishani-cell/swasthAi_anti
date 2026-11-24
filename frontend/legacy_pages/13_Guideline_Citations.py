# -*- coding: utf-8 -*-
"""SwasthAI CDSS – Guideline Citations & RAG Retrieval (Page 13)
Displays retrieved Standard Treatment Guidelines (ICMR, NVBDCP, RSSDI) with section/page attribution.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
from backend.app.rag.vector_store import vector_store
from backend.app.rag.knowledge_base import CLINICAL_GUIDELINE_CORPUS

st.set_page_config(page_title="SwasthAI CDSS – Guideline Citations", page_icon="🏥", layout="wide")

def require_login():
    if "user" not in st.session_state:
        st.session_state["user"] = {"id": "usr-doc-01", "username": "dr.sharma", "full_name": "Dr. Rajesh Sharma, MD", "role": "clinician"}

require_login()

st.title("📚 Clinical Guideline Citations (Local RAG)")
st.caption("Standard Treatment Guidelines from ICMR, MoHFW, NVBDCP, RSSDI, and ICS. Preserves section, page, and exact text citations.")

st.divider()

# Search knowledge base
q = st.text_input("Query Clinical Guidelines", placeholder="e.g. STEMI emergency healthpod management, Dengue thrombocytopenia fluids, Pneumonia antibiotics")
if not q:
    q = "Pneumonia community-acquired treatment"

results = vector_store.query(q, top_k=3)

st.subheader(f"Retrieved Guidelines for: '{q}'")
st.markdown(f"**Retrieval Status**: `{results['retrieval_status']}` | **Distance Threshold (τ)**: `{results['distance_threshold']}`")

if results["chunks"]:
    for idx, chunk in enumerate(results["chunks"], 1):
        with st.expander(f"📖 Citation {idx}: {chunk['doc_title']} ({chunk['publisher']}, {chunk['year']})", expanded=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Condition**: `{chunk['condition']}` | **Section**: `{chunk['section']}` | **Page**: {chunk['page']}")
                st.markdown(f"**Clinical Text**:\n\n> {chunk['full_content']}")
            with col2:
                st.metric("Cosine Similarity", f"{chunk['cosine_similarity']:.4f}")
                st.metric("Distance (1 - sim)", f"{chunk['distance']:.4f}")
else:
    st.warning("No guideline chunks met the cosine distance threshold (tau <= 0.35). Explicit 'unavailable' status returned.")

st.divider()
st.subheader("🏛️ Complete Guideline Corpus (Offline Knowledge Base)")
for g in CLINICAL_GUIDELINE_CORPUS:
    with st.expander(f"📁 {g['doc_title']} — {g['publisher']} ({g['year']})"):
        st.markdown(f"- **Condition**: {g['condition']}")
        st.markdown(f"- **Keywords**: {', '.join(g['keywords'])}")
        st.markdown(f"- **Content**: {g['content_text']}")
