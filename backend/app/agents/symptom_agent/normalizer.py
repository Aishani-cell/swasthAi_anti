"""
Symptom Text Normalizer
Handles Unicode NFKC normalization, whitespace standardization, and punctuation cleansing
while preserving Devanagari characters for Hindi text.
"""
import unicodedata
import re

def normalize_text(text: str) -> str:
    """Standardizes input text for symptom matching."""
    if not text:
        return ""
    # Unicode NFKC normalization
    text = unicodedata.normalize('NFKC', text)
    # Lowercase
    text = text.lower()
    # Replace newlines, tabs, and multiple spaces with a single space
    text = re.sub(r'[\r\n\t]+', ' ', text)
    # Strip unnecessary trailing/leading punctuation but keep characters & spaces
    text = re.sub(r'[,;:\(\)\[\]\{\}\*\/\\_\-]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
