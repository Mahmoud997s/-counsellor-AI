# test_digital_judge_v5.py
from case_manager import CaseManager
import json

def test_judgment_day():
    manager = CaseManager()
    print("⚖️ Digital Judge v5: Judgment Day Test 🚀")
    
    # 1. Start a New Case
    case_id = manager.create_case("قضية الدفاع الشرعي المتكاملة", "تحقيق في واقعة قتل مع ادعاء دفاع شرعي")
    print(f"✅ Case Created: {case_id}")
    
    # 2. Input 1: The Threat (Imminent Danger)
    print("\n📩 Input 1: 'المجني عليه هجم على المتهم بسكين وهدده بالقتل'")
    res1 = manager.process_input(case_id, "المجني عليه هجم على المتهم بسكين وهدده بالقتل")
    
    # 3. Input 2: The Response (Lethal Intent)
    print("\n📩 Input 2: 'قام المتهم بإخراج مسدسه وقتل المجني عليه عمداً'")
    res2 = manager.process_input(case_id, "قام المتهم بإخراج مسدسه وقتل المجني عليه عمداً")
    
    # 4. Final Verdict Analysis
    reasoning = res2["reasoning"]
    print(f"\n🧠 Semantic Analysis:")
    interp = reasoning["interpreted_state"]
    print(f"  - Violence Score: {interp['violence_score']:.2f}")
    print(f"  - Threat Imminence: {interp['threat_imminence']:.2f}")
    print(f"  - Lethal Intent: {interp['lethal_intent']}")
    
    print(f"\n⚖️ Judicial Verdict: {reasoning.get('conflict_rule')}")
    print(f"📜 Final Results: {json.dumps(reasoning['final_verdict']['verdict'], ensure_ascii=False)}")
    
    print(f"\n💡 Interpretation Trace:")
    for step in reasoning["reasoning_trace"]:
        print(f"  - {step}")

    print("\n✨ Digital Judge v5 Verified Successfully!")

if __name__ == "__main__":
    test_judgment_day()
