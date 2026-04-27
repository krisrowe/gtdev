# Project Context: {{PROJECT_NAME}} ({{JIRA_ID}})

<!-- 
AGENT INSTRUCTION:
If you find any double-brace placeholders like {{PLACEHOLDER}} in this file, 
you MUST inform the user immediately that the project context is incomplete 
and ask them to provide the missing details before proceeding with complex tasks.
-->

This file captures project-specific constraints, architectural realities, known issues, and conventions.

## Team Branching & PR Strategy

### 1. Core Workflow Rules
- **Always Isolate:** Never commit directly to a base branch. Always create a new branch.
- **Sync First:** Before branching, checkout the base branch and `git pull`.
- **PR Cleanliness:** Do not mention internal tools ("Gemini", "gtdev") in PR titles, bodies, or comments.

### 2. Repository-Specific Targets
| Repository | Base / Source Branch | Target Branch (PR) |
| :--- | :--- | :--- |
| {{REPO_NAME}} | {{BASE_BRANCH}} | {{TARGET_BRANCH}} |

### 3. Branch Naming Conventions
- **Features:** `feature/{{JIRA_ID}}/short-description`
- **Fixes:** `fix/{{JIRA_ID}}/short-description`

## Known Constraints & Realities
- **Namespace:** {{K8S_NAMESPACE}}
- **Cluster:** {{K8S_CLUSTER}}

## Workspace Conventions
- **Overrides Source:** {{OVERRIDES_PATH}}

## References
- **Status Reports:** `daily/YYYY-MM-DD/summary.md`
- **Detailed Issues:** `issues/MM-DD_ID_title.md`
