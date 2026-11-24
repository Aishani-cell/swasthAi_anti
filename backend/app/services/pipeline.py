"""
SwasthAI End-to-End Multimodal Clinical Pipeline Orchestrator
Faithfully implements the Four-Stage Evidence Pipeline and Emergency Circuit Breaker.
"""
from typing import Dict, Any, Optional, List
from backend.app.schemas.patient import PatientCreate
from backend.app.schemas.vitals import VitalsInput
from backend.app.schemas.labs import ExtractedLabItem, ResolvedLabItem
from backend.app.schemas.symptoms import SymptomSummary
from backend.app.schemas.imaging import RadiologyReport
from backend.app.schemas.respiratory import RespiratoryAnalysisResult
from backend.app.schemas.evidence import EvidenceGraphModel
from backend.app.schemas.consultation import DiagnosisOutput, DrugRecommendationOutput

from backend.app.core.privacy import scrub_text, create_deidentified_demographics, hash_identifier
from backend.app.agents.symptom_agent.service import symptom_service
from backend.app.agents.lab_agent.service import lab_agent_service
from backend.app.agents.lab_resolver.resolver_service import lab_resolver_service
from backend.app.agents.vision_agent.service import vision_agent
from backend.app.ml.respiratory_service import run_respiratory_analysis
from backend.app.safety.engine import safety_engine
from backend.app.evidence.builder import build_evidence_graph
from backend.app.rag.service import rag_service
from backend.app.agents.diagnosis_agent.agent import diagnosis_agent
from backend.app.agents.drug_agent.agent import drug_agent
from backend.app.db.session import get_db_connection
from backend.app.core.tracer import tracer

class SwasthAIPipeline:
    @staticmethod
    def execute_consultation_pipeline(
        encounter_id: str,
        patient_info: Dict[str, Any],
        symptom_text: Optional[str] = None,
        vitals_data: Optional[Dict[str, Any]] = None,
        lab_items_raw: Optional[List[Dict[str, Any]]] = None,
        imaging_file_path: Optional[str] = None,
        imaging_report_text: Optional[str] = None,
        respiratory_file_path: Optional[str] = None,
        patient_allergies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes complete consultation through all 4 stages of the evidence pipeline.
        Guarantees independent emergency circuit breaker bypass.
        """
        missing_modalities: List[str] = []

        tracer.event(
            encounter_id,
            "pipeline",
            "consultation_pipeline",
            "STARTED",
            detail="Save Encounter and Generate Diagnosis triggered",
        )

        # --- STAGE 1: Demographics & Privacy Scrubbing ---
        age = patient_info.get("age")
        sex = patient_info.get("sex", "UNKNOWN")
        is_preg = patient_info.get("is_pregnant", False)
        demographics = create_deidentified_demographics(age, sex, is_preg)

        # --- STAGE 2: Modality-Specific Extraction ---
        # 1. Symptom NLP
        with tracer.stage(encounter_id, "symptom_nlp", "symptom_extraction"):
            if symptom_text and symptom_text.strip():
                scrubbed_symptoms, _ = scrub_text(symptom_text, patient_name=patient_info.get("full_name"))
                symptom_summary: SymptomSummary = symptom_service.process_symptoms(scrubbed_symptoms)
            else:
                symptom_summary = SymptomSummary(
                    extracted_symptoms=[],
                    negated_symptoms=[],
                    summary_text="No symptoms recorded.",
                    fallback_used=False
                )
                missing_modalities.append("symptoms")

        # 2. Vitals validation & Rule Engine
        with tracer.stage(encounter_id, "vitals_rule_engine", "vitals_validation"):
            vitals: Optional[VitalsInput] = None
            if vitals_data:
                try:
                    vitals = VitalsInput(**vitals_data)
                except Exception:
                    missing_modalities.append("vitals_invalid")
            else:
                missing_modalities.append("vitals")

        # 3. Laboratory extraction
        with tracer.stage(encounter_id, "laboratory_agent", "lab_extraction"):
            extracted_labs: List[ExtractedLabItem] = []
            if lab_items_raw and len(lab_items_raw) > 0:
                extracted_labs = lab_agent_service.extract_from_dict_list(lab_items_raw)
            else:
                missing_modalities.append("laboratory")

        # 4. Radiology vision agent
        with tracer.stage(encounter_id, "vision_agent", "radiology_analysis"):
            radiology_report: Optional[RadiologyReport] = None
            if imaging_file_path:
                radiology_report = vision_agent.process_image(imaging_file_path, reported_findings_text=imaging_report_text)
            else:
                missing_modalities.append("radiology_imaging")

        # 5. Respiratory acoustic AI
        with tracer.stage(encounter_id, "acoustic_agent", "respiratory_analysis"):
            respiratory_result: Optional[RespiratoryAnalysisResult] = None
            if respiratory_file_path:
                respiratory_result = run_respiratory_analysis(respiratory_file_path)
            else:
                missing_modalities.append("respiratory_audio")

        # --- STAGE 3: Laboratory Identity, Unit, and Plausibility Resolution (LOINC) ---
        with tracer.stage(encounter_id, "loinc_resolver", "loinc_triplet_resolution"):
            resolved_labs: List[ResolvedLabItem] = []
            if extracted_labs:
                resolved_labs = lab_resolver_service.resolve_items(extracted_labs)

        # --- STAGE 4: Deterministic Symbolic Safety & Emergency Circuit Breaker ---
        with tracer.stage(encounter_id, "safety_engine", "vitals_and_lab_safety_assessment"):
            alerts, vitals_class, cb_result = safety_engine.run_safety_assessment(
                vitals=vitals,
                labs=resolved_labs,
                age=demographics.get("age"),
                is_pregnant=demographics.get("is_pregnant", False)
            )

        # Build Verified EvidenceGraph
        with tracer.stage(encounter_id, "evidence_graph", "evidence_graph_construction"):
            evidence_graph = build_evidence_graph(
                encounter_id=encounter_id,
                demographics=demographics,
                symptoms=symptom_summary.extracted_symptoms,
                negated_symptoms=symptom_summary.negated_symptoms,
                vitals=vitals,
                vitals_classification=vitals_class,
                resolved_labs=resolved_labs,
                imaging_findings=[f.model_dump() for f in (radiology_report.findings if radiology_report else [])],
                respiratory_finding=respiratory_result,
                missing_modalities=missing_modalities,
                safety_alerts=alerts,
                circuit_breaker_tripped=cb_result.is_halted
            )

        # Gated Downstream Reasoning
        if cb_result.is_halted:
            # Emergency Circuit Breaker Tripped! Generative models are BLOCKED
            diagnosis_output = DiagnosisOutput(
                primary_diagnosis="Emergency Escalation Triggered",
                differential_diagnoses=[],
                evidence_citations=[cb_result.primary_reason],
                guideline_citations=[],
                missing_data_warnings=["Generative LLM bypass active: clinical safety rule triggered"],
                conditional_laboratory_findings=[],
                model_version="CircuitBreaker-SafetyBypass",
                physician_review_mandatory=True
            )
            drug_output = DrugRecommendationOutput(
                generic_drug_classes=[],
                clinical_context="All automated drug recommendations withheld during active emergency.",
                guideline_citations=[],
                contraindication_flags=["Emergency circuit breaker active"],
                caution_notes=cb_result.escalation_actions,
                physician_review_mandatory=True,
                no_brand_names_verified=True
            )
            rag_output = {
                "retrieval_status": "bypassed",
                "reason": "Emergency circuit breaker bypassed knowledge retrieval."
            }
        else:
            # Safe for Knowledge Grounding and CDSS Reasoning
            with tracer.stage(encounter_id, "rag_service", "guideline_retrieval"):
                rag_output = rag_service.retrieve_guidelines(evidence_graph)
            with tracer.stage(encounter_id, "diagnosis_agent", "differential_diagnosis_generation"):
                diagnosis_output = diagnosis_agent.generate_diagnosis(evidence_graph, rag_output)
            with tracer.stage(encounter_id, "drug_agent", "drug_class_recommendation"):
                drug_output = drug_agent.recommend_drug_classes(
                    diagnosis_output,
                    evidence_graph,
                    patient_allergies=patient_allergies,
                    guidelines_result=rag_output
                )

        tracer.event(
            encounter_id,
            "pipeline",
            "consultation_pipeline",
            "COMPLETED",
            detail=f"circuit_breaker_halted={cb_result.is_halted}",
        )
        tracer.event(
            encounter_id,
            "report_generator",
            "clinical_report",
            "COMPLETED",
            detail="Structured clinical report successfully assembled",
        )

        # Return full structured consultation dossier
        return {
            "encounter_id": encounter_id,
            "demographics": demographics,
            "missing_modalities": missing_modalities,
            "symptom_summary": symptom_summary.model_dump(),
            "vitals_classification": vitals_class,
            "resolved_labs": [l.model_dump() for l in resolved_labs],
            "radiology_report": radiology_report.model_dump() if radiology_report else None,
            "respiratory_result": respiratory_result.model_dump() if respiratory_result else None,
            "safety_assessment": {
                "circuit_breaker_halted": cb_result.is_halted,
                "safety_status": cb_result.safety_status,  # 'Approved' or 'Rejected'
                "primary_reason": cb_result.primary_reason,
                "escalation_actions": cb_result.escalation_actions,
                "alerts": [a.model_dump() for a in alerts]
            },
            "evidence_graph": evidence_graph.model_dump(),
            "rag_retrieval": rag_output,
            "diagnosis": diagnosis_output.model_dump(),
            "drug_recommendation": drug_output.model_dump(),
            "physician_review_mandatory": True
        }

pipeline = SwasthAIPipeline()
