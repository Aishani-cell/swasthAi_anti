"""
EvidenceGraph Deterministic Serializer and Cryptographic Hasher
Ensures immutable snapshots and tamper-traceability.
"""
import json
import hashlib
from typing import Dict, Any

def serialize_evidence_graph(graph_dict: Dict[str, Any]) -> str:
    """
    Deterministically serializes the EvidenceGraph dictionary to a sorted-key JSON string.
    """
    # Exclude dynamic/volatile hash field itself during hash generation
    clean_dict = {k: v for k, v in graph_dict.items() if k != "integrity_hash"}
    return json.dumps(clean_dict, sort_keys=True, ensure_ascii=False, default=str)

def compute_graph_hash(serialized_json: str) -> str:
    """Computes SHA-256 digest of the serialized canonical EvidenceGraph."""
    return hashlib.sha256(serialized_json.encode('utf-8')).hexdigest()
