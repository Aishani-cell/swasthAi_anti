"""
Machine Learning, Evaluation & Model Status Endpoints
"""
import os
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from backend.app.schemas.respiratory import RespiratoryAnalysisResult
from ml.respiratory.inference.predict import respiratory_inference_service
from ml.respiratory.training.train import train_respiratory_model
from backend.app.evaluation.evaluator import evaluate_50_vignettes, PAPER_REFERENCE_METRICS
from backend.app.rag.vector_store import vector_store

router = APIRouter(prefix="", tags=["ML & Knowledge Services"])

@router.get("/models/status")
def get_models_status():
    from ml.respiratory.paths import BEST_CHECKPOINT
    from ml.respiratory.runtime import active_model, device_report
    from ml.respiratory.data.icbhi import dataset_status
    return {
        "status": "ONLINE",
        "active_models": 1 if active_model() else 0,
        "max_active_models": 1,
        "device": device_report(),
        "hardware_target": "NVIDIA RTX 3050 Laptop (6144 MiB) / Intel i5-14450HX / 24 GB RAM",
        "models": {
            "respllm": {
                "architecture": "CNN-BiGRU encoder, 768-d embedding, 4-class ICBHI head, closed-vocabulary GRU decoder",
                "replaces": "Frozen OPERA-CT plus the paper's planned RespLLM integration",
                "checkpoint_available": BEST_CHECKPOINT.exists(),
                "weights_path": str(BEST_CHECKPOINT),
                "icbhi": dataset_status(),
            },
            "vision": {
                "type": "Metadata audit and operator-entered findings",
                "not_loaded": "Qwen3-VL-32B-Instruct",
                "reason": "32B vision-language weights do not fit in 6 GB VRAM",
            },
            "language": {
                "configured_local_model": "qwen2.5:1.5b-instruct via Ollama when installed",
                "constraint": "May only confirm the deterministic diagnosis. It cannot author evidence or drug classes.",
            },
            "symptom_nlp": {
                "algorithm": "Curated Bilingual Lexicon + Ratcliff-Obershelp (0.90) + 20-char Negation",
                "status": "ACTIVE_DETERMINISTIC"
            },
            "safety_engine": {
                "type": "Deterministic Rule Engine (Non-LLM Circuit Breaker)",
                "status": "ACTIVE_ZERO_DEPENDENCY"
            },
            "reasoning_agent": {
                "type": "Purpose-Limited CDSS (Temp=0.0) with Deterministic Fallback",
                "status": "READY"
            }
        }
    }

@router.get("/rag/status")
def get_rag_status():
    return {
        "status": "ONLINE",
        "document_count": len(vector_store.documents),
        "embedding_vocabulary_size": len(vector_store.vocabulary),
        "distance_threshold_tau": vector_store.tau,
        "guideline_publishers": ["ICMR", "Ministry of Health & Family Welfare", "NVBDCP", "RSSDI", "ICS"]
    }

@router.post("/respiratory/analyze", response_model=RespiratoryAnalysisResult)
async def analyze_respiratory_audio(file: UploadFile = File(...)):
    temp_path = f"./data/uploads/temp_{file.filename}"
    Path("./data/uploads").mkdir(parents=True, exist_ok=True)
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    res = respiratory_inference_service.predict(temp_path)
    return res

@router.post("/training/train_respiratory")
def trigger_respiratory_training(epochs: int = 3, smoke_test: bool = True):
    res = train_respiratory_model(epochs=epochs, smoke_test=smoke_test)
    return res

@router.get("/evaluation/results")
def get_evaluation_results():
    report_file = Path("./reports/evaluation/clinical_vignettes_results.json")
    if report_file.exists():
        with open(report_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return evaluate_50_vignettes()
