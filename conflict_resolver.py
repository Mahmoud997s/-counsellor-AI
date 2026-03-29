"""
Universal Legal Rule Engine — Data-Driven Edition

Pipeline:
  1. procedure  → final=True stops engine immediately
  2. override   → disables targets via "overrides" array (*, category:X, name)
  3. exception  → special-case rules
  4. normal     → priority competition among active (non-disabled) rules
"""


def _get_produces(rule: dict) -> dict:
    """Support both 'produces' (new) and 'outcomes' (legacy)."""
    return rule.get("produces") or rule.get("outcomes") or {}


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


def _build_result(rule: dict, applied_type: str, disabled: set) -> dict:
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
    }


def _empty_result() -> dict:
    return {
        "has_conflict": False, "conflict_rule": None,
        "final_verdict": None, "article": None, "law": None,
        "modifier": None, "reason": None,
        "disabled_rules": [], "applied_type": None,
    }


def _build_multi_result(rules: list, applied_type: str, disabled: set) -> dict:
    produces = {
        "verdict": " و ".join([_get_produces(r).get("verdict", "") for r in rules]),
        "article_number": " و ".join([str(_get_produces(r).get("article_number", "")) for r in rules]),
        "law": rules[0].get("produces", {}).get("law", "") if rules else ""
    }
    return {
        "has_conflict":   True,
        "conflict_rule":  " + ".join([r.get("name") or r.get("rule", "") for r in rules]),
        "final_verdict":  produces,
        "article":        produces.get("article_number"),
        "law":            produces.get("law"),
        "modifier":       None,
        "reason":         "تعدد جرائم",
        "disabled_rules": sorted(disabled),
        "applied_type":   applied_type,
        "confidence":     max([_get_produces(r).get("confidence", 0.9) for r in rules]) if rules else 0.9,
    }


def _run_engine(all_matched: dict) -> dict:
    # Sort every group by priority (highest first)
    for group in all_matched.values():
        group.sort(key=lambda r: r.get("priority", 0), reverse=True)

    disabled = set()

    # ── STEP 1: Procedure rules (إجرائية) ─────────────────────────
    for rule in all_matched.get("procedure", []):
        if rule.get("final", False):
            return _build_result(rule, "procedure", disabled)
        _apply_overrides(rule, all_matched, disabled)

    # ── STEP 2: Override rules (دفوع / موانع) ─────────────────────
    active_overrides = [
        r for r in all_matched.get("override", [])
        if r["name"] not in disabled
    ]
    if active_overrides:
        # Highest priority wins (already sorted)
        best = active_overrides[0]
        _apply_overrides(best, all_matched, disabled)
        return _build_result(best, "override", disabled)

    # ── STEP 3: Exception rules ────────────────────────────────────
    active_exceptions = [
        r for r in all_matched.get("exception", [])
        if r["name"] not in disabled
    ]
    if active_exceptions:
        best = active_exceptions[0]
        _apply_overrides(best, all_matched, disabled)
        return _build_result(best, "exception", disabled)

    # ── STEP 4: Normal rules (filtered) ───────────────────────────
    active_normals = [
        r for r in all_matched.get("normal", [])
        if r["name"] not in disabled
    ]
    if active_normals:
        # Avoid duplicate categories (keep highest priority only for each category)
        unique_cats = set()
        final_rules = []
        for r in active_normals:
            cat = r.get("category", "")
            if cat not in unique_cats:
                unique_cats.add(cat)
                final_rules.append(r)

        if len(final_rules) == 1:
            return _build_result(final_rules[0], "normal", disabled)
        else:
            return _build_multi_result(final_rules, "normal", disabled)

    return _empty_result()


# ── Public API ─────────────────────────────────────────────────────

def execute(all_matched: dict) -> dict:
    """Direct entry: pass dict grouped by type."""
    return _run_engine(all_matched)


def resolve_conflicts(state: dict, matched_rules: list, db_overrides: list) -> dict:
    """Legacy-compatible entry point — merges both lists then runs engine."""
    all_matched: dict = {"procedure": [], "override": [], "exception": [], "normal": []}
    for r in matched_rules + db_overrides:
        t = r.get("type", "normal")
        if t == "substantive":
            t = "normal"
        all_matched.setdefault(t, []).append(r)
    return _run_engine(all_matched)
