import psycopg2
import re
import math
import json
import copy
from conflict_resolver import execute as engine_execute, resolve_conflicts
from fact_system import make_true, make_false, get_fact_value, get_active_facts_summary, get_confidence_weighted_facts
from inference_logger import InferenceLog

# ⚖️ Judicial Language Templates (v3.5)
JUDICIAL_TEMPLATES = {
    "reject_self_defense": "وحيث إنه عن الدفع بقيام حالة الدفاع الشرعي، ولما كان الثابت من الأوراق خلو الواقعة من خطر حال يهدد النفس أو المال، فإن هذا الدفع يكون على غير سند من الواقع والقانون متعيناً رفضه.",
    "reject_necessity": "وحيث إنه عن التمسك بحالة الضرورة، فإنه لما لم يثبت وقوع إكراه مادي لا قبل للمتهم بدفعه، فإن التمسك بهذا الظرف لا يعدو أن يكون قولاً مرسلاً لا يعول عليه.",
    "accept_murder": "وحيث إن الواقعة قد استقرت في يقين المحكمة واطمأن إليها وجدانها، وقد توافرت أركان جريمة القتل العمد المشروطة قانوناً، فإن المحكمة تقضي بإدانة المتهم.",
    "accept_premeditation": "ولما كان المتهم قد صمم على ارتباك الجريمة وأعد لها ذخيرته وتربص للمجني عليه، فإن ظرف سبق الإصرار يكون قائماً في حقه.",
    "accept_nullity": "وحيث إن التفتيش قد وقع باطلاً لعدم استناد مأمور الضبط القضائي لإذن نيابة أو حالة تلبس، فإنه يبطل ما تلاه من إجراءات وما نتج عنه من دليل.",
    "contradiction_logic": "وحيث إن رواية المتهم قد تهاوت أمام الحقائق المادية الثابتة بالأوراق، ووقعت في تعارض منطقي يمنع المحكمة من الأخذ بها.",
    "general_conviction": "وحيث إنه ولما تقدم، فقد تيقن للمحكمة صحة إسناد التهمة للمتهم، مما يتعين معه عقابه بمقتضى نصوص القانون.",
    "transition_fact": "ولما كان من المقرر قانوناً أن {fact_logic}، فإنه..."
}

DB_PARAMS = {
    "dbname": "counselor",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5433"
}

# =============================================
# NLP: Eternal Glory Extraction (v18.2)
# =============================================
def extract_state_from_text(case_text):
    state = {}
    clean_text = case_text.replace("ـ", " ")
    clean_text = re.sub(r"[أإآ]", "ا", clean_text)
    clean_text = re.sub(r"\s+", " ", clean_text)
    
    negated_intent = bool(re.search(r"دون قصد|بغير قصد|بلا قصد|غير عمد|دون عمد|لم يقصد|لم يتعمد", clean_text, re.I))
    uncertainty = bool(re.search(r"يحتمل|قد|ربما|من الممكن|لعله|شبهة|يشتبه", clean_text, re.I))
    
    base_confidence = 0.4 if uncertainty else 0.9
    patterns = {
        "intent": r"عمد|قصد|قاصد|بنية|تعمد|إصرار|ترصد|ازهق",
        "murder": r"قتل|ذبح|خنق|مميتة|وفاة|أودى بحياة|إزهاق",
        "assault": r"ضرب|جرح|لكم|ركل|اعتداء|بدأ بالضرب|طعن|طعنه",
        "weapon_used": r"سكين|سلاح|مسدس|بندقية|أداة حادة|عصا|حجر",
        "imminent_danger": r"هجم|هدد|تعدى|حاول|خطر|خاطر|على وشك",
        "self_defense": r"دفاع|شرعي|اضطررت|كان سيقتلني|رد اعتداء",
        "necessity": r"ضرورة|اضطرار|ملجأ|هرب|خلاص",
        "nullity_procedural": r"بطلان|إجراءات|تفتيش|قبض|بدون إذن|غير قانوني",
        "premeditation": r"سبق اصرار|ترصد|خطط|دبر|انتقام|ثار|بيت النية|صمم على",
        "negligence": r"اهمال|رعونة|غير عمد|خطا|دون قصد",
        "temporal_gap": r"بعد ساعات|بعد ايام|بعد الواقعة|لاحقا|بعد فترة",
        "by_force": r"كره|اكراه|مكره|قوة|غصب|اجبر|عنوة|تهديد",
        "at_night": r"ليلا|ليل|اقتحم|اقتحام",
        "group": r"عصابة|جماعة|اشخاص|متعدد|تشكيل",
        "juvenile_offender": r"حدث|اقل من 18|قاصر|طفل",
        "murder": r"قتل|ازهق|حياة|بقتل|قتله|جثة|وفاة|اطلاق نار",
        "assault": r"ضرب|جرح|اعتداء|ايذاء|اعتدى|اصابة|اصاب",
        "theft": r"سرق|سارق|مسروق|اختلس|نهب|استولى|اخذ",
        "forgery": r"تزوير|زور|تغيير بيانات|تبديل حقائق",
        "kidnapping": r"خطف|اختطاف",
        "weapon_used": r"سلاح|مسدس|سكين|الة حادة",
        "severe_injury": r"بليغة|جسيمة|شديدة|عاهة",
        "permanent_disability": r"عاهة مستديمة",
        "from_residence": r"مسكن|منزل|بيت|شقة",
        "nullity_procedural": r"\bبطلان\b|\bباطل\b|\bاخلال\b",
        "search": r"تفتيش|فتش|ضبط",
        "evidence": r"دليل|ادلة|وجدوا|ضبط|عثر",
        "confession": r"اقر|اعترف|اعتراف|ادلى باعتراف",
        "no_warrant": r"بدون اذن|عدم وجود اذن|خلو من اذن|لا يوجد اذن|بغير اذن|خلو الاوراق من اذن",
        "red_handed": r"تلبس|متلبس",
        "necessity": r"حالة ضرورة|ضرورة قصوى|اكراه|مكره|اضطر|اضطرار"
    }

    # Smart Procedural Negation (v6.0.5/6.1.0)
    # Detects "Lack of red-handedness" even with interleaved text
    if re.search(r"لعدم|انتفاء|عدم وجود|خلو.*?(?:حالة ال)?تلبس", clean_text):
        state["red_handed"] = make_false()
    elif re.search(patterns["red_handed"], clean_text):
        state["red_handed"] = make_true(0.95)

    if re.search(r"بطلان|باطل|غير قانوني|لعدم استناد|لعدم وجود اذن", clean_text):
        state["procedural_error"] = make_true(0.99)
        state["no_warrant"] = make_true(0.99)
        state["nullity_procedural"] = make_true(0.99)
    
    for key, p in patterns.items():
        if re.search(p, clean_text, re.I):
            if key == "intent" and negated_intent: continue
            state[key] = make_true(base_confidence)

    if re.search(r"شروع|حاول|بدأ في|لم يكمل", clean_text, re.I):
        state["attempted"] = make_true(0.9)

    all_keys = list(patterns.keys()) + ["attempted", "civil_fault", "injury", "contract", "reparation", "expiration"]
    for k in all_keys:
        if k not in state: state[k] = make_false()

    crim_triggers = ["murder", "assault", "kidnapping", "theft", "forgery", "nullity_procedural", "search"]
    has_crime = any(get_fact_value(state.get(f)) for f in crim_triggers)
    state["_civil_only"] = not has_crime
    # High-Priority Detection Enhancement (v6.1.0)
    if re.search(r"طعن|قتل|ذبح|وفاة|وفاته|ازهق|اطلاق نار|اطلق النار", clean_text):
        results = {}
        if re.search(r"قتل|ذبح|وفاة|وفاته|ازهق|اطلاق نار|اطلق النار", clean_text): 
            results["murder"] = {"value": True, "confidence": 0.98}
        if re.search(r"طعن", clean_text): 
            results["assault"] = {"value": True, "confidence": 0.95}
        
        # Inject these directly
        for k, v in results.items():
            v["source"] = "direct_regex_v6"
            state[k] = v

    return state

# =============================================
# Event Splitter
# =============================================
TEMPORAL_MARKERS = [
    r"في يوم [\d\w]+", r"بتاريخ", r"بعد مرور", r"في ختام", r"بعد ساعات",
    r"بعد يومين", r"بعد الواقعة", r"لاحقا", r"بعد فترة", r"في نفس اليوم",
    r"في التحقيقات", r"اثناء المواجهة", r"وقت الضبط", r"لحظة"
]

def split_into_events(case_text: str) -> list:
    text = re.sub(r"[\u0623\u0625\u0622]", "\u0627", case_text)
    text = re.sub(r"\s+", " ", text).strip()
    global_expiration = bool(re.search(r"تقادم|انقض|مضي مدة", text, re.I))

    markers = []
    combined = "|".join(TEMPORAL_MARKERS)
    for m in re.finditer(combined, text, re.I):
        markers.append({"start": m.start(), "text": m.group()})

    boundaries = [0] + [m["start"] for m in markers]
    events = []
    current_threat = False

    for i, start in enumerate(boundaries):
        end = boundaries[i + 1] if i + 1 < len(boundaries) else len(text)
        seg = text[start:end].strip()
        if len(seg) < 15: continue
        
        if "تهديد" in seg or "توعد" in seg: current_threat = True

        events.append({
            "id": f"event_{i+1}",
            "text": seg,
            "start_index": start,
            "relative_time": markers[i-1]["text"] if i > 0 else "بداية الواقعة",
            "inherits_threat": current_threat and i > 0,
            "threat_level": 0.9 if current_threat else 0.5,
            "global_expiration": global_expiration
        })
    return events if events else [{"id": "event_1", "text": text, "start_index": 0, "relative_time": "بداية الواقعة", "inherits_threat": False, "threat_level": 0.5, "global_expiration": global_expiration}]

# =============================================
# SCENARIO GENERATION
# =============================================
CRITICAL_FACTS = ["self_defense", "intent", "necessity", "premeditation"]

def generate_scenarios(base_state: dict) -> list:
    scenarios = [base_state.copy()]
    has_weapon = get_fact_value(base_state.get("weapon_used"))
    has_assault = get_fact_value(base_state.get("assault"))
    has_danger = get_fact_value(base_state.get("imminent_danger"))
    has_threat = get_fact_value(base_state.get("by_force")) or get_fact_value(base_state.get("kidnapping"))
    has_crime = not base_state.get("_civil_only", True)
    
    for fact in CRITICAL_FACTS:
        s = base_state.copy()
        if get_fact_value(s.get(fact)):
            s[fact] = {"value": False, "confidence": 0.1, "source": "scenario", "flipped": True}
            scenarios.append(s)
        else:
            valid = False
            if fact == "self_defense" and (has_weapon or has_assault or has_danger): valid = True
            elif fact == "necessity" and (has_threat or has_danger): valid = True
            elif fact in ("intent", "premeditation") and has_crime: valid = True
            if valid:
                s[fact] = {"value": True, "confidence": 0.2, "source": "scenario", "flipped": True}
                scenarios.append(s)
    return scenarios

# =============================================
# ENGINE EXECUTION: Foundation v2 (Stateful Brain)
# =============================================

class StructuredEvent:
    def __init__(self, event_type, actor=None, target=None, text="", confidence=0.9):
        self.event_type = event_type
        self.actor = actor
        self.target = target
        self.text = text
        self.confidence = confidence

    def to_dict(self):
        return {
            "event": self.event_type,
            "actor": self.actor,
            "target": self.target,
            "text": self.text,
            "confidence": self.confidence
        }

def analyze_structured_events(text: str) -> list:
    """
    Foundation v2 logic: Extracts structured (Actor -> Action -> Target) events.
    """
    state_facts = extract_state_from_text(text)
    clean_text = text.replace("ـ", " ")
    events = []
    
    # Improvements (v6.1 - v7.1): Aggressive NER Noise Reduction
    SKIP_WORDS = [
        "النار", "على", "بـ", "الرصاص", "بالقتل", "بالضرب", "قام", 
        "مما", "أدى", "الى", "في", "الحال", "عليه", "بموت", "بإصابة", "بسبب",
        "مما أدى", "أدى لوفاته", "في الحال", "لوفاته", "وفاته", "أطلق", "اطلق",
        "بقتل", "قتل", "بضرب", "ضرب", "فيقتل", "فقتل"
    ]
    for sw in SKIP_WORDS:
        # Complete word replacement with spacing
        clean_text = re.sub(rf"\b{sw}\b", " ", clean_text)

    # Refined Arabic Name Extractor
    name_patterns = [
        r"(?:المتهم|المجني عليه)(?:\s+[\d\u0621-\u064A]+)?\s+([\u0621-\u064A]+\s+[\u0621-\u064A]+(?:\s+[\u0621-\u064A]+)?)",
        r"(?:السيد|المدعو|الاستاذ)\s+([\u0621-\u064A]+\s+[\u0621-\u064A]+)"
    ]
    
    # 1. Extraction (Order-independent)
    actor = None
    target = None
    
    def extract_full_name(role_key_index, text_segment):
        # role_key_index is the index in name_patterns
        match = re.search(name_patterns[role_key_index], text_segment)
        if match:
            # Skip noise words
            noise = ["الأول", "الثاني", "الثالث", "المتهم", "المجني", "عليه", "المدعو", "المدعى"]
            parts = match.group(1).split() # Get the captured name group
            filtered = [p for p in parts if p not in noise]
            if filtered:
                return " ".join(filtered[:2])
        return None

    # 2. Resolve Primary Actors
    actor_name = extract_full_name(0, clean_text)
    if not actor_name:
        if "المتهم" in clean_text: actor_name = "المتهم"
        elif "الجاني" in clean_text: actor_name = "المتهم"
    
    target_name = extract_full_name(0, clean_text)
    if not target_name:
        if "المجني عليه" in clean_text: target_name = "المجني عليه"
        elif "القتيل" in clean_text: target_name = "المجني عليه"
    
    # Check if 'المجني عليه' or specific victim name is associated with aggressive actions
    victim_is_aggressor = re.search(r"المجني عليه.*(هجم|دفع|ضرب|هدد|حاول|بدأ|صوب|سحب|طعن)", clean_text) or \
                          re.search(r"(هجم|دفع|ضرب|هدد|حاول|بدأ|صوب|طعن).*المجني عليه", clean_text)
    
    # 3. Save Events
    actor = actor_name or "المتهم"
    target = target_name or "المجني عليه"
    
    # Check if 'المتهم' or specific defendant name is associated with aggressive actions
    defendant_is_aggressor = re.search(r"المتهم.*(قتل|طعن|ضرب|أطلق|دافع|رد|أصاب)", clean_text) or \
                             re.search(r"(قتل|طعن|ضرب|أطلق|دافع|رد|أصاب).*المتهم", clean_text)

    if victim_is_aggressor:
        actor = target_name or "المجني عليه"
        target = actor_name or "المتهم"
    elif defendant_is_aggressor:
        actor = actor_name or "المتهم"
        target = target_name or "المجني عليه"
    
    # Priority 2: Keyword presence in state
    if not actor:
        if any(f in state_facts for f in ["imminent_danger", "by_force"]):
            actor = target_name or "المجني عليه"
        elif any(f in state_facts for f in ["murder", "assault"]):
            actor = actor_name or "المتهم"
    
    # Defaults
    if not actor: actor = "المتهم"
    if not target: target = "المجني عليه" if actor == "المتهم" else "المتهم"

    for fact, val in state_facts.items():
        if fact.startswith("_") or not get_fact_value(val): continue
    # 4. Generate Final Structured Event
    main_event = StructuredEvent(
        event_type=list(state_facts.keys())[0] if state_facts else "unknown",
        actor=actor,
        target=target,
        text=text,
        confidence=0.95
    )
    events.append(main_event.to_dict())

    # 5. Injection of Procedural System Events (v6.2.2)
    # This ensures procedural findings like 'no_warrant' reach the DB and recompute_case_state
    if state_facts.get("procedural_error", {}).get("value"):
        events.append(StructuredEvent(
            event_type="procedural_error",
            actor="SYSTEM",
            target="CASE",
            text="بطلان إجرائي مرصود لغوياً",
            confidence=0.99
        ).to_dict())
    
    if state_facts.get("no_warrant", {}).get("value"):
        events.append(StructuredEvent(
            event_type="no_warrant",
            actor="SYSTEM",
            target="SEARCH",
            text="تفتيش بدون إذن نيابة",
            confidence=0.99
        ).to_dict())

    return events

def apply_rules_to_state(state: dict, conn, all_rules: list, debug=False) -> dict:
    cursor = conn.cursor()
    all_matched = {"procedure": [], "override": [], "normal": []}
    for r_name, r_logic, r_art_id in all_rules:
        rtype = r_logic.get("type", "normal")
        if state.get("_civil_only") and rtype == "normal" and r_logic.get("domain") == "criminal": continue
        
        match = True
        for c in r_logic.get("conditions", []):
            fkey = c.get("fact") or c.get("facct")
            if get_fact_value(state.get(fkey)) != c.get("value"):
                match = False
                break
        
        if match:
            cursor.execute("SELECT article_number FROM articles WHERE id=%s;", (r_art_id,))
            row = cursor.fetchone()
            
            # DEEP CLONE logic to prevent cross-scenario/shared-rule contamination 
            final_rule = copy.deepcopy(r_logic)
            
            # Injection: Ensure metadata exists at the root for the Conflict Resolver
            final_rule["name"] = r_name
            final_rule["priority"] = final_rule.get("priority", 0)
            final_rule["category"] = final_rule.get("category", "unclassified")
            final_rule["overrides"] = final_rule.get("overrides", [])
            
            # Outcome Alignment: Inject resolved article_number directly into produces
            if "produces" not in final_rule:
                final_rule["produces"] = final_rule.get("outcomes", {}) # legacy fallback
            
            final_rule["produces"]["article_number"] = row[0] if row else final_rule["produces"].get("article_number", "?")
            
            all_matched.setdefault(rtype, []).append(final_rule)
            if debug: print(f"    ✅ Rule Matched: {r_name}")

    cursor.close()
    return engine_execute(all_matched) if any(all_matched.values()) else None

def evaluate_scenario(scenario, res, base, global_ctx):
    if not res or not res.get("final_verdict"): return -1.0, 0.0, []
    penalty, reasons = 0.0, []
    truth = global_ctx.get("truth_ledger", {})
    if truth.get("is_victim_dead") and get_fact_value(scenario.get("self_defense")):
        penalty += 0.8; reasons.append("تعارض منطقي جسيم")
    
    conf = [v.get("confidence", 0.0) for v in scenario.values() if isinstance(v,dict) and v.get("value")]
    avg_conf = sum(conf)/len(conf) if conf else 0.0
    score = (avg_conf * 0.5) + (res.get("confidence", 0.9)*0.1) - penalty
    return score, penalty, reasons

def _analyze_single_event(event, conn, rules, log, global_ctx, debug=False):
    state = extract_state_from_text(event["text"])
    if event.get("inherits_threat"): state["imminent_danger"] = {"value": True, "confidence": 0.8}
    if get_fact_value(state.get("self_defense")): state["imminent_danger"] = {"value": True, "confidence": 0.9}

    scenarios = generate_scenarios(state)
    best_s, best_res, best_scen, best_reasons = -1.0, None, {}, []
    for s in scenarios:
        res = apply_rules_to_state(s, conn, rules, debug=debug)
        score, pen, reas = evaluate_scenario(s, res, state, global_ctx)
        if score > best_s: best_s, best_res, best_scen, best_reasons = score, res, s, reas

    if best_s < 0.1:
        return {"event_id": event["id"], "text": event["text"], "verdict": "تحليل أولي", "score": best_s, "active_facts": get_active_facts_summary(state), "applied_type": "contradiction"}

    fv = best_res["final_verdict"]
    txt = JUDICIAL_TEMPLATES["accept_murder"]
    if "self_defense" in best_scen and best_res.get("type") == "normal": txt += " " + JUDICIAL_TEMPLATES["reject_self_defense"]

    return {
        "event_id": event["id"], "text": event["text"], "verdict": fv.get("verdict"),
        "score": best_s, "active_facts": get_active_facts_summary(best_scen), "judicial_judgment": txt,
        "applied_type": best_res.get("applied_type", "normal"), "start_index": event.get("start_index", 0)
    }

def analyze_events(text, debug=False):
    events = split_into_events(text)
    conn = psycopg2.connect(**DB_PARAMS); cursor = conn.cursor()
    cursor.execute("SELECT rule_name, logic, article_id FROM rules;"); rules = cursor.fetchall(); cursor.close()
    res = []; ctx = {"threat_history": False, "truth_ledger": {"is_victim_dead": False}}
    for e in events:
        r = _analyze_single_event(e, conn, rules, None, ctx, debug=debug)
        res.append(r)
        if "murder" in r.get("active_facts", {}): ctx["truth_ledger"]["is_victim_dead"] = True
    conn.close()
    return {"events": res, "total_events": len(res), "final_summary": " | ".join(set(e["verdict"] for e in res if e.get("verdict")))}

def analyze_case(text, debug=False):
    if len(text.split()) >= 150:
        from pipeline_v4 import execute_pipeline_v4
        res = execute_pipeline_v4(text, debug=debug)
        return {"verdict": res["final_summary"], "active_facts": {}, "total_events": res["total_events"], "all_verdicts": res.get("all_verdicts", []), "judicial_judgment": res.get("judicial_judgment", ""), "v4_active": True}
    res = analyze_events(text, debug=debug)
    return {"verdict": res["final_summary"], "active_facts": {}, "total_events": res["total_events"], "all_verdicts": [], "judicial_judgment": "", "v4_active": False}
