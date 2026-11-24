"""
Dataset Export Utility
Exports generated encounters dataset to CSV or formatted JSON.
"""
import json
import csv
import argparse
from pathlib import Path

def export_dataset(input_jsonl: str = "./data/generated/encounters.jsonl", output_format: str = "csv", output_path: str = "./data/generated/encounters_export.csv"):
    in_p = Path(input_jsonl)
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    records = []
    with open(in_p, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    if output_format == "csv":
        if not records:
            return
        fieldnames = [
            "case_id", "synthetic_patient_id", "encounter_id", "age", "sex", "pregnancy_status",
            "symptom_language", "symptoms_original", "safety_status", "emergency_escalation_status",
            "predicted_primary_diagnosis", "gold_diagnosis", "gold_safety_status", "split"
        ]
        with open(out_p, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in records:
                writer.writerow(r)
        print(f"Exported {len(records)} records to CSV: {output_path}")

    elif output_format == "json":
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        print(f"Exported {len(records)} records to JSON: {output_path}")

if __name__ == "__main__":
    export_dataset()
