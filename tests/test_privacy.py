"""
Privacy & Security Tests
"""
import unittest
from backend.app.core.privacy import scrub_text, create_deidentified_demographics, hash_identifier, validate_llm_input

class TestPrivacyModule(unittest.TestCase):
    def test_phone_and_aadhaar_scrubbing(self):
        text = "Patient Ramesh Kumar, phone +91 9876543210, Aadhaar 4532 8901 2345 arrived with chest pain."
        scrubbed, stats = scrub_text(text, patient_name="Ramesh Kumar")
        self.assertNotIn("9876543210", scrubbed)
        self.assertNotIn("4532", scrubbed)
        self.assertNotIn("Ramesh", scrubbed)
        self.assertIn("[REDACTED_PHONE]", scrubbed)
        self.assertIn("[REDACTED_GOVT_ID]", scrubbed)

    def test_sha256_identifier_hashing(self):
        h1 = hash_identifier("+91 98765-43210")
        h2 = hash_identifier("9876543210")
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_demographic_minimization(self):
        dem = create_deidentified_demographics(age=45, sex="female", pregnancy_status="yes")
        self.assertEqual(dem["age"], 45)
        self.assertEqual(dem["sex"], "FEMALE")
        self.assertTrue(dem["is_pregnant"])

    def test_prompt_injection_phi_validator(self):
        clean_prompt = "Age 54, Male, complains of cough and fever."
        self.assertTrue(validate_llm_input(clean_prompt))
        leaky_prompt = "Patient contact 9876543210 has severe dyspnea."
        self.assertFalse(validate_llm_input(leaky_prompt))

if __name__ == "__main__":
    unittest.main()
