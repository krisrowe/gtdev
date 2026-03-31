import os
import getpass
import subprocess
import json
import fnmatch
import time
import hashlib
import importlib.resources
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

class ProfileManager:
    def __init__(self):
        self.profiles = {}
        self._load_profiles()

    def _load_profiles(self):
        # Using importlib.resources to find profiles bundled in the package
        try:
            # For Python 3.9+
            pkg_path = importlib.resources.files("gtdev") / "profiles"
            if pkg_path.is_dir():
                for f in pkg_path.glob("*.json"):
                    with f.open("r") as data:
                        profile = json.load(data)
                        self.profiles[profile["name"]] = profile
        except Exception:
            # Fallback for local dev if not installed
            local_path = Path(__file__).parent / "profiles"
            if local_path.is_dir():
                for f in local_path.glob("*.json"):
                    with f.open("r") as data:
                        profile = json.load(data)
                        self.profiles[profile["name"]] = profile

    def get_profile(self, name):
        return self.profiles.get(name)

    def match_by_owner(self, owner_name: str):
        if not owner_name:
            return None
        
        # Simple neutral one-way hash
        h = hashlib.sha256(owner_name.lower().encode()).hexdigest()
        for p in self.profiles.values():
            if p.get("owner_hash") == h:
                return p
        return None

    def check_status(self, profile):
        """Returns a list of (step, passed) results for a profile."""
        results = []
        for step in profile.get("guidance", []):
            passed = True
            if "check" in step:
                try:
                    res = subprocess.run(step["check"], shell=True, capture_output=True)
                    if res.returncode != 0:
                        passed = False
                except Exception:
                    passed = False
            results.append((step, passed))
        return results

class ConfigManager:
    def __init__(self):
        self.config_dir = get_config_dir()
        self.config_file = self.config_dir / "config.json"
        self._load()

    def _load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}
        else:
            self.data = {}

    def save(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self.data, f, indent=2)

    @property
    def default_owner(self):
        return self.data.get("default_owner")

    @default_owner.setter
    def default_owner(self, value):
        self.data["default_owner"] = value

    @property
    def active_profile(self):
        return self.data.get("active_profile")

    @active_profile.setter
    def active_profile(self, value):
        self.data["active_profile"] = value

    @property
    def search_roots(self):
        roots = self.data.get("search_roots", [])
        if not roots:
            return [str(get_user_profile())]
        return roots

    def add_root(self, path: str):
        roots = self.data.get("search_roots", [])
        abs_path = str(Path(path).expanduser().resolve())
        if abs_path not in roots:
            roots.append(abs_path)
            self.data["search_roots"] = roots

    def remove_root(self, path: str):
        roots = self.data.get("search_roots", [])
        abs_path = str(Path(path).expanduser().resolve())
        if abs_path in roots:
            roots.remove(abs_path)
            self.data["search_roots"] = roots

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

def find_local_repos(pattern: str = "*", owner: str = None):
    repos = []
    depth = os.environ.get("GTDEV_GIT_SCAN_DEPTH", "4")
    config = ConfigManager()
    owner = owner or config.default_owner
    roots = config.search_roots

    for root in roots:
        root_path = Path(root)
        if not root_path.exists():
            continue
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
                        
                        # Apply owner filter if present and pattern is not absolute
                        if owner and "/" not in pattern:
                            if not simple_name.startswith(f"{owner}/"):
                                continue

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

def validate_github_access(owner: str):
    """
    Validates that the gh CLI is installed, logged in, and the owner is accessible.
    Returns (success, message, repo_count)
    """
    # 1. Check if gh is installed
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, "GitHub CLI (gh) is not installed or not in PATH.", 0

    # 2. Check if logged in
    try:
        subprocess.run(["gh", "auth", "status"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        return False, "Not logged into GitHub CLI. Run 'gh auth login'.", 0

    # 3. Validate owner and count repos
    try:
        # We use --limit 1000 just to get a decent count, but we only care about accessibility
        res = subprocess.run(
            ["gh", "repo", "list", owner, "--limit", "100", "--json", "name"],
            capture_output=True, text=True, check=True
        )
        repos = json.loads(res.stdout)
        return True, f"GitHub access confirmed for '{owner}'.", len(repos)
    except subprocess.CalledProcessError:
        return False, f"Could not access repositories for GitHub owner '{owner}'. Check the name and your permissions.", 0
    except Exception as e:
        return False, f"Unexpected error validating GitHub access: {str(e)}", 0
