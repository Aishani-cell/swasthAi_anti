# -*- coding: utf-8 -*-
"""SwasthAI CDSS – Respiratory Model Training (Page 18)
Trains the lightweight 4-class Compact Respiratory CRNN model (ICBHI protocol).
"""
import sys, os, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
from ml.respiratory.training.train import train_respiratory_model

st.set_page_config(page_title="SwasthAI CDSS – Model Training", page_icon="🏥", layout="wide")

def require_login():
    if "user" not in st.session_state:
        st.session_state["user"] = {"id": "usr-doc-01", "username": "dr.sharma", "full_name": "Dr. Rajesh Sharma, MD", "role": "clinician"}

require_login()

st.title("🧠 Respiratory Acoustic Model Training")
st.caption("RespLLM training. ICBHI 2017 is used when installed. Otherwise this page can run a labeled synthetic smoke test only.")

st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Training Parameters")
    epochs = st.slider("Number of Epochs", min_value=1, max_value=20, value=3)
    lr = st.select_slider("Learning Rate", options=[0.0001, 0.0005, 0.001, 0.005, 0.01], value=0.001)
    smoke_test = st.checkbox("Synthetic smoke test (not ICBHI)", value=True)

    if st.button("🚀 Start Training Run", type="primary", use_container_width=True):
        with st.spinner("Training RespLLM on one device at a time..."):
            res = train_respiratory_model(epochs=epochs, lr=lr, smoke_test=smoke_test)
            st.success("✅ Training completed successfully!")
            st.json(res)

with col2:
    st.markdown("### Architecture & Checkpoint Status")
    ckpt_path = pathlib.Path("./ml/respiratory/checkpoints/best_respllm.pt")
    if ckpt_path.exists():
        st.success(f"✅ Checkpoint found: `{ckpt_path.name}` ({ckpt_path.stat().st_size / 1024:.1f} KB)")
    else:
        st.warning("No saved model checkpoint found. Run a training session to generate weights.")

    st.markdown("#### Hardware Adaptation")
    st.markdown("- **Architecture**: RespLLM CNN–BiGRU, 768-d embedding, 4-class head, closed-vocabulary decoder")
    st.markdown("- **Spectrogram**: 64 Mel Bins, 16 kHz sampling, 5.0s window")
    st.markdown("- **Device Strategy**: Single-model active memory management (prevents VRAM spill)")
