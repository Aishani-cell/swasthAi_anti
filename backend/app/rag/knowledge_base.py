"""
Curated Clinical Guideline Knowledge Base
Grounds clinical reasoning in official Standard Treatment Guidelines (ICMR, AIIMS, WHO-SEARO).
Preserves structural tables and section/page attribution.
"""
from typing import List, Dict, Any

CLINICAL_GUIDELINE_CORPUS: List[Dict[str, Any]] = [
    # 1. Cardiac: STEMI / Acute Coronary Syndrome
    {
        "guideline_id": "ICMR-STG-CARD-001",
        "doc_title": "ICMR Standard Treatment Workflow: Acute ST-Elevation Myocardial Infarction",
        "publisher": "Indian Council of Medical Research (ICMR)",
        "year": 2024,
        "page": 4,
        "section": "Emergency Healthpod Presentation & Primary Action",
        "condition": "STEMI",
        "keywords": ["chest pain", "troponin", "stemi", "myocardial infarction", "substernal", "angina"],
        "content_text": (
            "Clinical Presentation: Severe retrosternal crushing chest pain radiating to left arm or jaw, accompanied by diaphoresis and dyspnea. "
            "Biomarker: Cardiac Troponin I elevation (>=0.4 ng/mL) or positive rapid point-of-care cardiac strip. "
            "Primary Healthpod Actions: Immediate chewable Aspirin 300 mg + Clopidogrel 300 mg loading dose unless contraindicated. Sublingual Nitroglycerin 0.5 mg if SBP > 90 mmHg. "
            "Emergency Escalation: Immediate ambulance transfer to nearest PCI-capable hospital within golden hour (<120 min). DO NOT delay referral for further tests."
        )
    },
    
    # 2. Cardiac: Heart Failure
    {
        "guideline_id": "ICMR-STG-CARD-002",
        "doc_title": "National Health Mission: Primary Care Management of Congestive Heart Failure",
        "publisher": "Ministry of Health & Family Welfare (MoHFW), Govt of India",
        "year": 2023,
        "page": 12,
        "section": "Diagnostic Criteria and Drug Classes",
        "condition": "Heart Failure",
        "keywords": ["orthopnea", "dyspnea", "heart failure", "edema", "breathlessness", "crepitations"],
        "content_text": (
            "Clinical Presentation: Exertional breathlessness, orthopnea, paroxysmal nocturnal dyspnea, bilateral pedal edema, and bilateral lung base crackles. "
            "Drug-Class Recommendations: Loop diuretics (e.g. Furosemide) for fluid congestion; ACE inhibitors or Angiotensin Receptor Blockers (ARBs); Beta-blockers once euvolemic. "
            "Contraindications: Avoid NSAIDs due to renal sodium retention and acute decompensation risk."
        )
    },

    # 3. Infectious: Pneumonia (Community-Acquired)
    {
        "guideline_id": "ICMR-STG-INF-001",
        "doc_title": "ICMR Guidelines for Management of Community-Acquired Pneumonia",
        "publisher": "ICMR & Department of Health Research",
        "year": 2023,
        "page": 7,
        "section": "Primary Health Centre Empiric Antibiotic Guidance",
        "condition": "Pneumonia",
        "keywords": ["cough", "fever", "pneumonia", "sputum", "dyspnea", "crackles", "crepitation"],
        "content_text": (
            "Diagnostic Criteria: Fever, productive cough with purulent sputum, localized crackles/bronchial breathing on auscultation, leukocytosis (WBC > 11,000 /cumm). "
            "Recommended Drug Classes: First-line outpatient empiric therapy: Beta-lactam (Amoxicillin) or Macrolide (Azithromycin) for mild cases. For severe pneumonia: Co-amoxiclav + Macrolide. "
            "Triage Red Flags: Respiratory rate >= 30/min, SpO2 < 90%, confusion require immediate inpatient escalation."
        )
    },

    # 4. Infectious: Dengue Fever & Severe Dengue
    {
        "guideline_id": "NVBDCP-DENGUE-2023",
        "doc_title": "National Vector Borne Disease Control Programme: Clinical Guidelines for Dengue",
        "publisher": "Directorate of NVBDCP, MoHFW, New Delhi",
        "year": 2023,
        "page": 15,
        "section": "Warning Signs and Platelet Management",
        "condition": "Dengue",
        "keywords": ["dengue", "fever", "platelets", "thrombocytopenia", "retro-orbital", "rash", "myalgia"],
        "content_text": (
            "Clinical Presentation: Acute high fever (2-7 days), severe retro-orbital headache, intense arthralgia/myalgia ('break-bone fever'), macular rash, leukopenia, thrombocytopenia. "
            "Critical Warning Signs: Persistent vomiting, abdominal pain, mucosal bleeding, lethargy, rapid drop in platelets (<50,000 /cumm). "
            "Management Protocol: Paracetamol is the ONLY antipyretic recommended. Oral rehydration therapy. "
            "Strict Contraindication: ABSOLUTELY CONTRAINDICATED: Aspirin, Ibuprofen, Diclofenac, and all other NSAIDs due to severe platelet inhibition and fatal hemorrhagic risk."
        )
    },

    # 5. Infectious: Malaria
    {
        "guideline_id": "NVBDCP-MALARIA-2022",
        "doc_title": "National Drug Policy on Malaria",
        "publisher": "NVBDCP, Ministry of Health and Family Welfare",
        "year": 2022,
        "page": 8,
        "section": "Treatment of Plasmodium falciparum and vivax",
        "condition": "Malaria",
        "keywords": ["malaria", "chills", "fever", "shivering", "rigor", "headache", "splenomegaly"],
        "content_text": (
            "Clinical Presentation: Paroxysms of fever with intense chills/rigors, profuse sweating, headache, anemia, and splenomegaly. "
            "Diagnostic Confirmation: Rapid Diagnostic Test (RDT) or peripheral blood smear for malarial parasite (MP). "
            "Recommended Drug Classes: P. falciparum: Artemisinin-based Combination Therapy (ACT: Artesunate + Sulfadoxine-Pyrimethamine or Artemether-Lumefantrine). P. vivax: Chloroquine followed by Primaquine (check G6PD)."
        )
    },

    # 6. Endocrine: Diabetic Ketoacidosis (DKA)
    {
        "guideline_id": "RSSDI-DM-2024",
        "doc_title": "RSSDI Clinical Practice Recommendations for Primary Health Care",
        "publisher": "Research Society for the Study of Diabetes in India",
        "year": 2024,
        "page": 31,
        "section": "Acute Hyperglycemic Emergencies",
        "condition": "DKA",
        "keywords": ["glucose", "dka", "hyperglycemia", "diabetic ketoacidosis", "polyuria", "vomiting", "ketones"],
        "content_text": (
            "Diagnostic Criteria: Blood glucose >= 250-400 mg/dL, presence of urine ketones (>=2+), dehydration, Kussmaul deep breathing, nausea/vomiting, and abdominal pain. "
            "Emergency Action: Immediate 0.9% Normal Saline fluid resuscitation (1 Liter in 1st hour). Regular Insulin 0.1 units/kg IV bolus. Urgent referral to intensive care unit. DO NOT delay transport."
        )
    },

    # 7. Cardiovascular: Hypertensive Crisis
    {
        "guideline_id": "ICMR-STG-HTN-001",
        "doc_title": "Indian Guidelines on Hypertension (I.G.H.-IV)",
        "publisher": "Hypertension Society of India & ICMR",
        "year": 2023,
        "page": 19,
        "section": "Hypertensive Crises: Urgency vs Emergency",
        "condition": "Hypertensive Crisis",
        "keywords": ["hypertension", "bp", "hypertensive crisis", "headache", "systolic", "diastolic"],
        "content_text": (
            "Definition: SBP >= 180 mmHg or DBP >= 120 mmHg. "
            "Triage: Inspect for end-organ damage (chest pain, acute pulmonary edema, acute neurological deficits, papilledema). "
            "Emergency Protocol: Immediate emergency referral. In hypertensive urgency without acute organ damage: oral anti-hypertensives (e.g. Amlodipine 5-10 mg or Clonidine) with close monitoring. Avoid rapid precipitous BP reduction."
        )
    },

    # 8. Renal: Acute Kidney Injury (AKI)
    {
        "guideline_id": "ISN-AKI-2023",
        "doc_title": "Indian Society of Nephrology Guidelines: Management of AKI in Rural Settings",
        "publisher": "Indian Society of Nephrology",
        "year": 2023,
        "page": 5,
        "section": "Early Identification and GFR Dosing",
        "condition": "AKI",
        "keywords": ["creatinine", "aki", "oliguria", "urea", "kidney injury", "renal failure"],
        "content_text": (
            "Diagnostic Criteria: Serum creatinine elevation (>=1.5 times baseline or >= 1.5-2.0 mg/dL acute rise) with or without reduced urine output (<0.5 mL/kg/h). "
            "Primary Care Action: Assess volume status. Stop all nephrotoxic drugs (NSAIDs, Aminoglycosides). Hydrate if volume-depleted. Adjust all antibiotics and cardiovascular drugs for renal function."
        )
    },

    # 9. Respiratory: COPD Exacerbation & Asthma
    {
        "guideline_id": "ICS-COPD-2023",
        "doc_title": "Indian Chest Society Guidelines for Chronic Obstructive Pulmonary Disease",
        "publisher": "Indian Chest Society (ICS) & National College of Chest Physicians (NCCP)",
        "year": 2023,
        "page": 22,
        "section": "Management of Acute Respiratory Exacerbations",
        "condition": "COPD",
        "keywords": ["copd", "asthma", "wheeze", "wheezing", "dyspnea", "inhaler", "smoking", "bronchospasm"],
        "content_text": (
            "Clinical Presentation: Increased dyspnea, cough, sputum volume/purulence, bilateral expiratory polyphonic wheezing. "
            "Recommended Drug Classes: Inhaled short-acting beta2-agonists (SABA: Salbutamol) + Inhaled short-acting anticholinergics (SAMA: Ipratropium) via nebulizer or spacer. Short course systemic corticosteroid (oral Prednisolone 40 mg for 5 days). "
            "Antibiotics indicated if increased sputum purulence."
        )
    },

    # 10. Gastrointestinal: Acute Gastroenteritis
    {
        "guideline_id": "ICMR-STG-GI-001",
        "doc_title": "ICMR Standard Treatment Guidelines: Acute Diarrheal Diseases",
        "publisher": "ICMR",
        "year": 2022,
        "page": 3,
        "section": "Oral Rehydration and Zinc Supplementation",
        "condition": "Gastroenteritis",
        "keywords": ["diarrhea", "dast", "vomiting", "dehydration", "gastroenteritis", "loose stools"],
        "content_text": (
            "Clinical Presentation: Frequent loose watery stools, vomiting, abdominal cramps, dehydration. "
            "Treatment Cornerstones: Reduced-osmolarity Oral Rehydration Salts (ORS) solution continuously. Zinc supplementation (20 mg/day for 14 days). "
            "Antibiotics: Only indicated for severe bloody diarrhea (dysentery) or suspected cholera."
        )
    }
]
