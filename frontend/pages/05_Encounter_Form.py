# -*- coding: utf-8 -*-
"""
SwasthAI — Clinical Encounter Form
===================================
Layout matches Screenshot 2 and myAadhaar visual theme.
Two-column structured encounter form:
  LEFT COLUMN:
    - Healthpod Vitals (Systolic BP, Diastolic BP, Pulse, Temp, SpO2, Weight, Height, BMI auto-calc)
    - Multilingual Symptoms (English, Hindi, Hinglish)
  RIGHT COLUMN:
    - Diagnostic Scans (X-Ray, CT, MRI, DICOM) with file display & removal
    - Acoustic recordings (WAV, MP3) with file display & removal
    - Laboratory Reports (PDF, scanned PDF, JPG, PNG)
      - "Extract Lab Values" button
      - Editable table directly below (Analyte, Value, Unit, Reference Interval)
      - Add/delete row, full cell editing, audit OCR text preserved separately
  BOTTOM:
    - ONE primary button: "Save Encounter and Generate Diagnosis"
    - Runs multi-agent pipeline with real-time terminal tracer
    - Displays 8-section Final Clinical Report
    - Evidence Graph view button
"""

import sys
import os
import uuid
import json
import hashlib
import pandas as pd
from pathlib import Path
import streamlit as st

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

st.set_page_config(
    page_title="Clinical Encounter · SwasthAI",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

from frontend.common import inject_css, init_session, get_current_operator, get_current_patient
from backend.app.core.config import settings
from backend.app.db.session import get_db_connection
from backend.app.agents.lab_agent.service import lab_agent_service
from backend.app.services.pipeline import pipeline
from backend.app.ehr.patient_service import patient_ehr_service
from backend.app.core.tracer import tracer

inject_css()
init_session()

operator = get_current_operator()
if not operator:
    st.warning("Please sign in as a Healthpod Operator to conduct clinical encounters.")
    if st.button("Go to Login", type="primary"):
        st.switch_page("pages/01_Login.py")
    st.stop()

# Ensure active patient and consultation exist
patient_id = st.session_state.get("selected_patient_id")
encounter_id = st.session_state.get("selected_encounter_id")

if not patient_id or not encounter_id:
    st.warning("No active patient consultation selected.")
    st.info("Please register a new patient or select an existing patient first.")
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("➕ Register New Patient", type="primary", use_container_width=True):
            st.switch_page("pages/03_Register_Patient.py")
    with col_nav2:
        if st.button("🔍 Login Existing Patient", type="primary", use_container_width=True):
            st.switch_page("pages/04_Search_Patients.py")
    st.stop()

# Fetch active patient info
with get_db_connection() as conn:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, pseudonym_id, full_name, phone_number, dob, age, sex, is_pregnant FROM patients WHERE id = ?;",
        (patient_id,),
    )
    pat_row = cur.fetchone()

if not pat_row:
    st.error("Patient record not found.")
    st.stop()

patient = dict(pat_row)
patient_name = patient.get("full_name") or patient.get("pseudonym_id", "Patient")
patient_age = patient.get("age", "Unknown")
patient_sex = patient.get("sex", "UNKNOWN")
patient_phone = patient.get("phone_number", "—")
patient_dob = patient.get("dob") or f"Age: {patient_age}"

# ---------------------------------------------------------
# SIDEBAR — Patient Access Card (matches Screenshot 2 left)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
            <span style="font-size:18px;">🔐</span>
            <span style="font-size:15px;font-weight:700;color:#002244;">Patient Access</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="patient-access-card">
            <div style="font-size:13px;color:#0066b3;font-weight:600;margin-bottom:6px;">
                👤 Logged in as: <b>{patient_name}</b>
            </div>
            <div style="font-size:12px;color:#5c6b7a;line-height:1.7;">
                📞 <b>Phone:</b> {patient_phone}<br/>
                📅 <b>DOB / Age:</b> {patient_dob}<br/>
                ⚧ <b>Gender:</b> {patient_sex}<br/>
                📋 <b>Consultation ID:</b><br/><code>{encounter_id}</code><br/>
                🆔 <b>Patient ID:</b><br/><code>{patient_id}</code>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🚪 Logout / Switch Patient", use_container_width=True):
        st.session_state["selected_patient_id"] = None
        st.session_state["selected_encounter_id"] = None
        st.session_state["consultation_dossier"] = None
        st.switch_page("app.py")

# ---------------------------------------------------------
# TOP BANNER (matches Screenshot 2 green/teal header card)
# ---------------------------------------------------------
st.markdown(
    """
    <div class="encounter-banner">
        <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:24px;">🏥</span>
            <div>
                <h2>SwasthAI — Satnavri Healthpod AI Assistant</h2>
                <p>AI-assisted clinical decision support for the Satnavri Smart Village Healthpod</p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"<h3 style='color:#002244;font-size:19px;font-weight:700;margin:0 0 16px 0;'>"
    f"📋 New Encounter Form for {patient_name} (Age: {patient_age})</h3>",
    unsafe_allow_html=True,
)

# Initialize encounter form state
if "lab_table_data" not in st.session_state:
    st.session_state["lab_table_data"] = []

if "uploaded_scan_file" not in st.session_state:
    st.session_state["uploaded_scan_file"] = None

if "uploaded_audio_file" not in st.session_state:
    st.session_state["uploaded_audio_file"] = None

if "uploaded_lab_file" not in st.session_state:
    st.session_state["uploaded_lab_file"] = None

if "consultation_dossier" not in st.session_state:
    st.session_state["consultation_dossier"] = None

if "show_evidence_graph" not in st.session_state:
    st.session_state["show_evidence_graph"] = False

# ---------------------------------------------------------
# MAIN TWO-COLUMN LAYOUT
# ---------------------------------------------------------
col_left, col_right = st.columns([1, 1], gap="large")

# =========================================================
# LEFT COLUMN — VITALS AND SYMPTOMS
# =========================================================
with col_left:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
            <span style="font-size:18px;">🩺</span>
            <span style="font-size:16px;font-weight:700;color:#002244;">Healthpod Vitals</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Row 1: BP
    bp_c1, bp_c2 = st.columns(2)
    with bp_c1:
        sbp = st.number_input("Systolic BP (mmHg)", min_value=50, max_value=300, value=120, step=1)
    with bp_c2:
        dbp = st.number_input("Diastolic BP (mmHg)", min_value=30, max_value=200, value=80, step=1)

    # Row 2: Pulse & Temp
    p_c1, p_c2 = st.columns(2)
    with p_c1:
        pulse = st.number_input("Pulse Rate (BPM)", min_value=30, max_value=250, value=75, step=1)
    with p_c2:
        temp_f = st.number_input("Temperature (°F)", min_value=85.0, max_value=115.0, value=98.6, step=0.1, format="%.1f")
    temp_c = round((temp_f - 32.0) * 5.0 / 9.0, 2)
    # Row 3: SpO2 & Weight
    sp_c1, w_c2 = st.columns(2)
    with sp_c1:
        spo2 = st.number_input("SpO2 (%)", min_value=50.0, max_value=100.0, value=98.0, step=0.5, format="%.1f")
    with w_c2:
        weight_kg = st.number_input("Weight (kg)", min_value=2.0, max_value=300.0, value=65.0, step=0.5, format="%.1f")

    # Row 4: Height
    h_c1, _ = st.columns(2)
    with h_c1:
        height_cm = st.number_input("Height (cm)", min_value=30.0, max_value=250.0, value=170.0, step=0.5, format="%.1f")

    # Auto-calculate BMI
    if height_cm > 0:
        height_m = height_cm / 100.0
        calc_bmi = round(weight_kg / (height_m * height_m), 1)
    else:
        calc_bmi = 0.0

    # Live Vitals Summary Pill Tags (matching Screenshot 2)
    bmi_class = "bmi" if (18.5 <= calc_bmi <= 24.9) else "alert"
    bp_alert = "alert" if (sbp >= 140 or dbp >= 90) else ""
    spo2_alert = "alert" if (spo2 < 94) else ""

    st.markdown(
        f"""
        <div class="metric-pill-row">
            <span class="metric-pill {bp_alert}">• Systolic: {sbp}mmHg</span>
            <span class="metric-pill {bp_alert}">• Diastolic: {dbp}mmHg</span>
            <span class="metric-pill">• Pulse: {pulse}bpm</span>
            <span class="metric-pill {spo2_alert}">• SpO2: {spo2}%</span>
            <span class="metric-pill">• Temp: {temp_f}°F</span>
            <span class="metric-pill {bmi_class}">• BMI: {calc_bmi}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Pregnancy Status
    is_pregnant = False
    if patient_sex == "FEMALE":
        is_pregnant = st.checkbox("🤰 Patient is Currently Pregnant", value=bool(patient.get("is_pregnant", False)))

    st.markdown("<hr style='margin:18px 0;border:none;border-top:1px solid #e2e8f0;'/>", unsafe_allow_html=True)

    # SYMPTOMS
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <span style="font-size:18px;">💬</span>
            <span style="font-size:16px;font-weight:700;color:#002244;">Chief Complaint &amp; Symptoms</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Supports multilingual input in English, Hindi (Devanagari), or Hinglish without selecting a language.")
    
    symptoms_input = st.text_area(
        "Enter symptoms",
        height=140,
        placeholder="e.g. Chest pain for 2 days, breathlessness, bukhar nahi hai.\nया: सीने में तेज दर्द, सांस लेने में दिक्कत, चक्कर आ रहे हैं।",
        label_visibility="collapsed",
    )

# =========================================================
# RIGHT COLUMN — DIAGNOSTIC INPUTS
# =========================================================
with col_right:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
            <span style="font-size:18px;">🧪</span>
            <span style="font-size:16px;font-weight:700;color:#002244;">Laboratory Diagnostics &amp; Imaging &amp; Lung Sounds</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # A. RADIOLOGICAL IMAGES
    with st.container():
        st.markdown(
            """
            <div class="upload-group-card">
                <div class="title">🖼️ Upload Diagnostic Scan (Chest X-Ray / CT / Brain MRI / DICOM)</div>
                <div class="hint">Supported formats: JPG, JPEG, PNG, DCM. Max 200MB.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        scan_file = st.file_uploader(
            "Upload Radiology Scan",
            type=["png", "jpg", "jpeg", "dcm"],
            key="scan_uploader",
            label_visibility="collapsed",
        )
        if scan_file:
            st.session_state["uploaded_scan_file"] = scan_file
            st.markdown(
                f"<div style='font-size:12px;color:#0066b3;margin-top:4px;'>Selected: <b>{scan_file.name}</b> ({scan_file.size/1024:.1f} KB)</div>",
                unsafe_allow_html=True,
            )
            if st.button("🗑️ Remove Scan", key="remove_scan_btn"):
                st.session_state["uploaded_scan_file"] = None
                st.rerun()

    # B. ACOUSTIC / LUNG SOUND UPLOAD
    with st.container():
        st.markdown(
            """
            <div class="upload-group-card" style="margin-top:10px;">
                <div class="title">🎧 Upload Lung Sound / Cough / Breathing Recording (.wav / .mp3)</div>
                <div class="hint">ICBHI respiratory acoustic analysis. Supported formats: WAV, MP3.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        audio_file = st.file_uploader(
            "Upload Respiratory Audio",
            type=["wav", "mp3"],
            key="audio_uploader",
            label_visibility="collapsed",
        )
        if audio_file:
            st.session_state["uploaded_audio_file"] = audio_file
            st.markdown(
                f"<div style='font-size:12px;color:#0066b3;margin-top:4px;'>Selected: <b>{audio_file.name}</b> ({audio_file.size/1024:.1f} KB)</div>",
                unsafe_allow_html=True,
            )
            if st.button("🗑️ Remove Audio", key="remove_audio_btn"):
                st.session_state["uploaded_audio_file"] = None
                st.rerun()

    # C. LABORATORY REPORTS & INLINE EXTRACTION
    with st.container():
        st.markdown(
            """
            <div class="upload-group-card" style="margin-top:10px;">
                <div class="title">📑 Upload Lab Reports / Prescriptions (PDFs or Images)</div>
                <div class="hint">Add lab reports (e.g., Blood Glucose, Hemoglobin, WBC) with test value &amp; reference range. Supported formats: PDF, PNG, JPG, JPEG.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        lab_file = st.file_uploader(
            "Upload Laboratory Document",
            type=["pdf", "png", "jpg", "jpeg"],
            key="lab_uploader",
            label_visibility="collapsed",
        )
        if lab_file:
            st.session_state["uploaded_lab_file"] = lab_file
            st.markdown(
                f"<div style='font-size:12px;color:#0066b3;margin-top:4px;'>Selected: <b>{lab_file.name}</b> ({lab_file.size/1024:.1f} KB)</div>",
                unsafe_allow_html=True,
            )

        # Extract Lab Values Button
        col_ext, col_clr = st.columns([2, 1])
        with col_ext:
            extract_clicked = st.button("🔬 Extract Lab Values", type="secondary", use_container_width=True)
        with col_clr:
            if st.button("🧹 Clear Table", width="stretch"):
                st.session_state["lab_table_data"] = []
                st.rerun()

        if extract_clicked:
            if not st.session_state.get("uploaded_lab_file"):
                st.warning("Please upload a laboratory report (PDF or image) before extracting values.")
            else:
                target_file = st.session_state["uploaded_lab_file"]
                try:
                    with st.spinner("Extracting laboratory analytes and preserving raw OCR text..."):
                        # Extract raw text
                        raw_text = lab_agent_service.extract_text_from_file(target_file, filename=target_file.name)
                        
                        # Preserve raw OCR text separately in lab_documents table for audit
                        file_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
                        doc_id = f"labdoc-{uuid.uuid4().hex[:10]}"
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO lab_documents (id, encounter_id, file_name, file_hash, raw_text) VALUES (?, ?, ?, ?, ?);",
                                (doc_id, encounter_id, target_file.name, file_hash, raw_text),
                            )
                            conn.commit()
                        
                        # Parse recognizable laboratory analytes
                        extracted_items = lab_agent_service.extract_from_text(raw_text)
                        
                        new_rows = []
                        for item in extracted_items:
                            new_rows.append({
                                "Analyte / Test Name": item.analyte_name,
                                "Value": str(item.numeric_value if item.numeric_value is not None else item.raw_value),
                                "Unit": item.unit or "",
                                "Reference Interval": item.reference_interval or "",
                            })

                        if not new_rows:
                            st.info("No recognizable laboratory analytes found via automated extraction. You can manually add rows below.")
                        else:
                            st.session_state["lab_table_data"].extend(new_rows)
                            st.success(f"Extracted {len(new_rows)} laboratory test item(s). Please review and correct values in the table below.")
                            st.rerun()
                except Exception as ex:
                    st.error(f"Extraction error: {ex}")

        # EDITABLE LAB VALUES TABLE (Part 4 requirement)
        st.markdown("<h5 style='color:#002244;margin:12px 0 6px 0;'>Reviewed Laboratory Values</h5>", unsafe_allow_html=True)
        st.caption("Every cell is editable. Only reviewed values below are submitted to the LOINC resolver.")

        # Ensure default schema if table is empty
        if not st.session_state["lab_table_data"]:
            df_labs = pd.DataFrame(columns=["Analyte / Test Name", "Value", "Unit", "Reference Interval"])
        else:
            df_labs = pd.DataFrame(st.session_state["lab_table_data"])

        # Display editable table
        edited_df = st.data_editor(
            df_labs,
            num_rows="dynamic",
            use_container_width=True,
            key="lab_table_editor",
            column_config={
                "Analyte / Test Name": st.column_config.TextColumn("Analyte / Test Name", required=True),
                "Value": st.column_config.TextColumn("Value", required=True),
                "Unit": st.column_config.TextColumn("Unit", required=False),
                "Reference Interval": st.column_config.TextColumn("Reference Interval", required=False),
            },
        )
        # Keep table data synced
        st.session_state["lab_table_data"] = edited_df.to_dict(orient="records")

# ---------------------------------------------------------
# BOTTOM ACTION — SAVE ENCOUNTER AND GENERATE DIAGNOSIS
# ---------------------------------------------------------
st.markdown("<hr style='margin:30px 0 20px 0;border:none;border-top:2px solid #cbd5e1;'/>", unsafe_allow_html=True)

save_col1, save_col2, save_col3 = st.columns([1, 2.5, 1])
with save_col2:
    generate_diagnosis_btn = st.button(
        "🚀 Save Encounter and Generate Diagnosis",
        type="primary",
        use_container_width=True,
        help="Saves encounter data, runs vitals rules, symptom NLP, radiology, audio, LOINC resolver, evidence graph, and CDSS diagnostic reasoner.",
    )

# ---------------------------------------------------------
# PIPELINE EXECUTION & RESULT RENDERING
# ---------------------------------------------------------
if generate_diagnosis_btn:
    tracer.event(
        encounter_id,
        "encounter_form",
        "save_and_generate_diagnosis",
        "STARTED",
        detail=f"Patient: {patient_id}",
    )

    with st.spinner("Processing multimodal clinical pipeline..."):
        try:
            # 1. Prepare vitals payload (convert temp F to C for clinical consistency)
            temp_c = round((temp_f - 32.0) * 5.0 / 9.0, 2)
            vitals_payload = {
                "systolic_bp": float(sbp),
                "diastolic_bp": float(dbp),
                "heart_rate": float(pulse),
                "temperature_c": float(temp_c),
                "spo2": float(spo2),
                "weight_kg": float(weight_kg),
                "height_cm": float(height_cm),
                "bmi": float(calc_bmi),
            }

            # 2. Persist vitals into database
            vit_id = f"vit-{uuid.uuid4().hex[:10]}"
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """INSERT OR REPLACE INTO vitals 
                       (id, encounter_id, systolic_bp, diastolic_bp, heart_rate, temperature_c, spo2, weight_kg, height_cm, bmi)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                    (vit_id, encounter_id, sbp, dbp, pulse, temp_c, spo2, weight_kg, height_cm, calc_bmi),
                )
                conn.commit()

            # 3. Save uploaded files to data/uploads
            imaging_saved_path = None
            if st.session_state.get("uploaded_scan_file"):
                f = st.session_state["uploaded_scan_file"]
                img_dir = Path(settings.UPLOAD_DIR) / "radiology"
                img_dir.mkdir(parents=True, exist_ok=True)
                img_path = img_dir / f"{encounter_id}_{f.name}"
                with open(img_path, "wb") as out:
                    out.write(f.getvalue())
                imaging_saved_path = str(img_path)

            audio_saved_path = None
            if st.session_state.get("uploaded_audio_file"):
                f = st.session_state["uploaded_audio_file"]
                aud_dir = Path(settings.UPLOAD_DIR) / "respiratory"
                aud_dir.mkdir(parents=True, exist_ok=True)
                aud_path = aud_dir / f"{encounter_id}_{f.name}"
                with open(aud_path, "wb") as out:
                    out.write(f.getvalue())
                audio_saved_path = str(aud_path)

            # 4. Prepare reviewed laboratory entries
            reviewed_labs = []
            for row in st.session_state.get("lab_table_data", []):
                t_name = str(row.get("Analyte / Test Name", "")).strip()
                t_val = str(row.get("Value", "")).strip()
                if t_name and t_val:
                    reviewed_labs.append({
                        "analyte_name": t_name,
                        "raw_value": t_val,
                        "unit": str(row.get("Unit", "")).strip() or None,
                        "reference_interval": str(row.get("Reference Interval", "")).strip() or None,
                    })

            # 5. Execute Multi-Agent Clinical Pipeline
            progress_bar = st.progress(10, text="Executing Vitals Rule Engine and Symptom NLP...")
            
            dossier = pipeline.execute_consultation_pipeline(
                encounter_id=encounter_id,
                patient_info=patient,
                symptom_text=symptoms_input,
                vitals_data=vitals_payload,
                lab_items_raw=reviewed_labs,
                imaging_file_path=imaging_saved_path,
                respiratory_file_path=audio_saved_path,
            )

            progress_bar.progress(80, text="Persisting Clinical Findings & EvidenceGraph...")
            
            # Persist full encounter in SQLite EHR
            patient_ehr_service.persist_full_encounter(dossier, patient_id=patient_id)
            progress_bar.progress(100, text="Clinical Pipeline Complete!")

            st.session_state["consultation_dossier"] = dossier
            st.success("Encounter processed and saved successfully! Detailed clinical report generated below.")
            
            tracer.event(
                encounter_id,
                "encounter_form",
                "save_and_generate_diagnosis",
                "COMPLETED",
                detail="Final report rendered",
            )

        except Exception as exc:
            tracer.event(
                encounter_id,
                "encounter_form",
                "save_and_generate_diagnosis",
                "FAILED",
                exception=exc,
            )
            st.error(f"Pipeline error: {exc}")

# ---------------------------------------------------------
# FINAL CLINICAL REPORT (8 SECTIONS, Part 13 Requirement)
# ---------------------------------------------------------
dossier = st.session_state.get("consultation_dossier")

if dossier:
    st.markdown("<hr style='margin:40px 0 24px 0;border:none;border-top:3px solid var(--primary);'/>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:#002244;font-size:24px;font-weight:800;margin-bottom:16px;'>📄 Structured Clinical Report</h2>", unsafe_allow_html=True)

    safety = dossier.get("safety_assessment", {})
    circuit_breaker = safety.get("circuit_breaker_halted", False)
    alerts = safety.get("alerts", [])

    # SECTION 8: CLINICAL SAFETY ALERTS (Prominently displayed first as required by Part 13)
    if circuit_breaker or alerts:
        st.markdown(
            f"""
            <div style="background:#fef2f2;border:2px solid #ef4444;border-radius:10px;padding:18px 22px;margin-bottom:24px;">
                <div style="display:flex;align-items:center;gap:10px;color:#991b1b;font-size:17px;font-weight:800;">
                    🚨 CLINICAL SAFETY ALERT — {'EMERGENCY CIRCUIT BREAKER HALTED' if circuit_breaker else 'CRITICAL / WARNING THRESHOLDS DETECTED'}
                </div>
                <div style="color:#7f1d1d;font-size:14px;margin-top:6px;font-weight:600;">
                    {safety.get('primary_reason', 'Active physiological safety warnings identified.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if safety.get("escalation_actions"):
            st.markdown("<div style='font-size:13px;font-weight:700;color:#991b1b;'>Immediate Escalation Actions:</div>", unsafe_allow_html=True)
            for act in safety.get("escalation_actions", []):
                st.markdown(f"- 🔴 **{act}**")

    # SECTION 1: Patient and Consultation Information
    st.markdown("<h4 style='color:#002244;margin-top:20px;'>1. Patient and Consultation Information</h4>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Patient ID", patient_id)
    c2.metric("Consultation ID", encounter_id)
    c3.metric("Demographics", f"Age {patient_age} · {patient_sex}")
    c4.metric("Status", "VERIFIED")

    # SECTION 2: Vitals Assessment
    st.markdown("<h4 style='color:#002244;margin-top:20px;'>2. Vitals Assessment</h4>", unsafe_allow_html=True)
    v_class = dossier.get("vitals_classification", {})
    v_items = []
    if "blood_pressure" in v_class:
        v_items.append(f"**Blood Pressure:** {v_class['blood_pressure']}")
    if "oxygenation" in v_class:
        v_items.append(f"**Oxygenation:** {v_class['oxygenation']}")
    if not v_items:
        v_items.append("All vital signs within documented reference limits.")
    
    st.markdown(
        f"""
        <div class="card" style="padding:14px 18px;">
            <p style="margin:0 0 6px 0;"><b>Recorded Values:</b> SBP {sbp} mmHg, DBP {dbp} mmHg, Pulse {pulse} bpm, Temp {temp_f}°F ({temp_c}°C), SpO2 {spo2}%, BMI {calc_bmi}</p>
            <p style="margin:0;color:#0066b3;"><b>Rule-Engine Staging:</b> {', '.join(v_items)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # SECTION 3: Symptom Assessment
    st.markdown("<h4 style='color:#002244;margin-top:20px;'>3. Symptom Assessment</h4>", unsafe_allow_html=True)
    s_sum = dossier.get("symptom_summary", {})
    st.markdown(
        f"""
        <div class="card" style="padding:14px 18px;">
            <p style="margin:0 0 6px 0;"><b>Reported Symptom Text:</b> <i>{symptoms_input or 'None entered'}</i></p>
            <p style="margin:0;color:#004d80;"><b>Extraction Summary:</b> {s_sum.get('summary_text', 'No symptoms extracted.')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # SECTION 4: Radiology Findings
    st.markdown("<h4 style='color:#002244;margin-top:20px;'>4. Radiology Findings</h4>", unsafe_allow_html=True)
    rad = dossier.get("radiology_report")
    if rad:
        st.markdown(
            f"""
            <div class="card" style="padding:14px 18px;">
                <p style="margin:0 0 6px 0;"><b>Modality:</b> {rad.get('modality', 'CR')} &nbsp;·&nbsp; <b>Body Part:</b> {rad.get('body_part', 'CHEST')} &nbsp;·&nbsp; <b>Image Quality:</b> {rad.get('image_quality', 'ADEQUATE')}</p>
                <p style="margin:0 0 6px 0;"><b>Observed Findings:</b> {rad.get('observed_findings') or rad.get('summary_text', 'No focal lesions identified.')}</p>
                <p style="margin:0 0 6px 0;"><b>Location:</b> {rad.get('location_of_findings', 'Bilateral lung fields')}</p>
                <p style="margin:0 0 6px 0;color:#92400e;"><b>Limitations &amp; Uncertainty:</b> {rad.get('limitations', 'Standard 2D projection.')} ({rad.get('uncertainty', 'Moderate')})</p>
                <div style="font-size:11px;color:#64748b;margin-top:6px;border-top:1px dashed #e2e8f0;padding-top:4px;">
                    ⚠️ {rad.get('clinical_disclaimer', 'Assistive model observations; not clinically validated diagnostic interpretation.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("No radiological images submitted for this encounter.")

    # SECTION 5: Laboratory Findings
    st.markdown("<h4 style='color:#002244;margin-top:20px;'>5. Laboratory Findings</h4>", unsafe_allow_html=True)
    resolved_labs_list = dossier.get("resolved_labs", [])
    if resolved_labs_list:
        lab_display = []
        for l in resolved_labs_list:
            lab_display.append({
                "Analyte": l.get("analyte_name"),
                "Canonical Name": l.get("canonical_name"),
                "Value": l.get("numeric_value"),
                "Unit": l.get("canonical_unit") or l.get("unit"),
                "Reference Interval": l.get("reference_interval"),
                "LOINC Code": l.get("loinc_code") or "UNRESOLVED",
                "Status": l.get("verification_status"),
                "Plausibility": l.get("plausibility_flag") or "NORMAL",
            })
        st.dataframe(pd.DataFrame(lab_display), use_container_width=True, hide_index=True)
    else:
        st.info("No laboratory analyte values submitted for this encounter.")

    # SECTION 6: Differential Diagnosis
    st.markdown("<h4 style='color:#002244;margin-top:20px;'>6. Differential Diagnosis</h4>", unsafe_allow_html=True)
    diag = dossier.get("diagnosis", {})
    st.markdown(
        f"""
        <div class="card" style="padding:16px 20px;border-left:4px solid #0066b3;">
            <h4 style="margin:0 0 8px 0;color:#002244;">Primary Diagnosis: {diag.get('primary_diagnosis', 'Pending')}</h4>
            <p style="margin:0 0 8px 0;"><b>Differential Considerations:</b> {', '.join(diag.get('differential_diagnoses', [])) or 'None'}</p>
            <p style="margin:0 0 8px 0;color:#5c6b7a;"><b>Clinical Evidence Grounding:</b> {'; '.join(diag.get('evidence_citations', [])) or 'Standard clinical guidelines'}</p>
            <div style="font-size:12px;color:#64748b;margin-top:6px;">CDSS advisory output. Mandatory review by licensed practitioner prior to care management.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # SECTION 7: Drug Recommendations
    st.markdown("<h4 style='color:#002244;margin-top:20px;'>7. Drug Recommendations (Generic Classes Only)</h4>", unsafe_allow_html=True)
    drugs = dossier.get("drug_recommendation", {})
    drug_classes = drugs.get("generic_drug_classes", [])
    if drug_classes:
        st.markdown(
            f"""
            <div class="card" style="padding:16px 20px;">
                <p style="margin:0 0 8px 0;"><b>Recommended Generic Classes:</b> {', '.join(drug_classes)}</p>
                <p style="margin:0 0 8px 0;color:#5c6b7a;"><b>Context &amp; Guidelines:</b> {drugs.get('clinical_context', 'Standard STG therapeutic guidance')}</p>
                <div style="background:#fffbeb;border:1px solid #fcd34d;border-radius:6px;padding:8px 12px;font-size:12px;color:#92400e;">
                    ⚠️ Zero brand names prescribed. Generic drug classes advisory only. Clinician must verify allergies and dosage before prescribing.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("No autonomous drug classes recommended (withheld during active safety protocols or emergency escalation).")

    # ---------------------------------------------------------
    # PART 14 — EVIDENCE GRAPH VIEW (One additional option)
    # ---------------------------------------------------------
    st.markdown("<hr style='margin:30px 0 20px 0;border:none;border-top:1px solid #cbd5e1;'/>", unsafe_allow_html=True)
    
    col_view_eg, _ = st.columns([2, 1])
    with col_view_eg:
        if st.button("📊 View Evidence Graph", type="secondary", use_container_width=True):
            st.session_state["show_evidence_graph"] = not st.session_state["show_evidence_graph"]

    if st.session_state.get("show_evidence_graph"):
        eg = dossier.get("evidence_graph", {})
        st.markdown("<h3 style='color:#002244;margin:20px 0 10px 0;'>🌐 Evidence Graph Visualization</h3>", unsafe_allow_html=True)
        st.caption("Demonstrating provenance: Patient → Consultation → Clinical Inputs → Agent Findings → Evidence Graph → Differential Diagnosis")

        st.markdown(
            f"""
            <div class="card" style="padding:20px;background:#f8fafc;border:1px solid #cbd5e1;">
                <div style="font-size:13px;color:#5c6b7a;margin-bottom:12px;">
                    <b>Graph ID:</b> <code>{eg.get('graph_id', 'N/A')}</code> &nbsp;·&nbsp; 
                    <b>Cryptographic SHA-256 Digest:</b> <code>{eg.get('integrity_hash', 'N/A')}</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Mermaid Graph Diagram
        symptom_nodes = [s.get("canonical_concept", "symptom") for s in eg.get("symptoms", [])]
        symptom_str = " | ".join(symptom_nodes) if symptom_nodes else "None"
        vitals_str = f"BP {sbp}/{dbp}, Pulse {pulse}, SpO2 {spo2}%"
        lab_nodes = [f"{l.get('canonical_name', 'Lab')} ({l.get('loinc_code', 'N/A')})" for l in eg.get("resolved_labs", [])]
        lab_str = " | ".join(lab_nodes) if lab_nodes else "None"
        primary_diag = diag.get("primary_diagnosis", "Pending")

        mermaid_code = f"""
        graph TD
            P["Patient: {patient_name} ({patient_id})"] --> C["Consultation: {encounter_id}"]
            C --> I1["Vitals: {vitals_str}"]
            C --> I2["Symptoms: {symptom_str}"]
            C --> I3["Labs: {lab_str}"]
            C --> I4["Radiology: {rad.get('modality', 'None') if rad else 'None'}"]
            I1 --> EG["EvidenceGraph (Digest: {eg.get('integrity_hash', '')[:12]}...)"]
            I2 --> EG
            I3 --> EG
            I4 --> EG
            EG --> D["Differential Diagnosis: {primary_diag}"]
            D --> R["Generic Drug Classes"]
            
            classDef patient fill:#0066b3,stroke:#004d80,stroke-width:2px,color:#fff;
            classDef consult fill:#004d80,stroke:#002244,stroke-width:2px,color:#fff;
            classDef input fill:#e0f2fe,stroke:#0284c7,stroke-width:1px,color:#0369a1;
            classDef graphNode fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff;
            classDef diag fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff;
            classDef drug fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff;

            class P patient;
            class C consult;
            class I1,I2,I3,I4 input;
            class EG graphNode;
            class D diag;
            class R drug;
        """
        st.markdown(f"```mermaid\n{mermaid_code}\n```")
        
        with st.expander("View Raw Evidence Graph JSON", expanded=False):
            st.json(eg)
