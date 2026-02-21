import os
import subprocess
import time
from typing import Dict, Any, List
import httpx

PYTHON = os.environ.get("PYTHON_BIN", "python")


class ToolError(Exception):
    pass


def _run(cmd: List[str], cwd: str | None = None, timeout: int = 300) -> tuple[int, str, str]:
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        out, err = p.communicate()
        raise ToolError(f"Timeout running {' '.join(cmd)}")
    return p.returncode, out, err


def run_tests(path: str) -> Dict[str, Any]:
    rc, out, err = _run([PYTHON, "-m", "pytest", "-q"], cwd=path, timeout=240)
    passed = failed = 0
    text = out + "\n" + err
    for line in text.splitlines():
        if " passed" in line and "==" in line:
            try:
                passed = int([tok for tok in line.split() if tok.isdigit()][0])
            except Exception:
                pass
        if " failed" in line and "==" in line:
            try:
                for i, tok in enumerate(line.split()):
                    if tok == "failed":
                        prev = line.split()[i - 1]
                        failed = int(prev) if prev.isdigit() else failed
                        break
            except Exception:
                pass
    return {"passed": passed, "failed": failed, "raw": text, "ok": rc == 0}


def coverage_report(path: str) -> Dict[str, Any]:
    _run([PYTHON, "-m", "coverage", "erase"], cwd=path)
    rc, out1, err1 = _run([PYTHON, "-m", "coverage", "run", "-m", "pytest", "-q"], cwd=path, timeout=300)
    rc2, out2, err2 = _run([PYTHON, "-m", "coverage", "report", "-m"], cwd=path)
    cov = 0.0
    for line in (out2 + "\n" + err2).splitlines():
        line = line.strip()
        if line.startswith("TOTAL"):
            try:
                cov = float(line.split()[-1].rstrip("%")) / 100.0
            except Exception:
                pass
            break
    return {"coverage": cov, "raw": out1 + out2 + err1 + err2, "ok": rc == 0}


def lint_check(path: str) -> Dict[str, Any]:
    rc, out, err = _run([PYTHON, "-m", "flake8", "."], cwd=path)
    errors = len([l for l in out.splitlines() if l.strip()])
    return {"errors": errors, "raw": out + "\n" + err, "ok": rc == 0}


def complexity_score(path: str) -> Dict[str, Any]:
    rc, out, err = _run([PYTHON, "-m", "radon", "cc", "-s", "-a", "."], cwd=path)
    avg = 0.0
    for line in (out + "\n" + err).splitlines():
        if line.strip().startswith("Average complexity"):
            import re
            m = re.search(r"\((\d+(?:\.\d+)?)\)", line)
            if m:
                avg = float(m.group(1))
                break
    return {"avg_cyclomatic": avg, "raw": out + "\n" + err, "ok": rc == 0}


def api_probe(url: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        r = httpx.get(url, timeout=5)
        t1 = time.perf_counter()
        return {
            "status_ok": r.status_code == 200,
            "latency_p50": t1 - t0,
            "p95_estimate": (t1 - t0) * 1.5,
            "status_code": r.status_code,
        }
    except Exception as e:
        return {"status_ok": False, "error": str(e), "latency_p50": 0.0, "p95_estimate": 0.0}
