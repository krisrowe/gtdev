# Agent Environment Configuration

> **Note:** This file provides the primary global context for the Gemini CLI agent and its local workstation setup. It is typically imported via a loader file at `~/.gemini/GEMINI.md`.

## Context Separation Policy
- **Global Context (this file)**: Contains instructions for tooling, agent behaviors, workspace management, and skill coordination.
- **Project Context (`PROJECT-CONTEXT.md`)**: Contains project-specific constraints, architectural facts (e.g., node names, WIF patterns, namespace limits), and known technical issues. This file should be located in the workspace root.
- **Task-Specific Context**: Detailed findings, logs, and investigation steps go into `issues/` or `daily/` reports. Do not clutter the project or global context with one-off findings.

## Workspace Management
- **Workspace Root**: The parent directory where repositories are cloned. Launch Gemini from this root or a subdirectory to ensure hierarchical context loading.
- **Dynamic Paths**: Avoid hardcoding absolute paths in project files or tools. Use relative paths or resolve paths dynamically via the `gtdev` SDK, `config.json` settings (e.g., `context_dir`, `assets_dir`, `workspace_dir`, `chats_dir`), or native Python libraries.
- **Downloads Directory**: Resolve dynamically based on the current user environment (e.g., `/mnt/c/Users/$USER/Downloads` in WSL) rather than hardcoding specific user IDs or wildcards.

## Professional Communication & Governance
- **Internal Tools**: NEVER mention "Gemini", "gtdev", "cli", or other internal tool names in Pull Request titles, bodies, comments, status write-ups, investigation logs, or any other `.md` files that are not part of internal tooling documentation. 
- **Process Noise & Meta-Reporting**: Do not document local-only activities such as "syncing Teams chats", "running local git fetch", or "preparing reports". **Never include meta-information about the reporting process itself** (e.g., "Status report updated", "Carried over from yesterday"). Shared reports must only contain external project facts, findings, and technical status.
- **Timestamp Accuracy**: Always verify the current time based on the **Eastern Time zone (ET)** in North America before including timestamps. NEVER hallucinate or predict dates/times. If a timestamp is used, it must reflect the exact moment the event occurred or the current moment of recording.
- **No Future Reporting**: Never describe events that have not yet happened.
- **Tone**: Maintain a professional, technical, and objective tone. Use "we" or "the team" to describe actions.

## Repository Management
- **Explicit Approval Required**: Never clone a new repository locally without asking for the user's explicit approval first.
- **Organization Repositories**: Clone organization repositories (e.g., `Acme-Corp`) as siblings in the primary workspace directory.
- **OSS Repositories**: Non-organizational repositories should be cloned to a dedicated `~/oss/` directory.

## CLI & MCP Development Workflow
When making code changes to local Python-based CLI tools (e.g., `gtdev`, `teams-cli`) or MCP servers (e.g., `gtdev-mcp`):
- **Editable Install**: ALWAYS install local repositories in editable mode using `pipx install -e <path> --force`. This ensures that your changes are immediately reflected in the global binaries without requiring a re-install.
- **Verification**: After installation, verify the binary path with `which <command>` (should point to `~/.local/bin/`).

## MS Teams Sync Protocol
- **Database Sync**: Use the `teams-chat-sync` skill to update the local message archive. The underlying `teams-cli` handles deduplication automatically.
- **Contextual Export**: When needed for status reports or analysis, export recent relevant chat blocks to the directory specified by `chats_dir` in your configuration.
- **Archive Integrity**: Rely on the CLI sync to manage state; do not manually edit the local JSON storage.
