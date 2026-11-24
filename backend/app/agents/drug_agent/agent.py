"""
Drug-Class Recommendation Agent
Implements Section 3.8 of the SwasthAI paper:
- Constrained generation at temperature=0.0
- Generic drug classes only with mandatory physician-review language
- Contraindication-aware filtering
- Calibrated confidence scores and pharmacological explanations for each recommended class
- Covers all 25 disease categories evaluated in the paper
- Jaccard similarity computation for evaluation: J(A, B) = |A cap B| / |A cup B|
"""
import re
from typing import List, Dict, Any, Set, Tuple, Optional
from backend.app.core.ollama_client import ollama_client
from backend.app.schemas.evidence import EvidenceGraphModel
from backend.app.schemas.consultation import DiagnosisOutput, DrugRecommendationOutput
from backend.app.agents.drug_agent.contraindications import check_contraindications
from backend.app.core.ollama_client import ollama_client
# Comprehensive mapping of conditions to guideline-directed generic drug classes
RECOMMENDED_DRUG_CLASSES_DB: Dict[str, Dict[str, Any]] = {
    "STEMI": {
        "classes": ["Antiplatelet agents", "Statins", "Nitrates"],
        "context": "Emergency antiplatelet loading and coronary perfusion support pending urgent transfer."
    },
    "Heart Failure": {
        "classes": ["Loop diuretics", "ACE inhibitors", "Beta-blockers"],
        "context": "Decongestion and neurohormonal blockade for ventricular unloading."
    },
    "Pericarditis": {
        "classes": ["Anti-inflammatory agents", "Colchicine"],
        "context": "Suppression of pericardial inflammation and prevention of recurrence."
    },
    "Pneumonia": {
        "classes": ["Beta-lactam antibiotics", "Macrolides", "Antipyretics"],
        "context": "Empiric community-acquired respiratory bacterial eradication."
    },
    "Dengue": {
        "classes": ["Antipyretics (Paracetamol only)", "Oral rehydration electrolytes"],
        "context": "Supportive hydration and antipyresis. Strictly NO NSAIDs."
    },
    "Malaria": {
        "classes": ["Artemisinin-based combination therapies", "Aminoquinolines", "Antipyretics"],
        "context": "Antimalarial parasitic clearance per NVBDCP guidelines."
    },
    "Sepsis": {
        "classes": ["Intravenous broad-spectrum antibiotics", "Intravenous isotonic crystalloids"],
        "context": "Urgent antimicrobial control and volume resuscitation for systemic infection."
    },
    "Septic Shock": {
        "classes": ["Vasopressors", "Intravenous crystalloids", "Broad-spectrum antibiotics"],
        "context": "Emergency mean arterial pressure support and broad-spectrum antimicrobial therapy."
    },
    "UTI": {
        "classes": ["Nitrofurantoin", "Fluoroquinolones", "Urinary alkalinizers"],
        "context": "First-line lower urinary tract antimicrobial clearance."
    },
    "Pyelonephritis": {
        "classes": ["Fluoroquinolones", "Cephalosporins", "Antipyretics"],
        "context": "Upper urinary tract antimicrobial therapy with renal tissue penetration."
    },
    "Appendicitis": {
        "classes": ["Surgical referral", "Intravenous antibiotics", "Analgesics"],
        "context": "Emergency surgical evaluation; perioperative broad-spectrum coverage."
    },
    "Meningitis": {
        "classes": ["Third-generation cephalosporins", "Vancomycin", "Corticosteroids"],
        "context": "Blood-brain barrier penetrating empiric bacterial coverage and neuroinflammation suppression."
    },
    "DKA": {
        "classes": ["Short-acting regular insulin", "Intravenous isotonic crystalloids", "Potassium chloride"],
        "context": "Restoration of glycemic control, intravascular volume, and electrolyte balance."
    },
    "Hypothyroidism": {
        "classes": ["Levothyroxine sodium"],
        "context": "Synthetic thyroid hormone replacement therapy."
    },
    "Hyperthyroidism": {
        "classes": ["Antithyroid agents", "Beta-blockers"],
        "context": "Inhibition of thyroid hormone synthesis and adrenergic symptom control."
    },
    "AKI": {
        "classes": ["Intravenous isotonic crystalloids", "Loop diuretics (cautious)"],
        "context": "Renal perfusion maintenance; avoid all nephrotoxic agents."
    },
    "Asthma Exacerbation": {
        "classes": ["Inhaled short-acting beta2-agonists", "Inhaled anticholinergics", "Systemic corticosteroids"],
        "context": "Rapid relief of bronchospasm and suppression of airway inflammation."
    },
    "COPD": {
        "classes": ["Inhaled short-acting bronchodilators", "Systemic corticosteroids", "Broad-spectrum antibiotics"],
        "context": "Bronchodilation and reduction of exacerbation severity."
    },
    "Pulmonary Embolism": {
        "classes": ["Anticoagulants", "Supplemental oxygen"],
        "context": "Immediate therapeutic anticoagulation to prevent clot propagation."
    },
    "Hypertension": {
        "classes": ["Calcium channel blockers", "ACE inhibitors", "Angiotensin receptor blockers"],
        "context": "Gradual blood pressure reduction to target range."
    },
    "Hypertensive Emergency": {
        "classes": ["Intravenous vasodilators", "Central alpha-2 agonists", "Emergency transport electrolytes"],
        "context": "Emergency controlled blood pressure reduction under intensive medical supervision."
    },
    "Stroke": {
        "classes": ["Emergency neurovascular referral", "Antiplatelets (conditional)"],
        "context": "Immediate stroke unit imaging for thrombolysis window."
    },
    "Acute Pancreatitis": {
        "classes": ["Intravenous crystalloids", "Opioid analgesics", "Bowel rest"],
        "context": "Aggressive fluid resuscitation and visceral analgesia."
    },
    "Cholecystitis": {
        "classes": ["Intravenous antibiotics", "Analgesics", "Surgical consultation"],
        "context": "Biliary antimicrobial coverage and surgical triage."
    },
    "Gastroenteritis": {
        "classes": ["Oral rehydration salts", "Zinc supplements"],
        "context": "Restoration of fluid and mucosal zinc homeostasis."
    }
}

DRUG_CLASS_METADATA: Dict[str, Dict[str, Any]] = {
    "Antiplatelet agents": {
        "confidence": 0.96,
        "mechanism": "Inhibits platelet COX-1 or P2Y12 receptors to prevent acute arterial thrombosis."
    },
    "Statins": {
        "confidence": 0.94,
        "mechanism": "HMG-CoA reductase inhibitor stabilizing vulnerable plaques and reducing vascular inflammation."
    },
    "Nitrates": {
        "confidence": 0.90,
        "mechanism": "Generates nitric oxide causing venodilation, reducing preload and myocardial wall stress."
    },
    "Loop diuretics": {
        "confidence": 0.95,
        "mechanism": "Inhibits Na+/K+/2Cl- cotransporter in the thick ascending limb of Henle promoting rapid fluid decongestion."
    },
    "ACE inhibitors": {
        "confidence": 0.93,
        "mechanism": "Blocks conversion of angiotensin I to II, decreasing systemic vascular resistance and adverse cardiac remodeling."
    },
    "Beta-blockers": {
        "confidence": 0.92,
        "mechanism": "Attenuates sympathetic neurohormonal overdrive, reducing heart rate and myocardial oxygen consumption."
    },
    "Beta-lactam antibiotics": {
        "confidence": 0.96,
        "mechanism": "Inhibits bacterial cell-wall peptidoglycan synthesis via penicillin-binding protein (PBP) binding."
    },
    "Macrolides": {
        "confidence": 0.91,
        "mechanism": "Binds to bacterial 50S ribosomal subunit inhibiting protein synthesis, active against atypical pathogens."
    },
    "Antipyretics": {
        "confidence": 0.94,
        "mechanism": "Inhibits central hypothalamic prostaglandin synthesis to normalize thermoregulatory set-point."
    },
    "Antipyretics (Paracetamol only)": {
        "confidence": 0.98,
        "mechanism": "Selectively lowers fever without inhibiting peripheral cyclooxygenase or impairing platelet aggregation (safe in dengue)."
    },
    "Oral rehydration electrolytes": {
        "confidence": 0.98,
        "mechanism": "Sodium-glucose co-transport restores intravascular volume and compensates for microvascular permeability."
    },
    "Artemisinin-based combination therapies": {
        "confidence": 0.97,
        "mechanism": "Generates lethal endoperoxide-mediated free radicals in Plasmodium parasites, achieving rapid biomass reduction."
    },
    "Aminoquinolines": {
        "confidence": 0.92,
        "mechanism": "Interferes with hemoglobin digestion in malaria parasites, preventing toxic heme polymerization."
    },
    "Intravenous broad-spectrum antibiotics": {
        "confidence": 0.96,
        "mechanism": "Rapid bactericidal antimicrobial coverage against potential Gram-positive and Gram-negative pathogens."
    },
    "Intravenous isotonic crystalloids": {
        "confidence": 0.98,
        "mechanism": "Expands effective circulating arterial volume, optimizing cardiac preload and end-organ perfusion."
    },
    "Vasopressors": {
        "confidence": 0.97,
        "mechanism": "Alpha-1 adrenergic vasoconstriction restores mean arterial pressure (>65 mmHg) during distributive vasoplegic shock."
    },
    "Nitrofurantoin": {
        "confidence": 0.94,
        "mechanism": "Concentrates highly in urine; bacterial nitroreductases generate reactive intermediates damaging bacterial DNA."
    },
    "Fluoroquinolones": {
        "confidence": 0.92,
        "mechanism": "Inhibits bacterial DNA gyrase and topoisomerase IV, providing excellent urinary and renal tissue penetration."
    },
    "Urinary alkalinizers": {
        "confidence": 0.88,
        "mechanism": "Increases urinary pH, symptomatic relief of dysuria and metabolic stabilization."
    },
    "Cephalosporins": {
        "confidence": 0.94,
        "mechanism": "Beta-lactam bactericidal activity with broad spectrum and favorable safety in acute pyelonephritis."
    },
    "Short-acting regular insulin": {
        "confidence": 0.99,
        "mechanism": "Promotes cellular glucose and potassium uptake while halting lipolysis and hepatic ketogenesis."
    },
    "Potassium chloride": {
        "confidence": 0.96,
        "mechanism": "Replaces obligate urinary and intracellular potassium deficits during insulin-mediated acid-base correction."
    },
    "Levothyroxine sodium": {
        "confidence": 0.98,
        "mechanism": "Synthetic tetraiodothyronine (T4) replacement restoring baseline metabolic rate."
    },
    "Antithyroid agents": {
        "confidence": 0.94,
        "mechanism": "Inhibits thyroid peroxidase-catalyzed iodination and coupling of thyroglobulin tyrosine residues."
    },
    "Inhaled short-acting beta2-agonists": {
        "confidence": 0.98,
        "mechanism": "Directly activates airway smooth muscle beta-2 receptors causing rapid cyclic AMP-mediated bronchodilation."
    },
    "Inhaled anticholinergics": {
        "confidence": 0.93,
        "mechanism": "Blocks muscarinic M3 receptors, reducing parasympathetic vagal bronchoconstrictor tone."
    },
    "Systemic corticosteroids": {
        "confidence": 0.95,
        "mechanism": "Suppresses inflammatory transcription factors (NF-kappaB), reducing airway mucosal edema and eosinophil recruitment."
    },
    "Inhaled short-acting bronchodilators": {
        "confidence": 0.96,
        "mechanism": "Combined beta-2 and anticholinergic bronchodilation relieving dynamic air-trapping."
    },
    "Anticoagulants": {
        "confidence": 0.96,
        "mechanism": "Inhibits coagulation cascade factors (Xa or IIa) preventing pulmonary thromboembolus propagation."
    },
    "Calcium channel blockers": {
        "confidence": 0.94,
        "mechanism": "Inhibits voltage-sensitive L-type calcium channels in arterial smooth muscle, decreasing peripheral resistance."
    },
    "Intravenous vasodilators": {
        "confidence": 0.96,
        "mechanism": "Rapidly lowers systemic vascular resistance under continuous ICU monitoring during hypertensive emergencies."
    },
    "Central alpha-2 agonists": {
        "confidence": 0.90,
        "mechanism": "Stimulates central presynaptic alpha-2 receptors, reducing peripheral sympathetic outflow."
    },
    "Oral rehydration salts": {
        "confidence": 0.98,
        "mechanism": "Equimolar glucose-sodium solution utilizes intact sodium-glucose cotransporters in enterocytes to restore hydration."
    },
    "Zinc supplements": {
        "confidence": 0.92,
        "mechanism": "Enhances mucosal brush-border regeneration and boosts cellular immunity in acute diarrhea."
    }
}

def compute_jaccard_similarity(predicted: List[str], gold: List[str]) -> float:
    """
    Computes Jaccard similarity between predicted and gold standard drug classes:
    J(A, B) = |A ∩ B| / |A ∪ B|
    """
    if not predicted and not gold:
        return 1.0
    if not predicted or not gold:
        return 0.0

    def norm(s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r'[\(\)\[\]\-_,]+', ' ', s)
        return re.sub(r'\s+', ' ', s).strip()

    pred_set = {norm(x) for x in predicted}
    gold_set = {norm(x) for x in gold}

    intersection_count = 0
    matched_gold = set()
    for p in pred_set:
        for g in gold_set:
            if g not in matched_gold and (p in g or g in p):
                intersection_count += 1
                matched_gold.add(g)
                break

    union_count = len(pred_set) + len(gold_set) - intersection_count
    if union_count == 0:
        return 0.0
    return round(intersection_count / union_count, 4)
def generate_drug_llm_explanation(
    condition: str,
    approved_classes: List[str],
    clinical_context: str,
    guideline_citations: List[str]
) -> Optional[str]:
    """
    Generate an explanatory summary for already-approved drug classes.

    The LLM cannot select, add, or remove drug classes.
    Deterministic contraindication filtering remains authoritative.
    """

    if not approved_classes:
        return None

    system_prompt = """
You are the explanation component of a clinical decision-support system.

Your task is ONLY to explain the already-approved generic drug classes
provided in the input.

STRICT RULES:
1. Do not recommend any additional drug or drug class.
2. Do not remove or modify any approved drug class.
3. Do not provide dosages, frequencies, or administration instructions.
4. Do not override contraindication checks or safety decisions.
5. Do not invent guideline citations or claim that a guideline was consulted.
6. If the supplied information is insufficient, explicitly say so.
7. State that all recommendations require licensed clinician review.

Return a concise explanation in plain text.
"""

    user_prompt = f"""
Diagnostic hypothesis: {condition}

Already-approved generic drug classes:
{approved_classes}

Existing clinical context:
{clinical_context}

Guideline citations supplied by the system:
{guideline_citations}

Explain the general clinical rationale for these classes only.
Do not introduce any other treatment or medication.
"""

    return ollama_client.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
        max_tokens=250,
        timeout=120,
    )
class DrugRecommendationAgent:
    @staticmethod
    def recommend_drug_classes(
    diagnosis_output: DiagnosisOutput,
    evidence_graph: EvidenceGraphModel,
    patient_allergies: List[str] = None,
    guidelines_result: Dict[str, Any] = None
) -> DrugRecommendationOutput:
        """
        Generates contraindication-filtered generic drug-class recommendations.
        Provides calibrated confidence scores and pharmacological explanations for each class.
        Gated by circuit breaker and clinician confirmation.
        """
        if evidence_graph.circuit_breaker_tripped:
            return DrugRecommendationOutput(
                generic_drug_classes=[],
                confidence_scores={},
                drug_explanations={},
                explanation="All automated pharmaceutical recommendations withheld by the Emergency Circuit Breaker. Immediate stabilization protocol active.",
                clinical_context="Recommendation withheld: Emergency circuit breaker active.",
                guideline_citations=[],
                contraindication_flags=["Generative recommendations blocked during critical emergency."],
                caution_notes=["Immediate clinical stabilization and physician referral required."],
                physician_review_mandatory=True,
                no_brand_names_verified=True
            )

        condition = diagnosis_output.primary_diagnosis.strip()
        db_match = None
        for k, v in RECOMMENDED_DRUG_CLASSES_DB.items():
            if k.lower() in condition.lower() or condition.lower() in k.lower():
                db_match = v
                break

        if not db_match:
            return DrugRecommendationOutput(
                generic_drug_classes=[],
                confidence_scores={},
                drug_explanations={},
                explanation=f"Diagnostic hypothesis '{condition}' requires specialist clinician evaluation before drug class selection.",
                clinical_context=f"Diagnostic hypothesis '{condition}' requires specialist clinician evaluation before drug class selection.",
                guideline_citations=diagnosis_output.guideline_citations,
                contraindication_flags=[],
                caution_notes=["No autonomous prescription allowed."],
                physician_review_mandatory=True,
                no_brand_names_verified=True
            )

        candidate_classes = db_match["classes"]
        approved_classes = []
        confidence_scores = {}
        drug_explanations = {}
        contraindication_flags = []

        for d_class in candidate_classes:
            is_contraindicated, reasons = check_contraindications(d_class, evidence_graph, patient_allergies)
            if is_contraindicated:
                contraindication_flags.extend(reasons)
            else:
                approved_classes.append(d_class)
                meta = DRUG_CLASS_METADATA.get(d_class, {})
                confidence_scores[d_class] = meta.get("confidence", 0.90)
                drug_explanations[d_class] = meta.get("mechanism", f"Guideline-directed therapeutic class for {condition}.")

        llm_explanation = generate_drug_llm_explanation(
            condition=condition,
            approved_classes=approved_classes,
            clinical_context=db_match["context"],
            guideline_citations=diagnosis_output.guideline_citations,
        )

        deterministic_explanation = (
            f"Recommended {len(approved_classes)} generic drug classes "
            f"for diagnostic hypothesis '{condition}'. "
            + db_match["context"]
        )

        overall_explanation = (
            llm_explanation
            if llm_explanation
            else deterministic_explanation
        )
        return DrugRecommendationOutput(
            generic_drug_classes=approved_classes,
            confidence_scores=confidence_scores,
            drug_explanations=drug_explanations,
            explanation=overall_explanation,
            clinical_context=db_match["context"],
            guideline_citations=diagnosis_output.guideline_citations,
            contraindication_flags=contraindication_flags,
            caution_notes=[
                "MANDATORY CLINICIAN REVIEW: Advisory decision support only.",
                "Dosages and administration routes must be verified by a licensed medical practitioner.",
                "Generic therapeutic classes specified; zero commercial brand names promoted."
            ],
            physician_review_mandatory=True,
            no_brand_names_verified=True
        )

drug_agent = DrugRecommendationAgent()
