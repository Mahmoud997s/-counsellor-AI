# Implementation Plan - Legal Engine v3.0 (Scenario Generation)

## Objective
Upgrade the engine from a "Rule-Based Trigger" to a competitive **Reasoning Engine**. The engine will generate multiple plausible legal scenarios by toggling critical facts, evaluate them using a mathematically sound scoring function (incorporating logical consistency and penalties), and select the "Best" outcome.

## User Review Required

> [!IMPORTANT]
> I have adopted your exact scoring and generation formulas.
> 
> *   **Independent Toggles Only**: We only flip one critical fact per scenario to prevent exponential explosion.
> *   **Context-Aware Activation**: We will NOT randomly flip `self_defense` to `True` unless the base facts already contain `imminent_danger` or `weapon_used` or `assault`.
> *   **Rule Return Data**: `apply_rules` will be refactored to return `{"verdict": X, "priority": Y, "rule_id": Z}`.
> *   **Debug Mode**: `analyze_case` will print the top scenarios and their scores when `debug=True`.
> 
> Is the `ConsistencyScore` mapping ready for execution? (I will penalize `self_defense` without `imminent_danger`, and `intent=False` with `premeditation=True`).

## Proposed Architecture

### 1. The Math Formula
```python
import math

Score = (AvgConfidence * 0.4) + (ConsistencyScore * 0.3) + (LegalStrength * 0.3) - Penalty
```
*   `LegalStrength`: `math.log(1 + priority)`
*   `Penalty`: `0.2` if fact was flipped (i.e. assumed)
*   `AvgConfidence`: The average `confidence` value of all currently active facts.

### 2. Scenario Generation (`generate_scenarios`)
#### [MODIFY] [case_analyzer.py](file:///c:/Users/DELL/Desktop/قانون/case_analyzer.py)
*   **Base Scenario**: Original NLP extracted state.
*   **Critical Facts**: `["self_defense", "intent", "necessity"]`
*   **Toggle Logic**: 
    *   If active: Generate a scenario where it is `False` (simulate "What if the NLP was overreacting?").
    *   If inactive but context supports it (e.g. `self_defense` needs `assault` or `imminent_danger` exist in base), generate a scenario where it is `True` with `0.2` confidence.

### 3. Rule Refactoring (`apply_rules`)
#### [MODIFY] [case_analyzer.py](file:///c:/Users/DELL/Desktop/قانون/case_analyzer.py)
*   Update `apply_rules` to return the matching rule's `priority` and `condition` keys for logging.

### 4. Verification Plan
*   Run the main Test Suite (`test_suite.py`).
*   Ensure the introduction of Scenario Generation does NOT break the 100% accuracy of the base test suite.
*   Inspect the debug logs of Case X to visually see the engine testing `self_defense=False` and penalizing it.
