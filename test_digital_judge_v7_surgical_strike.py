# test_digital_judge_v7_surgical_strike.py
from case_manager import CaseManager
from uuid import uuid4
import json

def test_v7_surgical_suppression():
    print("⚖️ Digital Judge v7.0: Surgical Suppression Test 🚀")
    manager = CaseManager()
    
    # 1. Setup Case
    cid = manager.create_case("قضية القتل مع الدليل المختلط", "اختبار الاستبعاد الجراحي v7.0")
    print(f"⏳ Case Created: {cid}")

    # 2. Add Murder Event
    print("\n[Step 1] Initial Murder Event...")
    manager.process_input(cid, "قام المتهم بقتل المجني عليه")
    
    # Get the murder event ID to link evidence later
    events = manager.get_case_events(cid)
    murder_ev_id = next(e['id'] for e in events if e['event'] == 'murder')
    
    # 3. Add Illegal Search Event (Procedural Trigger)
    print("[Step 2] Procedural Nullity (Illegal Search)...")
    manager.process_input(cid, "وقع التفتيش باطلاً لعدم وجود إذن نيابة")
    
    # Get the search event ID for PROVENANCE link
    events = manager.get_case_events(cid)
    search_ev_id = next(e['id'] for e in events if e['event'] == 'no_warrant')

    # 4. Add Evidence 1: The Gun (Provenance = Illegal Search)
    print("[Step 3] Adding Illegal Evidence (The Gun)...")
    gun_id = manager.add_evidence(cid, "weapon_found", "مسدس تم العثور عليه في تفتيش باطل", weight=0.9)
    manager.link_evidence_to_event(gun_id, search_ev_id, role='provenance')
    manager.link_evidence_to_event(gun_id, murder_ev_id, score=1.0, role='corroboration')

    # 5. Add Evidence 2: Witness Statement (Provenance = Independent Action)
    print("[Step 4] Adding Independent Evidence (Witness)...")
    witness_id = manager.add_evidence(cid, "testimonial", "شاهد عيان رأى الواقعة قبل التفتيش", weight=0.8)
    # This evidence is NOT linked to the search provenance
    manager.link_evidence_to_event(witness_id, murder_ev_id, score=0.9, role='corroboration')

    # 6. Final Inference
    print("\n📜 --- JUDICIAL INFERENCE (v7.0) ---")
    state = manager.recompute_case_state(cid)
    res = manager.engine.run(cid, state)
    
    for actor, verdict in res['defendants'].items():
        print(f"👤 Defendant: {actor}")
        print(f"⚖️ Verdict: {verdict.get('final_verdict', {}).get('verdict')}")
        print(f"📖 Law: {verdict.get('law')} (المادة {verdict.get('article')})")
        
        print("\n🔍 REASONING TRACE:")
        for t in verdict.get('reasoning_trace', []):
            print(f"  {t}")
            
    print(f"\n🚫 Suppressed Tracks: {res.get('suppressed_tracks')}")
    print("\n✨ v7.0 Surgical Suppression Test Complete!")

if __name__ == "__main__":
    test_v7_surgical_suppression()
