---
name: capture-project-context
description: Comprehensive daily status update. Captures session context (decisions, changes, TODOs) AND integrates recent MS Teams chat summaries into the daily project status file (daily/YYYY-MM-DD/summary.md).
---

# Capture Project Context

This is the primary skill for persisting work and communication context. It creates a unified, timestamped update in the daily status log.

## Dependencies
*   **MS Teams**: It is highly recommended to run the `teams-chat-sync` skill *before* this skill to ensure the chat summary includes the latest messages.

## Configuration
*   **Target Directory**: Configured in `~/.config/gtdev/config.json` under `context_dir`.
*   **File Format**: `daily/YYYY-MM-DD/summary.md`.

## Workflow

1.  **Locate Context Directory**: 
    *   Read `~/.config/gtdev/config.json` to find `context_dir`.
2.  **Determine Target File**:
    *   Target Folder: `<context_dir>/daily/$(date +%Y-%m-%d)/`.
    *   Target File: `<context_dir>/daily/$(date +%Y-%m-%d)/summary.md`.
    *   Initialize the folder and the file with a header if they do not exist.
3.  **Gather Context (Session & Teams)**:
    *   **Engineering Events**: Identify every significant event in the session (new issue found, code change, test run, deployment). **CRITICAL**: Record the exact date/time, the specific issue/ticket involved, and the status change (e.g., "In Progress" to "Resolved").
    *   **Teams Data**: Review recently synced MS Teams messages. Extract technical discussions, blockers, or external decisions.
4.  **Idempotent Update**:
    *   Append a new timestamped section `## Status Update - <Time>`.
    *   **Sub-section: Overall Day Summary**: A high-level 2-3 sentence overview of the day's progress.
    *   **Sub-section: Issue Status Matrix**: A table or list showing each issue worked on, its starting status, and its current status (including resolution date/time if applicable).
    *   **Sub-section: Detailed Event Log**: A chronological list of specific actions taken, who was involved (if from Teams), and the exact timestamp for each status change or new issue discovery.
    *   **Sub-section: Open TODOs**: List updated action items.
    *   NEVER remove or replace existing content. Always append to the log.
