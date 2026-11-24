"""
SwasthAI Clinical Benchmark Evaluator
Executes the 50-case 25-category clinical vignette evaluation matching the paper's Table 1 and Table 2.
"""
import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from backend.app.evaluation.clinical_vignettes import CLINICAL_VIGNETTES_50
from backend.app.services.pipeline import pipeline
from backend.app.agents.diagnosis_agent.agent import deterministic_diagnosis_fallback
from backend.app.agents.drug_agent.agent import drug_agent, compute_jaccard_similarity
from backend.app.evidence.builder import build_evidence_graph
from backend.app.rag.service import rag_service
from backend.app.schemas.symptoms import SymptomSummary
from backend.app.agents.symptom_agent.service import symptom_service
from backend.app.agents.lab_agent.service import lab_agent_service
from backend.app.agents.lab_resolver.resolver_service import lab_resolver_service
from backend.app.safety.engine import safety_engine
from backend.app.schemas.vitals import VitalsInput
from ml.respiratory.evaluation.curves import write_confusion_svg
from ml.respiratory.paths import REPORT_DIR

PAPER_REFERENCE_METRICS = {
    "diagnosis_agent": {
        "accuracy": 78.00,
        "macro_precision": 64.52,
        "macro_recall": 62.90,
        "macro_f1": 63.44
    },
    "safety_status_agent": {
        "accuracy": 86.00,
        "macro_precision": 73.92,
        "macro_recall": 71.43,
        "macro_f1": 72.55
    },
    "drug_recommendation_agent": {
        "mean_jaccard_similarity": 74.17
    }
}

def evaluate_50_vignettes() -> Dict[str, Any]:
    total_cases = len(CLINICAL_VIGNETTES_50)
    
    # Safety tracking (42 Approved / 8 Rejected)
    safety_tp = 0  # Exp Rejected, Pred Rejected
    safety_fn = 0  # Exp Rejected, Pred Approved
    safety_fp = 0  # Exp Approved, Pred Rejected
    safety_tn = 0  # Exp Approved, Pred Approved

    # Diagnosis tracking
    diag_correct = 0
    condition_performance: Dict[str, Dict[str, int]] = {}

    # Drug Jaccard tracking
    jaccard_scores = []
    case_results = []

    for idx, case in enumerate(CLINICAL_VIGNETTES_50):
        c_id = case["case_id"]
        cond = case["condition"]
        exp_safety = case["expected_safety"]
        gold_diag = case["gold_diagnosis"]
        gold_drugs = case["gold_drug_classes"]

        # 1. Pipeline extraction & resolution
        symptom_summary = symptom_service.process_symptoms(case["symptoms"])
        vitals_obj = VitalsInput(**case["vitals"]) if case.get("vitals") else None
        extracted_labs = lab_agent_service.extract_from_dict_list(case.get("labs", []))
        resolved_labs = lab_resolver_service.resolve_items(extracted_labs)

        # 2. Safety Status Agent Evaluation
        alerts, vitals_class, cb_result = safety_engine.run_safety_assessment(
            vitals=vitals_obj,
            labs=resolved_labs,
            age=45,
            is_pregnant=False
        )
        pred_safety = cb_result.safety_status

        if exp_safety == "Rejected":
            if pred_safety == "Rejected":
                safety_tp += 1
            else:
                safety_fn += 1
        else:
            if pred_safety == "Approved":
                safety_tn += 1
            else:
                safety_fp += 1

        # 3. Build EvidenceGraph for clinical reasoning
        evidence_graph = build_evidence_graph(
            encounter_id=f"bench-{idx+1:02d}",
            demographics={"age": 45, "sex": "MALE", "is_pregnant": False},
            symptoms=symptom_summary.extracted_symptoms,
            negated_symptoms=symptom_summary.negated_symptoms,
            vitals=vitals_obj,
            vitals_classification=vitals_class,
            resolved_labs=resolved_labs,
            imaging_findings=[],
            respiratory_finding=None,
            missing_modalities=[],
            safety_alerts=alerts,
            circuit_breaker_tripped=cb_result.is_halted
        )

        rag_output = rag_service.retrieve_guidelines(evidence_graph)
        
        # 4. Diagnosis Agent Evaluation
        diag_output = deterministic_diagnosis_fallback(evidence_graph, rag_output)
        pred_diag = diag_output.primary_diagnosis

        is_diag_correct = False
        if gold_diag.lower() in pred_diag.lower() or pred_diag.lower() in gold_diag.lower():
            is_diag_correct = True
            diag_correct += 1

        if cond not in condition_performance:
            condition_performance[cond] = {"total": 0, "correct": 0}
        condition_performance[cond]["total"] += 1
        if is_diag_correct:
            condition_performance[cond]["correct"] += 1

        # 5. Drug Recommendation Agent Evaluation (Table 1 Benchmark)
        # Evaluates candidate drug class recommendation accuracy for the diagnostic hypothesis
        eval_graph = evidence_graph.model_copy(update={"circuit_breaker_tripped": False})
        drug_output = drug_agent.recommend_drug_classes(diag_output, eval_graph)
        pred_drugs = drug_output.generic_drug_classes
        j_score = compute_jaccard_similarity(pred_drugs, gold_drugs)
        jaccard_scores.append(j_score)

        case_results.append({
            "case_id": c_id,
            "condition": cond,
            "expected_safety": exp_safety,
            "predicted_safety": pred_safety,
            "gold_diagnosis": gold_diag,
            "predicted_diagnosis": pred_diag,
            "is_diag_correct": is_diag_correct,
            "jaccard_similarity": j_score
        })

    # Safety metrics
    safety_acc = (safety_tp + safety_tn) / total_cases
    rec_rej = safety_tp / (safety_tp + safety_fn) if (safety_tp + safety_fn) > 0 else 0.0
    prec_rej = safety_tp / (safety_tp + safety_fp) if (safety_tp + safety_fp) > 0 else 0.0
    f1_rej = (2 * prec_rej * rec_rej) / (prec_rej + rec_rej) if (prec_rej + rec_rej) > 0 else 0.0

    rec_app = safety_tn / (safety_tn + safety_fp) if (safety_tn + safety_fp) > 0 else 0.0
    prec_app = safety_tn / (safety_tn + safety_fn) if (safety_tn + safety_fn) > 0 else 0.0
    f1_app = (2 * prec_app * rec_app) / (prec_app + rec_app) if (prec_app + rec_app) > 0 else 0.0

    safety_macro_p = (prec_rej + prec_app) / 2.0
    safety_macro_r = (rec_rej + rec_app) / 2.0
    safety_macro_f1 = (f1_rej + f1_app) / 2.0

    # Diagnosis metrics
    diag_acc = diag_correct / total_cases
    per_cond_acc = [v["correct"] / v["total"] for v in condition_performance.values()]
    diag_macro_p = float(np.mean(per_cond_acc))
    diag_macro_r = diag_acc
    diag_macro_f1 = (2 * diag_macro_p * diag_macro_r) / (diag_macro_p + diag_macro_r) if (diag_macro_p + diag_macro_r) > 0 else 0.0

    mean_jaccard = float(np.mean(jaccard_scores))
    jaccard_bins = {"0.0-0.25": 0, "0.25-0.5": 0, "0.5-0.75": 0, "0.75-1.0": 0}
    for score in jaccard_scores:
        if score < 0.25:
            jaccard_bins["0.0-0.25"] += 1
        elif score < 0.5:
            jaccard_bins["0.25-0.5"] += 1
        elif score < 0.75:
            jaccard_bins["0.5-0.75"] += 1
        else:
            jaccard_bins["0.75-1.0"] += 1

    labels = sorted({c["condition"] for c in CLINICAL_VIGNETTES_50})
    label_index = {name: i for i, name in enumerate(labels)}
    diag_matrix = np.zeros((len(labels), len(labels)), dtype=int)
    gold_counts = {name: 0 for name in labels}
    pred_counts = {name: 0 for name in labels}
    true_positives = {name: 0 for name in labels}
    for row in case_results:
        gold = row["condition"]
        pred = row["predicted_diagnosis"]
        gold_counts[gold] += 1
        candidates = [name for name in labels if name.lower() in pred.lower() or pred.lower() in name.lower()]
        matched = max(candidates, key=len) if candidates else None
        if matched is not None:
            diag_matrix[label_index[gold], label_index[matched]] += 1
            pred_counts[matched] += 1
            if matched == gold:
                true_positives[matched] += 1
    diag_precisions, diag_recalls = [], []
    for name in labels:
        diag_precisions.append(true_positives[name] / pred_counts[name] if pred_counts[name] else 0.0)
        diag_recalls.append(true_positives[name] / gold_counts[name] if gold_counts[name] else 0.0)
    diag_f1s = [
        (2 * p * r) / (p + r) if (p + r) else 0.0
        for p, r in zip(diag_precisions, diag_recalls)
    ]

    safety_matrix = [
        [safety_tn, safety_fp],
        [safety_fn, safety_tp],
    ]
    write_confusion_svg(safety_matrix, ["Approved", "Rejected"], REPORT_DIR.parent / "evaluation" / "safety_confusion_matrix.svg")

    evaluation_summary = {
        "total_cases": total_cases,
        "safety_agent_performance": {
            "accuracy": round(safety_acc * 100, 2),
            "macro_precision": round(safety_macro_p * 100, 2),
            "macro_recall": round(safety_macro_r * 100, 2),
            "macro_f1": round(safety_macro_f1 * 100, 2),
            "confusion_matrix": {
                "true_approved_pred_approved": safety_tn,
                "true_approved_pred_rejected_fp": safety_fp,
                "true_rejected_pred_approved_fn": safety_fn,
                "true_rejected_pred_rejected_tp": safety_tp
            }
        },
        "diagnosis_agent_performance": {
            "accuracy": round(diag_acc * 100, 2),
            "macro_precision": round(diag_macro_p * 100, 2),
            "macro_recall": round(diag_macro_r * 100, 2),
            "macro_f1": round(diag_macro_f1 * 100, 2),
            "correct_cases": diag_correct,
            "total_cases": total_cases,
            "multiclass": {
                "macro_precision": round(float(np.mean(diag_precisions)) * 100, 2),
                "macro_recall": round(float(np.mean(diag_recalls)) * 100, 2),
                "macro_f1": round(float(np.mean(diag_f1s)) * 100, 2),
                "labels": labels,
                "confusion_matrix": diag_matrix.tolist(),
                "note": "Rows are gold conditions. A column increments only when the predicted string matches that condition name."
            }
        },
        "vision_agent_performance": {
            "status": "NOT_EVALUATED",
            "accuracy": None,
            "macro_precision": None,
            "macro_recall": None,
            "macro_f1": None,
            "reason": "Section 4.5 of the paper defers quantitative imaging evaluation. This repository has no labeled radiology set, and the 32B vision model is not run. No vision accuracy is reported."
        },
        "drug_agent_performance": {
            "mean_jaccard_similarity": round(mean_jaccard * 100, 2),
            "jaccard_bins": jaccard_bins
        },
        "paper_reference_comparison": PAPER_REFERENCE_METRICS,
        "condition_breakdown": condition_performance,
        "case_details": case_results
    }

    out_dir = Path("./reports/evaluation")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "clinical_vignettes_results.json", "w", encoding="utf-8") as f:
        json.dump(evaluation_summary, f, indent=2)

    return evaluation_summary

if __name__ == "__main__":
    res = evaluate_50_vignettes()
    print("=== SWASTHAI CLINICAL BENCHMARK EVALUATION (N=50) ===")
    print(f"Safety Agent Accuracy: {res['safety_agent_performance']['accuracy']}% (Macro-F1: {res['safety_agent_performance']['macro_f1']}%)")
    print(f"Diagnosis Agent Accuracy: {res['diagnosis_agent_performance']['accuracy']}% (Macro-F1: {res['diagnosis_agent_performance']['macro_f1']}%)")
    print(f"Drug Recommendation Jaccard: {res['drug_agent_performance']['mean_jaccard_similarity']}%")
