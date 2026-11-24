# SwasthAI

**Hardware-Optimized, Privacy-Preserving, Neuro-Symbolic Multimodal Clinical Decision Support System (CDSS) for Rural Primary Healthpods**

[![CI](https://github.com/swasthai/swasthai/actions/workflows/ci.yml/badge.svg)](https://github.com/swasthai/swasthai/actions)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139-teal.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.66-red.svg)](https://streamlit.io)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)

---

## 📌 Executive Summary

**SwasthAI** is an offline-capable, multimodal multi-agent Clinical Decision Support System designed for deployment in rural primary healthpods (such as the Satnavari village healthpod in Maharashtra, India, following ITU-T Recommendation Y.4218).

It faithfully implements the research methodology proposed by **Aishani Bhatnagar (BIT Durg)**, **Bushra Ameen (BIT Durg)**, and **Santosh Kumar (IIIT-Naya Raipur)** in the research paper:

> *"SwasthAI: A Privacy-Preserving Neuro-Symbolic Multi-Agent AI Framework for Multimodal Diagnosis and Drug-Class Recommendation in Rural Healthpods"*

---

## 🏛️ System Architecture

SwasthAI implements an end-to-end Four-Stage Evidence Pipeline with an **Independent Deterministic Emergency Circuit Breaker**:

```
[Patient Ingestion]
        │
        ▼
[Privacy Scrubbing (Section 3.3)] ──> SHA-256 Hashing of Phone / Aadhaar (Zero Plaintext PHI)
        │
        ▼
[Modality-Specific Extraction Agents (Section 3.4)]
 ├── Symptom NLP (Bilingual English / Devanagari Hindi / Hinglish, Longest-Match + Ratcliff-Obershelp τ=0.90)
 ├── Laboratory Extractor (Regex + LOINC Standardization + Unit Normalization)
 ├── Respiratory Acoustic Agent (ICBHI 2017 Protocol, 64-Mel Filterbank, 768-dim Embedding CRNN)
 └── Radiology Vision Agent (DICOM Metadata Audit & Observation Extraction)
        │
        ▼
[Stage 3: Laboratory Triplet Resolution (Section 3.5)] ──> LOINC Mapping + Plausibility Interval Checking
        │
        ▼
[Stage 4: Deterministic Symbolic Safety Engine (Section 3.6 & Equation 3)]
        │
        ├────────────────────────────────────────┐
        ▼                                        ▼
[Normal / Warning Cases]               [Critical Physiological Anomaly]
        │                                        │
        ▼                                        ▼
[Verified Immutable EvidenceGraph]     [🚨 EMERGENCY CIRCUIT BREAKER HALTED]
  (SHA-256 Cryptographic Digest)                 │
        │                                        ├── Bypass Generative LLMs & RAG
        ▼                                        ├── Withhold Autonomous Drug Classes
[Local RAG (Section 3.7 & Equation 4)]           └── Output Immediate Emergency Escalation
  (ICMR, NVBDCP, RSSDI, ICS STGs, τ=0.35)             Protocols (Ambulance / Oxygen / ICCU)
        │
        ▼
[Diagnosis Agent (Section 3.8)] ──> (Temp=0.0 / Clinically Prioritized Deterministic Fallback)
        │
        ▼
[Drug-Class Recommendation Agent (Section 3.8)] ──> (Generic Classes Only, Zero Brand Names, Contraindication-Aware)
        │
        ▼
[Mandatory Licensed Clinician Attestation & Longitudinal SQLite EHR (Section 3.9)]
```

---

## 💻 Hardware Adaptation Profile

The system is rigorously benchmarked and adapted for a local developer / healthpod laptop:
- **Processor**: Intel Core i5 HX Series (10 cores, 16 threads)
- **Discrete GPU**: NVIDIA GeForce RTX 3050 Laptop GPU (6 GB GDDR6 VRAM, Compute 8.6)
- **Host RAM**: 24 GB DDR5-4800
- **Operating System**: Windows 11 / Linux compatible
- **VRAM Constraint**: Single-model sequential activation (< 5,000 MB VRAM cap) to guarantee zero out-of-memory crashes on consumer mobile GPUs.
- **Offline Guarantee**: All critical clinical pathways (Safety Engine, Symptom NLP, LOINC Resolver, Diagnostic Expert, Drug Agent) run with zero internet and zero remote cloud dependencies.

---

## Measured local results

These numbers come from commands run in this repository. They are not the paper’s Qwen2.5-14B run on two GTX 1080 Ti GPUs, and they are not ICBHI scores.

Clinical vignettes (`python -m backend.app.evaluation.evaluator`), deterministic agents, bundled 50 cases (41 Approved / 9 Rejected in this file, versus 42 / 8 in the paper’s Table 1):

| Metric | This run |
|---|---|
| Safety accuracy / macro-F1 | 100.00% / 100.00% (41 true approved, 9 true rejected) |
| Diagnosis accuracy / macro-F1 (substring match used by the evaluator) | 100.00% / 100.00% |
| Diagnosis multiclass macro-F1 (longest condition-name match) | 97.87% |
| Drug-class mean Jaccard | 97.00% |
| Vision accuracy | Not evaluated. No labeled image set is in the repo, and Qwen3-VL-32B is not loaded. |

Paper Table 2 targets remain 78.00% diagnosis accuracy, 86.00% safety accuracy, and 74.17% drug Jaccard. Matching or beating those targets here does not reproduce that experiment.

RespLLM smoke training, 25 epochs, synthetic tones, patient-disjoint holdout of 20 cycles, CPU: accuracy 1.00 and macro-F1 1.00. `dataset_source` is `synthetic_protocol_smoke`. That only shows the synthetic tones were separable. Official ICBHI training has not been run.

Tests: `py -3.14 -m pytest tests -q` → 48 passed.

Model choices, the CPU PyTorch build, and the ICBHI download steps are in `docs/MODEL_SELECTION.md` and `docs/ICBHI_SETUP.md`.

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Git

### 2. Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/swasthai/swasthai.git
cd swasthai

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-ml.txt
```

ICBHI 2017 is not downloaded automatically. See `docs/ICBHI_SETUP.md` before a real respiratory training run. A synthetic smoke check is:

```bash
python -c "from ml.respiratory.training.train import train_respiratory_model; train_respiratory_model(epochs=25, smoke_test=True, resume=False)"
```

### 3. Run the Streamlit Interactive Frontend (20 Workflows)
```bash
python -m streamlit run frontend/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

Pre-seeded Healthpod Accounts:
- **Clinician**: `dr.sharma` / `Clinician@2026`
- **ASHA Worker**: `asha.sunita` / `AshaWorker@2026`
- **ANM**: `anm.priya` / `AnmWorker@2026`
- **Telemed Technician**: `tech.rahul` / `Technician@2026`
- **Admin**: `admin` / `SwasthAdmin@2026`

### 4. Run the FastAPI REST Backend
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive OpenAPI Swagger docs available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 5. Run the Test Suite
```bash
python -m pytest tests/ -v
```

### 6. Run the 50-Vignette Clinical Benchmark
```bash
python -m backend.app.evaluation.evaluator
```

---

## 📁 Repository Structure

```
SwasthAI/
├── backend/
│   └── app/
│       ├── agents/              # Modality & reasoning agents
│       │   ├── symptom_agent/   # Bilingual exact + Ratcliff-Obershelp NLP
│       │   ├── lab_agent/       # Text parser
│       │   ├── lab_resolver/    # LOINC aliases, unit conversions, plausibility
│       │   ├── vision_agent/    # DICOM & radiology observation auditor
│       │   ├── diagnosis_agent/ # Multi-agent diagnostic reasoner
│       │   └── drug_agent/      # Generic drug recommender & contraindications
│       ├── api/                 # FastAPI routes (auth, patients, consultations, etc.)
│       ├── core/                # Settings, PBKDF2 auth, SHA-256 privacy scrubber
│       ├── db/                  # SQLite schema (14 tables, WAL mode, foreign keys)
│       ├── ehr/                 # Longitudinal EHR persistence service
│       ├── evaluation/          # 50 clinical vignettes benchmark & evaluator
│       ├── evidence/            # Immutable EvidenceGraph builder & hasher
│       ├── rag/                 # Local vector store & Indian STG guideline corpus
│       ├── reporting/           # Printable consultation report generator
│       ├── safety/              # Deterministic symbolic safety engine & circuit breaker
│       └── services/            # End-to-end 4-stage pipeline orchestrator
├── frontend/                    # Streamlit multi-page clinical portal (20 pages)
│   ├── app.py                   # Central healthpod hub
│   └── pages/                   # 20 distinct clinical & administrative pages
├── ml/
│   └── respiratory/             # Pure-NumPy Log-Mel preprocessing, CRNN model & training
├── data/
│   ├── generated/               # 500 synthetic encounter dataset (train/val/test)
│   └── uploads/                 # Local staged files
├── docs/                        # Specifications, hardware profile, requirements matrix
├── reports/                     # Benchmark evaluation results & clinical summaries
├── tests/                       # 13 test suites covering all modules (42 tests)
├── requirements.txt             # Pinned dependency specifications
└── LICENSE                      # Apache 2.0 with Clinical Disclaimer
```

---

## ⚖️ Statutory Medical & Research Disclaimer

**IMPORTANT NOTICE**: SwasthAI is an investigational software artifact developed for academic research purposes. It is designed solely as an advisory Clinical Decision Support System (CDSS) for trained primary health personnel (ASHAs, ANMs, and telemedicine operators). It does **NOT** provide autonomous medical diagnosis or issue independent prescriptions. All generated outputs must be reviewed, verified, and signed off by a licensed medical practitioner prior to clinical decision-making.
