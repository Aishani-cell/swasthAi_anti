"""
Symptom NLP Agent Tests
"""
import unittest
from backend.app.agents.symptom_agent.service import symptom_service

class TestSymptomAgent(unittest.TestCase):
    def test_english_symptom_extraction_with_negation(self):
        text = "Patient complains of high fever and dry cough, but denies chest pain."
        res = symptom_service.process_symptoms(text)
        pos_concepts = {s.canonical_concept for s in res.extracted_symptoms}
        neg_concepts = {s.canonical_concept for s in res.negated_symptoms}

        self.assertIn("fever", pos_concepts)
        self.assertIn("cough", pos_concepts)
        self.assertIn("chest_pain", neg_concepts)

    def test_hinglish_symptom_extraction(self):
        text = "Marij ko 2 din se tez bukhar hai aur ulti ho rahi hai par seene me dard nahi hai"
        res = symptom_service.process_symptoms(text)
        pos_concepts = {s.canonical_concept for s in res.extracted_symptoms}
        neg_concepts = {s.canonical_concept for s in res.negated_symptoms}

        self.assertIn("fever", pos_concepts)
        self.assertIn("nausea_vomiting", pos_concepts)
        self.assertIn("chest_pain", neg_concepts)

    def test_devanagari_hindi_symptom_extraction(self):
        text = "सीने में दर्द और सांस फूलना"
        res = symptom_service.process_symptoms(text)
        pos_concepts = {s.canonical_concept for s in res.extracted_symptoms}

        self.assertIn("chest_pain", pos_concepts)
        self.assertIn("dyspnea", pos_concepts)

    def test_fuzzy_ratcliff_obershelp_matching(self):
        # Slightly misspelled symptom: "shortnes of breath"
        text = "Complaining of shortnes of breath on exertion"
        res = symptom_service.process_symptoms(text)
        pos_concepts = {s.canonical_concept for s in res.extracted_symptoms}
        self.assertIn("dyspnea", pos_concepts)

if __name__ == "__main__":
    unittest.main()
