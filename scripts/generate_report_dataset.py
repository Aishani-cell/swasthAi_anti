"""
Pipeline-Accurate Synthetic Report Dataset Generator
Generates realistic clinical encounters across all 25 disease categories,
passing each record through the actual SwasthAI pipeline to produce ground-truth
and pipeline-derived evidence fields.
"""
import os
import json
import random
from pathlib import Path
from typing import Dict, Any, List
from backend.app.evaluation.clinical_vignettes import CLINICAL_VIGNETTES_50
from backend.app.services.pipeline import pipeline
from backend.app.reporting.report_generator import report_generator

def generate_report_dataset(
    target_count: int = 500,
    seed: int = 42,
    output_dir: str = "./data/generated"
) -> Dict[str, Any]:
    """
    Generates a structured dataset of synthetic clinical encounters and source reports.
    """
    random.seed(seed)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    lab_dir = out_path / "lab_reports"
    lab_dir.mkdir(parents=True, exist_ok=True)
    rep_dir = out_path / "consultation_reports"
    rep_dir.mkdir(parents=True, exist_ok=True)

    jsonl_file = out_path / "encounters.jsonl"
    demo_file = out_path / "encounters_demo.jsonl"

    encounters: List[Dict[str, Any]] = []

    # Scenario distributions: 70% train, 15% val, 15% test
    splits = ["train"] * int(0.70 * target_count) + ["validation"] * int(0.15 * target_count)
    splits += ["test"] * (target_count - len(splits))
    random.shuffle(splits)

    languages = ["en", "hi", "hinglish"]

    base_cases = CLINICAL_VIGNETTES_50

    for idx in range(target_count):
        base = base_cases[idx % len(base_cases)]
        case_id = f"CASE-{idx+1:04d}"
        pat_id = f"SYN-PAT-{1000 + (idx % 80)}"
        enc_id = f"enc-{idx+1:04d}"
        split = splits[idx]

        # Demographic variation
        age = random.randint(18, 78)
        sex = random.choice(["MALE", "FEMALE"])
        is_pregnant = (sex == "FEMALE" and age < 45 and random.random() < 0.15)

        # Perturb vitals slightly while preserving clinical condition
        vitals_dict = None
        if base.get("vitals") and random.random() > 0.05:  # 5% missing vitals scenario
            v = base["vitals"].copy()
            v["systolic_bp"] = round(v["systolic_bp"] + random.uniform(-4, 4), 1)
            v["diastolic_bp"] = round(v["diastolic_bp"] + random.uniform(-3, 3), 1)
            v["heart_rate"] = round(v["heart_rate"] + random.uniform(-4, 4), 1)
            v["spo2"] = min(100.0, round(v["spo2"] + random.uniform(-1, 1), 1))
            vitals_dict = v

        # Labs
        labs_list = []
        if base.get("labs") and random.random() > 0.08:  # 8% missing labs scenario
            for l in base["labs"]:
                l_copy = l.copy()
                if l_copy["unit"] == "/cumm" and random.random() < 0.2:
                    # Unit variation: test unit converter
                    l_copy["unit"] = "cells/uL"
                labs_list.append(l_copy)

        # Run through the actual SwasthAI pipeline
        res = pipeline.execute_consultation_pipeline(
            encounter_id=enc_id,
            patient_info={"age": age, "sex": sex, "is_pregnant": is_pregnant},
            symptom_text=base["symptoms"],
            vitals_data=vitals_dict,
            lab_items_raw=labs_list,
            patient_allergies=[]
        )

        eg = res["evidence_graph"]
        safety = res["safety_assessment"]
        diag = res["diagnosis"]
        drug = res["drug_recommendation"]

        # First lab item summary if present
        first_lab = labs_list[0] if labs_list else {}

        encounter_record = {
            "case_id": case_id,
            "synthetic_patient_id": pat_id,
            "encounter_id": enc_id,
            "age": age,
            "sex": sex,
            "pregnancy_status": is_pregnant,
            "symptoms_original": base["symptoms"],
            "symptom_language": "hi" if any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in base["symptoms"]) else ("hinglish" if " me " in base["symptoms"] or " hai" in base["symptoms"] else "en"),
            "symptoms_normalized": [s["canonical_concept"] for s in eg.get("symptoms", [])],
            "negated_symptoms": [s["canonical_concept"] for s in eg.get("negated_symptoms", [])],
            "vital_signs": vitals_dict or {},
            "laboratory_test_name": first_lab.get("analyte_name"),
            "laboratory_value": first_lab.get("value"),
            "laboratory_unit": first_lab.get("unit"),
            "loinc_code": eg.get("resolved_labs", [{}])[0].get("loinc_code") if eg.get("resolved_labs") else None,
            "laboratory_validation_status": eg.get("resolved_labs", [{}])[0].get("verification_status", "NO_DATA") if eg.get("resolved_labs") else "MISSING",
            "missing_modalities": res["missing_modalities"],
            "safety_status": safety["safety_status"],
            "emergency_escalation_status": safety["circuit_breaker_halted"],
            "predicted_primary_diagnosis": diag["primary_diagnosis"],
            "predicted_differential_diagnoses": diag["differential_diagnoses"],
            "predicted_drug_classes": drug["generic_drug_classes"],
            "gold_diagnosis": base["gold_diagnosis"],
            "gold_safety_status": base["expected_safety"],
            "gold_drug_classes": base["gold_drug_classes"],
            "data_provenance": "SwasthAI-Pipeline-Deterministic-Generator",
            "split": split,
            "pipeline_version": "1.0.0"
        }

        encounters.append(encounter_record)

        # Generate sample text lab report for first 10 encounters
        if idx < 10 and labs_list:
            lab_txt_file = lab_dir / f"lab_report_{enc_id}.txt"
            with open(lab_txt_file, "w", encoding="utf-8") as lf:
                lf.write(f"SATNAVARI PRIMARY HEALTHPOD - LABORATORY REPORT\n")
                lf.write(f"Encounter: {enc_id} | Patient: {pat_id}\n")
                lf.write("="*50 + "\n")
                for l in labs_list:
                    lf.write(f"{l['analyte_name']:<25} : {l['value']} {l['unit']}\n")
                lf.write("="*50 + "\n")
                lf.write("Verified by: Point-of-Care Automated Bio-Analyzer\n")

        # Generate sample consultation markdown report for first 10 encounters
        if idx < 10:
            rep_md_file = rep_dir / f"consultation_report_{enc_id}.md"
            report_generator.generate_markdown_report(res, str(rep_md_file))

    # Save full JSONL dataset
    with open(jsonl_file, "w", encoding="utf-8") as f:
        for enc in encounters:
            f.write(json.dumps(enc, ensure_ascii=False) + "\n")

    # Save demonstration subset (first 25 encounters)
    with open(demo_file, "w", encoding="utf-8") as f:
        for enc in encounters[:25]:
            f.write(json.dumps(enc, ensure_ascii=False) + "\n")

    stats = {
        "status": "DATASET_GENERATION_SUCCESS",
        "total_records": len(encounters),
        "demo_records": min(25, len(encounters)),
        "train_records": sum(1 for e in encounters if e["split"] == "train"),
        "val_records": sum(1 for e in encounters if e["split"] == "validation"),
        "test_records": sum(1 for e in encounters if e["split"] == "test"),
        "output_jsonl": str(jsonl_file),
        "demo_jsonl": str(demo_file),
        "sample_lab_reports": 10,
        "sample_consultation_reports": 10
    }

    return stats

if __name__ == "__main__":
    s = generate_report_dataset(target_count=500, seed=42)
    print("Dataset generation complete:", json.dumps(s, indent=2))
