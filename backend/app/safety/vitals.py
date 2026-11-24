"""
Vital Signs Safety Rule Evaluation
Implements Section 3.6 & Equation 3 from the SwasthAI paper.
"""
from typing import Optional, List, Dict, Any, Tuple
from backend.app.schemas.vitals import VitalsInput
from backend.app.schemas.evidence import SafetyAlert
from backend.app.safety.rules import CRITICAL_SAFETY_RULES, WARNING_SAFETY_RULES, RULES_VERSION

def evaluate_vitals_safety(
    vitals: Optional[VitalsInput],
    age: Optional[int] = None,
    is_pregnant: bool = False
) -> Tuple[List[SafetyAlert], Dict[str, str], bool]:
    """
    Evaluates vitals deterministically without LLM.
    Returns: (alerts, classifications, circuit_breaker_triggered)
    """
    alerts: List[SafetyAlert] = []
    classifications: Dict[str, str] = {}
    tripped = False

    if not vitals:
        return alerts, classifications, tripped

    sbp = vitals.systolic_bp
    dbp = vitals.diastolic_bp
    hr = vitals.heart_rate
    spo2 = vitals.spo2
    temp = vitals.temperature_c

    # 1. Blood Pressure Staging (Equation 3)
    if sbp is not None and dbp is not None:
        if sbp >= 180 or dbp >= 120:
            bp_status = "Hypertensive crisis"
            classifications["blood_pressure"] = bp_status
            rule = CRITICAL_SAFETY_RULES["RULE_VIT_BP_CRISIS"]
            alerts.append(SafetyAlert(
                rule_id=rule["rule_id"],
                ruleset_version=RULES_VERSION,
                severity=rule["severity"],
                observed_value=f"SBP={sbp}, DBP={dbp} mmHg",
                threshold="SBP >= 180 or DBP >= 120",
                circuit_breaker_halted=True,
                escalation_instructions=rule["escalation_instructions"],
                explanation=f"Patient in hypertensive crisis ({sbp}/{dbp} mmHg)."
            ))
            tripped = True
        elif sbp >= 140 or dbp >= 90:
            bp_status = "Stage 2 Hypertension"
            classifications["blood_pressure"] = bp_status
            rule = WARNING_SAFETY_RULES["RULE_VIT_BP_STAGE2"]
            alerts.append(SafetyAlert(
                rule_id=rule["rule_id"],
                ruleset_version=RULES_VERSION,
                severity=rule["severity"],
                observed_value=f"SBP={sbp}, DBP={dbp} mmHg",
                threshold="SBP >= 140 or DBP >= 90",
                circuit_breaker_halted=False,
                escalation_instructions=rule["escalation_instructions"],
                explanation=f"Blood pressure indicates Stage 2 hypertension ({sbp}/{dbp} mmHg)."
            ))
        elif (120 <= sbp < 130) and dbp < 80:
            bp_status = "Elevated"
            classifications["blood_pressure"] = bp_status
        elif sbp < 120 and dbp < 80:
            bp_status = "Normal"
            classifications["blood_pressure"] = bp_status
        else:
            bp_status = "Stage 1 Hypertension"
            classifications["blood_pressure"] = bp_status

    # 2. Oxygen Saturation (SpO2)
    if spo2 is not None:
        if spo2 < 90.0:
            classifications["oxygenation"] = "Critical Hypoxemia"
            rule = CRITICAL_SAFETY_RULES["RULE_VIT_SPO2_CRITICAL"]
            alerts.append(SafetyAlert(
                rule_id=rule["rule_id"],
                ruleset_version=RULES_VERSION,
                severity=rule["severity"],
                observed_value=f"SpO2={spo2}%",
                threshold="SpO2 < 90%",
                circuit_breaker_halted=True,
                escalation_instructions=rule["escalation_instructions"],
                explanation=f"Critical arterial desaturation (SpO2 {spo2}%)."
            ))
            tripped = True
        elif spo2 < 94.0:
            classifications["oxygenation"] = "Mild/Moderate Hypoxemia"
            rule = WARNING_SAFETY_RULES["RULE_VIT_SPO2_MILD"]
            alerts.append(SafetyAlert(
                rule_id=rule["rule_id"],
                ruleset_version=RULES_VERSION,
                severity=rule["severity"],
                observed_value=f"SpO2={spo2}%",
                threshold="SpO2 < 94%",
                circuit_breaker_halted=False,
                escalation_instructions=rule["escalation_instructions"],
                explanation=f"Reduced oxygen saturation (SpO2 {spo2}%)."
            ))
        else:
            classifications["oxygenation"] = "Normal"

    # 3. Heart Rate / Pulse
    if hr is not None:
        if hr < 40.0 or hr > 150.0:
            classifications["pulse"] = "Critical Arrhythmia / Extreme Rate"
            rule = CRITICAL_SAFETY_RULES["RULE_VIT_HR_CRITICAL"]
            alerts.append(SafetyAlert(
                rule_id=rule["rule_id"],
                ruleset_version=RULES_VERSION,
                severity=rule["severity"],
                observed_value=f"Heart Rate={hr} bpm",
                threshold="HR < 40 or HR > 150",
                circuit_breaker_halted=True,
                escalation_instructions=rule["escalation_instructions"],
                explanation=f"Life-threatening heart rate extremes ({hr} bpm)."
            ))
            tripped = True
        elif hr > 100.0:
            classifications["pulse"] = "Tachycardia"
        elif hr < 60.0:
            classifications["pulse"] = "Bradycardia"
        else:
            classifications["pulse"] = "Normal"

    # 4. Temperature
    if temp is not None:
        if temp >= 40.0:
            classifications["temperature"] = "Hyperpyrexia"
            rule = CRITICAL_SAFETY_RULES["RULE_VIT_TEMP_HYPERPYREXIA"]
            alerts.append(SafetyAlert(
                rule_id=rule["rule_id"],
                ruleset_version=RULES_VERSION,
                severity=rule["severity"],
                observed_value=f"Temperature={temp}°C",
                threshold="Temp >= 40.0°C",
                circuit_breaker_halted=True,
                escalation_instructions=rule["escalation_instructions"],
                explanation=f"Hyperpyrexia detected ({temp}°C)."
            ))
            tripped = True
        elif temp >= 38.0:
            classifications["temperature"] = "Febrile"
        elif temp < 35.5:
            classifications["temperature"] = "Hypothermia"
        else:
            classifications["temperature"] = "Afebrile"

    return alerts, classifications, tripped
