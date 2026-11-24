"""
EvidenceGraph Schemas
Implements the canonical immutable EvidenceGraph from the paper.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.vitals import VitalsInput
from backend.app.schemas.symptoms import SymptomExtractionResult
from backend.app.schemas.labs import ResolvedLabItem
from backend.app.schemas.respiratory import RespiratoryAnalysisResult

class SafetyAlert(BaseModel):
    rule_id: str
    ruleset_version: str
    severity: str = Field(..., pattern="^(CRITICAL|WARNING|INFO)$")
    observed_value: str
    threshold: str
    circuit_breaker_halted: bool = False
    escalation_instructions: Optional[str] = None
    explanation: str

class EvidenceGraphModel(BaseModel):
    graph_id: str
    encounter_id: str
    version: int = 1
    timestamp: str
    demographics: Dict[str, Any]
    symptoms: List[SymptomExtractionResult] = []
    negated_symptoms: List[SymptomExtractionResult] = []
    vitals: Optional[VitalsInput] = None
    vitals_classification: Dict[str, str] = {}
    resolved_labs: List[ResolvedLabItem] = []
    imaging_findings: List[Dict[str, Any]] = []
    respiratory_finding: Optional[RespiratoryAnalysisResult] = None
    missing_modalities: List[str] = []
    safety_alerts: List[SafetyAlert] = []
    circuit_breaker_tripped: bool = False
    integrity_hash: Optional[str] = None
    human_review_required: bool = True
