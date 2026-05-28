from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    response: str
    sources: list[str]
    session_id: str
    provider: str
    lead_captured: bool = False


class Lead(BaseModel):
    session_id: str
    captured_at: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    concerns: list[str] = []
    treatments_interested: list[str] = []
    is_first_time: Optional[bool] = None
    passed_candidacy: Optional[bool] = None
    preferred_date: Optional[str] = None
    timeline: Optional[str] = None
    budget_range: Optional[str] = None
    score: int = 0
    score_reasoning: str = ""
    status: str = "new"
    conversation_summary: str = ""


class LeadListResponse(BaseModel):
    total: int
    leads: list[Lead]


class ContactRequest(BaseModel):
    session_id: str
    name: str
    email: str
    phone: Optional[str] = None


class StatusUpdateRequest(BaseModel):
    status: str
