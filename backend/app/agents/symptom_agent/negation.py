"""
Symptom Negation Detection Module
Implements Section 3.4 of the SwasthAI paper with precise syntactic polarity direction:
- Pre-negation cues (e.g., 'no', 'without', 'denies', 'bina'): cue precedes symptom (lookbehind window).
- Post-negation cues (e.g., 'nahi', 'nahin', 'absent', 'denied', 'negative'): cue follows symptom (lookahead window delta = 20 chars).
- Clause boundaries (', but', 'however', '.', ';') strictly terminate negation propagation.
"""
import re
from typing import Tuple

PRE_NEGATION_CUES = {
    "no", "not", "without", "denies", "denied", "free of", "absent of",
    "bina", "koi nahi", "kuch nahi", "gair",
    "बिना", "गैर", "मुक्त"
}

POST_NEGATION_CUES = {
    "absent", "negative", "none", "denied",
    "nahi", "nahin", "naahi", "nidarad", "nahi hai", "nahin hai",
    "नहीं", "नहीं है", "ना", "नदारद", "अनुपस्थित"
}

CLAUSE_BOUNDARIES = re.compile(r'(\bbut\b|\bhowever\b|\balso\b|[,;:\.\?!\n])', re.IGNORECASE)

def check_negation(full_text: str, match_start: int, match_end: int, delta: int = 20) -> Tuple[bool, str]:
    """
    Determines if symptom at [match_start, match_end] in full_text is negated.
    """
    text_len = len(full_text)

    # 1. Lookahead window (up to delta chars after symptom end)
    raw_lookahead = full_text[match_end : min(text_len, match_end + delta)]
    # Stop lookahead at any clause boundary (e.g. punctuation, "but")
    boundary_match = CLAUSE_BOUNDARIES.search(raw_lookahead)
    if boundary_match:
        lookahead_chunk = raw_lookahead[:boundary_match.start()]
    else:
        lookahead_chunk = raw_lookahead

    lookahead_tokens = re.findall(r'[\w\u0900-\u097F]+', lookahead_chunk.lower())
    for token in lookahead_tokens:
        if token in POST_NEGATION_CUES:
            return True, f"post_negation:{token}"

    # 2. Lookbehind window (up to delta chars before symptom start)
    raw_lookbehind = full_text[max(0, match_start - delta) : match_start]
    # Stop lookbehind at earlier clause boundary
    boundary_matches = list(CLAUSE_BOUNDARIES.finditer(raw_lookbehind))
    if boundary_matches:
        last_boundary = boundary_matches[-1]
        lookbehind_chunk = raw_lookbehind[last_boundary.end():]
    else:
        lookbehind_chunk = raw_lookbehind

    lookbehind_tokens = re.findall(r'[\w\u0900-\u097F]+', lookbehind_chunk.lower())
    for token in lookbehind_tokens:
        if token in PRE_NEGATION_CUES:
            return True, f"pre_negation:{token}"

    return False, ""
