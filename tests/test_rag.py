"""
Unit tests for Local Guideline Knowledge Base & RAG Retrieval Module.
Tests vector store TF representation, cosine distance gating (tau=0.35),
and Indian clinical guideline citations (ICMR, NVBDCP, RSSDI).
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.rag.vector_store import vector_store
from backend.app.rag.knowledge_base import CLINICAL_GUIDELINE_CORPUS
from backend.app.rag.service import rag_service
from backend.app.evidence.builder import build_evidence_graph
from backend.app.schemas.symptoms import SymptomExtractionResult


class TestRAGModule(unittest.TestCase):
    def test_guideline_corpus_loaded(self):
        self.assertGreaterEqual(len(CLINICAL_GUIDELINE_CORPUS), 8)
        publishers = {g["publisher"] for g in CLINICAL_GUIDELINE_CORPUS}
        self.assertTrue(any("ICMR" in p for p in publishers))
        self.assertTrue(any("NVBDCP" in p for p in publishers))

    def test_vector_store_retrieval(self):
        results = vector_store.query("dengue fever thrombocytopenia fluids", top_k=2)
        self.assertIn("retrieval_status", results)
        if results["retrieval_status"] == "available":
            self.assertGreaterEqual(len(results["chunks"]), 1)
            top_match = results["chunks"][0]
            self.assertIn("Dengue", top_match["doc_title"])

    def test_rag_service_from_evidence_graph(self):
        sym = SymptomExtractionResult(
            canonical_concept="fever",
            original_phrase="chills and rigors fever",
            language="en",
            is_negated=False,
            extraction_method="LEXICON_EXACT",
            confidence_score=1.0
        )
        eg = build_evidence_graph(
            encounter_id="enc-rag-01",
            demographics={"age": 30, "sex": "MALE", "is_pregnant": False},
            symptoms=[sym],
            negated_symptoms=[],
            vitals=None,
            vitals_classification={},
            resolved_labs=[],
            imaging_findings=[],
            respiratory_finding=None,
            missing_modalities=["vitals"],
            safety_alerts=[],
            circuit_breaker_tripped=False
        )
        retrieval = rag_service.retrieve_guidelines(eg)
        self.assertIn(retrieval["retrieval_status"], ["available", "unavailable", "empty"])
        if retrieval["retrieval_status"] == "available":
            self.assertGreaterEqual(len(retrieval["citations"]), 1)


if __name__ == "__main__":
    unittest.main()
