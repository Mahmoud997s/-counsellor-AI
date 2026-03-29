# test_digital_judge_v5_1.py
from case_manager import CaseManager
import json

def test_causal_brain():
    manager = CaseManager()
    print("⚖️ Digital Judge v5.1: The Causal Gauntlet 🚀")
    
    # --- SCENARIO 3: Delayed Response (Temporal Gap) ---
    print("\n🚨 [TEST 3] Delayed Response (Gap Check)")
    cid3 = manager.create_case("قضية هجوم مؤجل", "تهديد قديم تبعه اعتداء متأخر")
    manager.process_input(cid3, "المجني عليه هدد المتهم بالقتل")
    res3 = manager.process_input(cid3, "بعد يوم كامل، قام المتهم بقتل المجني عليه")
    reasoning3 = res3["reasoning"]
    findings3 = reasoning3["interpreted_state"]["findings"]
    print(f"  - Delayed Target Found: {findings3['delayed_response']}")
    print(f"  - Verdict: {reasoning3.get('conflict_rule')}")
    print(f"  - Trace: {reasoning3.get('reasoning_trace')}")
    print(f"  - Concepts: {reasoning3['interpreted_state']['concepts']}")

    # --- SCENARIO 5: Escalation (Extreme Excess) ---
    print("\n🚨 [TEST 5] Escalation (Proportionality Check)")
    cid5 = manager.create_case("قضية تجاوز دفاع", "استخدام سلاح ناري ضد دفع باليد")
    manager.process_input(cid5, "المجني عليه دفع المتهم بيده")
    res5 = manager.process_input(cid5, "قام المتهم بإطلاق النار على المجني عليه وقتله")
    reasoning5 = res5["reasoning"]
    findings5 = reasoning5["interpreted_state"]["findings"]
    print(f"  - Force Ratio: {findings5['force_ratio']:.2f}")
    print(f"  - Force Tier: {findings5['force_tier']}")
    print(f"  - Verdict: {reasoning5.get('conflict_rule')}")
    print(f"  - Trace: {reasoning5.get('reasoning_trace')}")

    # --- SCENARIO 4: First Strike (Initial Aggressor) ---
    print("\n🚨 [TEST 4] First Strike (Causality Check)")
    cid4 = manager.create_case("قضية المعتدي الأول", "المتهم بدأ بالضرب رغم وجود تهديد بسيط")
    manager.process_input(cid4, "كان المجني عليه يصرخ في وجه المتهم")
    res4 = manager.process_input(cid4, "قام المتهم بطعن المجني عليه فوراً")
    reasoning4 = res4["reasoning"]
    findings4 = reasoning4["interpreted_state"]["findings"]
    print(f"  - Initial Aggressor: {findings4['initial_aggressor']}")
    print(f"  - Verdict: {reasoning4.get('conflict_rule')}")
    print(f"  - Trace: {reasoning4.get('reasoning_trace')}")

    print("\n✨ Digital Judge v5.1 Causal Gauntlet Complete!")

if __name__ == "__main__":
    test_causal_brain()
