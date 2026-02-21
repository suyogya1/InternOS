import os
import tempfile
from typing import Optional
from git import Repo
from datetime import datetime


def repo_clone(url: str, base_dir: Optional[str] = None) -> str:
    base_dir = base_dir or tempfile.mkdtemp(prefix="internos_")

    if url.startswith("file://"):
        src = url.replace("file://", "")
        dst = os.path.join(base_dir, os.path.basename(src.rstrip("/\\")))
        Repo.clone_from(src, dst)
        return dst

    if os.path.isdir(url):
        dst = os.path.join(base_dir, os.path.basename(url.rstrip("/\\")))
        Repo.clone_from(url, dst)
        return dst

    name = os.path.basename(url.rstrip("/ ")).replace(".git", "")
    dst = os.path.join(base_dir, name)
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
    try:
        repo = Repo(repo_path)
        base = None
        for name in ["origin/main", "origin/master", "main", "master"]:
            try:
                repo.git.rev_parse(name)
                base = name
                break
            except Exception:
                continue
        if base is None:
            return 0
        diff = repo.git.diff(base, "--shortstat")
        import re
        m = re.findall(r"(\d+)", diff)
        return sum(int(x) for x in m) if m else 0
    except Exception:
        return 0
