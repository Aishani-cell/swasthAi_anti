"""
Dataset Management API Endpoints
"""
import os
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from scripts.generate_report_dataset import generate_report_dataset
from scripts.validate_dataset import validate_dataset

router = APIRouter(prefix="/datasets", tags=["Datasets"])

@router.post("/generate")
def generate_dataset_endpoint(target_count: int = 100, seed: int = 42):
    stats = generate_report_dataset(target_count=target_count, seed=seed)
    return stats

@router.get("")
def get_dataset_stats():
    jsonl_file = Path("./data/generated/encounters.jsonl")
    if not jsonl_file.exists():
        return {"status": "NOT_GENERATED", "record_count": 0}
    val = validate_dataset(str(jsonl_file))
    return val

@router.post("/validate")
def validate_dataset_endpoint():
    return validate_dataset()
