import re
import json
import hashlib

class LegalMemory:
    """
    الذاكرة النشطة للمحرك (v4.1)
    تدير السجل الحي للأحداث وحل التعارضات "على الهواء"
    """
    def __init__(self):
        self.registry = {} # {fingerprint: event_object}
        self.conflicts = [] # سجل التعارضات للمراجعة
        self.memo_sections = {
            "procedure": {"score": -1, "txt": ""},
            "murder": {"score": -1, "txt": ""},
            "theft": {"score": -1, "txt": ""},
            "other": {"score": -1, "txt": ""}
        }

    def get_event(self, fp):
        return self.registry.get(fp)

    def set_event(self, fp, event):
        self.registry[fp] = event

    def add_conflict(self, fp, ev1, ev2, winner):
        self.conflicts.append({
            "fp": fp,
            "verdicts": [ev1.get("verdict"), ev2.get("verdict")],
            "winner": winner.get("verdict")
        })

class AggregationRefiner:
    """
    مصفي التكرار والتعارض (v4.1)
    """
    LEGAL_PRIORITY = {
        "procedure": 3,
        "override": 2, # (acquittal/necessity)
        "normal": 1,   # (conviction)
        "contradiction": 0
    }

    @staticmethod
    def generate_fingerprint_v2(ev: dict):
        action = ev.get("applied_type", "unknown")
        # Ensure facts are sorted
        facts = tuple(sorted(ev.get("active_facts", {}).keys()))
        verdict = ev.get("verdict", "none")
        
        # Finer buckets: 500 chars (approx 70-100 words)
        raw_idx = ev.get("start_index", 0)
        try:
            idx = int(raw_idx)
        except:
            idx = 0
        time_hint = idx // 400 
        
        fingerprint_data = f"{action}|{facts}|{verdict}|{time_hint}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()

    def resolve_conflict(self, existing: dict, new: dict):
        s1 = float(existing.get("score", 0))
        s2 = float(new.get("score", 0))
        
        p1 = self.LEGAL_PRIORITY.get(existing.get("applied_type", "normal"), 1)
        p2 = self.LEGAL_PRIORITY.get(new.get("applied_type", "normal"), 1)

        if abs(s1 - s2) > 0.20:
            return existing if s1 > s2 else new
        
        return existing if p1 >= p2 else new

class LongCasePipeline:
    """
    معمارية معالجة القضايا الطويلة (v4.1 STATEFUL)
    """
    def __init__(self):
        self.memory = LegalMemory()
        self.refiner = AggregationRefiner()

    def is_phantom(self, ev: dict):
        has_facts = len(ev.get("active_facts", {})) > 0
        score = float(ev.get("score", 0))
        atype = ev.get("applied_type", "normal")
        
        # Preserve overrides (Self-Defense, Necessity) and procedures (Nullity) even if score is low
        if atype in ("override", "procedure"):
            return False
            
        # Standard filter for normal/contradiction events
        if score > 0.05 or has_facts:
            return False
        return True

    def run(self, case_text: str, debug=False):
        from case_analyzer import analyze_events, JUDICIAL_TEMPLATES
        
        # 1. Sliding Window processing
        words = case_text.split()
        size, overlap = 1200, 400
        windows = []
        for i in range(0, len(words), size - overlap):
            windows.append(" ".join(words[i : i + size]))
            if i + size >= len(words): break

        if debug: print(f"🚀 V4.1 Pipeline Active. Case: {len(words)} words. Windows: {len(windows)}")

        for w_idx, win in enumerate(windows):
            res = analyze_events(win, debug=debug)
            if debug: print(f"Window [{w_idx+1}] extracted {len(res.get('events', []))} events.")
            
            for ev in res.get("events", []):
                # Detailed diagnostic
                if self.is_phantom(ev):
                    if debug: print(f"  - Phantom Filtered: {ev.get('verdict')} (Score: {ev.get('score')})")
                    continue
                
                fp = self.refiner.generate_fingerprint_v2(ev)
                existing = self.memory.get_event(fp)
                if existing:
                    winner = self.refiner.resolve_conflict(existing, ev)
                    if debug: print(f"  - Conflict Resolver at {fp}: winner={winner.get('verdict')}")
                    self.memory.add_conflict(fp, existing, ev, winner)
                    self.memory.set_event(fp, winner)
                else:
                    if debug: print(f"  - Event Stored: {ev.get('verdict')} facts={list(ev.get('active_facts', {}).keys())}")
                    self.memory.set_event(fp, ev)

        # 5. Final Aggregation from Memory
        unique_events = list(self.memory.registry.values())
        if debug: print(f"Final Deduplicated Events: {len(unique_events)}")

        # 6. Categorized Memo Cleanup
        memo_storage = {
            "procedure": {"score": -2, "txt": ""},
            "murder": {"score": -2, "txt": ""},
            "theft": {"score": -2, "txt": ""},
            "other": {"score": -2, "txt": ""}
        }
        
        for ev in unique_events:
            atype = ev.get("applied_type", "other")
            score = float(ev.get("score", 0))
            txt = ev.get("judicial_judgment", "")
            if not txt: continue
            
            cat = "other"
            if atype == "procedure" or "بطلان" in txt: cat = "procedure"
            elif "قتل" in txt or "إعدام" in txt: cat = "murder"
            elif "سرقة" in txt or "اختلاس" in txt: cat = "theft"
            
            if score >= memo_storage[cat]["score"]:
                memo_storage[cat]["score"] = score
                memo_storage[cat]["txt"] = txt

        # Assemble result
        parts = []
        for c in ["procedure", "murder", "theft", "other"]:
            if memo_storage[c]["txt"]: parts.append(memo_storage[c]["txt"])
            
        final_judgment = "\n\n".join(parts)
        if final_judgment:
            final_judgment += "\n\n" + JUDICIAL_TEMPLATES["general_conviction"]

        unique_v = list(set(e["verdict"] for e in unique_events if e.get("verdict")))

        return {
            "events": unique_events,
            "total_events": len(unique_events),
            "final_summary": " | ".join(unique_v) if unique_v else "لا وقائع محددة",
            "all_verdicts": unique_v,
            "judicial_judgment": final_judgment
        }

def execute_pipeline_v4(text: str, debug=False):
    pipeline = LongCasePipeline()
    return pipeline.run(text, debug=debug)
