import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .db import get_db
from .models import User, Ticket, Attempt, Metric, SignalSnapshot
from .schemas import (
    StartTicketRequest,
    StartTicketResponse,
    SubmitRequest,
    AttemptMetricsResponse,
    MetricOut,
    RecruiterSignal,
)
from .utils_git import repo_clone
from .grader import grade_attempt
from .rubric import score_metrics

router = APIRouter()


@router.post("/tickets/start", response_model=StartTicketResponse)
def start_ticket(payload: StartTicketRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.handle == payload.handle).one_or_none()
    if not user:
        user = User(handle=payload.handle)
        db.add(user)
        db.flush()

    ticket = db.query(Ticket).filter(Ticket.id == payload.ticket_id).one_or_none()
    if not ticket:
        raise HTTPException(404, "ticket not found")

    repo_path = repo_clone(ticket.repo_url)
    attempt = Attempt(user_id=user.id, ticket_id=ticket.id, repo_path=repo_path)
    db.add(attempt)
    db.flush()

    return StartTicketResponse(attempt_id=attempt.id, repo_path=repo_path)


@router.post("/tickets/submit")
def submit_attempt(payload: SubmitRequest, db: Session = Depends(get_db)):
    attempt = db.query(Attempt).filter(Attempt.id == payload.attempt_id).one_or_none()
    if not attempt:
        raise HTTPException(404, "attempt not found")

    if attempt.status not in ("in_progress", "submitted"):
        raise HTTPException(400, "attempt already graded")

    from datetime import datetime

    attempt.finished_at = datetime.utcnow()
    attempt.status = "submitted"

    scores = grade_attempt(
        db,
        attempt,
        submitted_at=attempt.finished_at.timestamp(),
        pr_url=payload.pr_url,
        standup_text=payload.standup_text,
        postmortem_text=payload.postmortem_text,
    )

    # Optional n8n webhook
    hook = os.getenv("N8N_WEBHOOK_URL")
    if hook:
        try:
            metrics = {m.key: m.value for m in attempt.metrics}
            data = {
                "attempt_id": attempt.id,
                "user": attempt.user_id,
                "ticket": attempt.ticket_id,
                "scores": scores,
                "metrics": metrics,
                "submitted_at": attempt.finished_at.isoformat(),
            }
            httpx.post(hook, json=data, timeout=5)
        except Exception:
            # keep silent on webhook issues
            pass

    return {"attempt_id": attempt.id, "scores": scores}


@router.get("/attempts/{attempt_id}/metrics", response_model=AttemptMetricsResponse)
def get_metrics(attempt_id: int, db: Session = Depends(get_db)):
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).one_or_none()
    if not attempt:
        raise HTTPException(404, "attempt not found")

    ms = [MetricOut(key=m.key, value=m.value, extra=m.extra) for m in attempt.metrics]
    return AttemptMetricsResponse(attempt_id=attempt.id, status=attempt.status, metrics=ms)


@router.get("/recruiter/{handle}", response_model=RecruiterSignal)
def recruiter_view(handle: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.handle == handle).one_or_none()
    if not user:
        raise HTTPException(404, "user not found")

    # Collect attempts and aggregate metrics (simple average for MVP)
    rows = db.query(Attempt).filter(Attempt.user_id == user.id).all()
    all_metrics = {}
    for a in rows:
        for m in a.metrics:
            all_metrics.setdefault(m.key, []).append(m.value)

    agg = {k: sum(v) / len(v) for k, v in all_metrics.items() if v}
    scores = score_metrics(agg)

    snapshot = {
        "summary": {
            "tickets_shipped": len(rows),
            "coverage": round(agg.get("coverage", 0.0), 3),
            "lint_errors": round(agg.get("lint_errors", 0.0), 2),
            "avg_cyclomatic": round(agg.get("avg_cyclomatic", 0.0), 2),
            "pr_size": round(agg.get("pr_size", 0.0), 1),
            "scores": scores,
        },
    }

    db.add(SignalSnapshot(user_id=user.id, snapshot_json=snapshot))

    return RecruiterSignal(handle=handle, snapshot=snapshot)
