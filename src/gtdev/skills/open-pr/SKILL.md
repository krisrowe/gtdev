---
name: open-pr
description: Prepare a Pull Request using the workspace's observed branching strategy. Use this when the user asks to open a PR or raise a PR. It creates the branch and commits but leaves the final PR creation command for the user to execute.
---

# Open PR Skill

This skill outlines the process for making changes and preparing a Pull Request (PR) in the workspace repositories. It adheres strictly to the observed team branching strategies and **must end by giving the user a ready-to-run command.**

## Core Mandates
1. **NEVER execute `gh pr create` yourself.** You must prepare the branch, push the changes, and formulate the exact `gh pr create` command. Present this command to the user to copy and paste into their own terminal.
2. **Research First.** Always analyze the specific repository's recent history to derive the correct branching conventions and base branch before starting.

## Workflow

When asked to raise or open a PR, follow these exact steps:

### Step 1: Research the Repository's Strategy
Before doing any work, determine the repository's active base branch (`main` vs `develop`) and how branches are typically named.

```bash
# 1. Checkout the primary branch (main, master, or develop) and pull the latest
git checkout main || git checkout develop || git checkout master
git pull --no-edit

# 2. Check recent PRs to see what branches they merge into (the base)
gh pr list --state all --limit 5

# 3. Check recent branch naming conventions
git log --oneline --graph --decorate --all -n 10
```

### Step 2: Create the Branch
Based on your research in Step 1, create a branch that follows the repository's convention. 
- Typical patterns observed in the workspace include: `feature/<JIRA-TICKET>/<description>`, `fix/<description>`, or `scratch/<description>`.
- Checkout the new branch off the appropriate base branch.

```bash
git checkout -b <derived_branch_name>
```

### Step 3: Implement and Commit
Make the necessary changes to the codebase requested by the user, add the files, and commit.

```bash
# Make file changes...
git add .
git commit -m "<Clear, descriptive commit message based on changes>"
```

### Step 4: Push the Branch
Push the branch to the remote repository.

```bash
git push -u origin <derived_branch_name>
```

### Step 5: Generate the PR Command (Do Not Execute)
Construct the `gh pr create` command based on the work done. You must explicitly instruct the user to copy and paste this command into their terminal.

**Example Output:**

"The branch has been pushed. I am not allowed to open the PR for you directly. Please review and run the following command in your terminal to open the PR:

\`\`\`bash
gh pr create \
  --base <target_base_branch_identified_in_step_1> \
  --head <your_new_branch_name> \
  --title "<Clear PR Title>" \
  --body "<Detailed description of the changes made>"
\`\`\`
"