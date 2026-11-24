"""
End-to-end integration tests for the SwasthAI Multimodal Clinical Pipeline.
Tests normal patient consultation, bilingual symptom flow, and emergency circuit breaker halt.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.services.pipeline import pipeline


class TestPipeline(unittest.TestCase):
    def test_pneumonia_consultation(self):
        patient = {"full_name": "Ramesh Kumar", "age": 45, "sex": "MALE", "is_pregnant": False}
        dossier = pipeline.execute_consultation_pipeline(
            encounter_id="enc-pipe-01",
            patient_info=patient,
            symptom_text="Cough with yellow sputum and fever for 3 days",
            vitals_data={"systolic_bp": 120, "diastolic_bp": 78, "heart_rate": 88, "spo2": 95, "temperature_c": 38.6},
            lab_items_raw=[{"analyte_name": "WBC", "raw_value": "13500", "unit": "/cumm"}]
        )
        self.assertFalse(dossier["safety_assessment"]["circuit_breaker_halted"])
        self.assertEqual(dossier["safety_assessment"]["safety_status"], "Approved")
        self.assertEqual(dossier["diagnosis"]["primary_diagnosis"], "Pneumonia")
        self.assertIn("Beta-lactam antibiotics", dossier["drug_recommendation"]["generic_drug_classes"])
        self.assertTrue(dossier["evidence_graph"]["integrity_hash"] is not None)

    def test_hindi_symptom_consultation(self):
        patient = {"full_name": "Sunita Bai", "age": 35, "sex": "FEMALE", "is_pregnant": False}
        dossier = pipeline.execute_consultation_pipeline(
            encounter_id="enc-pipe-02",
            patient_info=patient,
            symptom_text="तेज बुखार और कंपकंपी आना",
            vitals_data={"systolic_bp": 110, "diastolic_bp": 70, "heart_rate": 96, "spo2": 98, "temperature_c": 39.1}
        )
        self.assertFalse(dossier["safety_assessment"]["circuit_breaker_halted"])
        self.assertEqual(dossier["diagnosis"]["primary_diagnosis"], "Malaria")

    def test_emergency_halt_pipeline(self):
        patient = {"full_name": "Emergency Case", "age": 60, "sex": "MALE", "is_pregnant": False}
        dossier = pipeline.execute_consultation_pipeline(
            encounter_id="enc-pipe-03",
            patient_info=patient,
            symptom_text="Seene me tez dard",
            vitals_data={"systolic_bp": 210, "diastolic_bp": 130, "heart_rate": 110, "spo2": 88}
        )
        self.assertTrue(dossier["safety_assessment"]["circuit_breaker_halted"])
        self.assertEqual(dossier["safety_assessment"]["safety_status"], "Rejected")
        # Ensure generative drugs are blocked
        self.assertEqual(len(dossier["drug_recommendation"]["generic_drug_classes"]), 0)
        self.assertIn("Emergency circuit breaker active", dossier["drug_recommendation"]["contraindication_flags"])


if __name__ == "__main__":
    unittest.main()
