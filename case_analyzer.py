import psycopg2
import re
import json
from conflict_resolver import execute as engine_execute, resolve_conflicts
from fact_system import make_true, make_false, get_fact_value, get_active_facts_summary, get_confidence_weighted_facts
from inference_logger import InferenceLog

DB_PARAMS = {
    "dbname": "counselor",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5433"
}

# =============================================
# Rendering Helpers
# =============================================
def to_arabic_numerals(n):
    return str(n).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))

def format_reference(article_number, law):
    return f"(المادة {to_arabic_numerals(article_number)} - {law})"

# =============================================
# NLP: Eternal Glory Extraction (v17)
# =============================================
def extract_state_from_text(case_text):
    state = {}
    
    # Deep Normalization
    clean_text = case_text.replace("ـ", " ")
    clean_text = re.sub(r"[أإآ]", "ا", clean_text)
    clean_text = re.sub(r"\s+", " ", clean_text)
    
    # Helper: detect negation before setting intent
    negated_intent = bool(re.search(r"دون قصد|بغير قصد|بلا قصد|غير عمد|دون عمد|لم يقصد|لم يتعمد|without intent", clean_text, re.I))

    # 1. Intent & Circumstances (with confidence scores)
    if not negated_intent and re.search(r"عمد|قصد|قاصد|بنية|تعمد|أزهق|ازهق|أقدم على|اقدم على", clean_text, re.I):
        state["intent"] = make_true(0.9)
    if re.search(r"سبق اصرار|ترصد|خطط|دبر|premeditation", clean_text, re.I): 
        state["premeditation"] = make_true(0.95)
        state["intent"] = make_true(0.95)

    if re.search(r"اهمال|رعونة|غير عمد|خطا|دون قصد|negligence", clean_text, re.I): state["negligence"] = make_true(0.9)
    if re.search(r"دفاع شرعي|دافع عن نفسه|self defense", clean_text, re.I): state["self_defense"] = make_true(0.95)
    if re.search(r"خطر|هجم|سيقتل|يقتل|يهدد|داهم|مهاجم|سكين", clean_text, re.I): state["imminent_danger"] = make_true(0.9)

    if re.search(r"كره|قوة|غصب|تهديد|force", clean_text, re.I): state["by_force"] = make_true(0.85)
    if re.search(r"ليلا|ليل|night", clean_text, re.I): state["at_night"] = make_true(0.95)
    if re.search(r"عصابة|جماعة|اشخاص|متعدد|group", clean_text, re.I): state["group"] = make_true(0.9)
    if re.search(r"حدث|أقل من 18|قاصر|طفل|صغير|juvenile|minor", clean_text, re.I):
        state["juvenile_offender"] = make_true(0.95)
        state["minor_victim"] = make_true(0.95)

    # 2. Crimes
    if re.search(r"قتل|ازهق|حياة|بقتل|قتله|قتلته|جثة|murder|kill", clean_text, re.I): state["murder"] = make_true(0.95)
    if re.search(r"ضرب|جرح|اعتداء|ايذاء|اعتدى|hurt|assault", clean_text, re.I): state["assault"] = make_true(0.9)
    if re.search(r"سرق|اختلس|نهب|theft|rob|stolen", clean_text, re.I): state["theft"] = make_true(0.95)
    if re.search(r"تزوير|زور|forgery|forge", clean_text, re.I): state["forgery"] = make_true(0.95)
    if re.search(r"خطف|اختطاف|kidnap", clean_text, re.I): state["kidnapping"] = make_true(0.95)
    if re.search(r"حريق|اشعل|نار|أشعل|burned|fire|arson", clean_text, re.I): state["arson"] = make_true(0.9)
    if re.search(r"سلاح|مسدس|سكين|الة حادة|weapon|gun|knife", clean_text, re.I): state["weapon_used"] = make_true(0.9)
    if re.search(r"موظف عام|وظيفته|رسمي|public official", clean_text, re.I): state["public_official"] = make_true(0.9)

    if re.search(r"بليغة|جسيمة|شديدة|عاهة|severe|disability", clean_text, re.I):
        state["severe_injury"] = make_true(0.85)
        if re.search(r"عاهة", clean_text): state["permanent_disability"] = make_true(0.9)
    if re.search(r"مسكن|منزل|بيت|شقة|residence|house", clean_text, re.I): state["from_residence"] = make_true(0.9)

    # 3. Civil
    if re.search(r"اخطا|بخطئه|غلط|إهمال|اهمال|fault|negligence", clean_text, re.I): state["civil_fault"] = make_true(0.85)
    if re.search(r"ضرر|يضر|اضرار|اصابة|injury|damage|harm", clean_text, re.I): state["injury"] = make_true(0.85)
    if re.search(r"عقد|اتفاق|تعاقد|contract|agreement", clean_text, re.I): state["contract"] = make_true(0.9)
    if re.search(r"تعويض|يطالب|مطالبة|compensation|reparation", clean_text, re.I): state["reparation"] = make_true(0.9)

    # 4. Procedural
    if re.search(r"بطلان|باطل|بدون اذن|بغير اذن|دون اذن|بلا اذن|void|null|nullity", clean_text, re.I):
        if re.search(r"فسخ|عقد", clean_text): state["nullity"] = make_true(0.9)
        else: state["nullity_procedural"] = make_true(0.9)
    if re.search(r"فسخ|إنهاء عقد", clean_text, re.I): state["nullity"] = make_true(0.9)
    if re.search(r"تفتيش|فتش|ضبط|search|seizure", clean_text, re.I): state["search"] = make_true(0.9)
    if re.search(r"تقادم|انقض|مضي مدة|expiration|prescription", clean_text, re.I): state["expiration"] = make_true(0.95)
    if re.search(r"دليل|ادلة|وجدوا|ضبط|عثر|evidence", clean_text, re.I): state["evidence"] = make_true(0.8)
    if re.search(r"حالة ضرورة|ضرورة قصوى|إكراه|اكراه|اضطر|إضطرار|necessity|duress", clean_text, re.I): state["necessity"] = make_true(0.9)

    # Defaults (False for any unset key)
    all_keys = [
        "murder", "assault", "kidnapping", "theft", "forgery", "arson", "intent",
        "negligence", "self_defense", "imminent_danger", "by_force", "at_night",
        "group", "public_official", "minor_victim", "weapon_used", "severe_injury",
        "permanent_disability", "from_residence", "civil_fault", "injury", "contract",
        "reparation", "nullity", "nullity_procedural", "search", "expiration",
        "evidence", "necessity", "premeditation"
    ]
    for k in all_keys:
        if k not in state: state[k] = make_false()

    crim_triggers = ["murder", "assault", "kidnapping", "theft", "forgery", "arson", "nullity_procedural", "search", "expiration"]
    has_crime = any(get_fact_value(state.get(f)) for f in crim_triggers)
    state["_civil_only"] = not has_crime
    return state

def analyze_case(case_text: str, debug: bool = False) -> dict:
    state = extract_state_from_text(case_text)
    log = InferenceLog(case_text)
    active_facts = get_active_facts_summary(state)
    log.log_facts(active_facts)

    if not active_facts:
        return {"verdict": None, "active_facts": {}, "error": "لم يتم التعرف على وقائع."}

    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    cursor.execute("SELECT rule_name, logic, article_id FROM rules;")
    all_rules = cursor.fetchall()

    # Build grouped dict for the Universal Rule Engine
    all_matched: dict = {"procedure": [], "override": [], "exception": [], "normal": []}

    for rule_name, logic, article_id in all_rules:
        rule_type = logic.get("type", "normal")
        if rule_type == "substantive":
            rule_type = "normal"
        rule_domain = logic.get("domain", "")

        # civil_only filter: ONLY skip normal/exception criminal rules
        # procedure and override always run (they may exonerate regardless)
        if (state.get("_civil_only")
                and rule_type in ("normal", "exception")
                and rule_domain in ("criminal", "procedural")):
            continue

        priority = logic.get("priority", 0)
        rule_matched = all(
            get_fact_value(state.get(c["fact"])) == c["value"]
            for c in logic.get("conditions", [])
        )
        log.log_rule_evaluated(rule_name, rule_matched, rule_type, priority)

        if rule_matched:
            cursor.execute("SELECT article_number FROM articles WHERE id=%s;", (article_id,))
            art_row = cursor.fetchone()
            produces = logic.get("produces") or logic.get("outcomes") or {}
            rule_data = {
                "name":         rule_name,
                "rule":         rule_name,
                "type":         rule_type,
                "category":     logic.get("category", ""),
                "priority":     priority,
                "overrides":    logic.get("overrides", []),
                "final":        logic.get("final", False),
                "produces":     produces,
                # backward-compat aliases
                "verdict":      produces.get("verdict", ""),
                "article_number": produces.get("article_number",
                                               art_row[0] if art_row else "?"),
                "law":          produces.get("law", ""),
                "pack":         logic.get("pack", ""),
                "rule_type":    logic.get("rule_type", ""),
                "outcomes":     produces,
            }
            all_matched.setdefault(rule_type, []).append(rule_data)

    cursor.close(); conn.close()

    total = sum(len(v) for v in all_matched.values())
    if total == 0:
        return {"verdict": None, "active_facts": active_facts, "error": "لا توجد قواعد مطابقة."}

    conflict_res = engine_execute(all_matched)

    if conflict_res["has_conflict"] and conflict_res["final_verdict"]:
        produces = conflict_res["final_verdict"]
        top = {
            "verdict":        produces.get("verdict", ""),
            "article_number": conflict_res["article"],
            "law":            conflict_res["law"],
            "rule":           conflict_res["conflict_rule"]
        }
        log.log_override(conflict_res["conflict_rule"], True,
                         conflict_res.get("reason") or "")
        log.log_verdict(top["verdict"], top["article_number"] or "?", top["law"] or "")
    else:
        top = {"verdict": None, "article_number": "?", "law": "", "rule": "لا حكم"}
        log.log_verdict("", "?", "")

    result = {
        "verdict": top["verdict"],
        "references": [{
            "article_number": top.get("article_number", "?"),
            "law":            top.get("law", ""),
            "display":        format_reference(top.get("article_number", "?"), top.get("law", ""))
        }],
        "active_facts":     active_facts,
        "rule_applied":     top.get("rule"),
        "confidence_facts": get_confidence_weighted_facts(state),
        "inference_log":    log.to_dict(),
        "disabled_rules":   conflict_res.get("disabled_rules", []),
        "applied_type":     conflict_res.get("applied_type"),
    }
    if debug:
        print(log.render_human())
    return result

if __name__ == "__main__":
    analyze_case("قام المتهم بقتل الضحية عمدا")
