import os
import getpass
from pathlib import Path

def get_user_profile() -> Path:
    """
    Returns the primary user profile directory.
    """
    # 1. Manual override for edge cases and test isolation
    env_path = os.environ.get("GTDEV_USER_PROFILE")
    if env_path:
        return Path(env_path)

    # 2. Smart check: If on WSL2, try to find the mounted Windows profile
    try:
        user = getpass.getuser()
        wsl_mnt = Path("/mnt/c/Users") / user
        if wsl_mnt.exists():
            return wsl_mnt
    except Exception:
        pass

    # 3. Default: Fallback to the current system home
    return Path.home()

def get_config_dir() -> Path:
    """Returns the tool's local configuration directory."""
    path_str = os.environ.get("GTDEV_CONFIG_DIR")
    if path_str:
        return Path(path_str)
    
    return Path.home() / ".config" / "gtdev"

def init_workspace():
    """Initializes the local workspace and reports the environment state."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    
    profile = get_user_profile()
    return f"Initialized workspace.\nConfig: {config_dir}\nProfile: {profile}"
