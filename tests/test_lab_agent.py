"""
Laboratory Extraction and LOINC Resolution Tests
"""
import unittest
from backend.app.schemas.labs import ExtractedLabItem
from backend.app.agents.lab_agent.lab_parser import parse_lab_text
from backend.app.agents.lab_resolver.loinc_resolver import resolve_lab_item
from backend.app.agents.lab_resolver.unit_converter import convert_to_canonical_unit

class TestLabModule(unittest.TestCase):
    def test_lab_text_parsing(self):
        report_text = """
        Hemoglobin .......... 13.5 g/dL (12.0 - 16.0)
        WBC Count ........... 8,400 /cumm
        Platelets ........... 250,000 /cumm
        Serum Creatinine .... 1.1 mg/dL
        """
        extracted = parse_lab_text(report_text)
        self.assertGreaterEqual(len(extracted), 3)
        analytes = {e.analyte_name.lower(): e for e in extracted}
        self.assertTrue(any("hemoglobin" in k for k in analytes))
        self.assertTrue(any("creatinine" in k for k in analytes))

    def test_loinc_resolution_hemoglobin(self):
        item = ExtractedLabItem(analyte_name="Hb", raw_value="13.2", numeric_value=13.2, unit="g/dL")
        resolved = resolve_lab_item(item)
        self.assertEqual(resolved.verification_status, "VERIFIED")
        self.assertEqual(resolved.loinc_code, "718-7")
        self.assertEqual(resolved.plausibility_flag, "NORMAL")

    def test_platelet_unit_conversion(self):
        # 1.8 lakhs/cumm -> 180,000 cells/uL
        conv_val, unit, is_valid = convert_to_canonical_unit("platelets", 1.8, "lakhs/cumm")
        self.assertTrue(is_valid)
        self.assertEqual(conv_val, 180000.0)
        self.assertEqual(unit, "cells/uL")

    def test_panic_critical_lab_flag(self):
        # Platelets 25,000 -> CRITICAL_LOW
        item = ExtractedLabItem(analyte_name="Platelets", raw_value="25000", numeric_value=25000, unit="/cumm")
        resolved = resolve_lab_item(item)
        self.assertEqual(resolved.verification_status, "VERIFIED")
        self.assertEqual(resolved.plausibility_flag, "CRITICAL_LOW")

    def test_implausible_survival_bounds(self):
        # Hemoglobin 55 g/dL is biologically impossible for a human
        item = ExtractedLabItem(analyte_name="Hemoglobin", raw_value="55", numeric_value=55.0, unit="g/dL")
        resolved = resolve_lab_item(item)
        self.assertEqual(resolved.verification_status, "IMPLAUSIBLE")

if __name__ == "__main__":
    unittest.main()
