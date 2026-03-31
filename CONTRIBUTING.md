# Contributing to gtdev

Thank you for your interest in improving `gtdev`! This document outlines how to contribute new environment profiles (Fruit Profiles) while maintaining the privacy and portability standards of the project.

## Adding New Fruit Profiles

Profiles are non-descript JSON files stored in `src/gtdev/profiles/`. They provide environment-specific setup guidance without naming organizations or specific users.

### 1. Naming Convention
We use exotic fruit names for profiles, with a preference for **Latin American fruits** (e.g., `maracuya`, `guava`, `plantain`, `acerola`, `pitaya`). This ensures that the profile name itself doesn't reveal the target organization.

### 2. Profile Structure
A profile should follow this JSON structure:

```json
{
  "owner_hash": "sha256_hash_of_github_owner",
  "name": "fruit_name",
  "description": "Short, neutral description of the environment type.",
  "guidance": [
    {
      "step": "Descriptive name of the setup step",
      "command": "The actual shell command to run",
      "check": "A lightweight command to verify if the step is already complete",
      "notes": "Optional context or warnings for the user"
    }
  ],
  "package_manager": "e.g., dnf, homebrew, apt",
  "shell_profile": "e.g., ~/.bashrc, ~/.zshrc"
}
```

### 3. Secure Owner Matching (`owner_hash`)
To maintain anonymity, we do **not** store GitHub owner names (users or organizations) directly. Instead, we use a SHA-256 hash.

To generate a hash for a new organization:
```bash
echo -n "my-org-name" | shasum -a 256
```
Place the resulting hex string in the `owner_hash` field. This allows `gtdev init --github-owner=my-org-name` to discover the profile locally without the repository ever containing the string "my-org-name".

### 4. Step Design
- **Idempotency**: Commands should ideally be safe to run multiple times.
- **Check Commands**: The `check` field is used to show a `✅` or `❌` in the CLI. Common checks include `command -v <tool>` or `grep -q "pattern" ~/.bashrc`.
- **Sudo & Privileges**: 
    - **Never run `gtdev` as `sudo`**: Doing so will cause configuration files (like `~/.config/gtdev/config.json`) to be owned by `root`, which breaks normal user access.
    - **Use `sudo` inside the profile**: If a specific setup step requires elevated privileges (e.g., `sudo dnf install`), include `sudo` in the `command` field of that step.
    - **Interactivity**: `gtdev` runs these commands as subprocesses attached to your terminal, so they will correctly prompt for your password when needed.

### 5. Installation Policy
- **No Automatic Installs**: `gtdev` must **NEVER** automatically attempt to install software or modify the workstation environment without explicit user direction.
- **Explicit Flags**: Any action that performs an installation must be triggered by a command or option that explicitly uses the word `install` (e.g., `--install-dependencies`).
- **Guidance First**: The default behavior of `gtdev init` is to provide guidance and status checks. It should only attempt to run setup commands if the user provides the explicit installation flag.

## Privacy & Purity Standards

- **No Real Names**: Never include real organization names, project names, or user identities in the profile content, descriptions, or commit messages.
- **Generic Placeholders**: Use `myorg`, `myuser`, or `<GH_OWNER>` when providing examples in documentation or test data.
- **Local Paths**: Never hardcode absolute local paths (e.g., `/Users/yourname/...`). Use `~` or environment variables instead.

## Testing Your Changes
After adding a profile, verify it is discoverable:
```bash
# Verify discovery via owner name (should announce match)
gtdev init --github-owner=the-org-you-hashed

# Verify silent behavior for unknown owners
gtdev init --github-owner=unknown-org

# Verify forced application (alternative when owner is not hashed)
gtdev init --profile=fruit_name
```

### Initialization Rules
- **Idempotency**: `gtdev init` is idempotent. Re-running it will update the default owner but will **not** overwrite an existing active profile unless `--profile` is used.
- **Silent Discovery**: Profile discovery via `--github-owner` is silent on failure. If no profile matches the owner's hash, `gtdev` simply updates the owner and continues without mentioning profiles.
- **Discovery Announcement**: If a profile *is* discovered and applied, `gtdev` clearly announces the match to the user.
- **Manual Override**: The `--profile` flag serves as a manual override and an alternative for environments where the GitHub owner name has not yet been added to a profile's `owner_hash` list.

## Philosophies on Tests & AI Tooling

### 1. Sociable Unit Tests
We prefer **Sociable Unit Tests** over solitary unit tests. Tests for the CLI (e.g., in `tests/unit/test_cli.py`) invoke the real CLI commands and let them call the SDK naturally. This ensures we test the interaction between CLI and SDK, verifying real behaviors.
- **Limit Mocking**: Only mock external system boundaries (GitHub API calls, subprocess runs, file system if needed) where necessary. Do not mock internal SDK functions unless there is a very good reason (e.g., simulating complex failures).

### 2. User & Contributor Perspectives
Always maintain a clean separation of concerns:
- **User Perspective**: CLI output should be clean, concise, and helpful. Minimize noise (no unnecessary identifiers or lists).
- **Contributor Perspective**: Interfaces should be predictable and testable.

### 3. AI Assisted Maintenance (Gemini CLI)
Since this repository is maintained using the Gemini CLI and AI assistants, we enforce clarity through local context files (like `.gemini/settings.json` or project-specific instructions in `docs/`).
- **Encourage Gemini usage**: Contributors are encouraged to use Gemini CLI to maintain and extend the repository, following the guidelines set in this documentation.
- **Verify before push**: Always run `make test` before pushing to ensure AI changes haven't introduced regressions.
