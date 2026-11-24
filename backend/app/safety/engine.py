"""
Unified Safety Engine
Coordinates vitals rules, laboratory rules, and circuit breaker gating.
"""
from typing import Optional, List, Dict, Any, Tuple
from backend.app.schemas.vitals import VitalsInput
from backend.app.schemas.labs import ResolvedLabItem
from backend.app.schemas.evidence import SafetyAlert
from backend.app.safety.vitals import evaluate_vitals_safety
from backend.app.safety.labs import evaluate_labs_safety
from backend.app.safety.circuit_breaker import evaluate_circuit_breaker, CircuitBreakerResult

class SafetyEngine:
    @staticmethod
    def run_safety_assessment(
        vitals: Optional[VitalsInput] = None,
        labs: Optional[List[ResolvedLabItem]] = None,
        age: Optional[int] = None,
        is_pregnant: bool = False
    ) -> Tuple[List[SafetyAlert], Dict[str, str], CircuitBreakerResult]:
        """
        Runs comprehensive deterministic safety verification.
        Returns: (all_alerts, vitals_classifications, circuit_breaker_result)
        """
        all_alerts: List[SafetyAlert] = []
        
        # 1. Evaluate vitals
        vit_alerts, classifications, vit_tripped = evaluate_vitals_safety(
            vitals, age=age, is_pregnant=is_pregnant
        )
        all_alerts.extend(vit_alerts)

        # 2. Evaluate lab values
        if labs:
            lab_alerts, lab_tripped = evaluate_labs_safety(labs)
            all_alerts.extend(lab_alerts)

        # 3. Evaluate circuit breaker
        cb_result = evaluate_circuit_breaker(all_alerts)

        return all_alerts, classifications, cb_result

safety_engine = SafetyEngine()
