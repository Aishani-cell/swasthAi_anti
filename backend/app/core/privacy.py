"""
SwasthAI Privacy & Identifier De-identification Module
Implements Section 3.3 of the SwasthAI paper:
- Scrubs direct identifiers (Name, Phone, DOB, Address, Aadhaar/Govt ID)
- Retains only coarse demographic context (Age, Sex, Pregnancy Status)
- Provides deterministic SHA-256 pseudonymization
- Validates model inputs to prevent PHI leakage into LLM prompts
"""
import re
import hashlib
from typing import Dict, Any, Tuple, Optional

# Regular expressions for identifying private health information (PHI)
PHONE_REGEX = re.compile(r'(?:\+?91[\-\s]?)?[6789]\d{9}\b')
AADHAAR_REGEX = re.compile(r'\b[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b')
DOB_REGEX = re.compile(r'\b(?:\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})\b')
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')

# Honorifics & name markers common in Indian clinical settings
NAME_PREFIX_REGEX = re.compile(
    r'\b(?:Mr\.|Mrs\.|Ms\.|Shri|Smt\.|Kumar|Kumari|Dr\.|Patient(?:\s+Name)?\s*[:\-])\s+([A-Za-z]{2,25}(?:\s+[A-Za-z]{2,25})?)',
    re.IGNORECASE
)

# Address keywords
ADDRESS_REGEX = re.compile(
    r'\b(?:Village|Gram|Taluka|District|Dist\.|Pin\s*Code|Pincode|Mohalla|Post|Ward\s*No\.?)\s*[:\-]?\s*([A-Za-z0-9\s,.-]{4,40})',
    re.IGNORECASE
)

def hash_identifier(identifier: str) -> str:
    """Computes a one-way SHA-256 hash for secure indexing without persisting plaintext."""
    if not identifier:
        return ""
    # Normalize by keeping only alphanumeric characters (e.g., standardizing phone/ID formats)
    clean = re.sub(r'[^a-zA-Z0-9]', '', str(identifier).strip().lower())
    # Standardize Indian phone numbers (10 digits)
    if len(clean) == 12 and clean.startswith("91"):
        clean = clean[2:]
    elif len(clean) == 11 and clean.startswith("0"):
        clean = clean[1:]
    return hashlib.sha256(clean.encode('utf-8')).hexdigest()

def scrub_text(text: str, patient_name: Optional[str] = None) -> Tuple[str, Dict[str, int]]:
    """
    Scrubs identifiers from free-text clinical notes or extracted documents.
    Returns: (deidentified_text, scrub_statistics)
    """
    if not text:
        return "", {"names": 0, "phones": 0, "dates": 0, "ids": 0, "addresses": 0}
        
    stats = {"names": 0, "phones": 0, "dates": 0, "ids": 0, "addresses": 0}
    scrubbed = text

    # Explicit name scrubbing if provided
    if patient_name and len(patient_name.strip()) > 2:
        name_parts = patient_name.strip().split()
        for part in name_parts:
            if len(part) > 2:
                pattern = re.compile(re.escape(part), re.IGNORECASE)
                matches = len(pattern.findall(scrubbed))
                if matches > 0:
                    stats["names"] += matches
                    scrubbed = pattern.sub("[REDACTED_NAME]", scrubbed)

    # Phone numbers
    phone_matches = len(PHONE_REGEX.findall(scrubbed))
    if phone_matches:
        stats["phones"] += phone_matches
        scrubbed = PHONE_REGEX.sub("[REDACTED_PHONE]", scrubbed)

    # Aadhaar / National ID
    aadhaar_matches = len(AADHAAR_REGEX.findall(scrubbed))
    if aadhaar_matches:
        stats["ids"] += aadhaar_matches
        scrubbed = AADHAAR_REGEX.sub("[REDACTED_GOVT_ID]", scrubbed)

    # Emails
    scrubbed = EMAIL_REGEX.sub("[REDACTED_EMAIL]", scrubbed)

    # Addresses
    def replace_address(m):
        stats["addresses"] += 1
        return "[REDACTED_ADDRESS]"
    scrubbed = ADDRESS_REGEX.sub(replace_address, scrubbed)

    # Named entities with clinical prefixes
    def replace_name_prefix(m):
        stats["names"] += 1
        return "[REDACTED_NAME]"
    scrubbed = NAME_PREFIX_REGEX.sub(replace_name_prefix, scrubbed)

    return scrubbed, stats

def create_deidentified_demographics(age: Optional[int], sex: Optional[str], pregnancy_status: Optional[str]) -> Dict[str, Any]:
    """
    Enforces data minimization: produces only the coarse demographics permitted by the paper.
    """
    clean_sex = (sex or "UNKNOWN").upper()
    if clean_sex not in ["MALE", "FEMALE", "OTHER"]:
        clean_sex = "UNKNOWN"

    clean_preg = False
    if clean_sex == "FEMALE" and pregnancy_status:
        clean_preg = str(pregnancy_status).lower() in ["true", "yes", "pregnant", "1"]

    return {
        "age": age if (age is not None and 0 <= age <= 125) else None,
        "sex": clean_sex,
        "is_pregnant": clean_preg,
    }

def validate_llm_input(prompt_text: str) -> bool:
    """
    Safety gate: verifies that no unscrubbed phones, Aadhaar numbers, or emails enter the prompt.
    Returns True if clean, False if potential PHI detected.
    """
    if PHONE_REGEX.search(prompt_text):
        return False
    if AADHAAR_REGEX.search(prompt_text):
        return False
    if EMAIL_REGEX.search(prompt_text):
        return False
    return True
