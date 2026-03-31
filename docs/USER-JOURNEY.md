# User Journey: Getting Started with gtdev

This document walks through a typical user experience with `gtdev`, from installation to advanced troubleshooting.

## Why Focusing on Local Workspace Matters
In large organizations, there can be hundreds of repositories and builds. Remembering many identifiers or tracking which branch is active across multiple projects can lead to team confusion and high cognitive load. `gtdev` simplifies this by focusing ONLY on the repositories you have cloned locally. No more noise, just the code you are actively working on.

## 1. Installation
A user installs `gtdev` globally using `pipx` to ensure it's available in their PATH without interfering with other Python projects.

```bash
pipx install git+https://github.com/krisrowe/gtdev.git
```

## 2. Initialization
The user initializes the tool with their GitHub organization. This step validates their `gh` CLI setup and discovers any relevant environment guidance.

```bash
$ gtdev init --github-owner=acme-corp
Initialized workspace at /Users/user/.config/gtdev
Validating GitHub access for 'acme-corp'...
✅ GitHub access confirmed for 'acme-corp'.
Found 3 repos local (run 'gtdev repos list' to see these)
Configuration saved for owner: acme-corp
```

## 3. Environment Setup (Optional)
If the organization has a matching "fruit profile" (e.g., `pitaya`), `gtdev` provides specific guidance. The user can check their status and install missing dependencies explicitly.

```bash
$ gtdev init
--- Setup Guidance: Pitaya ---
Enterprise environment with DNF package management.

✅ 1. Install GitHub CLI
   Command: sudo dnf install -y gh
❌ 2. Configure Shell Path
   Command: echo "export PATH=\$PATH:~/.local/bin" >> ~/.bashrc
----------------------------------------
Some steps are missing. Use 'gtdev init --install-dependencies' to execute them.

$ gtdev init --install-dependencies
▶ Running: Configure Shell Path
  Command: echo "export PATH=\$PATH:~/.local/bin" >> ~/.bashrc
Proceed? [y/N]: y
✅ Successfully completed 'Configure Shell Path'
```

## 4. Repository Discovery
The user lists their local repositories. `gtdev` automatically filters the list to the default owner set during `init`.

```bash
$ gtdev repos list
Filtering by owner: acme-corp
Listing locally cloned repositories tracking origin:
NAME                             GITHUB REPO                     LOCAL PATH
----------------------------------------------------------------------------------------------------
phoenix--apigee-gcp-infra        phoenix--apigee-gcp-infra       ~/src/acme/phoenix--apigee-gcp-infra
phoenix-apigee-hybrid-deploy     phoenix-apigee-hybrid-deploy     ~/src/acme/phoenix-apigee-hybrid-deploy
phoenix-apigee-apis-cicd         phoenix-apigee-apis-cicd         ~/src/acme/phoenix-apigee-apis-cicd
```

## 5. Tracking Builds
The user wants to see the status of recent CI/CD runs across their Apigee projects.

```bash
$ gtdev builds list --limit=3
Filtering by owner: acme-corp
ID           ⚡  REPO                      BRANCH          CREATED      TITLE
--------------------------------------------------------------------------------------------------------------
123456781    ⏳  phoenix-apigee-hybrid...  main            03/31 10:15  Validate Hybrid Config
123456789    ✅  phoenix-apigee-apis-cicd  main            03/31 10:00  Deploy proxies to prod
123456780    ❌  phoenix--apigee-gcp-i...  feat/lb-config  03/31 09:45  Provision GCP Resources
```

## 6. Investigating a Failure
The user sees a failed build (`123456780`) and investigates the details.

```bash
$ gtdev builds show 123456780
Build ID: 123456780
Repo:     acme-corp/phoenix--apigee-gcp-infra
Status:   ❌ completed (failure)
Branch:   feat/lb-config
Workflow: Infra Provisioning
Title:    Provision GCP Resources
----------------------------------------
To view logs:
  gtdev logs --repo=acme-corp/phoenix--apigee-gcp-infra --id=123456780
```

## 7. Fixing and Re-triggering
After fixing the local code and pushing the change, the user can re-trigger the workflow directly.

```bash
$ git commit -am "fix: correct load balancer health check port" && git push
...
$ gtdev builds show 123456780
...
To trigger this workflow again:
  gh workflow run "Infra Provisioning" --repo acme-corp/phoenix--apigee-gcp-infra --ref feat/lb-config
```

The user runs the suggested command and confirms the new build passes.
