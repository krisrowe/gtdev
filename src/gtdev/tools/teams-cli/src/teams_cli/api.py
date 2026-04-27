import requests
import re
import json
import os
from datetime import datetime
from .config import load_json, save_json, PEOPLE_FILE, MESSAGES_DIR

def clean_html(content):
    """Strips HTML tags and unescapes common entities."""
    if not content:
        return ""
    # Clean up HTML tags
    content = re.sub('<[^<]+?>', '', content)
    # Unescape entities
    content = content.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
    # Collapse whitespace
    content = re.sub('\s+', ' ', content).strip()
    return content

def fetch_messages(chat_id, token, limit=50, offset=None):
    """Fetches messages from the Teams Messaging API."""
    url = f"https://amer.ng.msg.teams.microsoft.com/v1/users/ME/conversations/{chat_id}/messages"
    headers = {"Authentication": f"skypetoken={token}"}
    params = {
        "view": "msnp24Equivalent",
        "pageSize": limit
    }
    if offset:
        params["startTime"] = offset
        
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"API Error ({response.status_code}): {response.text}")
        
    return response.json()

def process_messages(chat_id, raw_data):
    """Processes raw API messages, applying identity mapping and deduplication."""
    messages = raw_data.get("messages", [])
    processed = []
    
    people = load_json(PEOPLE_FILE, {})
    people_updated = False
    
    # Load existing messages for this room to deduplicate
    room_data_path = os.path.join(MESSAGES_DIR, f"{chat_id.replace(':', '_')}.json")
    existing_data = load_json(room_data_path, {"messages": []})
    existing_ids = {m.get("clientmessageid") or m.get("id") or m.get("originalarrivaltime") for m in existing_data["messages"]}
    
    for msg in messages:
        if msg.get("type") != "Message":
            continue
            
        msg_id = msg.get("clientmessageid") or msg.get("id") or msg.get("originalarrivaltime")
        if msg_id in existing_ids:
            continue
            
        sender_raw = msg.get("fromDisplayNameInToken", "Unknown")
        
        # Human identification and mapping
        if sender_raw != "Unknown" and sender_raw not in people:
            parts = sender_raw.split(", ")
            if len(parts) == 2:
                display_name = f"{parts[1]} {parts[0]}"
            else:
                display_name = sender_raw
                
            people[sender_raw] = {
                "display_name": display_name,
                "raw_name": sender_raw
            }
            people_updated = True
            
        msg["sender_display"] = people.get(sender_raw, {}).get("display_name", sender_raw)
        msg["content_clean"] = clean_html(msg.get("content", ""))
        
        processed.append(msg)
        existing_ids.add(msg_id)
        
    if people_updated:
        save_json(PEOPLE_FILE, people)
        
    if processed:
        # Append new messages and save
        existing_data["messages"].extend(processed)
        # Sort all messages by arrival time
        existing_data["messages"].sort(key=lambda x: x.get("originalarrivaltime", ""))
        save_json(room_data_path, existing_data)
        
    return processed

def merge_external_json(source_path, target_dir=None):
    """Merges an external JSON file into the message archive with deduplication."""
    if target_dir is None:
        target_dir = MESSAGES_DIR
        
    with open(source_path, 'r') as f:
        data = json.load(f)
        
    messages = data.get("messages", [])
    total_seen = len(messages)
    
    # Track date ranges
    def get_date(msg):
        t = msg.get("originalarrivaltime")
        if t:
            return t.split(".")[0].replace("T", " ")
        return None

    all_dates = [get_date(m) for m in messages if get_date(m)]
    
    # Group by conversation ID
    by_room = {}
    for msg in messages:
        chat_id = msg.get("conversationid")
        if not chat_id:
            continue
        if chat_id not in by_room:
            by_room[chat_id] = []
        by_room[chat_id].append(msg)
        
    stats = {
        "total_seen": total_seen,
        "imported": 0,
        "duplicates": 0,
        "rooms_affected": len(by_room),
        "total_range": (min(all_dates), max(all_dates)) if all_dates else (None, None),
        "imported_range": (None, None)
    }
    
    imported_dates = []
    
    for chat_id, room_messages in by_room.items():
        # Prepare data in the format process_messages expects
        raw_data = {"messages": room_messages}
        
        # We need a custom path if target_dir is different
        room_filename = f"{chat_id.replace(':', '_')}.json"
        room_data_path = os.path.join(target_dir, room_filename)
        
        # Load existing for this specific target path
        existing_data = load_json(room_data_path, {"messages": []})
        existing_ids = {m.get("clientmessageid") or m.get("id") or m.get("originalarrivaltime") for m in existing_data["messages"]}
        
        people = load_json(PEOPLE_FILE, {})
        people_updated = False
        
        room_imported = 0
        room_duplicates = 0
        
        new_processed = []
        for msg in room_messages:
            msg_id = msg.get("clientmessageid") or msg.get("id") or msg.get("originalarrivaltime")
            if msg_id in existing_ids:
                room_duplicates += 1
                continue
                
            # Basic cleanup if missing
            if "sender_display" not in msg:
                sender_raw = msg.get("fromDisplayNameInToken", "Unknown")
                if sender_raw != "Unknown" and sender_raw not in people:
                    parts = sender_raw.split(", ")
                    if len(parts) == 2:
                        display_name = f"{parts[1]} {parts[0]}"
                    else:
                        display_name = sender_raw
                    people[sender_raw] = {"display_name": display_name, "raw_name": sender_raw}
                    people_updated = True
                msg["sender_display"] = people.get(sender_raw, {}).get("display_name", sender_raw)
            
            if "content_clean" not in msg:
                msg["content_clean"] = clean_html(msg.get("content", ""))
                
            new_processed.append(msg)
            existing_ids.add(msg_id)
            room_imported += 1
            
            dt = get_date(msg)
            if dt:
                imported_dates.append(dt)

        if people_updated:
            save_json(PEOPLE_FILE, people)
            
        if new_processed:
            existing_data["messages"].extend(new_processed)
            existing_data["messages"].sort(key=lambda x: x.get("originalarrivaltime", ""))
            save_json(room_data_path, existing_data)
            
        stats["imported"] += room_imported
        stats["duplicates"] += room_duplicates
        
    if imported_dates:
        stats["imported_range"] = (min(imported_dates), max(imported_dates))
        
    return stats

def format_message_line(msg, room_name=None):
    """Formats a single message into a human-readable string."""
    timestamp = msg.get("originalarrivaltime", "").split(".")[0].replace("T", " ")
    sender = msg.get("sender_display", "Unknown")
    content = msg.get("content_clean", "")
    if content:
        if room_name:
            trunc_room = (room_name[:12] + '...') if len(room_name) > 15 else room_name
            return f"[{timestamp}] [{trunc_room:<15}] {sender}: {content}"
        return f"[{timestamp}] {sender}: {content}"
    return None
