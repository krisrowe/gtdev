from gtdev import sdk
import os
import subprocess
from pathlib import Path

def test_init_creates_config_directory():
    config_dir = sdk.get_config_dir()
    assert not config_dir.exists()
    sdk.init_workspace()
    assert config_dir.exists()
    assert config_dir.is_dir()

def test_find_local_repos_respects_depth(tmp_path, monkeypatch):
    # Create a repo at depth 3: tmp_path/d1/d2/d3/.git
    repo_dir = tmp_path / 'd1' / 'd2' / 'd3'
    repo_dir.mkdir(parents=True)
    subprocess.run(['git', 'init', str(repo_dir)], check=True)
    subprocess.run(['git', '-C', str(repo_dir), 'remote', 'add', 'origin', 'https://github.com/user/repo.git'], check=True)

    # 1. Test with depth 2 (should NOT find it)
    monkeypatch.setenv('GTDEV_GIT_SCAN_DEPTH', '2')
    repos = sdk.find_local_repos(tmp_path)
    assert len(repos) == 0

    # 2. Test with depth 4 (should find it)
    monkeypatch.setenv('GTDEV_GIT_SCAN_DEPTH', '4')
    repos = sdk.find_local_repos(tmp_path)
    assert len(repos) == 1
    assert repos[0]['github_repo'] == 'user/repo'
