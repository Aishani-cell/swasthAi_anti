"""
Unit tests for the SwasthAI Drug-Class Recommendation Agent (Section 3.8).
Tests Jaccard similarity calculation, guideline-directed generic drug class retrieval,
contraindication filtering (e.g., NSAID prohibition in dengue, pregnancy cautions),
and emergency circuit-breaker withholding.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.schemas.consultation import DiagnosisOutput
from backend.app.schemas.evidence import EvidenceGraphModel
from backend.app.schemas.symptoms import SymptomExtractionResult
from backend.app.evidence.builder import build_evidence_graph
from backend.app.agents.drug_agent.agent import drug_agent, compute_jaccard_similarity, RECOMMENDED_DRUG_CLASSES_DB


class TestDrugAgent(unittest.TestCase):
    def test_jaccard_computation(self):
        gold = ["Beta-lactam antibiotics", "Macrolides", "Antipyretics"]
        pred = ["Beta-lactam antibiotics", "Macrolides", "Antipyretics"]
        self.assertEqual(compute_jaccard_similarity(pred, gold), 1.0)

        disjoint = ["Loop diuretics", "ACE inhibitors"]
        self.assertEqual(compute_jaccard_similarity(disjoint, gold), 0.0)

        partial = ["Beta-lactam antibiotics", "Macrolides"]
        j = compute_jaccard_similarity(partial, gold)
        self.assertAlmostEqual(j, 2/3, places=2)

    def test_dengue_contraindication_filter(self):
        diag = DiagnosisOutput(
            primary_diagnosis="Dengue",
            differential_diagnoses=[],
            evidence_citations=[],
            guideline_citations=[],
            missing_data_warnings=[],
            conditional_laboratory_findings=[],
            model_version="test",
            physician_review_mandatory=True
        )
        eg = build_evidence_graph(
            encounter_id="enc-dengue-drug",
            demographics={"age": 25, "sex": "MALE", "is_pregnant": False},
            symptoms=[], negated_symptoms=[], vitals=None, vitals_classification={},
            resolved_labs=[], imaging_findings=[], respiratory_finding=None,
            missing_modalities=[], safety_alerts=[], circuit_breaker_tripped=False
        )
        rec = drug_agent.recommend_drug_classes(diag, eg)
        self.assertIn("Antipyretics (Paracetamol only)", rec.generic_drug_classes)
        # Verify no NSAIDs are recommended
        for drug in rec.generic_drug_classes:
            self.assertNotIn("nsaid", drug.lower())
            self.assertNotIn("aspirin", drug.lower())
            self.assertNotIn("ibuprofen", drug.lower())

    def test_circuit_breaker_blocks_drugs(self):
        diag = DiagnosisOutput(
            primary_diagnosis="STEMI",
            differential_diagnoses=[],
            evidence_citations=[],
            guideline_citations=[],
            missing_data_warnings=[],
            conditional_laboratory_findings=[],
            model_version="test",
            physician_review_mandatory=True
        )
        eg = build_evidence_graph(
            encounter_id="enc-stemi-drug",
            demographics={"age": 60, "sex": "MALE", "is_pregnant": False},
            symptoms=[], negated_symptoms=[], vitals=None, vitals_classification={},
            resolved_labs=[], imaging_findings=[], respiratory_finding=None,
            missing_modalities=[], safety_alerts=[], circuit_breaker_tripped=True
        )
        rec = drug_agent.recommend_drug_classes(diag, eg)
        self.assertEqual(len(rec.generic_drug_classes), 0)
        self.assertTrue(rec.physician_review_mandatory)
        self.assertTrue(any("blocked" in f.lower() for f in rec.contraindication_flags))


if __name__ == "__main__":
    unittest.main()
