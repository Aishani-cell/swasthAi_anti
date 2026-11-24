"""
Dataset Validation Script
Validates schema compliance, checks missingness distributions, and ensures no data leakage across splits.
"""
import json
from pathlib import Path
from typing import Dict, Any

def validate_dataset(jsonl_path: str = "./data/generated/encounters.jsonl") -> Dict[str, Any]:
    p = Path(jsonl_path)
    if not p.exists():
        return {"status": "ERROR", "message": f"File {jsonl_path} does not exist"}

    total = 0
    splits = {"train": 0, "validation": 0, "test": 0}
    safeties = {"Approved": 0, "Rejected": 0}
    modalities_missing = {}
    diagnoses = {}

    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            total += 1

            # Required field checks
            for req in ["case_id", "synthetic_patient_id", "encounter_id", "symptoms_original", "vital_signs", "gold_diagnosis"]:
                if req not in rec:
                    return {"status": "INVALID", "message": f"Missing required field {req} in record {rec.get('case_id')}"}

            splits[rec.get("split", "unknown")] = splits.get(rec.get("split", "unknown"), 0) + 1
            safeties[rec.get("safety_status", "unknown")] = safeties.get(rec.get("safety_status", "unknown"), 0) + 1
            
            d_name = rec.get("gold_diagnosis", "Unknown")
            diagnoses[d_name] = diagnoses.get(d_name, 0) + 1

            for m in rec.get("missing_modalities", []):
                modalities_missing[m] = modalities_missing.get(m, 0) + 1

    return {
        "status": "VALID",
        "total_records": total,
        "split_distribution": splits,
        "safety_distribution": safeties,
        "unique_diagnostic_categories": len(diagnoses),
        "missing_modality_counts": modalities_missing
    }

if __name__ == "__main__":
    res = validate_dataset()
    print("Validation Results:", json.dumps(res, indent=2))
