"""
Backend ML Service Bridge for Respiratory Acoustics
"""
from typing import Optional
from backend.app.schemas.respiratory import RespiratoryAnalysisResult
from ml.respiratory.inference.predict import respiratory_inference_service

def run_respiratory_analysis(audio_path: str) -> RespiratoryAnalysisResult:
    return respiratory_inference_service.predict(audio_path)
