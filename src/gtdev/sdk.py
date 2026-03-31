import os
import getpass
import subprocess
import json
import fnmatch
import time
from pathlib import Path
from datetime import datetime, timedelta

def get_user_profile() -> Path:
    env_path = os.environ.get("GTDEV_USER_PROFILE")
    if env_path:
        return Path(env_path)
    try:
        user = getpass.getuser()
        wsl_mnt = Path("/mnt/c/Users") / user
        if wsl_mnt.exists():
            return wsl_mnt
    except Exception:
        pass
    return Path.home()

def get_config_dir() -> Path:
    path_str = os.environ.get("GTDEV_CONFIG_DIR")
    if path_str:
        return Path(path_str)
    return Path.home() / ".config" / "gtdev"

def get_current_identities():
    """Returns a list of unique names/emails/logins from git and gh."""
    ids = set()
    # Git global and local
    for scope in ["--global", ""]:
        for field in ["user.email", "user.name"]:
            try:
                res = subprocess.run(["git", "config", scope, field], capture_output=True, text=True)
                if res.returncode == 0 and res.stdout.strip():
                    ids.add(res.stdout.strip().lower())
            except Exception:
                pass
    # GH CLI login
    try:
        res = subprocess.run(["gh", "api", "user", "--jq", ".login"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            ids.add(res.stdout.strip().lower())
    except Exception:
        pass
    return list(ids)

def has_recent_commits(repo_path: str, user_patterns: list, max_age_hours: int) -> bool:
    """Checks if any commit matching user_patterns exists within max_age_hours."""
    since = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
    cmd = ["git", "-C", repo_path, "log", "--since", since, "--format=%ae|%an"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return False
        for line in res.stdout.splitlines():
            if "|" not in line: continue
            email, name = line.lower().split("|")
            for p in user_patterns:
                if p in email or p in name:
                    return True
    except Exception:
        pass
    return False

def find_local_repos(root_path: Path, pattern: str = "*"):
    repos = []
    depth = os.environ.get("GTDEV_GIT_SCAN_DEPTH", "4")
    try:
        result = subprocess.run(
            ["find", str(root_path), "-maxdepth", depth, "(", "-name", ".git", "-type", "d", "-print", "-prune", ")", "-o", "(", "-name", ".*", "-prune", ")"],
            capture_output=True, text=True
        )
        for git_dir in result.stdout.splitlines():
            repo_path = Path(git_dir).parent
            remote_res = subprocess.run(["git", "-C", str(repo_path), "remote", "get-url", "origin"], capture_output=True, text=True)
            if remote_res.returncode == 0:
                url = remote_res.stdout.strip()
                if "github.com" in url:
                    simple_name = url.split("github.com")[-1].replace(":", "/").lstrip("/").removesuffix(".git")
                    if fnmatch.fnmatch(simple_name, pattern) or fnmatch.fnmatch(repo_path.name, pattern):
                        repos.append({
                            "name": repo_path.name,
                            "path": str(repo_path),
                            "github_repo": simple_name
                        })
    except Exception:
        pass
    return repos

def get_builds(github_repo: str, limit: int = 10, refresh: bool = False):
    """Fetches build runs with 60s caching."""
    cache_dir = get_config_dir() / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{github_repo.replace('/', '_')}_builds.json"

    if not refresh and cache_file.exists():
        if time.time() - cache_file.stat().st_mtime < 60:
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass

    fields = "databaseId,status,conclusion,displayTitle,createdAt,headBranch,event,workflowName"
    cmd = ["gh", "run", "list", "--repo", github_repo, "--limit", str(max(limit, 20)), "--json", fields]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        with open(cache_file, "w") as f:
            json.dump(data, f)
        return data
    except Exception:
        return []

def get_build_logs(github_repo: str, run_id: str):
    cmd = ["gh", "run", "view", str(run_id), "--repo", github_repo, "--log"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"

def init_workspace():
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return f"Initialized workspace at {config_dir}"
