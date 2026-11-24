"""
Symptom Agent Service Interface
"""
from typing import Dict, Any
from backend.app.schemas.symptoms import SymptomSummary
from backend.app.agents.symptom_agent.extractor import extract_symptoms

class SymptomService:
    @staticmethod
    def process_symptoms(text: str) -> SymptomSummary:
        return extract_symptoms(text)

symptom_service = SymptomService()
