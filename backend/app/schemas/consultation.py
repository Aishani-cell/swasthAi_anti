"""
Consultation, Diagnosis, and Drug Recommendation Schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DiagnosisHypothesis(BaseModel):
    condition_name: str
    icd10_hint: Optional[str] = None
    supporting_evidence: List[str] = []
    guideline_citations: List[str] = []
    confidence: Optional[float] = None
    reasoning_summary: Optional[str] = None
    differentiating_features: Optional[str] = None

class DiagnosisOutput(BaseModel):
    primary_diagnosis: str
    primary_confidence: float = 0.88
    explanation: str = ""
    differential_diagnoses: List[str] = []
    differential_hypotheses: List[DiagnosisHypothesis] = []
    evidence_citations: List[str] = []
    guideline_citations: List[str] = []
    missing_data_warnings: List[str] = []
    conditional_laboratory_findings: List[str] = []
    model_version: str
    physician_review_mandatory: bool = True

class DrugRecommendationOutput(BaseModel):
    generic_drug_classes: List[str]
    confidence_scores: Dict[str, float] = {}
    drug_explanations: Dict[str, str] = {}
    explanation: str = ""
    clinical_context: str
    guideline_citations: List[str] = []
    contraindication_flags: List[str] = []
    caution_notes: List[str] = []
    physician_review_mandatory: bool = True
    no_brand_names_verified: bool = True
