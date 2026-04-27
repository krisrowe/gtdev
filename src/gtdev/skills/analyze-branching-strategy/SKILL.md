---
name: analyze-branching-strategy
description: Analyzes the branching strategy, branch naming conventions, PR targets, and author/approver patterns for the projects the team contributes to. It also provides actionable guidance on how to create a new branch or commit for a fix based on historical evidence.
---

# Analyze Branching Strategy

This skill outlines the process for identifying and adhering to the branching conventions and Pull Request (PR) workflows of a project based on empirical repository data.

## Workflow: Strategic Research

Before making any changes, you must systematically map the repository's workflow using the following steps:

### Step 1: Identify Active Contributors
Determine who the primary contributors are to understand whose patterns you should follow.
```bash
git log --since="1 month ago" --format="%ae" | sort | uniq -c | sort -nr | head -n 5
```

### Step 2: Determine Base Branch Strategy
Identify which branch is the primary target for development and releases.
```bash
# Check recent merged PRs to see the 'base' (target) branch
gh pr list --state merged --limit 10 --json baseRefName,headRefName
```
*Observe if PRs target `main`, `master`, `develop`, or a specific `release/*` branch.*

### Step 3: Map Naming Conventions
Analyze the naming patterns for branches and PR titles.
```bash
# Check branch naming patterns
git branch -a --list 'origin/*' | head -n 20

# Check PR titles and descriptions
gh pr list --state all --limit 10 --json title,headRefName
```
*Common patterns to look for: `feature/<ID>/<desc>`, `fix/<desc>`, `hotfix/<version>`, or `<ID>-<desc>`.*

### Step 4: Identify Review/Approval Patterns
Understand how changes are merged and who the key reviewers are.
```bash
gh pr list --state merged --limit 10 --json author,mergedBy
```
*Note if authors merge their own work or if a second party is always involved (indicating a required review).*

## Actionable Guidance: Applying a Fix

When applying a fix, adhere to the patterns discovered in the Research phase:

1.  **Always Isolate Changes:** Never commit directly to a shared base branch. Always create a new, descriptive branch.
2.  **Synchronize with Base:** Always branch off the latest state of the identified target branch (e.g., `main` or `develop`).
3.  **Follow Naming Standards:** Use the prefix (`feature/`, `fix/`, `chore/`) and ID format (e.g., ticket numbers) consistent with the repo's history.
4.  **Target the Correct Branch:** When opening the PR, ensure the `--base` flag matches the repository's established integration branch.

### Template Execution Flow
```bash
# 1. Update local base
git checkout <base_branch>
git pull origin <base_branch>

# 2. Create isolated branch
git checkout -b <prefix>/<id>/<short-description>

# 3. Implement, commit, and push
git add .
git commit -m "<type>(<scope>): <short description>"
git push -u origin <prefix>/<id>/<short-description>
```
