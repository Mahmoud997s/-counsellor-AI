# test_digital_judge_v5_3.py
from case_manager import CaseManager
import json

def test_multi_actor_complexity():
    manager = CaseManager()
    print("⚖️ Digital Judge v5.3: The Multi-Actor Ultra Gauntlet 🚀")
    
    cid = manager.create_case("القضية الجنائية المركبة", "اشتباك متعدد الأطراف في مقهى")
    
    # Phase 1: The Threat (1 Hour Gap)
    print("\n⏳ Processing Phase 1: The Initial Threat...")
    manager.process_input(cid, "نشب خلاف لفظي بين المتهم الأول أحمد سالم والمجني عليه الأول محمد علي")
    manager.process_input(cid, "قام المجني عليه محمد علي بتهديد المتهم الأول أحمد سالم بالقتل")
    
    # Phase 2: The Ambush/Encounter
    print("⚔️ Processing Phase 2: The Encounter...")
    manager.process_input(cid, "بعد ساعة التقى المتهم الأول أحمد سالم بالمتهم الثاني محمود جابر")
    manager.process_input(cid, "المجني عليه محمد علي هجم على المتهم أحمد سالم ودفع أحمد أولاً")
    
    # Phase 3: The Escalation
    print("🩸 Processing Phase 3: Multiple Assaults...")
    manager.process_input(cid, "قام المتهم الأول أحمد سالم بضرب المجني عليه محمد علي بيده")
    manager.process_input(cid, "قام المتهم الثاني محمود جابر بطعن المجني عليه الثاني خالد حسن بسكين")
    manager.process_input(cid, "قام المتهم الثالث كريم فتحي بضرب المجني عليه الثالث يوسف عبد الرحمن بعصا")
    
    # Phase 4: The Fatal Shot
    print("💣 Processing Phase 4: The Fatal Escalation...")
    final_res = manager.process_input(cid, "قام المتهم الأول أحمد سالم بإطلاق النار من مسدسه وقتل محمد علي")
    
    # --- ANALYSIS ---
    reasoning = final_res["reasoning"]
    defendants = reasoning.get("defendants", {})

    print("\n📜 --- VERDICT SUMMARY ---")
    for name, verdict in defendants.items():
        print(f"\n👤 Defendant: {name}")
        print(f"  - Primary Crime: {verdict.get('conflict_rule', 'None')}")
        print(f"  - Reasoning:\n{verdict.get('final_summary')}")
        if "reasoning_trace" in verdict:
            print(f"  - Trace: {verdict['reasoning_trace'][:3]}...")

    print("\n✨ Digital Judge v5.3 Ultra Gauntlet Complete!")

if __name__ == "__main__":
    test_multi_actor_complexity()
