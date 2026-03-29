import re

def extract_state_from_text(case_text):
    """
    Extract legal facts/state from text using robust NLP (Arabic/English).
    """
    state = {}
    
    # 1. عناصر القصد والظروف (Intent & Circumstances)
    if re.search(r"عمد|عن قصد|قاصد|عمداً|متعمد|بنية|أردى|أزهق|intent", case_text, re.I): state["intent"] = True
    if re.search(r"سبق إصرار|سبق الإصرار|ترصد|بترصد|الترصد|خطط|دبّر|premeditation", case_text, re.I): state["premeditation"] = True
    if re.search(r"إهمال|رعونة|غير عمد|خطأ|دون قصد|بغير قصد|negligence", case_text, re.I): state["negligence"] = True
    if re.search(r"دفاع شرعي|دفع اعتداء|اتقاء خطر|دافع عن نفسه|self defense", case_text, re.I): state["self_defense"] = True
    if re.search(r"بالإكراه|بالقوة|غصباً|force", case_text, re.I): state["by_force"] = True
    if re.search(r"ليلاً|بالليل|في الليل|at night", case_text, re.I): state["at_night"] = True
    if re.search(r"حدث|أقل من 18|صبي|صغير|juvenile", case_text, re.I): state["juvenile_offender"] = True

    # 2. الجرائم (Crimes)
    if re.search(r"قتل|أزهق|حياة|بقتل|murder|kill", case_text, re.I): state["murder"] = True
    if re.search(r"ضرب|جرح|اعتداء|إيذاء|اعتدى|hurt|assault", case_text, re.I): state["assault"] = True
    if re.search(r"سرق|اختلس|نهب|استولى|theft|rob|stolen", case_text, re.I): state["theft"] = True
    if re.search(r"نصب|احتيال|fraud|scam", case_text, re.I): state["fraud"] = True
    if re.search(r"تزوير|زور|forgery|forge", case_text, re.I): state["forgery"] = True
    if re.search(r"خطف|اختطاف|kidnap", case_text, re.I): state["kidnapping"] = True
    if re.search(r"حريق|أشعل نار|burned|fire|arson", case_text, re.I): state["arson"] = True
    if re.search(r"سلاح|مسدس|سكين|آلة حادة|بآلة|weapon|gun|knife", case_text, re.I): 
        state["weapon"] = True
        state["weapon_used"] = True
    if re.search(r"مخدرات|حشيش|drug|narcotic", case_text, re.I): state["drug"] = True
    if re.search(r"موظف عام|بحكم وظيفته|رسمي|public official", case_text, re.I): state["public_official"] = True
    if re.search(r"بليغة|جسيمة|شديدة|عاهة|severe|disability", case_text, re.I): 
        state["severe_injury"] = True
        if re.search(r"عاهة", case_text): state["permanent_disability"] = True
    if re.search(r"مسكن|منزل|بيت|شقة|residence|house", case_text, re.I): state["from_residence"] = True

    # 3. القانون المدني والالتزامات (Civil)
    if re.search(r"أخطأ|خطأ|بخطئه|غلط|إهمال|fault|negligence|breach", case_text, re.I): state["civil_fault"] = True
    if re.search(r"ضرر|يضر|خسارة|تلف|إتلاف|injury|damage|loss", case_text, re.I): state["injury"] = True
    if re.search(r"عقد|اتفاق|تعاقد|contract|agreement", case_text, re.I): state["contract"] = True
    if re.search(r"تعويض|يطالب|مطالبة|compensation|indemnity", case_text, re.I): state["reparation"] = True
    if re.search(r"فسخ|إنهاء عقد|فسخ العقد|rescission|termination", case_text, re.I): state["nullity_civil"] = True

    # 4. الإجراءات الجنائية (Procedural)
    if re.search(r"بطلان|باطل|بطلان إجراء|void|null|nullity", case_text, re.I) and not re.search(r"فسخ|عقد", case_text): 
        state["nullity_procedural"] = True
    if re.search(r"بدون إذن|بغير إذن|دون إذن|بلا إذن|no warrant", case_text, re.I): state["nullity_procedural"] = True
    if re.search(r"تفتيش|فتشوه|صادروا|search|seizure", case_text, re.I): state["search"] = True
    if re.search(r"قبض|اعتقل|arrest", case_text, re.I): state["arrest"] = True
    if re.search(r"تقادم|انقضاء|انقضت|مضي مدة|expiration|prescription", case_text, re.I): state["expiration"] = True
    if re.search(r"دليل|أدلة|evidence", case_text, re.I): state["evidence"] = True

    # 5. تنظيف وضبط القيم الافتراضية
    all_keys = [
        "murder", "assault", "kidnapping", "sexual_crime", "theft", "robbery", 
        "fraud", "forgery", "bribery", "embezzlement", "arson", "vandalism", 
        "trespass", "defamation", "perjury", "drug", "weapon", "smuggling",
        "intent", "negligence", "self_defense", "by_force", "with_weapon", 
        "at_night", "group", "public_official", "family_relation", "recidivism",
        "minor_victim", "under_influence", "aggravating", "juvenile_offender",
        "weapon_used", "severe_injury", "permanent_disability", "from_residence",
        "civil_fault", "injury", "contract", "reparation", "nullity_civil", "nullity_procedural",
        "search", "arrest", "expiration", "evidence"
    ]
    for k in all_keys:
        if k not in state:
            state[k] = False

    # 6. تحديد النطاق (Domain Detection)
    criminal_facts_triggers = [
        "murder", "assault", "kidnapping", "theft", "fraud", "forgery", "arson", 
        "drug", "weapon", "search", "arrest", "expiration", "nullity_procedural"
    ]
    has_crime = any(state.get(f) for f in criminal_facts_triggers)
    state["_civil_only"] = not has_crime

    return state
