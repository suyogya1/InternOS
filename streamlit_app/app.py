import os
import json
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


st.set_page_config(page_title="InternOS Recruiter", page_icon="briefcase", layout="wide")
st.markdown(
    """
    <style>
    div[data-baseweb="slider"] [role="slider"] {
        transition: transform 120ms ease, box-shadow 120ms ease, background-color 120ms ease;
    }
    div[data-baseweb="slider"] [role="slider"]:hover {
        transform: scale(1.05);
        box-shadow: 0 0 0 6px rgba(56, 189, 248, 0.12);
    }
    div[data-baseweb="slider"] > div {
        transition: all 160ms ease;
    }
    div[data-testid="stMetric"] {
        transition: transform 140ms ease, border-color 140ms ease, background-color 140ms ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-1px);
    }
    .candidate-chip {
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 16px;
        padding: 0.85rem 1rem;
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.88), rgba(2, 6, 23, 0.96));
        box-shadow: 0 14px 30px rgba(2, 6, 23, 0.22);
        transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
        margin-bottom: 0.35rem;
    }
    .candidate-chip:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.45);
        box-shadow: 0 18px 34px rgba(8, 47, 73, 0.28);
    }
    .candidate-chip__name {
        font-size: 1.02rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0.2rem;
    }
    .candidate-chip__meta {
        font-size: 0.84rem;
        color: #cbd5e1;
        line-height: 1.55;
    }
    .candidate-chip__value {
        color: #7dd3fc;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


ROLE_OPTIONS = [
    "Software Engineering Intern",
    "Backend Engineer",
    "Frontend Engineer",
    "Full Stack Engineer",
    "Data/AI Intern",
    "Data Scientist",
    "Machine Learning Engineer",
    "DevOps Engineer",
]

SKILL_OPTIONS = [
    "java", "python", "javascript", "typescript", "react", "node.js", "spring",
    "sql", "postgres", "mysql", "mongodb", "aws", "docker", "kubernetes",
    "fastapi", "django", "flask", "pandas", "numpy", "tensorflow", "pytorch",
]

MAX_BATCH_UPLOAD_BYTES = 100 * 1024 * 1024


def load_api_url() -> str:
    env = os.getenv("INTERNOS_API_URL")
    if env:
        return env

    possible = [
        Path.home() / ".streamlit" / "secrets.toml",
        Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml",
        Path(__file__).resolve().parent / ".streamlit" / "secrets.toml",
    ]
    if any(path.exists() for path in possible):
        return st.secrets.get("API_URL", "http://127.0.0.1:8000")

    return "http://127.0.0.1:8000"


API = load_api_url()


def show_api_error(exc: Exception):
    st.error(f"API connection failed for {API}. Start the backend server on that address. Details: {exc}")


def api_get(path: str, params: dict | None = None, timeout: int = 20):
    return requests.get(f"{API}{path}", params=params, timeout=timeout)


def api_post_multipart(path: str, data: dict, files: dict, timeout: int = 60):
    return requests.post(f"{API}{path}", data=data, files=files, timeout=timeout)


def score_label(value: float) -> str:
    if value >= 0.8:
        return "Strong"
    if value >= 0.6:
        return "Good"
    if value >= 0.4:
        return "Average"
    return "Needs work"


def confidence_label(value: float) -> str:
    if value >= 0.85:
        return "Very confident"
    if value >= 0.65:
        return "Confident"
    if value >= 0.4:
        return "Somewhat confident"
    return "Low confidence"


def yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def nice_list(values: list[str], empty: str = "Not found") -> str:
    return ", ".join(values) if values else empty


def format_mb(num_bytes: int) -> str:
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def format_skill_group_name(value: str) -> str:
    return value.replace("_", " ").title()


def render_skill_groups(skills_payload: dict):
    categorized = skills_payload.get("categorized", {})
    if not categorized:
        detected = skills_payload.get("detected", [])
        st.write(f"Detected skills: {nice_list(detected)}")
        return

    st.write(f"Total skills found: {len(skills_payload.get('detected', []))}")
    for group_name, values in categorized.items():
        if values:
            st.write(f"{format_skill_group_name(group_name)}: {nice_list(values)}")


def humanize_error(raw_error: str) -> tuple[str, str]:
    detail = raw_error
    try:
        payload = json.loads(raw_error)
        detail = payload.get("detail", raw_error)
    except Exception:
        pass

    lowered = detail.lower()
    if "document rejected:" in lowered:
        reason = detail.split(":", 1)[1].strip() if ":" in detail else detail
        return "This file is not a resume.", reason

    if "resume text could not be extracted" in lowered:
        return (
            "We could not read enough text from this file.",
            "Try uploading a clearer PDF or DOCX version of the resume.",
        )

    if "could not parse resume" in lowered:
        return (
            "This file could not be analyzed.",
            detail,
        )

    return ("This file could not be processed.", detail)


def render_scorecard(nlp: dict):
    scores = nlp.get("scores", {})
    education = nlp.get("education", {})
    skills_payload = nlp.get("skills", {})
    degree_summary = education.get("highest_degree") or nice_list(education.get("degrees", []), "Not identified")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall fit", f"{int(float(scores.get('overall', 0.0)) * 100)}%")
    c2.metric("Resume clarity", score_label(float(scores.get("clarity", 0.0))))
    c3.metric("Impact evidence", score_label(float(scores.get("impact", 0.0))))
    c4.metric("Graduated", yes_no(bool(education.get("graduated", False))))

    render_skill_groups(skills_payload)
    st.write(f"Degree level: {degree_summary.title() if degree_summary != 'Not identified' else degree_summary}")
    if education.get("graduation_year"):
        st.write(f"Graduation year: {education['graduation_year']}")


def render_document_check(nlp: dict):
    document_check = nlp.get("document_check", {})
    if not document_check:
        return

    is_resume = bool(document_check.get("is_resume", False))
    confidence = float(document_check.get("confidence", 0.0))
    doc_type = document_check.get("document_type", "unknown").replace("_", " ")
    reason = document_check.get("reason") or "No explanation available."

    st.subheader("Document Check")
    if is_resume:
        st.success("Resume detected")
    else:
        st.warning("This file may not be a resume")

    c1, c2 = st.columns(2)
    c1.metric("Detected as", "Resume" if is_resume else doc_type.title())
    c2.metric("Confidence", confidence_label(confidence))
    st.write(f"Why this decision was made: {reason}")


def render_plain_language_analysis(nlp: dict, llm: dict):
    identity = nlp.get("identity", {})
    scores = nlp.get("scores", {})
    education = nlp.get("education", {})
    matched = nlp.get("keywords", {}).get("matched", [])
    missing = nlp.get("keywords", {}).get("missing", [])

    render_document_check(nlp)

    st.subheader("Candidate Overview")
    st.write(f"Name: {identity.get('name') or 'Not clearly found in the resume'}")
    st.write(f"Email: {identity.get('email') or 'Not found'}")
    st.write(f"Target role checked: {nlp.get('target_role', 'Not specified')}")
    st.write(
        f"Resume fit: {score_label(float(scores.get('overall', 0.0))).lower()} "
        f"({int(float(scores.get('overall', 0.0)) * 100)}%)."
    )

    st.subheader("Recruiter Summary")
    st.info(llm.get("summary") or "No summary available.")

    st.subheader("What Looks Good")
    strengths = llm.get("top_strengths", [])
    if strengths:
        for item in strengths:
            st.write(f"- {item}")
    else:
        st.write("No major strengths were highlighted yet.")

    st.subheader("What Needs Improvement")
    gaps = llm.get("top_gaps", [])
    if gaps:
        for item in gaps:
            st.write(f"- {item}")
    else:
        st.write("No major gaps were highlighted.")

    st.subheader("Role Match")
    st.write(f"Relevant role keywords found: {nice_list(matched)}")
    if missing:
        st.write(f"Keywords still missing: {nice_list(missing[:6])}")

    st.subheader("Skills Found")
    render_skill_groups(nlp.get("skills", {}))

    st.subheader("Education Check")
    st.write(f"Graduated: {yes_no(bool(education.get('graduated', False)))}")
    if "expected_graduation" in education:
        st.write(f"Expected graduation mentioned: {yes_no(bool(education.get('expected_graduation', False)))}")
    highest_degree = education.get("highest_degree")
    if highest_degree:
        st.write(f"Most relevant degree: {highest_degree.title()}")
    elif education.get("degrees"):
        st.write(f"Degree found: {nice_list(education.get('degrees', []), 'Not identified')}")
    else:
        st.write("Degree found: Not identified")
    if education.get("graduation_year"):
        st.write(f"Graduation year: {education.get('graduation_year')}")


def render_candidate_cards(results: list[dict]):
    for row in results:
        display_name = row.get("name") or row["handle"]
        overall_fit = int(float(row["overall_score"]) * 100)
        clarity = score_label(float(row.get("clarity_score", row["overall_score"])))

        st.markdown(
            f"""
            <div class="candidate-chip">
                <div class="candidate-chip__name">{display_name}</div>
                <div class="candidate-chip__meta">
                    Overall fit: <span class="candidate-chip__value">{overall_fit}%</span><br>
                    Resume clarity: <span class="candidate-chip__value">{clarity}</span><br>
                    Handle: {row["handle"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander(f"View full review for {display_name}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Fit", f"{overall_fit}%")
            c2.metric("Graduated", yes_no(bool(row["graduated"])))
            c3.metric("Graduation year", row["graduation_year"] or "Unknown")
            st.write(f"Skills: {nice_list(row.get('matched_skills', []))}")
            st.write(f"Degree: {nice_list(row.get('degrees', []), 'Not identified')}")
            if row.get("top_strengths"):
                st.write(f"Highlights: {nice_list(row['top_strengths'])}")
            if row.get("top_gaps"):
                st.write(f"Watchouts: {nice_list(row['top_gaps'])}")
            if row.get("document_type"):
                st.write(f"Document type: {row['document_type']}")


def render_uploaded_resume_results(results: list[dict]):
    for item in results:
        with st.container(border=True):
            st.subheader(item.get("handle", item.get("filename", "Resume")))
            st.caption(item.get("filename", ""))
            if item.get("error"):
                title, reason = humanize_error(item["error"])
                st.warning(title)
                st.write(reason)
                continue
            render_scorecard(item.get("nlp", {}))
            render_plain_language_analysis(item.get("nlp", {}), item.get("llm", {}))


def render_full_candidate_results(items: list[dict]):
    for item in items:
        nlp = item.get("nlp", {})
        identity = nlp.get("identity", {})
        scores = nlp.get("scores", {})
        display_name = identity.get("name") or item.get("handle", "Candidate")
        overall_fit = int(float(scores.get("overall", 0.0)) * 100)
        clarity = score_label(float(scores.get("clarity", 0.0)))

        st.markdown(
            f"""
            <div class="candidate-chip">
                <div class="candidate-chip__name">{display_name}</div>
                <div class="candidate-chip__meta">
                    Overall fit: <span class="candidate-chip__value">{overall_fit}%</span><br>
                    Resume clarity: <span class="candidate-chip__value">{clarity}</span><br>
                    Handle: {item.get("handle", "Not available")}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander(f"View full review for {display_name}"):
            st.caption(item.get("filename", ""))
            render_scorecard(nlp)
            render_plain_language_analysis(nlp, item.get("llm", {}))


st.title("InternOS Recruiter Workspace")
st.caption(f"API: {API}")
st.write("Analyze resumes once, then review candidates in plain language.")

upload_tab, candidate_tab, search_tab = st.tabs(["Upload Resume", "Candidate Review", "Search Candidates"])

with upload_tab:
    st.subheader("Analyze Resumes")
    target_role = st.selectbox("Target role", options=ROLE_OPTIONS)
    uploads = st.file_uploader("Upload resumes", type=["pdf", "docx"], accept_multiple_files=True)
    total_bytes = sum(getattr(upload, "size", 0) for upload in uploads) if uploads else 0
    st.caption("Upload limit: up to 100 MB total per batch. Files are processed one at a time.")
    if uploads:
        st.write(f"Selected files: {len(uploads)}")
        st.write(f"Total selected size: {format_mb(total_bytes)}")
        if total_bytes > MAX_BATCH_UPLOAD_BYTES:
            st.warning("The selected files are above the 100 MB batch limit. Remove some files before uploading.")

    if st.button("Analyze resumes", type="primary"):
        if not uploads:
            st.error("Choose one or more PDF or DOCX resumes first.")
        elif total_bytes > MAX_BATCH_UPLOAD_BYTES:
            st.error("The selected files exceed the 100 MB batch limit.")
        else:
            results = []
            progress = st.progress(0)
            for index, upload in enumerate(uploads, start=1):
                files = {
                    "file": (
                        upload.name,
                        upload.getvalue(),
                        upload.type or "application/octet-stream",
                    )
                }
                data = {"target_role": target_role}
                try:
                    response = api_post_multipart("/resumes/analyze", data=data, files=files, timeout=120)
                    if response.ok:
                        out = response.json()
                        st.session_state["handle"] = out["handle"]
                        results.append(out)
                    else:
                        results.append({
                            "filename": upload.name,
                            "error": response.text,
                        })
                except requests.RequestException as exc:
                    progress.progress(index / len(uploads))
                    show_api_error(exc)
                    break
                progress.progress(index / len(uploads))

            if results:
                success_count = sum(1 for item in results if "error" not in item)
                st.success(f"Processed {success_count} of {len(results)} resumes.")

                summary_table = pd.DataFrame([
                    {
                        "File": item.get("filename"),
                        "Handle": item.get("handle", "Failed"),
                        "Fit %": int(float(item.get("nlp", {}).get("scores", {}).get("overall", 0.0)) * 100)
                        if "error" not in item else "-",
                        "Status": "Ready" if "error" not in item else "Failed",
                    }
                    for item in results
                ])
                st.dataframe(summary_table, use_container_width=True)

                successful = [item for item in results if "error" not in item]
                failed = [item for item in results if "error" in item]

                if successful:
                    st.subheader("Resume Results")
                    render_uploaded_resume_results(successful)

                if failed:
                    st.subheader("Files That Failed")
                    render_uploaded_resume_results(failed)

with candidate_tab:
    st.subheader("Latest Candidate Analysis")
    candidate_query = st.text_input(
        "Search by first name, last name, full name, or handle",
        value=st.session_state.get("handle", "*") or "*",
        key="candidate_handle",
    )

    if st.button("Load latest analysis", type="primary"):
        try:
            normalized_query = candidate_query.strip().lower()
            if normalized_query in {"*", "all"}:
                response = api_get("/resumes/all", params={"limit": 100})
                if response.ok:
                    out = response.json()
                    items = out.get("items", [])
                    st.info(f"Showing latest analysis for all candidates: {out.get('total', 0)} found.")
                    render_full_candidate_results(items)
                else:
                    st.error(response.text)
            else:
                response = api_get("/resumes/find", params={"query": candidate_query})
                if response.ok:
                    out = response.json()
                    st.session_state["handle"] = out["handle"]
                    if out.get("match_count", 0) > 1:
                        st.info(f"Showing the closest match. Similar matches found: {out['match_count']}")
                    render_full_candidate_results([out])
                else:
                    st.error(response.text)
        except requests.RequestException as exc:
            show_api_error(exc)

with search_tab:
    st.subheader("Find Matching Candidates")
    required_skills = st.multiselect("Required skills", options=SKILL_OPTIONS)
    graduated_choice = st.selectbox("Graduation status", options=["Any", "Graduated only", "Not graduated"])
    degree_query = st.text_input("Degree contains", placeholder="bachelor")
    min_score = st.slider("Minimum overall score", min_value=0.0, max_value=1.0, value=0.0, step=0.01)
    st.caption(f"Current minimum fit threshold: {int(min_score * 100)}%")

    if st.button("Search candidates", type="primary"):
        params = {
            "required_skills": ",".join(required_skills),
            "degree_query": degree_query,
            "min_score": min_score,
            "limit": 50,
        }
        if graduated_choice == "Graduated only":
            params["graduated"] = "true"
        elif graduated_choice == "Not graduated":
            params["graduated"] = "false"

        try:
            response = api_get("/resumes/search", params=params, timeout=30)
            if response.ok:
                out = response.json()
                results = out.get("results", [])
                st.caption(f"Matches found: {out.get('total', 0)}")
                if not results:
                    st.info("No candidates matched the current filters.")
                else:
                    summary_table = pd.DataFrame([
                        {
                            "Candidate": row["handle"],
                            "Fit %": int(float(row["overall_score"]) * 100),
                            "Graduated": yes_no(bool(row["graduated"])),
                            "Year": row["graduation_year"] or "Unknown",
                            "Skills": nice_list(row["matched_skills"]),
                        }
                        for row in results
                    ])
                    st.dataframe(summary_table, use_container_width=True)
                    st.subheader("Candidate Details")
                    render_candidate_cards(results)
            else:
                st.error(response.text)
        except requests.RequestException as exc:
            show_api_error(exc)
