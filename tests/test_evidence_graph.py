"""
Unit tests for Immutable EvidenceGraph Construction and Hashing (Section 3.7).
Verifies deterministic JSON serialization, SHA-256 integrity hash verification,
and text serialization for LLM grounding.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.schemas.vitals import VitalsInput
from backend.app.schemas.symptoms import SymptomExtractionResult
from backend.app.evidence.builder import build_evidence_graph, format_evidence_graph_text
from backend.app.evidence.serializer import serialize_evidence_graph, compute_graph_hash


class TestEvidenceGraph(unittest.TestCase):
    def test_build_and_hash_integrity(self):
        sym = SymptomExtractionResult(
            canonical_concept="cough",
            original_phrase="persistent cough",
            language="en",
            is_negated=False,
            extraction_method="LEXICON_EXACT",
            confidence_score=1.0
        )
        vit = VitalsInput(systolic_bp=120, diastolic_bp=80, heart_rate=72)
        eg = build_evidence_graph(
            encounter_id="enc-test-01",
            demographics={"age": 42, "sex": "FEMALE", "is_pregnant": False},
            symptoms=[sym],
            negated_symptoms=[],
            vitals=vit,
            vitals_classification={"blood_pressure": "Normal"},
            resolved_labs=[],
            imaging_findings=[],
            respiratory_finding=None,
            missing_modalities=["laboratory", "radiology"],
            safety_alerts=[],
            circuit_breaker_tripped=False
        )

        self.assertIsNotNone(eg.integrity_hash)
        self.assertEqual(len(eg.integrity_hash), 64)  # SHA-256 is 64 hex chars
        
        # Verify deterministic hash matches recomputation
        d = eg.model_dump()
        serialized = serialize_evidence_graph(d)
        recomputed = compute_graph_hash(serialized)
        self.assertEqual(eg.integrity_hash, recomputed)

    def test_format_evidence_graph_text(self):
        sym = SymptomExtractionResult(
            canonical_concept="fever",
            original_phrase="high fever",
            language="en",
            is_negated=False,
            extraction_method="LEXICON_EXACT",
            confidence_score=1.0
        )
        eg = build_evidence_graph(
            encounter_id="enc-test-02",
            demographics={"age": 28, "sex": "MALE", "is_pregnant": False},
            symptoms=[sym],
            negated_symptoms=[],
            vitals=VitalsInput(temperature_c=39.0),
            vitals_classification={"temperature": "Febrile"},
            resolved_labs=[],
            imaging_findings=[],
            respiratory_finding=None,
            missing_modalities=[],
            safety_alerts=[],
            circuit_breaker_tripped=False
        )
        txt = format_evidence_graph_text(eg)
        self.assertIn("fever", txt)
        self.assertIn("39.0", txt)


if __name__ == "__main__":
    unittest.main()
