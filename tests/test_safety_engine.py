"""
Unit tests for the Deterministic Safety Engine (Section 3.6).
Verifies rule evaluation on critical and warning vitals, panic laboratory thresholds,
and circuit breaker status.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.schemas.vitals import VitalsInput
from backend.app.schemas.labs import ResolvedLabItem
from backend.app.safety.engine import safety_engine
from backend.app.safety.vitals import evaluate_vitals_safety
from backend.app.safety.labs import evaluate_labs_safety


class TestSafetyEngine(unittest.TestCase):
    def test_hypertensive_crisis_rule(self):
        v = VitalsInput(systolic_bp=195, diastolic_bp=125, heart_rate=88, spo2=97)
        alerts, classif, cb = safety_engine.run_safety_assessment(vitals=v)
        self.assertTrue(cb.is_halted)
        self.assertEqual(cb.safety_status, "Rejected")
        self.assertEqual(classif.get("blood_pressure"), "Hypertensive crisis")
        critical_alerts = [a for a in alerts if a.severity == "CRITICAL"]
        self.assertGreaterEqual(len(critical_alerts), 1)

    def test_critical_hypoxemia(self):
        v = VitalsInput(systolic_bp=120, diastolic_bp=80, heart_rate=100, spo2=86)
        alerts, classif, cb = safety_engine.run_safety_assessment(vitals=v)
        self.assertTrue(cb.is_halted)
        self.assertEqual(classif.get("oxygenation"), "Critical Hypoxemia")

    def test_normal_vitals_approved(self):
        v = VitalsInput(systolic_bp=118, diastolic_bp=76, heart_rate=72, spo2=98, temperature_c=36.8)
        alerts, classif, cb = safety_engine.run_safety_assessment(vitals=v)
        self.assertFalse(cb.is_halted)
        self.assertEqual(cb.safety_status, "Approved")
        self.assertEqual(len(alerts), 0)

    def test_stage2_hypertension_warning(self):
        v = VitalsInput(systolic_bp=148, diastolic_bp=92, heart_rate=78, spo2=97)
        alerts, classif, cb = safety_engine.run_safety_assessment(vitals=v)
        self.assertFalse(cb.is_halted)  # Warnings do NOT trip the emergency circuit breaker
        self.assertEqual(cb.safety_status, "Approved")
        self.assertEqual(classif.get("blood_pressure"), "Stage 2 Hypertension")
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].severity, "WARNING")

    def test_panic_potassium(self):
        k_lab = ResolvedLabItem(
            analyte_name="Potassium",
            canonical_name="Potassium",
            loinc_code="2823-3",
            raw_value="7.1",
            numeric_value=7.1,
            unit="mEq/L",
            canonical_unit="mEq/L",
            reference_interval="3.5 - 5.1 mEq/L",
            verification_status="VERIFIED",
            plausibility_flag="CRITICAL_HIGH"
        )
        alerts, cb_tripped = evaluate_labs_safety([k_lab])
        self.assertTrue(cb_tripped)
        self.assertEqual(alerts[0].rule_id, "RULE_LAB_POTASSIUM_PANIC")


if __name__ == "__main__":
    unittest.main()
