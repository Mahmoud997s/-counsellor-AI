"""
Conflict Resolver - محرك حل التعارض القانوني (نسخة البيانات)
يستقبل القواعد المطابقة من قاعدة البيانات ويطبّق منطق الإلغاء أو التعديل
"""

def resolve_conflicts(state: dict, matched_rules: list, db_overrides: list) -> dict:
    result = {
        "has_conflict": False,
        "conflict_rule": None,
        "final_verdict": None,
        "reason": None,
        "modifier": None,
        "article": None,
        "law": None
    }
    
    # 1. البحث عن قواعد الإلغاء/التجاوز الكامل (Overrides)
    overrides = [r for r in db_overrides if r.get("type") == "override"]
    overrides.sort(key=lambda x: x.get("priority", 0), reverse=True)
    
    for ovr in overrides:
        target_rules = ovr.get("overrides", []) or []
        ovr_name = ovr.get("rule") or ovr.get("name") or "Unnamed Override"
        
        active_rules = [r.get("rule", "") for r in matched_rules]
        blocked_outcomes = ovr.get("blocks_outcomes", []) or []
        active_outcomes = [r.get("punishment_type", "") for r in matched_rules]
        
        should_trigger = False
        
        # FIXED: GLOBAL OVERRIDE triggers even if SUBSTANTIVE is missing (Default)
        if not target_rules and not blocked_outcomes:
            should_trigger = True
        else:
            # Specific Target Lookup
            for tr in target_rules:
                if any(tr.lower() in ar.lower() for ar in active_rules):
                    should_trigger = True
                    break
            if not should_trigger and blocked_outcomes:
                if any(bo in active_outcomes for bo in blocked_outcomes):
                    should_trigger = True
            
        if should_trigger:
            outcomes = ovr.get("outcomes", {})
            result["has_conflict"] = True
            result["conflict_rule"] = ovr_name
            result["final_verdict"] = outcomes
            result["article"] = outcomes.get("article_number")
            result["law"] = outcomes.get("law")
            return result

    # 2. البحث عن القواعد المُعدّلة (Modifiers)
    modifiers = [r for r in db_overrides if r.get("type") == "modifier"]
    if modifiers:
        best_mod = max(modifiers, key=lambda x: x.get("priority", 0))
        mod_outcomes = best_mod.get("outcomes", {})
        result["has_conflict"] = True
        result["conflict_rule"] = best_mod.get("rule") or best_mod.get("name")
        result["modifier"] = best_mod.get("modifier")
        result["article"] = mod_outcomes.get("article_number")
        result["law"] = mod_outcomes.get("law")

    return result
