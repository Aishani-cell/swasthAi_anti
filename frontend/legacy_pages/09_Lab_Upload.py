
# -*- coding: utf-8 -*-
"""SwasthAI CDSS – Clinical Extraction & Laboratory Review"""

import sys
import os
import hashlib
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd

from backend.app.agents.symptom_agent.service import symptom_service
from backend.app.agents.lab_agent.service import lab_agent_service
from backend.app.agents.lab_resolver.resolver_service import lab_resolver_service
from backend.app.schemas.labs import ExtractedLabItem


st.set_page_config(
    page_title="SwasthAI CDSS – Extraction Review",
    page_icon="🏥",
    layout="wide",
)


def require_login():
    if "user" not in st.session_state:
        st.session_state["user"] = {
            "id": "usr-doc-01",
            "username": "dr.sharma",
            "full_name": "Dr. Rajesh Sharma, MD",
            "role": "clinician",
        }


require_login()


def parse_numeric_value(value):
    """Convert an edited value to float without silently accepting invalid data."""
    if value is None or pd.isna(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    # Remove thousands separators, then validate the complete numeric string.
    normalized = value.replace(",", "")

    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", normalized):
        raise ValueError(f"'{value}' is not a valid numeric value.")

    return float(normalized)


def make_editor_dataframe(items):
    """Convert extracted schema objects into editable table rows."""
    return pd.DataFrame([
        {
            "Analyte": item.analyte_name,
            "Value": item.raw_value,
            "Unit": item.unit or "",
            "Reference Interval": item.reference_interval or "",
            "Extraction Confidence": item.confidence,
        }
        for item in items
    ], columns=[
        "Analyte",
        "Value",
        "Unit",
        "Reference Interval",
        "Extraction Confidence",
    ])


def get_reviewed_items(edited_df):
    """Validate edited rows and convert them into ExtractedLabItem objects."""
    reviewed_items = []
    errors = []

    for index, row in edited_df.iterrows():
        analyte = "" if pd.isna(row["Analyte"]) else str(row["Analyte"]).strip()
        raw_value = "" if pd.isna(row["Value"]) else str(row["Value"]).strip()
        unit = "" if pd.isna(row["Unit"]) else str(row["Unit"]).strip()
        reference_interval = (
            ""
            if pd.isna(row["Reference Interval"])
            else str(row["Reference Interval"]).strip()
        )

        # Ignore completely empty rows added by the editor.
        if not analyte and not raw_value and not unit and not reference_interval:
            continue

        if not analyte:
            errors.append(f"Row {index + 1}: Analyte name is missing.")
            continue

        if not raw_value:
            errors.append(f"Row {index + 1}: Value is missing.")
            continue

        try:
            numeric_value = parse_numeric_value(raw_value)
        except ValueError as exc:
            errors.append(f"Row {index + 1}: {exc}")
            continue

        confidence = row.get("Extraction Confidence", 1.0)

        if confidence is None or pd.isna(confidence):
            confidence = 1.0

        reviewed_items.append(
            ExtractedLabItem(
                analyte_name=analyte,
                raw_value=raw_value,
                numeric_value=numeric_value,
                unit=unit or None,
                reference_interval=reference_interval or None,
                confidence=float(confidence),
            )
        )

    return reviewed_items, errors


# ---------------------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------------------

st.title("🔬 Clinical Extraction & Laboratory Review")
st.caption(
    "Review extracted clinical information and standardize laboratory "
    "results using the deterministic LOINC resolver."
)

st.divider()


# ---------------------------------------------------------------------
# SYMPTOM NLP AGENT – EXISTING FUNCTIONALITY PRESERVED
# ---------------------------------------------------------------------

st.subheader("🗣️ Symptom NLP Agent")

sample_sym = st.text_area(
    "Enter Symptoms to Test Extraction",
    value="सीने में तेज दर्द, पसीना आना और सांस लेने में दिक्कत, no fever",
    height=100,
    key="symptom_input",
)

if st.button("Extract Symptoms", type="primary"):
    try:
        summary = symptom_service.process_symptoms(sample_sym)

        st.markdown(f"**Canonical Summary:** {summary.summary_text}")

        if summary.extracted_symptoms:
            st.markdown("#### Positive Symptoms")

            df_pos = pd.DataFrame([
                {
                    "Canonical Concept": s.canonical_concept,
                    "Original Phrase": s.original_phrase,
                    "Language": s.language,
                    "Method": s.extraction_method,
                    "Confidence": f"{s.confidence_score:.2f}",
                }
                for s in summary.extracted_symptoms
            ])

            st.dataframe(df_pos, use_container_width=True)

        if summary.negated_symptoms:
            st.markdown("#### Negated Symptoms (20-Char Boundary)")

            df_neg = pd.DataFrame([
                {
                    "Concept": s.canonical_concept,
                    "Phrase": s.original_phrase,
                    "Negated": "Yes",
                }
                for s in summary.negated_symptoms
            ])

            st.dataframe(df_neg, use_container_width=True)

    except Exception as exc:
        st.error(f"Symptom extraction failed: {exc}")


st.divider()


# ---------------------------------------------------------------------
# LABORATORY REPORT UPLOAD AND REVIEW
# ---------------------------------------------------------------------

st.subheader("🧪 Laboratory Report Upload & Review")

st.write(
    "Upload a laboratory report. Extracted values will appear in an editable "
    "table so that you can correct them before LOINC resolution."
)

uploaded_file = st.file_uploader(
    "Upload Laboratory Report",
    type=["pdf", "jpg", "jpeg", "png"],
    help="Supported formats: PDF, JPG, JPEG and PNG.",
    key="lab_report_uploader",
)


# Initialize session state.
if "lab_original_text" not in st.session_state:
    st.session_state["lab_original_text"] = ""

if "lab_editor_df" not in st.session_state:
    st.session_state["lab_editor_df"] = pd.DataFrame(
        columns=[
            "Analyte",
            "Value",
            "Unit",
            "Reference Interval",
            "Extraction Confidence",
        ]
    )

if "lab_upload_hash" not in st.session_state:
    st.session_state["lab_upload_hash"] = None

if "lab_resolved_results" not in st.session_state:
    st.session_state["lab_resolved_results"] = None

if "lab_reviewed_items" not in st.session_state:
    st.session_state["lab_reviewed_items"] = None


# Extract only when a new file is uploaded.
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    current_hash = hashlib.sha256(file_bytes).hexdigest()

    if current_hash != st.session_state["lab_upload_hash"]:
        try:
            with st.spinner("Extracting laboratory report text..."):
                original_text = lab_agent_service.extract_text_from_file(
                    file_bytes,
                    filename=uploaded_file.name,
                )

                extracted_items = lab_agent_service.extract_from_text(
                    original_text
                )

            st.session_state["lab_original_text"] = original_text
            st.session_state["lab_editor_df"] = make_editor_dataframe(
                extracted_items
            )
            st.session_state["lab_upload_hash"] = current_hash

            # Invalidate previous results when a new report is uploaded.
            st.session_state["lab_resolved_results"] = None
            st.session_state["lab_reviewed_items"] = None

            st.session_state["staged_lab_text"] = original_text

            if not extracted_items:
                st.warning(
                    "Text was extracted, but no recognizable laboratory "
                    "analytes were found. You can add entries manually below."
                )

        except Exception as exc:
            st.session_state["lab_original_text"] = ""
            st.session_state["lab_editor_df"] = pd.DataFrame(
                columns=[
                    "Analyte",
                    "Value",
                    "Unit",
                    "Reference Interval",
                    "Extraction Confidence",
                ]
            )
            st.error(f"Could not process the uploaded report: {exc}")


# ---------------------------------------------------------------------
# EDITABLE TABLE – DIRECTLY BELOW UPLOAD CONTROL
# ---------------------------------------------------------------------

if uploaded_file is not None and st.session_state["lab_upload_hash"] is not None:

    st.markdown("### Review Extracted Laboratory Values")

    st.caption(
        "Edit the analyte, value, unit and reference interval. "
        "Use the table controls to add or delete rows. "
        "Extraction confidence is read-only."
    )

    editor_key = f"lab_editor_{st.session_state['lab_upload_hash']}"

    edited_df = st.data_editor(
        st.session_state["lab_editor_df"],
        key=editor_key,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Analyte": st.column_config.TextColumn(
                "Analyte / Test Name",
                help="Name of the laboratory test.",
                required=True,
            ),
            "Value": st.column_config.TextColumn(
                "Result Value",
                help="Edit the reported value.",
                required=True,
            ),
            "Unit": st.column_config.TextColumn(
                "Unit",
                help="For example: mg/dL, g/dL, mEq/L.",
            ),
            "Reference Interval": st.column_config.TextColumn(
                "Reference Interval",
                help="For example: 12–16 g/dL.",
            ),
            "Extraction Confidence": st.column_config.NumberColumn(
                "OCR Confidence",
                disabled=True,
                format="%.2f",
            ),
        },
    )

    st.caption(
        "Rows can be added or removed using the table controls. "
        "Manually added rows may have a blank OCR confidence."
    )

    if st.button(
        "Save and Validate Results",
        type="primary",
        use_container_width=True,
    ):
        reviewed_items, validation_errors = get_reviewed_items(edited_df)

        if validation_errors:
            st.error("Please correct the following entries before validation:")
            for error in validation_errors:
                st.write(f"- {error}")

            st.session_state["lab_resolved_results"] = None
            st.session_state["lab_reviewed_items"] = None

        elif not reviewed_items:
            st.warning("There are no laboratory entries to validate.")

            st.session_state["lab_resolved_results"] = None
            st.session_state["lab_reviewed_items"] = None

        else:
            try:
                with st.spinner("Resolving and validating reviewed results..."):
                    resolved = lab_resolver_service.resolve_items(
                        reviewed_items
                    )

                st.session_state["lab_resolved_results"] = resolved
                st.session_state["lab_reviewed_items"] = reviewed_items

                st.success(
                    f"{len(reviewed_items)} reviewed laboratory entries "
                    "were submitted to the LOINC resolver."
                )

            except Exception as exc:
                st.session_state["lab_resolved_results"] = None
                st.session_state["lab_reviewed_items"] = None
                st.error(f"Laboratory resolution failed: {exc}")


# ---------------------------------------------------------------------
# RESOLVED RESULTS
# ---------------------------------------------------------------------

resolved = st.session_state.get("lab_resolved_results")

if resolved is not None:

    st.divider()
    st.markdown("### LOINC Resolution Results")

    if resolved:
        df_res = pd.DataFrame([
            {
                "Analyte": r.canonical_name,
                "LOINC": r.loinc_code or "N/A",
                "Original Value": r.raw_value,
                "Normalized Value": (
                    f"{r.numeric_value} {r.canonical_unit or ''}".strip()
                    if r.numeric_value is not None
                    else "N/A"
                ),
                "Status": r.verification_status,
                "Plausibility Flag": r.plausibility_flag or "NOT FLAGGED",
                "Reference Interval": r.reference_interval or "N/A",
            }
            for r in resolved
        ])

        st.dataframe(
            df_res,
            use_container_width=True,
            hide_index=True,
        )

        critical_results = [
            r for r in resolved
            if r.plausibility_flag in ["CRITICAL_HIGH", "CRITICAL_LOW"]
        ]

        needs_review = [
            r for r in resolved
            if r.verification_status != "VERIFIED"
        ]

        if critical_results:
            st.error(
                f"🚨 {len(critical_results)} critical laboratory value(s) "
                "flagged. Clinician review and appropriate escalation are required."
            )

        if needs_review:
            st.warning(
                f"{len(needs_review)} result(s) are not marked VERIFIED. "
                "Review their resolver status before using them in clinical reasoning."
            )

        if not critical_results and not needs_review:
            st.success("All resolved entries are marked VERIFIED and have no critical flags.")

    else:
        st.warning("The resolver returned no results.")


# ---------------------------------------------------------------------
# ORIGINAL OCR TEXT – PRESERVED SEPARATELY FOR AUDIT
# ---------------------------------------------------------------------

original_text = st.session_state.get("lab_original_text", "")

if original_text:
    with st.expander("View Original Extracted Report Text (Audit Record)"):
        st.caption(
            "This is the original extracted text. Editing the table above "
            "does not modify this record."
        )
        st.text_area(
            "Original OCR / PDF Text",
            value=original_text,
            height=250,
            disabled=True,
            key="original_lab_text_display",
        )
