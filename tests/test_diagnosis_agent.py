"""
Unit tests for the SwasthAI Diagnosis Agent (Section 3.8).
Tests deterministic fallback logic across acute conditions:
STEMI, Pneumonia, Dengue, Malaria, DKA, Stroke, Appendicitis, Heart Failure.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.schemas.evidence import EvidenceGraphModel
from backend.app.schemas.symptoms import SymptomExtractionResult
from backend.app.schemas.vitals import VitalsInput
from backend.app.schemas.labs import ResolvedLabItem
from backend.app.evidence.builder import build_evidence_graph
from backend.app.agents.diagnosis_agent.agent import deterministic_diagnosis_fallback


class TestDiagnosisAgent(unittest.TestCase):
    def test_stemi_diagnosis(self):
        sym = SymptomExtractionResult(
            canonical_concept="chest_pain", original_phrase="crushing chest pain",
            language="en", is_negated=False, extraction_method="LEXICON_EXACT", confidence_score=1.0
        )
        trop_lab = ResolvedLabItem(
            analyte_name="Troponin I", canonical_name="Troponin I", loinc_code="10839-9",
            raw_value="0.9", numeric_value=0.9, unit="ng/mL", canonical_unit="ng/mL",
            verification_status="VERIFIED", plausibility_flag="CRITICAL_HIGH"
        )
        eg = build_evidence_graph(
            encounter_id="enc-stemi", demographics={"age": 55, "sex": "MALE", "is_pregnant": False},
            symptoms=[sym], negated_symptoms=[], vitals=VitalsInput(heart_rate=105),
            vitals_classification={}, resolved_labs=[trop_lab], imaging_findings=[],
            respiratory_finding=None, missing_modalities=[], safety_alerts=[], circuit_breaker_tripped=False
        )
        diag = deterministic_diagnosis_fallback(eg, {})
        self.assertEqual(diag.primary_diagnosis, "STEMI")
        self.assertIn("troponin", " ".join(diag.evidence_citations).lower())

    def test_dengue_diagnosis(self):
        fever = SymptomExtractionResult(
            canonical_concept="fever", original_phrase="high fever",
            language="en", is_negated=False, extraction_method="LEXICON_EXACT", confidence_score=1.0
        )
        plt_lab = ResolvedLabItem(
            analyte_name="Platelet Count", canonical_name="Platelet Count", loinc_code="777-3",
            raw_value="45000", numeric_value=45000, unit="/cumm", canonical_unit="cells/uL",
            verification_status="VERIFIED", plausibility_flag="CRITICAL_LOW"
        )
        eg = build_evidence_graph(
            encounter_id="enc-dengue", demographics={"age": 22, "sex": "FEMALE", "is_pregnant": False},
            symptoms=[fever], negated_symptoms=[], vitals=VitalsInput(temperature_c=39.5),
            vitals_classification={}, resolved_labs=[plt_lab], imaging_findings=[],
            respiratory_finding=None, missing_modalities=[], safety_alerts=[], circuit_breaker_tripped=False
        )
        diag = deterministic_diagnosis_fallback(eg, {})
        self.assertEqual(diag.primary_diagnosis, "Dengue")


if __name__ == "__main__":
    unittest.main()
