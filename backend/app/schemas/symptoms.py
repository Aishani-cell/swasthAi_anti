"""
Symptom Pydantic Schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field

class SymptomExtractionResult(BaseModel):
    canonical_concept: str
    original_phrase: str
    language: str = Field(..., pattern="^(en|hi|hinglish)$")
    is_negated: bool = False
    extraction_method: str = Field(..., pattern="^(LEXICON_EXACT|RATCLIFF_OBERSHELP|LLM_FALLBACK)$")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    source_span: Optional[str] = None
    verification_status: str = "VERIFIED"

class SymptomSummary(BaseModel):
    extracted_symptoms: List[SymptomExtractionResult]
    negated_symptoms: List[SymptomExtractionResult]
    summary_text: str
    fallback_used: bool = False
