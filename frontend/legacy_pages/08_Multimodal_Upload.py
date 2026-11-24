# -*- coding: utf-8 -*-
"""SwasthAI CDSS – Multimodal Evidence Upload (Page 08)
Supports uploading and staging heterogeneous clinical modalities:
Vitals streams, lab reports, digitized acoustic WAV files, and radiology metadata.
"""
import sys, os, uuid, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
from backend.app.core.config import settings

st.set_page_config(page_title="SwasthAI CDSS – Multimodal Upload", page_icon="🏥", layout="wide")

def require_login():
    if "user" not in st.session_state:
        st.session_state["user"] = {"id": "usr-doc-01", "username": "dr.sharma", "full_name": "Dr. Rajesh Sharma, MD", "role": "clinician"}

require_login()

st.title("📤 Multimodal Clinical Evidence Ingestion")
st.caption("Upload structured or unstructured multimodal diagnostic data for ingestion into the SwasthAI Evidence Pipeline.")

st.divider()

UPLOAD_DIR = pathlib.Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

tab1, tab2, tab3 = st.columns(3)

with tab1:
    st.markdown("### 🧪 Lab Report Ingestion")
    st.caption("Structured text or semi-structured reports")
    lab_text = st.text_area("Paste Lab Report Text", height=150, placeholder="Hemoglobin: 12.4 g/dL\nWBC: 8400 /cumm\nPlatelet Count: 210000 /cumm\nSerum Creatinine: 0.9 mg/dL")
    if st.button("Parse Laboratory Text", use_container_width=True):
        if lab_text:
            st.session_state["staged_lab_text"] = lab_text
            st.success("Staged lab text for extraction review.")
            st.switch_page("pages/09_Extraction_Review.py")

with tab2:
    st.markdown("### 🫁 Respiratory Audio")
    st.caption("Stethoscope lung recordings (WAV format)")
    audio_file = st.file_uploader("Upload Lung Sound Recording", type=["wav"])
    if audio_file:
        saved_path = UPLOAD_DIR / f"resp_{uuid.uuid4().hex[:8]}.wav"
        saved_path.write_bytes(audio_file.getvalue())
        st.success(f"Saved audio: `{saved_path.name}`")
        if st.button("Analyze Respiratory Sound", use_container_width=True):
            st.switch_page("pages/10_Respiratory_Audio.py")

with tab3:
    st.markdown("### 🩻 Radiology Metadata")
    st.caption("DICOM header / radiologist observation")
    rad_text = st.text_area("Paste Radiology Observation", height=150, placeholder="CXR PA View: Increased bronchovascular markings with patchy alveolar opacities in right middle lobe.")
    if st.button("Stage Radiology Finding", use_container_width=True):
        if rad_text:
            st.session_state["staged_rad_text"] = rad_text
            st.success("Staged radiology findings.")
            st.switch_page("pages/11_Radiology.py")
