# Implementation Plan - Legal Engine v3.0 (Scenario Generation)

## Objective
Introduce **Scenario Generation & Evaluation** to the Legal Inference Engine. Instead of trusting the NLP extraction blindly, the engine will act like a legal strategist, generating multiple plausible scenarios (e.g., "What if this is NOT self-defense?"), evaluating each through the rule engine, and selecting the mathematically "best" interpretation.

## User Review Required

> [!IMPORTANT]
> The scoring mechanism is the most critical part of this plan. 
> I propose the following basic scoring formula for a scenario:
> `Score = (Average Confidence of Active Facts) * (Winning Rule Priority)`
> *   **Base Fact Confidence**: If NLP found `self_defense` (confidence 0.95), keeping it gives a high score.
> *   **Flipped Fact Confidence**: If we test a scenario where we flip `self_defense` to `False`, we assign a penalty confidence (e.g., `0.1`) to that altered fact.
> *   **Winning Rule Priority**: A strong rule like `Acquittal` (Priority 10) or `Murder` (Priority 9) will heavily multiply the score.
> 
> Does this scoring approach align with your vision?

## Proposed Changes

### [MODIFY] [case_analyzer.py](file:///c:/Users/DELL/Desktop/قانون/case_analyzer.py)

#### 1. Define Critical Facts
```python
CRITICAL_FACTS = ["self_defense", "necessity", "premeditation", "intent"]
```

#### 2. Implement `generate_scenarios(base_state)`
*   Start with `scenarios = [base_state]`
*   Iterate through `CRITICAL_FACTS`:
    *   If the fact is Active in `base_state`, create a scenario where it is False (assigning it a low confidence like `0.1`).
    *   If the fact is Inactive but the case has crimes (`murder`, `theft`, etc.), create a scenario where it is True (assigning it a low confidence like `0.2` as a "what-if" defense).

#### 3. Implement `evaluate_scenario(scenario, verdict_data)`
*   Calculate the Average Fact Confidence of all active facts in the scenario.
*   Multiply by `verdict_data["priority"]` if a verdict exists, else `1`.
*   Return the final `score`.

#### 4. Update Engine Pipeline in `analyze_events`
*   Instead of `apply_rules(state)`, we will:
    *   `scenarios = generate_scenarios(state)`
    *   Iterate scenarios and track `best_scenario` and `best_verdict`.
    *   Output the selected scenario's verdict for that event.

## Open Questions

1.  **Rule Priority Source**: Currently, `apply_rules` doesn't return the integer `priority` of the matched rule, but we need it for scoring. I will modify `apply_rules` to return a `{"verdict": X, "priority": Y}` dictionary, or just look up the priority from the matched rule.
2.  **Number of Scenarios**: Do we want combinatorial explosion (all combinations of critical facts) or just independent toggles? Independent toggles (1 flip per scenario) is safer to start.
