from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime

class StartTicketRequest(BaseModel):
    handle: str
    ticket_id: int

class StartTicketResponse(BaseModel):
    attempt_id: int
    repo_path: str

class SubmitRequest(BaseModel):
    attempt_id: int
    pr_url: Optional[str] = None
    standup_text: Optional[str] = None
    postmortem_text: Optional[str] = None

class MetricOut(BaseModel):
    key: str
    value: float
    extra: Optional[Dict[str, Any]] = None

class AttemptMetricsResponse(BaseModel):
    attempt_id: int
    status: str
    metrics: List[MetricOut]

class RecruiterSignal(BaseModel):
    handle: str
    snapshot: Dict[str, Any]

    