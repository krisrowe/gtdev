import click
import os
import json
from rich.console import Console
from rich.table import Table
from .config import (
    load_json, save_json, load_token, save_token, get_token_age,
    ROOMS_FILE, PEOPLE_FILE, MESSAGES_DIR, TOKEN_FILE,
    TOKEN_ARCHIVE_DIR, CACHE_DIR
)
from .har import get_token, extract_from_har, save_token_locations, DOWNLOADS_DIR
from .api import fetch_messages, process_messages, format_message_line

@click.group()
def cli():
    """Teams CLI for chat extraction and management."""
    pass

@cli.command()
@click.argument("har_file", required=False)
@click.option("--har-file", "har_file_opt", help="Override the auto-detected latest HAR file.")
@click.option("--limit", default=1, help="Number of unique tokens to extract.")
def extract_token(har_file, har_file_opt, limit):
    """Extract and save a new skypetoken from config."""
    # Use option if provided, else positional argument
    target_har = har_file_opt or har_file
    token, path = get_token(target_har)
    if token:
        save_token(token)
        click.echo(f"Successfully extracted token from: {path}")
        click.echo(f"Updated {TOKEN_FILE}")
        
        # Save token locations to XDG cache
        har_name = os.path.basename(path)
        loc_file = f"{har_name}.token-locations.txt"
        loc_path = os.path.join(TOKEN_ARCHIVE_DIR, loc_file)
        if save_token_locations(path, token, loc_path):
            click.echo(f"Token locations saved to: {loc_path}")
    else:
        click.echo(f"Error: No token found in {path or 'Downloads folder'}")

@cli.command()
def guide():
    """Display instructions for manual extraction from Chrome DevTools."""
    click.echo("\n--- Microsoft Teams Manual Extraction Guide ---\n")
    click.echo("1. Open Teams in Chrome (https://teams.microsoft.com)")
    click.echo("2. Open DevTools (F12 or Ctrl+Shift+I)")
    click.echo("3. Go to the 'Network' tab.")
    click.echo("4. To find the SKYPE TOKEN:")
    click.echo("   - Filter for: 'amer.ng.msg' or just '/messages'")
    click.echo("   - Select any request in the list.")
    click.echo("   - Check 'Request Headers' -> 'Authentication: skypetoken=...'")
    click.echo("\n5. To find ROOM IDs (Thread IDs) and Names:")
    click.echo("   - Filter for: 'conversations?'")
    click.echo("   - Look for a request that returns a JSON list of rooms.")
    click.echo("   - Response contains 'id' (19:xxx@thread.v2) and 'threadProperties.topic'.")
    click.echo("\n6. To generate a HAR file for this CLI:")
    click.echo("   - Right-click ANY request in the network list.")
    click.echo("   - Select 'Save all as HAR with content'.")
    click.echo(f"   - Save to: {DOWNLOADS_DIR}")
    click.echo("\n7. Then run: teams extract-token")
    click.echo("\n-----------------------------------------------\n")

@cli.group()
def rooms():
    """Manage tracked rooms."""
    pass

@rooms.command(name="list")
def list_rooms():
    """List tracked rooms."""
    data = load_json(ROOMS_FILE, {"rooms": []})
    rooms = data.get("rooms", [])
    console = Console()
    
    if not rooms:
        console.print("[yellow]No rooms found in config.[/yellow]")
        return
        
    table = Table(title="Tracked Teams Rooms", show_header=True, header_style="bold magenta")
    table.add_column("Room Name", style="cyan")
    table.add_column("Thread ID", style="dim")
    
    for r in rooms:
        name = r.get("name", "Unknown")
        chat_id = r.get("id", "No ID")
        table.add_row(name, chat_id)
        
    console.print(table)

@cli.group()
def people():
    """Manage known people mappings."""
    pass

@people.command(name="list")
def list_people():
    """List all known human identity mappings."""
    people = load_json(PEOPLE_FILE, {})
    console = Console()
    
    if not people:
        console.print("[yellow]No people mappings found.[/yellow]")
        return
        
    table = Table(title="Known People Mappings", show_header=True, header_style="bold green")
    table.add_column("Display Name", style="cyan")
    table.add_column("Raw Identifier", style="dim")
    
    for raw_name, info in people.items():
        display_name = info.get("display_name", raw_name)
        table.add_row(display_name, raw_name)
        
    console.print(table)

@cli.group()
def messages():
    """Access and sync chat messages."""
    pass

def find_rooms(query):
    data = load_json(ROOMS_FILE, {"rooms": []})
    rooms = data.get("rooms", [])
    query_lower = query.lower()
    matched = []
    for r in rooms:
        if query_lower in r.get("name", "").lower() or query_lower == r.get("id", "").lower():
            matched.append(r)
    return matched

@messages.command(name="list")
@click.option("--room", required=True, help="Room name or ID (partial match supported).")
@click.option("--limit", default=50, help="Number of messages to fetch per room.")
@click.option("--offset", help="Starting offset (timestamp) for pagination.")
def list_messages(room, limit, offset):
    """Fetch and display historical/paged messages, syncing to local storage."""
    matched_rooms = find_rooms(room)
    if not matched_rooms:
        click.echo(f"Error: No room matching '{room}' found.")
        return
        
    token = load_token()
    if not token:
        click.echo("Error: No token found. Run 'extract-token' first.")
        return
        
    all_processed = []
    try:
        for r in matched_rooms:
            chat_id = r['id']
            click.echo(f"[*] Fetching messages for {r['name']}...")
            raw_data = fetch_messages(chat_id, token, limit=limit, offset=offset)
            processed = process_messages(chat_id, raw_data)
            
            for msg in processed:
                msg['__room_name'] = r['name']
            all_processed.extend(processed)
            
        if not all_processed:
            click.echo("No new messages found.")
            return
            
        all_processed.sort(key=lambda x: x.get("originalarrivaltime", ""))
        
        if len(matched_rooms) == 1:
            click.echo(f"\n--- {matched_rooms[0]['name']} (New Messages: {len(all_processed)}) ---\n")
            for msg in all_processed:
                line = format_message_line(msg)
                if line:
                    click.echo(line)
        else:
            click.echo(f"\n--- Multiple Rooms (New Messages: {len(all_processed)}) ---\n")
            for msg in all_processed:
                line = format_message_line(msg, room_name=msg.get('__room_name'))
                if line:
                    click.echo(line)
                    
        click.echo("\n--------------------------")
    except Exception as e:
        err_msg = str(e)
        if "401" in err_msg or "911" in err_msg:
            age = get_token_age()
            click.echo("\n[!] ERROR: Token Expired or Invalid.")
            if age is not None:
                click.echo(f"    Current token was saved {age} minutes ago.")
            click.echo(f"    Please filter for 'amer.ng.msg' in Chrome DevTools,")
            click.echo(f"    download a new .har file to {DOWNLOADS_DIR},")
            click.echo(f"    and run 'teams extract-token'.\n")
        else:
            click.echo(f"Error: {e}")

@messages.command(name="view")
@click.option("--room", required=True, help="Room name or ID (partial match supported).")
@click.option("--limit", default=20, help="Number of most recent messages to show.")
def view_messages(room, limit):
    """View messages from the local archive."""
    matched_rooms = find_rooms(room)
    if not matched_rooms:
        click.echo(f"Error: No room matching '{room}' found.")
        return
        
    for r in matched_rooms:
        chat_id = r['id']
        room_filename = f"{chat_id.replace(':', '_')}.json"
        room_data_path = os.path.join(MESSAGES_DIR, room_filename)
        
        if not os.path.exists(room_data_path):
            click.echo(f"[*] No local archive found for {r['name']}. Try 'teams messages list --room \"{r['name']}\"' first.")
            continue
            
        data = load_json(room_data_path, {"messages": []})
        msgs = data.get("messages", [])
        
        if not msgs:
            click.echo(f"[*] Local archive for {r['name']} is empty.")
            continue
            
        # Show last N messages
        display_msgs = msgs[-limit:]
        
        click.echo(f"\n--- {r['name']} (Local Archive: {len(display_msgs)}/{len(msgs)}) ---\n")
        for msg in display_msgs:
            line = format_message_line(msg)
            if line:
                click.echo(line)
        click.echo("\n--------------------------")

@messages.command(name="export")
@click.option("--room", required=True, help="Room name or ID (partial match supported).")
@click.option("--date", help="Filter by date (YYYY-MM-DD).")
@click.option("--format", type=click.Choice(['text', 'json']), default='text')
@click.option("--output", type=click.Path(), help="Output file path.")
def export_messages(room, date, format, output):
    """Export messages from the local archive to a file or stdout."""
    matched_rooms = find_rooms(room)
    if not matched_rooms:
        click.echo(f"Error: No room matching '{room}' found.")
        return
        
    all_exported = []
    for r in matched_rooms:
        chat_id = r['id']
        room_filename = f"{chat_id.replace(':', '_')}.json"
        room_data_path = os.path.join(MESSAGES_DIR, room_filename)
        
        if not os.path.exists(room_data_path):
            continue
            
        data = load_json(room_data_path, {"messages": []})
        msgs = data.get("messages", [])
        
        for m in msgs:
            # Date filter
            if date:
                m_date = m.get("originalarrivaltime", "").split("T")[0]
                if m_date != date:
                    continue
            m['__room_name'] = r['name']
            all_exported.append(m)
            
    if not all_exported:
        click.echo("No messages found matching criteria.")
        return
        
    all_exported.sort(key=lambda x: x.get("originalarrivaltime", ""))
    
    if format == 'json':
        content = json.dumps(all_exported, indent=2)
    else:
        lines = []
        multi = len(matched_rooms) > 1
        for msg in all_exported:
            line = format_message_line(msg, room_name=msg.get('__room_name') if multi else None)
            if line:
                lines.append(line)
        content = "\n".join(lines)
        
    if output:
        with open(output, 'w') as f:
            f.write(content)
        click.echo(f"Successfully exported {len(all_exported)} messages to {output}")
    else:
        click.echo(content)

@messages.command(name="archive")
@click.argument("source_file", type=click.Path(exists=True))
@click.option("--target-dir", type=click.Path(), help="Override default archive directory.")
def archive_messages(source_file, target_dir):
    """Merge an external JSON file of messages into the local archive."""
    from .api import merge_external_json
    
    click.echo(f"[*] Archiving messages from: {source_file}")
    try:
        stats = merge_external_json(source_file, target_dir)
        
        click.echo(f"\n--- Archive Results ---")
        click.echo(f"Total messages seen: {stats['total_seen']}")
        click.echo(f"Rooms affected:      {stats['rooms_affected']}")
        click.echo(f"Messages imported:   {stats['imported']}")
        click.echo(f"Duplicates skipped:  {stats['duplicates']}")
        
        if stats['total_range'][0]:
            click.echo(f"Source date range:   {stats.get('total_range')[0]} to {stats.get('total_range')[1]}")
            
        if stats['imported_range'][0]:
            click.echo(f"Imported date range: {stats.get('imported_range')[0]} to {stats.get('imported_range')[1]}")
        elif stats['imported'] > 0:
            click.echo(f"Imported date range: (unknown)")
        else:
            click.echo(f"Imported date range: (none)")
            
        click.echo(f"----------------------\n")
    except Exception as e:
        click.echo(f"Error during archive: {e}")

@messages.command(name="stats")
def stats_messages():
    """Show statistics for the local message archive."""
    data = load_json(ROOMS_FILE, {"rooms": []})
    rooms_list = data.get("rooms", [])
    room_map = {r.get("id"): r.get("name") for r in rooms_list}
    
    console = Console()
    table = Table(title="Local Message Archive Stats", show_header=True, header_style="bold blue")
    table.add_column("Room Name", style="cyan")
    table.add_column("Thread ID", style="dim")
    table.add_column("Messages", justify="right", style="green")
    table.add_column("Earliest Message", style="yellow")
    table.add_column("Latest Message", style="yellow")
    
    if not os.path.exists(MESSAGES_DIR) or not os.listdir(MESSAGES_DIR):
        console.print("[yellow]No messages archive found or directory empty.[/yellow]")
        return
        
    for filename in os.listdir(MESSAGES_DIR):
        if not filename.endswith(".json"):
            continue
            
        # config.py does f"{chat_id.replace(':', '_')}.json"
        chat_id = filename.replace(".json", "").replace("_", ":", 1)
        room_name = room_map.get(chat_id, "Unknown (Not in config)")
        filepath = os.path.join(MESSAGES_DIR, filename)
        
        try:
            room_data = load_json(filepath, {"messages": []})
            msgs = room_data.get("messages", [])
            count = len(msgs)
            
            if count > 0:
                dates = []
                for m in msgs:
                    t = m.get("originalarrivaltime")
                    if t:
                        dates.append(t.split(".")[0].replace("T", " "))
                earliest = min(dates) if dates else "N/A"
                latest = max(dates) if dates else "N/A"
            else:
                earliest = "N/A"
                latest = "N/A"
                
            table.add_row(room_name, chat_id, str(count), earliest, latest)
        except Exception as e:
            table.add_row(room_name, chat_id, "Error", "-", "-")
            
    console.print(table)

@cli.group()
def live():
    """Real-time operations."""
    pass

@live.group(name="messages")
def live_messages_group():
    """Real-time message operations."""
    pass

@live_messages_group.command(name="list")
@click.option("--room", required=True, help="Room name or ID (partial match supported).")
@click.option("--limit", default=20, help="Number of most recent messages per room.")
def live_list_messages(room, limit):
    """Fetch the absolute most recent messages directly from the API."""
    matched_rooms = find_rooms(room)
    if not matched_rooms:
        click.echo(f"Error: No room matching '{room}' found.")
        return
        
    token = load_token()
    if not token:
        click.echo("Error: No token found. Run 'extract-token' first.")
        return
        
    all_messages = []
    try:
        from .api import clean_html, format_message_line
        people = load_json(PEOPLE_FILE, {})
        
        for r in matched_rooms:
            chat_id = r['id']
            click.echo(f"[*] Fetching live messages for {r['name']}...")
            raw_data = fetch_messages(chat_id, token, limit=limit)
            
            messages = raw_data.get("messages", [])
            for msg in messages:
                if msg.get("type") != "Message":
                    continue
                
                sender_raw = msg.get("fromDisplayNameInToken", "Unknown")
                msg["sender_display"] = people.get(sender_raw, {}).get("display_name", sender_raw)
                msg["content_clean"] = clean_html(msg.get("content", ""))
                msg["__room_name"] = r['name']
                all_messages.append(msg)
        
        if not all_messages:
            click.echo("No messages found.")
            return
            
        all_messages.sort(key=lambda x: x.get("originalarrivaltime", ""))
        
        if len(matched_rooms) == 1:
            click.echo(f"\n--- LIVE: {matched_rooms[0]['name']} ---\n")
            for msg in all_messages:
                line = format_message_line(msg)
                if line:
                    click.echo(line)
        else:
            click.echo(f"\n--- LIVE: Multiple Rooms ---\n")
            for msg in all_messages:
                line = format_message_line(msg, room_name=msg.get('__room_name'))
                if line:
                    click.echo(line)
                    
        click.echo("\n--------------------------")
        
        # Source reporting as per plan
        latest_har = get_token()[1]
        if latest_har:
            click.echo(f"Token sourced from: {latest_har}")
            
    except Exception as e:
        err_msg = str(e)
        if "401" in err_msg or "911" in err_msg:
            age = get_token_age()
            click.echo("\n[!] ERROR: Token Expired or Invalid.")
            if age is not None:
                click.echo(f"    Current token was saved {age} minutes ago.")
            click.echo(f"    Please filter for 'amer.ng.msg' in Chrome DevTools,")
            click.echo(f"    download a new .har file to {DOWNLOADS_DIR},")
            click.echo(f"    and run 'teams extract-token'.\n")
        else:
            click.echo(f"Error: {e}")

if __name__ == "__main__":
    cli()
