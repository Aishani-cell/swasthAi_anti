"""
RAG Service Wrapper
Extracts clinical queries from EvidenceGraph and retrieves top-3 grounded guidelines.
"""
from typing import Dict, Any, List
from backend.app.schemas.evidence import EvidenceGraphModel
from backend.app.rag.vector_store import vector_store

class RAGService:
    @staticmethod
    def retrieve_guidelines(evidence_graph: EvidenceGraphModel, top_k: int = 3) -> Dict[str, Any]:
        """
        Builds a clinical query from positive symptoms and abnormal vitals/labs,
        then queries the local vector index under relevance threshold tau.
        """
        query_terms = []
        for s in evidence_graph.symptoms:
            query_terms.append(s.canonical_concept.replace('_', ' '))
            query_terms.append(s.original_phrase)

        for lab in evidence_graph.resolved_labs:
            if lab.plausibility_flag and lab.plausibility_flag != "NORMAL":
                query_terms.append(lab.canonical_name)

        if evidence_graph.vitals:
            v = evidence_graph.vitals
            if v.systolic_bp and v.systolic_bp >= 140:
                query_terms.append("hypertension blood pressure")
            if v.spo2 and v.spo2 < 94:
                query_terms.append("hypoxemia dyspnea oxygen")
            if v.temperature_c and v.temperature_c >= 38.0:
                query_terms.append("fever pyrexia")

        query_text = " ".join(query_terms)
        return vector_store.query(query_text, top_k=top_k)

rag_service = RAGService()
