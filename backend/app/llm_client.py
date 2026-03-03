import os

import httpx


def _score_band(value: float) -> str:
    if value >= 0.8:
        return "strong"
    if value >= 0.6:
        return "good"
    if value >= 0.4:
        return "mixed"
    return "weak"


def llm_review_stub(profile: dict, resume_text: str) -> dict:
    gaps = []
    if not profile["links"]["github"]:
        gaps.append("Add a GitHub link so recruiters can review project work.")
    if profile["bullets"]["with_numbers"] == 0:
        gaps.append("Add numbers to achievements so impact is easier to understand.")
    if not profile["sections"].get("projects", False):
        gaps.append("Add a projects section with 2 or 3 strong examples.")
    missing = profile["keywords"]["missing"][:6]
    if missing:
        gaps.append(f"Important keywords missing for this role: {', '.join(missing)}.")

    strengths = []
    if profile["keywords"]["matched"]:
        strengths.append(f"Relevant skills found: {', '.join(profile['keywords']['matched'][:6])}.")
    if profile["links"]["linkedin"]:
        strengths.append("LinkedIn is included.")
    if profile["bullets"]["verb_first"] >= 3:
        strengths.append("Experience bullets use clear action-oriented language.")

    score = float(profile.get("scores", {}).get("overall", 0.0))
    target_role = profile.get("target_role", "the target role")
    summary = (
        f"This resume looks {_score_band(score)} for {target_role.lower()}. "
        f"It shows some relevant experience, but a few details could be clearer for recruiters."
    )

    return {
        "summary": summary,
        "top_strengths": strengths[:3],
        "top_gaps": gaps[:4],
        "recommended_edits": gaps[:3],
        "confidence": 0.55,
    }


def llm_review_http(profile: dict, resume_text: str) -> dict:
    """
    Generic HTTP LLM call (you provide endpoint & key).
    Expect the endpoint to return JSON {"review": {...}}.
    """
    url = os.getenv("LLM_HTTP_URL", "")
    key = os.getenv("LLM_HTTP_KEY", "")
    if not url:
        return llm_review_stub(profile, resume_text)

    payload = {
        "profile": profile,
        "resume_text": resume_text[:20000],
        "instructions": "Return JSON: {review:{summary,top_strengths,top_gaps,recommended_edits,confidence}}",
    }
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    response = httpx.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data.get("review") or llm_review_stub(profile, resume_text)


def resume_cleanup_stub(resume_text: str, filename: str) -> dict:
    return {
        "clean_text": resume_text,
        "facts": {},
        "used_llm": False,
        "source": "stub",
    }


def resume_cleanup_http(resume_text: str, filename: str) -> dict:
    url = os.getenv("LLM_HTTP_URL", "")
    key = os.getenv("LLM_HTTP_KEY", "")
    if not url:
        return resume_cleanup_stub(resume_text, filename)

    payload = {
        "filename": filename,
        "resume_text": resume_text[:24000],
        "instructions": (
            "You receive OCR-extracted resume text that may contain errors. "
            "Return compact JSON with the exact shape "
            "{\"clean_text\": string, \"facts\": {"
            "\"name\": string|null, "
            "\"email\": string|null, "
            "\"graduated\": boolean|null, "
            "\"graduation_year\": number|null, "
            "\"degrees\": string[], "
            "\"skills\": string[], "
            "\"skill_groups\": object, "
            "\"expected_graduation\": boolean|null"
            "}}. "
            "Fix obvious OCR mistakes, preserve resume meaning, and do not invent facts."
        ),
    }
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    response = httpx.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    data = response.json()
    return {
        "clean_text": data.get("clean_text") or resume_text,
        "facts": data.get("facts") or {},
        "used_llm": True,
        "source": "http",
    }


def clean_resume_text_with_llm(resume_text: str, filename: str) -> dict:
    mode = os.getenv("LLM_MODE", "stub").lower()
    if mode == "http":
        return resume_cleanup_http(resume_text, filename)
    return resume_cleanup_stub(resume_text, filename)


def document_classifier_stub(text: str, filename: str) -> dict:
    return {
        "is_resume": None,
        "document_type": "unknown",
        "confidence": 0.0,
        "reason": "LLM classifier is not configured.",
        "used_llm": False,
    }


def document_classifier_http(text: str, filename: str) -> dict:
    url = os.getenv("LLM_HTTP_URL", "")
    key = os.getenv("LLM_HTTP_KEY", "")
    if not url:
        return document_classifier_stub(text, filename)

    payload = {
        "filename": filename,
        "document_text": text[:20000],
        "instructions": (
            "Classify whether this document is a candidate resume/CV. "
            "Return compact JSON with exact shape "
            "{\"is_resume\": boolean|null, "
            "\"document_type\": string, "
            "\"confidence\": number, "
            "\"reason\": string}. "
            "Use document_type values like resume, cover_letter, invoice, contract, form, essay, unknown. "
            "Do not invent facts."
        ),
    }
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    response = httpx.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    data = response.json()
    return {
        "is_resume": data.get("is_resume"),
        "document_type": data.get("document_type") or "unknown",
        "confidence": float(data.get("confidence", 0.0) or 0.0),
        "reason": data.get("reason") or "",
        "used_llm": True,
    }


def classify_document_with_llm(text: str, filename: str) -> dict:
    mode = os.getenv("LLM_MODE", "stub").lower()
    if mode == "http":
        return document_classifier_http(text, filename)
    return document_classifier_stub(text, filename)


def generate_llm_review(profile: dict, resume_text: str) -> dict:
    mode = os.getenv("LLM_MODE", "stub").lower()
    if mode == "http":
        return llm_review_http(profile, resume_text)
    return llm_review_stub(profile, resume_text)
