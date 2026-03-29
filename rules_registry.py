# rules_registry.py
from typing import Callable, Dict, Any, List, Optional

class Rule:
    def __init__(self, name: str, group: str, condition: Callable[[Dict[str, Any]], bool], 
                 effect: Callable[[], Dict[str, Any]], priority: int = 50, 
                 burden_of_proof: float = 0.7, suppress_origin: List[str] = None):
        self.name = name
        self.group = group 
        self.condition = condition
        self.effect = effect
        self.priority = priority
        self.burden_of_proof = burden_of_proof
        self.suppress_origin = suppress_origin or []

    def evaluate(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Verification of state confidence vs burden of proof happens in the Engine
        if self.condition(state):
            effect_data = self.effect()
            res = {
                "name": self.name,
                "group": self.group,
                "priority": self.priority,
                "burden_of_proof": self.burden_of_proof,
                "suppress_origin": self.suppress_origin, # Essential for v7.1
                "conditions": [] 
            }
            # Flatten effect_data into top level (v6.3.0)
            res.update(effect_data)
            return res
        return None

# --- Legal Rule Definitions (Art. 230-251 Egyptian Penal Code) ---

MURDER_RULE = Rule(
    name="جناية القتل العمد (المادة 230-234)",
    group="normal",
    condition=lambda s: s["concepts"].get("violence_score", 0) > 0.8 and s["concepts"].get("lethal_intent", False),
    effect=lambda: {
        "verdict": "الإعدام أو السجن المؤبد",
        "law": "قانون العقوبات المصري",
        "article_number": "230-234",
        "category": "homicide",
        "overrides": ["category:homicide_unintentional"] # Suppress lesser crimes
    },
    priority=50,
    burden_of_proof=0.85
)

SELF_DEFENSE_RULE = Rule(
    name="الدفاع الشرعي الكامل (المادة 245-247)",
    group="override",
    condition=lambda s: s["findings"].get("immediate_threat") and s["findings"].get("proportional_response") and s["findings"].get("initial_aggressor") != s.get("current_actor"),
    effect=lambda: {
        "verdict": "البراءة لقيام حالة الدفاع الشرعي الكامل",
        "law": "قانون العقوبات المصري",
        "article_number": "245-247",
        "category": "legal_defense",
        "overrides": ["category:homicide", "category:assault"]
    },
    priority=90,
    burden_of_proof=0.60
)

EXCESSIVE_DEFENSE_RULE = Rule(
    name="تجاوز حدود الدفاع الشرعي (المادة 251)",
    group="override",
    condition=lambda s: s["findings"].get("immediate_threat") and s["findings"].get("force_tier") in ("excessive", "extreme_excess"),
    effect=lambda: {
        "verdict": "تخفيف العقوبة إلى الحبس (تجاوز حدود الدفاع الشرعي بموجب المادة 251)",
        "law": "قانون العقوبات المصري",
        "article_number": "251",
        "category": "legal_mitigation",
        "overrides": ["category:homicide"]
    },
    priority=85,
    burden_of_proof=0.60
)

ASSAULT_LEADING_TO_DEATH = Rule(
    name="الضرب المفضي إلى الموت (المادة 236)",
    group="normal",
    condition=lambda s: s["concepts"].get("violence_score", 0) > 0.7,
    effect=lambda: {
        "verdict": "السجن المشدد أو السجن من 3 إلى 7 سنوات",
        "law": "قانون العقوبات المصري",
        "article_number": "236",
        "category": "homicide_unintentional"
    },
    priority=40,
    burden_of_proof=0.70
)

PROCEDURAL_NULLITY = Rule(
    name="بطلان إجراءات الضبط (المادة 30 أ.ج)",
    group="procedure",
    condition=lambda s: s.get("raw_facts", {}).get("procedural_error", {}).get("value", False),
    effect=lambda: {
        "verdict": "بطلان إجراءات القبض والتفتيش وما تلاهما من دليل",
        "law": "قانون الإجراءات الجنائية المصري",
        "article_number": "30",
        "category": "procedure_void",
        "overrides": [] # We don't override the case anymore, we suppress evidence
    },
    priority=100,
    burden_of_proof=0.55,
    suppress_origin=["SEARCH", "SEIZURE", "no_warrant", "illegal_search"] # Expanded for v7.1 mapping
)

WARRANTLESS_SEARCH_RULE = Rule(
    name="بطلان التفتيش لانتفاء حالة التلبس وعدم وجود إذن",
    group="procedure",
    condition=lambda s: s.get("raw_facts", {}).get("no_warrant", {}).get("value", False) and not s.get("raw_facts", {}).get("red_handed", {}).get("value", False),
    effect=lambda: {
        "verdict": "بطلان التفتيش وبطرح الدليل المستمد منه",
        "law": "قانون الإجراءات الجنائية المصري",
        "article_number": "30",
        "category": "procedure_void",
        "overrides": ["category:homicide", "category:assault", "category:homicide_unintentional"]
    },
    priority=95,
    burden_of_proof=0.55,
    suppress_origin=["SEARCH", "no_warrant"]
)

ASSAULT_MISDEMEANOR_RULE = Rule(
    name="جنحة الضرب البسيط (المادة 242)",
    group="normal",
    condition=lambda s: s["concepts"].get("violence_score", 0) >= 0.05, # Captures any battery
    effect=lambda: {
        "verdict": "الحبس مدة لا تزيد على سنة أو الغرامة",
        "law": "قانون العقوبات المصري",
        "article_number": "241-242",
        "category": "assault"
    },
    priority=30,
    burden_of_proof=0.50
)

RULES_REGISTRY: List[Rule] = [
    MURDER_RULE,
    SELF_DEFENSE_RULE,
    EXCESSIVE_DEFENSE_RULE,
    ASSAULT_LEADING_TO_DEATH,
    ASSAULT_MISDEMEANOR_RULE,
    PROCEDURAL_NULLITY,
    WARRANTLESS_SEARCH_RULE
]
