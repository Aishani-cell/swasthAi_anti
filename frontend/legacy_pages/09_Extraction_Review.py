# -*- coding: utf-8 -*-
"""SwasthAI CDSS – Extraction & LOINC Resolution Review (Page 09)
Interactive review of bilingual symptom extraction and deterministic LOINC laboratory resolution.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
import pandas as pd
from backend.app.agents.symptom_agent.service import symptom_service
from backend.app.agents.lab_agent.service import lab_agent_service
from backend.app.agents.lab_resolver.resolver_service import lab_resolver_service

st.set_page_config(page_title="SwasthAI CDSS – Extraction Review", page_icon="🏥", layout="wide")

def require_login():
    if "user" not in st.session_state:
        st.session_state["user"] = {"id": "usr-doc-01", "username": "dr.sharma", "full_name": "Dr. Rajesh Sharma, MD", "role": "clinician"}

require_login()

st.title("🔬 Clinical Extraction & LOINC Resolution Review")
st.caption("Inspect bilingual symptom concept mappings (Ratcliff-Obershelp tau=0.90) and standardized LOINC laboratory unit conversions.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("🗣️ Symptom NLP Agent")
    sample_sym = st.text_area("Enter Symptoms to Test Extraction", value="सीने में तेज दर्द, पसीना आना और सांस लेने में दिक्कत, no fever", height=100)
    if st.button("Extract Symptoms", type="primary"):
        summary = symptom_service.process_symptoms(sample_sym)
        st.markdown(f"**Canonical Summary**: {summary.summary_text}")
        
        if summary.extracted_symptoms:
            st.markdown("#### Positive Symptoms")
            df_pos = pd.DataFrame([{
                "Canonical Concept": s.canonical_concept,
                "Original Phrase": s.original_phrase,
                "Language": s.language,
                "Method": s.extraction_method,
                "Confidence": f"{s.confidence_score:.2f}"
            } for s in summary.extracted_symptoms])
            st.dataframe(df_pos, use_container_width=True)

        if summary.negated_symptoms:
            st.markdown("#### Negated Symptoms (20-Char Boundary)")
            df_neg = pd.DataFrame([{
                "Concept": s.canonical_concept,
                "Phrase": s.original_phrase,
                "Negated": "Yes"
            } for s in summary.negated_symptoms])
            st.dataframe(df_neg, use_container_width=True)

with col2:
    st.subheader("🧪 Laboratory LOINC Resolver")
    sample_lab = st.text_area(
        "Enter Raw Lab Report",
        value=st.session_state.get("staged_lab_text", "Platelet Count: 42,000 /cumm\nHb: 13.5 g/dL\nSerum Creatinine: 1.8 mg/dL\nPotassium: 6.8 mEq/L"),
        height=100
    )
    if st.button("Parse & Resolve with LOINC", type="primary"):
        extracted = lab_agent_service.parse_text_report(sample_lab)
        resolved = lab_resolver_service.resolve_items(extracted)
        
        if resolved:
            df_res = pd.DataFrame([{
                "Analyte": r.canonical_name,
                "LOINC": r.loinc_code or "N/A",
                "Normalized Value": f"{r.numeric_value} {r.canonical_unit}",
                "Status": r.verification_status,
                "Plausibility Flag": r.plausibility_flag or "NORMAL",
                "Reference Interval": r.reference_interval or "N/A"
            } for r in resolved])
            st.dataframe(df_res, use_container_width=True)
            
            # Check for critical flags
            crit = [r for r in resolved if r.plausibility_flag in ["CRITICAL_HIGH", "CRITICAL_LOW"]]
            if crit:
                st.error(f"🚨 **{len(crit)} Critical Panic Laboratory Values Detected!** Will trigger Emergency Circuit Breaker.")
        else:
            st.warning("No recognizable laboratory analytes matched.")
