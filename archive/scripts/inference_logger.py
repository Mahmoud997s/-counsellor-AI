"""
inference_logger.py - نظام تسجيل وتتبع سلسلة استدلال الحكم

يُنشئ سجلاً كاملاً لكل قضية:
- الحقائق المُستخلصة
- القواعد المُطابَقة
- التجاوزات المُطبَّقة
- الحكم النهائي مع المرجع القانوني
"""

from datetime import datetime
from typing import Optional


class InferenceLog:
    """يجمع ويُنظّم كل خطوة في سلسلة الاستدلال القانوني."""
    
    def __init__(self, case_text: str):
        self.case_text = case_text[:200]  # اقتصاص للعرض
        self.timestamp = datetime.utcnow().isoformat()
        self.facts_extracted: dict = {}
        self.rules_evaluated: list = []
        self.rules_matched: list = []
        self.overrides_evaluated: list = []
        self.override_applied: Optional[str] = None
        self.override_reason: Optional[str] = None
        self.final_verdict: Optional[str] = None
        self.final_article: Optional[str] = None
        self.final_law: Optional[str] = None
    
    def log_facts(self, facts: dict):
        """يسجل الحقائق المُستخلصة من نص القضية."""
        self.facts_extracted = facts
    
    def log_rule_evaluated(self, rule_name: str, matched: bool, rule_type: str, priority: int):
        """يسجل اختبار قاعدة ما."""
        self.rules_evaluated.append({
            "rule": rule_name, "matched": matched, "type": rule_type, "priority": priority
        })
        if matched:
            self.rules_matched.append({"rule": rule_name, "type": rule_type, "priority": priority})
    
    def log_override(self, override_name: str, applied: bool, reason: str = ""):
        """يسجل محاولة تجاوز قاعدة ما."""
        self.overrides_evaluated.append({
            "override": override_name, "applied": applied, "reason": reason
        })
        if applied:
            self.override_applied = override_name
            self.override_reason = reason
    
    def log_verdict(self, verdict: str, article: str, law: str):
        """يسجل الحكم النهائي."""
        self.final_verdict = verdict
        self.final_article = article
        self.final_law = law
    
    def to_dict(self) -> dict:
        """يُحوّل السجل إلى كائن JSON قابل للإرسال عبر API."""
        return {
            "timestamp": self.timestamp,
            "case_summary": self.case_text,
            "facts_extracted": {
                k: v for k, v in self.facts_extracted.items() if v
            },
            "rules_matched": [r["rule"] for r in self.rules_matched],
            "override_applied": self.override_applied,
            "override_reason": self.override_reason,
            "final_verdict": self.final_verdict,
            "final_article": self.final_article,
            "final_law": self.final_law
        }
    
    def render_human(self) -> str:
        """يُنتج تقريراً مقروءاً للمحامي."""
        lines = [
            "=" * 55,
            "⚖️  سجل الاستدلال القانوني",
            "=" * 55,
            f"📄 القضية: {self.case_text}",
            "-" * 55,
        ]
        
        # الحقائق
        active_facts = [k for k, v in self.facts_extracted.items() if v]
        if active_facts:
            lines.append(f"🔍 الحقائق المُستخلصة ({len(active_facts)}):")
            for fact in active_facts:
                val = self.facts_extracted[fact]
                if isinstance(val, dict):
                    conf = int(val.get("confidence", 1.0) * 100)
                    lines.append(f"   ✓ {fact} (ثقة: {conf}%)")
                else:
                    lines.append(f"   ✓ {fact}")
        
        lines.append("-" * 55)
        
        # القواعد المُطابَقة
        if self.rules_matched:
            lines.append(f"📋 القواعد المُطابَقة ({len(self.rules_matched)}):")
            for r in self.rules_matched:
                prefix = "🔁 تجاوز" if r["type"] == "override" else "📌 موضوعية"
                lines.append(f"   {prefix}: {r['rule']} (أولوية: {r['priority']})")
        else:
            lines.append("⚠️  لا توجد قواعد مطابقة")
        
        lines.append("-" * 55)
        
        # التجاوز
        if self.override_applied:
            lines.append(f"⚡ تجاوز مُطبَّق: {self.override_applied}")
            if self.override_reason:
                lines.append(f"   السبب: {self.override_reason}")
        
        # الحكم النهائي
        lines.append("-" * 55)
        lines.append(f"✅ الحكم النهائي: {self.final_verdict or 'لا حكم'}")
        if self.final_article and self.final_law:
            lines.append(f"   المرجع: المادة {self.final_article} - {self.final_law}")
        lines.append("=" * 55)
        
        return "\n".join(lines)
    
    def render_json(self) -> str:
        """يُنتج سجلاً بتنسيق JSON."""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# =======================================================
# Self-Test
# =======================================================

if __name__ == "__main__":
    log = InferenceLog("هجم المجني عليه على المتهم بسكين وكان سيقتله فدافع عن نفسه")
    log.log_facts({"murder": True, "self_defense": True, "imminent_danger": True})
    log.log_rule_evaluated("القتل العمد البسيط", True, "substantive", 98)
    log.log_rule_evaluated("البراءة للدفاع الشرعي", True, "override", 110)
    log.log_override("البراءة للدفاع الشرعي", True, "الدفاع الشرعي يُسقط التهمة بموجب م.245")
    log.log_verdict("البراءة - فعل مباح بالدفاع الشرعي", "245", "قانون العقوبات")
    
    print(log.render_human())
