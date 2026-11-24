"""
Laboratory Biological Plausibility and Survival Bounds Verification
Implements deterministic plausibility checking from Section 3.5 of the paper.
"""
from typing import Dict, Any, Tuple
from backend.app.agents.lab_resolver.aliases import LAB_REFERENCE_REGISTRY

def check_plausibility(test_key: str, value: float) -> Tuple[bool, str, str]:
    """
    Checks if a lab value falls within survival bounds and clinical reference intervals.
    Returns: (is_plausible, classification_flag, explanation)
    """
    if test_key not in LAB_REFERENCE_REGISTRY:
        return True, "UNKNOWN_ANALYTE", "Analyte not in reference bounds database."

    spec = LAB_REFERENCE_REGISTRY[test_key]
    p_min = spec["plausible_min"]
    p_max = spec["plausible_max"]
    ref_min = spec["ref_min"]
    ref_max = spec["ref_max"]
    crit_low = spec.get("critical_low")
    crit_high = spec.get("critical_high")

    # 1. Biological Survival Bounds Check
    if (p_min is not None and value < p_min) or (p_max is not None and value > p_max):
        return False, "IMPLAUSIBLE", f"Value {value} is outside human biological survival bounds [{p_min}, {p_max}]."

    # 2. Critical High / Critical Low (Life-threatening)
    if crit_high is not None and value >= crit_high:
        return True, "CRITICAL_HIGH", f"Value {value} exceeds critical panic threshold ({crit_high} {spec['canonical_unit']})."
    if crit_low is not None and value <= crit_low:
        return True, "CRITICAL_LOW", f"Value {value} below critical panic threshold ({crit_low} {spec['canonical_unit']})."

    # 3. Standard Abnormal / Normal Bounds
    if ref_max is not None and value > ref_max:
        return True, "HIGH", f"Value {value} is elevated above standard reference upper limit ({ref_max})."
    if ref_min is not None and value < ref_min:
        return True, "LOW", f"Value {value} is below standard reference lower limit ({ref_min})."

    return True, "NORMAL", f"Value {value} is within normal reference interval [{ref_min}, {ref_max}]."
