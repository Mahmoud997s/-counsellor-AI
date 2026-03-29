import psycopg2
import json

DB_PARAMS = {
    "dbname": "counselor",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5433"
}

# =============================================
# القواعد - output مُهيكل (Structured Schema)
# Store: integers | Render: later
# =============================================
RULES = [
    # --- قانون العقوبات ---
    {
        "rule_name": "القتل العمد - عقوبة الإعدام",
        "article_number": "230",
        "article_domain": "criminal",
        "logic": {
            "domain": "criminal",
            "priority": 10,
            "confidence": 0.95,
            "conditions": [
                {"fact": "murder", "value": True},
                {"fact": "intent", "value": True}
            ],
            "outcomes": {
                "verdict": "الإعدام",
                "article_number": 230,
                "law": "قانون العقوبات",
                "punishment_type": "death_penalty"
            }
        }
    },
    {
        "rule_name": "القتل بلا قصد - السجن المؤبد",
        "article_number": "235",
        "article_domain": "criminal",
        "logic": {
            "domain": "criminal",
            "priority": 9,
            "confidence": 0.9,
            "conditions": [
                {"fact": "murder", "value": True},
                {"fact": "intent", "value": False}
            ],
            "outcomes": {
                "verdict": "السجن المؤبد",
                "article_number": 235,
                "law": "قانون العقوبات",
                "punishment_type": "life_imprisonment"
            }
        }
    },
    {
        "rule_name": "السرقة البسيطة - السجن",
        "article_number": "311",
        "article_domain": "criminal",
        "logic": {
            "domain": "criminal",
            "priority": 7,
            "confidence": 0.9,
            "conditions": [
                {"fact": "theft", "value": True},
                {"fact": "aggravating", "value": False}
            ],
            "outcomes": {
                "verdict": "السجن",
                "article_number": 311,
                "law": "قانون العقوبات",
                "punishment_type": "imprisonment"
            }
        }
    },
    {
        "rule_name": "السرقة بالإكراه - سجن مشدد",
        "article_number": "314",
        "article_domain": "criminal",
        "logic": {
            "domain": "criminal",
            "priority": 8,
            "confidence": 0.9,
            "conditions": [
                {"fact": "theft", "value": True},
                {"fact": "aggravating", "value": True}
            ],
            "outcomes": {
                "verdict": "السجن المؤبد أو المشدد",
                "article_number": 314,
                "law": "قانون العقوبات",
                "punishment_type": "life_imprisonment"
            }
        }
    },
    {
        "rule_name": "الاعتداء الجسدي - حبس وغرامة",
        "article_number": "241",
        "article_domain": "criminal",
        "logic": {
            "domain": "criminal",
            "priority": 6,
            "confidence": 0.85,
            "conditions": [
                {"fact": "assault", "value": True},
                {"fact": "murder", "value": False}
            ],
            "outcomes": {
                "verdict": "الحبس والغرامة",
                "article_number": 241,
                "law": "قانون العقوبات",
                "punishment_type": "imprisonment_and_fine"
            }
        }
    },
    {
        "rule_name": "الاحتيال والتزوير - السجن",
        "article_number": "335",
        "article_domain": "criminal",
        "logic": {
            "domain": "criminal",
            "priority": 7,
            "confidence": 0.88,
            "conditions": [
                {"fact": "fraud", "value": True}
            ],
            "outcomes": {
                "verdict": "السجن",
                "article_number": 335,
                "law": "قانون العقوبات",
                "punishment_type": "imprisonment"
            }
        }
    },
    {
        "rule_name": "الدفاع الشرعي - البراءة",
        "article_number": "245",
        "article_domain": "criminal",
        "logic": {
            "domain": "criminal",
            "priority": 10,
            "confidence": 0.92,
            "conditions": [
                {"fact": "self_defense", "value": True}
            ],
            "outcomes": {
                "verdict": "البراءة",
                "article_number": 245,
                "law": "قانون العقوبات",
                "punishment_type": "acquittal"
            }
        }
    },
    # --- قانون الإجراءات الجنائية 2025 ---
    {
        "rule_name": "لا إدانة بلا دليل",
        "article_number": "1",
        "article_domain": "criminal_procedure",
        "logic": {
            "domain": "criminal_procedure",
            "priority": 10,
            "confidence": 0.99,
            "conditions": [
                {"fact": "evidence", "value": False},
                {"fact": "conviction", "value": True}
            ],
            "outcomes": {
                "verdict": "البراءة - لا إدانة بلا دليل",
                "article_number": 1,
                "law": "قانون الإجراءات الجنائية 2025",
                "punishment_type": "acquittal"
            }
        }
    },
    {
        "rule_name": "التفتيش بلا إذن - دليل باطل",
        "article_number": "91",
        "article_domain": "criminal_procedure",
        "logic": {
            "domain": "criminal_procedure",
            "priority": 9,
            "confidence": 0.93,
            "conditions": [
                {"fact": "search", "value": True},
                {"fact": "search_warrant", "value": False}
            ],
            "outcomes": {
                "verdict": "بطلان الدليل المستخرج",
                "article_number": 91,
                "law": "قانون الإجراءات الجنائية 2025",
                "punishment_type": "nullity"
            }
        }
    },
    # --- قانون مدني ---
    {
        "rule_name": "المسؤولية المدنية - خطأ وضرر",
        "article_number": "163",
        "article_domain": "civil_law",
        "logic": {
            "domain": "civil_law",
            "priority": 8,
            "confidence": 0.9,
            "conditions": [
                {"fact": "fault", "value": True},
                {"fact": "damage", "value": True}
            ],
            "outcomes": {
                "verdict": "الالتزام بالتعويض",
                "article_number": 163,
                "law": "القانون المدني",
                "punishment_type": "compensation"
            }
        }
    },
    {
        "rule_name": "لا تعويض بلا ضرر",
        "article_number": "163",
        "article_domain": "civil_law",
        "logic": {
            "domain": "civil_law",
            "priority": 4,
            "confidence": 0.9,
            "conditions": [
                {"fact": "damage", "value": False},
                {"fact": "compensation", "value": True}
            ],
            "outcomes": {
                "verdict": "رفض دعوى التعويض",
                "article_number": 163,
                "law": "القانون المدني",
                "punishment_type": "no_compensation"
            }
        }
    },
]

def seed_rules():
    print("🔌 Connecting to Counselor DB - Phase 5: Rules Seeding...")
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM rules;")
    print("🗑️  Cleared old rules.")

    inserted = 0
    skipped = 0

    for rule in RULES:
        cursor.execute("""
            SELECT id FROM articles
            WHERE article_number = %s AND domain = %s
            LIMIT 1
        """, (rule["article_number"], rule["article_domain"]))
        res = cursor.fetchone()

        if not res:
            print(f"   ⚠️  Article {rule['article_number']} ({rule['article_domain']}) not found - skipping")
            skipped += 1
            continue

        cursor.execute("""
            INSERT INTO rules (article_id, rule_name, logic)
            VALUES (%s, %s, %s)
        """, (res[0], rule["rule_name"], json.dumps(rule["logic"], ensure_ascii=False)))
        inserted += 1
        print(f"   ✅ {rule['rule_name']}")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n{'='*45}")
    print(f"📋 Inserted: {inserted} | Skipped: {skipped}")
    print(f"{'='*45}")

if __name__ == "__main__":
    seed_rules()
