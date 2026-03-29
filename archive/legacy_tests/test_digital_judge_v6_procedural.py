# test_digital_judge_v6_procedural.py
import uuid
from case_manager import CaseManager
import json

def test_procedural_integrity():
    print("⚖️ Digital Judge v6.0: Procedural Integrity Test 🚀")
    manager = CaseManager()
    
    cid = manager.create_case("قضية القتل والبحث الباطل", "Murder case with illegal search (Fruit of the poisonous tree)")
    print(f"⏳ Case Created: {cid}")

    # Step 1: Criminal Act
    print("\n[Step 1] Processing Murder Act...")
    manager.process_input(cid, "أطلق المتهم النار على المجني عليه مما أدى لوفاته في الحال")
    
    # Step 2: Add Evidence (The Gun) via Forensics
    # Let's get the event to link it
    events = manager.get_case_events(cid)
    murder_event_id = None
    for e in events:
        if e['event'] == 'murder':
            # We need the actual UUID, which get_case_events doesn't return currently. 
            # I'll modify CaseManager to be more flexible if needed, 
            # but for this test, I'll just look at the DB.
            pass

    print("[Step 2] Adding Forensic Evidence (The Gun)...")
    # Actually, I'll link to ALL events for simplicity in this test
    e_id = manager.add_evidence(cid, "forensic", "مسدس ماركة حلوان عيار 9 ملم", weight=1.0)
    
    # Step 3: Trigger Procedural Nullity (The Illegal Search)
    print("[Step 3] Processing Procedural Protest (Illegal Search)...")
    result = manager.process_input(cid, "وقع التفتيش باطلاً لعدم استناد مأمور الضبط القضائي لإذن نيابة أو حالة تلبس")
    
    # Show Reasoning
    reasoning = result['reasoning']
    defendants = reasoning.get('defendants', {})
    
    print("\n📜 --- FINAL VERDICT ---")
    for actor_name, verdict in defendants.items():
        if verdict.get('has_conflict'):
            print(f"👤 Defendant: {actor_name}")
            print(f"⚖️ Verdict: {verdict['final_verdict'].get('verdict')}")
            print(f"📖 Law: {verdict['final_verdict'].get('law')} (المادة {verdict['final_verdict'].get('article_number')})")
            
            print("\n🔍 REASONING TRACE:")
            # In the new engine, trace might be in 'reasoning_trace' or similar
            for line in verdict.get('reasoning_trace', []):
                if "Suppression" in line or "Rejected" in line or "✅" in line or "🚫" in line:
                    print(f"  {line}")
        else:
            print(f"👤 Defendant: {actor_name} -> No specific rule matched.")

    print("\n✨ Procedural Integrity Test Complete!")

if __name__ == "__main__":
    test_procedural_integrity()
