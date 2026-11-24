"""
EvidenceGraph Builder Module
Assembles normalized clinical findings into the canonical EvidenceGraph structure.
"""
import uuid
import datetime
from typing import Optional, List, Dict, Any
from backend.app.schemas.evidence import EvidenceGraphModel, SafetyAlert
from backend.app.schemas.vitals import VitalsInput
from backend.app.schemas.symptoms import SymptomExtractionResult
from backend.app.schemas.labs import ResolvedLabItem
from backend.app.schemas.respiratory import RespiratoryAnalysisResult
from backend.app.evidence.serializer import serialize_evidence_graph, compute_graph_hash

def build_evidence_graph(
    encounter_id: str,
    demographics: Dict[str, Any],
    symptoms: List[SymptomExtractionResult],
    negated_symptoms: List[SymptomExtractionResult],
    vitals: Optional[VitalsInput],
    vitals_classification: Dict[str, str],
    resolved_labs: List[ResolvedLabItem],
    imaging_findings: List[Dict[str, Any]],
    respiratory_finding: Optional[RespiratoryAnalysisResult],
    missing_modalities: List[str],
    safety_alerts: List[SafetyAlert],
    circuit_breaker_tripped: bool,
    version: int = 1
) -> EvidenceGraphModel:
    """
    Constructs and signs a verified EvidenceGraph.
    """
    graph_id = f"eg-{uuid.uuid4().hex[:12]}"
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Pre-model assembly
    graph_dict = {
        "graph_id": graph_id,
        "encounter_id": encounter_id,
        "version": version,
        "timestamp": timestamp,
        "demographics": demographics,
        "symptoms": [s.model_dump() for s in symptoms],
        "negated_symptoms": [s.model_dump() for s in negated_symptoms],
        "vitals": vitals.model_dump() if vitals else None,
        "vitals_classification": vitals_classification,
        "resolved_labs": [l.model_dump() for l in resolved_labs],
        "imaging_findings": imaging_findings,
        "respiratory_finding": respiratory_finding.model_dump() if respiratory_finding else None,
        "missing_modalities": missing_modalities,
        "safety_alerts": [a.model_dump() for a in safety_alerts],
        "circuit_breaker_tripped": circuit_breaker_tripped,
        "human_review_required": True
    }

    serialized = serialize_evidence_graph(graph_dict)
    integrity_hash = compute_graph_hash(serialized)

    return EvidenceGraphModel(
        graph_id=graph_id,
        encounter_id=encounter_id,
        version=version,
        timestamp=timestamp,
        demographics=demographics,
        symptoms=symptoms,
        negated_symptoms=negated_symptoms,
        vitals=vitals,
        vitals_classification=vitals_classification,
        resolved_labs=resolved_labs,
        imaging_findings=imaging_findings,
        respiratory_finding=respiratory_finding,
        missing_modalities=missing_modalities,
        safety_alerts=safety_alerts,
        circuit_breaker_tripped=circuit_breaker_tripped,
        integrity_hash=integrity_hash,
        human_review_required=True
    )

def format_evidence_graph_text(graph: EvidenceGraphModel) -> str:
    """
    Formats the verified EvidenceGraph into clean, structured prompt text for downstream reasoning agents.
    Excludes any unverified raw notes or direct patient identifiers.
    """
    lines = []
    lines.append("=== CERTIFIED EVIDENCE GRAPH ===")
    lines.append(f"Demographics: Age {graph.demographics.get('age', 'Unknown')}, Sex {graph.demographics.get('sex', 'Unknown')}, Pregnant: {graph.demographics.get('is_pregnant', False)}")

    # Symptoms
    if graph.symptoms:
        pos_symptoms = [f"{s.canonical_concept} (source: '{s.original_phrase}')" for s in graph.symptoms]
        lines.append(f"Positive Symptoms: {', '.join(pos_symptoms)}")
    else:
        lines.append("Positive Symptoms: None reported")

    if graph.negated_symptoms:
        neg_symptoms = [f"NOT {s.canonical_concept}" for s in graph.negated_symptoms]
        lines.append(f"Negated/Denied Symptoms: {', '.join(neg_symptoms)}")

    # Vitals
    if graph.vitals:
        v = graph.vitals
        v_parts = []
        if v.systolic_bp and v.diastolic_bp:
            v_parts.append(f"BP {v.systolic_bp:.0f}/{v.diastolic_bp:.0f} mmHg ({graph.vitals_classification.get('blood_pressure', 'Staged')})")
        if v.heart_rate:
            v_parts.append(f"HR {v.heart_rate:.0f} bpm ({graph.vitals_classification.get('pulse', '')})")
        if v.spo2:
            v_parts.append(f"SpO2 {v.spo2:.1f}% ({graph.vitals_classification.get('oxygenation', '')})")
        if v.temperature_c:
            v_parts.append(f"Temp {v.temperature_c:.1f}°C")
        if v.blood_glucose_mg_dl:
            v_parts.append(f"Glucose {v.blood_glucose_mg_dl:.0f} mg/dL")
        lines.append(f"Vital Signs: {', '.join(v_parts)}")
    else:
        lines.append("Vital Signs: Not recorded")

    # Resolved Labs
    if graph.resolved_labs:
        lines.append("Verified Laboratory Values:")
        for lab in graph.resolved_labs:
            flag = f" [{lab.plausibility_flag}]" if lab.plausibility_flag and lab.plausibility_flag != "NORMAL" else ""
            loinc = f" (LOINC: {lab.loinc_code})" if lab.loinc_code else ""
            lines.append(f"  - {lab.canonical_name}: {lab.numeric_value} {lab.canonical_unit} (Ref: {lab.reference_interval}){flag}{loinc}")
    else:
        lines.append("Laboratory Values: None available")

    # Respiratory
    if graph.respiratory_finding:
        rf = graph.respiratory_finding
        narrative = f" Narrative: {rf.respllm_narrative}" if rf.respllm_narrative else ""
        lines.append(
            f"Respiratory Acoustics: Acoustic Class='{rf.predicted_class}' "
            f"(Confidence: {rf.confidence:.2f}, source={rf.dataset_source}).{narrative}"
        )

    # Imaging
    if graph.imaging_findings:
        lines.append("Imaging Findings:")
        for im in graph.imaging_findings:
            lines.append(f"  - {im.get('observation', '')}")

    # Missing Modalities
    if graph.missing_modalities:
        lines.append(f"Explicit Missing Modalities: {', '.join(graph.missing_modalities)}")

    lines.append(f"Integrity Checksum: SHA-256:{graph.integrity_hash[:16]}...")
    lines.append("================================")
    return "\n".join(lines)
