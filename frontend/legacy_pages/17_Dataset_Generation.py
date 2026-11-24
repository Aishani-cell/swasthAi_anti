# -*- coding: utf-8 -*-
"""SwasthAI CDSS – Dataset Generation & Validation Dashboard (Page 17)
Generate, validate, and inspect the 500-record synthetic clinical encounter dataset
partitioned into 350 train / 75 val / 75 test across 25 diagnostic conditions.
"""
import sys, os, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
import pandas as pd
from scripts.validate_dataset import validate_dataset
from scripts.generate_report_dataset import generate_report_dataset

st.set_page_config(page_title="SwasthAI CDSS – Dataset Operations", page_icon="🏥", layout="wide")

def require_login():
    if "user" not in st.session_state:
        st.session_state["user"] = {"id": "usr-doc-01", "username": "dr.sharma", "full_name": "Dr. Rajesh Sharma, MD", "role": "clinician"}

require_login()

st.title("🧬 Dataset Management & Generation Dashboard")
st.caption("Manage synthetic multimodal clinical encounter records matching the research paper's specifications.")

st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("⚡ Generate New Synthetic Encounters")
    st.caption("Covers 25 diagnostic categories, multilingual symptoms, LOINC lab panels, and vitals.")
    target_n = st.slider("Target Record Count", min_value=25, max_value=500, value=100, step=25)
    seed_val = st.number_input("Random Seed", min_value=1, max_value=9999, value=42)
    
    if st.button("🚀 Generate Synthetic Dataset", type="primary"):
        with st.spinner(f"Generating {target_n} clinical encounters..."):
            stats = generate_report_dataset(target_count=target_n, seed=seed_val)
            st.success(f"Generated {stats['total_records']} encounters successfully!")
            st.json(stats["splits"])

with col2:
    st.subheader("🔍 Validate Existing Dataset")
    data_file = pathlib.Path("./data/generated/encounters.jsonl")
    if data_file.exists():
        st.markdown(f"**Found File**: `{data_file.resolve()}`")
        if st.button("Run Schema & Clinical Validation", type="secondary"):
            val_res = validate_dataset(str(data_file))
            if val_res.get("is_valid"):
                st.success("✅ **Dataset is Fully Valid and Schema Compliant!**")
                colA, colB, colC = st.columns(3)
                colA.metric("Total Records", val_res["total_records"])
                colB.metric("Unique Conditions", len(val_res["condition_counts"]))
                colC.metric("Status", "VALID")
                
                st.markdown("#### Condition Distribution")
                st.bar_chart(val_res["condition_counts"])
            else:
                st.error("Dataset validation failed!")
                st.json(val_res.get("errors", []))
    else:
        st.warning("No generated dataset found at `data/generated/encounters.jsonl`.")
