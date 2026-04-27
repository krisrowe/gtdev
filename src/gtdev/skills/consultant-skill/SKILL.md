---
name: consultant-skill
description: Guide for developing and managing local, self-contained AI agent skills on a constrained workstation. Use when creating a new skill, updating an existing skill, or organizing reusable local assets.
---

# Developing Consultant Skills

## Default Posture: Constrained Local Footprint
As a consultant operating on client machines or constrained environments, skills must be self-contained locally without assuming access to external skill marketplaces or public repositories. All new skills are developed, stored, and installed directly from the local workstation's asset directory.

## Dynamic Configuration and Pathing
**CRITICAL:** NEVER hardcode user-specific paths (e.g., `/home/user`), project IDs, domains, GitHub organization names, or Kubernetes namespaces into the skills you generate. 

Instead, instruct the generated skill (or the agent using it) to dynamically resolve these values via the local `gtdev` configuration file, which follows XDG Base Directory specifications:
- Linux/macOS: `~/.config/gtdev/config.json`
- Windows: `%APPDATA%\gtdev\config.json` (or `~/.config/gtdev/config.json` in WSL)

This configuration file stores environment-specific values, such as:
```json
{
  "assets_dir": "/home/user/assets",
  "gcp_project": "project-management-id",
  "k8s_namespace": "my-namespace"
}
```

## Skill Output Location
When creating a new skill, read the `gtdev` config to determine the `assets_dir`. The new skill MUST be created in the `skills` subfolder of that directory:
`<assets_dir>/skills/<new-skill-name>/SKILL.md`

## Installation
Do not reference or use marketplace installation commands (like `em skills install`). Use local linking to maintain the footprint.

**For Gemini CLI:**
Use the native installation command which handles symlinking:
```bash
gemini skills install <assets_dir>/skills/<new-skill-name>
```

**For Other Agents (e.g., Claude Code):**
Manually create a symbolic link into the agent's configuration directory. For example:
```bash
ln -s <assets_dir>/skills/<new-skill-name> ~/.claude/skills/<new-skill-name>
```

## Skill Format: agentskills.io Standard
Skills use the [agentskills.io](https://agentskills.io/specification) open standard. A skill is a directory containing a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: my-skill
description: When to invoke this skill and what it does
---

Instructions for the agent...
```

### Required Fields
- `name` — lowercase, hyphens, 1-64 chars, must match directory name
- `description` — tells the agent when to invoke. Be specific about triggers.

### Optional Platform Fields
These are platform extensions:
- `disable-model-invocation: true` — user-only / slash-only, agent won't auto-invoke.
- `user-invocable: false` — ambient-only, hidden from slash menu.
- `allowed-tools: Bash, Read` — pre-approved tools.

## Writing Good Skill Instructions
- **Be specific about when to activate.** The `description` field is how agents decide to invoke. Include trigger phrases and scenarios.
- **Keep it focused.** One skill, one purpose. If it does two unrelated things, split it into two skills.
- **Include examples** of commands, workflows, or outputs the agent should produce.
