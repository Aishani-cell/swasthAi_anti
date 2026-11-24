"""
Laboratory Unit Standardization and Conversion
Converts regional reporting units into canonical units for LOINC verification.
"""
from typing import Tuple, Optional

def convert_to_canonical_unit(
    test_key: str,
    raw_value: float,
    input_unit: Optional[str]
) -> Tuple[Optional[float], Optional[str], bool]:
    """
    Normalizes value to canonical unit.
    Returns: (converted_numeric_value, canonical_unit, is_valid_unit)
    """
    if not input_unit:
        return raw_value, None, False
        
    unit = input_unit.strip().lower()
    
    # 1. White Blood Cells (Canonical: cells/uL)
    if test_key == "white_blood_cells":
        if unit in ["cells/ul", "/cumm", "cumm", "cells/mm3", "/ul"]:
            return raw_value, "cells/uL", True
        elif unit in ["x10^3/ul", "10*3/ul", "k/ul", "10^3/ul"]:
            return raw_value * 1000.0, "cells/uL", True
        elif unit in ["x10^9/l", "10^9/l"]:
            return raw_value * 1000.0, "cells/uL", True
        return None, None, False

    # 2. Platelets (Canonical: cells/uL)
    if test_key == "platelets":
        if unit in ["cells/ul", "/cumm", "cumm", "cells/mm3", "/ul"]:
            # If value is e.g. 1.8, operator likely meant 1.8 lakhs
            if raw_value < 50.0:
                return raw_value * 100000.0, "cells/uL", True
            return raw_value, "cells/uL", True
        elif unit in ["lakhs/cumm", "lakh/cumm", "lakhs", "lac", "lacs"]:
            return raw_value * 100000.0, "cells/uL", True
        elif unit in ["x10^3/ul", "10*3/ul", "k/ul", "10^3/ul"]:
            return raw_value * 1000.0, "cells/uL", True
        elif unit in ["x10^5/ul"]:
            return raw_value * 100000.0, "cells/uL", True
        return None, None, False

    # 3. Hemoglobin (Canonical: g/dL)
    if test_key == "hemoglobin":
        if unit in ["g/dl", "gm/dl", "g%", "gm%"]:
            return raw_value, "g/dL", True
        elif unit in ["g/l"]:
            return raw_value / 10.0, "g/dL", True
        return None, None, False

    # 4. Serum Creatinine (Canonical: mg/dL)
    if test_key == "serum_creatinine":
        if unit in ["mg/dl", "mg/l * 10"]:
            return raw_value, "mg/dL", True
        elif unit in ["umol/l", "micromol/l"]:
            return round(raw_value / 88.4, 2), "mg/dL", True
        return None, None, False

    # 5. Blood Glucose (Canonical: mg/dL)
    if test_key in ["fasting_blood_glucose", "random_blood_glucose"]:
        if unit in ["mg/dl", "mg%"]:
            return raw_value, "mg/dL", True
        elif unit in ["mmol/l"]:
            return round(raw_value * 18.0182, 1), "mg/dL", True
        return None, None, False

    # 6. Electrolytes (Potassium, Sodium) (Canonical: mEq/L)
    if test_key in ["serum_potassium", "serum_sodium"]:
        if unit in ["meq/l", "mmol/l"]:
            return raw_value, "mEq/L", True
        return None, None, False

    # 7. Bilirubin (Canonical: mg/dL)
    if test_key == "serum_bilirubin_total":
        if unit in ["mg/dl", "mg%"]:
            return raw_value, "mg/dL", True
        elif unit in ["umol/l"]:
            return round(raw_value / 17.1, 2), "mg/dL", True
        return None, None, False

    # 8. Troponin I (Canonical: ng/mL)
    if test_key == "troponin_i":
        if unit in ["ng/ml", "ug/l"]:
            return raw_value, "ng/mL", True
        elif unit in ["pg/ml"]:
            return raw_value / 1000.0, "ng/mL", True
        return None, None, False

    # 9. Red Blood Cells (Canonical: million/uL)
    if test_key == "red_blood_cells":
        if unit in ["million/ul", "million/cumm", "mil/cumm", "x10^6/ul", "x10^12/l", "10^6/ul", "m/cumm", "million/mm3"]:
            return raw_value, "million/uL", True
        return None, None, False

    # 10. Liver Enzymes (ALT, AST) (Canonical: U/L)
    if test_key in ["alanine_aminotransferase", "aspartate_aminotransferase"]:
        if unit in ["u/l", "iu/l"]:
            return raw_value, "U/L", True
        return None, None, False

    # 11. Glycated Hemoglobin (HbA1c) (Canonical: %)
    if test_key == "glycated_hemoglobin":
        if unit in ["%", "percent"]:
            return raw_value, "%", True
        return None, None, False

    # 12. Erythrocyte Sedimentation Rate (Canonical: mm/hr)
    if test_key == "erythrocyte_sedimentation_rate":
        if unit in ["mm/hr", "mm/1st hr", "mm/h"]:
            return raw_value, "mm/hr", True
        return None, None, False

    # Default fallback
    return raw_value, input_unit, True
