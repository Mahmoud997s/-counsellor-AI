# models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class Actor(BaseModel):
    id: Optional[UUID] = None
    case_id: UUID
    name: str
    role: str # defendant, plaintiff, witness, etc.
    aliases: List[str] = []
    metadata: Dict[str, Any] = {}
    created_at: Optional[datetime] = None

class Event(BaseModel):
    id: UUID
    case_id: UUID
    event_type: str
    actor_id: Optional[UUID] = None
    target_id: Optional[UUID] = None
    text_snippet: Optional[str] = None
    confidence: float = 1.0
    status: str = "active"
    sequence_order: int = 0
    causes_id: Optional[UUID] = None
    contradicts_id: Optional[UUID] = None
    created_at: datetime

class Case(BaseModel):
    id: UUID
    title: str
    summary: Optional[str] = None
    current_state: Dict[str, Any] = {
        "active_crimes": [],
        "active_defenses": [],
        "facts": {} # {fact_name: {value: bool, confidence: float}}
    }
    created_at: datetime

class Contradiction(BaseModel):
    id: Optional[UUID] = None
    case_id: UUID
    event_a_id: UUID
    event_b_id: UUID
    contradiction_type: str # factual, temporal, legal
    resolved: bool = False
    created_at: Optional[datetime] = None

class Evidence(BaseModel):
    id: Optional[UUID] = None
    case_id: UUID
    type: str # forensic, digital, testimonial, physical
    description: str
    weight: float = 0.5
    actor_id: Optional[UUID] = None # Link to witness/expert
    created_at: Optional[datetime] = None

class EvidenceLink(BaseModel):
    id: Optional[UUID] = None
    evidence_id: UUID
    event_id: UUID
    corroboration_score: float = 1.0 # 1.0 = supports, -1.0 = contradicts

class Case(BaseModel):
    id: Optional[UUID] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    current_state: Dict[str, Any] = {}
    importance_score: float = 0.0
    status: str = "open"
    last_updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
