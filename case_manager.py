import psycopg2
from psycopg2.extras import RealDictCursor, execute_values, register_uuid
import json
from uuid import UUID, uuid4
from typing import List, Dict, Any
from models import Case, Actor, Event, Contradiction
from case_analyzer import DB_PARAMS, extract_state_from_text, get_fact_value, analyze_structured_events
from reasoning_engine import get_engine
from evidence_evaluator import get_evaluator

register_uuid()

class CaseManager:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_PARAMS)
        self.conn.autocommit = True
        self.engine = get_engine()
        self.evaluator = get_evaluator()

    def create_case(self, title: str, summary: str = "") -> UUID:
        with self.conn.cursor() as cur:
            case_id = uuid4()
            cur.execute(
                "INSERT INTO cases (id, title, summary) VALUES (%s, %s, %s) RETURNING id;",
                (case_id, title, summary)
            )
            return cur.fetchone()[0]

    def get_or_create_actor(self, case_id: UUID, name: str, role: str) -> UUID:
        """
        Smart actor resolution: checks for name match or alias match.
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if name is exact or in aliases
            cur.execute(
                "SELECT id FROM actors WHERE case_id = %s AND (name = %s OR %s = ANY(aliases));",
                (case_id, name, name)
            )
            row = cur.fetchone()
            if row:
                return row['id']
            
            # Create new actor
            actor_id = uuid4()
            cur.execute(
                "INSERT INTO actors (id, case_id, name, role, aliases) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
                (actor_id, case_id, name, role, [name])
            )
            return cur.fetchone()['id']

    def add_actor_alias(self, actor_id: UUID, alias: str):
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE actors SET aliases = array_append(aliases, %s) WHERE id = %s AND NOT (%s = ANY(aliases));",
                (alias, actor_id, alias)
            )

    def recompute_case_state(self, case_id: UUID):
        """
        The Judicial Scale Builder v6: Weighted Evidence Aggregation.
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Fetch active events
            cur.execute(
                "SELECT id, event_type, confidence, status FROM events WHERE case_id = %s AND status = 'active';",
                (case_id,)
            )
            events = cur.fetchall()
            
            agg_state = {}
            for ev in events:
                etype = ev['event_type']
                eid = ev['id']
                base_conf = ev['confidence']
                
                # 2. Fetch Evidence Links for this event (v7.0: only active evidence)
                cur.execute(
                    """SELECT e.evidence_type as type, el.corroboration_score 
                       FROM evidence_links el 
                       JOIN evidence e ON el.evidence_id = e.id 
                       WHERE el.event_id = %s AND e.status = 'active';""",
                    (eid,)
                )
                links = cur.fetchall()
                
                # 3. Calculate "Verified Confidence"
                verified_conf = self.evaluator.calculate_fact_strength(base_conf, links)
                
                if etype not in agg_state:
                    agg_state[etype] = {"count": 1, "sum_conf": verified_conf, "max_conf": verified_conf}
                else:
                    agg_state[etype]["count"] += 1
                    agg_state[etype]["sum_conf"] += verified_conf
                    agg_state[etype]["max_conf"] = max(agg_state[etype]["max_conf"], verified_conf)

            # Final state calculation: Weighted Average + Boost for repetition
            new_state = {
                "active_crimes": [],
                "active_defenses": [],
                "facts": {}
            }
            
            CRIMES = ["murder", "assault", "theft", "forgery", "kidnapping"]
            DEFENSES = ["self_defense", "necessity", "juvenile_offender"]

            for etype, data in agg_state.items():
                # Logic: Average + small bonus for multiple sources, capped at 0.99
                avg = data["sum_conf"] / data["count"]
                boost = 0.05 * (data["count"] - 1)
                final_conf = min(0.99, avg + boost)
                
                new_state["facts"][etype] = {"value": True, "confidence": final_conf}
                
                if etype in CRIMES: new_state["active_crimes"].append(etype)
                if etype in DEFENSES: new_state["active_defenses"].append(etype)

            cur.execute(
                "UPDATE cases SET current_state = %s, last_updated_at = CURRENT_TIMESTAMP WHERE id = %s;",
                (json.dumps(new_state), case_id)
            )
            return new_state

    def process_input(self, case_id: UUID, text: str):
        """
        Foundation v2 Pipeline: extract -> link -> save -> recompute
        """
        # 1. Extraction (Using case_analyzer - simplified for Foundation v2)
        fact_state = extract_state_from_text(text)
        
        # 2. Extract & Process Events
        structured_events = analyze_structured_events(text)
        actor_map = {}
        processed_events = []
        
        for a_event in structured_events:
            a_name = a_event["actor"]
            t_name = a_event["target"]
            
            # Determine Roles dynamically
            a_role = "victim" if "المجني عليه" in a_name or any(v in a_name for v in ["محمد", "خالد", "يوسف"]) else "defendant"
            t_role = "victim" if a_role == "defendant" else "defendant"
            
            actor_id = self.get_or_create_actor(case_id, a_name, a_role)
            target_id = self.get_or_create_actor(case_id, t_name, t_role)
            actor_map[a_name] = actor_id
            actor_map[t_name] = target_id
            
            processed_events.append({
                "fact": a_event["event"],
                "a_id": actor_id,
                "t_id": target_id,
                "conf": a_event["confidence"]
            })

        # 3. Save Events
        with self.conn.cursor() as cur:
            for pe in processed_events:
                cur.execute(
                    """INSERT INTO events (case_id, event_type, actor_id, target_id, text_snippet, confidence)
                       VALUES (%s, %s, %s, %s, %s, %s);""",
                    (case_id, pe["fact"], pe["a_id"], pe["t_id"], text[:200], pe["conf"])
                )

        # 4. Check for Contradictions (Simple rule-based)
        self._detect_contradictions(case_id)

        # 5. Recompute Brain State
        current_state = self.recompute_case_state(case_id)
        
        # 6. Digital Judge Inference (Digital Judge v5.1)
        reasoning_result = self.engine.run(case_id, current_state)
        
        return {
            "state": current_state,
            "reasoning": reasoning_result
        }

    def get_digital_verdict(self, case_id: UUID):
        """
        Retrieves the latest reasoning result for a case.
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT current_state FROM cases WHERE id = %s;", (case_id,))
            row = cur.fetchone()
            if row:
                return self.engine.run(case_id, row['current_state'])
        return None

    def get_case_events(self, case_id: UUID) -> List[Dict[str, Any]]:
        """
        Returns all active events for temporal analysis.
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT 
                    e.id,
                    e.event_type as event, 
                    COALESCE(a.name, 'غير محدد') as actor, 
                    COALESCE(t.name, 'غير محدد') as target, 
                    e.text_snippet as text, 
                    e.confidence, 
                    e.sequence_order 
                FROM events e
                LEFT JOIN actors a ON e.actor_id = a.id
                LEFT JOIN actors t ON e.target_id = t.id
                WHERE e.case_id = %s AND e.status = 'active'
                ORDER BY e.sequence_order ASC;
                """,
                (case_id,)
            )
            return cur.fetchall()

    def add_evidence(self, case_id: UUID, e_type: str, description: str, weight: float = 0.5, actor_id: UUID = None) -> UUID:
        with self.conn.cursor() as cur:
            e_id = uuid4()
            cur.execute(
                "INSERT INTO evidence (id, case_id, evidence_type, description, weight, actor_id) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;",
                (e_id, case_id, e_type, description, weight, actor_id)
            )
            return cur.fetchone()[0]

    def link_evidence_to_event(self, evidence_id: UUID, event_id: UUID, score: float = 1.0, role: str = 'corroboration'):
        with self.conn.cursor() as cur:
            link_id = uuid4()
            cur.execute(
                "INSERT INTO evidence_links (id, evidence_id, event_id, corroboration_score, link_role) VALUES (%s, %s, %s, %s, %s);",
                (link_id, evidence_id, event_id, score, role)
            )

    def suppress_evidence_by_type(self, case_id: UUID, origins: List[str]):
        """
        v7.0 Surgical Suppression: Targets evidence produced by illegal systems.
        """
        with self.conn.cursor() as cur:
            # Find evidence linked via PROVENANCE to illegal event types
            cur.execute(
                """
                UPDATE evidence e
                SET status = 'suppressed'
                FROM evidence_links el
                JOIN events ev ON el.event_id = ev.id
                WHERE e.id = el.evidence_id 
                  AND e.case_id = %s 
                  AND ev.event_type = ANY(%s)
                  AND el.link_role = 'provenance';
                """,
                (case_id, origins)
            )

    def _detect_contradictions(self, case_id: UUID):
        # Placeholder for complex contradiction logic (Factual / Temporal)
        pass

    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
