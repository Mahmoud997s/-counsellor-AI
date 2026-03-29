import psycopg2
import json
import uuid

DB_PARAMS = {
    'dbname': 'counselor',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5433'
}

def seed_golden_rules_final():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("TRUNCATE rules CASCADE")
    
    # Unified list of all articles used by the rules
    golden_articles = [
        {"num": "230", "law": "قانون العقوبات", "title": "القتل مع سبق الإصرار", "text": "بالإعدام."},
        {"num": "234", "law": "قانون العقوبات", "title": "القتل العمد البسيط", "text": "بالسجن المؤبد."},
        {"num": "236", "law": "قانون العقوبات", "title": "الضرب المفضي إلى موت", "text": "بالسجن المشدد."},
        {"num": "317", "law": "قانون العقوبات", "title": "السرقة المشددة", "text": "بالسجن."},
        {"num": "163", "law": "القانون المدني", "title": "التعويض", "text": "يلزم بالتعويض."},
        {"num": "157", "law": "القانون المدني", "title": "الفسخ", "text": "يجوز الفسخ."},
        {"num": "15", "law": "قانون الإجراءات", "title": "التقادم", "text": "تنقضي الدعوى."},
        {"num": "331", "law": "قانون الإجراءات", "title": "البطلان", "text": "يترتب البطلان."},
        {"num": "245", "law": "قانون العقوبات", "title": "الدفاع الشرعي", "text": "لا عقاب."},
        {"num": "241", "law": "قانون العقوبات", "title": "الضرب المغلظ", "text": "بالسجن."},
        {"num": "211", "law": "قانون العقوبات", "title": "تزوير رسمي", "text": "بالسجن المؤبد."},
        {"num": "290", "law": "قانون العقوبات", "title": "الخطف", "text": "بالسجن المؤبد."},
        {"num": "252", "law": "قانون العقوبات", "title": "الحريق العمد", "text": "بالسجن المؤبد."}
    ]
    
    article_mapping = {}
    for a in golden_articles:
        full_title = f"{a['law']} - {a['title']}"
        cur.execute("SELECT id FROM articles WHERE article_number = %s AND title = %s", (a["num"], full_title))
        row = cur.fetchone()
        if not row:
            uid = str(uuid.uuid4())
            cur.execute("INSERT INTO articles (id, article_number, title, plain_text, domain) VALUES (%s, %s, %s, %s, %s) RETURNING id", 
                       (uid, a["num"], full_title, a["text"], "civil" if "مدني" in a["law"] else "criminal"))
            article_mapping[a["num"]] = cur.fetchone()[0]
        else:
            article_mapping[a["num"]] = row[0]

    rules = [
        # ═══ Criminal Pack ═══
        {"name": "الدفاع الشرعي", "art": "245", "log": {
            "type": "override", "priority": 110, "domain": "criminal",
            "law_type": "penal_code", "rule_type": "self_defense", "pack": "criminal_pack_v1",
            "conditions": [{"fact": "self_defense", "value": True}, {"fact": "imminent_danger", "value": True}],
            "outcomes": {"verdict": "البراءة - فعل مباح بالدفاع الشرعي", "article_number": "245", "law": "قانون العقوبات"}}},

        {"name": "القتل مع سبق الإصرار", "art": "230", "log": {
            "type": "substantive", "priority": 99, "domain": "criminal",
            "law_type": "penal_code", "rule_type": "homicide", "pack": "criminal_pack_v1",
            "conditions": [{"fact": "murder", "value": True}, {"fact": "premeditation", "value": True}],
            "outcomes": {"verdict": "الإعدام شنقاً", "article_number": "230", "law": "قانون العقوبات"}}},

        {"name": "القتل العمد", "art": "234", "log": {
            "type": "substantive", "priority": 98, "domain": "criminal",
            "law_type": "penal_code", "rule_type": "homicide", "pack": "criminal_pack_v1",
            "conditions": [{"fact": "murder", "value": True}, {"fact": "intent", "value": True}],
            "outcomes": {"verdict": "الإعدام", "article_number": "234", "law": "قانون العقوبات"}}},

        {"name": "الضرب المفضي لموت", "art": "236", "log": {
            "type": "substantive", "priority": 97, "domain": "criminal",
            "law_type": "penal_code", "rule_type": "homicide", "pack": "criminal_pack_v1",
            "conditions": [{"fact": "murder", "value": True}, {"fact": "negligence", "value": True}],
            "outcomes": {"verdict": "السجن المؤبد", "article_number": "236", "law": "قانون العقوبات"}}},

        {"name": "السرقة المشددة", "art": "317", "log": {
            "type": "substantive", "priority": 90, "domain": "criminal",
            "law_type": "penal_code", "rule_type": "theft", "pack": "criminal_pack_v1",
            "conditions": [{"fact": "theft", "value": True}, {"fact": "group", "value": True}],
            "outcomes": {"verdict": "السجن المؤبد", "article_number": "317", "law": "قانون العقوبات"}}},

        {"name": "السرقة ليلاً", "art": "317", "log": {
            "type": "substantive", "priority": 89, "domain": "criminal",
            "law_type": "penal_code", "rule_type": "theft", "pack": "criminal_pack_v1",
            "conditions": [{"fact": "theft", "value": True}, {"fact": "from_residence", "value": True}],
            "outcomes": {"verdict": "سجن", "article_number": "317", "law": "قانون العقوبات"}}},

        {"name": "الضرب بآلة حادة", "art": "241", "log": {
            "type": "substantive", "priority": 85, "domain": "criminal",
            "law_type": "penal_code", "rule_type": "assault", "pack": "criminal_pack_v1",
            "conditions": [{"fact": "assault", "value": True}, {"fact": "weapon_used", "value": True}],
            "outcomes": {"verdict": "سجن", "article_number": "241", "law": "قانون العقوبات"}}},

        {"name": "عاهة مستديمة", "art": "241", "log": {
            "type": "substantive", "priority": 84, "domain": "criminal",
            "law_type": "penal_code", "rule_type": "assault", "pack": "criminal_pack_v1",
            "conditions": [{"fact": "assault", "value": True}, {"fact": "permanent_disability", "value": True}],
            "outcomes": {"verdict": "سجن", "article_number": "241", "law": "قانون العقوبات"}}},

        {"name": "تزوير موظف", "art": "211", "log": {
            "type": "substantive", "priority": 95, "domain": "criminal",
            "law_type": "penal_code", "rule_type": "forgery", "pack": "criminal_pack_v1",
            "conditions": [{"fact": "forgery", "value": True}, {"fact": "public_official", "value": True}],
            "outcomes": {"verdict": "السجن المؤبد", "article_number": "211", "law": "قانون العقوبات"}}},

        {"name": "خطف قاصر", "art": "290", "log": {
            "type": "substantive", "priority": 95, "domain": "criminal",
            "law_type": "penal_code", "rule_type": "kidnapping", "pack": "criminal_pack_v1",
            "conditions": [{"fact": "kidnapping", "value": True}, {"fact": "minor_victim", "value": True}],
            "outcomes": {"verdict": "سجن", "article_number": "290", "law": "قانون العقوبات"}}},

        {"name": "حريق عمد", "art": "252", "log": {
            "type": "substantive", "priority": 95, "domain": "criminal",
            "law_type": "penal_code", "rule_type": "arson", "pack": "criminal_pack_v1",
            "conditions": [{"fact": "arson", "value": True}],
            "outcomes": {"verdict": "سجن", "article_number": "252", "law": "قانون العقوبات"}}},

        # ═══ Civil Pack ═══
        {"name": "التعويض المدني", "art": "163", "log": {
            "type": "substantive", "priority": 80, "domain": "civil",
            "law_type": "civil_code", "rule_type": "civil_liability", "pack": "civil_pack_v1",
            "conditions": [{"fact": "civil_fault", "value": True}, {"fact": "injury", "value": True}],
            "outcomes": {"verdict": "إلزام المتسبب بالتعويض الجابر للضرر", "article_number": "163", "law": "القانون المدني"}}},

        {"name": "التعويض الجابر", "art": "163", "log": {
            "type": "substantive", "priority": 81, "domain": "civil",
            "law_type": "civil_code", "rule_type": "civil_liability", "pack": "civil_pack_v1",
            "conditions": [{"fact": "reparation", "value": True}],
            "outcomes": {"verdict": "إلزام المتسبب بالتعويض الجابر للضرر", "article_number": "163", "law": "القانون المدني"}}},

        {"name": "فسخ العقد", "art": "157", "log": {
            "type": "substantive", "priority": 82, "domain": "civil",
            "law_type": "civil_code", "rule_type": "contract_nullity", "pack": "civil_pack_v1",
            "conditions": [{"fact": "contract", "value": True}, {"fact": "nullity", "value": True}],
            "outcomes": {"verdict": "فسخ العقد وإعادة الحال لما كان عليه", "article_number": "157", "law": "القانون المدني"}}},

        # ═══ Procedure Pack ═══
        {"name": "التقادم", "art": "15", "log": {
            "type": "substantive", "priority": 105, "domain": "procedural",
            "law_type": "procedure_code", "rule_type": "expiration", "pack": "procedure_pack_v1",
            "conditions": [{"fact": "expiration", "value": True}],
            "outcomes": {"verdict": "انقضاء الدعوى الجنائية بمضي المدة", "article_number": "15", "law": "قانون الإجراءات"}}},

        {"name": "بطلان التفتيش", "art": "331", "log": {
            "type": "substantive", "priority": 96, "domain": "procedural",
            "law_type": "procedure_code", "rule_type": "nullity", "pack": "procedure_pack_v1",
            "conditions": [{"fact": "nullity_procedural", "value": True}],
            "outcomes": {"verdict": "باطل - لعدم مراعاة أحكام القانون", "article_number": "331", "law": "قانون الإجراءات"}}},
    ]

    for r in rules:
        cur.execute("INSERT INTO rules (article_id, rule_name, logic) VALUES (%s, %s, %s)", (article_mapping[r["art"]], r["name"], json.dumps(r["log"])))
    
    conn.commit()
    print(f"Seeded {len(rules)} rules.")
    cur.close(); conn.close()

if __name__ == "__main__":
    seed_golden_rules_final()
