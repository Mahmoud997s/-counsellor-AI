from typing import Dict, Any, List
from temporal_engine import get_temporal_engine

class SemanticInterpreter:
    ACTION_WEIGHTS = {
        "shout": 0.1, "push": 0.2, "threat": 0.4, "assault": 0.6, "murder": 1.0
    }
    WEAPON_WEIGHTS = {
        "fist": 0.1, "stick": 0.3, "knife": 0.7, "gun": 1.0, "none": 0.1
    }

    def __init__(self):
        self.temporal = get_temporal_engine()

    def interpret(self, raw_state: Dict[str, Any], raw_events: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Refined Stage 1: Concepts & Stage 2: Findings.
        """
        # 0. Temporal Reconstruction
        sorted_events = self.temporal.sort_events(raw_events or [])
        sorted_events = self.temporal.detect_gaps(sorted_events)
        
        facts = raw_state.get("facts", {})

        # 0.5. Building LOCAL Fact View (Isolation Layer)
        # Instead of global raw_state, we look at only what this actor DID and SAW.
        local_facts = {}
        for ev in sorted_events:
            etype = ev.get("event")
            if etype not in local_facts:
                local_facts[etype] = {"count": 1, "confidence": 0.9}
            else:
                local_facts[etype]["count"] += 1

        # 1. Findings: Initial Aggressor
        initial_aggressor = None
        for e in sorted_events:
            etype = e.get("event")
            if etype in ("assault", "murder", "theft", "imminent_danger", "by_force"):
                # If the event is 'imminent_danger' from the Target to the Actor
                # We need to see who is the AGGRESSOR for it to be a defense
                initial_aggressor = e.get("actor")
                break
        
        # 2. Findings: Force Proportionality
        # Calculate THREAT Force (Incoming - what the target did to the actor)
        incoming_events = [e for e in sorted_events if e.get("actor") != raw_state.get("current_actor")]
        threat_action_w = 0.4 if any(e['event'] in ["imminent_danger", "by_force"] for e in incoming_events) else 0.1
        threat_weapon_w = 0.7 if any(e['event'] == "weapon_used" for e in incoming_events) else 0.1
        threat_force = threat_action_w * threat_weapon_w

        # Defense / Aggressive Force (Outgoing - what the actor did)
        outgoing_events = [e for e in sorted_events if e.get("actor") == raw_state.get("current_actor")]
        agg_action_w = 1.0 if "murder" in local_facts else (0.6 if "assault" in local_facts else 0.1)
        agg_weapon_w = 1.0 if "weapon_used" in local_facts else 0.1
        defense_force = agg_action_w * agg_weapon_w
        
        # Effective force ratio
        force_ratio = defense_force / (threat_force or 0.1)
        force_tier = "justified" if force_ratio <= 1.5 else ("excessive" if force_ratio <= 3.0 else "extreme_excess")
        
        # 3. Findings: Immediacy
        has_gap = any(e.get("is_delayed", False) for e in sorted_events)
        immediate_threat = (threat_force > 0.1) and not has_gap
        
        # 4. Legal Concepts (Scoped to this actor's actions)
        violence_score = 1.0 if "murder" in local_facts else (0.6 if "assault" in local_facts else 0.1)
        
        has_intent = "intent" in local_facts or "premeditation" in local_facts or (violence_score > 0.8)
        
        concepts = {
            "violence_score": violence_score,
            "lethal_intent": has_intent,
            "procedural_error": raw_state.get("facts", {}).get("nullity_procedural", {}).get("confidence", 0) > 0.6
        }

        return {
            "concepts": concepts,
            "findings": {
                "initial_aggressor": initial_aggressor or "غير محدد",
                "force_ratio": force_ratio,
                "force_tier": force_tier,
                "immediate_threat": immediate_threat,
                "proportional_response": force_tier == "justified",
                "delayed_response": has_gap
            },
            "raw_facts": facts
        }

def get_interpreter():
    return SemanticInterpreter()
