"""
Safety Rules Definitions and Rule Registry
Implements Section 3.6 of the SwasthAI paper.
Includes BP staging (Equation 3), age-specific pulse bounds, SpO2, and panic lab limits.
"""
from typing import Dict, Any, List

RULES_VERSION = "2026.1-CLINICAL-DETERMINISTIC"

CRITICAL_SAFETY_RULES = {
    # 1. Blood Pressure Staging & Hypertensive Crisis (Equation 3)
    "RULE_VIT_BP_CRISIS": {
        "rule_id": "RULE_VIT_BP_CRISIS",
        "description": "Hypertensive Crisis: SBP >= 180 mmHg or DBP >= 120 mmHg",
        "severity": "CRITICAL",
        "action": "EMERGENCY_ESCALATION",
        "escalation_instructions": "IMMEDIATE EMERGENCY REFERRAL: Hypertensive emergency. Administer emergency triage protocol, place patient in calm seated position, monitor vitals continuously, and initiate urgent transfer to secondary/tertiary hospital."
    },
    
    # 2. Critical Hypoxemia
    "RULE_VIT_SPO2_CRITICAL": {
        "rule_id": "RULE_VIT_SPO2_CRITICAL",
        "description": "Critical Hypoxemia: SpO2 < 90%",
        "severity": "CRITICAL",
        "action": "EMERGENCY_ESCALATION",
        "escalation_instructions": "CRITICAL RESPIRATORY FAILURE: Initiate high-flow supplemental oxygen immediately (target SpO2 94-98%). Check airway patency, position upright, and arrange immediate emergency transport."
    },

    # 3. Severe Bradycardia or Tachycardia (Shock / Arrhythmia)
    "RULE_VIT_HR_CRITICAL": {
        "rule_id": "RULE_VIT_HR_CRITICAL",
        "description": "Extreme Heart Rate: Pulse < 40 bpm or Pulse > 150 bpm",
        "severity": "CRITICAL",
        "action": "EMERGENCY_ESCALATION",
        "escalation_instructions": "HAEMODYNAMIC INSTABILITY: Life-threatening arrhythmia / shock risk. Verify pulse manually, obtain immediate 12-lead ECG, establish IV access, and call emergency medical services."
    },

    # 4. Severe Hyperpyrexia
    "RULE_VIT_TEMP_HYPERPYREXIA": {
        "rule_id": "RULE_VIT_TEMP_HYPERPYREXIA",
        "description": "Hyperpyrexia: Core temperature >= 40.0°C (104°F)",
        "severity": "CRITICAL",
        "action": "EMERGENCY_ESCALATION",
        "escalation_instructions": "HYPERPYREXIA ALERT: High risk of febrile encephalopathy / septic shock. Initiate active cooling, cold sponging, maintain hydration, and refer for immediate evaluation."
    },

    # 5. Critical Severe Thrombocytopenia (Dengue hemorrhagic / bleeding risk)
    "RULE_LAB_PLATELETS_PANIC": {
        "rule_id": "RULE_LAB_PLATELETS_PANIC",
        "description": "Panic Low Platelets: Platelet count < 50,000 cells/uL",
        "severity": "CRITICAL",
        "action": "EMERGENCY_ESCALATION",
        "escalation_instructions": "SEVERE BLEEDING RISK: Platelet count critically low (<50,000 /cumm). Inspect for petechiae, spontaneous bleeding, hematuria; initiate urgent hospital transfer for platelet transfusion evaluation."
    },

    # 6. Critical Potassium Anomaly (Arrhythmia / Cardiac Arrest risk)
    "RULE_LAB_POTASSIUM_PANIC": {
        "rule_id": "RULE_LAB_POTASSIUM_PANIC",
        "description": "Panic Potassium: K+ < 2.8 mEq/L or K+ >= 6.5 mEq/L",
        "severity": "CRITICAL",
        "action": "EMERGENCY_ESCALATION",
        "escalation_instructions": "FATAL DYSRHYTHMIA RISK: Serum potassium at panic level. Immediate ECG required; prepare emergency calcium gluconate/insulin-glucose protocol under physician direction."
    },

    # 7. Acute Coronary / STEMI Marker (Elevated Troponin + Chest Pain)
    "RULE_LAB_TROPONIN_STEMI": {
        "rule_id": "RULE_LAB_TROPONIN_STEMI",
        "description": "Elevated Troponin I >= 0.4 ng/mL with Chest Pain or Ischemia",
        "severity": "CRITICAL",
        "action": "EMERGENCY_ESCALATION",
        "escalation_instructions": "ACUTE CORONARY SYNDROME / STEMI: Positive myocardial necrosis marker. Administer chewable Aspirin 300mg immediately if non-allergic, monitor ECG, and transfer urgently to cath lab / ICCU."
    },

    # 8. Severe Metabolic Crisis (Diabetic Ketoacidosis / Hyperosmolar state)
    "RULE_LAB_GLUCOSE_CRITICAL": {
        "rule_id": "RULE_LAB_GLUCOSE_CRITICAL",
        "description": "Severe Hyperglycemia: Blood glucose >= 400 mg/dL",
        "severity": "CRITICAL",
        "action": "EMERGENCY_ESCALATION",
        "escalation_instructions": "DIABETIC KETOACIDOSIS ALERT: Extreme hyperglycemia. Check urine ketones, initiate IV normal saline rehydration, and arrange urgent medical admission."
    }
}

WARNING_SAFETY_RULES = {
    "RULE_VIT_BP_STAGE2": {
        "rule_id": "RULE_VIT_BP_STAGE2",
        "description": "Stage 2 Hypertension: SBP >= 140 mmHg or DBP >= 90 mmHg",
        "severity": "WARNING",
        "action": "CLINICIAN_REVIEW",
        "escalation_instructions": "Hypertension Stage 2 detected. Requires clinical confirmation, lifestyle counseling, and anti-hypertensive medical evaluation."
    },
    "RULE_VIT_SPO2_MILD": {
        "rule_id": "RULE_VIT_SPO2_MILD",
        "description": "Mild to Moderate Hypoxemia: SpO2 90-93%",
        "severity": "WARNING",
        "action": "CLINICIAN_REVIEW",
        "escalation_instructions": "Oxygen saturation below normal (90-93%). Recheck sensor placement, assess respiratory effort, and consider supplemental oxygen."
    },
    "RULE_LAB_CREATININE_ELEVATED": {
        "rule_id": "RULE_LAB_CREATININE_ELEVATED",
        "description": "Elevated Serum Creatinine > 1.5 mg/dL",
        "severity": "WARNING",
        "action": "CLINICIAN_REVIEW",
        "escalation_instructions": "Renal impairment indicator. Adjust all drug dosages for estimated GFR and avoid nephrotoxic agents (NSAIDs)."
    }
}
