"""
Unit tests for the Emergency Circuit Breaker Module (Section 3.6).
Verifies that critical alerts force immediate safety halts (status='Rejected')
and escalation instructions are appropriately populated.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.schemas.evidence import SafetyAlert
from backend.app.safety.circuit_breaker import evaluate_circuit_breaker


class TestCircuitBreaker(unittest.TestCase):
    def test_approved_when_no_alerts(self):
        cb = evaluate_circuit_breaker([])
        self.assertFalse(cb.is_halted)
        self.assertEqual(cb.safety_status, "Approved")
        self.assertEqual(len(cb.critical_alerts), 0)

    def test_approved_with_warning_alerts_only(self):
        warning = SafetyAlert(
            rule_id="RULE_VIT_BP_STAGE2",
            ruleset_version="2026.1",
            severity="WARNING",
            observed_value="145/95",
            threshold="SBP >= 140",
            circuit_breaker_halted=False,
            escalation_instructions="Monitor and follow-up",
            explanation="Stage 2 hypertension"
        )
        cb = evaluate_circuit_breaker([warning])
        self.assertFalse(cb.is_halted)
        self.assertEqual(cb.safety_status, "Approved")
        self.assertEqual(len(cb.warning_alerts), 1)

    def test_rejected_with_critical_alert(self):
        crit = SafetyAlert(
            rule_id="RULE_VIT_SPO2_CRITICAL",
            ruleset_version="2026.1",
            severity="CRITICAL",
            observed_value="82%",
            threshold="SpO2 < 90%",
            circuit_breaker_halted=True,
            escalation_instructions="Administer immediate high-flow oxygen",
            explanation="Critical hypoxemic respiratory failure"
        )
        cb = evaluate_circuit_breaker([crit])
        self.assertTrue(cb.is_halted)
        self.assertEqual(cb.safety_status, "Rejected")
        self.assertIn("Critical hypoxemic", cb.primary_reason)
        self.assertIn("Administer immediate high-flow oxygen", cb.escalation_actions)


if __name__ == "__main__":
    unittest.main()
