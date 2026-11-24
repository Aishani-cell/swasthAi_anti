
SYMPTOM_TEST_CASES = [
    # ==========================================
    # A. POSITIVE SYMPTOM EXTRACTION
    # ==========================================

    {
        "id": "SYM001",
        "text": "Patient has chest pain",
        "expected": {"chest_pain": "positive"}
    },
    {
        "id": "SYM002",
        "text": "Patient is suffering from high fever",
        "expected": {"fever": "positive"}
    },
    {
        "id": "SYM003",
        "text": "Patient complains of severe headache",
        "expected": {"headache": "positive"}
    },
    {
        "id": "SYM004",
        "text": "Patient has a dry cough",
        "expected": {"cough": "positive"}
    },
    {
        "id": "SYM005",
        "text": "Patient reports difficulty in breathing",
        "expected": {"breathlessness": "positive"}
    },
    {
        "id": "SYM006",
        "text": "Patient is experiencing nausea",
        "expected": {"nausea": "positive"}
    },
    {
        "id": "SYM007",
        "text": "Patient has been vomiting since morning",
        "expected": {"vomiting": "positive"}
    },
    {
        "id": "SYM008",
        "text": "Patient reports loose motions",
        "expected": {"diarrhea": "positive"}
    },
    {
        "id": "SYM009",
        "text": "Patient complains of abdominal pain",
        "expected": {"abdominal_pain": "positive"}
    },
    {
        "id": "SYM010",
        "text": "Patient feels extremely weak and tired",
        "expected": {"weakness": "positive", "fatigue": "positive"}
    },

    # ==========================================
    # B. NEGATION DETECTION
    # ==========================================

    {
        "id": "SYM011",
        "text": "Patient denies chest pain",
        "expected": {"chest_pain": "negated"}
    },
    {
        "id": "SYM012",
        "text": "Patient has no fever",
        "expected": {"fever": "negated"}
    },
    {
        "id": "SYM013",
        "text": "Patient does not have a headache",
        "expected": {"headache": "negated"}
    },
    {
        "id": "SYM014",
        "text": "Patient denies any cough",
        "expected": {"cough": "negated"}
    },
    {
        "id": "SYM015",
        "text": "Patient is not experiencing breathlessness",
        "expected": {"breathlessness": "negated"}
    },
    {
        "id": "SYM016",
        "text": "Patient reports no nausea or vomiting",
        "expected": {
            "nausea": "negated",
            "vomiting": "negated"
        }
    },
    {
        "id": "SYM017",
        "text": "Patient denies abdominal pain",
        "expected": {"abdominal_pain": "negated"}
    },
    {
        "id": "SYM018",
        "text": "Patient has no history of dizziness",
        "expected": {"dizziness": "negated"}
    },
    {
        "id": "SYM019",
        "text": "Patient denies having diarrhea",
        "expected": {"diarrhea": "negated"}
    },
    {
        "id": "SYM020",
        "text": "Patient reports absence of joint pain",
        "expected": {"joint_pain": "negated"}
    },

    # ==========================================
    # C. MULTIPLE SYMPTOMS IN ONE SENTENCE
    # ==========================================

    {
        "id": "SYM021",
        "text": "Patient has fever, headache and body pain",
        "expected": {
            "fever": "positive",
            "headache": "positive",
            "body_pain": "positive"
        }
    },
    {
        "id": "SYM022",
        "text": "Patient complains of cough, cold and sore throat",
        "expected": {
            "cough": "positive",
            "common_cold": "positive",
            "sore_throat": "positive"
        }
    },
    {
        "id": "SYM023",
        "text": "Patient has nausea, vomiting and abdominal pain",
        "expected": {
            "nausea": "positive",
            "vomiting": "positive",
            "abdominal_pain": "positive"
        }
    },
    {
        "id": "SYM024",
        "text": "Patient reports fever and difficulty breathing",
        "expected": {
            "fever": "positive",
            "breathlessness": "positive"
        }
    },
    {
        "id": "SYM025",
        "text": "Patient has fatigue, dizziness and weakness",
        "expected": {
            "fatigue": "positive",
            "dizziness": "positive",
            "weakness": "positive"
        }
    },
    {
        "id": "SYM026",
        "text": "Patient has chest pain but no cough",
        "expected": {
            "chest_pain": "positive",
            "cough": "negated"
        }
    },
    {
        "id": "SYM027",
        "text": "Patient has headache and fever but denies vomiting",
        "expected": {
            "headache": "positive",
            "fever": "positive",
            "vomiting": "negated"
        }
    },
    {
        "id": "SYM028",
        "text": "Patient reports joint pain, muscle pain and back pain",
        "expected": {
            "joint_pain": "positive",
            "muscle_pain": "positive",
            "back_pain": "positive"
        }
    },
    {
        "id": "SYM029",
        "text": "Patient has diarrhea but no fever or vomiting",
        "expected": {
            "diarrhea": "positive",
            "fever": "negated",
            "vomiting": "negated"
        }
    },
    {
        "id": "SYM030",
        "text": "Patient complains of palpitations and chest discomfort",
        "expected": {
            "palpitations": "positive",
            "chest_pain": "positive"
        }
    },

    # ==========================================
    # D. HISTORICAL SYMPTOMS
    # ==========================================

    {
        "id": "SYM031",
        "text": "Patient had chest pain last week",
        "expected": {"chest_pain": "historical"}
    },
    {
        "id": "SYM032",
        "text": "Patient experienced fever two days ago",
        "expected": {"fever": "historical"}
    },
    {
        "id": "SYM033",
        "text": "Patient had a cough last month",
        "expected": {"cough": "historical"}
    },
    {
        "id": "SYM034",
        "text": "Patient previously suffered from severe headaches",
        "expected": {"headache": "historical"}
    },
    {
        "id": "SYM035",
        "text": "Patient had diarrhea yesterday, which has now resolved",
        "expected": {"diarrhea": "historical"}
    },
    {
        "id": "SYM036",
        "text": "Patient experienced vomiting three days ago",
        "expected": {"vomiting": "historical"}
    },
    {
        "id": "SYM037",
        "text": "Patient had breathlessness during the previous illness",
        "expected": {"breathlessness": "historical"}
    },
    {
        "id": "SYM038",
        "text": "Patient reports a previous episode of dizziness",
        "expected": {"dizziness": "historical"}
    },

    # ==========================================
    # E. UNCERTAIN SYMPTOMS
    # ==========================================

    {
        "id": "SYM039",
        "text": "Patient may be experiencing chest pain",
        "expected": {"chest_pain": "uncertain"}
    },
    {
        "id": "SYM040",
        "text": "Possible fever reported by the patient",
        "expected": {"fever": "uncertain"}
    },
    {
        "id": "SYM041",
        "text": "Patient possibly has a headache",
        "expected": {"headache": "uncertain"}
    },
    {
        "id": "SYM042",
        "text": "Patient reports suspected breathlessness",
        "expected": {"breathlessness": "uncertain"}
    },
    {
        "id": "SYM043",
        "text": "Patient is unsure whether nausea is present",
        "expected": {"nausea": "uncertain"}
    },
    {
        "id": "SYM044",
        "text": "Patient might be experiencing abdominal pain",
        "expected": {"abdominal_pain": "uncertain"}
    },

    # ==========================================
    # F. COMMON CLINICAL EXPRESSIONS
    # ==========================================

    {
        "id": "SYM045",
        "text": "Patient complains of dyspnea",
        "expected": {"breathlessness": "positive"}
    },
    {
        "id": "SYM046",
        "text": "Patient reports cephalalgia",
        "expected": {"headache": "positive"}
    },
    {
        "id": "SYM047",
        "text": "Patient complains of pyrexia",
        "expected": {"fever": "positive"}
    },
    {
        "id": "SYM048",
        "text": "Patient reports emesis",
        "expected": {"vomiting": "positive"}
    },
    {
        "id": "SYM049",
        "text": "Patient is experiencing arthralgia",
        "expected": {"joint_pain": "positive"}
    },
    {
        "id": "SYM050",
        "text": "Patient reports myalgia",
        "expected": {"muscle_pain": "positive"}
    },

    # ==========================================
    # G. ROBUSTNESS AND COMPLEX NEGATION
    # ==========================================

    {
        "id": "SYM051",
        "text": "No complaints of fever, cough or headache",
        "expected": {
            "fever": "negated",
            "cough": "negated",
            "headache": "negated"
        }
    },
    {
        "id": "SYM052",
        "text": "Although the patient has fever, there is no cough",
        "expected": {
            "fever": "positive",
            "cough": "negated"
        }
    },
    {
        "id": "SYM053",
        "text": "Patient denies fever but reports chills",
        "expected": {
            "fever": "negated",
            "chills": "positive"
        }
    },
    {
        "id": "SYM054",
        "text": "Patient reports persistent pain in the lower back",
        "expected": {"back_pain": "positive"}
    },
    {
        "id": "SYM055",
        "text": "Patient complains of a burning sensation while urinating",
        "expected": {"burning_micturition": "positive"}
    },
    {
        "id": "SYM056",
        "text": "Patient reports excessive sweating during the night",
        "expected": {"sweating": "positive"}
    },
    {
        "id": "SYM057",
        "text": "Patient has swelling in both legs",
        "expected": {"swelling": "positive"}
    },
    {
        "id": "SYM058",
        "text": "Patient reports loss of appetite",
        "expected": {"loss_of_appetite": "positive"}
    },
    {
        "id": "SYM059",
        "text": "Patient complains of blurred vision",
        "expected": {"blurred_and_distorted_vision": "positive"}
    },
    {
        "id": "SYM060",
        "text": "Patient reports chills, fever and severe body aches",
        "expected": {
            "chills": "positive",
            "fever": "positive",
            "body_pain": "positive"
        }
    },

    # ==========================================
    # H. HINDI (ROMANIZED) - POSITIVE EXTRACTION
    # HIN_SYM061–070
    # ==========================================

    
    # ==========================================
    # H. HINDI (ROMANIZED) - POSITIVE EXTRACTION
    # HIN_SYM061–070
    # ==========================================

    {
        "id": "HIN_SYM061",
        "text": "Mujhe seene mein bahut dard ho raha hai.",
        "expected": {"chest_pain": "positive"}
    },
    {
        "id": "HIN_SYM062",
        "text": "Kal raat se mujhe bukhar aa raha hai.",
        "expected": {"fever": "positive"}
    },
    {
        "id": "HIN_SYM063",
        "text": "Mera sir subah se bahut dukh raha hai.",
        "expected": {"headache": "positive"}
    },
    {
        "id": "HIN_SYM064",
        "text": "Mujhe lagataar khaansi ho rahi hai.",
        "expected": {"cough": "positive"}
    },
    {
        "id": "HIN_SYM065",
        "text": "Thoda chalne par meri saans phool jaati hai.",
        "expected": {"breathlessness": "positive"}
    },
    {
        "id": "HIN_SYM066",
        "text": "Mera jee baar baar michla raha hai.",
        "expected": {"nausea": "positive"}
    },
    {
        "id": "HIN_SYM067",
        "text": "Subah se mujhe kai baar ulti ho chuki hai.",
        "expected": {"vomiting": "positive"}
    },
    {
        "id": "HIN_SYM068",
        "text": "Mujhe din bhar patle dast lag rahe hain.",
        "expected": {"diarrhea": "positive"}
    },
    {
        "id": "HIN_SYM069",
        "text": "Mere pet ke daaye taraf dard ho raha hai.",
        "expected": {"abdominal_pain": "positive"}
    },
    {
        "id": "HIN_SYM070",
        "text": "Mujhe bahut thakaan rehti hai aur shareer mein kamzori hai.",
        "expected": {
            "weakness": "positive",
            "fatigue": "positive"
        }
    },

    # ==========================================
    # I. HINDI (ROMANIZED) - NEGATION DETECTION
    # HIN_SYM071–080
    # ==========================================

    {
        "id": "HIN_SYM071",
        "text": "Mujhe seene mein koi dard nahi hai.",
        "expected": {"chest_pain": "negated"}
    },
    {
        "id": "HIN_SYM072",
        "text": "Mujhe bilkul bhi bukhar nahi hai.",
        "expected": {"fever": "negated"}
    },
    {
        "id": "HIN_SYM073",
        "text": "Mera sir nahi dukh raha hai.",
        "expected": {"headache": "negated"}
    },
    {
        "id": "HIN_SYM074",
        "text": "Mujhe khaansi ki koi dikkat nahi hai.",
        "expected": {"cough": "negated"}
    },
    {
        "id": "HIN_SYM075",
        "text": "Mujhe saans lene mein koi pareshani nahi hoti.",
        "expected": {"breathlessness": "negated"}
    },
    {
        "id": "HIN_SYM076",
        "text": "Na jee michla raha hai aur na hi ulti aa rahi hai.",
        "expected": {
            "nausea": "negated",
            "vomiting": "negated"
        }
    },
    {
        "id": "HIN_SYM077",
        "text": "Mere pet mein dard nahi hai.",
        "expected": {"abdominal_pain": "negated"}
    },
    {
        "id": "HIN_SYM078",
        "text": "Mujhe chakkar aane ki koi shikayat nahi hai.",
        "expected": {"dizziness": "negated"}
    },
    {
        "id": "HIN_SYM079",
        "text": "Ab mujhe dast nahi ho rahe hain.",
        "expected": {"diarrhea": "negated"}
    },
    {
        "id": "HIN_SYM080",
        "text": "Mere jodon mein bilkul dard nahi hota.",
        "expected": {"joint_pain": "negated"}
    },

    # ==========================================
    # J. HINDI (ROMANIZED) - MULTIPLE SYMPTOMS
    # HIN_SYM081–090
    # ==========================================

    {
        "id": "HIN_SYM081",
        "text": "Mujhe bukhar, sir dard aur badan mein dard hai.",
        "expected": {
            "fever": "positive",
            "headache": "positive",
            "body_pain": "positive"
        }
    },
    {
        "id": "HIN_SYM082",
        "text": "Mujhe khaansi, zukhaam aur gale mein dard hai.",
        "expected": {
            "cough": "positive",
            "common_cold": "positive",
            "sore_throat": "positive"
        }
    },
    {
        "id": "HIN_SYM083",
        "text": "Mera jee michla raha hai, ulti aa rahi hai aur pet mein dard hai.",
        "expected": {
            "nausea": "positive",
            "vomiting": "positive",
            "abdominal_pain": "positive"
        }
    },
    {
        "id": "HIN_SYM084",
        "text": "Mujhe bukhar hai aur saans lene mein bhi dikkat ho rahi hai.",
        "expected": {
            "fever": "positive",
            "breathlessness": "positive"
        }
    },
    {
        "id": "HIN_SYM085",
        "text": "Mujhe thakaan, chakkar aur bahut kamzori mehsoos hoti hai.",
        "expected": {
            "fatigue": "positive",
            "dizziness": "positive",
            "weakness": "positive"
        }
    },
    {
        "id": "HIN_SYM086",
        "text": "Seene mein dard hai lekin khaansi bilkul nahi hai.",
        "expected": {
            "chest_pain": "positive",
            "cough": "negated"
        }
    },
    {
        "id": "HIN_SYM087",
        "text": "Mujhe sir dard aur bukhar hai lekin ulti nahi ho rahi.",
        "expected": {
            "headache": "positive",
            "fever": "positive",
            "vomiting": "negated"
        }
    },
    {
        "id": "HIN_SYM088",
        "text": "Mere jodon, maanspeshiyon aur kamar mein dard hai.",
        "expected": {
            "joint_pain": "positive",
            "muscle_pain": "positive",
            "back_pain": "positive"
        }
    },
    {
        "id": "HIN_SYM089",
        "text": "Dast ho rahe hain lekin bukhar aur ulti nahi hai.",
        "expected": {
            "diarrhea": "positive",
            "fever": "negated",
            "vomiting": "negated"
        }
    },
    {
        "id": "HIN_SYM090",
        "text": "Mera dil bahut tez dhadak raha hai aur seene mein takleef hai.",
        "expected": {
            "palpitations": "positive",
            "chest_pain": "positive"
        }
    },

    # ==========================================
    # K. HINDI (ROMANIZED) - HISTORICAL SYMPTOMS
    # HIN_SYM091–098
    # ==========================================

    {
        "id": "HIN_SYM091",
        "text": "Pichhle hafte mere seene mein dard hua tha.",
        "expected": {"chest_pain": "historical"}
    },
    {
        "id": "HIN_SYM092",
        "text": "Do din pehle mujhe bahut tez bukhar tha.",
        "expected": {"fever": "historical"}
    },
    {
        "id": "HIN_SYM093",
        "text": "Pichhle mahine mujhe khaansi hui thi.",
        "expected": {"cough": "historical"}
    },
    {
        "id": "HIN_SYM094",
        "text": "Pehle mujhe bahut tez sir dard hota tha.",
        "expected": {"headache": "historical"}
    },
    {
        "id": "HIN_SYM095",
        "text": "Kal dast hue the lekin ab theek ho gaye hain.",
        "expected": {"diarrhea": "historical"}
    },
    {
        "id": "HIN_SYM096",
        "text": "Teen din pehle mujhe ulti hui thi.",
        "expected": {"vomiting": "historical"}
    },
    {
        "id": "HIN_SYM097",
        "text": "Pichhli baar beemar hone par mujhe saans lene mein dikkat hui thi.",
        "expected": {"breathlessness": "historical"}
    },
    {
        "id": "HIN_SYM098",
        "text": "Kuch mahine pehle mujhe chakkar aane ki dikkat hui thi.",
        "expected": {"dizziness": "historical"}
    },

    # ==========================================
    # L. HINDI (ROMANIZED) - UNCERTAIN SYMPTOMS
    # HIN_SYM099–104
    # ==========================================

    {
        "id": "HIN_SYM099",
        "text": "Shayad mere seene mein dard ho raha hai.",
        "expected": {"chest_pain": "uncertain"}
    },
    {
        "id": "HIN_SYM100",
        "text": "Lagta hai mujhe bukhar ho sakta hai.",
        "expected": {"fever": "uncertain"}
    },
    {
        "id": "HIN_SYM101",
        "text": "Ho sakta hai mera sir dukh raha ho.",
        "expected": {"headache": "uncertain"}
    },
    {
        "id": "HIN_SYM102",
        "text": "Mujhe lag raha hai ki saans lene mein dikkat ho sakti hai.",
        "expected": {"breathlessness": "uncertain"}
    },
    {
        "id": "HIN_SYM103",
        "text": "Pata nahi mujhe matli ho rahi hai ya nahi.",
        "expected": {"nausea": "uncertain"}
    },
    {
        "id": "HIN_SYM104",
        "text": "Shayad mere pet mein dard ho raha hai.",
        "expected": {"abdominal_pain": "uncertain"}
    },

    # ==========================================
    # M. HINDI (ROMANIZED) - CLINICAL EXPRESSIONS
    # HIN_SYM105–110
    # ==========================================

    {
        "id": "HIN_SYM105",
        "text": "Mujhe saans chadh rahi hai.",
        "expected": {"breathlessness": "positive"}
    },
    {
        "id": "HIN_SYM106",
        "text": "Mere maathe aur sir mein tez peeda ho rahi hai.",
        "expected": {"headache": "positive"}
    },
    {
        "id": "HIN_SYM107",
        "text": "Mera shareer tap raha hai aur mujhe bukhar hai.",
        "expected": {"fever": "positive"}
    },
    {
        "id": "HIN_SYM108",
        "text": "Mujhe baar baar vaman ho raha hai.",
        "expected": {"vomiting": "positive"}
    },
    {
        "id": "HIN_SYM109",
        "text": "Mere ghutnon aur doosre jodon mein dard hai.",
        "expected": {"joint_pain": "positive"}
    },
    {
        "id": "HIN_SYM110",
        "text": "Meri maanspeshiyon mein bahut dard ho raha hai.",
        "expected": {"muscle_pain": "positive"}
    },

    # ==========================================
    # N. HINDI (ROMANIZED) - ROBUSTNESS AND
    # COMPLEX NEGATION
    # HIN_SYM111–120
    # ==========================================

    {
        "id": "HIN_SYM111",
        "text": "Mujhe na bukhar hai, na khaansi aur na hi sir dard.",
        "expected": {
            "fever": "negated",
            "cough": "negated",
            "headache": "negated"
        }
    },
    {
        "id": "HIN_SYM112",
        "text": "Bukhar toh hai lekin khaansi bilkul nahi hai.",
        "expected": {
            "fever": "positive",
            "cough": "negated"
        }
    },
    {
        "id": "HIN_SYM113",
        "text": "Mujhe bukhar nahi hai par thand lag rahi hai aur kapkapi ho rahi hai.",
        "expected": {
            "fever": "negated",
            "chills": "positive"
        }
    },
    {
        "id": "HIN_SYM114",
        "text": "Meri kamar ke neeche wale hisse mein lagataar dard hai.",
        "expected": {"back_pain": "positive"}
    },
    {
        "id": "HIN_SYM115",
        "text": "Peshaab karte waqt jalan aur dard hota hai.",
        "expected": {"burning_micturition": "positive"}
    },
    {
        "id": "HIN_SYM116",
        "text": "Raat ko sote waqt bahut paseena aata hai.",
        "expected": {"sweating": "positive"}
    },
    {
        "id": "HIN_SYM117",
        "text": "Mere dono pairon mein soojan aa gayi hai.",
        "expected": {"swelling": "positive"}
    },
    {
        "id": "HIN_SYM118",
        "text": "Mujhe bhookh bilkul nahi lag rahi hai.",
        "expected": {"loss_of_appetite": "positive"}
    },
    {
        "id": "HIN_SYM119",
        "text": "Mujhe cheezein dhundhli dikhai de rahi hain.",
        "expected": {"blurred_and_distorted_vision": "positive"}
    },
    {
        "id": "HIN_SYM120",
        "text": "Mujhe thand lag rahi hai, bukhar hai aur poore badan mein dard hai.",
        "expected": {
            "chills": "positive",
            "fever": "positive",
            "body_pain": "positive"
        }
    },
    
    # ==========================================
    # HINGLISH NLP TEST DATASET
    # HING_SYM001–HING_SYM060
    # ==========================================

    # ==========================================
    # A. POSITIVE SYMPTOM EXTRACTION (10)
    # HING_SYM001–010
    # ==========================================

    {
        "id": "HING_SYM001",
        "text": "Mujhe kal raat se high fever aa raha hai.",
        "expected": {"fever": "positive"}
    },
    {
        "id": "HING_SYM002",
        "text": "Mere chest mein bahut severe pain ho raha hai.",
        "expected": {"chest_pain": "positive"}
    },
    {
        "id": "HING_SYM003",
        "text": "Subah se continuous headache ho raha hai.",
        "expected": {"headache": "positive"}
    },
    {
        "id": "HING_SYM004",
        "text": "Mujhe dry cough ke saath throat irritation bhi hai.",
        "expected": {
            "cough": "positive",
            "sore_throat": "positive"
        }
    },
    {
        "id": "HING_SYM005",
        "text": "Thoda walk karne par bhi breathing difficult ho jaati hai.",
        "expected": {"breathlessness": "positive"}
    },
    {
        "id": "HING_SYM006",
        "text": "Khana khane ke baad mujhe nausea feel hota hai.",
        "expected": {"nausea": "positive"}
    },
    {
        "id": "HING_SYM007",
        "text": "Morning se three times vomiting ho chuki hai.",
        "expected": {"vomiting": "positive"}
    },
    {
        "id": "HING_SYM008",
        "text": "Mujhe stomach upset hai aur loose motions ho rahe hain.",
        "expected": {"diarrhea": "positive"}
    },
    {
        "id": "HING_SYM009",
        "text": "Mere lower abdomen mein sharp pain ho raha hai.",
        "expected": {"abdominal_pain": "positive"}
    },
    {
        "id": "HING_SYM010",
        "text": "I feel bahut tired aur body mein weakness bhi hai.",
        "expected": {
            "fatigue": "positive",
            "weakness": "positive"
        }
    },

    # ==========================================
    # B. NEGATION DETECTION (10)
    # HING_SYM011–020
    # ==========================================

    {
        "id": "HING_SYM011",
        "text": "Mujhe chest pain bilkul nahi ho raha hai.",
        "expected": {"chest_pain": "negated"}
    },
    {
        "id": "HING_SYM012",
        "text": "I don't have fever abhi.",
        "expected": {"fever": "negated"}
    },
    {
        "id": "HING_SYM013",
        "text": "Mera headache ab nahi ho raha.",
        "expected": {"headache": "negated"}
    },
    {
        "id": "HING_SYM014",
        "text": "Mujhe cough ki koi problem nahi hai.",
        "expected": {"cough": "negated"}
    },
    {
        "id": "HING_SYM015",
        "text": "Patient ko breathing mein difficulty nahi hoti.",
        "expected": {"breathlessness": "negated"}
    },
    {
        "id": "HING_SYM016",
        "text": "No nausea aur no vomiting, dono symptoms absent hain.",
        "expected": {
            "nausea": "negated",
            "vomiting": "negated"
        }
    },
    {
        "id": "HING_SYM017",
        "text": "Mere stomach mein currently koi pain nahi hai.",
        "expected": {"abdominal_pain": "negated"}
    },
    {
        "id": "HING_SYM018",
        "text": "Mujhe dizziness feel nahi hoti.",
        "expected": {"dizziness": "negated"}
    },
    {
        "id": "HING_SYM019",
        "text": "Loose motions ab bilkul nahi ho rahe.",
        "expected": {"diarrhea": "negated"}
    },
    {
        "id": "HING_SYM020",
        "text": "My joints mein koi pain nahi hai.",
        "expected": {"joint_pain": "negated"}
    },

    # ==========================================
    # C. MULTIPLE SYMPTOMS (10)
    # HING_SYM021–030
    # ==========================================

    {
        "id": "HING_SYM021",
        "text": "Mujhe fever, headache aur severe body pain hai.",
        "expected": {
            "fever": "positive",
            "headache": "positive",
            "body_pain": "positive"
        }
    },
    {
        "id": "HING_SYM022",
        "text": "I have cough, cold aur throat pain since yesterday.",
        "expected": {
            "cough": "positive",
            "common_cold": "positive",
            "sore_throat": "positive"
        }
    },
    {
        "id": "HING_SYM023",
        "text": "Mujhe nausea ho raha hai, vomiting bhi hai aur stomach pain bhi.",
        "expected": {
            "nausea": "positive",
            "vomiting": "positive",
            "abdominal_pain": "positive"
        }
    },
    {
        "id": "HING_SYM024",
        "text": "Patient ko high fever hai aur breathing mein bhi problem aa rahi hai.",
        "expected": {
            "fever": "positive",
            "breathlessness": "positive"
        }
    },
    {
        "id": "HING_SYM025",
        "text": "Mujhe dizziness, fatigue aur body weakness feel ho rahi hai.",
        "expected": {
            "dizziness": "positive",
            "fatigue": "positive",
            "weakness": "positive"
        }
    },
    {
        "id": "HING_SYM026",
        "text": "Chest mein pain hai but cough bilkul nahi hai.",
        "expected": {
            "chest_pain": "positive",
            "cough": "negated"
        }
    },
    {
        "id": "HING_SYM027",
        "text": "Headache aur fever dono hain, but vomiting nahi ho rahi.",
        "expected": {
            "headache": "positive",
            "fever": "positive",
            "vomiting": "negated"
        }
    },
    {
        "id": "HING_SYM028",
        "text": "Mere knees, muscles aur lower back mein pain hai.",
        "expected": {
            "joint_pain": "positive",
            "muscle_pain": "positive",
            "back_pain": "positive"
        }
    },
    {
        "id": "HING_SYM029",
        "text": "Loose motions ho rahe hain, lekin fever aur vomiting nahi hai.",
        "expected": {
            "diarrhea": "positive",
            "fever": "negated",
            "vomiting": "negated"
        }
    },
    {
        "id": "HING_SYM030",
        "text": "Mera heart fast beat kar raha hai aur chest discomfort bhi hai.",
        "expected": {
            "palpitations": "positive",
            "chest_pain": "positive"
        }
    },

    # ==========================================
    # D. HISTORICAL SYMPTOMS (8)
    # HING_SYM031–038
    # ==========================================

    {
        "id": "HING_SYM031",
        "text": "Last week mujhe severe chest pain hua tha.",
        "expected": {"chest_pain": "historical"}
    },
    {
        "id": "HING_SYM032",
        "text": "Two days ago mujhe high fever tha.",
        "expected": {"fever": "historical"}
    },
    {
        "id": "HING_SYM033",
        "text": "Pichhle month mujhe continuous cough ho rahi thi.",
        "expected": {"cough": "historical"}
    },
    {
        "id": "HING_SYM034",
        "text": "Earlier mujhe frequent headaches hote the.",
        "expected": {"headache": "historical"}
    },
    {
        "id": "HING_SYM035",
        "text": "Kal loose motions hue the but ab completely resolved hain.",
        "expected": {"diarrhea": "historical"}
    },
    {
        "id": "HING_SYM036",
        "text": "Three days pehle mujhe vomiting hui thi.",
        "expected": {"vomiting": "historical"}
    },
    {
        "id": "HING_SYM037",
        "text": "Last illness ke time mujhe breathing problem hui thi.",
        "expected": {"breathlessness": "historical"}
    },
    {
        "id": "HING_SYM038",
        "text": "Kuch months pehle mujhe dizziness ke episodes aate the.",
        "expected": {"dizziness": "historical"}
    },

    # ==========================================
    # E. UNCERTAIN SYMPTOMS (6)
    # HING_SYM039–044
    # ==========================================

    {
        "id": "HING_SYM039",
        "text": "Shayad mujhe chest pain ho raha hai, not sure.",
        "expected": {"chest_pain": "uncertain"}
    },
    {
        "id": "HING_SYM040",
        "text": "I think mujhe fever ho sakta hai.",
        "expected": {"fever": "uncertain"}
    },
    {
        "id": "HING_SYM041",
        "text": "Maybe mera headache start ho raha hai.",
        "expected": {"headache": "uncertain"}
    },
    {
        "id": "HING_SYM042",
        "text": "Lagta hai ki mujhe breathing difficulty ho sakti hai.",
        "expected": {"breathlessness": "uncertain"}
    },
    {
        "id": "HING_SYM043",
        "text": "Mujhe nausea jaisa feel ho raha hai, but confirm nahi hai.",
        "expected": {"nausea": "uncertain"}
    },
    {
        "id": "HING_SYM044",
        "text": "Possibly mere stomach mein pain ho raha hai.",
        "expected": {"abdominal_pain": "uncertain"}
    },

    # ==========================================
    # F. CLINICAL EXPRESSIONS (6)
    # HING_SYM045–050
    # ==========================================

    {
        "id": "HING_SYM045",
        "text": "Mujhe exertion ke time dyspnea feel hota hai.",
        "expected": {"breathlessness": "positive"}
    },
    {
        "id": "HING_SYM046",
        "text": "Mere sir mein intense cephalalgia ho rahi hai.",
        "expected": {"headache": "positive"}
    },
    {
        "id": "HING_SYM047",
        "text": "Body temperature high hai aur patient febrile lag raha hai.",
        "expected": {"fever": "positive"}
    },
    {
        "id": "HING_SYM048",
        "text": "Patient ko repeated emesis episodes ho rahe hain.",
        "expected": {"vomiting": "positive"}
    },
    {
        "id": "HING_SYM049",
        "text": "Mere joints mein arthralgia aur stiffness dono hain.",
        "expected": {"joint_pain": "positive"}
    },
    {
        "id": "HING_SYM050",
        "text": "Exercise ke baad muscles mein severe myalgia hoti hai.",
        "expected": {"muscle_pain": "positive"}
    },

    # ==========================================
    # G. ROBUSTNESS AND COMPLEX NEGATION (10)
    # HING_SYM051–060
    # ==========================================

    {
        "id": "HING_SYM051",
        "text": "Mujhe na fever hai, na cough hai aur neither headache.",
        "expected": {
            "fever": "negated",
            "cough": "negated",
            "headache": "negated"
        }
    },
    {
        "id": "HING_SYM052",
        "text": "Fever toh hai, but cough aur cold dono nahi hain.",
        "expected": {
            "fever": "positive",
            "cough": "negated",
            "common_cold": "negated"
        }
    },
    {
        "id": "HING_SYM053",
        "text": "Mujhe fever nahi hai, lekin chills aur body shivering ho rahi hai.",
        "expected": {
            "fever": "negated",
            "chills": "positive"
        }
    },
    {
        "id": "HING_SYM054",
        "text": "Lower back mein persistent pain hai, especially while bending.",
        "expected": {"back_pain": "positive"}
    },
    {
        "id": "HING_SYM055",
        "text": "Urination ke time burning sensation aur pain hota hai.",
        "expected": {"burning_micturition": "positive"}
    },
    {
        "id": "HING_SYM056",
        "text": "Raat ko excessive sweating hoti hai, even when room cool ho.",
        "expected": {"sweating": "positive"}
    },
    {
        "id": "HING_SYM057",
        "text": "Mere dono legs mein swelling aur heaviness feel hoti hai.",
        "expected": {"swelling": "positive"}
    },
    {
        "id": "HING_SYM058",
        "text": "I don't feel hungry at all, bhookh bilkul nahi lagti.",
        "expected": {"loss_of_appetite": "positive"}
    },
    {
        "id": "HING_SYM059",
        "text": "Door ki objects clearly nahi dikh rahi, vision blurred ho gaya hai.",
        "expected": {"blurred_and_distorted_vision": "positive"}
    },
    {
        "id": "HING_SYM060",
        "text": "Patient ko chills aur fever hai, but body pain nahi hai.",
        "expected": {
            "chills": "positive",
            "fever": "positive",
            "body_pain": "negated"
        }
    },
    # ==========================================
# O. EXPERIENCER DETECTION
# ==========================================

{
    "id": "NEW001",
    "text": "My mother has been suffering from severe chest pain.",
    "expected": {"chest_pain": "other"}
},
{
    "id": "NEW002",
    "text": "My father has diabetes and frequent dizziness.",
    "expected": {"dizziness": "other"}
},
{
    "id": "NEW003",
    "text": "I have fever, but my brother has a cough.",
    "expected": {
        "fever": "positive",
        "cough": "other"
    }
},
{
    "id": "NEW004",
    "text": "My child is vomiting repeatedly.",
    "expected": {"vomiting": "other"}
},
{
    "id": "NEW005",
    "text": "My grandmother complains of joint pain.",
    "expected": {"joint_pain": "other"}
},
{
    "id": "NEW006",
    "text": "Meri maa ko bahut tez bukhar hai.",
    "expected": {"fever": "other"}
},
{
    "id": "NEW007",
    "text": "Papa ko saans lene mein dikkat ho rahi hai.",
    "expected": {"breathlessness": "other"}
},
{
    "id": "NEW008",
    "text": "Mujhe bukhar hai, lekin meri behen ko khaansi hai.",
    "expected": {
        "fever": "positive",
        "cough": "other"
    }
},
{
    "id": "NEW009",
    "text": "My husband had severe abdominal pain yesterday.",
    "expected": {"abdominal_pain": "other"}
},
{
    "id": "NEW010",
    "text": "Patient reports that her mother experiences frequent headaches.",
    "expected": {"headache": "other"}
},
# ==========================================
# P. CONDITIONAL AND HYPOTHETICAL SYMPTOMS
# ==========================================

{
    "id": "NEW011",
    "text": "I experience chest pain only while walking.",
    "expected": {"chest_pain": "positive"}
},
{
    "id": "NEW012",
    "text": "I feel dizzy whenever I stand up suddenly.",
    "expected": {"dizziness": "positive"}
},
{
    "id": "NEW013",
    "text": "I develop a headache after prolonged screen exposure.",
    "expected": {"headache": "positive"}
},
{
    "id": "NEW014",
    "text": "If I eat spicy food, I experience abdominal pain.",
    "expected": {"abdominal_pain": "positive"}
},
{
    "id": "NEW015",
    "text": "I might develop fever in the coming days.",
    "expected": {"fever": "hypothetical"}
},
{
    "id": "NEW016",
    "text": "If I get an infection, I usually experience chills.",
    "expected": {"chills": "conditional"}
},
{
    "id": "NEW017",
    "text": "Mujhe sirf chalne par saans phoolti hai.",
    "expected": {"breathlessness": "positive"}
},
{
    "id": "NEW018",
    "text": "Jab bhi main khana khata hoon, pet mein dard hota hai.",
    "expected": {"abdominal_pain": "positive"}
},
{
    "id": "NEW019",
    "text": "Agar mujhe bukhar hua toh main doctor ke paas jaunga.",
    "expected": {"fever": "hypothetical"}
},
{
    "id": "NEW020",
    "text": "Mujhe shayad exercise karne par dizziness ho sakti hai.",
    "expected": {"dizziness": "uncertain"}
},
# ==========================================
# Q. ADVANCED NEGATION SCOPE
# ==========================================

{
    "id": "NEW021",
    "text": "No fever, but severe headache and vomiting are present.",
    "expected": {
        "fever": "negated",
        "headache": "positive",
        "vomiting": "positive"
    }
},
{
    "id": "NEW022",
    "text": "I do not have fever anymore, but my cough continues.",
    "expected": {
        "fever": "historical",
        "cough": "positive"
    }
},
{
    "id": "NEW023",
    "text": "I am not free from chest pain.",
    "expected": {"chest_pain": "positive"}
},
{
    "id": "NEW024",
    "text": "There is no evidence that the patient has a headache.",
    "expected": {"headache": "negated"}
},
{
    "id": "NEW025",
    "text": "Mujhe bukhar nahi hai, par sir dard bahut hai.",
    "expected": {
        "fever": "negated",
        "headache": "positive"
    }
},
{
    "id": "NEW026",
    "text": "Khaansi nahi hai, lekin gale mein dard aur bukhar hai.",
    "expected": {
        "cough": "negated",
        "sore_throat": "positive",
        "fever": "positive"
    }
},
{
    "id": "NEW027",
    "text": "Patient denies neither nausea nor vomiting.",
    "expected": {
        "nausea": "positive",
        "vomiting": "positive"
    }
},
{
    "id": "NEW028",
    "text": "I have no pain except occasional abdominal pain.",
    "expected": {"abdominal_pain": "positive"}
},
{
    "id": "NEW029",
    "text": "Na bukhar hai, na ulti, bas pet mein dard hai.",
    "expected": {
        "fever": "negated",
        "vomiting": "negated",
        "abdominal_pain": "positive"
    }
},
{
    "id": "NEW030",
    "text": "Headache is absent, whereas dizziness is present.",
    "expected": {
        "headache": "negated",
        "dizziness": "positive"
    }
},
# ==========================================
# R. INFORMAL LANGUAGE AND MISSPELLINGS
# ==========================================

{
    "id": "NEW031",
    "text": "I have a very bad hedache since morning.",
    "expected": {"headache": "positive"}
},
{
    "id": "NEW032",
    "text": "Mujhe bukhar aur sar dard ho rha h.",
    "expected": {
        "fever": "positive",
        "headache": "positive"
    }
},
{
    "id": "NEW033",
    "text": "Chest me pain ho rha hai aur saans bhi nahi aa rahi.",
    "expected": {
        "chest_pain": "positive",
        "breathlessness": "positive"
    }
},
{
    "id": "NEW034",
    "text": "I am feeling week and tierd.",
    "expected": {
        "weakness": "positive",
        "fatigue": "positive"
    }
},
{
    "id": "NEW035",
    "text": "Mera pet dukh raha h aur ulti jaisa lag raha h.",
    "expected": {
        "abdominal_pain": "positive",
        "nausea": "positive"
    }
},
{
    "id": "NEW036",
    "text": "Mujhe khansi aur zukam hai.",
    "expected": {
        "cough": "positive",
        "common_cold": "positive"
    }
},
{
    "id": "NEW037",
    "text": "I feel like puking after eating.",
    "expected": {"nausea": "positive"}
},
{
    "id": "NEW038",
    "text": "My tummy hurts badly.",
    "expected": {"abdominal_pain": "positive"}
},
{
    "id": "NEW039",
    "text": "Meri saans ful rhi h.",
    "expected": {"breathlessness": "positive"}
},
{
    "id": "NEW040",
    "text": "Sir me dard hai but fever nhi hai.",
    "expected": {
        "headache": "positive",
        "fever": "negated"
    }
},

    # ==========================================
# S. TEMPORAL REASONING
# ==========================================

{
    "id": "NEW041",
    "text": "I had fever yesterday, but I am completely fine today.",
    "expected": {"fever": "historical"}
},
{
    "id": "NEW042",
    "text": "My cough started three days ago and is still present.",
    "expected": {"cough": "positive"}
},
{
    "id": "NEW043",
    "text": "I used to have headaches, but they stopped last month.",
    "expected": {"headache": "historical"}
},
{
    "id": "NEW044",
    "text": "Fever keeps returning every evening.",
    "expected": {"fever": "positive"}
},
{
    "id": "NEW045",
    "text": "I have been experiencing continuous abdominal pain for two weeks.",
    "expected": {"abdominal_pain": "positive"}
},
{
    "id": "NEW046",
    "text": "Mujhe kal bukhar tha, aaj nahi hai.",
    "expected": {"fever": "historical"}
},
{
    "id": "NEW047",
    "text": "Pichhle teen din se khaansi ho rahi hai aur abhi bhi hai.",
    "expected": {"cough": "positive"}
},
{
    "id": "NEW048",
    "text": "Mera sir dard pehle theek ho gaya tha, lekin ab phir shuru ho gaya hai.",
    "expected": {"headache": "positive"}
},
{
    "id": "NEW049",
    "text": "I experienced vomiting last night and have nausea currently.",
    "expected": {
        "vomiting": "historical",
        "nausea": "positive"
    }
},
{
    "id": "NEW050",
    "text": "The patient has recurrent episodes of dizziness.",
    "expected": {"dizziness": "positive"}
},
# ==========================================
# T. CLINICAL ABBREVIATIONS
# ==========================================

{
    "id": "NEW051",
    "text": "Patient complains of SOB during walking.",
    "expected": {"breathlessness": "positive"}
},
{
    "id": "NEW052",
    "text": "Patient reports DOE.",
    "expected": {"breathlessness": "positive"}
},
{
    "id": "NEW053",
    "text": "Patient is afebrile.",
    "expected": {"fever": "negated"}
},
{
    "id": "NEW054",
    "text": "Patient complains of CP.",
    "expected": {"chest_pain": "positive"}
},
{
    "id": "NEW055",
    "text": "Patient reports N/V since morning.",
    "expected": {
        "nausea": "positive",
        "vomiting": "positive"
    }
},
{
    "id": "NEW056",
    "text": "Patient has c/o headache and dizziness.",
    "expected": {
        "headache": "positive",
        "dizziness": "positive"
    }
},
{
    "id": "NEW057",
    "text": "Patient denies SOB.",
    "expected": {"breathlessness": "negated"}
},
{
    "id": "NEW058",
    "text": "Patient reports intermittent palpitations.",
    "expected": {"palpitations": "positive"}
},
{
    "id": "NEW059",
    "text": "Patient has dysuria.",
    "expected": {"burning_micturition": "positive"}
},
{
    "id": "NEW060",
    "text": "Patient complains of anorexia.",
    "expected": {"loss_of_appetite": "positive"}
},
# ==========================================
# U. SYMPTOM ATTRIBUTES
# ==========================================

{
    "id": "NEW061",
    "text": "I have severe pain in my right lower abdomen.",
    "expected": {"abdominal_pain": "positive"}
},
{
    "id": "NEW062",
    "text": "Mild headache started this morning.",
    "expected": {"headache": "positive"}
},
{
    "id": "NEW063",
    "text": "I have moderate pain in both knees.",
    "expected": {"joint_pain": "positive"}
},
{
    "id": "NEW064",
    "text": "Sharp pain in the left side of my chest.",
    "expected": {"chest_pain": "positive"}
},
{
    "id": "NEW065",
    "text": "My lower back hurts whenever I bend.",
    "expected": {"back_pain": "positive"}
},
{
    "id": "NEW066",
    "text": "Mere daaye pair mein sujan hai.",
    "expected": {"swelling": "positive"}
},
{
    "id": "NEW067",
    "text": "Mujhe halki si khaansi ho rahi hai.",
    "expected": {"cough": "positive"}
},
{
    "id": "NEW068",
    "text": "I have a burning sensation in my throat.",
    "expected": {"sore_throat": "positive"}
},
{
    "id": "NEW069",
    "text": "Severe headache with sensitivity to light.",
    "expected": {
        "headache": "positive"
    }
},
{
    "id": "NEW070",
    "text": "Both feet are swollen and painful.",
    "expected": {
        "swelling": "positive",
        "foot_pain": "positive"
    }
},

    # ==========================================
    # V. COREFERENCE RESOLUTION
    # NEW071–076
    # ==========================================

    {
        "id": "NEW071",
        "text": "I have a headache and it becomes worse in the evening.",
        "expected": {"headache": "positive"}
    },
    {
        "id": "NEW072",
        "text": "My chest hurts. This pain increases when I walk.",
        "expected": {"chest_pain": "positive"}
    },
    {
        "id": "NEW073",
        "text": "I have fever and cough. The latter is getting worse.",
        "expected": {
            "fever": "positive",
            "cough": "positive"
        }
    },
    {
        "id": "NEW074",
        "text": "Mere pet mein dard hai aur yeh raat ko badh jata hai.",
        "expected": {"abdominal_pain": "positive"}
    },
    {
        "id": "NEW075",
        "text": "I have dizziness and nausea. This feeling occurs after standing.",
        "expected": {
            "dizziness": "positive",
            "nausea": "positive"
        }
    },
    {
        "id": "NEW076",
        "text": "Mujhe sir dard hai. Yeh dard subah se ho raha hai.",
        "expected": {"headache": "positive"}
    },

    # ==========================================
    # W. SEVERITY EXTRACTION
    # NEW077–082
    # ==========================================

    {
        "id": "NEW077",
        "text": "I have mild headache since morning.",
        "expected": {"headache": "positive"},
        "expected_attributes": {
            "headache": {"severity": "mild"}
        }
    },
    {
        "id": "NEW078",
        "text": "Patient complains of moderate abdominal pain.",
        "expected": {"abdominal_pain": "positive"},
        "expected_attributes": {
            "abdominal_pain": {"severity": "moderate"}
        }
    },
    {
        "id": "NEW079",
        "text": "I am experiencing severe chest pain.",
        "expected": {"chest_pain": "positive"},
        "expected_attributes": {
            "chest_pain": {"severity": "severe"}
        }
    },
    {
        "id": "NEW080",
        "text": "Mujhe bahut tez sir dard ho raha hai.",
        "expected": {"headache": "positive"},
        "expected_attributes": {
            "headache": {"severity": "severe"}
        }
    },
    {
        "id": "NEW081",
        "text": "Mere pet mein halka sa dard hai.",
        "expected": {"abdominal_pain": "positive"},
        "expected_attributes": {
            "abdominal_pain": {"severity": "mild"}
        }
    },
    {
        "id": "NEW082",
        "text": "The patient describes unbearable pain in the chest.",
        "expected": {"chest_pain": "positive"},
        "expected_attributes": {
            "chest_pain": {"severity": "severe"}
        }
    },

    # ==========================================
    # X. DURATION AND ONSET EXTRACTION
    # NEW083–088
    # ==========================================

    {
        "id": "NEW083",
        "text": "I have been suffering from fever for three days.",
        "expected": {"fever": "positive"},
        "expected_attributes": {
            "fever": {"duration": "3 days"}
        }
    },
    {
        "id": "NEW084",
        "text": "My cough started suddenly this morning.",
        "expected": {"cough": "positive"},
        "expected_attributes": {
            "cough": {"onset": "sudden", "duration": "since this morning"}
        }
    },
    {
        "id": "NEW085",
        "text": "I have had continuous abdominal pain for two weeks.",
        "expected": {"abdominal_pain": "positive"},
        "expected_attributes": {
            "abdominal_pain": {
                "duration": "2 weeks",
                "pattern": "continuous"
            }
        }
    },
    {
        "id": "NEW086",
        "text": "Mujhe kal raat se khaansi ho rahi hai.",
        "expected": {"cough": "positive"},
        "expected_attributes": {
            "cough": {"duration": "since last night"}
        }
    },
    {
        "id": "NEW087",
        "text": "The headache began approximately thirty minutes ago.",
        "expected": {"headache": "positive"},
        "expected_attributes": {
            "headache": {"duration": "30 minutes"}
        }
    },
    {
        "id": "NEW088",
        "text": "For the past six months, I have experienced recurring joint pain.",
        "expected": {"joint_pain": "positive"},
        "expected_attributes": {
            "joint_pain": {
                "duration": "6 months",
                "pattern": "recurring"
            }
        }
    },

    # ==========================================
    # Y. ANATOMICAL SPECIFICITY AND LATERALITY
    # NEW089–094
    # ==========================================

    {
        "id": "NEW089",
        "text": "I have pain in the right lower abdomen.",
        "expected": {"abdominal_pain": "positive"},
        "expected_attributes": {
            "abdominal_pain": {
                "location": "lower abdomen",
                "laterality": "right"
            }
        }
    },
    {
        "id": "NEW090",
        "text": "There is sharp pain on the left side of my chest.",
        "expected": {"chest_pain": "positive"},
        "expected_attributes": {
            "chest_pain": {
                "location": "chest",
                "laterality": "left"
            }
        }
    },
    {
        "id": "NEW091",
        "text": "I have pain in my upper back.",
        "expected": {"back_pain": "positive"},
        "expected_attributes": {
            "back_pain": {"location": "upper back"}
        }
    },
    {
        "id": "NEW092",
        "text": "Mere daaye ghutne mein dard ho raha hai.",
        "expected": {"joint_pain": "positive"},
        "expected_attributes": {
            "joint_pain": {
                "location": "knee",
                "laterality": "right"
            }
        }
    },
    {
        "id": "NEW093",
        "text": "Both my feet are swollen.",
        "expected": {"swelling": "positive"},
        "expected_attributes": {
            "swelling": {
                "location": "feet",
                "laterality": "bilateral"
            }
        }
    },
    {
        "id": "NEW094",
        "text": "Pain is present in my left lower back.",
        "expected": {"back_pain": "positive"},
        "expected_attributes": {
            "back_pain": {
                "location": "lower back",
                "laterality": "left"
            }
        }
    },

    # ==========================================
    # Z. ADVANCED CODE-SWITCHING
    # NEW095–100
    # ==========================================

    {
        "id": "NEW095",
        "text": "Mujhe severe headache ho raha hai since yesterday.",
        "expected": {"headache": "positive"},
        "expected_attributes": {
            "headache": {
                "severity": "severe",
                "duration": "since yesterday"
            }
        }
    },
    {
        "id": "NEW096",
        "text": "Patient ko fever nahi hai but severe body pain aur weakness hai.",
        "expected": {
            "fever": "negated",
            "body_pain": "positive",
            "weakness": "positive"
        }
    },
    {
        "id": "NEW097",
        "text": "Mujhe breathing difficulty ho rahi hai while walking, but rest karne par theek ho jata hai.",
        "expected": {"breathlessness": "positive"}
    },
    {
        "id": "NEW098",
        "text": "I have loose motions since morning, lekin vomiting bilkul nahi ho rahi.",
        "expected": {
            "diarrhea": "positive",
            "vomiting": "negated"
        }
    },
    {
        "id": "NEW099",
        "text": "Mera left shoulder pain kar raha hai and movement karne par pain increase hota hai.",
        "expected": {"shoulder_pain": "positive"}
    },
    {
        "id": "NEW100",
        "text": "Mujhe fever tha yesterday, but abhi headache aur dizziness ho rahi hai.",
        "expected": {
            "fever": "historical",
            "headache": "positive",
            "dizziness": "positive"
        }
    },

    # ==========================================
    # AA. SYMPTOM VS DISEASE DISTINCTION
    # NEW101–105
    # ==========================================

    {
        "id": "NEW101",
        "text": "The patient has diabetes and complains of dizziness.",
        "expected": {"dizziness": "positive"}
    },
    {
        "id": "NEW102",
        "text": "Patient has hypertension but denies headache.",
        "expected": {"headache": "negated"}
    },
    {
        "id": "NEW103",
        "text": "The patient was diagnosed with malaria last week.",
        "expected": {}
    },
    {
        "id": "NEW104",
        "text": "I have asthma and currently experience breathlessness.",
        "expected": {"breathlessness": "positive"}
    },
    {
        "id": "NEW105",
        "text": "The patient has tuberculosis, but no cough or fever.",
        "expected": {
            "cough": "negated",
            "fever": "negated"
        }
    },

    # ==========================================
    # AB. FAMILY HISTORY DETECTION
    # NEW106–110
    # ==========================================

    {
        "id": "NEW106",
        "text": "My mother has a history of diabetes.",
        "expected": {}
    },
    {
        "id": "NEW107",
        "text": "My father frequently experiences chest pain.",
        "expected": {"chest_pain": "other"}
    },
    {
        "id": "NEW108",
        "text": "My grandmother had hypertension and frequent headaches.",
        "expected": {"headache": "other"}
    },
    {
        "id": "NEW109",
        "text": "My family has a history of asthma, but I have no breathing difficulty.",
        "expected": {"breathlessness": "negated"}
    },
    {
        "id": "NEW110",
        "text": "Meri maa ko diabetes hai aur mujhe bukhar ho raha hai.",
        "expected": {
            "fever": "positive"
        }
    },

    # ==========================================
    # AC. CONTRADICTORY SYMPTOM REPORTS
    # NEW111–115
    # ==========================================

    {
        "id": "NEW111",
        "text": "I have fever, but I do not have fever.",
        "expected": {"fever": "conflicting"}
    },
    {
        "id": "NEW112",
        "text": "Patient initially reports chest pain but later denies having it.",
        "expected": {"chest_pain": "conflicting"}
    },
    {
        "id": "NEW113",
        "text": "Mujhe bukhar hai, lekin abhi keh raha hoon ki bukhar nahi hai.",
        "expected": {"fever": "conflicting"}
    },
    {
        "id": "NEW114",
        "text": "The patient reports both presence and absence of headache.",
        "expected": {"headache": "conflicting"}
    },
    {
        "id": "NEW115",
        "text": "Patient says cough is present, but the examination notes no cough.",
        "expected": {"cough": "conflicting"}
    },


]
