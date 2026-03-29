"""
Universal Legal Rule Engine — Data-Driven Edition

Pipeline:
  1. procedure  → final=True stops engine immediately
  2. override   → disables targets via "overrides" array (*, category:X, name)
  3. exception  → special-case rules
  4. normal     → priority competition among active (non-disabled) rules
"""


def _get_produces(rule: dict) -> dict:
    """Support 'produces' (legacy), 'outcomes' (legacy), and flattened (v6.3) structures."""
    if "produces" in rule:
        return rule["produces"]
    if "outcomes" in rule:
        return rule["outcomes"]
    # If flattened, the rule itself contains the verdict fields
    if "verdict" in rule:
        return rule
    return {}


def _apply_overrides(rule: dict, all_matched: dict, disabled: set):
    """Populate disabled set from rule's 'overrides' array.
    Supports:  "*"            → global wildcard (all normal + exception)
               "category:X"  → all rules with matching category
               "rule_name"   → specific rule name (safe fallback)
    """
    for target in rule.get("overrides", []):
        if target == "*":
            for g in ("normal", "exception"):
                for r in all_matched.get(g, []):
                    disabled.add(r["name"])
        elif target.startswith("category:"):
            cat = target[len("category:"):]
            for group in all_matched.values():
                for r in group:
                    if r.get("category") == cat:
                        disabled.add(r["name"])
        else:
            disabled.add(target)  # Named — safe fallback, ignore if not found


def _build_result(rule: dict, applied_type: str, disabled: set, procedural_notes: list = None) -> dict:
    produces = _get_produces(rule)
    return {
        "has_conflict":   True,
        "conflict_rule":  rule.get("name") or rule.get("rule", ""),
        "final_verdict":  produces,
        "article":        produces.get("article_number"),
        "law":            produces.get("law"),
        "modifier":       None,
        "reason":         rule.get("name", ""),
        "disabled_rules": sorted(disabled),
        "applied_type":   applied_type,
        "confidence":     produces.get("confidence", 0.9),
        "suppress_origin": rule.get("suppress_origin", []),
        "procedural_notes": procedural_notes or [] # v7.2 Clean separation
    }


def _empty_result() -> dict:
    return {
        "has_conflict": False, "conflict_rule": None,
        "final_verdict": None, "article": None, "law": None,
        "modifier": None, "reason": None,
        "disabled_rules": [], "applied_type": None,
        "reasoning_trace": [],
        "procedural_notes": [] # v7.2
    }


def _build_multi_result(rules: list, applied_type: str, disabled: set, procedural_notes: list = None) -> dict:
    """v7.2: Judicial Subsumption — Pick the single highest priority rule."""
    if not rules: return _empty_result()
    
    # Rules are already sorted by priority in _run_engine
    primary = rules[0]
    produces = _get_produces(primary)
    
    # Capture secondary rules as reason
    secondaries = [r.get("name") for r in rules[1:]]
    reason_text = "تعدد جرائم"
    if secondaries:
        reason_text += f" (مرتبط بـ: {', '.join(secondaries)})"

    return {
        "has_conflict":   True,
        "conflict_rule":  primary.get("name") or primary.get("rule", ""),
        "final_verdict":  produces,
        "article":        produces.get("article_number"),
        "law":            produces.get("law"),
        "modifier":       None,
        "reason":         reason_text,
        "disabled_rules": sorted(disabled),
        "applied_type":   applied_type,
        "confidence":     produces.get("confidence", 0.9),
        "procedural_notes": procedural_notes or []
    }


def _run_engine(all_matched: dict, state: dict = None) -> dict:
    # Sort every group by priority (highest first)
    for group in all_matched.values():
        group.sort(key=lambda r: r.get("priority", 0), reverse=True)

    disabled = set()
    trace = []
    
    fact_ledger = state.get("facts", {}) if state else {}

    def is_burden_met(rule: dict) -> bool:
        threshold = rule.get("burden_of_proof", 0.7)
        # Check rule conditions against fact ledger confidence
        for cond in rule.get("conditions", []):
            fkey = cond.get("fact")
            val = cond.get("value")
            if val is True:
                f_data = fact_ledger.get(fkey, {"confidence": 0})
                if f_data.get("confidence", 0) < threshold:
                    trace.append(f"Rejected {rule['name']}: Fact {fkey} confidence {f_data.get('confidence')} < threshold {threshold}")
                    return False
        return True

    # ── STEP 1: Procedure rules (إجرائية) ─────────────────────────
    procedural_notes = []
    for rule in all_matched.get("procedure", []):
        if is_burden_met(rule):
            # Capture for v7.2 report
            procedural_notes.append({
                "name": rule.get("name"),
                "verdict": _get_produces(rule).get("verdict"),
                "article": _get_produces(rule).get("article_number")
            })
            
            # Apply evidence suppression first (Fruit of the poisonous tree)
            for target in rule.get("overrides", []):
                if target.startswith("evidence:"):
                    e_fact = target[len("evidence:"):]
                    if e_fact == "any":
                        trace.append(f"🚫 Procedural Suppression: ALL evidence suppressed by {rule['name']}")
                        for f in fact_ledger:
                            fact_ledger[f]["confidence"] = 0.0
                    elif e_fact in fact_ledger:
                        trace.append(f"🚫 Procedural Suppression: Evidence {e_fact} suppressed by {rule['name']}")
                        fact_ledger[e_fact]["confidence"] = 0.0

            if rule.get("final", False):
                res = _build_result(rule, "procedure", disabled, procedural_notes)
                res["reasoning_trace"] = trace
                return res
            _apply_overrides(rule, all_matched, disabled)

    # ── STEP 2: Override rules (دفوع / موانع) ─────────────────────
    active_overrides = [
        r for r in all_matched.get("override", [])
        if r["name"] not in disabled and is_burden_met(r)
    ]
    if active_overrides:
        best = active_overrides[0]
        _apply_overrides(best, all_matched, disabled)
        res = _build_result(best, "override", disabled, procedural_notes)
        res["reasoning_trace"] = trace
        return res

    # ── STEP 3: Exception rules ────────────────────────────────────
    active_exceptions = [
        r for r in all_matched.get("exception", [])
        if r["name"] not in disabled and is_burden_met(r)
    ]
    if active_exceptions:
        best = active_exceptions[0]
        _apply_overrides(best, all_matched, disabled)
        res = _build_result(best, "exception", disabled, procedural_notes)
        res["reasoning_trace"] = trace
        return res

    # ── STEP 4: Normal rules (filtered) ───────────────────────────
    active_normals = [
        r for r in all_matched.get("normal", [])
        if r["name"] not in disabled and is_burden_met(r)
    ]
    if active_normals:
        unique_cats = set()
        final_rules = []
        for r in active_normals:
            cat = r.get("category", "")
            if cat not in unique_cats:
                unique_cats.add(cat)
                final_rules.append(r)

        if len(final_rules) == 1:
            res = _build_result(final_rules[0], "normal", disabled, procedural_notes)
        else:
            res = _build_multi_result(final_rules, "normal", disabled, procedural_notes)
        res["reasoning_trace"] = trace
        return res

    res = _empty_result()
    res["reasoning_trace"] = trace
    return res


# ── Public API ─────────────────────────────────────────────────────

def execute(all_matched: dict, state: dict = None) -> dict:
    """Direct entry: pass dict grouped by type."""
    return _run_engine(all_matched, state)


def resolve_conflicts(state: dict, matched_rules: list, db_overrides: list) -> dict:
    """Legacy-compatible entry point — merges both lists then runs engine."""
    all_matched: dict = {"procedure": [], "override": [], "exception": [], "normal": []}
    for r in matched_rules + db_overrides:
        t = r.get("type", "normal")
        if t == "substantive":
            t = "normal"
        all_matched.setdefault(t, []).append(r)
    return _run_engine(all_matched, state)
