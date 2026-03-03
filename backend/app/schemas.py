from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ResumeSearchResult(BaseModel):
    handle: str
    name: Optional[str] = None
    resume_id: int
    filename: str
    uploaded_at: str
    overall_score: float
    clarity_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    graduated: bool
    graduation_year: Optional[int] = None
    degrees: List[str]
    top_strengths: List[str]
    top_gaps: List[str]


class ResumeSearchResponse(BaseModel):
    total: int
    filters: Dict[str, Any]
    results: List[ResumeSearchResult]
