import pytest
from click.testing import CliRunner
from gtdev.cli.main import main
from gtdev import sdk
import json
import subprocess
import os
from pathlib import Path

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture(autouse=True)
def mock_gh_validation(monkeypatch):
    def mock_validate(owner):
        return True, "Mock validation success", 5
    monkeypatch.setattr(sdk, "validate_github_access", mock_validate)

def test_init_with_owner_discovers_profile(runner, tmp_path):
    # 'sample-org' hashes to 'f89272a3...' which is 'maracuya'
    result = runner.invoke(main, ["init", "--github-owner", "sample-org"])
    assert result.exit_code == 0
    assert "Discovered and matched profile 'maracuya'" in result.output
    assert "Configuration saved" in result.output
    
    # Verify config was saved
    cm = sdk.ConfigManager()
    assert cm.default_owner == "sample-org"
    assert cm.active_profile == "maracuya"

def test_init_with_unknown_owner_is_silent(runner):
    result = runner.invoke(main, ["init", "--github-owner", "unknown-org"])
    assert result.exit_code == 0
    assert "matched profile" not in result.output.lower()
    assert "Configuration saved" in result.output
    
    cm = sdk.ConfigManager()
    assert cm.default_owner == "unknown-org"
    assert cm.active_profile is None

def test_init_fails_on_bad_owner(runner, monkeypatch):
    def mock_validate_fail(owner):
        return False, "Owner not found", 0
    monkeypatch.setattr(sdk, "validate_github_access", mock_validate_fail)
    
    result = runner.invoke(main, ["init", "--github-owner", "bad-org"])
    assert result.exit_code == 1
    assert "❌ Owner not found" in result.output
    
    # Verify config was NOT saved
    cm = sdk.ConfigManager()
    assert cm.default_owner is None

def test_init_required_for_other_cmds(runner):
    # Try list without init
    result = runner.invoke(main, ["repos", "list"])
    assert result.exit_code == 1
    assert "Error: gtdev is not initialized" in result.output
    assert "init --github-owner" in result.output

def test_init_idempotency(runner):
    # First init
    runner.invoke(main, ["init", "--github-owner", "sample-org"])
    
    # Second init without flags should preserve profile
    result = runner.invoke(main, ["init"])
    assert result.exit_code == 0
    assert "--- Setup Guidance: Maracuya ---" in result.output
    
    cm = sdk.ConfigManager()
    assert cm.active_profile == "maracuya"

def test_repos_list_warns_on_missing_setup(runner, tmp_path, monkeypatch):
    # Setup a profile that will fail a check
    runner.invoke(main, ["init", "--github-owner", "sample-org"])
    
    # Mock find_local_repos to return something so we don't just see "No repositories found"
    def mock_repos(*args, **kwargs):
        return [{"name": "test-repo", "github_repo": "sample-org/test-repo", "path": str(tmp_path)}]
    monkeypatch.setattr(sdk, "find_local_repos", mock_repos)
    
    # Mock check_status to show something is missing
    def mock_status(self, profile):
        return [(profile['guidance'][0], False)] # First step failed
    monkeypatch.setattr(sdk.ProfileManager, "check_status", mock_status)
    
    result = runner.invoke(main, ["repos", "list"])
    assert "Missing setup steps for profile 'maracuya'" in result.output

def test_init_install_dependencies_interactive(runner, monkeypatch):
    runner.invoke(main, ["init", "--github-owner", "sample-org"])
    
    # Mock subprocess.run to track calls
    run_calls = []
    def mock_run(cmd, **kwargs):
        run_calls.append(cmd)
        return subprocess.CompletedProcess(args=cmd, returncode=0)
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    # Mock check_status to show steps need running
    def mock_status(self, profile):
        return [(profile['guidance'][0], False)]
    monkeypatch.setattr(sdk.ProfileManager, "check_status", mock_status)
    
    # Run with 'y' to confirm the step
    result = runner.invoke(main, ["init", "--install-dependencies"], input="y\n")
    
    assert result.exit_code == 0
    assert "Successfully completed" in result.output
    # The command is string based in the profile
    assert any("dnf install" in call for call in run_calls)

def test_config_add_root(runner):
    # Init first
    runner.invoke(main, ["init", "--github-owner", "sample-org"])
    
    test_path = "/tmp/fake-root"
    result = runner.invoke(main, ["config", "add-root", test_path])
    assert result.exit_code == 0
    assert f"Added search root: {test_path}" in result.output
    
    cm = sdk.ConfigManager()
    resolved_path = str(Path(test_path).expanduser().resolve())
    assert resolved_path in cm.search_roots

def test_apigee_fixtures_display(runner, monkeypatch):
    """Verifies that the CLI correctly displays data from the Apigee fixtures."""
    # 1. Load fixtures
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    with open(fixtures_dir / "repos_acme-corp.json") as f:
        repos_data = json.load(f)
    with open(fixtures_dir / "builds_acme-corp.json") as f:
        builds_data = json.load(f)

    # 2. Mock SDK to return fixture data
    runner.invoke(main, ["init", "--github-owner", "acme-corp"])
    monkeypatch.setattr(sdk, "find_local_repos", lambda **kwargs: repos_data)
    monkeypatch.setattr(sdk, "get_builds", lambda repo, **kwargs: [b for b in builds_data if b["repo_name"] == repo])

    # 3. Test repos list
    result = runner.invoke(main, ["repos", "list"])
    assert result.exit_code == 0
    assert "phoenix--apigee-gcp-infra" in result.output
    assert "phoenix-apigee-apis-cicd" in result.output

    # 4. Test builds list
    result = runner.invoke(main, ["builds", "list"])
    assert result.exit_code == 0
    assert "Deploy proxies to prod" in result.output
    assert "Provision GCP Resources" in result.output
    assert "Validate Hybrid Config" in result.output
