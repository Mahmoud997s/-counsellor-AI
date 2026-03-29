# temporal_engine.py
import re
from typing import List, Dict, Any

class TemporalEngine:
    # Arabic temporal markers with their chronological influence
    # Positive: happened after previous event, Negative: happened before previous event
    MARKERS = {
        r"بعد ذلك|عقب ذلك|تلا ذلك|ثم|لاحقا|بعد قليل": 1,
        r"قبل ذلك|سابقا|تمهيدا|من قبل|كان يسبقها": -1,
        r"في ذات الوقت|متزامنا|بينما": 0
    }

    def sort_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Refines event order by balancing DB sequence vs NLP Temporal Keywords.
        """
        if not events: return []
        
        # Initial ranking based on DB sequence_order (extracted from text position)
        ranked_events = sorted(events, key=lambda e: e.get("sequence_order", 0))
        
        # Adjust rank based on keywords in text snippet
        for i in range(1, len(ranked_events)):
            text = ranked_events[i].get("text", "").lower()
            current_order = ranked_events[i].get("sequence_order", i)
            
            for pattern, weight in self.MARKERS.items():
                if re.search(pattern, text):
                    # If keyword says "before", we swap/decrement its virtual order
                    if weight == -1:
                        ranked_events[i]["virtual_order"] = current_order - 1.5
                    elif weight == 1:
                        ranked_events[i]["virtual_order"] = current_order + 0.5
                    break
            else:
                ranked_events[i]["virtual_order"] = current_order

        if "virtual_order" not in ranked_events[0]:
            ranked_events[0]["virtual_order"] = ranked_events[0].get("sequence_order", 0)

        return sorted(ranked_events, key=lambda e: e.get("virtual_order", 0))

    def detect_gaps(self, sorted_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detects if there is a significant temporal gap (e.g., 'بعد ساعة').
        Delayed responses (after hour/day) usually void self-defense.
        """
        for e in sorted_events:
            text = e.get("text", "")
            if re.search(r"بعد ساعة|بعد يوم|بعد فترة|لاحقا", text):
                e["is_delayed"] = True
            else:
                e["is_delayed"] = False
        return sorted_events

def get_temporal_engine():
    return TemporalEngine()
