---
name: setup-machine
description: Orchestrates the initial setup or repair of the local workstation agent environment. Use when asked to "setup this machine", "fix my environment", or when initializing a new workstation.
---

# Setup Machine

This skill automates the idempotent installation of the global context and agent skills.

## Workflow

1.  **Locate Assets**:
    *   Find the `assets` directory (typically `~/assets`).
2.  **Execute Install Script**:
    *   Run the `./install setup` command from the root of the `assets` directory.
    *   **Note**: This command will link the global `GEMINI.md` and all managed skills. It will fail safely if a non-empty `GEMINI.md` file already exists.
3.  **Verify & Reload**:
    *   After the command completes, advise the user to run `/skills reload` in their interactive session.
4.  **Optional Tool Installation**:
    *   If the user also needs technical tools, offer to run `./install tools gtdev` or other managed tools.

## Safety Constraints
*   Do NOT attempt to manually link `GEMINI.md` if the script fails. The script's failure indicates a conflict that requires human intervention.
