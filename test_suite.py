"""
Test Suite - اختبار شامل للمحرك القانوني
كل test case يحتوي: Input → Expected Verdict + Expected Facts
"""
import sys
sys.path.insert(0, r'c:\Users\DELL\Desktop\قانون')
from case_analyzer import analyze_case

# =============================================
# قائمة الاختبارات
# =============================================
TEST_CASES = [

    # ════ القتل العمد ════
    {
        "id": "T01",
        "case": "قام المتهم بقتل الضحية عمداً بعد أن أطلق عليها النار بمسدسه",
        "expected_verdict_contains": "الإعدام",
        "expected_facts": ["murder", "intent", "weapon_used"],
        "category": "قتل"
    },
    {
        "id": "T02",
        "case": "خطط المتهم لقتل ضحيته وترصد له أياماً ثم أقدم على قتله",
        "expected_verdict_contains": "الإعدام",
        "expected_facts": ["murder", "premeditation"],
        "category": "قتل"
    },
    {
        "id": "T03",
        "case": "تشاجر المتهم مع جاره وضربه بعصا حتى فارق الحياة دون قصد القتل",
        "expected_verdict_contains": "المؤبد",
        "expected_facts": ["murder", "negligence"],
        "category": "قتل"
    },

    # ════ الدفاع الشرعي ════
    {
        "id": "T04",
        "case": "هجم المجني عليه على المتهم بسكين وكان سيقتله فدافع عن نفسه وقتله",
        "expected_verdict_contains": "البراءة",
        "expected_facts": ["murder", "self_defense", "imminent_danger"],
        "category": "دفاع شرعي"
    },

    # ════ السرقة ════
    {
        "id": "T05",
        "case": "سرق المتهم المحل بالقوة والتهديد بمسدس مع عصابة مسلحة",
        "expected_verdict_contains": "المؤبد",
        "expected_facts": ["theft", "weapon_used", "by_force", "group"],
        "category": "سرقة"
    },
    {
        "id": "T06",
        "case": "سرق من منزل الجار ليلاً دون استخدام أي قوة",
        "expected_verdict_contains": "سجن",
        "expected_facts": ["theft", "at_night", "from_residence"],
        "category": "سرقة"
    },

    # ════ الاعتداء ════
    {
        "id": "T07",
        "case": "اعتدى المتهم على المجني عليه بسكين وأحدث به جروحاً بليغة",
        "expected_verdict_contains": "سجن",
        "expected_facts": ["assault", "weapon_used", "severe_injury"],
        "category": "اعتداء"
    },
    {
        "id": "T08",
        "case": "اعتدى المتهم على المجني عليه وأحدث به عاهة مستديمة في يده",
        "expected_verdict_contains": "سجن",
        "expected_facts": ["assault", "permanent_disability"],
        "category": "اعتداء"
    },

    # ════ الإجراءات / البطلان ════
    {
        "id": "T09",
        "case": "دخل ضباط الشرطة المنزل وفتشوه بدون إذن قضائي ووجدوا أدلة",
        "expected_verdict_contains": "باطل",
        "expected_facts": ["search", "evidence"],
        "category": "إجراءات"
    },

    # ════ المدني ════
    {
        "id": "T10",
        "case": "تسبب المتهم بإهماله في حادث أدى لأضرار جسيمة في سيارة المجني عليه",
        "expected_verdict_contains": "تعويض",
        "expected_facts": ["civil_fault", "injury"],
        "category": "مدني"
    },

    # ════ التزوير + موظف عام ════
    {
        "id": "T11",
        "case": "قام الموظف العام بتزوير محررات رسمية بحكم وظيفته لصرف أموال عامة",
        "expected_verdict_contains": "المؤبد",
        "expected_facts": ["forgery", "public_official"],
        "category": "تزوير"
    },

    # ════ خطف ════
    {
        "id": "T12",
        "case": "خطف المتهم طفلاً قاصراً وطالب أهله بفدية",
        "expected_verdict_contains": "سجن",
        "expected_facts": ["kidnapping", "minor_victim"],
        "category": "خطف"
    },

    # ════ حريق ════
    {
        "id": "T13",
        "case": "اشعل المتهم النار في المبنى عمداً مما أدى لأضرار جسيمة",
        "expected_verdict_contains": "سجن",
        "expected_facts": ["arson", "intent"],
        "category": "حريق"
    },

    # ════ مدني (إنجليزي) ════
    {
        "id": "T14",
        "case": "The defendant committed a fault using his car which caused a permanent injury to the pedestrian's leg, and the pedestrian is now claiming reparation for his damages.",
        "expected_verdict_contains": "التعويض",
        "expected_facts": ["civil_fault", "injury", "reparation"],
        "category": "Civil - EN"
    },

    # ════ مدني (عربي) ════
    {
        "id": "T15",
        "case": "قام الطرفان بتوقيع عقد بيع، ولكن تبين لاحقاً أن العقد يتضمن بنوداً تؤدي إلى بطلان الاتفاق (فسخ).",
        "expected_verdict_contains": "فسخ",
        "expected_facts": ["contract", "nullity"],
        "category": "Civil - AR"
    },

    # ════ إجراءات ════
    {
        "id": "T16",
        "case": "تم تفتيش منزل المتهم وضبط أشياء ولكن المحامي دفع بانقضاء الدعوى الجنائية بمضي المدة (تقادم).",
        "expected_verdict_contains": "انقضاء",
        "expected_facts": ["search", "expiration"],
        "category": "Procedure"
    },

    # ════ Override vs Override ════
    {
        "id": "T17",
        "case": "تم إكراه المتهم وتهديده لقتل شخص واضطرار لذلك، لكن المجني عليه هجم عليه فدافع عن نفسه وقتله (إكراه + دفاع شرعي)",
        "expected_verdict_contains": "البراءة",
        "expected_facts": ["murder", "by_force", "self_defense", "necessity"],
        "category": "Override vs Override"
    },

    # ════ Procedure vs Override ════
    {
        "id": "T18",
        "case": "فتشوا منزله بلا إذن (بطلان) ووجدوا جثة هجم صاحبها بسكين فدافع عن نفسه",
        "expected_verdict_contains": "باطل",
        "expected_facts": ["search", "nullity_procedural", "murder", "self_defense"],
        "category": "Procedure vs Override"
    },

    # ════ Global Override Robustness ════
    {
        "id": "T19",
        "case": "عاد المتهم ليلاً مع عصابة وسرقوا المحل وضربوا الحارس ولكن تبين وجود حالة ضرورة قصوى",
        "expected_verdict_contains": "البراءة",
        "expected_facts": ["theft", "group", "at_night", "assault", "necessity"],
        "category": "Global Override"
    },

    # ════ قضايا متنوعة جديدة (T20-T29) ════
    {
        "id": "T20",
        "case": "شرع المتهم في قتل الضحية بسكين لكن الناس أوقفوه قبل إتمام الجريمة",
        "expected_verdict_contains": "السجن المشدد",
        "expected_facts": ["murder", "attempted", "weapon_used"],
        "category": "شروع"
    },
    {
        "id": "T21",
        "case": "ضرب المتهم جاره وسرق منه حافظة نقوده بالقوة في الطريق العام",
        "expected_verdict_contains": "المؤبد", # سرقة مشددة (By Force)
        "expected_facts": ["theft", "assault", "by_force"],
        "category": "سرقة بالإكراه"
    },
    {
        "id": "T22",
        "case": "سرق المتهم قطعة خبز من السوبر ماركت وفر هارباً",
        "expected_verdict_contains": "حبس", # سرقة بسيطة
        "expected_facts": ["theft"],
        "category": "سرقة بسيطة"
    },
    {
        "id": "T23",
        "case": "اعتدى عليه بالضرب المبرح مما أدى لكسر في ذراعه (عاهة)",
        "expected_verdict_contains": "سجن", # ضرب مغلظ
        "expected_facts": ["assault", "permanent_disability"],
        "category": "اعتداء جسيم"
    },
    {
        "id": "T24",
        "case": "يطالب المدعي بتعويض عادل عن الأضرار المادية والأدبية التي لحقت به",
        "expected_verdict_contains": "تعويض",
        "expected_facts": ["reparation"],
        "category": "مدني - تعويض"
    },
    {
        "id": "T25",
        "case": "الموظف العام قام بتغيير بيانات رسمية في السجلات الحكومية",
        "expected_verdict_contains": "المؤبد", # تزوير رسمي
        "expected_facts": ["forgery", "public_official"],
        "category": "تزوير موظف"
    },
    {
        "id": "T26",
        "case": "تم تفتيش المتهم بدون إذن قضائي وضبطت معه أدلة جريمة، ولكن الجريمة ارتكبت منذ أكثر من 20 عاماً (تقادم)",
        "expected_verdict_contains": "انقضاء", # التقادم يسبق البطلان في الترتيب أو كلاهما يغلق الدعوى
        "expected_facts": ["search", "evidence", "expiration"],
        "category": "تعدد إجرائي"
    },
    {
        "id": "T27",
        "case": "هجم اللص على صاحب المنزل بسكين، فقام صاحب المنزل بسحب سلاح اللص وقتله به",
        "expected_verdict_contains": "البراءة",
        "expected_facts": ["murder", "self_defense", "imminent_danger", "weapon_used"],
        "category": "دفاع معقد"
    },
    {
        "id": "T28",
        "case": "The contractor failed to complete the building as per the agreement, leading to a lawsuit for breach of contract.",
        "expected_verdict_contains": "فسخ",
        "expected_facts": ["contract", "nullity"],
        "category": "Civil EN - Breach"
    },
    {
        "id": "T29",
        "case": "أجبره المجرمون تحت تهديد السلاح على سرقة خزينة البنك (إكراه/ضرورة)",
        "expected_verdict_contains": "البراءة",
        "expected_facts": ["theft", "by_force", "necessity"],
        "category": "سرقة تحت الإكراه"
    },

    # ════ قضايا الإصدار v2.5 (T30-T34) ════
    {
        "id": "T30",
        "case": "هجم عليه اللص بسكين في ورشته، فقام بطعنه فوراً بسكين للدفاع عن نفسه وقتله",
        "expected_verdict_contains": "البراءة",
        "expected_facts": ["murder", "self_defense", "imminent_danger"],
        "category": "دفاع شرعي سليم"
    },
    {
        "id": "T31",
        "case": "ضربه جاره بزجاجة، فذهب المتهم وعاد بعد فترة زمنية لاحقا ومعه مسدس وقتله للثأر والانتقام",
        "expected_verdict_contains": "الإعدام", # انتقام + فاصل زمني يبطل الدفاع
        "expected_facts": ["murder", "assault", "weapon_used", "temporal_gap", "retaliation"],
        "category": "انتقام وتجاوز"
    },
    {
        "id": "T32",
        "case": "تم تفتيش شقته بدون إذن وعثروا على أدلة تدينه، ورغم ذلك اعترف المتهم بالجريمة",
        "expected_verdict_contains": "باطل", # الإجراء الباطل هو final=True فيسقط الاعتراف
        "expected_facts": ["search", "nullity_procedural", "evidence", "confession"],
        "category": "اعتراف مع بطلان"
    },
    {
        "id": "T33",
        "case": "تم استدراجه وتهديده بإيذاء أسرته (إكراه) فنقل البضاعة المسروقة رغم اعترافه بذلك",
        "expected_verdict_contains": "البراءة", # حالة ضرورة تغلب
        "expected_facts": ["theft", "necessity", "confession"],
        "category": "إكراه جاد"
    },
    {
        "id": "T34",
        "case": "في مشاجرة، قتل الأول شخصاً بسكين مع سبق الإصرار، وضرب الثاني محدثاً به عاهة مستديمة",
        "expected_verdict_contains": "الإعدام", # بسبب تعدد الجرائم نتوقع ظهور العقوبتين أو دمج النص
        "expected_facts": ["murder", "assault", "permanent_disability", "weapon_used"],
        "category": "تعدد الأحكام"
    },
]

# =============================================
# تشغيل الاختبارات
# =============================================
def run_tests():
    print("🧪 Running Legal Engine Test Suite...")
    print("=" * 65)

    passed = 0
    failed = 0
    results = []

    for t in TEST_CASES:
        result = analyze_case(t["case"])
        verdict = result.get("verdict", "") or ""
        active = result.get("active_facts", {})

        # فحص الحكم
        verdict_ok = t["expected_verdict_contains"].lower() in verdict.lower()

        # فحص الـ Facts
        facts_ok = all(active.get(f) for f in t["expected_facts"])
        missing_facts = [f for f in t["expected_facts"] if not active.get(f)]

        ok = verdict_ok and facts_ok

        status = "✅ PASS" if ok else "❌ FAIL"
        if ok:
            passed += 1
        else:
            failed += 1

        results.append({
            "id": t["id"],
            "status": status,
            "category": t["category"],
            "verdict": verdict[:40] if verdict else "لا حكم",
            "verdict_ok": verdict_ok,
            "facts_ok": facts_ok,
            "missing_facts": missing_facts
        })

        print(f"{status} [{t['id']}] {t['category']}")
        print(f"       الحكم: {verdict[:50] if verdict else 'لا حكم'}")
        if not verdict_ok:
            print(f"       ⚠️  توقعنا: '{t['expected_verdict_contains']}'")
        if missing_facts:
            print(f"       ⚠️  Facts ناقصة: {missing_facts}")
        print()

    print("=" * 65)
    print(f"📊 النتيجة: {passed}/{len(TEST_CASES)} نجح | {failed} فشل")

    score = (passed / len(TEST_CASES)) * 100
    print(f"🎯 دقة المحرك: {score:.0f}%")

    if score == 100:
        print("🏆 المحرك يعمل بكفاءة مثالية!")
    elif score >= 80:
        print("✅ المحرك جيد - يحتاج تحسينات طفيفة")
    elif score >= 60:
        print("⚠️  المحرك متوسط - يحتاج مراجعة")
    else:
        print("❌ المحرك يحتاج إصلاحات جوهرية")

    print("=" * 65)
    return results

if __name__ == "__main__":
    run_tests()
