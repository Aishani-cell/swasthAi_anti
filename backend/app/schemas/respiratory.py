"""
Respiratory Acoustic Schemas
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class RespiratoryCycleAnnotation(BaseModel):
    cycle_index: int
    start_sec: float
    end_sec: float
    predicted_class: str = Field(..., pattern="^(normal|crackle|wheeze|both|unverified)$")
    confidence: float

class RespiratoryAnalysisResult(BaseModel):
    predicted_class: str = Field(..., pattern="^(normal|crackle|wheeze|both|unverified)$")
    confidence: float
    cycle_count: int
    quality_status: str = "VALID"
    sample_rate: int
    duration_seconds: float
    probabilities: Dict[str, float] = {}
    acoustic_embedding_dim: int = 768
    model_version: str = "SwasthAI-RespLLM-light-v1"
    explanation: str = ""
    respllm_narrative: Optional[str] = None
    cycles: List[RespiratoryCycleAnnotation] = []
    dataset_source: str = "untrained"
    device: str = "cpu"
    human_review_required: bool = True
