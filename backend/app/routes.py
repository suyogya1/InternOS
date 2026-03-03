import os

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from .db import get_db
from .llm_client import classify_document_with_llm, clean_resume_text_with_llm, generate_llm_review
from .models import Resume, User
from .nlp_pipeline import compute_signals, detect_resume_document
from .resume_parser import extract_resume_text
from .schemas import ResumeSearchResponse, ResumeSearchResult


router = APIRouter()


def _serialize_resume(user: User, resume: Resume) -> ResumeSearchResult:
    nlp = resume.nlp_json or {}
    llm = resume.llm_json or {}
    education = nlp.get("education", {})
    scores = nlp.get("scores", {})

    return ResumeSearchResult(
        handle=user.handle,
        resume_id=resume.id,
        filename=resume.filename,
        uploaded_at=resume.created_at.isoformat(),
        overall_score=float(scores.get("overall", 0.0)),
        matched_skills=list(nlp.get("skills", {}).get("detected", [])),
        missing_skills=list(nlp.get("keywords", {}).get("missing", [])),
        graduated=bool(education.get("graduated", False)),
        graduation_year=education.get("graduation_year"),
        degrees=list(education.get("degrees", [])),
        top_strengths=list(llm.get("top_strengths", [])),
        top_gaps=list(llm.get("top_gaps", [])),
    )


def _latest_resume_rows(db: Session):
    latest_per_user = (
        db.query(Resume.user_id.label("user_id"), func.max(Resume.id).label("resume_id"))
        .group_by(Resume.user_id)
        .subquery()
    )

    return (
        db.query(User, Resume)
        .join(latest_per_user, latest_per_user.c.user_id == User.id)
        .join(Resume, Resume.id == latest_per_user.c.resume_id)
        .order_by(Resume.id.desc())
        .all()
    )


def _matches_candidate_query(query: str, user: User, resume: Resume) -> bool:
    normalized_query = " ".join(query.lower().split())
    if not normalized_query:
        return False

    nlp = resume.nlp_json or {}
    identity = nlp.get("identity", {})
    name = str(identity.get("name") or "").lower()
    handle = str(user.handle or "").lower()

    haystacks = [handle, name]
    tokens = [token for token in normalized_query.split() if token]

    for haystack in haystacks:
        if normalized_query in haystack:
            return True
        if tokens and all(token in haystack for token in tokens):
            return True

    return False


def _unique_handle(db: Session, base_handle: str) -> str:
    handle = base_handle
    suffix = 2
    while db.query(User).filter(User.handle == handle).one_or_none():
        handle = f"{base_handle}-{suffix}"
        suffix += 1
    return handle


@router.post("/resumes/analyze")
async def analyze_resume(
    target_role: str = Form("Software Engineering Intern"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    data = await file.read()
    if not file.filename:
        raise HTTPException(400, "filename is required")
    if not data:
        raise HTTPException(400, "uploaded file is empty")

    try:
        text = extract_resume_text(file.filename, data)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(400, f"could not parse resume: {exc}") from exc

    if not text.strip():
        raise HTTPException(400, "resume text could not be extracted")

    document_check = detect_resume_document(text)
    if 0.35 <= float(document_check.get("confidence", 0.0)) <= 0.75:
        llm_check = classify_document_with_llm(text, file.filename)
        if llm_check.get("is_resume") is not None:
            document_check = {
                "is_resume": bool(llm_check.get("is_resume")),
                "document_type": llm_check.get("document_type", document_check.get("document_type", "unknown")),
                "confidence": float(llm_check.get("confidence", document_check.get("confidence", 0.0))),
                "reason": llm_check.get("reason") or document_check.get("reason", ""),
                "used_llm": bool(llm_check.get("used_llm")),
            }
    else:
        document_check["used_llm"] = False

    if not bool(document_check.get("is_resume", False)):
        reason = document_check.get("reason") or "The uploaded file does not look like a resume."
        raise HTTPException(400, f"document rejected: {reason}")

    cleanup = clean_resume_text_with_llm(text, file.filename)
    cleaned_text = cleanup.get("clean_text") or text
    extracted_facts = cleanup.get("facts") or {}

    nlp_profile = compute_signals(
        cleaned_text,
        target_role=target_role,
        filename=file.filename,
        facts=extracted_facts,
    )
    nlp_profile["extraction"] = {
        "used_llm_cleanup": bool(cleanup.get("used_llm")),
        "cleanup_source": cleanup.get("source", "stub"),
    }
    nlp_profile["document_check"] = document_check
    identity = nlp_profile.get("identity", {})
    derived_handle = identity.get("derived_handle") or "candidate"
    user = db.query(User).filter(User.handle == derived_handle).one_or_none()
    if not user:
        user = User(handle=_unique_handle(db, derived_handle))
        db.add(user)
        db.flush()

    llm_review = generate_llm_review(nlp_profile, text)

    resume = Resume(
        user_id=user.id,
        filename=file.filename,
        text=cleaned_text,
        nlp_json=nlp_profile,
        llm_json=llm_review,
    )
    db.add(resume)
    db.flush()

    hook = os.getenv("N8N_WEBHOOK_URL", "")
    if hook:
        try:
            httpx.post(
                hook,
                json={
                    "type": "resume_analysis",
                    "handle": user.handle,
                    "resume_id": resume.id,
                    "target_role": target_role,
                    "nlp": nlp_profile,
                    "llm": llm_review,
                },
                timeout=10,
            )
        except Exception:
            pass

    return {
        "handle": user.handle,
        "resume_id": resume.id,
        "filename": resume.filename,
        "nlp": nlp_profile,
        "llm": llm_review,
    }


@router.get("/resumes/{handle}/latest")
def resume_latest(handle: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.handle == handle).one_or_none()
    if not user:
        raise HTTPException(404, "user not found")

    latest = db.query(Resume).filter(Resume.user_id == user.id).order_by(Resume.id.desc()).first()
    if not latest:
        raise HTTPException(404, "no resume uploaded")

    return {
        "handle": handle,
        "resume_id": latest.id,
        "filename": latest.filename,
        "nlp": latest.nlp_json,
        "llm": latest.llm_json,
    }


@router.get("/resumes/find")
def find_resume(query: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    rows = _latest_resume_rows(db)
    matches = [(user, resume) for user, resume in rows if _matches_candidate_query(query, user, resume)]
    if not matches:
        raise HTTPException(404, "no matching candidate found")

    user, latest = matches[0]
    return {
        "handle": user.handle,
        "resume_id": latest.id,
        "filename": latest.filename,
        "nlp": latest.nlp_json,
        "llm": latest.llm_json,
        "match_count": len(matches),
        "matches": [
            {
                "handle": match_user.handle,
                "name": (match_resume.nlp_json or {}).get("identity", {}).get("name"),
                "filename": match_resume.filename,
            }
            for match_user, match_resume in matches[:10]
        ],
    }


@router.get("/resumes/search", response_model=ResumeSearchResponse)
def search_resumes(
    required_skills: str = Query("", description="Comma-separated required skills"),
    graduated: bool | None = Query(default=None),
    degree_query: str = Query("", description="Match degree names"),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = _latest_resume_rows(db)

    required = [skill.strip().lower() for skill in required_skills.split(",") if skill.strip()]
    degree_query_norm = degree_query.strip().lower()
    results = []

    for user, resume in rows:
        nlp = resume.nlp_json or {}
        skills = [skill.lower() for skill in nlp.get("skills", {}).get("detected", [])]
        education = nlp.get("education", {})
        degrees = [degree.lower() for degree in education.get("degrees", [])]
        overall_score = float(nlp.get("scores", {}).get("overall", 0.0))

        if required and not all(skill in skills for skill in required):
            continue
        if graduated is not None and bool(education.get("graduated", False)) != graduated:
            continue
        if degree_query_norm and not any(degree_query_norm in degree for degree in degrees):
            continue
        if overall_score < min_score:
            continue

        results.append(_serialize_resume(user, resume))
        if len(results) >= limit:
            break

    return ResumeSearchResponse(
        total=len(results),
        filters={
            "required_skills": required,
            "graduated": graduated,
            "degree_query": degree_query_norm or None,
            "min_score": min_score,
            "limit": limit,
        },
        results=results,
    )
