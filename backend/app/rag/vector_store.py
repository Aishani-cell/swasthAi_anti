"""
Lightweight Vector Store and Cosine Similarity Index
Implements Section 3.7 & Equation 4 from the SwasthAI paper:
sim(q, ci) = (q . ci) / (||q|| ||ci||)
retrieve ci iff 1 - sim(q, ci) <= tau
Top-3 retrieval with explicit 'retrieval_status = unavailable' when below threshold.
"""
import math
import re
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.rag.knowledge_base import CLINICAL_GUIDELINE_CORPUS

def tokenize(text: str) -> List[str]:
    """Extracts alphanumeric words from text."""
    return re.findall(r'\b[a-z0-9]{2,}\b', text.lower())

def compute_tf_vector(tokens: List[str], vocabulary: Dict[str, int]) -> List[float]:
    """Computes normalized term-frequency vector."""
    vec = [0.0] * len(vocabulary)
    for t in tokens:
        if t in vocabulary:
            vec[vocabulary[t]] += 1.0
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes dot product of normalized vectors."""
    return sum(a * b for a, b in zip(v1, v2))

class LocalVectorIndex:
    def __init__(self, tau: float = None):
        self.tau = tau or settings.RAG_DISTANCE_THRESHOLD
        self.documents: List[Dict[str, Any]] = []
        self.vocabulary: Dict[str, int] = {}
        self.doc_vectors: List[List[float]] = []
        self._build_index()

    def _build_index(self):
        """Builds vocabulary and precomputes document vectors."""
        self.documents = CLINICAL_GUIDELINE_CORPUS.copy()
        vocab_set = set()
        tokenized_docs = []
        for doc in self.documents:
            full_text = f"{doc['doc_title']} {doc['condition']} {' '.join(doc['keywords'])} {doc['content_text']}"
            tokens = tokenize(full_text)
            tokenized_docs.append(tokens)
            vocab_set.update(tokens)

        self.vocabulary = {word: idx for idx, word in enumerate(sorted(vocab_set))}
        self.doc_vectors = [compute_tf_vector(toks, self.vocabulary) for toks in tokenized_docs]

    def query(self, query_text: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Retrieves top_k chunks where 1 - sim(q, ci) <= tau.
        Returns: {
            'retrieval_status': 'available' | 'unavailable',
            'chunks': [...],
            'citations': [...],
            'distance_threshold': tau
        }
        """
        q_tokens = tokenize(query_text)
        if not q_tokens:
            return {
                "retrieval_status": "unavailable",
                "reason": "Empty query tokens",
                "chunks": [],
                "citations": [],
                "distance_threshold": self.tau
            }

        q_vec = compute_tf_vector(q_tokens, self.vocabulary)
        scores = []
        for idx, d_vec in enumerate(self.doc_vectors):
            sim = cosine_similarity(q_vec, d_vec)
            dist = 1.0 - sim
            scores.append((dist, sim, idx))

        # Sort by distance ascending (similarity descending)
        scores.sort(key=lambda x: x[0])

        valid_chunks = []
        citations = []
        for dist, sim, idx in scores[:top_k]:
            if dist <= self.tau:
                doc = self.documents[idx]
                chunk_info = {
                    "doc_title": doc["doc_title"],
                    "publisher": doc["publisher"],
                    "year": doc["year"],
                    "page": doc["page"],
                    "section": doc["section"],
                    "condition": doc["condition"],
                    "content_snippet": doc["content_text"][:250] + "...",
                    "full_content": doc["content_text"],
                    "cosine_similarity": round(sim, 4),
                    "distance": round(dist, 4)
                }
                valid_chunks.append(chunk_info)
                citations.append(f"[{doc['publisher']} {doc['year']}, p. {doc['page']}] {doc['doc_title']}")

        if valid_chunks:
            return {
                "retrieval_status": "available",
                "chunks": valid_chunks,
                "citations": citations,
                "distance_threshold": self.tau
            }
        else:
            return {
                "retrieval_status": "unavailable",
                "reason": f"No guideline chunks met relevance distance threshold (dist <= {self.tau})",
                "chunks": [],
                "citations": [],
                "distance_threshold": self.tau
            }

vector_store = LocalVectorIndex()
