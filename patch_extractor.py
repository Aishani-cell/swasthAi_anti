import re
path = 'c:/Users/Aishani/Downloads/swasthAi/backend/app/agents/symptom_agent/extractor.py'
data = open(path, encoding='utf-8').read()

start_marker = '    # 4. Fallback check: if |R_lex| < eta (eta = 1)'
end_marker = '        fallback_used=fallback_used\n    )'
si = data.index(start_marker)
ei = data.index(end_marker) + len(end_marker)

new_block = '''    # 4. Fallback check: if |R_lex| < eta (eta = 1)
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
    )'''

data = data[:si] + new_block + data[ei:]
open(path, 'w', encoding='utf-8').write(data)
print("patched")
