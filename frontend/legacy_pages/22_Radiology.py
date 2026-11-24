# -*- coding: utf-8 -*-
"""SwasthAI CDSS – Radiology / Imaging Metadata (Page 11)

Parse radiology report findings and optional DICOM metadata through the
vision agent.  This is a **metadata-only** pipeline – no CNN-based image
classification is performed (not viable on RTX 3050 within latency budget).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st

st.set_page_config(page_title="SwasthAI CDSS – Radiology", page_icon="🏥", layout="wide")

# ── helpers ──────────────────────────────────────────────────────────────────
def require_login():
    if "user" not in st.session_state:
        st.warning("🔒 Please log in from the Login page.")
        st.stop()

require_login()

# ── page header ──────────────────────────────────────────────────────────────
st.title("🩻 Radiology Report & Imaging Metadata")
st.caption(
    "Enter free-text radiology findings and/or upload DICOM metadata. "
    "The vision agent will parse, structure, and audit the report."
)

st.divider()

# ── input section ────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📝 Radiology Report Findings")
    findings_text = st.text_area(
        "Paste or type the radiology report findings",
        height=260,
        placeholder=(
            "e.g. PA chest radiograph shows bilateral patchy opacities in the lower lobes, "
            "consistent with pneumonia. No pleural effusion. Cardiomediastinal silhouette is normal."
        ),
    )

with col_right:
    st.subheader("📂 DICOM Metadata (optional)")
    dicom_file = st.file_uploader(
        "Upload DICOM metadata file",
        type=["json", "txt", "csv", "dcm"],
        help="Accepted: exported DICOM tag JSON/TXT/CSV or a raw .dcm file (tags only are extracted).",
    )
    modality_override = st.selectbox(
        "Modality override",
        ["Auto-detect", "CR", "CT", "MR", "US", "DX", "NM", "PT", "XA"],
        index=0,
        help="Override modality if auto-detection from report text is unreliable.",
    )

st.divider()

# ── process ──────────────────────────────────────────────────────────────────
if st.button("🔍 Analyse Report", type="primary", use_container_width=True):
    if not findings_text.strip():
        st.warning("Please enter radiology findings before analysing.")
        st.stop()

    with st.spinner("Processing through Vision Agent …"):
        try:
            from backend.app.agents.vision_agent.service import vision_agent  # noqa: E402

            payload: dict = {"text": findings_text.strip()}
            if modality_override != "Auto-detect":
                payload["modality"] = modality_override
            if dicom_file is not None:
                payload["dicom_metadata"] = dicom_file.getvalue().decode("utf-8", errors="replace")

            result = vision_agent.process_image(payload)
        except Exception as exc:
            result = None
            st.error(f"⚠️ Vision agent error: {exc}")

    if result is not None:
        st.success("✅ Report processed successfully.")

        # ── results display ──────────────────────────────────────────────────
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            modality = result.get("modality", "N/A")
            st.metric("Modality", modality)
        with col_b:
            audit_flags = result.get("audit_flags", [])
            audit_status = "PASS" if not audit_flags else "ISSUES"
            colour = "green" if audit_status == "PASS" else "orange"
            st.metric("Audit", audit_status)
            st.markdown(f"<span style='color:{colour};font-weight:700'>{audit_status}</span>", unsafe_allow_html=True)
        with col_c:
            st.metric("Findings", len(result.get("findings", [])))

        # audit flag details
        if audit_flags:
            st.subheader("⚠️ Audit Flags")
            for flag in audit_flags:
                st.warning(flag)

        # parsed findings
        findings_list = result.get("findings", [])
        if findings_list:
            st.subheader("📋 Parsed Findings")
            for i, f in enumerate(findings_list, 1):
                # each finding is a dict
                label = f.get("observation", "")
                severity = f.get("severity", "NORMAL").lower()
                confidence = f.get("confidence_score")
                sev_colour = {"critical": "🔴", "moderate": "🟠", "mild": "🟡", "normal": "🟢"}.get(severity, "⚪")
                conf_text = f" ({confidence:.0%})" if confidence is not None else ""
                st.markdown(f"{sev_colour} **{i}.** {label}{conf_text}")
        else:
            st.info("No structured findings extracted.")

        # additional metadata
        with st.expander("🗂️ Full Result Payload"):
            st.json(result)
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            modality = result.get("modality", "N/A")
            st.metric("Modality", modality)
        with col_b:
            audit = result.get("audit_status", result.get("status", "N/A"))
            colour = "green" if audit in ("PASS", "OK", "APPROVED") else "orange"
            st.metric("Audit Status", audit)
            st.markdown(f"<span style='color:{colour};font-weight:700'>{audit}</span>", unsafe_allow_html=True)
        with col_c:
            st.metric("Findings Count", len(result.get("parsed_findings", result.get("findings", []))))

        # parsed findings
        findings_list = result.get("parsed_findings", result.get("findings", []))
        if findings_list:
            st.subheader("📋 Parsed Findings")
            for i, f in enumerate(findings_list, 1):
                if isinstance(f, dict):
                    label = f.get("finding", f.get("text", str(f)))
                    severity = f.get("severity", "")
                    sev_colour = {"critical": "🔴", "moderate": "🟠", "mild": "🟡", "normal": "🟢"}.get(
                        severity.lower(), "⚪"
                    )
                    st.markdown(f"{sev_colour} **{i}.** {label}")
                else:
                    st.markdown(f"⚪ **{i}.** {f}")
        else:
            st.info("No structured findings extracted.")

        # additional metadata
        with st.expander("🗂️ Full Result Payload"):
            st.json(result)

    # ── no-CNN note ──────────────────────────────────────────────────────────
    st.divider()
    st.info(
        "ℹ️ **Metadata-only pipeline** – This page processes radiology *report text* and DICOM tags. "
        "No CNN-based image classification is performed. The NVIDIA RTX 3050 (4 GB) does not meet "
        "the VRAM requirements for real-time radiological image inference within the latency budget."
    )

else:
    st.info("👆 Enter findings above and click **Analyse Report**.")

# ── disclaimer ───────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "⚕️ **Disclaimer:** Automated report parsing is advisory. All radiology interpretations "
    "must be verified by a qualified radiologist before clinical action."
)
