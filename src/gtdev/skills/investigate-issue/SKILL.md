---
name: investigate-issue
description: Standardized process for investigating a technical issue. Scans logs, identifies root causes, and documents findings in a structured format within the daily status folder. Use when asked to "look into an issue", "debug a failure", or "investigate PTIDE-XXXXX".
---

# Investigate Issue

This skill provides a structured approach to technical troubleshooting and ensures findings are persisted for daily status reporting.

## Workflow

1.  **Define Scope**:
    *   Identify the Issue ID (e.g., PROJECT-12345) and a brief description of the symptoms.
2.  **Information Gathering & Incremental Persistence**:
    *   **Save-As-You-Go**: After each tool call or search that yields a relevant finding, **pause and immediately append it** to the investigation log (`issues/MM-DD_<ID>_short-title.md`). 
    *   **Rationale**: This ensures that even if you get stuck or the session is interrupted, your findings are already persisted and can be picked up in a new session.
    *   **Logs**: Search relevant log files in `org-repo-name` or other reference repositories.
    *   **Chats**: Search MS Teams messages for mentions of the issue or similar symptoms.
    *   **Historical Context & Known Constraints**: You MUST actively use `grep` to search through `<context_dir>/issues/` and `<context_dir>/daily/` for keywords related to your findings or any observed limitations (e.g., RBAC errors, missing permissions, specific component names).
    *   **Rationale for Context**: The project has established workarounds and known realities (e.g., lacking cluster-wide access, operating strictly within specific namespaces). Searching past context ensures you do not prematurely report these known baseline realities as "new" bugs or suggest incorrect, impossible next steps.
3.  **Iterative Analysis**:
    *   Cross-reference any suspected "root causes" against the known constraints found in your historical grep search.
    *   As you gather findings, update the "Root Cause Analysis" or "Proposed Fix" sections of the log file iteratively.
    *   Document reproduction steps as they are identified.
4.  **Documentation**:
    *   Target: `<context_dir>/issues/MM-DD_<ID>_short-title.md`
    *   **Format Rules**:
        *   If the issue is a JIRA bug, use the full JIRA ID (e.g., `04-19_PROJECT-12345_auth-failure.md`).
        *   If no JIRA ID exists yet, use a descriptive slug.
    *   **Traceability**: Explicitly document the "Impacted Feature/User Story" (e.g., "Impacts PROJECT-12345 - Cloud Platform Deployment").
    *   **Continuous Logging**: Treat this file as a **running detailed log** of all relevant findings. Append each significant discovery *without loss* immediately after it is found.
    *   **Entry Format**: Prefix each entry with the date/time in ET: `MM/DD h:mmam/pm ET - <Finding>` (e.g., `4/19 4:17pm ET - found xyz in the kubectl logs output for watcher service suggesting role grant missing for xyz`).
    *   **Sections**:
        *   **Title & Impacted JIRA Story**
        *   **Issue Description & Symptoms**
        *   **Running Investigation Log** (The primary chronological list of all findings)
        *   **Root Cause Analysis**
        *   **Proposed Fix / Resolution**
5.  **Integration**:
    *   Update the `summary.md` for the current business day to include the issue.
    *   **Constraint**: Use a prettified link (e.g., `[Auth Failure in Operator](./../../issues/04-19_PROJECT-12345_auth-failure.md)`) so the raw filename is not visible in the rendered text.

## Privacy & Standards
*   NEVER mention "Gemini" or "AI".
*   Use relative paths only for links.
*   Protect sensitive data (secrets, PII) when copying logs.
