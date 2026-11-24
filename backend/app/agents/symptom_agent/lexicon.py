"""
Bilingual (English/Hindi/Hinglish) Curated Symptom Lexicon
Comprehensive clinical coverage for all 25 disease categories evaluated in the SwasthAI paper.
"""
from typing import Dict, List, Any

SYMPTOM_LEXICON: List[Dict[str, Any]] = [
    # Cardiac / Circulatory
    {
        "canonical": "chest_pain",
        "category": "cardiac",
        "english": ["chest pain", "pain in chest", "angina", "chest tightness", "chest pressure", "substernal pain", "crushing chest pain", "sharp chest pain", "pleuritic chest pain"],
        "hindi": ["सीने में दर्द", "छाती में दर्द", "सीने में भारीपन", "छाती में जकड़न", "सीने में तेज दर्द"],
        "hinglish": ["seene me dard", "seene mein dard", "chaati me dard", "chest pain", "seene me jalan", "chhati dard", "chaati me jakdan", "seene me tez dard", "seene me tez chubhan"]
    },
    {
        "canonical": "palpitations",
        "category": "cardiac",
        "english": ["palpitations", "rapid heartbeat", "fluttering in chest", "racing pulse", "heart pounding", "tachycardia"],
        "hindi": ["दिल की धड़कन तेज होना", "घबराहट", "धड़कन बढ़ना"],
        "hinglish": ["dil ki dhadkan tez", "ghabrahat", "dhadkan badhna", "heart tez chal raha"]
    },
    {
        "canonical": "orthopnea",
        "category": "cardiac",
        "english": ["orthopnea", "shortness of breath lying flat", "breathlessness when lying down", "nocturnal breathlessness"],
        "hindi": ["लेटने पर सांस फूलना", "सीधे सोने पर सांस में तकलीफ"],
        "hinglish": ["letne par saans phoolna", "soye huye saans lene me takleef"]
    },
    {
        "canonical": "pedal_edema",
        "category": "cardiac",
        "english": ["leg swelling", "bilateral leg swelling", "pedal edema", "ankle swelling", "swollen feet", "calf swelling"],
        "hindi": ["पैरों में सूजन", "पैरों में पानी भरना", "सूजन"],
        "hinglish": ["pairo me sujan", "pair me sujan", "pao me sujan", "legs me swelling"]
    },
    {
        "canonical": "positional_chest_pain",
        "category": "cardiac",
        "english": ["relieved by sitting forward", "improves when bending forward", "worsening on lying flat", "sitting forward", "bending forward"],
        "hindi": ["आगे झुकने पर आराम", "सीधे लेटने पर दर्द बढ़ना"],
        "hinglish": ["aage jhukne par aaram", "letne par dard badhna", "aage jhukna"]
    },
    {
        "canonical": "smoking_history",
        "category": "respiratory",
        "english": ["chronic smoker", "smoker", "smoking", "heavy smoker", "tobacco smoker"],
        "hindi": ["धूम्रपान", "बीड़ी पीना", "सिगरेट पीना"],
        "hinglish": ["smoker", "bidi peena", "bidi", "cigarette", "smoking"]
    },

    # Respiratory
    {
        "canonical": "cough",
        "category": "respiratory",
        "english": ["cough", "coughing", "dry cough", "productive cough", "wet cough", "hacking cough", "morning cough"],
        "hindi": ["खांसी", "सूखी खांसी", "बलगम वाली खांसी", "खोकला", "पुरानी खांसी"],
        "hinglish": ["khansi", "sukhi khansi", "balgam wali khansi", "cough", "dhansna", "purani khansi"]
    },
    {
        "canonical": "sputum",
        "category": "respiratory",
        "english": ["sputum", "phlegm", "purulent sputum", "yellowish sputum", "greenish sputum"],
        "hindi": ["बलगम", "पीला बलगम", "कफ"],
        "hinglish": ["balgam", "peela balgam", "sputum", "cough me balgam"]
    },
    {
        "canonical": "dyspnea",
        "category": "respiratory",
        "english": ["shortness of breath", "dyspnea", "breathlessness", "difficulty breathing", "wheezing", "wheeze", "air hunger", "breathless"],
        "hindi": ["सांस फूलना", "सांस लेने में दिक्कत", "दम घुटना", "सांस में घरघराहट", "सीटी जैसी आवाज", "सांस में तकलीफ", "सांस लेने में परेशानी"],
        "hinglish": ["saans phoolna", "saans lene mein dikkat", "saas lene me dikkat", "saans lene me takleef", "dam ghutna", "saas ki takleef", "breathlessness", "breathless", "seeti jaisi aawaz", "wheezing"]
    },
    {
        "canonical": "hemoptysis",
        "category": "respiratory",
        "english": ["coughing up blood", "hemoptysis", "blood in sputum", "bloody cough"],
        "hindi": ["खांसी में खून", "बलगम में खून आना"],
        "hinglish": ["khansi me khoon", "balgam me khoon", "cough me blood"]
    },

    # Infectious / Systemic
    {
        "canonical": "fever",
        "category": "infectious",
        "english": ["fever", "high temperature", "febrile", "pyrexia", "feeling hot", "high grade fever", "low grade fever"],
        "hindi": ["बुखार", "तेज बुखार", "तापमान बढ़ना", "ताप"],
        "hinglish": ["bukhar", "tez bukhar", "tej bukhar", "fever", "shareer garam", "taap"]
    },
    {
        "canonical": "chills",
        "category": "infectious",
        "english": ["chills", "rigors", "shivering with cold", "intense shivering", "shivering"],
        "hindi": ["कंपकंपी", "ठंड लगना", "जाड़ा लगना"],
        "hinglish": ["kampkampi", "thand lagna", "jada lagna", "shivering"]
    },
    {
        "canonical": "fatigue",
        "category": "general",
        "english": ["fatigue", "tiredness", "exhaustion", "lethargy", "weakness", "body ache", "chronic fatigue", "extreme lethargy"],
        "hindi": ["थकान", "कमजोरी", "बदन दर्द", "सुस्ती", "आलस"],
        "hinglish": ["thakan", "kamjori", "badan dard", "sustee", "kamzori", "weakness", "badan me bheed-bhad"]
    },
    {
        "canonical": "joint_pain_rash",
        "category": "infectious",
        "english": ["joint ache", "rash", "retro-orbital pain", "retro-orbital headache", "bleeding gums", "bleeding"],
        "hindi": ["जोड़ों में दर्द", "चकत्ते", "आंखों के पीछे दर्द", "मसूड़ों से खून"],
        "hinglish": ["aankho ke peeche dard", "retro-orbital", "bleeding gums", "rash", "badan me dard"]
    },

    # Neurological
    {
        "canonical": "headache",
        "category": "neurological",
        "english": ["headache", "head pain", "migraine", "severe headache", "pounding headache", "occipital headache"],
        "hindi": ["सिरदर्द", "सर में दर्द", "आधा सीसी दर्द", "सिर में तेज दर्द"],
        "hinglish": ["sir dard", "sar dard", "headache", "sar me dard", "matha dard", "sir me tez dard", "sir me bahut bhayankar dard"]
    },
    {
        "canonical": "neck_stiffness",
        "category": "neurological",
        "english": ["neck stiffness", "stiff neck", "nuchal rigidity", "photophobia"],
        "hindi": ["गर्दन में जकड़न", "गर्दन अकड़ना", "रोशनी से परेशानी"],
        "hinglish": ["gardan me jakdan", "neck stiffness", "gardan akadna", "photophobia"]
    },
    {
        "canonical": "neurological_deficit",
        "category": "neurological",
        "english": ["facial drooping", "slurred speech", "arm weakness", "sudden weakness", "facial droop"],
        "hindi": ["मुंह टेढ़ा होना", "बोलने में लड़खड़ाहट", "हाथ में कमजोरी"],
        "hinglish": ["muh tedha hona", "bolne me ladkhadahat", "slurred speech", "facial droop", "arm weakness"]
    },
    {
        "canonical": "altered_mental_status",
        "category": "neurological",
        "english": ["confusion", "altered mental status", "disorientation", "drowsiness", "unresponsive", "profound lethargy"],
        "hindi": ["बेहोशी", "भ्रम", "होश खोना", "सुध-बुध खोना"],
        "hinglish": ["behosh", "behosi", "bhram", "confusion", "hosh me na hona", "unresponsive"]
    },

    # Gastrointestinal & Abdominal
    {
        "canonical": "right_lower_quadrant_pain",
        "category": "gastrointestinal",
        "english": ["right lower quadrant abdominal pain", "rlq pain", "pain in right lower abdomen"],
        "hindi": ["पेट में दाहिनी तरफ नीचे दर्द"],
        "hinglish": ["pet me dahini taraf neeche dard", "right lower quadrant"]
    },
    {
        "canonical": "right_upper_quadrant_pain",
        "category": "gastrointestinal",
        "english": ["right upper quadrant abdominal pain", "ruq pain", "pain after fatty meal", "gallbladder pain"],
        "hindi": ["पेट में दाहिनी तरफ ऊपर दर्द"],
        "hinglish": ["pet me dahini taraf upar dard", "right upper quadrant", "pain after fatty meal"]
    },
    {
        "canonical": "epigastric_pain",
        "category": "gastrointestinal",
        "english": ["epigastric pain", "pain radiating to back", "epigastric abdominal pain"],
        "hindi": ["पेट के ऊपरी हिस्से में दर्द", "दर्द जो पीठ की तरफ जाता है"],
        "hinglish": ["epigastric pain", "pet ke oopri hisse me tez dard", "peeth ki taraf jata hai"]
    },
    {
        "canonical": "abdominal_pain",
        "category": "gastrointestinal",
        "english": ["abdominal pain", "stomach ache", "belly pain", "abdominal cramps"],
        "hindi": ["पेट में दर्द", "पेट दर्द", "पेट में मरोड़"],
        "hinglish": ["pet me dard", "pet dard", "pet me marod", "stomach pain", "belly ache"]
    },
    {
        "canonical": "nausea_vomiting",
        "category": "gastrointestinal",
        "english": ["nausea", "vomiting", "feeling sick", "throwing up", "emesis"],
        "hindi": ["उल्टी", "जी मिचलाना", "कै होना"],
        "hinglish": ["ulti", "vomiting", "ji michlana", "ulti jaisa lagna", "kai"]
    },
    {
        "canonical": "diarrhea",
        "category": "gastrointestinal",
        "english": ["diarrhea", "loose stools", "loose motions", "watery loose stools", "watery stool"],
        "hindi": ["दस्त", "पतले दस्त", "पेचिश"],
        "hinglish": ["dast", "patle dast", "loose motion", "loose motions", "pechish", "watery loose stools"]
    },

    # Renal / Genitourinary
    {
        "canonical": "flank_pain",
        "category": "renal",
        "english": ["flank pain", "right flank pain", "left flank pain", "kidney pain"],
        "hindi": ["कमर में एक तरफ दर्द", "कमर में दर्द"],
        "hinglish": ["kamar me ek taraf tez dard", "flank pain", "kamar dard"]
    },
    {
        "canonical": "dysuria",
        "category": "renal",
        "english": ["dysuria", "burning urination", "painful urination", "burning during pee"],
        "hindi": ["पेशाब में जलन", "पेशाब करते समय दर्द", "दर्दनाक पेशाब"],
        "hinglish": ["peshab me jalan", "peshab me dard", "urine me jalan", "burning urination"]
    },
    {
        "canonical": "urinary_frequency",
        "category": "renal",
        "english": ["urinary frequency", "frequent urination", "peeing often", "oliguria", "decreased urine output"],
        "hindi": ["बार-बार पेशाब आना", "पेशाब की अधिकता", "पेशाब कम आना"],
        "hinglish": ["baar baar peshab", "frequent urine", "peshab zyada aana", "peshab kam aana", "decreased urine"]
    },

    # Endocrine & Metabolic
    {
        "canonical": "polyuria_polydipsia",
        "category": "endocrine",
        "english": ["excessive thirst", "excessive hunger", "polydipsia", "polyuria"],
        "hindi": ["बहुत ज्यादा प्यास लगना", "बार-बार प्यास"],
        "hinglish": ["zyada pyaas lagna", "bahut pyaas", "excessive thirst", "zyada pyaas"]
    },
    {
        "canonical": "temperature_intolerance",
        "category": "endocrine",
        "english": ["cold intolerance", "heat intolerance", "unexplained weight gain", "weight loss despite hunger", "tremor"],
        "hindi": ["ठंड बर्दाश्त न होना", "गर्मी बर्दाश्त न होना", "वजन बढ़ना", "हाथ कांपना"],
        "hinglish": ["cold intolerance", "heat intolerance", "wajan badhna", "thand lagna", "hath kapna", "tremor"]
    },
    {
        "canonical": "dizziness",
        "category": "neurological",
        "english": ["dizziness", "dizzy", "lightheadedness", "vertigo", "giddiness", "feeling faint"],
        "hindi": ["चक्कर", "चक्कर आना", "चक्कर आते हैं", "घबराहट"],
        "hinglish": ["chakkar", "chakkar aana", "chakkar aate hain", "dizzy", "head light hona", "best hona"],
    }
]

# Negation lexicon in English, Hindi, and Hinglish
NEGATION_CUES = {
    "en": ["no", "not", "without", "denies", "denied", "negative for", "absent", "no history of", "free of"],
    "hi": ["नहीं", "ना", "बिना", "गैर", "नदारद"],
    "hinglish": ["nahi", "nahin", "naahi", "bina", "koi nahi", "kuch nahi", "mat", "no", "not"]
}
