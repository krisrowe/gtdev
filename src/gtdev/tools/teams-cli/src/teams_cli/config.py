import os
import json
import time
import shutil

# XDG_CONFIG_HOME for Configuration
CONFIG_DIR = os.path.expanduser(os.environ.get("XDG_CONFIG_HOME", "~/.config/gtdev"))
TOKEN_FILE = os.path.join(CONFIG_DIR, "teams_token")
ROOMS_FILE = os.path.join(CONFIG_DIR, "teams_rooms.json")
PEOPLE_FILE = os.path.join(CONFIG_DIR, "known_people.json")

# XDG_DATA_HOME for Data Storage
DATA_DIR = os.path.expanduser(os.environ.get("XDG_DATA_HOME", "~/.local/share/gtdev"))
MESSAGES_DIR = os.path.join(DATA_DIR, "messages")

# XDG_CACHE_HOME for Cache and Backups
CACHE_DIR = os.path.expanduser(os.environ.get("XDG_CACHE_HOME", "~/.cache/gtdev"))
TOKEN_ARCHIVE_DIR = os.path.join(CACHE_DIR, "tokens")

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(MESSAGES_DIR, exist_ok=True)
os.makedirs(TOKEN_ARCHIVE_DIR, exist_ok=True)

def load_json(filepath, default_val):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return default_val

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    return None

def get_token_age():
    """Returns the age of the token in minutes, or None if not found."""
    if os.path.exists(TOKEN_FILE):
        mtime = os.path.getmtime(TOKEN_FILE)
        return int((time.time() - mtime) / 60)
    return None

def save_token(token):
    # Archive existing token before overwriting
    if os.path.exists(TOKEN_FILE):
        timestamp = int(time.time())
        archive_name = f"teams_token_{timestamp}"
        archive_path = os.path.join(TOKEN_ARCHIVE_DIR, archive_name)
        shutil.copy2(TOKEN_FILE, archive_path)
    
    with open(TOKEN_FILE, "w") as f:
        f.write(token)
