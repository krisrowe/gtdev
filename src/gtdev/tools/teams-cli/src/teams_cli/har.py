import os
import re
import glob
import sys

# Dynamically resolve Downloads directory - handles WSL and standard Linux
USER_HOME = os.path.expanduser("~")
# Fallback for WSL if Windows user is needed, but prefer $HOME/Downloads for portability
DOWNLOADS_DIR = os.path.join(USER_HOME, "Downloads")

# Compile regex patterns for raw byte extraction
PATTERNS = {
    "skypetoken": re.compile(b'skypetoken=(eyJ[a-zA-Z0-9\\._-]*)'),
    "thread_id": re.compile(b'(19:[a-zA-Z0-9_-]+@thread\\.v2)'),
    "topic_name": re.compile(b'"topicName"\s*:\s*"([^"]+)"'),
    "person_name": re.compile(b'"fromDisplayNameInToken"\s*:\s*"([^"]+)"'),
    "user_mri": re.compile(b'"mri"\s*:\s*"(8:orgid:[a-zA-Z0-9_-]+)"'),
    "message_id": re.compile(b'"clientmessageid"\s*:\s*"([^"]+)"')
}

def get_latest_har():
    """Returns the path to the most recent .har file in the Downloads directory."""
    if not os.path.exists(DOWNLOADS_DIR):
        return None
    files = glob.glob(os.path.join(DOWNLOADS_DIR, "*.har"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def extract_from_har(har_path, pattern_keys=None, limit=1):
    """
    Scans a HAR file in chunks using regex to extract specified metadata.
    """
    if not os.path.exists(har_path):
        raise FileNotFoundError(f"HAR file not found: {har_path}")

    if pattern_keys is None:
        pattern_keys = ["skypetoken"]

    results = {key: set() for key in pattern_keys}
    chunk_size = 4 * 1024 * 1024  # 4MB chunks
    overlap = 2048  # Overlap to prevent missing patterns split across chunks
    
    with open(har_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
                
            for key in pattern_keys:
                if len(results[key]) >= limit:
                    continue
                    
                matches = PATTERNS[key].findall(chunk)
                for m in matches:
                    try:
                        decoded = m.decode('utf-8')
                        results[key].add(decoded)
                        if len(results[key]) >= limit:
                            break
                    except UnicodeDecodeError:
                        pass
                        
            # Check if all limits reached
            if all(len(results[k]) >= limit for k in pattern_keys):
                break
                
            if len(chunk) == chunk_size:
                f.seek(f.tell() - overlap)
                
    return {k: list(v) for k, v in results.items()}

def get_token(har_path=None):
    """Convenience function to get the first skypetoken from a HAR file."""
    if not har_path:
        har_path = get_latest_har()
    
    if not har_path:
        return None, None
        
    extracted = extract_from_har(har_path, ["skypetoken"], limit=1)
    tokens = extracted.get("skypetoken", [])
    return (tokens[0] if tokens else None, har_path)

def save_token_locations(har_path, token_value, output_path, limit=20):
    """Finds occurrences of a token in a HAR file and saves offsets/context to a file."""
    if not os.path.exists(har_path):
        return False

    token_bytes = token_value.encode('utf-8')
    chunk_size = 4 * 1024 * 1024  # 4MB
    overlap = len(token_bytes) * 2
    found_count = 0
    
    with open(har_path, 'rb') as f, open(output_path, 'w') as out:
        out.write(f"Source HAR: {har_path}\n")
        out.write(f"Token (first 50): {token_value[:50]}...\n\n")
        
        while True:
            start_pos = f.tell()
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            idx = chunk.find(token_bytes)
            while idx != -1:
                found_count += 1
                absolute_pos = start_pos + idx
                
                context_start = max(0, idx - 100)
                context_end = min(len(chunk), idx + len(token_bytes) + 100)
                context = chunk[context_start:context_end].decode('utf-8', errors='ignore')
                
                out.write(f"[{found_count}] Offset: {absolute_pos}\n")
                out.write(f"Context: ...{context}...\n")
                out.write("-" * 20 + "\n")
                
                if found_count >= limit:
                    return True
                
                idx = chunk.find(token_bytes, idx + 1)
            
            if len(chunk) == chunk_size:
                f.seek(f.tell() - overlap)
    return found_count > 0

def extract_room_mappings(har_path):
    """Extracts thread IDs and topic names to build room mappings."""
    # This is tricky because we need to pair them.
    # Usually, they appear close together in the JSON response for conversations.
    # For now, we'll just extract all unique ones and let the user see them.
    results = extract_from_har(har_path, ["thread_id", "topic_name"], limit=500)
    return results
