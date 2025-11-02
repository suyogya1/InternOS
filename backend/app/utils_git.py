import os
import tempfile
import subprocess
from git import Repo
from datetime import datetime
from typing import Optional

def repo_clone(url: str, base_dir: Optional[str] = None) -> str:
    # Support local path via file:// or plain path
    if url.startswith("file:.//"):
        src = url.replace("file://", "")
        dst = os.path.join(base_dir, os.path.basename(src.rstrip("/")))
        Repo.clone_from(src, dst)
        return dst
    if os.path.isdir(url):
        dst = os.path.join(base_dir, os.path.basename(url.rstrip("/")))
        Repo.clone_from(url, dst)
        return dst
    # Remote
    dst = os.path.join(base_dir, os.path.basename(url.rstrip("/ ").replace('.git','')))
    Repo.clone_from(url, dst)
    return dst

def first_commit_time(repo_path: str) -> Optional[datetime]:
    try:
        repo = Repo(repo_path)
        commits = list(repo.iter_commits())
        if not commits:
            return None
        last = commits[-1]
        return datetime.fromtimestamp(last.committed_date)
    except Exception:
        return None
    
def pr_size_loc(repo_path: str) -> int:
    # Approximate PR size as current diff lines vs main (if exists)
    try: 
        repo = Repo(repo_path)
        base = None
        for name in ["origin/main", "origin/master", "main", "master"]:
            base = name
            break
        if base is None:
            return 0
        diff = repo.git.diff(base, "--shortstat")
        # Parse numvers from "X Files changed, Y insertions(+), Z deletion(-)"
        import re
        m = re.findall(r"(\d+)", diff)
        return sum(int(x) for x in m) if m else 0
    except Exception:
        return 0
    
    
        