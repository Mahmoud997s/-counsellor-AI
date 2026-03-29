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
