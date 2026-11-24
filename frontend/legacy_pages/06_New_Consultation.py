"""
SwasthAI — New Consultation
=============================
The MAIN clinical workflow page.  Seven-step consultation flow that calls
SwasthAIPipeline.execute_consultation_pipeline() directly and displays
results inline with safety-coded alerts.
"""

import sys, os, uuid, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st

st.set_page_config(page_title="New Consultation · SwasthAI", page_icon="📋", layout="wide")

from backend.app.db.session import init_db
from backend.app.ehr.patient_service import patient_ehr_service
from backend.app.services.pipeline import SwasthAIPipeline
from backend.app.reporting.report_generator import report_generator

init_db()


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
        <h2 style="margin:0;color:#fff;">📋 New Consultation</h2>
        <p style="margin:6px 0 0;opacity:0.9;">
            Multimodal Clinical Evidence Pipeline · Safety-First
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =====================================================================
# STEP 1 — Select Patient
# =====================================================================
st.markdown("### Step 1: Select Patient")

default_pid = st.session_state.get("selected_patient_id", "")
patient_id = st.text_input(
    "Patient ID *",
    value=default_pid,
    placeholder="e.g. pat-abc1234567",
    help="Enter the patient ID. Register a new patient if needed.",
)

patient_info = None
if patient_id:
    patient_info = patient_ehr_service.get_patient_by_id(patient_id.strip())
    if patient_info:
        pi1, pi2, pi3, pi4 = st.columns(4)
        pi1.metric("Pseudonym", patient_info.get("pseudonym_id", "—"))
        pi2.metric("Age", f"{patient_info.get('age', '—')} yrs")
        pi3.metric("Sex", patient_info.get("sex", "—"))
        pi4.metric("Pregnant", "Yes" if patient_info.get("is_pregnant") else "No")
    else:
        st.error("Patient not found. Please check the ID or register a new patient.")

if not patient_info:
    if st.button("🆕 Register New Patient"):
        st.switch_page("pages/03_Register_Patient.py")
    st.stop()

st.markdown("---")


# =====================================================================
# STEP 2 — Chief Complaint / Symptoms
# =====================================================================
st.markdown("### Step 2: Chief Complaint / Symptoms")
st.caption("Supports English, Hindi (Devanagari), and Hinglish input.")

symptoms_text = st.text_area(
    "Describe symptoms *",
    height=120,
    placeholder=(
        "e.g. Patient complains of high fever for 3 days, cough with yellowish sputum, "
        "breathlessness on exertion.\n"
        "या: मरीज़ को 3 दिन से तेज़ बुखार है, पीला बलगम वाली खांसी, चलने पर सांस फूलती है।"
    ),
    help="Enter symptoms in any language. The NLP engine handles bilingual input.",
)

st.markdown("---")


# =====================================================================
# STEP 3 — Vital Signs
# =====================================================================
st.markdown("### Step 3: Vital Signs")
st.caption("Enter available readings. Normal adult reference ranges shown.")

v1, v2, v3 = st.columns(3)
with v1:
    systolic_bp = st.number_input(
        "Systolic BP (mmHg)", min_value=40.0, max_value=300.0,
        value=120.0, step=1.0, help="Normal: 90–120 mmHg"
    )
    diastolic_bp = st.number_input(
        "Diastolic BP (mmHg)", min_value=20.0, max_value=200.0,
        value=80.0, step=1.0, help="Normal: 60–80 mmHg"
    )

with v2:
    heart_rate = st.number_input(
        "Heart Rate (bpm)", min_value=20.0, max_value=250.0,
        value=78.0, step=1.0, help="Normal: 60–100 bpm"
    )
    respiratory_rate = st.number_input(
        "Respiratory Rate (/min)", min_value=5.0, max_value=80.0,
        value=16.0, step=1.0, help="Normal: 12–20 /min"
    )

with v3:
    temperature_c = st.number_input(
        "Temperature (°C)", min_value=30.0, max_value=45.0,
        value=36.8, step=0.1, format="%.1f", help="Normal: 36.1–37.2 °C"
    )
    spo2 = st.number_input(
        "SpO2 (%)", min_value=40.0, max_value=100.0,
        value=97.0, step=1.0, help="Normal: ≥ 95%"
    )

blood_glucose = st.number_input(
    "Random Blood Sugar (mg/dL) — optional",
    min_value=10.0, max_value=1000.0, value=110.0, step=1.0,
    help="Normal fasting: 70–100 mg/dL",
)

vitals_data = {
    "systolic_bp": systolic_bp,
    "diastolic_bp": diastolic_bp,
    "heart_rate": heart_rate,
    "respiratory_rate": respiratory_rate,
    "temperature_c": temperature_c,
    "spo2": spo2,
    "blood_glucose_mg_dl": blood_glucose,
}

st.markdown("---")


# =====================================================================
# STEP 4 — Optional Lab Results
# =====================================================================
st.markdown("### Step 4: Laboratory Results (optional)")
st.caption("Add lab analyte rows. Leave empty if not available.")

if "lab_rows" not in st.session_state:
    st.session_state["lab_rows"] = []

def _add_lab_row():
    st.session_state["lab_rows"].append({"analyte_name": "", "value": "", "unit": ""})

st.button("➕ Add Lab Row", on_click=_add_lab_row)

lab_items_raw = []
rows_to_remove = []

for idx, lab in enumerate(st.session_state["lab_rows"]):
    lc1, lc2, lc3, lc4 = st.columns([3, 2, 2, 1])
    with lc1:
        name = st.text_input("Analyte", value=lab["analyte_name"], key=f"lab_name_{idx}",
                             placeholder="e.g. Hemoglobin")
    with lc2:
        val = st.text_input("Value", value=lab["value"], key=f"lab_val_{idx}",
                            placeholder="e.g. 12.5")
    with lc3:
        unit = st.text_input("Unit", value=lab["unit"], key=f"lab_unit_{idx}",
                             placeholder="e.g. g/dL")
    with lc4:
        st.markdown("")  # spacer
        if st.button("🗑️", key=f"lab_del_{idx}"):
            rows_to_remove.append(idx)

    if name and val:
        try:
            numeric = float(val)
        except ValueError:
            numeric = None
        lab_items_raw.append({
            "analyte_name": name,
            "value": numeric,
            "raw_value": val,
            "unit": unit if unit else None,
        })

# Clean up removed rows
if rows_to_remove:
    for i in sorted(rows_to_remove, reverse=True):
        st.session_state["lab_rows"].pop(i)
    st.rerun()

st.markdown("---")


# =====================================================================
# STEP 5 — Imaging Findings (text)
# =====================================================================
st.markdown("### Step 5: Imaging Findings (optional)")
imaging_findings = st.text_area(
    "Free-text imaging/radiology findings",
    height=80,
    placeholder="e.g. Chest X-ray PA view shows bilateral infiltrates in lower lobes.",
    help="Paste radiology report text if available.",
)

st.markdown("---")


# =====================================================================
# STEP 6 — Patient Allergies
# =====================================================================
st.markdown("### Step 6: Known Allergies (optional)")
allergies_text = st.text_input(
    "List allergies (comma-separated)",
    placeholder="e.g. Penicillin, Sulfa, Aspirin",
    help="Known drug or food allergies for contraindication checking.",
)
patient_allergies = [a.strip() for a in allergies_text.split(",") if a.strip()] if allergies_text else []

st.markdown("---")


# =====================================================================
# STEP 7 — Submit & Run Pipeline
# =====================================================================
st.markdown("### Step 7: Submit Consultation")

submit = st.button(
    "🚀 Run Clinical Pipeline",
    use_container_width=True,
    type="primary",
    help="Execute the full 4-stage evidence pipeline with safety circuit breaker.",
)

if submit:
    if not symptoms_text or not symptoms_text.strip():
        st.error("Please enter at least a chief complaint / symptoms description.")
        st.stop()

    encounter_id = f"enc-{uuid.uuid4().hex[:8]}"
    user = st.session_state["user"]

    with st.spinner("🔬 Running SwasthAI clinical pipeline..."):
        try:
            dossier = SwasthAIPipeline.execute_consultation_pipeline(
                encounter_id=encounter_id,
                patient_info={
                    "age": patient_info.get("age"),
                    "sex": patient_info.get("sex", "UNKNOWN"),
                    "is_pregnant": bool(patient_info.get("is_pregnant")),
                    "full_name": None,  # Privacy: never pass names to pipeline
                },
                symptom_text=symptoms_text,
                vitals_data=vitals_data,
                lab_items_raw=lab_items_raw if lab_items_raw else None,
                imaging_report_text=imaging_findings if imaging_findings else None,
                patient_allergies=patient_allergies if patient_allergies else None,
            )

            # Persist encounter
            patient_ehr_service.persist_full_encounter(
                pipeline_dossier=dossier,
                patient_id=patient_id.strip(),
                operator_id=user.get("user_id", "usr-asha-01"),
            )

            st.session_state["last_dossier"] = dossier
            st.session_state["last_encounter_id"] = encounter_id

        except Exception as e:
            st.error(f"❌ Pipeline execution failed: {e}")
            import traceback
            with st.expander("Error details"):
                st.code(traceback.format_exc())
            st.stop()


# =====================================================================
# RESULTS DISPLAY (if dossier in session)
# =====================================================================
if "last_dossier" in st.session_state:
    dossier = st.session_state["last_dossier"]
    safety = dossier.get("safety_assessment", {})
    diag = dossier.get("diagnosis", {})
    drug = dossier.get("drug_recommendation", {})
    eg = dossier.get("evidence_graph", {})

    st.markdown("---")
    st.markdown(f"## 📊 Consultation Results — `{dossier['encounter_id']}`")

    # ── 7a. Safety Assessment ───────────────────────────────────────────
    st.markdown("### 🛡️ Safety Assessment")

    cb_halted = safety.get("circuit_breaker_halted", False)
    if cb_halted:
        st.markdown(
            '<div style="background:#E74C3C;color:#fff;padding:16px 24px;'
            'border-radius:10px;font-size:1.15rem;font-weight:600;">'
            '⛔ CIRCUIT BREAKER: REJECTED — Emergency Escalation Required'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background:#27AE60;color:#fff;padding:16px 24px;'
            'border-radius:10px;font-size:1.15rem;font-weight:600;">'
            '✅ CIRCUIT BREAKER: APPROVED — Non-Critical'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown(f"**Status**: `{safety.get('safety_status', '—')}`")
    st.markdown(f"**Reason**: {safety.get('primary_reason', '—')}")

    if safety.get("escalation_actions"):
        st.warning("**Emergency Actions Required:**")
        for act in safety["escalation_actions"]:
            st.markdown(f"- 🚨 {act}")

    # Individual alerts
    alerts = safety.get("alerts", [])
    if alerts:
        st.markdown("#### Safety Alerts")
        for alert in alerts:
            severity = alert.get("severity", "INFO")
            if severity == "CRITICAL":
                st.error(
                    f"🔴 **CRITICAL** — Rule `{alert.get('rule_id', '?')}`  \n"
                    f"Observed: `{alert.get('observed_value', '?')}` · Threshold: `{alert.get('threshold', '?')}`  \n"
                    f"Escalation: {alert.get('escalation_instructions', '—')}"
                )
            elif severity == "WARNING":
                st.warning(
                    f"🟡 **WARNING** — Rule `{alert.get('rule_id', '?')}`  \n"
                    f"Observed: `{alert.get('observed_value', '?')}` · Threshold: `{alert.get('threshold', '?')}`"
                )
            else:
                st.info(
                    f"ℹ️ **INFO** — Rule `{alert.get('rule_id', '?')}`  \n"
                    f"Observed: `{alert.get('observed_value', '?')}`"
                )

    st.markdown("---")

    # ── 7b. Extracted Symptoms ──────────────────────────────────────────
    st.markdown("### 🩺 Extracted Symptoms")
    symptom_summary = dossier.get("symptom_summary", {})
    st.markdown(f"_{symptom_summary.get('summary_text', 'No summary.')}_")

    sym_list = symptom_summary.get("extracted_symptoms", [])
    neg_list = symptom_summary.get("negated_symptoms", [])

    if sym_list or neg_list:
        import pandas as pd
        all_syms = []
        for s in sym_list:
            all_syms.append({
                "Concept": s.get("canonical_concept", "—"),
                "Original Phrase": s.get("original_phrase", "—"),
                "Language": s.get("language", "—"),
                "Negated": "❌ No",
                "Method": s.get("extraction_method", "—"),
                "Confidence": f"{s.get('confidence_score', 0):.2f}",
            })
        for s in neg_list:
            all_syms.append({
                "Concept": s.get("canonical_concept", "—"),
                "Original Phrase": s.get("original_phrase", "—"),
                "Language": s.get("language", "—"),
                "Negated": "✅ Yes",
                "Method": s.get("extraction_method", "—"),
                "Confidence": f"{s.get('confidence_score', 0):.2f}",
            })
        st.dataframe(pd.DataFrame(all_syms), use_container_width=True, hide_index=True)
    else:
        st.caption("No symptoms extracted.")

    st.markdown("---")

    # ── 7c. Resolved Labs ───────────────────────────────────────────────
    st.markdown("### 🧪 Resolved Laboratory Values")
    resolved_labs = dossier.get("resolved_labs", [])
    if resolved_labs:
        import pandas as pd
        lab_df = pd.DataFrame(resolved_labs)
        display_cols = ["canonical_name", "numeric_value", "canonical_unit",
                        "reference_interval", "loinc_code", "verification_status",
                        "plausibility_flag"]
        available = [c for c in display_cols if c in lab_df.columns]
        lab_df = lab_df[available]
        lab_df.columns = ["Analyte", "Value", "Unit", "Reference", "LOINC",
                          "Status", "Flag"][:len(available)]
        st.dataframe(lab_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No laboratory results to display.")

    st.markdown("---")

    # ── 7d. Diagnosis ───────────────────────────────────────────────────
    st.markdown("### 🔬 Diagnostic Hypotheses")

    st.markdown(f"**Primary Diagnosis**: **{diag.get('primary_diagnosis', '—')}**")

    diffs = diag.get("differential_diagnoses", [])
    if diffs:
        st.markdown("**Differential Diagnoses:**")
        for d in diffs:
            st.markdown(f"- {d}")

    citations = diag.get("evidence_citations", [])
    if citations:
        with st.expander("📚 Evidence Citations"):
            for c in citations:
                st.markdown(f"- {c}")

    warnings = diag.get("missing_data_warnings", [])
    if warnings:
        for w in warnings:
            st.warning(f"⚠️ {w}")

    st.caption(f"Model: `{diag.get('model_version', '—')}` · "
               f"Review mandatory: {'✅ Yes' if diag.get('physician_review_mandatory') else '❌ No'}")

    st.markdown("---")

    # ── 7e. Drug Recommendations ────────────────────────────────────────
    st.markdown("### 💊 Drug-Class Recommendations")

    drug_classes = drug.get("generic_drug_classes", [])
    if drug_classes:
        for dc in drug_classes:
            st.markdown(f"- **{dc}**")
        st.markdown(f"_Clinical context: {drug.get('clinical_context', '—')}_")
    else:
        st.info("No drug classes recommended (may be withheld by safety circuit breaker).")

    contra = drug.get("contraindication_flags", [])
    if contra:
        st.warning("**Contraindication Alerts:**")
        for cf in contra:
            st.markdown(f"- ⚠️ {cf}")

    caution = drug.get("caution_notes", [])
    if caution:
        for cn in caution:
            st.markdown(f"- 📌 {cn}")

    st.markdown("---")

    # ── 7f. EvidenceGraph integrity ─────────────────────────────────────
    st.markdown("### 🔗 EvidenceGraph Integrity")
    integrity_hash = eg.get("integrity_hash", "—")
    st.code(f"SHA-256 Hash: {integrity_hash}", language="text")

    missing = dossier.get("missing_modalities", [])
    if missing:
        st.caption(f"Missing modalities: {', '.join(missing)}")

    st.markdown("---")

    # ── 7g. Report download ────────────────────────────────────────────
    st.markdown("### 📥 Download Report")

    try:
        md_report = report_generator.generate_markdown_report(dossier)
        st.download_button(
            "📄 Download Markdown Report",
            data=md_report,
            file_name=f"consultation_report_{dossier['encounter_id']}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    except Exception as e:
        st.warning(f"Could not generate report: {e}")

    try:
        json_report = report_generator.generate_json_report(dossier)
        st.download_button(
            "📋 Download JSON Dossier",
            data=json_report,
            file_name=f"consultation_dossier_{dossier['encounter_id']}.json",
            mime="application/json",
            use_container_width=True,
        )
    except Exception as e:
        st.warning(f"Could not generate JSON report: {e}")

    # Inline report preview
    with st.expander("📖 Preview Markdown Report"):
        try:
            st.markdown(md_report)
        except Exception:
            st.caption("Report preview unavailable.")

    # ── Mandatory disclaimer ────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "> **CLINICAL NOTICE**: This report is an AI-generated clinical "
        "decision support aid. It does **NOT** constitute a confirmed medical "
        "diagnosis or a prescription. All therapeutic decisions must be verified "
        "and signed by a registered medical practitioner."
    )
