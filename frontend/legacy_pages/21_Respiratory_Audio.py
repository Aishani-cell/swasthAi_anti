# -*- coding: utf-8 -*-
"""SwasthAI CDSS – Respiratory Acoustic Analysis (Page 10)

Upload a WAV recording of lung sounds and receive an AI-predicted
classification (Normal / Crackle / Wheeze / Both) with confidence scores.

Training data: ICBHI 2017 Respiratory Sound Database.
"""

import sys, os, uuid, datetime, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st

st.set_page_config(page_title="SwasthAI CDSS – Respiratory Audio", page_icon="🏥", layout="wide")

# ── helpers ──────────────────────────────────────────────────────────────────
def require_login():
    if "user" not in st.session_state:
        st.warning("🔒 Please log in from the Login page.")
        st.stop()

require_login()

UPLOAD_DIR = pathlib.Path(__file__).resolve().parents[2] / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

CLASS_COLOURS = {
    "Normal": "green",
    "Crackle": "orange",
    "Wheeze": "orange",
    "Both": "red",
}

# ── page header ──────────────────────────────────────────────────────────────
st.title("🫁 Respiratory Acoustic Analysis")
st.caption("Upload a WAV lung-sound recording for AI classification powered by the ICBHI-trained model.")

st.divider()

# ── file upload ──────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload a WAV file",
    type=["wav"],
    help="Mono or stereo WAV, ideally sampled at 4–44.1 kHz. Max 200 MB.",
    accept_multiple_files=False,
)

if uploaded is not None:
    # persist to data/uploads/
    file_id = uuid.uuid4().hex[:12]
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_name = f"resp_{ts}_{file_id}.wav"
    saved_path = UPLOAD_DIR / saved_name
    saved_path.write_bytes(uploaded.getvalue())

    st.success(f"✅ File saved → `{saved_path.name}` ({len(uploaded.getvalue()) / 1024:.1f} KB)")

    # audio player
    st.subheader("🎧 Playback")
    st.audio(uploaded, format="audio/wav")

    st.divider()

    # ── inference ────────────────────────────────────────────────────────────
    st.subheader("🔬 Model Inference")
    with st.spinner("Running respiratory model inference …"):
        try:
            from ml.respiratory.inference.predict import respiratory_inference_service  # noqa: E402

            result = respiratory_inference_service.predict(str(saved_path))
        except Exception as exc:
            result = None
            st.error(f"⚠️ Inference failed: {exc}")

    if result is not None:
        payload = result.model_dump() if hasattr(result, "model_dump") else result
        predicted_class = payload.get("predicted_class", "Unknown")
        confidence = payload.get("confidence", 0.0)
        spectrogram_info = {
            "probabilities": payload.get("probabilities", {}),
            "cycles": payload.get("cycles", []),
            "narrative": payload.get("respllm_narrative"),
            "dataset_source": payload.get("dataset_source"),
            "device": payload.get("device"),
            "explanation": payload.get("explanation"),
        }

        colour = CLASS_COLOURS.get(predicted_class, "gray")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Predicted Class", predicted_class)
            st.markdown(
                f"<span style='color:{colour};font-weight:bold;font-size:1.4em'>"
                f"{predicted_class}</span>",
                unsafe_allow_html=True,
            )
        with col2:
            st.metric("Confidence", f"{confidence * 100:.1f} %")
            if confidence < 0.5:
                st.warning("Low confidence – consider re-recording or clinician review.")
        with col3:
            st.metric("File", saved_name)

        # confidence bar
        st.progress(min(confidence, 1.0), text=f"Confidence: {confidence * 100:.1f} %")

        # spectrogram details
        if spectrogram_info:
            with st.expander("📊 Spectrogram Details"):
                st.json(spectrogram_info)

        # full result payload
        with st.expander("📄 Raw inference result"):
            st.json(payload)
    else:
        st.info("ℹ️ No inference result available. Ensure the respiratory model checkpoint exists.")

else:
    st.info("👆 Upload a `.wav` lung-sound file to begin analysis.")

# ── ICBHI note ───────────────────────────────────────────────────────────────
st.divider()
with st.expander("📚 About the model & training data"):
    st.markdown("""
**ICBHI 2017 Respiratory Sound Database**

RespLLM is a local CNN–BiGRU with a closed-vocabulary decoder. It is trained on ICBHI 2017
only after that dataset is placed in `data/external/icbhi`. A synthetic smoke checkpoint, if present,
is labeled as such and is not an ICBHI result. Four acoustic classes are supported:

| Class | Description |
|-------|-------------|
| **Normal** | No adventitious sounds detected |
| **Crackle** | Discontinuous, explosive sounds |
| **Wheeze** | Continuous, musical sounds |
| **Both** | Crackles *and* wheezes present |

> **Minimum requirements for retraining:** The original ICBHI `.wav` files and the
> `patient_diagnosis.csv` metadata file must be placed under `data/icbhi/`.

*Reference:* Rocha BM et al., "An open access database for the evaluation of respiratory sound
classification algorithms", *Physiological Measurement*, 2019.
""")

# ── disclaimer ───────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "⚕️ **Disclaimer:** This AI prediction is advisory only and must NOT replace professional "
    "clinical auscultation. Always correlate with patient history, physical exam, and other diagnostics."
)
