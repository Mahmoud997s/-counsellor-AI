# reasoning_engine.py
from typing import List, Dict, Any, Type
from rules_registry import Rule, MURDER_RULE, ASSAULT_LEADING_TO_DEATH, EXCESSIVE_DEFENSE_RULE, SELF_DEFENSE_RULE, PROCEDURAL_NULLITY
from conflict_resolver import execute as conflict_execute
from psycopg2.extras import RealDictCursor
from semantic_interpreter import get_interpreter
from rules_registry import RULES_REGISTRY

class ReasoningEngine:
    def __init__(self):
        self.interpreter = get_interpreter()
        self.rules = RULES_REGISTRY

    def run(self, case_id, case_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        The Causal Brain Loop: Sequence -> Interpret -> Findings -> Verdict
        """
        # 1. Fetch Events from DB
        from case_manager import CaseManager
        events = CaseManager().get_case_events(case_id)
        
        # 2. Interpret State (Findings Layer)
        interpreted_data = self.interpreter.interpret(case_state, events)
        findings = interpreted_data["findings"]
        
        # 2. Rule Application (Forward Chaining)
        matched_rules = {"procedure": [], "override": [], "normal": [], "exception": []}
        trace = []
        
        # Initial weighted confidence calculation (Simple for now)
        fact_confs = [f.get("confidence", 0) for f in case_state.get("facts", {}).values()]
        cm = CaseManager()
        events = cm.get_case_events(case_id)
        
        # Get all defendants
        with cm.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name FROM actors WHERE case_id = %s AND role = 'defendant';", (case_id,))
            defendants = cur.fetchall()

        all_verdicts = {}
        suppression_orders = set()
        
        # --- PASS 1: Identify Procedural Issues & Suppression Orders ---
        for def_node in defendants:
            d_id, d_name = def_node["id"], def_node["name"]
            if d_name.upper() in ["SYSTEM", "CASE", "SEARCH"]: continue
            
            d_events = [e for e in events if e.get("actor") == d_name]
            interpreted_data = self.interpreter.interpret(case_state, d_events)
            interpreted_data["current_actor"] = d_name
            
            # Simple first-pass rule match
            for rule in self.rules:
                res = rule.evaluate(interpreted_data)
                if res and res.get("group") == "procedure":
                    # Collect directive for Pass 2
                    for origin in res.get("suppress_origin", []):
                        suppression_orders.add(origin)
        
        # --- INTERMEDIATE: Apply Suppression & Recompute if needed ---
        if suppression_orders:
            cm.suppress_evidence_by_type(case_id, list(suppression_orders))
            # Refresh case state with sanitized data
            case_state = cm.recompute_case_state(case_id)
            # Refresh events for pass 2
            events = cm.get_case_events(case_id)

        # --- PASS 2: Final Inference (The 'Surgical' Verdict) ---
        for def_node in defendants:
            d_id, d_name = def_node["id"], def_node["name"]
            if d_name.upper() in ["SYSTEM", "CASE", "SEARCH"]: continue
            
            d_events = [e for e in events if e.get("actor") == d_name]
            interpreted_data = self.interpreter.interpret(case_state, d_events)
            interpreted_data["current_actor"] = d_name
            findings = interpreted_data["findings"]
            
            trace = []
            matched_rules = {"procedure": [], "override": [], "exception": [], "normal": []}
            
            for rule in self.rules:
                res = rule.evaluate(interpreted_data)
                if res:
                    trace.append(f"✅ Matched ({d_name}): {rule.name}")
                    matched_rules[rule.group].append(res)
            
            final_v = conflict_execute(matched_rules, interpreted_data)
            final_v["reasoning_trace"] = trace + final_v.get("reasoning_trace", [])
            
            self._build_judicial_explanation(final_v, findings, matched_rules, d_name)
            all_verdicts[d_name] = final_v

        return {
            "defendants": all_verdicts,
            "interpreted_state": interpreted_data,
            "suppressed_tracks": list(suppression_orders)
        }

    def _build_judicial_explanation(self, verdict, findings, matched_rules, actor_name="المتهم"):
        """
        Synthesizes findings into a logical syllogism.
        """
        aggressor = findings.get("initial_aggressor", "غير محدد")
        imminent = findings.get("immediate_threat", False)
        proportional = findings.get("proportional_response", False)
        ratio = findings.get("force_ratio", 0)

        explanation = []
        explanation.append(f"• ثبت من وقائع الدعوى أن البادئ بالاعتداء هو: {aggressor}.")
        
        if imminent:
            explanation.append("• ثبت وجود خطر حقيقي ومحدق يهدد سلامة المتهم.")
        else:
            explanation.append("• لم يثبت وجود خطر حال أو وشيك يبرر استخدام القوة.")
        
        winner_rule = verdict.get("label", "القواعد العامة")
        explanation.append(f"• بالتطبيق على نصوص القانون: تنطبق {winner_rule}.")
        
        verdict["final_summary"] = "\n".join(explanation)

def get_engine():
    return ReasoningEngine()

if __name__ == "__main__":
    # Test with dummy state
    dummy_state = {
        "facts": {
            "murder": {"confidence": 0.9},
            "intent": {"confidence": 0.9},
            "imminent_danger": {"confidence": 0.8}
        }
    }
    engine = get_engine()
    res = engine.run(dummy_state)
    import json
    print(json.dumps(res, indent=2, ensure_ascii=False))
