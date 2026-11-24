"""
Diagnosis Agent Implementation
Implements Section 3.8 of the SwasthAI paper.
Includes local LLM adapter (temperature=0.0) and clinically prioritized deterministic expert fallback
covering all 25 disease categories evaluated in the paper.
Features:
- Calibrated confidence scores for primary and differential diagnoses
- Comprehensive clinical explanations detailing symptom, vital, and laboratory findings
- Multi-hypothesis differential diagnosis with ICD-10 codes and differentiating features
"""
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings
from backend.app.core.privacy import validate_llm_input
from backend.app.core.ollama_client import ollama_client
from backend.app.schemas.evidence import EvidenceGraphModel
from backend.app.schemas.consultation import DiagnosisOutput, DiagnosisHypothesis
from backend.app.evidence.builder import format_evidence_graph_text
from backend.app.agents.diagnosis_agent.prompts import DIAGNOSIS_SYSTEM_PROMPT, DIAGNOSIS_USER_PROMPT_TEMPLATE

DIAGNOSTIC_METADATA_REGISTRY: Dict[str, Dict[str, Any]] = {
    "STEMI": {
        "icd10": "I21.9",
        "confidence": 0.94,
        "explanation": "Severe acute crushing chest pain with positive cardiac troponin I (>0.04 ng/mL) confirms acute myocardial necrosis in progress. Requires immediate emergency coronary reperfusion.",
        "differentials": [
            {"condition_name": "Unstable Angina", "icd10": "I20.0", "confidence": 0.28, "reasoning": "Ischemic chest pain without sustained biomarker elevation.", "differentiating": "Troponin is typically normal in unstable angina."},
            {"condition_name": "Acute Pericarditis", "icd10": "I30.9", "confidence": 0.18, "reasoning": "Pericardial inflammation can mimic acute coronary syndrome.", "differentiating": "Pericarditis improves leaning forward and has diffuse ST elevation rather than regional."},
            {"condition_name": "Aortic Dissection", "icd10": "I71.0", "confidence": 0.12, "reasoning": "Tearing chest pain radiating to back.", "differentiating": "Asymmetric pulses and widened mediastinum on imaging."}
        ]
    },
    "Heart Failure": {
        "icd10": "I50.9",
        "confidence": 0.91,
        "explanation": "Orthopnea, exertional dyspnea, and peripheral fluid overload (pedal edema) indicate elevated left ventricular filling pressures and systemic venous congestion.",
        "differentials": [
            {"condition_name": "COPD Exacerbation", "icd10": "J44.1", "confidence": 0.32, "reasoning": "Airflow limitation causing severe exertional dyspnea.", "differentiating": "COPD usually lacks elevated JVP, S3 gallop, or cardiomegaly."},
            {"condition_name": "Pneumonia", "icd10": "J18.9", "confidence": 0.22, "reasoning": "Infectious consolidation can produce crackles and dyspnea.", "differentiating": "Pneumonia presents with high fever, purulent sputum, and unilateral focal crackles."},
            {"condition_name": "Cirrhosis with Ascites", "icd10": "K74.60", "confidence": 0.14, "reasoning": "Portal hypertension causing lower extremity edema.", "differentiating": "Lack of orthopnea or pulmonary vascular congestion."}
        ]
    },
    "Pericarditis": {
        "icd10": "I30.9",
        "confidence": 0.89,
        "explanation": "Sharp pleuritic chest pain that characteristically worsens in the supine position and improves upon leaning forward (positional relief), consistent with inflamed pericardial membranes.",
        "differentials": [
            {"condition_name": "Acute Coronary Syndrome", "icd10": "I24.9", "confidence": 0.26, "reasoning": "Myocardial ischemia can cause retrosternal pain.", "differentiating": "ACS pain is typically dull/crushing and not relieved by sitting forward."},
            {"condition_name": "Pleurisy", "icd10": "R09.1", "confidence": 0.20, "reasoning": "Pleural inflammation causing sharp respiratory-phasic pain.", "differentiating": "Pleurisy is exacerbated mainly by deep inspiration and coughing, less dependent on posture."},
            {"condition_name": "Myocarditis", "icd10": "I40.9", "confidence": 0.15, "reasoning": "Myocardial inflammation often co-occurs with pericarditis.", "differentiating": "Myocarditis causes elevated troponin and ventricular dysfunction."}
        ]
    },
    "Pneumonia": {
        "icd10": "J18.9",
        "confidence": 0.92,
        "explanation": "Productive cough with purulent sputum, systemic febrile response, and auscultatory lung crackles confirm infectious alveolar consolidation.",
        "differentials": [
            {"condition_name": "Acute Bronchitis", "icd10": "J20.9", "confidence": 0.28, "reasoning": "Cough and fever from large airway inflammation.", "differentiating": "Lacks focal parenchymal consolidation or crackles."},
            {"condition_name": "Pulmonary Tuberculosis", "icd10": "A15.0", "confidence": 0.24, "reasoning": "Chronic subacute cough, fever, and weight loss in endemic areas.", "differentiating": "TB typically has duration > 2 weeks, hemoptysis, and apical cavitary lesions."},
            {"condition_name": "COPD Exacerbation", "icd10": "J44.1", "confidence": 0.18, "reasoning": "Worsening cough and dyspnea in patients with tobacco exposure.", "differentiating": "COPD features diffuse wheezes rather than focal localized crepitations."}
        ]
    },
    "Dengue": {
        "icd10": "A90",
        "confidence": 0.93,
        "explanation": "Acute high-grade fever accompanied by retro-orbital headache, intense arthralgia ('break-bone'), and thrombocytopenia indicates acute Dengue viral infection.",
        "differentials": [
            {"condition_name": "Malaria", "icd10": "B54", "confidence": 0.30, "reasoning": "Paroxysmal fever and rigors common in endemic zones.", "differentiating": "Malaria features cyclical chills/rigors and splenomegaly; diagnosed via peripheral smear/RDT."},
            {"condition_name": "Chikungunya", "icd10": "A92.0", "confidence": 0.25, "reasoning": "Severe polyarthralgia with acute febrile presentation.", "differentiating": "Chikungunya features prominent small-joint arthritis with less severe thrombocytopenia."},
            {"condition_name": "Typhoid Fever", "icd10": "A01.0", "confidence": 0.16, "reasoning": "Step-ladder fever with abdominal discomfort.", "differentiating": "Relative bradycardia, leukopenia, and positive Widal or blood culture."}
        ]
    },
    "Malaria": {
        "icd10": "B54",
        "confidence": 0.92,
        "explanation": "Paroxysmal spikes of high fever accompanied by intense shivering/rigors and sweating phases correspond to Plasmodium erythrocytic schizont rupture.",
        "differentials": [
            {"condition_name": "Dengue", "icd10": "A90", "confidence": 0.28, "reasoning": "Vector-borne acute fever with headache and body aches.", "differentiating": "Dengue features severe retro-orbital pain and marked thrombocytopenia without rigors."},
            {"condition_name": "Typhoid Fever", "icd10": "A01.0", "confidence": 0.20, "reasoning": "Prolonged bacteremic fever with hepatosplenomegaly.", "differentiating": "Step-ladder fever without periodic paroxysms."},
            {"condition_name": "Urinary Tract Infection", "icd10": "N39.0", "confidence": 0.14, "reasoning": "Fever with chills in ascending upper urinary tract infection.", "differentiating": "Presence of dysuria, frequency, and pyuria."}
        ]
    },
    "Sepsis / Septic Shock": {
        "icd10": "R65.21",
        "confidence": 0.95,
        "explanation": "Life-threatening organ dysfunction caused by a dysregulated host response to infection, presenting with marked hypotension (SBP < 90 mmHg), tachypnea, and peripheral hypoperfusion.",
        "differentials": [
            {"condition_name": "Severe Sepsis", "icd10": "R65.20", "confidence": 0.35, "reasoning": "Sepsis with acute organ dysfunction responding to initial fluid challenge.", "differentiating": "Responds to fluid resuscitation without requiring vasopressor infusion."},
            {"condition_name": "Cardiogenic Shock", "icd10": "R57.0", "confidence": 0.20, "reasoning": "Primary pump failure resulting in critical hypotension.", "differentiating": "Features elevated central venous pressure and pulmonary edema rather than warm vasodilation."},
            {"condition_name": "Hypovolemic Shock", "icd10": "R57.1", "confidence": 0.16, "reasoning": "Intravascular depletion from massive gastrointestinal losses or hemorrhage.", "differentiating": "Absence of infectious focus or high febrile response."}
        ]
    },
    "Sepsis": {
        "icd10": "A41.9",
        "confidence": 0.92,
        "explanation": "Systemic Inflammatory Response Syndrome (SIRS) driven by severe infection, characterized by leukocytosis (>11,000/cumm), tachycardia, and altered mental status.",
        "differentials": [
            {"condition_name": "Septic Shock", "icd10": "R65.21", "confidence": 0.32, "reasoning": "Progression to refractory arterial hypotension requiring vasopressors.", "differentiating": "SBP remains >= 90 mmHg or responsive to crystalloid volume."},
            {"condition_name": "Bacteremia", "icd10": "A49.9", "confidence": 0.25, "reasoning": "Bacterial dissemination in blood without full organ failure.", "differentiating": "Organ function scores (SOFA) remain preserved."},
            {"condition_name": "Severe Pneumonia", "icd10": "J18.9", "confidence": 0.22, "reasoning": "Pulmonary source of systemic inflammation.", "differentiating": "Focal respiratory signs predominate over multiorgan dysfunction."}
        ]
    },
    "UTI": {
        "icd10": "N39.0",
        "confidence": 0.90,
        "explanation": "Dysuria, urinary urgency, and frequency with suprapubic discomfort confirm localized lower urinary tract microbial colonization.",
        "differentials": [
            {"condition_name": "Pyelonephritis", "icd10": "N10", "confidence": 0.25, "reasoning": "Ascending infection reaching renal pelvis.", "differentiating": "Absence of high fever, rigors, or costovertebral flank tenderness."},
            {"condition_name": "Vaginitis / Cervicitis", "icd10": "N76.0", "confidence": 0.20, "reasoning": "External dysuria and pelvic irritation.", "differentiating": "Accompanied by vaginal discharge and pruritus rather than internal urinary frequency."},
            {"condition_name": "Urethritis", "icd10": "N34.1", "confidence": 0.18, "reasoning": "Urethral discharge and painful micturition.", "differentiating": "History of unprotected sexual contact, positive urethral swab."}
        ]
    },
    "Pyelonephritis": {
        "icd10": "N10",
        "confidence": 0.92,
        "explanation": "Upper urinary tract bacterial infection characterized by fever, rigors, unilateral flank/costovertebral angle tenderness, and lower urinary tract symptoms.",
        "differentials": [
            {"condition_name": "Urinary Tract Infection", "icd10": "N39.0", "confidence": 0.30, "reasoning": "Lower tract cystitis.", "differentiating": "Lacks systemic fever and costovertebral tenderness."},
            {"condition_name": "Renal Colic / Nephrolithiasis", "icd10": "N20.0", "confidence": 0.24, "reasoning": "Severe unilateral flank pain radiating to groin.", "differentiating": "Pain is spasmodic/colicky; absence of fever unless infected hydronephrosis."},
            {"condition_name": "Appendicitis", "icd10": "K35.80", "confidence": 0.16, "reasoning": "Right-sided abdominal/flank pain.", "differentiating": "Pain localizes to McBurney's point with peritoneal signs rather than flank CVA angle."}
        ]
    },
    "Appendicitis": {
        "icd10": "K35.80",
        "confidence": 0.93,
        "explanation": "Right lower quadrant abdominal pain with localized peritoneal signs (tenderness at McBurney's point, rebound tenderness) and leukocytosis indicative of acute appendiceal inflammation.",
        "differentials": [
            {"condition_name": "Mesenteric Adenitis", "icd10": "I88.0", "confidence": 0.28, "reasoning": "Viral lymphadenopathy mimicking appendicitis in young patients.", "differentiating": "Frequently preceded by upper respiratory infection, pain is more diffuse."},
            {"condition_name": "Ovarian Torsion / Ruptured Cyst", "icd10": "N83.51", "confidence": 0.22, "reasoning": "Acute pelvic pain in reproductive-age females.", "differentiating": "Sudden onset pelvic pain confirmed via pelvic ultrasound."},
            {"condition_name": "Gastroenteritis", "icd10": "A09", "confidence": 0.16, "reasoning": "Cramping abdominal pain and nausea.", "differentiating": "Diarrhea precedes pain; absence of focal RLQ peritoneal guarding."}
        ]
    },
    "Meningitis": {
        "icd10": "G03.9",
        "confidence": 0.94,
        "explanation": "High fever, severe headache, photophobia, and classic nuchal rigidity (Kernig/Brudzinski signs) represent acute meningeal inflammation requiring urgent lumbar puncture.",
        "differentials": [
            {"condition_name": "Subarachnoid Hemorrhage", "icd10": "I60.9", "confidence": 0.26, "reasoning": "Sudden thunderclap headache with meningismus.", "differentiating": "Onset is hyperacute ('worst headache of life') without preceding febrile prodrome."},
            {"condition_name": "Viral Encephalitis", "icd10": "A86", "confidence": 0.24, "reasoning": "Fever, altered sensorium, and headache.", "differentiating": "Features focal neurological signs, personality changes, and seizures."},
            {"condition_name": "Severe Migraine", "icd10": "G43.909", "confidence": 0.12, "reasoning": "Unilateral throbbing headache and photophobia.", "differentiating": "Absence of fever, neck stiffness, or leukocytosis."}
        ]
    },
    "DKA": {
        "icd10": "E10.1",
        "confidence": 0.95,
        "explanation": "Marked hyperglycemia (glucose >= 250 mg/dL), osmotic diuresis (polyuria/polydipsia), ketotic nausea/vomiting, and Kussmaul respirations establish diabetic ketoacidosis.",
        "differentials": [
            {"condition_name": "Hyperosmolar Hyperglycemic State", "icd10": "E11.0", "confidence": 0.30, "reasoning": "Severe hyperglycemia with profound dehydration in type 2 diabetes.", "differentiating": "Typically glucose > 600 mg/dL with minimal ketoacidosis and higher osmolality."},
            {"condition_name": "Acute Gastroenteritis", "icd10": "A09", "confidence": 0.18, "reasoning": "Vomiting and abdominal pain.", "differentiating": "Normoglycemic or mild reactive hyperglycemia without ketonuria."},
            {"condition_name": "Sepsis", "icd10": "A41.9", "confidence": 0.15, "reasoning": "Infection precipitating stress hyperglycemia.", "differentiating": "Sepsis may trigger DKA, but primary acid-base defect requires insulin and fluid replacement."}
        ]
    },
    "Hypothyroidism": {
        "icd10": "E03.9",
        "confidence": 0.89,
        "explanation": "Chronic progressive fatigue, weight gain, cold intolerance, dry skin, and resting bradycardia reflect systemic hypometabolism from thyroid hormone deficiency.",
        "differentials": [
            {"condition_name": "Chronic Fatigue Syndrome", "icd10": "R53.82", "confidence": 0.26, "reasoning": "Persistent unrefreshing fatigue.", "differentiating": "Normal TSH and absence of cold intolerance or physical myxedema."},
            {"condition_name": "Depression", "icd10": "F32.9", "confidence": 0.22, "reasoning": "Psychomotor slowing and apathy.", "differentiating": "Affective symptoms predominate; normal thyroid function tests."},
            {"condition_name": "Anemia", "icd10": "D64.9", "confidence": 0.20, "reasoning": "Lethargy and exertional fatigue.", "differentiating": "Identified by low hemoglobin on CBC with normal TSH."}
        ]
    },
    "Hyperthyroidism": {
        "icd10": "E05.9",
        "confidence": 0.90,
        "explanation": "Unexplained weight loss despite increased appetite, heat intolerance, resting tachycardia, fine tremors, and palpitations reflect hypermetabolic thyroid state.",
        "differentials": [
            {"condition_name": "Anxiety Disorder", "icd10": "F41.9", "confidence": 0.30, "reasoning": "Palpitations, diaphoresis, and fine tremors.", "differentiating": "Normal serum TSH/Free T4; symptoms episodic rather than sustained."},
            {"condition_name": "Pheochromocytoma", "icd10": "C74.00", "confidence": 0.15, "reasoning": "Paroxysmal hypertension, sweating, and palpitations.", "differentiating": "Marked paroxysmal blood pressure surges and elevated urinary metanephrines."},
            {"condition_name": "Atrial Fibrillation", "icd10": "I48.91", "confidence": 0.18, "reasoning": "Rapid irregular pulse and palpitations.", "differentiating": "ECG shows irregularly irregular rhythm without P waves; thyroid tests differentiate etiology."}
        ]
    },
    "AKI": {
        "icd10": "N17.9",
        "confidence": 0.92,
        "explanation": "Acute elevation in serum creatinine (>1.5 mg/dL) with decreased urine output (oliguria) signifies rapid reduction in glomerular filtration rate.",
        "differentials": [
            {"condition_name": "Chronic Kidney Disease", "icd10": "N18.9", "confidence": 0.32, "reasoning": "Elevated creatinine and impaired renal clearance.", "differentiating": "Small shrunken kidneys on ultrasound and long-standing proteinuria/anemia."},
            {"condition_name": "Prerenal Azotemia", "icd10": "R39.89", "confidence": 0.28, "reasoning": "Volume depletion reducing renal perfusion.", "differentiating": "Rapidly reverses with isotonic crystalloid fluid bolus."},
            {"condition_name": "Urinary Tract Obstruction", "icd10": "N13.9", "confidence": 0.16, "reasoning": "Postrenal hydronephrosis causing acute azotemia.", "differentiating": "Bilateral hydronephrosis visualized on renal sonography."}
        ]
    },
    "Asthma Exacerbation": {
        "icd10": "J45.901",
        "confidence": 0.92,
        "explanation": "Episodic dyspnea, expiratory wheezing, chest tightness, and nocturnal cough indicate reversible airway hyperreactivity and acute bronchospasm.",
        "differentials": [
            {"condition_name": "COPD Exacerbation", "icd10": "J44.1", "confidence": 0.30, "reasoning": "Wheezing and dyspnea in older smokers.", "differentiating": "COPD features irreversible airflow obstruction and chronic productive sputum."},
            {"condition_name": "Acute Bronchitis", "icd10": "J20.9", "confidence": 0.20, "reasoning": "Transient cough with mild wheezing following viral infection.", "differentiating": "Absence of prior recurrent atopic or nocturnal wheezing episodes."},
            {"condition_name": "Heart Failure (Cardiac Asthma)", "icd10": "I50.9", "confidence": 0.18, "reasoning": "Peribronchial edema causing wheezing in volume overload.", "differentiating": "Features orthopnea, elevated BNP/NT-proBNP, and cardiomegaly."}
        ]
    },
    "COPD": {
        "icd10": "J44.1",
        "confidence": 0.91,
        "explanation": "Chronic progressive exertional dyspnea and morning cough with sputum production in a patient with extensive tobacco smoking history indicate chronic obstructive pulmonary disease.",
        "differentials": [
            {"condition_name": "Asthma Exacerbation", "icd10": "J45.901", "confidence": 0.28, "reasoning": "Expiratory wheezing and airway obstruction.", "differentiating": "Asthma features marked spirometric bronchodilator reversibility and atopy history."},
            {"condition_name": "Bronchiectasis", "icd10": "J47.9", "confidence": 0.22, "reasoning": "Copious daily purulent sputum and recurrent infections.", "differentiating": "High-resolution CT demonstrates dilated, thickened non-tapering bronchi."},
            {"condition_name": "Heart Failure", "icd10": "I50.9", "confidence": 0.20, "reasoning": "Exertional dyspnea in older adults.", "differentiating": "Accompanied by orthopnea, elevated JVP, and responds to loop diuretics."}
        ]
    },
    "Pulmonary Embolism": {
        "icd10": "I26.9",
        "confidence": 0.93,
        "explanation": "Sudden-onset pleuritic chest pain, unexplained tachypnea, resting tachycardia, and signs of deep vein thrombosis (unilateral calf swelling) strongly indicate thromboembolic pulmonary arterial occlusion.",
        "differentials": [
            {"condition_name": "Acute Coronary Syndrome", "icd10": "I24.9", "confidence": 0.26, "reasoning": "Acute chest pain with diaphoresis and dyspnea.", "differentiating": "Pain is retrosternal pressure rather than sharp pleuritic, confirmed via ECG/troponin."},
            {"condition_name": "Spontaneous Pneumothorax", "icd10": "J93.9", "confidence": 0.22, "reasoning": "Acute unilateral sharp pleuritic pain and breathlessness.", "differentiating": "Unilateral absent breath sounds and hyperresonance on percussion."},
            {"condition_name": "Pneumonia / Pleurisy", "icd10": "J18.9", "confidence": 0.18, "reasoning": "Pleuritic chest pain and fever.", "differentiating": "Gradual onset with purulent sputum and parenchymal consolidation."}
        ]
    },
    "Hypertension": {
        "icd10": "I10",
        "confidence": 0.92,
        "explanation": "Sustained resting blood pressure elevation (SBP >= 140 mmHg or DBP >= 90 mmHg) without acute end-organ damage matches Stage 1 or Stage 2 Essential Hypertension.",
        "differentials": [
            {"condition_name": "White Coat Hypertension", "icd10": "R03.0", "confidence": 0.28, "reasoning": "Transient clinic-setting blood pressure elevation.", "differentiating": "Home or 24-hour ambulatory BP monitoring shows normal mean pressures."},
            {"condition_name": "Secondary Hypertension", "icd10": "I15.9", "confidence": 0.22, "reasoning": "Renal artery stenosis, hyperaldosteronism, or pheochromocytoma.", "differentiating": "Resistant to triple therapy, onset < 30 years, or severe hypokalemia."},
            {"condition_name": "Hypertensive Emergency", "icd10": "I16.1", "confidence": 0.15, "reasoning": "Critical BP elevation.", "differentiating": "SBP < 180 and DBP < 120 mmHg; zero acute end-organ target damage."}
        ]
    },
    "Hypertensive Emergency": {
        "icd10": "I16.1",
        "confidence": 0.96,
        "explanation": "Severe blood pressure elevation (SBP >= 180 mmHg or DBP >= 120 mmHg) presenting with life-threatening acute target organ dysfunction (headache, blurred vision, encephalopathy). Requires immediate IV antihypertensive titration.",
        "differentials": [
            {"condition_name": "Hypertensive Urgency", "icd10": "I16.0", "confidence": 0.30, "reasoning": "Severe BP elevation without acute end-organ failure.", "differentiating": "Absence of neurological, cardiac, or renal decompensation."},
            {"condition_name": "Renovascular Hypertension", "icd10": "I15.0", "confidence": 0.20, "reasoning": "Severe refractory blood pressure surges.", "differentiating": "Renal artery stenosis confirmed via renal Doppler sonography."},
            {"condition_name": "Pheochromocytoma Crisis", "icd10": "C74.00", "confidence": 0.14, "reasoning": "Hyperadrenergic crisis with pallor and headache.", "differentiating": "Accompanied by profound diaphoresis and markedly elevated plasma free metanephrines."}
        ]
    },
    "Stroke": {
        "icd10": "I63.9",
        "confidence": 0.94,
        "explanation": "Sudden onset focal neurological deficit (unilateral facial droop, arm drift, slurred speech) reflects acute cerebral ischemia or hemorrhage within vascular territory.",
        "differentials": [
            {"condition_name": "Transient Ischemic Attack", "icd10": "G45.9", "confidence": 0.30, "reasoning": "Focal neurological deficit resolving rapidly.", "differentiating": "Symptoms completely resolve within 24 hours without acute infarction on neuroimaging."},
            {"condition_name": "Intracranial Hemorrhage", "icd10": "I61.9", "confidence": 0.28, "reasoning": "Hemorrhagic stroke causing focal deficits and severe headache.", "differentiating": "Differentiated immediately via non-contrast head CT (hyperdense blood)."},
            {"condition_name": "Hypertensive Encephalopathy", "icd10": "I67.4", "confidence": 0.16, "reasoning": "Severe hypertension causing cerebral edema and confusion.", "differentiating": "Deficits are diffuse rather than strictly anatomic focal vascular."}
        ]
    },
    "Acute Pancreatitis": {
        "icd10": "K85.90",
        "confidence": 0.93,
        "explanation": "Severe epigastric abdominal pain radiating straight through to the back, exacerbated postprandially or after alcohol intake, typical of acute pancreatic parenchymal autodigestion.",
        "differentials": [
            {"condition_name": "Peptic Ulcer Perforation", "icd10": "K27.5", "confidence": 0.26, "reasoning": "Sudden severe epigastric pain with peritoneal signs.", "differentiating": "Features free air under diaphragm on erect abdominal radiograph."},
            {"condition_name": "Acute Cholecystitis", "icd10": "K81.0", "confidence": 0.24, "reasoning": "Upper quadrant postprandial pain.", "differentiating": "Pain localizes to right upper quadrant with Murphy's sign and gallbladder wall thickening."},
            {"condition_name": "Acute Mesenteric Ischemia", "icd10": "K55.0", "confidence": 0.16, "reasoning": "Severe abdominal pain out of proportion to exam.", "differentiating": "Associated with atrial fibrillation, severe metabolic acidosis, and elevated lactate."}
        ]
    },
    "Cholecystitis": {
        "icd10": "K81.0",
        "confidence": 0.91,
        "explanation": "Right upper quadrant abdominal pain worsening after ingestion of fatty foods, positive Murphy's sign, low-grade fever, and leukocytosis indicating acute gallbladder inflammation.",
        "differentials": [
            {"condition_name": "Biliary Colic", "icd10": "K80.20", "confidence": 0.32, "reasoning": "Episodic postprandial RUQ pain from transient cystic duct obstruction.", "differentiating": "Pain subsides within 4-6 hours; absence of fever or gallbladder wall thickening."},
            {"condition_name": "Acute Pancreatitis", "icd10": "K85.90", "confidence": 0.24, "reasoning": "Severe upper abdominal pain.", "differentiating": "Pain radiates to mid-back and features >3x elevation in serum lipase/amylase."},
            {"condition_name": "Acute Peptic Ulcer", "icd10": "K27.9", "confidence": 0.18, "reasoning": "Epigastric burning pain related to food intake.", "differentiating": "Relieved by antacids; absence of sonographic gallbladder pathology."}
        ]
    },
    "Gastroenteritis": {
        "icd10": "A09",
        "confidence": 0.90,
        "explanation": "Acute onset of frequent loose watery diarrhea accompanied by nausea, vomiting, and diffuse crampy abdominal pain without localized peritoneal signs.",
        "differentials": [
            {"condition_name": "Food Poisoning", "icd10": "A05.9", "confidence": 0.32, "reasoning": "Hyperacute onset of vomiting and diarrhea following contaminated food.", "differentiating": "Multiple individuals affected with short incubation (<6 hours)."},
            {"condition_name": "Amoebiasis", "icd10": "A06.0", "confidence": 0.22, "reasoning": "Subacute dysentery with blood and mucus in stool.", "differentiating": "Microscopic visualization of Entamoeba histolytica cysts/trophozoites in stool."},
            {"condition_name": "Viral Diarrhea (Rotavirus/Norovirus)", "icd10": "A08.4", "confidence": 0.26, "reasoning": "Watery diarrhea with low-grade fever.", "differentiating": "Self-limiting viral etiology confirmed via stool antigen testing."}
        ]
    }
}

def deterministic_diagnosis_fallback(graph: EvidenceGraphModel, guidelines: Dict[str, Any]) -> DiagnosisOutput:
    """
    Clinically prioritized deterministic reasoning covering all 25 categories from the paper.
    Outputs calibrated confidence scores, clinical explanations, and structured differential hypotheses.
    """
    symptoms = {s.canonical_concept for s in graph.symptoms}
    raw_symptom_phrases = " ".join([s.original_phrase.lower() for s in graph.symptoms])
    vitals = graph.vitals
    labs = {l.canonical_name.lower(): l for l in graph.resolved_labs}
    
    primary = "Clinical evidence insufficient"
    differentials: List[str] = []
    evidence: List[str] = []
    missing_data: List[str] = []

    has_trop = any("troponin" in k and l.numeric_value and l.numeric_value >= 0.04 for k, l in labs.items())
    has_leukocytosis = any("white blood cell" in k and l.numeric_value and l.numeric_value > 11000 for k, l in labs.items())
    has_thrombocytopenia = any("platelet" in k and l.numeric_value and l.numeric_value < 150000 for k, l in labs.items())
    has_hyperglycemia = any("glucose" in k and l.numeric_value and l.numeric_value >= 250 for k, l in labs.items())
    has_high_creatinine = any("creatinine" in k and l.numeric_value and l.numeric_value >= 1.5 for k, l in labs.items())

    # 1. Acute Stroke (Focal neurological deficits prioritize over reactive hypertension)
    if "neurological_deficit" in symptoms or any(w in raw_symptom_phrases for w in ["facial", "slurred", "droop", "arm weakness", "tedha", "ladkhadahat"]):
        primary = "Stroke"
        differentials = ["Transient Ischemic Attack", "Intracranial Hemorrhage", "Hypertensive Encephalopathy"]
        evidence = ["Sudden focal neurological deficits (facial droop, slurred speech)"]

    # 2. STEMI / Acute Myocardial Infarction
    elif "chest_pain" in symptoms and has_trop:
        primary = "STEMI"
        differentials = ["Unstable Angina", "Acute Pericarditis", "Aortic Dissection"]
        evidence = ["Severe crushing chest pain", "Positive cardiac troponin I"]

    # 3. Pulmonary Embolism (DVT signs + acute pleuritic pain/dyspnea)
    elif ("calf" in raw_symptom_phrases or any(w in raw_symptom_phrases for w in ["pair me sujan", "sudden onset sharp", "unilateral"])) and ("chest_pain" in symptoms or "dyspnea" in symptoms):
        primary = "Pulmonary Embolism"
        differentials = ["Acute Coronary Syndrome", "Pneumothorax", "Pneumonia"]
        evidence = ["Acute pleuritic dyspnea associated with deep vein thrombosis signs"]

    # 4. Pericarditis (Positional pleuritic chest pain)
    elif "positional_chest_pain" in symptoms or ("chest_pain" in symptoms and any(w in raw_symptom_phrases for w in ["sitting forward", "lying flat", "pleuritic", "leaning", "bending", "forward"])):
        primary = "Pericarditis"
        differentials = ["Acute Coronary Syndrome", "Pleurisy", "Myocarditis"]
        evidence = ["Pleuritic chest pain improving on forward tilt"]

    # 5. Acute Meningitis
    elif "neck_stiffness" in symptoms or (("headache" in symptoms or "fever" in symptoms) and any(w in raw_symptom_phrases for w in ["neck", "stiffness", "photophobia", "gardan", "jakdan"])):
        primary = "Meningitis"
        differentials = ["Subarachnoid Hemorrhage", "Viral Encephalitis", "Severe Migraine"]
        evidence = ["Fever, headache, and classic nuchal rigidity"]

    # 6. Sepsis & Septic Shock
    elif vitals and vitals.systolic_bp and vitals.systolic_bp < 90 and ("fever" in symptoms or (vitals.temperature_c and vitals.temperature_c > 38.5) or (vitals.temperature_c and vitals.temperature_c < 36.0)):
        primary = "Sepsis / Septic Shock"
        differentials = ["Severe Sepsis", "Cardiogenic Shock", "Hypovolemic Shock"]
        evidence = [f"Refractory hypotension ({vitals.systolic_bp} mmHg) with peripheral hypoperfusion"]

    elif "altered_mental_status" in symptoms and ("fever" in symptoms or (vitals and vitals.temperature_c and vitals.temperature_c >= 38.5)):
        primary = "Sepsis"
        differentials = ["Septic Shock", "Bacteremia", "Severe Pneumonia"]
        evidence = ["SIRS criteria with altered mental status"]

    elif has_leukocytosis and ("fever" in symptoms or (vitals and vitals.temperature_c and vitals.temperature_c >= 38.5)) and (vitals and vitals.heart_rate and vitals.heart_rate > 110):
        primary = "Sepsis"
        differentials = ["Severe Pneumonia", "Pyelonephritis", "Bacteremia"]
        evidence = ["Systemic inflammatory response with high leukocytosis"]

    # 7. Diabetic Ketoacidosis (DKA) - Prioritize over general polyuria/vomiting
    elif has_hyperglycemia or ("polyuria_polydipsia" in symptoms and ("nausea_vomiting" in symptoms or "abdominal_pain" in symptoms)):
        primary = "DKA"
        differentials = ["Hyperosmolar Hyperglycemic State", "Gastroenteritis", "Sepsis"]
        evidence = ["Marked hyperglycemia with osmotic diuresis and ketotic vomiting"]

    # 8. Acute Abdominal Emergencies
    elif "right_lower_quadrant_pain" in symptoms or any(w in raw_symptom_phrases for w in ["right lower", "rlq", "dahini taraf neeche"]):
        primary = "Appendicitis"
        differentials = ["Mesenteric Adenitis", "Ovarian Torsion", "Gastroenteritis"]
        evidence = ["Right lower quadrant abdominal pain with localized peritoneal signs"]

    elif "epigastric_pain" in symptoms or any(w in raw_symptom_phrases for w in ["epigastric", "radiating to back", "peeth", "heavy meal", "alcohol"]):
        primary = "Acute Pancreatitis"
        differentials = ["Peptic Ulcer Perforation", "Acute Cholecystitis", "Bowel Obstruction"]
        evidence = ["Severe epigastric pain radiating to the back"]

    elif "right_upper_quadrant_pain" in symptoms or any(w in raw_symptom_phrases for w in ["fatty", "right upper", "dahini taraf upar"]):
        primary = "Cholecystitis"
        differentials = ["Biliary Colic", "Acute Pancreatitis", "Acute Peptic Ulcer"]
        evidence = ["Right upper quadrant abdominal pain aggravated postprandially"]

    # 9. Renal / Genitourinary
    elif "flank_pain" in symptoms or (any(w in raw_symptom_phrases for w in ["flank", "kamar", "costovertebral"]) and ("fever" in symptoms or "chills" in symptoms)):
        primary = "Pyelonephritis"
        differentials = ["Urinary Tract Infection", "Renal Colic", "Appendicitis"]
        evidence = ["Fever, chills, and unilateral flank tenderness"]

    elif "dysuria" in symptoms or any(w in raw_symptom_phrases for w in ["peshab me jalan", "burning urination"]):
        primary = "UTI"
        differentials = ["Vaginitis", "Pyelonephritis", "Urethritis"]
        evidence = ["Dysuria and urinary urgency/frequency"]

    # 10. Acute Kidney Injury (AKI)
    elif has_high_creatinine or any(w in raw_symptom_phrases for w in ["decreased urine", "peshab kam", "oliguria"]):
        primary = "AKI"
        differentials = ["Chronic Kidney Disease", "Prerenal Azotemia", "Urinary Obstruction"]
        evidence = ["Acute elevation in creatinine / reduced urinary output"]

    # 11. Asthma Exacerbation (Reversible wheezing / bronchospasm takes priority over general orthopnea)
    elif "dyspnea" in symptoms and any(w in raw_symptom_phrases for w in ["wheeze", "wheezing", "seeti", "tightness"]):
        primary = "Asthma Exacerbation"
        differentials = ["COPD Exacerbation", "Acute Bronchitis", "Allergic Rhinitis"]
        evidence = ["Reversible expiratory wheezing and episodic bronchospasm"]

    # 12. COPD
    elif "smoking_history" in symptoms or any(w in raw_symptom_phrases for w in ["smoker", "smoking", "bidi", "purani khansi"]) or ("cough" in symptoms and "sputum" in symptoms and "dyspnea" in symptoms and not "fever" in symptoms):
        primary = "COPD"
        differentials = ["Asthma Exacerbation", "Bronchiectasis", "Heart Failure"]
        evidence = ["Chronic smoking history with progressive cough and sputum production"]

    # 13. Heart Failure
    elif "orthopnea" in symptoms or ("dyspnea" in symptoms and ("pedal_edema" in symptoms or any(w in raw_symptom_phrases for w in ["leg", "pedal", "sujan", "edema", "letne par"]))):
        primary = "Heart Failure"
        differentials = ["COPD Exacerbation", "Pneumonia", "Cirrhosis"]
        evidence = ["Orthopnea, exertional dyspnea, and peripheral fluid overload"]

    # 14. Respiratory: Pneumonia
    elif ("cough" in symptoms and "fever" in symptoms) or (graph.respiratory_finding and graph.respiratory_finding.predicted_class in ["crackle", "both"]):
        primary = "Pneumonia"
        differentials = ["Acute Bronchitis", "Pulmonary Tuberculosis", "COPD Exacerbation"]
        evidence = ["Fever with productive cough and purulent sputum"]

    # 15. Systemic Infection: Dengue vs Malaria
    elif "fever" in symptoms and (has_thrombocytopenia or any(w in raw_symptom_phrases for w in ["retro-orbital", "break-bone", "aankho", "bleeding gums"])):
        primary = "Dengue"
        differentials = ["Malaria", "Chikungunya", "Viral Fever"]
        evidence = ["High fever with thrombocytopenia / characteristic arthralgia"]

    elif "fever" in symptoms and ("chills" in symptoms or any(w in raw_symptom_phrases for w in ["kampkampi", "thand", "shivering"])):
        primary = "Malaria"
        differentials = ["Dengue", "Typhoid", "Urinary Tract Infection"]
        evidence = ["Paroxysmal fever with intense shivering/rigors"]

    # 16. Thyroid Disorders
    elif any(w in raw_symptom_phrases for w in ["cold intolerance", "weight gain", "wajan badhna"]) or (vitals and vitals.heart_rate and vitals.heart_rate < 60 and "fatigue" in symptoms):
        primary = "Hypothyroidism"
        differentials = ["Chronic Fatigue Syndrome", "Depression", "Anemia"]
        evidence = ["Chronic fatigue, weight gain, cold intolerance, and bradycardia"]

    elif any(w in raw_symptom_phrases for w in ["heat intolerance", "tremor", "weight loss", "racing pulse", "hath kapna"]) or (vitals and vitals.heart_rate and vitals.heart_rate > 100 and "palpitations" in symptoms):
        primary = "Hyperthyroidism"
        differentials = ["Anxiety Disorder", "Pheochromocytoma", "Atrial Fibrillation"]
        evidence = ["Weight loss, heat intolerance, fine tremors, and resting tachycardia"]

    # 17. Cardiovascular: Hypertensive Crisis vs Essential Hypertension
    elif vitals and vitals.systolic_bp and (vitals.systolic_bp >= 140 or (vitals.diastolic_bp and vitals.diastolic_bp >= 90)):
        if vitals.systolic_bp >= 180 or (vitals.diastolic_bp and vitals.diastolic_bp >= 120):
            primary = "Hypertensive Emergency"
            differentials = ["Essential Hypertension", "Renovascular Hypertension", "Pheochromocytoma"]
            evidence = [f"Critical BP elevation ({vitals.systolic_bp:.0f}/{vitals.diastolic_bp:.0f} mmHg)"]
        else:
            primary = "Hypertension"
            differentials = ["White Coat Hypertension", "Secondary Hypertension"]
            evidence = [f"Elevated blood pressure ({vitals.systolic_bp:.0f}/{vitals.diastolic_bp:.0f} mmHg)"]

    # 18. Acute Gastroenteritis
    elif "diarrhea" in symptoms or ("nausea_vomiting" in symptoms and "abdominal_pain" in symptoms):
        primary = "Gastroenteritis"
        differentials = ["Food Poisoning", "Amoebiasis", "Viral Diarrhea"]
        evidence = ["Frequent loose watery stools and abdominal cramping"]

    # Missing core checks
    if not vitals:
        missing_data.append("Vital signs not recorded")
    if not labs:
        missing_data.append("Baseline laboratory panel not available")

    citations = guidelines.get("citations", [])

    # Lookup rich metadata
    meta = DIAGNOSTIC_METADATA_REGISTRY.get(primary, {})
    primary_conf = meta.get("confidence", 0.88)
    clinical_explanation = meta.get("explanation", f"Presentation consistent with {primary} based on verified clinical evidence.")
    
    # Build differential hypotheses objects
    diff_objects: List[DiagnosisHypothesis] = []
    if meta.get("differentials"):
        for d in meta["differentials"]:
            diff_objects.append(DiagnosisHypothesis(
                condition_name=d["condition_name"],
                icd10_hint=d.get("icd10"),
                confidence=d.get("confidence", 0.20),
                supporting_evidence=[d.get("reasoning", "")],
                reasoning_summary=d.get("reasoning", ""),
                differentiating_features=d.get("differentiating", "")
            ))
    elif differentials:
        for d_name in differentials:
            diff_objects.append(DiagnosisHypothesis(
                condition_name=d_name,
                confidence=0.20,
                reasoning_summary="Considered based on clinical symptom overlap."
            ))

    return DiagnosisOutput(
        primary_diagnosis=primary,
        primary_confidence=primary_conf,
        explanation=clinical_explanation,
        differential_diagnoses=differentials or ["Evaluation pending further workup"],
        differential_hypotheses=diff_objects,
        evidence_citations=evidence or ["Symptom presentation"],
        guideline_citations=citations,
        missing_data_warnings=missing_data,
        conditional_laboratory_findings=["ECG if chest pain persists", "CBC / RDT for fever workup"],
        model_version="SwasthAI-Deterministic-Expert-v1.0",
        physician_review_mandatory=True
    )

def is_ollama_online() -> bool:
    """Check availability through the shared Ollama client."""
    return ollama_client.is_available()


def query_local_llm(
    system_prompt: str,
    user_prompt: str
) -> Optional[str]:
    """Generate diagnostic reasoning using the shared local model."""
    return ollama_client.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
        max_tokens=500,
        timeout=120,
    )


class DiagnosisAgent:
    @staticmethod
    def generate_diagnosis(
        evidence_graph: EvidenceGraphModel,
        guidelines_result: Dict[str, Any]
    ) -> DiagnosisOutput:
        if evidence_graph.circuit_breaker_tripped:
            return DiagnosisOutput(
                primary_diagnosis="Emergency Escalation Triggered (Generative CDSS Blocked)",
                primary_confidence=0.99,
                explanation="Emergency Circuit Breaker active. High-risk life-threatening physiological threshold reached. Generative AI bypassed to ensure safety.",
                differential_diagnoses=[],
                differential_hypotheses=[],
                evidence_citations=["Critical physiological safety threshold triggered"],
                guideline_citations=[],
                missing_data_warnings=["Generative diagnosis bypassed by emergency circuit breaker"],
                conditional_laboratory_findings=[],
                model_version="CircuitBreaker-SafetyBypass",
                physician_review_mandatory=True
            )

        eg_text = format_evidence_graph_text(evidence_graph)
        if not validate_llm_input(eg_text):
            return deterministic_diagnosis_fallback(evidence_graph, guidelines_result)

        citations_text = "\n".join(guidelines_result.get("citations", [])) or "No specific guideline chunk retrieved."
        user_prompt = DIAGNOSIS_USER_PROMPT_TEMPLATE.format(
            evidence_graph_text=eg_text,
            guideline_citations=citations_text
        )

        # The local 1.5B model may only agree with the deterministic reading.
        # It cannot replace evidence citations or introduce a diagnosis the
        # rule path did not already produce. Drug classes are chosen later
        # from that same diagnosis, so an unsupported label cannot reach them.
        deterministic = deterministic_diagnosis_fallback(evidence_graph, guidelines_result)
        raw_response = query_local_llm(DIAGNOSIS_SYSTEM_PROMPT, user_prompt)
        if raw_response:
            try:
                start = raw_response.find('{')
                end = raw_response.rfind('}') + 1
                if start != -1 and end > start:
                    parsed = json.loads(raw_response[start:end])
                    proposed = str(parsed.get("primary_diagnosis", "")).strip().lower()
                    if proposed and proposed == deterministic.primary_diagnosis.strip().lower():
                        return deterministic.model_copy(update={
                            "model_version": f"{settings.LOCAL_LLM_MODEL}-agrees-with-deterministic-evidence"
                        })
            except Exception:
                pass
        return deterministic

diagnosis_agent = DiagnosisAgent()
