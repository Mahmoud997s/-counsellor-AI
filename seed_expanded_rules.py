"""
Expanded Rules - قواعد مُوسّعة بـ Facts تفصيلية
تغطي سيناريوهات أكثر دقة من مجرد "قتل + عمد"
"""
import psycopg2
import json

DB_PARAMS = {
    "dbname": "counselor", "user": "postgres",
    "password": "postgres", "host": "localhost", "port": "5433"
}

# =============================================
# القواعد المُوسّعة - Facts تفصيلية
# =============================================
EXPANDED_RULES = [

    # ══════════════════════════════════
    # القتل العمد - سيناريوهات متعددة
    # ══════════════════════════════════
    {
        "rule_name": "قتل عمد + سبق إصرار وترصد → إعدام",
        "article_number": "230", "article_domain": "criminal",
        "logic": {
            "domain": "criminal", "priority": 10, "confidence": 0.97,
            "conditions": [
                {"fact": "murder", "value": True},
                {"fact": "premeditation", "value": True}
            ],
            "outcomes": {
                "verdict": "الإعدام", "article_number": 230,
                "law": "قانون العقوبات", "punishment_type": "death_penalty"
            }
        }
    },
    {
        "rule_name": "قتل عمد + سلاح ناري → إعدام",
        "article_number": "230", "article_domain": "criminal",
        "logic": {
            "domain": "criminal", "priority": 10, "confidence": 0.95,
            "conditions": [
                {"fact": "murder", "value": True},
                {"fact": "intent", "value": True},
                {"fact": "weapon_used", "value": True}
            ],
            "outcomes": {
                "verdict": "الإعدام", "article_number": 230,
                "law": "قانون العقوبات", "punishment_type": "death_penalty"
            }
        }
    },
    {
        "rule_name": "قتل عمد + تعدد ضحايا → إعدام مشدد",
        "article_number": "230", "article_domain": "criminal",
        "logic": {
            "domain": "criminal", "priority": 10, "confidence": 0.97,
            "conditions": [
                {"fact": "murder", "value": True},
                {"fact": "intent", "value": True},
                {"fact": "multiple_victims", "value": True}
            ],
            "outcomes": {
                "verdict": "الإعدام (تعدد الجرائم)", "article_number": 230,
                "law": "قانون العقوبات", "punishment_type": "death_penalty"
            }
        }
    },
    {
        "rule_name": "قتل بلا قصد + إهمال → سجن مؤبد",
        "article_number": "235", "article_domain": "criminal",
        "logic": {
            "domain": "criminal", "priority": 9, "confidence": 0.9,
            "conditions": [
                {"fact": "murder", "value": True},
                {"fact": "negligence", "value": True},
                {"fact": "premeditation", "value": False}
            ],
            "outcomes": {
                "verdict": "السجن المؤبد", "article_number": 235,
                "law": "قانون العقوبات", "punishment_type": "life_imprisonment"
            }
        }
    },

    # ══════════════════════════════════
    # السرقة - سيناريوهات
    # ══════════════════════════════════
    {
        "rule_name": "سرقة مسلحة + تهديد → سجن مشدد",
        "article_number": "314", "article_domain": "criminal",
        "logic": {
            "domain": "criminal", "priority": 9, "confidence": 0.93,
            "conditions": [
                {"fact": "theft", "value": True},
                {"fact": "weapon_used", "value": True},
                {"fact": "by_force", "value": True}
            ],
            "outcomes": {
                "verdict": "السجن المؤبد أو المشدد", "article_number": 314,
                "law": "قانون العقوبات", "punishment_type": "life_imprisonment"
            }
        }
    },
    {
        "rule_name": "سرقة ليلاً + من مسكن → سجن مشدد",
        "article_number": "316", "article_domain": "criminal",
        "logic": {
            "domain": "criminal", "priority": 8, "confidence": 0.88,
            "conditions": [
                {"fact": "theft", "value": True},
                {"fact": "at_night", "value": True},
                {"fact": "from_residence", "value": True}
            ],
            "outcomes": {
                "verdict": "السجن المشدد - سرقة ليلية من مسكن", "article_number": 316,
                "law": "قانون العقوبات", "punishment_type": "aggravated_prison"
            }
        }
    },

    # ══════════════════════════════════
    # الاعتداء - سيناريوهات
    # ══════════════════════════════════
    {
        "rule_name": "اعتداء + عاهة مستديمة → سجن",
        "article_number": "240", "article_domain": "criminal",
        "logic": {
            "domain": "criminal", "priority": 8, "confidence": 0.9,
            "conditions": [
                {"fact": "assault", "value": True},
                {"fact": "permanent_disability", "value": True}
            ],
            "outcomes": {
                "verdict": "السجن - عاهة مستديمة", "article_number": 240,
                "law": "قانون العقوبات", "punishment_type": "imprisonment"
            }
        }
    },
    {
        "rule_name": "اعتداء + سلاح + جروح بليغة → سجن مشدد",
        "article_number": "242", "article_domain": "criminal",
        "logic": {
            "domain": "criminal", "priority": 8, "confidence": 0.88,
            "conditions": [
                {"fact": "assault", "value": True},
                {"fact": "weapon_used", "value": True},
                {"fact": "severe_injury", "value": True}
            ],
            "outcomes": {
                "verdict": "السجن المشدد - اعتداء بسلاح يُحدث جروحاً بليغة", "article_number": 242,
                "law": "قانون العقوبات", "punishment_type": "aggravated_prison"
            }
        }
    },

    # ══════════════════════════════════
    # قرينة البراءة + دفاع شرعي
    # ══════════════════════════════════
    {
        "rule_name": "دفاع شرعي + خطر داهم → براءة",
        "article_number": "245", "article_domain": "criminal",
        "logic": {
            "domain": "criminal", "priority": 10, "confidence": 0.95,
            "conditions": [
                {"fact": "self_defense", "value": True},
                {"fact": "imminent_danger", "value": True}
            ],
            "outcomes": {
                "verdict": "البراءة - دفاع شرعي مع خطر داهم", "article_number": 245,
                "law": "قانون العقوبات", "punishment_type": "acquittal"
            }
        }
    },
    {
        "rule_name": "دفاع شرعي دون خطر داهم → تخفيف",
        "article_number": "245", "article_domain": "criminal",
        "logic": {
            "domain": "criminal", "priority": 8, "confidence": 0.8,
            "conditions": [
                {"fact": "self_defense", "value": True},
                {"fact": "imminent_danger", "value": False}
            ],
            "outcomes": {
                "verdict": "تخفيف العقوبة - دفاع شرعي منقوص", "article_number": 245,
                "law": "قانون العقوبات", "punishment_type": "mitigated"
            }
        }
    },

    # ══════════════════════════════════
    # إجراءات جنائية - بطلان
    # ══════════════════════════════════
    {
        "rule_name": "اعتراف تحت إكراه → باطل",
        "article_number": "272", "article_domain": "criminal_procedure",
        "logic": {
            "domain": "criminal_procedure", "priority": 9, "confidence": 0.95,
            "conditions": [
                {"fact": "confession", "value": True},
                {"fact": "coerced", "value": True}
            ],
            "outcomes": {
                "verdict": "الاعتراف باطل - انتُزع بالإكراه", "article_number": 272,
                "law": "قانون الإجراءات الجنائية 2025", "punishment_type": "nullity"
            }
        }
    },
    {
        "rule_name": "تسجيل بلا علم الطرفين → دليل باطل",
        "article_number": "95", "article_domain": "criminal_procedure",
        "logic": {
            "domain": "criminal_procedure", "priority": 8, "confidence": 0.88,
            "conditions": [
                {"fact": "wiretap", "value": True},
                {"fact": "search_warrant", "value": False}
            ],
            "outcomes": {
                "verdict": "الدليل الرقمي باطل - تسجيل بدون إذن قضائي", "article_number": 95,
                "law": "قانون الإجراءات الجنائية 2025", "punishment_type": "nullity"
            }
        }
    },
]


def seed_expanded_rules():
    print("🔌 Connecting to DB - Expanded Rules Seeding...")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    cur.execute("SELECT rule_name FROM rules;")
    existing = {r[0] for r in cur.fetchall()}

    inserted = skipped = 0

    for rule in EXPANDED_RULES:
        if rule["rule_name"] in existing:
            skipped += 1
            continue

        cur.execute("""
            SELECT id FROM articles
            WHERE article_number = %s AND domain = %s LIMIT 1
        """, (rule["article_number"], rule["article_domain"]))
        res = cur.fetchone()

        if not res:
            print(f"   ⚠️  Article {rule['article_number']} not found - skipping")
            skipped += 1
            continue

        cur.execute("""
            INSERT INTO rules (article_id, rule_name, logic)
            VALUES (%s, %s, %s)
        """, (res[0], rule["rule_name"], json.dumps(rule["logic"], ensure_ascii=False)))
        inserted += 1
        print(f"   ✅ {rule['rule_name']}")

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM rules;")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()

    print(f"\n{'='*50}")
    print(f"✅ Expanded Rules: +{inserted} | Total in DB: {total}")
    print(f"{'='*50}")

if __name__ == "__main__":
    seed_expanded_rules()
