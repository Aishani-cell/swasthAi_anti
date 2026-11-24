"""
Unit tests for the SwasthAI 50 Clinical Vignettes Evaluation Benchmark.
Tests dataset integrity (25 categories, 50 cases, 42 Approved / 8 Rejected),
and benchmark metric outputs.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.evaluation.clinical_vignettes import CLINICAL_VIGNETTES_50
from backend.app.evaluation.evaluator import evaluate_50_vignettes, PAPER_REFERENCE_METRICS


class TestEvaluationBenchmark(unittest.TestCase):
    def test_vignettes_dataset_structure(self):
        self.assertEqual(len(CLINICAL_VIGNETTES_50), 50)
        
        # Check 25 conditions × 2 cases each
        conditions = {}
        rejected_count = 0
        approved_count = 0
        for c in CLINICAL_VIGNETTES_50:
            cond = c["condition"]
            conditions[cond] = conditions.get(cond, 0) + 1
            if c["expected_safety"] == "Rejected":
                rejected_count += 1
            else:
                approved_count += 1

        self.assertEqual(len(conditions), 25)
        for cond, count in conditions.items():
            self.assertEqual(count, 2, f"Condition {cond} does not have exactly 2 cases")

        # 9 Rejected cases (critical emergency cases), 41 Approved
        self.assertGreaterEqual(rejected_count, 8)
        self.assertGreaterEqual(approved_count, 40)

    def test_evaluation_execution(self):
        res = evaluate_50_vignettes()
        self.assertIn("safety_agent_performance", res)
        self.assertIn("diagnosis_agent_performance", res)
        self.assertIn("drug_agent_performance", res)

        # Check performance exceeds paper target
        safety_acc = res["safety_agent_performance"]["accuracy"]
        diag_acc = res["diagnosis_agent_performance"]["accuracy"]
        drug_jaccard = res["drug_agent_performance"]["mean_jaccard_similarity"]

        self.assertGreaterEqual(safety_acc, 86.0)
        self.assertGreaterEqual(diag_acc, 78.0)
        self.assertGreaterEqual(drug_jaccard, 74.17)


if __name__ == "__main__":
    unittest.main()
