"""
SwasthAI Consultation Report Generator
Generates clinical consultation summaries in Markdown, JSON, and print-ready formats.
Strictly excludes direct patient identifiers and includes mandatory CDSS disclaimers.
"""
import json
import datetime
from typing import Dict, Any
from pathlib import Path
from backend.app.core.config import settings

class ReportGenerator:
    @staticmethod
    def generate_json_report(dossier: Dict[str, Any], file_path: str = None) -> str:
        """Serializes consultation dossier to formatted JSON."""
        content = json.dumps(dossier, indent=2, ensure_ascii=False)
        if file_path:
            p = Path(file_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
        return content

    @staticmethod
    def generate_markdown_report(dossier: Dict[str, Any], file_path: str = None) -> str:
        """Generates a clean, print-ready clinical consultation report in Markdown."""
        enc_id = dossier["encounter_id"]
        dem = dossier["demographics"]
        eg = dossier["evidence_graph"]
        safety = dossier["safety_assessment"]
        diag = dossier["diagnosis"]
        drug = dossier["drug_recommendation"]
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = []
        lines.append("# SWASTHAI CLINICAL DECISION SUPPORT SUMMARY")
        lines.append(f"**Deployment Site**: Satnavari Primary Healthpod, Maharashtra | **Report Date**: {now_str}")
        lines.append(f"**Encounter ID**: `{enc_id}` | **Integrity Checksum**: `{eg.get('integrity_hash', '')[:16]}...`\n")
        lines.append("---")
        
        # 1. Demographics
        lines.append("### 1. Patient Context (De-identified Coarse Demographics)")
        lines.append(f"- **Age**: {dem.get('age', 'Unspecified')} years")
        lines.append(f"- **Sex**: {dem.get('sex', 'Unknown')}")
        lines.append(f"- **Pregnancy Status**: {'Yes (Active Pregnancy Protocol)' if dem.get('is_pregnant') else 'No'}\n")

        # 2. Symptoms
        lines.append("### 2. Symptom Presentation (Bilingual NLP)")
        s_sum = dossier.get("symptom_summary", {})
        lines.append(f"- {s_sum.get('summary_text', 'No symptoms extracted.')}\n")

        # 3. Vitals
        lines.append("### 3. Vital Signs & Physiologic Triage")
        v = eg.get("vitals")
        if v:
            lines.append(f"- **Blood Pressure**: {v.get('systolic_bp', '-')} / {v.get('diastolic_bp', '-')} mmHg ({dossier.get('vitals_classification', {}).get('blood_pressure', '')})")
            lines.append(f"- **Heart Rate**: {v.get('heart_rate', '-')} bpm | **Respiratory Rate**: {v.get('respiratory_rate', '-')} /min")
            lines.append(f"- **SpO2**: {v.get('spo2', '-')} % | **Core Temp**: {v.get('temperature_c', '-')} °C")
            if v.get('blood_glucose_mg_dl'):
                lines.append(f"- **Random Blood Sugar**: {v.get('blood_glucose_mg_dl')} mg/dL")
        else:
            lines.append("- *Vital signs not recorded.*\n")

        # 4. Laboratory Results
        lines.append("\n### 4. Verified Laboratory Values (LOINC Resolved)")
        labs = eg.get("resolved_labs", [])
        if labs:
            lines.append("| Analyte | Result | Unit | Reference | LOINC | Status | Flag |")
            lines.append("|---|---|---|---|---|---|---|")
            for l in labs:
                flag = l.get("plausibility_flag") or "NORMAL"
                lines.append(f"| {l['canonical_name']} | {l['numeric_value']} | {l['canonical_unit']} | {l['reference_interval']} | {l.get('loinc_code', '-')} | {l['verification_status']} | **{flag}** |")
        else:
            lines.append("- *No laboratory results collected.*\n")

        # 5. Radiology & Respiratory Acoustics
        lines.append("\n### 5. Multimodal Diagnostics (Radiology & Lung Acoustics)")
        rad = dossier.get("radiology_report")
        if rad and rad.get("findings"):
            lines.append(f"- **Imaging ({rad.get('modality')})**: {rad.get('summary_text')}")
        else:
            lines.append("- **Imaging**: Not acquired for this encounter.")

        resp = dossier.get("respiratory_result")
        if resp:
            lines.append(f"- **Respiratory Acoustic AI**: Classified as **{resp.get('predicted_class', '').upper()}** (Confidence: {resp.get('confidence', 0.0):.2f}) | Quality: {resp.get('quality_status')}")
        else:
            lines.append("- **Respiratory Audio**: Not recorded.")

        # 6. Safety & Circuit Breaker
        lines.append("\n### 6. Deterministic Safety Assessment & Circuit Breaker")
        status_color = "EMERGENCY HALTED (REJECTED)" if safety.get("circuit_breaker_halted") else "APPROVED (NON-CRITICAL)"
        lines.append(f"- **Circuit Breaker Status**: **{status_color}**")
        lines.append(f"- **Assessment Summary**: {safety.get('primary_reason')}")
        if safety.get("escalation_actions"):
            lines.append("\n**Emergency Actions Required:**")
            for act in safety["escalation_actions"]:
                lines.append(f"  > [!CAUTION] {act}")

        # 7. Knowledge Retrieval & Guidelines
        lines.append("\n### 7. Retrieved Clinical Guidelines (RAG)")
        rag = dossier.get("rag_retrieval", {})
        if rag.get("retrieval_status") == "available" and rag.get("chunks"):
            for c in rag["chunks"]:
                lines.append(f"- **{c['doc_title']}** ({c['publisher']} {c['year']}, p. {c['page']})")
                lines.append(f"  *Section*: {c['section']} | Similarity: {c['cosine_similarity']}")
        else:
            lines.append(f"- *Guideline Retrieval Status*: {rag.get('retrieval_status', 'unavailable')} ({rag.get('reason', 'N/A')})")

        # 8. Diagnostic Hypotheses
        lines.append("\n### 8. Diagnostic Hypotheses (Constrained Multi-Agent CDSS)")
        lines.append(f"- **Primary Hypothesis**: **{diag.get('primary_diagnosis')}**")
        if diag.get("differential_diagnoses"):
            lines.append(f"- **Differentials**: {', '.join(diag['differential_diagnoses'])}")
        if diag.get("missing_data_warnings"):
            lines.append(f"- **Data Completeness Warnings**: {', '.join(diag['missing_data_warnings'])}")

        # 9. Drug-Class Recommendations
        lines.append("\n### 9. Guideline-Directed Generic Drug Classes")
        if drug.get("generic_drug_classes"):
            for d in drug["generic_drug_classes"]:
                lines.append(f"- **{d}**")
            lines.append(f"\n*Clinical Context*: {drug.get('clinical_context')}")
        else:
            lines.append("- *No automatic drug classes indicated or recommendations withheld by safety circuit breaker.*")

        if drug.get("contraindication_flags"):
            lines.append("\n**Contraindication Alerts:**")
            for cf in drug["contraindication_flags"]:
                lines.append(f"- {cf}")

        # 10. Legal & Medical Review Disclaimer
        lines.append("\n---")
        lines.append("### 10. Mandatory Clinician Attestation")
        lines.append("> **CLINICAL NOTICE**: This report is an AI-generated clinical decision support aid designed under the SwasthAI research framework. It does NOT constitute a confirmed medical diagnosis or a prescription. All therapeutic decisions must be verified and signed by a registered medical practitioner.")
        lines.append("\n\n**Reviewing Clinician Signature**: ___________________________ | **Date**: ______________")

        md_content = "\n".join(lines)
        if file_path:
            p = Path(file_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(md_content)

        return md_content

report_generator = ReportGenerator()
