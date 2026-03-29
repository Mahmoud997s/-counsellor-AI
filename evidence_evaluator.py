# evidence_evaluator.py
from typing import List, Dict, Any
from uuid import UUID

class EvidenceEvaluator:
    """
    The Judicial Scale: Weighs evidence types to produce a final 'Fact Strength'.
    """
    TYPE_WEIGHTS = {
        "forensic": 1.0,    # DNA, autopsy, ballistics
        "digital": 0.9,     # CCTV, GPS, phone data
        "physical": 0.8,    # Weapons, fingerprints
        "confession": 0.85, # Self-incrimination (un-coerced)
        "testimonial": 0.6  # Eye-witness accounts (highest risk of error)
    }

    def calculate_fact_strength(self, base_confidence: float, evidence_links: List[Dict[str, Any]]) -> float:
        """
        Calculates a 'Verified Confidence' score.
        score = base_conf + (weight_sum / n) * bonus_factor
        """
        if not evidence_links:
            return base_confidence * 0.8 # Penalize uncorroborated facts

        total_weight = 0
        contradiction_penalty = 1.0
        
        for link in evidence_links:
            type_w = self.TYPE_WEIGHTS.get(link.get("type"), 0.5)
            # Corroboration vs Contradiction
            # link["corroboration_score"] is 1.0 (supports) or -1.0 (contradicts)
            c_score = link.get("corroboration_score", 1.0)
            
            if c_score > 0:
                total_weight += type_w
            else:
                contradiction_penalty *= (1.0 - (type_w * 0.5))

        # Average influence of evidence
        avg_weight = total_weight / len(evidence_links)
        
        # New confidence: weighted towards evidence
        effective_conf = (base_confidence * 0.4) + (avg_weight * 0.6)
        
        # Apply penalty for contradictions
        final_score = min(1.0, effective_conf * contradiction_penalty)
        return round(final_score, 3)

def get_evaluator():
    return EvidenceEvaluator()
