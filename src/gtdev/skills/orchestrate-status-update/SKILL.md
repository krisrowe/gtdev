---
name: orchestrate-status-update
description: Orchestrates the full daily status update process. Syncs MS Teams chats, reviews recent progress, generates a comprehensive status folder for today with issue-level logs, and exports a summary to the Windows Downloads folder. Use when asked to "perform a full update", "sync and status", or at the end of the business day.
---

# Orchestrate Status Update

This skill automates the end-of-day (or anytime) status reporting by integrating multiple sources of context.

## Workflow

1.  **Initialize Context**:
    *   Run `date "+%A, %Y-%m-%d"` to determine the current day of the week and date.
    *   Extract the **context directory**: `jq -r '.context_dir' ~/.config/gtdev/config.json`.
2.  **Sync External Data**:
    *   **Sufficiency Check**: Run `teams messages stats` and check the "Latest Message" timestamp for active rooms.
    *   **Skip Logic**: 
        *   **Weekends**: If today is Sat/Sun and the database has messages up to Friday ~5:00 PM ET, inform the user and ask if a sync is necessary.
        *   **Business Hours**: Always attempt a sync during business hours. A 1-2 hour gap is unacceptable as project state changes rapidly.
    *   **Ad-hoc Option**: If syncing fails (e.g., token expired), offer to accept ad-hoc message text pasted by the user for the current report. Note that these won't be saved to the permanent JSON database but will be used for the current status report.
    *   If a sync is required and possible, execute the `teams-chat-sync` skill.
3.  **Determine Time Range**:
    *   **Current Business Day (T)**: If today is M-F, T is today. If today is Sat/Sun, T is the most recent Friday.
    *   **Prior Business Day (T-1)**: The business day immediately preceding T (e.g., if T is Monday, T-1 is Friday).
4.  **Gather Context**:
    *   **Prior Status**: Locate and read the status report for T-1 in the context directory.
    *   **Chat History**: Extract messages from all relevant rooms for T and T-1.
    *   **Source Control Activity**: The agent MUST actively run `git log --since="7 days ago"` and `gh pr list --state all --limit 20` (or similar commands) directly in the shell for the recognized **Contributed Repositories** (e.g., `org-repo-name`, `org-repo-name`, `org-tool-name`). The agent will parse this raw shell output in-memory to identify recent commits, author activities, and PR statuses. Do NOT create a python script for this; use the native CLI tools directly.
    *   **Engineering Events**: Identify significant actions (commits, build failures, issue resolutions) from the current session, combining them with the source control activity gathered above.
5.  **Create/Update Status Folder**:
    *   Target: `<context_dir>/daily/YYYY-MM-DD/` (where YYYY-MM-DD is T).
    *   Ensure the directory exists.
6.  **Generate `summary.md`**:
    *   Create or incrementally update `<context_dir>/daily/YYYY-MM-DD/summary.md`.
    *   **Constraint**: NEVER mention "Gemini" or "AI agent". Use professional, passive or first-person plural voice ("we", "the team").
    *   **Constraint**: Use **prettified relative hyperlinks** for any issue citations (e.g., `[Issue Title](./../../issues/MM-DD_ID_title.md)`). DO NOT show raw filenames or absolute paths in the text.
    *   **Traceability**: For each issue or blocker listed, indicate the **Impacted JIRA Story/Feature** (e.g., "Impacts PROJECT-12345").
    *   **Sections**:
        *   **Executive Summary**: 2-3 sentence high-level overview.
        *   **Key Accomplishments**: Bulleted list of completed items.
        *   **Issues & Blockers**:
            *   List each item with its Title (linked), Status, and the JIRA story it impacts.
        *   **Next Steps**: Action items for the next business day.

7.  **Export to Downloads**:
    *   Target: `~/Downloads/YYYY-MM-DD_Status/` (or mapped WSL path).
    *   Copy the entire `<context_dir>/daily/YYYY-MM-DD/` folder to the target.
8.  **Final Report**:
    *   Provide the user with a condensed summary of the update and the path to the exported files.

## Idempotency Rules
*   When updating `summary.md`, check for existing timestamped sections.
*   If an entry for the same issue/event exists, update its status rather than appending a duplicate.
*   Preserve all manually added notes or "Hand-off" sections found in existing files.
