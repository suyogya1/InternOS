import os
from sqlalchemy.orm import Session

from .models import Attempt, Metric, Artifact
from .mcp_tools import run_tests, coverage_report, lint_check, complexity_score
from .utils_git import first_commit_time, pr_size_loc
from .rubric import score_metrics

ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "./artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)


def _save_metric(db: Session, attempt_id: int, key: str, value: float, extra=None):
    db.add(Metric(attempt_id=attempt_id, key=key, value=value, extra=extra))


def grade_attempt(
    db: Session,
    attempt: Attempt,
    submitted_at: float,
    pr_url: str | None,
    standup_text: str | None,
    postmortem_text: str | None,
):
    repo = attempt.repo_path

    # --- Run tools ---
    tests = run_tests(repo)
    cov = coverage_report(repo)
    lint = lint_check(repo)
    comp = complexity_score(repo)

    # --- Derive metrics ---
    fc_time = first_commit_time(repo)
    first_commit_latency = 0.0
    if fc_time and attempt.started_at:
        first_commit_latency = max(0.0, (fc_time - attempt.started_at).total_seconds())

    time_to_green = submitted_at - attempt.started_at.timestamp()
    pr_size = pr_size_loc(repo)

    # Comm heuristics
    def clarity_score(text: str | None) -> float:
        if not text:
            return 0.4
        wc = len(text.split())
        has_bullets = any(x in text for x in ["- ", "* ", "1.", "\n\n"])
        return min(1.0, 0.3 + (wc / 150.0) + (0.2 if has_bullets else 0.0))

    standup_clarity = clarity_score(standup_text)
    pr_description = clarity_score(pr_url)  # proxy until we fetch real PR body
    reproducible = 1.0  # assume yes if tools ran

    # Build metrics dict (used for scoring) and persist rows
    m = {
        "tests_passed": float(tests.get("passed", 0)),
        "tests_failed": float(tests.get("failed", 0)),
        "coverage": float(cov.get("coverage", 0.0)),
        "lint_errors": float(lint.get("errors", 0)),
        "avg_cyclomatic": float(comp.get("avg_cyclomatic", 0.0)),
        "first_commit_latency": float(first_commit_latency),
        "time_to_green": float(time_to_green),
        "pr_size": float(pr_size),
        "standup_clarity": float(standup_clarity),
        "pr_description": float(pr_description),
        "reproducible": float(reproducible),
    }

    _save_metric(db, attempt.id, "tests_passed", m["tests_passed"], tests)
    _save_metric(db, attempt.id, "tests_failed", m["tests_failed"], tests)
    _save_metric(db, attempt.id, "coverage", m["coverage"], cov)
    _save_metric(db, attempt.id, "lint_errors", m["lint_errors"], lint)
    _save_metric(db, attempt.id, "avg_cyclomatic", m["avg_cyclomatic"], comp)
    _save_metric(db, attempt.id, "first_commit_latency", m["first_commit_latency"])
    _save_metric(db, attempt.id, "time_to_green", m["time_to_green"])
    _save_metric(db, attempt.id, "pr_size", m["pr_size"])
    _save_metric(db, attempt.id, "standup_clarity", m["standup_clarity"])
    _save_metric(db, attempt.id, "pr_description", m["pr_description"])
    _save_metric(db, attempt.id, "reproducible", m["reproducible"])

    # Score + store score_* metrics
    scores = score_metrics(m)
    for k, v in scores.items():
        _save_metric(db, attempt.id, f"score_{k}", float(v))

    # Artifacts (save raw tool outputs)
    for name, blob in [
        ("pytest.txt", tests.get("raw", "")),
        ("coverage.txt", cov.get("raw", "")),
        ("lint.txt", lint.get("raw", "")),
        ("complexity.txt", comp.get("raw", "")),
    ]:
        path = os.path.join(ARTIFACTS_DIR, f"attempt_{attempt.id}_{name}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(blob)
        db.add(Artifact(attempt_id=attempt.id, kind="report", url=path))

    if pr_url:
        db.add(Artifact(attempt_id=attempt.id, kind="pr", url=pr_url))

    attempt.status = "graded"

    return scores
