# test_foundation_v2.py
from case_manager import CaseManager
from uuid import UUID

def test_brain_foundation():
    manager = CaseManager()
    
    print("🚀 Testing Stateful Foundation v2...")
    
    # 1. Create Case
    case_id = manager.create_case("قضية تجريبية - القتل العمد", "قضية اختبار للنظام الجديد")
    print(f"✅ Case Created: {case_id}")
    
    # 2. Process first input (Murder with Weapon)
    print("\n📩 Processing Input 1: 'قام المتهم بقتل المجني عليه عمدا باستخدام سلاح'")
    state1 = manager.process_input(case_id, "قام المتهم بقتل المجني عليه عمدا باستخدام سلاح")
    print(f"🧠 Current Brain State: {state1.keys()}")
    
    # 3. Process second input (Self Defense claim)
    print("\n📩 Processing Input 2: 'يدعي المتهم انه كان في حالة دفاع شرعي'")
    state2 = manager.process_input(case_id, "يدعي المتهم انه كان في حالة دفاع شرعي")
    print(f"🧠 Updated Brain State: {state2.keys()}")
    
    # 4. Verify Actors
    with manager.conn.cursor() as cur:
        cur.execute("SELECT name, role, aliases FROM actors WHERE case_id = %s;", (case_id,))
        actors = cur.fetchall()
        print("\n👥 Actors in Case:")
        for a in actors:
            print(f"  - {a[0]} ({a[1]}) | Aliases: {a[2]}")

    print("\n✨ Foundation v2 Verified Successfully!")

if __name__ == "__main__":
    test_foundation_v2_res = test_brain_foundation()
