from typing import Dict, Any

# Default weights (Ship 40, Quality 35, Comm 15, Reliability 10)
WEIGHTS = {
    "ship": 0.40,
    "quality": 0.35,
    "comm": 0.15,
    "reliability": 0.10,
}

def score_metrics(m: Dict[str, Any]) -> Dict[str, Any]:
    # Normalize inputs from metrics dict
    coverage = float(m.get("coverage", 0.0)) # 0..1
    lint_erros = float(m.get("lint_errors", 10.0)) # smaller is better
    complexity = float(m.get("avg_cyclomatic", 10.0)) # smaller is better
    pr_size = float(m.get("pr_size", 400.0)) # smaller is better
    time_to_green = float(m.get("time_to_green", 3600.0)) # seconds, smaller better
    first_commit_latency = float(m.get("first_commit_latency", 1800.0))
    tests_passed = float(m.get("tests_passed", 0.0))
    tests_failed = float(m.get("tests_failed", 1.0))
    standup_clarity = float(m.get("tests_passed", 0.0)) # 0..1
    pr_description = float(m.get("pr_description", 0.5)) # 0..1
    reproducible = float(m.get("reproducible", 0.0)) # 0 or 1

    # Helper maps
    def inv_cap(x ,k):
        # inverse cap: 1 / (1 + x/k)
        return 1.0 / (1.0 + (x / k))
    
    ship = 0.25 * inv_cap(first_commit_latency, 900) + \
           0.35 * inv_cap(time_to_green, 1800) + \
           0.20 * inv_cap(pr_size, 300) + \
           0.20 * (1.0 if tests_failed == 0 and tests_passed > 0 else 0.3)
    
    quality = 0.45 * coverage + \
              0.25 * inv_cap(lint_erros, 10) + \
              0.30 * inv_cap(complexity, 5)
    
    comm = 0.6 * standup_clarity + 0.4 * pr_description

    reliability = 0.7 * reproducible + 0.3 * (1.0 if tests_failed == 0 else 0.4)

    overall = WEIGHTS["ship"]*ship + WEIGHTS["quality"]*quality + WEIGHTS["comm"]*comm + WEIGHTS["reliability"]*reliability

    return {
        "ship": round(ship, 3),
        "quality": round(quality, 3),
        "comm": round(comm, 3),
        "reliability": round(reliability, 3),
        "overall": round(overall, 3),
    }

