"""
Auto Rule Extractor - قانون العقوبات المصري
يقرأ مواد قانون العقوبات من DB ويولّد قواعد تنفيذية تلقائياً
"""
import psycopg2
import json
import re

DB_PARAMS = {
    "dbname": "counselor",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5433"
}

CRIME_PATTERNS = [
    # القتل والإيذاء
    ("murder",       r"قتل|القتل|أزهق|أودى بحياة|أردى|الضرب المفضي إلى الموت"),
    ("assault",      r"جرح|جرحاً|ضرب|اعتدى|أيذاء|إيذاء|عاهة|عجز|إصابة"),
    # السرقة والنهب
    ("theft",        r"سرق|سرقة|نشل|اختلس|استولى على"),
    ("robbery",      r"نهب|نهبا|اغتصب المال|أخذ بالقوة"),
    # الاحتيال والتزوير
    ("fraud",        r"احتيال|نصب|تدليس|خدع|غش|دلّس"),
    ("forgery",      r"تزوير|زوّر|أتلف محرراً|زور محرراً|زور توقيعاً"),
    # الجرائم الجنسية
    ("sexual_crime", r"هتك|اغتصب|وقاع|فحشاء|عرض"),
    # الحريق والتخريب
    ("arson",        r"حريق|أشعل|أضرم|حرق|إحراق"),
    ("vandalism",    r"أتلف|تخريب|هدم|أفسد|قطع|اقتلع|تلف"),
    # الجرائم الاقتصادية
    ("bribery",      r"رشوة|ارتشى|رشا|قبل عطية|طلب رشوة"),
    ("embezzlement", r"اختلس|خيانة أمانة|استولى على مال عام"),
    # جرائم أخرى
    ("trespass",     r"دخل بيتاً|دخل مسكناً|دخل أرضاً|دخل مبنى|تعدى على أرض"),
    ("defamation",   r"قذف|سب|إهانة|ذم|تحقير|إفشاء سر"),
    ("perjury",      r"شهادة زور|يمين كاذبة|شهد زوراً"),
    ("drug",         r"مخدرات|مؤثرات عقلية|حشيش|أفيون|هيروين"),
    ("weapon",       r"حيازة سلاح|إحراز سلاح|سلاح بغير ترخيص"),
    ("kidnapping",   r"خطف|اختطف|حجز|حرم من الحرية"),
    ("smuggling",    r"تهريب|تهريباً|أدخل خلسة"),
    # القانون المدني (Civil Law - Arabic)
    ("civil_fault",  r"كل خطأ|أحدث ضرراً|إخلال بالتزام|تقصير"),
    ("injury",       r"ضرر|أضرار|خسارة|تلفيات"),
    ("reparation",   r"تعويض|إصلاح|جبر الضرر|رد الشيء"),
    ("contract",     r"عقد|اتفاق|بنود|شريعة المتعاقدين"),
    ("nullity",      r"باطل|بطلان|قابلاً للإبطال|مخالف للنظام العام"),
    # Civil Law (English Patterns)
    ("obligation",   r"obligation|debtor|creditor|payment|restitution"),
    ("ownership",    r"owner|property|owns|possession|heir"),
    ("contract_en",  r"contract|agreement|void|revoked|consent"),
    ("liability_en", r"fault|injury|reparation|compensation|damage"),
    # الإجراءات الجنائية (Procedure)
    ("search",       r"تفتيش|فتش|دخول المساكن|ضبط الأشياء"),
    ("arrest",       r"قبض|حبس احتياطي|حرم من الحرية|إلزام بعدم مبارحة"),
    ("rights",       r"تظلم|حق في|إخطار|تبليغ|إذن"),
    ("expiration",   r"انقضاء|تقادم|بمضي المدة"),
]

# =============================================
# 2. كشاف العقوبات (Punishment Extractor)
# =============================================
PUNISHMENT_PATTERNS = [
    ("death_penalty",      r"بالإعدام|عقوبة الإعدام|يُحكم عليه بالإعدام"),
    ("life_imprisonment",  r"بالسجن المؤبد|السجن المؤبد"),
    ("aggravated_prison",  r"بالسجن المشدد|السجن المشدد"),
    ("imprisonment",       r"بالسجن(?! المؤبد| المشدد)|يعاقب بالسجن"),
    ("detention",          r"بالحبس(?!\s+مع)| بالحبس"),
    ("detention_work",     r"بالحبس مع الشغل|الحبس مع الشغل"),
    ("fine",               r"بغرامة|وغرامة|الغرامة"),
]

# =============================================
# 3. كشاف الظروف (Circumstance Extractor)
# =============================================
def extract_circumstances(text):
    """يكشف الظروف المشددة والمخففة من نص المادة"""
    facts = {}

    # ظروف مشددة
    if re.search(r"بالقوة|بالإكراه|بالتهديد|قسراً", text): facts["by_force"] = True
    if re.search(r"بالسلاح|مسلح|أداة|آلة حادة", text): facts["with_weapon"] = True
    if re.search(r"ليلاً|الليل", text): facts["at_night"] = True
    if re.search(r"جماعة|عصابة|أكثر من شخص|متعدد", text): facts["group"] = True
    if re.search(r"موظف عام|مأمور|وظيفته|بحكم وظيفته", text): facts["public_official"] = True
    if re.search(r"أصل|فرع|زوج|محرم|قريب", text): facts["family_relation"] = True
    if re.search(r"عود|معاود|سبق الحكم", text): facts["recidivism"] = True
    if re.search(r"قاصر|طفل|أقل من|لم يبلغ", text): facts["minor_victim"] = True
    if re.search(r"مخدر|سكران|حالة سكر", text): facts["under_influence"] = True

    # ظروف مخففة / موانع
    if re.search(r"دفاع شرعي|دفع اعتداء|اتقاء خطر", text): facts["self_defense"] = True
    if re.search(r"عذر مخفف|بداعي الشرف|ثورة الغضب", text): facts["mitigating"] = True
    if re.search(r"غير عمد|خطأ|إهمال|رعونة", text): facts["negligence"] = True
    if re.search(r"عمد|قصد|تعمد|عن سبق إصرار", text): facts["intent"] = True

    return facts

# =============================================
# 4. استخراج منطوق الحكم
# =============================================
def extract_punishment(text):
    """يكشف أعلى عقوبة مذكورة في المادة"""
    for p_type, pattern in PUNISHMENT_PATTERNS:
        if re.search(pattern, text):
            return p_type
    return None

PUNISHMENT_VERDICTS = {
    "death_penalty":     ("الإعدام", 10),
    "life_imprisonment": ("السجن المؤبد", 9),
    "aggravated_prison": ("السجن المشدد", 8),
    "imprisonment":      ("السجن", 7),
    "detention_work":    ("الحبس مع الشغل", 6),
    "detention":         ("الحبس", 5),
    "fine":              ("الغرامة", 4),
}

CIVIL_OUTCOMES = [
    ("reparation", r"التعويض|إصلاح الضرر", "التعويض المادي"),
    ("nullity", r"بطلان|باطل", "البطلان المطلق"),
    ("termination", r"فسخ|انحلال", "فسخ العقد"),
]

PROCEDURAL_OUTCOMES = [
    ("dismissal", r"انقضاء|تقادم|dismissal|expired", "انقضاء الدعوى"),
    ("nullity", r"بطلان|void|null", "بطلان الإجراء"),
]

CIVIL_EN_OUTCOMES = [
    ("reparation", r"compensation|reparation|indemnity", "التعويض للمدني"),
    ("nullity", r"void|null|rescinded", "فسخ العقد / البطلان"),
    ("ownership", r"ownership|title", "تثبيت الملكية"),
]

# =============================================
# 5. Pipeline الرئيسي
# =============================================
def extract_and_seed_rules():
    print("🔌 Connecting to DB...")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    # جلب المواد من كافة المجالات (فوق 30 حرف = ليست عناوين)
    cur.execute("""
        SELECT id, article_number, plain_text, domain
        FROM articles
        WHERE LENGTH(plain_text) > 80
        ORDER BY 
            domain DESC,
            CASE WHEN article_number ~ '^[0-9]+$' 
            THEN article_number::int ELSE 9999 END
    """)
    articles = cur.fetchall()
    print(f"📚 Found {len(articles)} legal articles total.\n")

    # جلب القواعد اليدوية الحالية للمحافظة عليها
    cur.execute("SELECT rule_name FROM rules;")
    existing_rules = {r[0] for r in cur.fetchall()}

    rules_added = 0
    rules_skipped = 0
    rules_no_match = 0

    for art_id, art_num, text, domain in articles:

        # 1. اكتشف الوقائع/الجرائم
        detected_facts = []
        for fact_type, pattern in CRIME_PATTERNS:
            if re.search(pattern, text, re.I):
                detected_facts.append(fact_type)

        if not detected_facts:
            rules_no_match += 1
            continue

        # 2. تحديد النطاق والنتائج
        verdict_text = None
        punishment_type = None
        base_priority = 5

        # تحليل معمق للقتل (Murder Deep Analysis)
        if "murder" in detected_facts:
            if re.search(r"مع سبق الإصرار|الترصد|عن قصد|عمد|premeditated|intent", text, re.I):
                verdict_text = "الإعدام شنقاً"
                punishment_type = "death_penalty"
                base_priority = 10
            else:
                verdict_text = "السجن المؤبد"
                punishment_type = "life_imprisonment"
                base_priority = 9

        if domain == 'criminal':
            punishment_type = extract_punishment(text)
            if punishment_type:
                verdict_text, base_priority = PUNISHMENT_VERDICTS[punishment_type]
        elif domain == 'civil_law':
            # Check Arabic outcomes
            for out_id, pattern, v_text in CIVIL_OUTCOMES:
                if re.search(pattern, text, re.I):
                    verdict_text = v_text
                    punishment_type = out_id
                    base_priority = 6
                    break
            # Check English outcomes if Arabic failed
            if not verdict_text:
                for out_id, pattern, v_text in CIVIL_EN_OUTCOMES:
                    if re.search(pattern, text, re.I):
                        verdict_text = v_text
                        punishment_type = out_id
                        base_priority = 6
                        break
        elif domain == 'criminal_procedure':
            for out_id, pattern, v_text in PROCEDURAL_OUTCOMES:
                if re.search(pattern, text):
                    verdict_text = v_text
                    punishment_type = out_id
                    base_priority = 8
                    break

        if not verdict_text:
            rules_no_match += 1
            continue

        # 3. اكتشف الظروف
        circumstances = extract_circumstances(text)

        # 4. بناء شروط القاعدة
        for primary_fact in detected_facts:
            conditions = [{"fact": primary_fact, "value": True}]

            circum_suffix = []
            for circum, val in circumstances.items():
                if val and circum != "negligence":
                    conditions.append({"fact": circum, "value": True})
                    circum_suffix.append(circum)

            # اسم فريد للقاعدة
            suffix = " + ".join(circum_suffix[:2]) if circum_suffix else "عام"
            rule_name = f"{primary_fact} [{art_num}] - {suffix}"

            if rule_name in existing_rules:
                rules_skipped += 1
                continue

            # بيانات القاعدة
            logic = {
                "domain": domain,
                "priority": min(10, base_priority + len(circum_suffix)),
                "confidence": 0.8 if domain != 'criminal' else 0.85,
                "conditions": conditions,
                "outcomes": {
                    "verdict": verdict_text,
                    "article_number": art_num,
                    "law": "القانون المدني" if domain == 'civil_law' else ("إجراءات جنائية" if domain == 'criminal_procedure' else "قانون العقوبات"),
                    "punishment_type": punishment_type
                }
            }

            cur.execute("""
                INSERT INTO rules (article_id, rule_name, logic)
                VALUES (%s, %s, %s)
            """, (art_id, rule_name, json.dumps(logic, ensure_ascii=False)))

            existing_rules.add(rule_name)
            rules_added += 1

            if rules_added % 100 == 0:
                print(f"   ⚙️  {rules_added} rules added so far...")

    conn.commit()

    # إحصاء نهائي
    cur.execute("SELECT COUNT(*) FROM rules;")
    total = cur.fetchone()[0]

    print(f"\n{'='*50}")
    print(f"✅ Auto-Extraction Complete!")
    print(f"   Rules Added:    {rules_added}")
    print(f"   Skipped (dup):  {rules_skipped}")
    print(f"   No Match:       {rules_no_match}")
    print(f"   Total in DB:    {total}")
    print(f"{'='*50}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    extract_and_seed_rules()
