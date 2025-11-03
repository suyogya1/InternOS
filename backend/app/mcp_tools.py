import os, json, subprocess, shlex, time
from typing import Dict, Any, List
import tempfile
import httpx

PYTHON = os.environ.get("PYTHON_BIN", "python")

class ToolError(Exception):
    pass

def _run(cmd: List[str], cwd: str | None = None, timeout: int = 300) -> tuple[int, str, str]:
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill(); out, err = p.communicate()
        raise ToolError(f"Timeout running  {' '.join(cmd)}")
    return p.returncode, out, err

# --- MCP tool shims ---

def run_tests(path: str) -> Dict[str, Any]:
    rc, out, err = _run([PYTHON, "-m", "pytest", "-q"], cwd=path, timeout=240)
    passed = 0; failed = 0
    for line in (out + "\n" + err).splitlines():
        if line.strip().endswith(" passed") and "==" in line:
            try:
                passed = int(line.strip().split()[0])
            except: pass
        if " failed" in line and "==" in line:
            try:
                failed = int([x for x in line.split() if x.isdigit()][0])
            except: pass
    return {"passed": passed, "failed": failed, "raw": out+"\n"+err, "ok": rc == 0}

def coverage_report(path: str) -> Dict[str, Any]:
    # Run coverage over tests
    _run([PYTHON, "-m", "coverage", "erase"], cwd=path)
    rc, out, err = _run([PYTHON, "-m", "coverage", "run", "-m", "pytest", "-q"], cwd=path, timeout=300)
    rc2, out2, err2 = _run([PYTHON, "-m", "coverage", "report", "-m"], cwd=path)
    # Parse total coverage
    cov = 0.0
    for line in (out2+"\n"+err2).splitlines():
        if line.strip().startswith("TOTAL"):
            try:
                cov = float(line.strip().split()[-1].rstrip("%")) / 100.0
            except: pass
    return {"coverage": cov, "raw": out+out2+err+err2, "ok": rc == 0}


def grade_postmoremt(text: str) -> Dict[str, Any]:
    # Simple heuristic grader; replace with LLM later
    lower = text.lower()
    scores = {
        "structure": 1.0 if all(k in lower for k in ["impact", "rca", "fix", "prevention"]) else 0.4,
        "clarity": min(1.0, max(0.2, len(text.split())/ 200.0)), # 200+ words ` full credit
        "prevention_score": 1.0 if any(k in lower for k in ["alerting", "tests", "rate limit", "circuit breaker"]) else 0.05,
    }
    return scores

