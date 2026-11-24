"""
Emergency Circuit Breaker Module
Implements Section 3.6 of the SwasthAI paper.
Completely bypasses LLMs, RAG, and generative drug recommendations when critical anomalies occur.
Outputs:
- 'Approved' (non-critical case: safe for generative CDSS assistance)
- 'Rejected' (critical emergency case: generative reasoning blocked, escalation activated)
"""
from typing import List, Dict, Any, Optional
from backend.app.schemas.evidence import SafetyAlert

class CircuitBreakerResult:
    def __init__(
        self,
        is_halted: bool,
        safety_status: str,  # 'Approved' or 'Rejected'
        primary_reason: str,
        escalation_actions: List[str],
        critical_alerts: List[SafetyAlert],
        warning_alerts: List[SafetyAlert]
    ):
        self.is_halted = is_halted
        self.safety_status = safety_status
        self.primary_reason = primary_reason
        self.escalation_actions = escalation_actions
        self.critical_alerts = critical_alerts
        self.warning_alerts = warning_alerts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_halted": self.is_halted,
            "safety_status": self.safety_status,
            "primary_reason": self.primary_reason,
            "escalation_actions": self.escalation_actions,
            "critical_alerts": [a.model_dump() for a in self.critical_alerts],
            "warning_alerts": [a.model_dump() for a in self.warning_alerts]
        }

def evaluate_circuit_breaker(alerts: List[SafetyAlert]) -> CircuitBreakerResult:
    """
    Evaluates safety alerts to decide whether the emergency circuit breaker must trip.
    """
    critical_alerts = [a for a in alerts if a.severity == "CRITICAL" or a.circuit_breaker_halted]
    warning_alerts = [a for a in alerts if a.severity == "WARNING"]

    if critical_alerts:
        primary_alert = critical_alerts[0]
        instructions = [a.escalation_instructions for a in critical_alerts if a.escalation_instructions]
        return CircuitBreakerResult(
            is_halted=True,
            safety_status="Rejected",
            primary_reason=f"CRITICAL SAFETY TRIGGER: {primary_alert.explanation}",
            escalation_actions=instructions,
            critical_alerts=critical_alerts,
            warning_alerts=warning_alerts
        )

    return CircuitBreakerResult(
        is_halted=False,
        safety_status="Approved",
        primary_reason="No critical life-threatening rules triggered.",
        escalation_actions=[],
        critical_alerts=[],
        warning_alerts=warning_alerts
    )
