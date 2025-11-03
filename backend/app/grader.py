import os, json, time, shutil
from sqlalchemy.orm import Session
from .models import Attempt, Metric, Artifact
from .mcp_tools import run_tests, coverage_report, lint_check, complexity_score
from .utils_git import first_commit_time, pr_size_loc
from .rubric import score_metrics

ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "./artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

def _save_metric(db: Session, attempt_id: int, key: str, value:float, extra=None)
    m = Metric(attempt_id=attempt_id, key=key, value=value, extra=extra)
    db.add(m)

def grade_attempt(db: Session, attempt: Attempt, submitted_at: float, pr_url: str | None, standup_text: str | None, postmortem_text: str | None):
    repo = attempt.repo_path

    # --- Run tools ---
    tests = run_tests(repo)
    cov = coverage_report(repo)
    lint = lint_check(repo)
    comp = complexity_score(repo)

    # --- Derice metrics ---
    first_commit = first_commit_time(repo)
    first_commit_latency = 0.0
    if first_commit and attempt.started_at:
        first_coammit_latency = max(0.0, (first_commit - attempt.started_at).total_seconds())
    
    time_to_green = submitted_at - attempt.started_at.timestamp()
    pr_size = pr_size_loc(repo)

    # --- Persis metrics ---
    _save_metric(db, attempt.id, "tests_passed", float(tests.get("passed, 0")), tests)
    _save_metric(db, attempt.id, "tests_failed", float(tests.get("failed", 0)), tests)
    _save_metric(db, attempt.id, "coverage", float(cov.get("coverage", 0.0)), cov)
    _save_metric(db, attempt.id, "lint_errors", float(lint.get("errors", 0)), lint)
    _save_metric(db, attempt.id, "avg_cyclomatic", float(comp.get("avg_cyclomatic, 0.0")), comp)
    _save_metric(db, attempt.id, "first_commit_latency", float(first_coammit_latency))
    _save_metric(db, attempt.id, "time_to_green", float(time_to_green))
    _save_metric(db, attempt.id, "pr_size", float(pr_size))

    if pr_url:
        art = Artifact(attempt_id=attempt.id, kind="pr", url=pr_url)
        db.add(art)

    # Comm heuristics
    def clarity_score(text: str | None) -> float:
        if not text: return 0.4
        wc = len(text.split())
        has_bullets = any(x in text for x in ["- ", "* ", "1.", "\n\n"])
        return min(1.0, 0.3 + (wc/150.0) + (0.2 if has_bullets else 0.0))
    
    _save_metric(db, attempt.id, "standup_clatrity", clarity_score(standup_text))
    _save_metric(db, attempt.id, "pr_description", clarity_score(pr_url)) # proxy if description fetched later
    _save_metric(db, attempt.id, "reproducible", 1.0) # assume yes if tests run in CI

    # Computer snapshot
    metrics = {m.key: m.value for m in attempt.metrics}
    scores = score_metrics(metrics)
    for k, v in scores.items():
        _save_metric(db, attempt.id, f"score_{k}", float(v))

    attempt.status = "graded"
    db.flush()

    # Save raw artifacts
    for name, blob in [
        ("pytest.txt", tests.get("raw", "")),
        ("coverage.txt", cov.get("raw", "")),
        ("lint.txt", lint.get("raw", "")),
        ("completely.txt", comp.get("raw", "")),
    ]:
        path = os.path.join(ARTIFACTS_DIR, f"attempt_{attempt.id}_{name}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(blob)
        db.add(Artifact(attempt_id=attempt.id, kind="report", url=path))

    return scores



    