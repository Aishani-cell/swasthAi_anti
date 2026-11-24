"""
Symptom Extractor Pipeline
Combines normalization, longest-phrase exact matching, Ratcliff-Obershelp fuzzy matching,
and 20-character negation detection.
"""
from typing import List, Dict, Any, Tuple, Optional
from backend.app.core.config import settings
from backend.app.core.ollama_client import ollama_client
from backend.app.schemas.symptoms import SymptomExtractionResult, SymptomSummary
from backend.app.agents.symptom_agent.normalizer import normalize_text
from backend.app.agents.symptom_agent.matcher import exact_phrase_matching, ratcliff_obershelp_fuzzy_matching, build_phrase_index
from backend.app.agents.symptom_agent.negation import check_negation
from backend.app.agents.symptom_agent.lexicon import SYMPTOM_LEXICON

# Canonical concepts available in the lexicon, used to validate LLM fallback output.
CANONICAL_CONCEPTS = {entry["canonical"] for entry in SYMPTOM_LEXICON}

# Prompt used only when the dictionary cannot resolve a phrase at all.
LLM_NORMALIZE_PROMPT = (
    "You are a careful clinical text normalizer for a rural healthpod decision-support tool.\n"
    "Translate the following patient symptom phrase (English, Hindi or Hinglish) into ONE short\n"
    "English symptom name. Reply with ONLY the English symptom name, nothing else.\n"
    "If the phrase is not a symptom, reply with exactly: NOT_A_SYMPTOM\n"
    "Phrase: \"{phrase}\"\n"
    "English symptom name:"
)

def _llm_normalize_unresolved(phrase: str) -> Optional[Dict[str, Any]]:
    """Ask the small local LLM to normalize an unresolved symptom phrase.

    Returns a dict with keys canonical, confidence, detail, or None when the
    LLM is unavailable or cannot confidently normalize the phrase.
    The original phrase is always preserved by the caller.
    """
    if not ollama_client.is_available():
        return None
    try:
        raw = ollama_client.generate(
            system_prompt="You are a clinical text normalizer. Reply with a single English symptom name or NOT_A_SYMPTOM.",
            user_prompt=LLM_NORMALIZE_PROMPT.format(phrase=phrase),
            temperature=0.0,
            max_tokens=32,
            timeout=60,
        )
    except Exception:
        return None
    if not raw:
        return None
    candidate = raw.strip().strip('"').strip("'").lower().rstrip(".")
    if candidate == "not_a_symptom" or not candidate:
        return None
    # Accept only if it maps to a known canonical concept (exact or fuzzy).
    best = None
    best_score = 0.0
    for concept in CANONICAL_CONCEPTS:
        score = __import__("difflib").SequenceMatcher(None, candidate, concept.replace("_", " ")).ratio()
        if score > best_score:
            best_score = score
            best = concept
    if best and best_score >= 0.80:
        return {"canonical": best, "confidence": 0.60, "detail": f"LLM normalized '{phrase}' to '{best}'"}
    return None

def extract_symptoms(text: str) -> SymptomSummary:
    """
    Extracts structured symptoms from multilingual clinical text.
    Implements Equations (1) and (2) from the paper.
    """
    if not text or not text.strip():
        return SymptomSummary(
            extracted_symptoms=[],
            negated_symptoms=[],
            summary_text="No symptoms recorded.",
            fallback_used=False
        )

    norm_text = normalize_text(text)
    
    # 1. Exact longest-phrase matching
    exact_matches, claimed_spans = exact_phrase_matching(norm_text)
    
    # 2. Ratcliff-Obershelp fuzzy matching (tau = 0.90) on remaining tokens
    fuzzy_matches = ratcliff_obershelp_fuzzy_matching(
        norm_text,
        claimed_spans,
        threshold=settings.RATCLIFF_OBERSHELP_THRESHOLD
    )
    
    all_raw_matches = exact_matches + fuzzy_matches
    
    extracted: List[SymptomExtractionResult] = []
    negated: List[SymptomExtractionResult] = []
    seen_concepts = set()

    # 3. Negation handling and result structuring
    for m in all_raw_matches:
        concept = m["canonical"]
        is_neg, cue = check_negation(
            norm_text,
            m["start"],
            m["end"],
            delta=settings.NEGATION_LOOKAHEAD_CHARS
        )
        
        result_item = SymptomExtractionResult(
            canonical_concept=concept,
            original_phrase=m["span_text"],
            language=m["language"],
            is_negated=is_neg,
            extraction_method=m["method"],
            confidence_score=m["confidence"],
            source_span=f"[{m['start']}:{m['end']}]",
            verification_status="VERIFIED"
        )
        
        # Deduplicate multiple matches of the same concept in same polarity
        key = (concept, is_neg)
        if key not in seen_concepts:
            seen_concepts.add(key)
            if is_neg:
                negated.append(result_item)
            else:
                extracted.append(result_item)

    # 4. Fallback check: if |R_lex| < eta (eta = 1)
    fallback_used = False
    if len(extracted) == 0 and len(negated) == 0:
        # Lexicon failure fallback: try the local LLM before giving up
        fallback_used = True
        stripped = norm_text.strip()
        if stripped:
            llm_result = _llm_normalize_unresolved(stripped)
            if llm_result is not None:
                is_neg, _ = check_negation(norm_text, 0, len(norm_text), delta=settings.NEGATION_LOOKAHEAD_CHARS)
                result_item = SymptomExtractionResult(
                    canonical_concept=llm_result["canonical"],
                    original_phrase=stripped,
                    language="hinglish",
                    is_negated=is_neg,
                    extraction_method="LLM_FALLBACK",
                    confidence_score=llm_result["confidence"],
                    source_span=f"[0:{len(norm_text)}]",
                    verification_status="VERIFIED",
                )
                key = (llm_result["canonical"], is_neg)
                if is_neg:
                    negated.append(result_item)
                else:
                    extracted.append(result_item)
    if len(extracted) == 0 and len(negated) == 0:
        unresolved_phrases = [norm_text.strip()] if norm_text.strip() else []
    else:
        unresolved_phrases = []

    # 5. Build canonical summary text
    pos_phrases = [f"{s.canonical_concept} ({s.original_phrase})" for s in extracted]
    neg_phrases = [f"no {s.canonical_concept}" for s in negated]

    summary_parts = []
    if pos_phrases:
        summary_parts.append("Reported symptoms: " + ", ".join(pos_phrases))
    if neg_phrases:
        summary_parts.append("Denies: " + ", ".join(neg_phrases))
    if unresolved_phrases:
        summary_parts.append("Unresolved phrases: " + ", ".join(unresolved_phrases))
    if not summary_parts:
        summary_parts.append("No recognized clinical symptoms extracted.")

    summary_text = ". ".join(summary_parts) + "."

    return SymptomSummary(
        extracted_symptoms=extracted,
        negated_symptoms=negated,
        summary_text=summary_text,
        fallback_used=fallback_used
    )
