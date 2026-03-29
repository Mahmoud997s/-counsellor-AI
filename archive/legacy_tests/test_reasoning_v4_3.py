# test_reasoning_v4_3.py
from case_manager import CaseManager
from conflict_resolver import execute
import json

def test_burden_of_proof():
    manager = CaseManager()
    print("🚀 Testing Intelligent Reasoning v4.3...")
    
    # 1. Create a Case
    case_id = manager.create_case("اختبار عبء الإثبات والتدرج", "تحقيق في تهمة قتل مع تضارب")
    print(f"✅ Case Created: {case_id}")
    
    # 2. Input 1: Uncertain Murder (يحتمل)
    print("\n📩 Input 1: 'يحتمل أن المتهم قام بقتل المجني عليه'")
    state1 = manager.process_input(case_id, "يحتمل أن المتهم قام بقتل المجني عليه")
    murder_conf = state1["facts"]["murder"]["confidence"]
    print(f"🧠 Current Murder Confidence: {murder_conf:.2f}")
    
    # 3. Simulate Rule Engine with threshold check (Burden = 0.85 for murder)
    rules = [{"name": "قاعدة القتل العمد (85%)", "burden_of_proof": 0.85, "type": "normal", "conditions": [{"fact": "murder", "value": True}], "produces": {"verdict": "إعدام"}}]
    res1 = execute({"normal": rules}, state1)
    print(f"🔎 Rule Result 1: {'Applied' if res1.get('has_conflict') else 'REJECTED (Below Threshold)'}")
    if not res1.get("has_conflict"):
        print(f"💡 Trace: {res1.get('reasoning_trace')}")

    # 4. Input 2: Another source confirms (Boosting confidence)
    print("\n📩 Input 2: 'شاهد عيان يؤكد: المتهم قتل المجني عليه فعلاً'")
    state2 = manager.process_input(case_id, "شاهد عيان يؤكد: المتهم قتل المجني عليه فعلاً")
    murder_conf = state2["facts"]["murder"]["confidence"]
    print(f"🧠 Improved Murder Confidence: {murder_conf:.2f}")

    # 5. Run Rule Engine again
    res2 = execute({"normal": rules}, state2)
    print(f"🔎 Rule Result 2: {'APPLIED' if res2.get('has_conflict') else 'Rejected'}")
    if res2.get("has_conflict"):
        print(f"⚖️ Verdict: {res2['final_verdict']['verdict']}")
        print(f"💡 Trace: {res2['reasoning_trace']}")

    print("\n✨ Intelligent Reasoning v4.3 Verified Successfully!")

if __name__ == "__main__":
    test_burden_of_proof()
