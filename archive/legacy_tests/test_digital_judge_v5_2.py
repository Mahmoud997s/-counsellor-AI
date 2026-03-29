# test_digital_judge_v5_2.py
from case_manager import CaseManager
import json

def test_judicial_graduation():
    manager = CaseManager()
    print("⚖️ Digital Judge v5.2: The Judicial Summary Gauntlet 🚀")
    
    # --- SCENARIO 5: Mitigated Excessive Defense (Art. 251) ---
    print("\n🚨 [TEST 5] Mitigated Excessive Defense (Art. 251)")
    cid5 = manager.create_case("قضية تجاوز دفاع", "استخدام سلاح ناري ضد عصا")
    manager.process_input(cid5, "المجني عليه هجم على المتهم بعصا خشبية")
    res5 = manager.process_input(cid5, "قام المتهم بإخراج مسدسه وقتل المجني عليه")
    reasoning5 = res5["reasoning"]
    
    print(f"  - Initial Aggressor: {reasoning5['interpreted_state']['findings']['initial_aggressor']}")
    print(f"  - Force Tier: {reasoning5['interpreted_state']['findings']['force_tier']}")
    print(f"  - Conflict Winner: {reasoning5.get('conflict_rule')}") 
    print(f"  - Final Summary:\n{reasoning5.get('final_summary')}")

    # --- SCENARIO 6: Rule Suppression (Murder vs Manslaughter) ---
    print("\n🚨 [TEST 6] Rule Suppression (Murder vs Manslaughter)")
    cid6 = manager.create_case("قضية قتل عمد كاملة الأركان", "قتل مع سبق الإصرار")
    manager.process_input(cid6, "بيت المتهم النية وصمم على قتل المجني عليه")
    res6 = manager.process_input(cid6, "نفذ المتهم الخطة وقتله بدم بارد")
    reasoning6 = res6["reasoning"]
    
    trace_cats = [r for r in reasoning6.get("reasoning_trace", []) if "Matched" in r]
    print(f"  - Verdict: {reasoning6.get('conflict_rule')}")
    print(f"  - Rules Matched: {len(trace_cats)}")
    print(f"  - Trace: {reasoning6.get('reasoning_trace')}") # Should NOT contain Art. 236 in final selection even if eligible

    print("\n✨ Digital Judge v5.2 Gauntlet Complete!")

if __name__ == "__main__":
    test_judicial_graduation()
