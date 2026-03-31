import pytest
import os

@pytest.fixture(autouse=True)
def isolate_env(tmp_path, monkeypatch):
    """Auto-isolate every test from the real filesystem and environment."""
    test_home = tmp_path / "home"
    test_config = tmp_path / "config"
    test_profile = tmp_path / "profile"
    
    test_home.mkdir(parents=True, exist_ok=True)
    test_profile.mkdir(parents=True, exist_ok=True)

    # Set variables for isolation
    monkeypatch.setenv("HOME", str(test_home))
    monkeypatch.setenv("GTDEV_CONFIG_DIR", str(test_config))
    monkeypatch.setenv("GTDEV_USER_PROFILE", str(test_profile))
