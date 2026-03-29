import psycopg2
import json
import uuid

DB_PARAMS = {
    'dbname': 'counselor', 'user': 'postgres',
    'password': 'postgres', 'host': 'localhost', 'port': '5433'
}

def seed_golden_rules_final():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("TRUNCATE rules CASCADE")

    articles = [
        {"num": "230", "law": "قانون العقوبات",  "title": "القتل مع سبق الإصرار",    "text": "بالإعدام."},
        {"num": "234", "law": "قانون العقوبات",  "title": "القتل العمد البسيط",       "text": "بالسجن المؤبد."},
        {"num": "236", "law": "قانون العقوبات",  "title": "الضرب المفضي إلى موت",    "text": "بالسجن المشدد."},
        {"num": "241", "law": "قانون العقوبات",  "title": "الضرب المغلظ",             "text": "بالسجن."},
        {"num": "242", "law": "قانون العقوبات",  "title": "الضرب البسيط",             "text": "بالحبس أو الغرامة."},
        {"num": "245", "law": "قانون العقوبات",  "title": "الدفاع الشرعي",            "text": "لا عقاب."},
        {"num": "252", "law": "قانون العقوبات",  "title": "الحريق العمد",             "text": "بالسجن المؤبد."},
        {"num": "290", "law": "قانون العقوبات",  "title": "الخطف",                    "text": "بالسجن المؤبد."},
        {"num": "317", "law": "قانون العقوبات",  "title": "السرقة المشددة",           "text": "بالسجن."},
        {"num": "318", "law": "قانون العقوبات",  "title": "السرقة البسيطة",           "text": "بالحبس."},
        {"num": "211", "law": "قانون العقوبات",  "title": "تزوير رسمي",               "text": "بالسجن المؤبد."},
        {"num": "62",  "law": "قانون العقوبات",  "title": "حالة الضرورة",             "text": "لا عقاب."},
        {"num": "163", "law": "القانون المدني",  "title": "التعويض",                  "text": "يلزم بالتعويض."},
        {"num": "157", "law": "القانون المدني",  "title": "الفسخ",                    "text": "يجوز الفسخ."},
        {"num": "15",  "law": "قانون الإجراءات", "title": "التقادم",                  "text": "تنقضي الدعوى."},
        {"num": "331", "law": "قانون الإجراءات", "title": "البطلان",                  "text": "يترتب البطلان."},
        {"num": "25",  "law": "قانون الأسلحة والذخائر", "title": "حيازة سلاح",         "text": "بالسجن."}
    ]

    am = {}  # article_mapping: num → db_id
    for a in articles:
        full = f"{a['law']} - {a['title']}"
        cur.execute("SELECT id FROM articles WHERE article_number=%s AND title=%s", (a["num"], full))
        row = cur.fetchone()
        if not row:
            uid = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO articles (id, article_number, title, plain_text, domain) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                (uid, a["num"], full, a["text"], "civil" if "مدني" in a["law"] else "criminal")
            )
            am[a["num"]] = cur.fetchone()[0]
        else:
            am[a["num"]] = row[0]

    rules = [

        # ══════════════════════════════════════════════════
        # PROCEDURE PACK  (checked first — final=True stops engine)
        # ══════════════════════════════════════════════════
        {"name": "التقادم", "art": "15", "logic": {
            "type": "procedure", "final": True, "priority": 120,
            "domain": "procedural", "law_type": "procedure_code",
            "rule_type": "expiration", "pack": "procedure_pack_v1",
            "category": "procedural_bar",
            "overrides": [],
            "conditions": [{"fact": "expiration", "value": True}],
            "produces": {"verdict": "انقضاء الدعوى الجنائية بمضي المدة",
                         "article_number": "15", "law": "قانون الإجراءات", "confidence": 0.99}}},

        {"name": "بطلان التفتيش", "art": "331", "logic": {
            "type": "procedure", "final": True, "priority": 115,
            "domain": "procedural", "law_type": "procedure_code",
            "rule_type": "nullity", "pack": "procedure_pack_v1",
            "category": "procedural_bar",
            "overrides": [],
            "conditions": [{"fact": "nullity_procedural", "value": True}],
            "produces": {"verdict": "باطل - لعدم مراعاة أحكام القانون",
                         "article_number": "331", "law": "قانون الإجراءات", "confidence": 0.98}}},

        # ══════════════════════════════════════════════════
        # OVERRIDE PACK  (checked second — highest priority wins)
        # ══════════════════════════════════════════════════
        {"name": "الدفاع الشرعي", "art": "245", "logic": {
            "type": "override", "final": False, "priority": 110,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "self_defense", "pack": "criminal_pack_v1",
            "category": "defense",
            "overrides": ["*"],   # Global — disables ALL normal/exception rules
            "conditions": [{"fact": "self_defense", "value": True},
                           {"fact": "imminent_danger", "value": True},
                           {"fact": "temporal_gap", "value": False}],
            "produces": {"verdict": "البراءة - فعل مباح بالدفاع الشرعي",
                         "article_number": "245", "law": "قانون العقوبات", "confidence": 0.98}}},

        {"name": "حالة الضرورة", "art": "62", "logic": {
            "type": "override", "final": False, "priority": 108,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "necessity", "pack": "criminal_pack_v1",
            "category": "defense",
            "overrides": ["category:violent_crimes", "category:property_crimes"],
            "conditions": [{"fact": "necessity", "value": True}],
            "produces": {"verdict": "البراءة - حالة ضرورة قانونية",
                         "article_number": "62", "law": "قانون العقوبات", "confidence": 0.95}}},

        # ══════════════════════════════════════════════════
        # CRIMINAL PACK — NORMAL rules
        # ══════════════════════════════════════════════════
        {"name": "القتل مع سبق الإصرار", "art": "230", "logic": {
            "type": "normal", "priority": 99,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "homicide", "pack": "criminal_pack_v1",
            "category": "violent_crimes",
            "overrides": [],
            "conditions": [{"fact": "murder", "value": True},
                           {"fact": "premeditation", "value": True}],
            "produces": {"verdict": "الإعدام شنقاً",
                         "article_number": "230", "law": "قانون العقوبات", "confidence": 0.99}}},

        {"name": "القتل العمد", "art": "234", "logic": {
            "type": "normal", "priority": 98,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "homicide", "pack": "criminal_pack_v1",
            "category": "violent_crimes",
            "overrides": [],
            "conditions": [{"fact": "murder", "value": True},
                           {"fact": "intent", "value": True}],
            "produces": {"verdict": "الإعدام",
                         "article_number": "234", "law": "قانون العقوبات", "confidence": 0.99}}},

        {"name": "الشروع في القتل", "art": "234", "logic": {
            "type": "normal", "priority": 97,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "homicide", "pack": "criminal_pack_v1",
            "category": "violent_crimes",
            "overrides": [],
            "conditions": [{"fact": "murder", "value": True},
                           {"fact": "attempted", "value": True}],
            "produces": {"verdict": "السجن المشدد",
                         "article_number": "234", "law": "قانون العقوبات", "confidence": 0.95}}},

        {"name": "الضرب المفضي لموت", "art": "236", "logic": {
            "type": "normal", "priority": 97,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "homicide", "pack": "criminal_pack_v1",
            "category": "violent_crimes",
            "overrides": [],
            "conditions": [{"fact": "murder", "value": True},
                           {"fact": "negligence", "value": True}],
            "produces": {"verdict": "السجن المؤبد",
                         "article_number": "236", "law": "قانون العقوبات", "confidence": 0.97}}},

        {"name": "تزوير موظف", "art": "211", "logic": {
            "type": "normal", "priority": 95,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "forgery", "pack": "criminal_pack_v1",
            "category": "forgery_crimes",
            "overrides": [],
            "conditions": [{"fact": "forgery", "value": True},
                           {"fact": "public_official", "value": True}],
            "produces": {"verdict": "السجن المؤبد",
                         "article_number": "211", "law": "قانون العقوبات", "confidence": 0.97}}},

        {"name": "خطف قاصر", "art": "290", "logic": {
            "type": "normal", "priority": 95,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "kidnapping", "pack": "criminal_pack_v1",
            "category": "kidnapping_crimes",
            "overrides": [],
            "conditions": [{"fact": "kidnapping", "value": True},
                           {"fact": "minor_victim", "value": True}],
            "produces": {"verdict": "سجن",
                         "article_number": "290", "law": "قانون العقوبات", "confidence": 0.97}}},

        {"name": "حريق عمد", "art": "252", "logic": {
            "type": "normal", "priority": 95,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "arson", "pack": "criminal_pack_v1",
            "category": "arson_crimes",
            "overrides": [],
            "conditions": [{"fact": "arson", "value": True}],
            "produces": {"verdict": "سجن",
                         "article_number": "252", "law": "قانون العقوبات", "confidence": 0.95}}},

        {"name": "السرقة بالإكراه", "art": "317", "logic": {
            "type": "normal", "priority": 91,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "theft", "pack": "criminal_pack_v1",
            "category": "property_crimes",
            "overrides": [],
            "conditions": [{"fact": "theft", "value": True}, {"fact": "by_force", "value": True}],
            "produces": {"verdict": "السجن المؤبد",
                         "article_number": "317", "law": "قانون العقوبات", "confidence": 0.98}}},

        {"name": "السرقة المشددة", "art": "317", "logic": {
            "type": "normal", "priority": 90,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "theft", "pack": "criminal_pack_v1",
            "category": "property_crimes",
            "overrides": [],
            "conditions": [{"fact": "theft", "value": True},
                           {"fact": "group", "value": True}],
            "produces": {"verdict": "السجن المؤبد",
                         "article_number": "317", "law": "قانون العقوبات", "confidence": 0.97}}},

        {"name": "السرقة ليلاً", "art": "317", "logic": {
            "type": "normal", "priority": 89,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "theft", "pack": "criminal_pack_v1",
            "category": "property_crimes",
            "overrides": [],
            "conditions": [{"fact": "theft", "value": True},
                           {"fact": "from_residence", "value": True}],
            "produces": {"verdict": "سجن",
                         "article_number": "317", "law": "قانون العقوبات", "confidence": 0.95}}},

        {"name": "الضرب بآلة حادة", "art": "241", "logic": {
            "type": "normal", "priority": 85,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "assault", "pack": "criminal_pack_v1",
            "category": "assault_crimes",
            "overrides": [],
            "conditions": [{"fact": "assault", "value": True},
                           {"fact": "weapon_used", "value": True}],
            "produces": {"verdict": "سجن",
                         "article_number": "241", "law": "قانون العقوبات", "confidence": 0.93}}},

        {"name": "عاهة مستديمة", "art": "241", "logic": {
            "type": "normal", "priority": 84,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "assault", "pack": "criminal_pack_v1",
            "category": "assault_crimes",
            "overrides": [],
            "conditions": [{"fact": "assault", "value": True},
                           {"fact": "permanent_disability", "value": True}],
            "produces": {"verdict": "سجن",
                         "article_number": "241", "law": "قانون العقوبات", "confidence": 0.93}}},

        {"name": "حيازة سلاح بدون ترخيص", "art": "25", "logic": {
            "type": "normal", "priority": 83,
            "domain": "criminal", "law_type": "weapons_law",
            "rule_type": "weapon_possession", "pack": "criminal_pack_v1",
            "category": "weapon_crimes",
            "overrides": [],
            "conditions": [{"fact": "weapon_used", "value": True}],
            "produces": {"verdict": "سجن",
                         "article_number": "25", "law": "قانون الأسلحة والذخائر", "confidence": 0.95}}},


        # ══════════════════════════════════════════════════
        # CIVIL PACK — NORMAL rules
        # ══════════════════════════════════════════════════
        {"name": "فسخ العقد", "art": "157", "logic": {
            "type": "normal", "priority": 82,
            "domain": "civil", "law_type": "civil_code",
            "rule_type": "contract_nullity", "pack": "civil_pack_v1",
            "category": "civil_contract",
            "overrides": [],
            "conditions": [{"fact": "contract", "value": True},
                           {"fact": "nullity", "value": True}],
            "produces": {"verdict": "فسخ العقد وإعادة الحال لما كان عليه",
                         "article_number": "157", "law": "القانون المدني", "confidence": 0.95}}},

        {"name": "التعويض الجابر", "art": "163", "logic": {
            "type": "normal", "priority": 81,
            "domain": "civil", "law_type": "civil_code",
            "rule_type": "civil_liability", "pack": "civil_pack_v1",
            "category": "civil_liability",
            "overrides": [],
            "conditions": [{"fact": "reparation", "value": True}],
            "produces": {"verdict": "إلزام المتسبب بالتعويض الجابر للضرر",
                         "article_number": "163", "law": "القانون المدني", "confidence": 0.93}}},

        {"name": "التعويض المدني", "art": "163", "logic": {
            "type": "normal", "priority": 80,
            "domain": "civil", "law_type": "civil_code",
            "rule_type": "civil_liability", "pack": "civil_pack_v1",
            "category": "civil_liability",
            "overrides": [],
            "conditions": [{"fact": "civil_fault", "value": True},
                           {"fact": "injury", "value": True}],
            "produces": {"verdict": "إلزام المتسبب بالتعويض الجابر للضرر",
                         "article_number": "163", "law": "القانون المدني", "confidence": 0.93}}},

        {"name": "سرقة بسيطة", "art": "318", "logic": {
            "type": "normal", "priority": 70,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "theft", "pack": "criminal_pack_v1",
            "category": "property_crimes",
            "overrides": [],
            "conditions": [{"fact": "theft", "value": True}],
            "produces": {"verdict": "حبس",
                         "article_number": "318", "law": "قانون العقوبات", "confidence": 0.9}}},

        {"name": "ضرب بسيط", "art": "242", "logic": {
            "type": "normal", "priority": 60,
            "domain": "criminal", "law_type": "penal_code",
            "rule_type": "assault", "pack": "criminal_pack_v1",
            "category": "assault_crimes",
            "overrides": [],
            "conditions": [{"fact": "assault", "value": True}],
            "produces": {"verdict": "حبس أو غرامة",
                         "article_number": "242", "law": "قانون العقوبات", "confidence": 0.85}}},
    ]

    for r in rules:
        cur.execute(
            "INSERT INTO rules (article_id, rule_name, logic) VALUES (%s, %s, %s)",
            (am[r["art"]], r["name"], json.dumps(r["logic"]))
        )

    conn.commit()
    print(f"Seeded {len(rules)} rules.")
    cur.close(); conn.close()

if __name__ == "__main__":
    seed_golden_rules_final()
