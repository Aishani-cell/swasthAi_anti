"""
Deterministic LOINC Laboratory Resolver
Implements Section 3.5 of the SwasthAI paper:
- Triplet verification: Analyte identity -> Unit consistency -> Physiological plausibility
- Statuses: VERIFIED, NEEDS_REVIEW, UNRESOLVED, INVALID_UNIT, IMPLAUSIBLE, INCOMPLETE
"""
import difflib
import re
from typing import Dict, Any, Optional, Tuple
from backend.app.schemas.labs import ExtractedLabItem, ResolvedLabItem
from backend.app.agents.lab_resolver.aliases import LAB_REFERENCE_REGISTRY
from backend.app.agents.lab_resolver.unit_converter import convert_to_canonical_unit
from backend.app.agents.lab_resolver.plausibility import check_plausibility

def clean_analyte_name(name: str) -> str:
    """Cleans test names, stripping common noise characters."""
    c = name.lower().strip()
    c = re.sub(r'[\(\)\[\]:;,\*\-_]+', ' ', c)
    return re.sub(r'\s+', ' ', c).strip()

def match_analyte(raw_name: str) -> Tuple[Optional[str], float]:
    """
    Finds best matching registry key for an extracted analyte name.
    First exact alias match, then Ratcliff-Obershelp fuzzy match (threshold 0.85).
    """
    cleaned = clean_analyte_name(raw_name)
    if not cleaned:
        return None, 0.0

    # 1. Exact alias match
    for key, spec in LAB_REFERENCE_REGISTRY.items():
        if cleaned in spec["aliases"] or cleaned == spec["canonical_name"].lower():
            return key, 1.0

    # 2. Substring match for compound strings (e.g. "complete blood count - platelets")
    for key, spec in LAB_REFERENCE_REGISTRY.items():
        for alias in spec["aliases"]:
            if alias in cleaned:
                return key, 0.95

    # 3. Fuzzy match
    best_key = None
    best_score = 0.0
    for key, spec in LAB_REFERENCE_REGISTRY.items():
        for alias in spec["aliases"]:
            score = difflib.SequenceMatcher(None, cleaned, alias).ratio()
            if score > 0.85 and score > best_score:
                best_score = score
                best_key = key

    return best_key, round(best_score, 2)

def resolve_lab_item(item: ExtractedLabItem) -> ResolvedLabItem:
    """
    Executes the full deterministic triplet verification on an extracted lab item.
    """
    raw_name = item.analyte_name.strip()
    raw_val_str = str(item.raw_value).strip()

    # Parse numeric value if not already given
    numeric_val = item.numeric_value
    if numeric_val is None:
        # Extract first float/int from string
        val_match = re.search(r'[-+]?\d*\.?\d+', raw_val_str.replace(',', ''))
        if val_match:
            try:
                numeric_val = float(val_match.group(0))
            except ValueError:
                numeric_val = None

    if numeric_val is None:
        return ResolvedLabItem(
            analyte_name=raw_name,
            canonical_name=raw_name,
            loinc_code=None,
            raw_value=raw_val_str,
            numeric_value=None,
            unit=item.unit,
            canonical_unit=None,
            reference_interval=item.reference_interval,
            verification_status="INCOMPLETE",
            plausibility_flag=None,
            notes="Could not extract numeric measurement value."
        )

    # Triplet 1: Analyte Identity
    matched_key, match_conf = match_analyte(raw_name)
    if not matched_key:
        return ResolvedLabItem(
            analyte_name=raw_name,
            canonical_name=raw_name,
            loinc_code=None,
            raw_value=raw_val_str,
            numeric_value=numeric_val,
            unit=item.unit,
            canonical_unit=item.unit,
            reference_interval=item.reference_interval,
            verification_status="UNRESOLVED",
            plausibility_flag=None,
            notes="Analyte not recognized in primary healthpod reference database."
        )

    spec = LAB_REFERENCE_REGISTRY[matched_key]
    canonical_name = spec["canonical_name"]
    loinc_code = spec["loinc_code"]

    # Triplet 2: Unit Consistency & Conversion
    conv_value, canonical_unit, valid_unit = convert_to_canonical_unit(
        matched_key,
        numeric_val,
        item.unit
    )

    if not valid_unit:
        return ResolvedLabItem(
            analyte_name=raw_name,
            canonical_name=canonical_name,
            loinc_code=loinc_code,
            raw_value=raw_val_str,
            numeric_value=numeric_val,
            unit=item.unit,
            canonical_unit=spec["canonical_unit"],
            reference_interval=item.reference_interval,
            verification_status="INVALID_UNIT",
            plausibility_flag=None,
            notes=f"Unit '{item.unit}' is incompatible with expected {spec['canonical_unit']}."
        )

    # Triplet 3: Physiological Plausibility & Survival Bounds
    is_plausible, flag, explanation = check_plausibility(matched_key, conv_value)
    if not is_plausible:
        return ResolvedLabItem(
            analyte_name=raw_name,
            canonical_name=canonical_name,
            loinc_code=loinc_code,
            raw_value=raw_val_str,
            numeric_value=conv_value,
            unit=canonical_unit,
            canonical_unit=canonical_unit,
            reference_interval=item.reference_interval,
            verification_status="IMPLAUSIBLE",
            plausibility_flag="IMPLAUSIBLE",
            notes=explanation
        )

    # All triplets passed
    return ResolvedLabItem(
        analyte_name=raw_name,
        canonical_name=canonical_name,
        loinc_code=loinc_code,
        raw_value=raw_val_str,
        numeric_value=conv_value,
        unit=canonical_unit,
        canonical_unit=canonical_unit,
        reference_interval=item.reference_interval or f"{spec['ref_min']}-{spec['ref_max']}",
        verification_status="VERIFIED",
        plausibility_flag=flag,
        notes=explanation
    )
