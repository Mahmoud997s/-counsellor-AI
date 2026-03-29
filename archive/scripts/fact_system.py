"""
fact_system.py - نظام إدارة الحقائق القانونية

يُحوّل الحقائق من Boolean بسيط إلى كائنات ذات مستوى ثقة ومصدر.
هذا يتيح دخول الـ AI لاحقاً بتحسين مستويات الثقة.
"""

# =======================================================
# Fact Factory
# =======================================================

def make_fact(value: bool, confidence: float = 1.0, source: str = "nlp_regex") -> dict:
    """
    ينشئ كائن حقيقة قانونية موحّد.
    
    Args:
        value: هل الحقيقة صحيحة؟
        confidence: مستوى الثقة (0.0 - 1.0)
        source: مصدر الحقيقة (nlp_regex, ai_model, manual, db_lookup)
    """
    return {
        "value": value,
        "confidence": confidence,
        "source": source
    }

def make_true(confidence: float = 1.0, source: str = "nlp_regex") -> dict:
    """اختصار لإنشاء حقيقة صحيحة."""
    return make_fact(True, confidence, source)

def make_false() -> dict:
    """اختصار لإنشاء حقيقة خاطئة."""
    return make_fact(False, 0.0, "default")


# =======================================================
# Fact Accessors
# =======================================================

def get_fact_value(fact) -> bool:
    """يستخرج قيمة الحقيقة بصرف النظر عن شكل تخزينها (dict أو bool)."""
    if isinstance(fact, dict):
        return bool(fact.get("value", False))
    return bool(fact)

def get_confidence(fact) -> float:
    """يستخرج مستوى الثقة."""
    if isinstance(fact, dict):
        return float(fact.get("confidence", 1.0))
    return 1.0 if fact else 0.0

def get_source(fact) -> str:
    """يستخرج مصدر الحقيقة."""
    if isinstance(fact, dict):
        return fact.get("source", "unknown")
    return "legacy_bool"

def is_fact_true(fact) -> bool:
    """يتحقق إذا كانت الحقيقة صحيحة (بصرف النظر عن الشكل)."""
    return get_fact_value(fact)


# =======================================================
# Fact State Utilities
# =======================================================

def normalize_state(state: dict) -> dict:
    """
    يحوّل state القديم (bool) إلى state الجديد (dict).
    للتوافق مع البيانات القديمة.
    """
    normalized = {}
    for key, val in state.items():
        if key.startswith("_"):
            normalized[key] = val  # keep private flags as-is
        elif isinstance(val, dict):
            normalized[key] = val  # already new format
        else:
            normalized[key] = make_fact(bool(val))
    return normalized

def get_active_facts_summary(state: dict) -> dict:
    """
    يُرجع ملخص الحقائق النشطة بتنسيق مناسب للـ API.
    
    Returns:
        {
            "murder": {"value": True, "confidence": 0.95, "source": "nlp_regex"},
            ...
        }
    """
    return {
        key: val for key, val in state.items()
        if not key.startswith("_") and is_fact_true(val)
    }

def get_confidence_weighted_facts(state: dict) -> list:
    """
    يُرجع قائمة الحقائق مرتبة حسب مستوى الثقة (للـ AI لاحقاً).
    """
    facts = []
    for key, val in state.items():
        if not key.startswith("_") and is_fact_true(val):
            facts.append({
                "fact": key,
                "confidence": get_confidence(val),
                "source": get_source(val)
            })
    return sorted(facts, key=lambda x: x["confidence"], reverse=True)


# =======================================================
# Self-Test
# =======================================================

if __name__ == "__main__":
    # اختبار سريع
    state = {
        "murder": make_true(confidence=0.95),
        "intent": make_true(confidence=0.9),
        "negligence": make_false(),
        "_civil_only": False
    }
    
    print("✅ Active facts:")
    for f in get_confidence_weighted_facts(state):
        print(f"  {f['fact']}: confidence={f['confidence']} source={f['source']}")
