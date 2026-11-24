"""
Symptom Matcher Module
Implements Section 3.4 of the SwasthAI paper:
- Longest-phrase matching first over bilingual lexicon
- Ratcliff-Obershelp similarity ratio with threshold tau_fuzzy = 0.90 (using difflib.SequenceMatcher)
"""
import difflib
import re
from typing import List, Dict, Any, Tuple
from backend.app.agents.symptom_agent.lexicon import SYMPTOM_LEXICON

def build_phrase_index() -> List[Dict[str, Any]]:
    index = []
    for entry in SYMPTOM_LEXICON:
        canonical = entry["canonical"]
        category = entry["category"]
        for phrase in entry["english"]:
            index.append({"phrase": phrase.lower(), "canonical": canonical, "lang": "en", "category": category})
        for phrase in entry["hindi"]:
            index.append({"phrase": phrase.lower(), "canonical": canonical, "lang": "hi", "category": category})
        for phrase in entry["hinglish"]:
            index.append({"phrase": phrase.lower(), "canonical": canonical, "lang": "hinglish", "category": category})
    index.sort(key=lambda x: len(x["phrase"]), reverse=True)
    return index

def exact_phrase_matching(text: str) -> Tuple[List[Dict[str, Any]], List[Tuple[int, int]]]:
    phrase_index = build_phrase_index()
    matches = []
    matched_spans = []
    lower_text = text.lower()

    for item in phrase_index:
        phrase = item["phrase"]
        canonical = item["canonical"]
        lang = item["lang"]

        escaped_phrase = re.escape(phrase)
        pattern = re.compile(rf'(?:\b|^){escaped_phrase}(?:\b|$)', re.IGNORECASE)

        for match in pattern.finditer(lower_text):
            start, end = match.start(), match.end()
            overlap = any(not (end <= m_start or start >= m_end) for m_start, m_end in matched_spans)
            if not overlap:
                matched_spans.append((start, end))
                matches.append({
                    "canonical": canonical,
                    "phrase": phrase,
                    "language": lang,
                    "method": "LEXICON_EXACT",
                    "confidence": 1.0,
                    "start": start,
                    "end": end,
                    "span_text": text[start:end]
                })

    return matches, matched_spans

def ratcliff_obershelp_fuzzy_matching(
    text: str,
    claimed_spans: List[Tuple[int, int]],
    threshold: float = 0.90
) -> List[Dict[str, Any]]:
    phrase_index = build_phrase_index()
    fuzzy_matches = []
    words = text.split()
    if not words:
        return fuzzy_matches

    for n in range(min(5, len(words)), 0, -1):
        for i in range(len(words) - n + 1):
            candidate_words = words[i:i + n]
            candidate_phrase = " ".join(candidate_words).lower()
            
            cand_start = text.lower().find(candidate_phrase)
            if cand_start == -1:
                continue
            cand_end = cand_start + len(candidate_phrase)

            if any(not (cand_end <= m_start or cand_start >= m_end) for m_start, m_end in claimed_spans):
                continue

            best_score = 0.0
            best_item = None
            for item in phrase_index:
                target_len = len(item["phrase"])
                cand_len = len(candidate_phrase)
                if abs(target_len - cand_len) > 5:
                    continue

                ratio = difflib.SequenceMatcher(None, candidate_phrase, item["phrase"]).ratio()
                if ratio >= threshold and ratio > best_score:
                    best_score = ratio
                    best_item = item

            if best_item and best_score >= threshold:
                claimed_spans.append((cand_start, cand_end))
                fuzzy_matches.append({
                    "canonical": best_item["canonical"],
                    "phrase": candidate_phrase,
                    "matched_alias": best_item["phrase"],
                    "language": best_item["lang"],
                    "method": "RATCLIFF_OBERSHELP",
                    "confidence": round(best_score, 3),
                    "start": cand_start,
                    "end": cand_end,
                    "span_text": text[cand_start:cand_end]
                })

    return fuzzy_matches
