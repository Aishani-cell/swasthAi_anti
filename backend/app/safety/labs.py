"""
Laboratory Safety Rule Evaluation
Deterministic panic-threshold evaluation for resolved laboratory markers.
"""
from typing import List, Tuple
from backend.app.schemas.labs import ResolvedLabItem
from backend.app.schemas.evidence import SafetyAlert
from backend.app.safety.rules import CRITICAL_SAFETY_RULES, WARNING_SAFETY_RULES, RULES_VERSION

def evaluate_labs_safety(labs: List[ResolvedLabItem]) -> Tuple[List[SafetyAlert], bool]:
    """
    Evaluates resolved lab items against deterministic critical rules.
    Returns: (alerts, circuit_breaker_triggered)
    """
    alerts: List[SafetyAlert] = []
    tripped = False

    for item in labs:
        val = item.numeric_value
        if val is None or item.verification_status != "VERIFIED":
            continue

        cname = item.canonical_name.lower()
        loinc = item.loinc_code

        # 1. Platelets < 50,000 /cumm
        if loinc == "777-3" or "platelet" in cname:
            if val < 50000.0:
                rule = CRITICAL_SAFETY_RULES["RULE_LAB_PLATELETS_PANIC"]
                alerts.append(SafetyAlert(
                    rule_id=rule["rule_id"],
                    ruleset_version=RULES_VERSION,
                    severity=rule["severity"],
                    observed_value=f"Platelets={val:.0f} {item.canonical_unit}",
                    threshold="Platelets < 50,000 cells/uL",
                    circuit_breaker_halted=True,
                    escalation_instructions=rule["escalation_instructions"],
                    explanation=f"Critical thrombocytopenia ({val:.0f} cells/uL) carries high hemorrhagic shock risk."
                ))
                tripped = True

        # 2. Potassium < 2.8 or >= 6.5 mEq/L
        elif loinc == "2823-3" or "potassium" in cname:
            if val < 2.8 or val >= 6.5:
                rule = CRITICAL_SAFETY_RULES["RULE_LAB_POTASSIUM_PANIC"]
                alerts.append(SafetyAlert(
                    rule_id=rule["rule_id"],
                    ruleset_version=RULES_VERSION,
                    severity=rule["severity"],
                    observed_value=f"Potassium={val} {item.canonical_unit}",
                    threshold="K+ < 2.8 or >= 6.5 mEq/L",
                    circuit_breaker_halted=True,
                    escalation_instructions=rule["escalation_instructions"],
                    explanation=f"Critical potassium level ({val} mEq/L) carries severe lethal cardiac arrhythmia risk."
                ))
                tripped = True

        # 3. Troponin I >= 0.4 ng/mL
        elif loinc == "10839-9" or "troponin" in cname:
            if val >= 0.4:
                rule = CRITICAL_SAFETY_RULES["RULE_LAB_TROPONIN_STEMI"]
                alerts.append(SafetyAlert(
                    rule_id=rule["rule_id"],
                    ruleset_version=RULES_VERSION,
                    severity=rule["severity"],
                    observed_value=f"Troponin I={val} {item.canonical_unit}",
                    threshold="Troponin I >= 0.4 ng/mL",
                    circuit_breaker_halted=True,
                    escalation_instructions=rule["escalation_instructions"],
                    explanation=f"Elevated cardiac troponin ({val} ng/mL) indicates acute myocardial infarction / STEMI."
                ))
                tripped = True

        # 4. Glucose >= 400 mg/dL
        elif loinc in ["1558-6", "2345-7"] or "glucose" in cname or "sugar" in cname:
            if val >= 400.0:
                rule = CRITICAL_SAFETY_RULES["RULE_LAB_GLUCOSE_CRITICAL"]
                alerts.append(SafetyAlert(
                    rule_id=rule["rule_id"],
                    ruleset_version=RULES_VERSION,
                    severity=rule["severity"],
                    observed_value=f"Glucose={val} {item.canonical_unit}",
                    threshold="Glucose >= 400 mg/dL",
                    circuit_breaker_halted=True,
                    escalation_instructions=rule["escalation_instructions"],
                    explanation=f"Extreme hyperglycemia ({val} mg/dL) indicative of diabetic ketoacidosis crisis."
                ))
                tripped = True

        # 5. Serum Creatinine > 1.5 mg/dL (Warning)
        elif loinc == "2160-0" or "creatinine" in cname:
            if val > 1.5:
                rule = WARNING_SAFETY_RULES["RULE_LAB_CREATININE_ELEVATED"]
                alerts.append(SafetyAlert(
                    rule_id=rule["rule_id"],
                    ruleset_version=RULES_VERSION,
                    severity=rule["severity"],
                    observed_value=f"Creatinine={val} {item.canonical_unit}",
                    threshold="Creatinine > 1.5 mg/dL",
                    circuit_breaker_halted=False,
                    escalation_instructions=rule["escalation_instructions"],
                    explanation=f"Elevated creatinine ({val} mg/dL) signals impaired renal filtration."
                ))

    return alerts, tripped
