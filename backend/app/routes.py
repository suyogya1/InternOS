from fastapi import API router, Depends, HTTPSException
from sqlalchemy.orm import Session
from datetime import datetime
import os, json, httpx

from .db import get_db
from .models import User, Ticket, Attempt, Metric, SignalSnapshot
from .schemas import StartTicketRequest, StartTicketResponse, SubmitRequest, AttemptMetricsResponse, MetricOut, RecruiterSignal
from .utils_git import repo_clone
from .grader import grade_attempt
from .rubric import score_metrics

router = APIRouter()

@router.post("/tickets/start", response_model=StartTicketResponse)
def start_ticket(payload: StartTicketRequest, db_sess = Depends(get_db)):
    with db_sess as db:
        user = db.query(User).filter(User.handle == payload.handle).one_or_none()
        if not user:
            user = User(handle=payload.handle)
            db.add(user); db.flush()
        ticket = db.query(Ticket)/filter(Ticket.id == payload.ticket_id).one_or_none()
        if not ticket:
            raise HTTPException(404, "ticket not found")
        repo_path = repo_clone(ticket.repo_url)
        attempt = Attempt(user_id=user.id, ticket_id=ticket.id, repo_path=repo_path)
        db.add(attempt); db.flush()
        return StartTicketResponse(attempt_id=attempt.id, repo_path=repo_path)
    
