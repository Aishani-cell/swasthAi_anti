"""
Laboratory Report Text & Regex Parser
Extracts analyte names, numeric values, measurement units, and reference intervals.
"""
import re
from typing import List, Dict, Any, Optional
from backend.app.schemas.labs import ExtractedLabItem

# Standard clinical report line regex patterns
# Matches lines like:
# "Hemoglobin .......... 13.2 g/dL (12.0 - 15.5)"
# "Serum Creatinine: 1.4 mg/dL [0.6 - 1.2]"
# "TLC : 11,500 /cumm"
LAB_LINE_REGEX = re.compile(
    r'^(?P<analyte>[A-Za-z0-9\s\.\-\/\+]+?)'
    r'[\s\.\:\t\=\-]{2,}'
    r'(?P<value>[-+]?\d+(?:[\.,]\d+)?)'
    r'(?:\s*(?P<unit>[A-Za-z0-9\%\^\/\*\.]+))?'
    r'(?:\s*[\(\[](?P<ref>[-+]?\d+(?:[\.,]\d+)?\s*[\-\–\to]\s*[-+]?\d+(?:[\.,]\d+)?)[\)\]])?',
    re.MULTILINE
)

# Inline key-value pattern for semi-structured text: e.g. "Hb 12.5, WBC 8000, Plt 150000"
INLINE_PAIR_REGEX = re.compile(
    r'\b(?P<analyte>[A-Za-z\s\.\-]{2,25}?)\s*[:\=]?\s*'
    r'(?P<value>[-+]?\d+(?:[\.,]\d+)?)'
    r'(?:\s*(?P<unit>[A-Za-z0-9\%\^\/\*\.]+))?',
    re.IGNORECASE
)

def parse_lab_text(raw_text: str) -> List[ExtractedLabItem]:
    """
    Parses unstructured or semi-structured laboratory report text into structured ExtractedLabItem objects.
    """
    if not raw_text or not raw_text.strip():
        return []

    results: List[ExtractedLabItem] = []
    seen_analytes = set()

    # Pass 1: Line-by-line structured report parsing
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or len(line) < 3:
            continue
            
        m = LAB_LINE_REGEX.search(line)
        if m:
            analyte = m.group("analyte").strip()
            raw_val = m.group("value").replace(',', '')
            unit = m.group("unit")
            ref_int = m.group("ref")
            
            # Avoid headers or false matches
            if len(analyte) > 1 and not re.match(r'^(date|page|name|age|sex|doctor|test|parameter)', analyte, re.I):
                try:
                    num_val = float(raw_val)
                    key = analyte.lower()
                    if key not in seen_analytes:
                        seen_analytes.add(key)
                        results.append(ExtractedLabItem(
                            analyte_name=analyte,
                            raw_value=raw_val,
                            numeric_value=num_val,
                            unit=unit,
                            reference_interval=ref_int,
                            confidence=0.95
                        ))
                except ValueError:
                    pass

    # Pass 2: Inline key-value parsing if Pass 1 found few items
    if len(results) == 0:
        for m in INLINE_PAIR_REGEX.finditer(raw_text):
            analyte = m.group("analyte").strip()
            raw_val = m.group("value").replace(',', '')
            unit = m.group("unit")
            if len(analyte) > 1 and not re.match(r'^(date|page|name|age|sex|doctor|day|hr|bp)', analyte, re.I):
                try:
                    num_val = float(raw_val)
                    key = analyte.lower()
                    if key not in seen_analytes:
                        seen_analytes.add(key)
                        results.append(ExtractedLabItem(
                            analyte_name=analyte,
                            raw_value=raw_val,
                            numeric_value=num_val,
                            unit=unit,
                            reference_interval=None,
                            confidence=0.85
                        ))
                except ValueError:
                    pass

    return results
