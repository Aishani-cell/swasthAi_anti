"""
Deterministic Drug-Class Contraindication and Interaction Engine
Enforces patient safety rules based on pregnancy, renal markers, and thrombocytopenia.
"""
from typing import List, Dict, Any, Tuple
from backend.app.schemas.evidence import EvidenceGraphModel

def check_contraindications(
    drug_class: str,
    evidence_graph: EvidenceGraphModel,
    patient_allergies: List[str] = None
) -> Tuple[bool, List[str]]:
    """
    Evaluates whether a candidate generic drug class is contraindicated.
    Returns: (is_contraindicated, reasons)
    """
    reasons = []
    d_lower = drug_class.lower()
    allergies = [a.lower() for a in (patient_allergies or [])]
    is_preg = evidence_graph.demographics.get("is_pregnant", False)

    # 1. Allergy check
    for a in allergies:
        if a in d_lower or d_lower in a:
            reasons.append(f"Patient has documented allergy to {drug_class} ({a}).")

    # 2. Pregnancy Contraindications
    if is_preg:
        if any(w in d_lower for w in ["ace inhibitor", "angiotensin receptor blocker", "arb", "statin", "tetracycline", "fluoroquinolone", "methotrexate"]):
            reasons.append(f"{drug_class} is strictly teratogenic / contraindicated during pregnancy.")

    # 3. Thrombocytopenia / Dengue Bleeding Risk
    labs = {l.canonical_name.lower(): l for l in evidence_graph.resolved_labs}
    is_thrombocytopenic = any("platelet" in k and l.numeric_value and l.numeric_value < 100000 for k, l in labs.items())
    if is_thrombocytopenic or any("dengue" in s.canonical_concept for s in evidence_graph.symptoms):
        if any(w in d_lower for w in ["nsaid", "non-steroidal anti-inflammatory", "aspirin", "ibuprofen", "diclofenac"]):
            reasons.append("NSAIDs strictly contraindicated in suspected dengue / low platelets due to fatal hemorrhagic risk.")

    # 4. Acute Kidney Injury (Creatinine > 1.5)
    is_renal_impaired = any("creatinine" in k and l.numeric_value and l.numeric_value > 1.5 for k, l in labs.items())
    if is_renal_impaired:
        if any(w in d_lower for w in ["nsaid", "aminoglycoside", "potassium-sparing diuretic"]):
            reasons.append(f"Nephrotoxic drug {drug_class} contraindicated in acute renal impairment.")

    return len(reasons) > 0, reasons
