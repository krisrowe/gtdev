---
name: teams-chat-sync
description: Syncs and updates the local MS Teams chat message database (~/.local/share/gtdev/messages/). Use this to pull the latest messages from MS Teams before attempting to summarize or capture teams context. Also handles HAR file token extraction for authentication.
---

# Teams Chat Sync

This skill ensures the local MS Teams cache is up to date without causing duplication.

## Workflow

0.  **Initialize Context**:
    * Run `date "+%Y-%m-%d %H:%M:%S"` to establish the current reference time.
1.  **Auth Check & HAR Processing**: 
    * Verify token validity using `teams messages stats`.
    * If unauthorized (401/403), locate a .har file in `~/Downloads` or the workspace created within the last 60 minutes.
    * If no recent .har file exists, ask the user to download a new one from MS Teams (filter for 'amer.ng.msg').
    * Run `teams extract-token path/to/file.har` to refresh the session. (Note: `--har-file` flag also works but is optional).
2.  **Sync Active Rooms**: For each active room (found in `~/.config/gtdev/teams_rooms.json` or based on project context):
    * Run: `teams messages list --room "<ROOM_NAME>" --limit 100`
    * The CLI handles deduplication automatically based on `clientmessageid`.
3.  **Verify**: Run `teams messages stats` to ensure the local archive is current.
