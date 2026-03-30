import os
import getpass
import subprocess
import json
import fnmatch
from pathlib import Path

def get_user_profile() -> Path:
    env_path = os.environ.get('GTDEV_USER_PROFILE')
    if env_path:
        return Path(env_path)
    try:
        user = getpass.getuser()
        wsl_mnt = Path('/mnt/c/Users') / user
        if wsl_mnt.exists():
            return wsl_mnt
    except Exception:
        pass
    return Path.home()

def get_config_dir() -> Path:
    path_str = os.environ.get('GTDEV_CONFIG_DIR')
    if path_str:
        return Path(path_str)
    return Path.home() / '.config' / 'gtdev'

def find_local_repos(root_path: Path, pattern: str = '*'):
    repos = []
    depth = os.environ.get('GTDEV_GIT_SCAN_DEPTH', '4')
    try:
        # Corrected find logic: find .git, print it, and PRUNE it so we don't scan its internals.
        # Also prune any other hidden directories.
        result = subprocess.run(
            ['find', str(root_path), '-maxdepth', depth, '(', '-name', '.git', '-type', 'd', '-print', '-prune', ')', '-o', '(', '-name', '.*', '-prune', ')'],
            capture_output=True, text=True
        )
        for git_dir in result.stdout.splitlines():
            repo_path = Path(git_dir).parent
            remote_res = subprocess.run(
                ['git', '-C', str(repo_path), 'remote', 'get-url', 'origin'],
                capture_output=True, text=True
            )
            if remote_res.returncode == 0:
                url = remote_res.stdout.strip()
                if 'github.com' in url:
                    simple_name = url.split('github.com')[-1].replace(':', '/').lstrip('/').removesuffix('.git')
                    if fnmatch.fnmatch(simple_name, pattern) or fnmatch.fnmatch(repo_path.name, pattern):
                        repos.append({'name': repo_path.name, 'path': str(repo_path), 'github_repo': simple_name})
    except Exception:
        pass
    return repos

def get_builds(github_repo: str, limit: int = 5):
    cmd = ['gh', 'run', 'list', '--repo', github_repo, '--limit', str(limit), '--json', 'databaseId,status,conclusion,displayTitle,createdAt']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception:
        return []

def get_build_logs(github_repo: str, run_id: str):
    cmd = ['gh', 'run', 'view', str(run_id), '--repo', github_repo, '--log']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except Exception as e:
        return f'Error: {str(e)}'

def init_workspace():
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return f'Initialized workspace at {config_dir}'
