# SwasthAI Synthetic Data & Ground-Truth Policy

## 1. Ground-Truth Integrity Principles

In strict accordance with clinical AI research standards, SwasthAI maintains **rigorous separation** across four distinct classes of data labels:

1. **Synthetic Deterministic Test Expectations**:
   - Expectations derived from explicitly coded rule systems, guideline tables, and synthetic test suites.
   - Purpose: Software unit and integration testing.
   - Clinical Claim: **Zero**. These are verification expectations, not clinical validations.

2. **Human-Reviewed Clinical Annotations**:
   - Data points examined, confirmed, and signed off by a licensed human physician.
   - Clearly labeled with `human_review_status = VERIFIED` and clinician ID.

3. **Real Benchmark Dataset Annotations**:
   - Legitimate external benchmark annotations (e.g., official ICBHI 2017 audio cycle annotations).
   - Provenance, license, and official challenge splits are strictly recorded.

4. **Model-Generated Predictions**:
   - Outputs produced by the Diagnosis Agent, Drug Recommendation Agent, or CRNN Acoustic model.
   - Never stored as ground truth; stored separately as advisory decision-support hypotheses.

---

## 2. Prohibition Against Contamination & Leakage
- **No Test-Set Tuning**: Test splits must never be used for prompt tuning, threshold calibration, or model training.
- **Patient-Grouped Splitting**: All multi-cycle recordings or longitudinal encounters from the same patient identifier are constrained to a single partition (`train` OR `test`).
- **Traceability**: Every record in `data/generated/` retains a `data_provenance` metadata field identifying the generation script and pipeline version.
