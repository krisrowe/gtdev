import click
import os
import json
import subprocess
from datetime import datetime
from functools import wraps
from gtdev import sdk

def format_path(path):
    """Converts absolute path to tilde-relative if under home."""
    home = os.path.expanduser('~')
    if path.startswith(home):
        return path.replace(home, '~', 1)
    return path

def get_status_icon(status, conclusion):
    """Returns a concise icon for build status."""
    if status != "completed":
        return "⏳"
    if conclusion == "success":
        return "✅"
    if conclusion == "failure":
        return "❌"
    if conclusion == "cancelled":
        return "🚫"
    return "❓"

def format_date(date_str):
    """Formats ISO date to M/DD HH:MM."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%m/%d %H:%M')
    except Exception:
        return date_str

def format_guidance(profile, pm):
    """Prints guidance from a profile with status checks."""
    click.echo(f"\n--- Setup Guidance: {profile['name'].capitalize()} ---")
    click.echo(profile.get("description", ""))
    click.echo("")
    
    results = pm.check_status(profile)
    all_passed = True
    for i, (step, passed) in enumerate(results, 1):
        status = "✅" if passed else "❌"
        if not passed: all_passed = False
        
        click.secho(f"{status} {i}. {step['step']}", bold=True)
        click.secho(f"   Command: {step['command']}", fg="yellow")
        if step.get("notes"):
            click.echo(f"   Note:    {step['notes']}")
            
    click.echo("-" * 40)
    if not all_passed:
        click.secho("Some steps are missing. Use 'gtdev init --install-dependencies' to execute them.", fg="cyan")
    else:
        click.secho("All setup steps appear to be complete.", fg="green")

def run_guidance(profile, pm):
    """Interactively runs missing commands from a profile."""
    results = pm.check_status(profile)
    completed = []
    failed = []
    
    for step, passed in results:
        if passed:
            click.echo(f"✅ Step '{step['step']}' already complete.")
            continue

        click.secho(f"\n▶ Running: {step['step']}", bold=True)
        click.secho(f"  Command: {step['command']}", fg="yellow")
        
        if click.confirm("Proceed?"):
            try:
                # Use shell=True for pipes/redirects
                subprocess.run(step["command"], shell=True, check=True)
                completed.append(step['step'])
                click.secho(f"✅ Successfully completed '{step['step']}'", fg="green")
            except subprocess.CalledProcessError as e:
                failed.append(step['step'])
                click.secho(f"❌ Error running command: {e}", fg="red")
                if not click.confirm("Continue to next step?"):
                    break
        else:
            click.echo(f"Skipped '{step['step']}'.")

    click.echo("\n--- Setup Summary ---")
    if completed:
        click.echo("Completed:")
        for c in completed: click.echo(f"  - {c}")
    if failed:
        click.secho("Failed:", fg="red")
        for f in failed: click.echo(f"  - {f}")
    
    final_status = pm.check_status(profile)
    if all(passed for _, passed in final_status):
        click.secho("\n✨ Environment setup is now complete!", fg="green", bold=True)
    else:
        click.secho("\n⚠  Environment setup is still incomplete.", fg="yellow")

def check_profile_status(pm, cm):
    """Checks for missing setup steps and warns the user."""
    if not cm.active_profile:
        return True
        
    profile = pm.get_profile(cm.active_profile)
    if not profile:
        return True
        
    results = pm.check_status(profile)
    missing = [step['step'] for step, passed in results if not passed]
    if missing:
        click.secho(f"⚠️  Missing setup steps for profile '{cm.active_profile}':", fg="yellow", err=True)
        for m in missing:
            click.echo(f"  - {m}", err=True)
        click.secho("Run 'gtdev init --install-dependencies' to complete your environment setup.", fg="cyan", err=True)
        click.echo("", err=True)
        return False
    return True

def ensure_initialized():
    """Decorator to ensure the tool is initialized before running a command."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cm = sdk.ConfigManager()
            if not cm.default_owner:
                click.secho("❌ Error: gtdev is not initialized.", fg="red", err=True)
                click.echo("Please run 'gtdev init --github-owner=<your-org-or-user>' to get started.", err=True)
                click.get_current_context().exit(1)
            return f(*args, **kwargs)
        return wrapper
    return decorator

@click.group()
def main():
    """gtdev CLI."""
    # Discourage running the tool itself as root/sudo
    if os.getuid() == 0:
        click.secho("WARNING: Running gtdev with sudo/root privileges is discouraged.", fg="yellow", err=True)
        click.secho("This can result in configuration files being owned by root.", fg="yellow", err=True)
        click.echo("", err=True)

@main.command()
@click.option("--github-owner", help="GitHub user or organization name.")
@click.option("--profile", help="Force a specific fruit profile (e.g., maracuya).")
@click.option("--install-dependencies", is_flag=True, help="Interactively run missing setup commands.")
def init(github_owner, profile, install_dependencies):
    """Initialize or update the gtdev workspace and environment."""
    click.echo(sdk.init_workspace())
    
    pm = sdk.ProfileManager()
    cm = sdk.ConfigManager()
    
    # Validation and Owner Update
    if github_owner:
        click.echo(f"Validating GitHub access for '{github_owner}'...")
        success, message, count = sdk.validate_github_access(github_owner)
        if not success:
            click.secho(f"❌ {message}", fg="red", err=True)
            click.get_current_context().exit(1)
        
        click.secho(f"✅ {message}", fg="green")
        
        # Count local repos found for this owner to focus on local workspace
        local_repos = sdk.find_local_repos(owner=github_owner)
        click.secho(f"Found {len(local_repos)} repos local (run 'gtdev repos list' to see these)", fg="cyan")
        cm.default_owner = github_owner
        
        # Profile discovery (only if no active profile and not forced)
        if not cm.active_profile and not profile:
            matched = pm.match_by_owner(github_owner)
            if matched:
                cm.active_profile = matched["name"]
                click.secho(f"Discovered and matched profile '{matched['name']}' for owner '{github_owner}'.", fg="cyan")
    
    # Requirement Check
    if not cm.default_owner:
        click.secho("❌ Error: --github-owner is required for initialization.", fg="red", err=True)
        click.echo("Usage: gtdev init --github-owner=<your-org-or-user>", err=True)
        click.get_current_context().exit(1)

    # Manual Profile Override
    if profile:
        target = pm.get_profile(profile)
        if target:
            cm.active_profile = profile
            click.secho(f"Active profile set to '{profile}'.", fg="cyan")
        else:
            click.secho(f"Profile '{profile}' not found.", fg="red")
            click.get_current_context().exit(1)

    cm.save()
    click.secho(f"Configuration saved for owner: {cm.default_owner}", fg="green")

    # Show Guidance
    if cm.active_profile:
        target_profile = pm.get_profile(cm.active_profile)
        if target_profile:
            if install_dependencies:
                run_guidance(target_profile, pm)
            else:
                format_guidance(target_profile, pm)
        else:
            click.echo(f"Active profile '{cm.active_profile}' no longer exists.")

@main.group()
def github():
    """Manage GitHub settings and identity."""
    pass

@github.command(name="show")
@ensure_initialized()
def github_show():
    """Show current GitHub configuration and matched profile."""
    cm = sdk.ConfigManager()
    pm = sdk.ProfileManager()
    
    click.echo(f"Default Owner: {cm.default_owner}")
    if cm.active_profile:
        profile = pm.get_profile(cm.active_profile)
        click.echo(f"Active Profile: {cm.active_profile}")
        if profile:
            click.echo(f"Description:    {profile.get('description', '')}")
    else:
        click.echo("Active Profile: (none)")

@main.group()
def config():
    """Manage gtdev configuration."""
    pass

@config.command(name="show")
@ensure_initialized()
def config_show():
    """Show current configuration."""
    cm = sdk.ConfigManager()
    click.echo(f"Config Directory: {cm.config_dir}")
    click.echo(f"Default Owner:    {cm.default_owner}")
    click.echo("Search Roots:")
    for root in cm.search_roots:
        click.echo(f"  - {format_path(root)}")

@config.command(name="add-root")
@ensure_initialized()
@click.argument("path")
def config_add_root(path):
    """Add a directory to the repository search paths."""
    cm = sdk.ConfigManager()
    cm.add_root(path)
    cm.save()
    click.echo(f"Added search root: {path}")

@config.command(name="remove-root")
@ensure_initialized()
@click.argument("path")
def config_remove_root(path):
    """Remove a directory from the repository search paths."""
    cm = sdk.ConfigManager()
    cm.remove_root(path)
    cm.save()
    click.echo(f"Removed search root: {path}")

@main.group()
def repos():
    """Manage local and GitHub repositories."""
    pass

@repos.command(name="list")
@ensure_initialized()
@click.option("--pattern", default="*", help="Filter by name or GitHub simple name.")
@click.option("--owner", help="Filter by GitHub owner.")
def list_repos_cmd(pattern, owner):
    """List local repositories and their GitHub mappings."""
    cm = sdk.ConfigManager()
    pm = sdk.ProfileManager()
    check_profile_status(pm, cm)
    
    effective_owner = owner or cm.default_owner
    
    if effective_owner != "all":
        click.secho(f"Filtering by owner: {effective_owner}", fg="cyan")
    
    click.secho("Listing locally cloned repositories tracking origin:", fg="cyan")

    repos = sdk.find_local_repos(pattern=pattern, owner=owner)
    
    if not repos:
        click.echo("No repositories found.")
        if effective_owner != "all":
            click.echo(f"Tip: Try --owner=all or 'gtdev init --github-owner=<new_owner>' to change filtering.")
        click.echo(f"Tip: Use 'gtdev config add-root <path>' if your repos are in a custom location.")
        return

    header = "%-25s %-30s %s" % ("NAME", "GITHUB REPO", "LOCAL PATH")
    click.echo(header)
    click.echo("-" * 100)
    for r in repos:
        path = format_path(r["path"])
        gh_repo = r["github_repo"]
        if effective_owner != "all" and gh_repo.startswith(f"{effective_owner}/"):
            gh_repo = gh_repo.replace(f"{effective_owner}/", "", 1)
        click.echo("%-25s %-30s %s" % (r["name"], gh_repo, path))

@main.group()
def builds():
    """Query GitHub Action builds."""
    pass

@builds.command(name="list")
@ensure_initialized()
@click.option("--repo", default="*", help="GitHub simple name or pattern.")
@click.option("--owner", help="Filter by GitHub owner.")
@click.option("--user", help="Contains match on email, name, or triggering actor.")
@click.option("--user-max-age", type=int, help="Max age in hours for commits from current user.")
@click.option("--limit", default=10, type=int, help="Number of builds to show.")
@click.option("--refresh", is_flag=True, help="Skip cache and fetch fresh data.")
def list_builds_cmd(repo, owner, user, user_max_age, limit, refresh):
    """List recent builds for repositories."""
    cm = sdk.ConfigManager()
    pm = sdk.ProfileManager()
    check_profile_status(pm, cm)
    
    effective_owner = owner or cm.default_owner

    if effective_owner != "all":
        click.secho(f"Filtering by owner: {effective_owner}", fg="cyan")

    all_repos = sdk.find_local_repos(pattern=repo, owner=owner)
    
    if not all_repos:
        click.echo(f"No repositories matching '{repo}' found.")
        return

    identities = sdk.get_current_identities() if user_max_age else []
    all_runs = []
    
    for r in all_repos:
        github_repo = r["github_repo"]
        if user_max_age and not sdk.has_recent_commits(r["path"], identities, user_max_age):
            continue

        runs = sdk.get_builds(github_repo, limit=limit, refresh=refresh)
        for run in runs:
            run["repo_name"] = github_repo
            actor = run.get("event", "unknown").lower()
            title = run.get("displayTitle", "").lower()
            if user and user.lower() not in actor and user.lower() not in title:
                continue
            all_runs.append(run)

    if not all_runs:
        click.echo("No builds matching criteria found.")
        return

    all_runs.sort(key=lambda x: x["createdAt"], reverse=True)
    all_runs = all_runs[:limit]

    header = "%-12s %-3s %-25s %-15s %-7s %-12s %s" % ("ID", "⚡", "REPO", "BRANCH", "PR", "CREATED", "TITLE")
    click.echo(header)
    click.echo("-" * 120)
    for r in all_runs:
        icon = get_status_icon(r["status"], r.get("conclusion"))
        
        gh_repo = r["repo_name"]
        if effective_owner != "all" and gh_repo.startswith(f"{effective_owner}/"):
            repo_display = gh_repo.replace(f"{effective_owner}/", "", 1)
        else:
            # Format as reponame (orgname)
            parts = gh_repo.split("/")
            if len(parts) == 2:
                org, repo_name = parts
                repo_display = f"{repo_name} ({org})"
            else:
                repo_display = gh_repo
            
        if len(repo_display) > 25:
            repo_display = repo_display[:22] + "..."
            
        branch = r.get("headBranch", "unknown")
        date = format_date(r["createdAt"])
        
        pr_display = ""
        prs = r.get("pullRequests", [])
        if prs:
            pr_display = f"#{prs[0]['number']}"
            
        click.echo("%-12s %-2s %-25s %-15s %-7s %-12s %s" % (
            str(r["databaseId"]), icon, repo_display, branch, pr_display, date, r["displayTitle"]
        ))

@main.group()
def prs():
    """Manage GitHub pull requests."""
    pass

@prs.command(name="list")
@ensure_initialized()
@click.option("--repo", default="*", help="GitHub simple name or pattern.")
@click.option("--owner", help="Filter by GitHub owner.")
@click.option("--state", default="open", help="PR state: open, closed, merged, all.")
@click.option("--limit", default=10, type=int, help="Number of PRs to show per repo.")
def list_prs_cmd(repo, owner, state, limit):
    """List pull requests for repositories."""
    cm = sdk.ConfigManager()
    pm = sdk.ProfileManager()
    check_profile_status(pm, cm)
    
    effective_owner = owner or cm.default_owner

    if effective_owner != "all":
        click.secho(f"Filtering by owner: {effective_owner}", fg="cyan")

    all_repos = sdk.find_local_repos(pattern=repo, owner=owner)
    
    if not all_repos:
        click.echo(f"No repositories matching '{repo}' found.")
        return

    all_prs = []
    for r in all_repos:
        github_repo = r["github_repo"]
        repo_prs = sdk.get_prs(github_repo, limit=limit, state=state)
        for pr in repo_prs:
            pr["repo_name"] = github_repo
            all_prs.append(pr)

    if not all_prs:
        click.echo("No pull requests matching criteria found.")
        return

    # Sort by creation date
    all_prs.sort(key=lambda x: x["createdAt"], reverse=True)

    header = "%-7s %-25s %-15s %-12s %s" % ("PR", "REPO", "AUTHOR", "CREATED", "TITLE")
    click.echo(header)
    click.echo("-" * 100)
    for pr in all_prs:
        gh_repo = pr["repo_name"]
        if effective_owner != "all" and gh_repo.startswith(f"{effective_owner}/"):
            repo_display = gh_repo.replace(f"{effective_owner}/", "", 1)
        else:
            parts = gh_repo.split("/")
            repo_display = parts[1] if len(parts) == 2 else gh_repo
            
        if len(repo_display) > 25:
            repo_display = repo_display[:22] + "..."
            
        author = pr.get("author", {}).get("login", "unknown")
        date = format_date(pr["createdAt"])
        click.echo("%-7s %-25s %-15s %-12s %s" % (
            f"#{pr['number']}", repo_display, author, date, pr["title"]
        ))

@prs.command(name="show")
@ensure_initialized()
@click.argument("number")
@click.option("--repo", help="GitHub simple name (if not auto-discoverable).")
def show_pr_cmd(number, repo):
    """Show details and browser URL for a specific pull request."""
    if number.startswith("#"):
        number = number[1:]
        
    target_repo = repo
    pr_data = None
    
    # Try to find repo in the cache
    cache_dir = sdk.get_config_dir() / "cache"
    if cache_dir.exists():
        for cache_file in cache_dir.glob("*_prs.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    for pr in data:
                        if str(pr['number']) == str(number):
                            pr_data = pr
                            if not target_repo:
                                target_repo = cache_file.name.replace('_prs.json', '').replace('_', '/')
                            break
                    if pr_data:
                        break
            except Exception:
                continue
    
    if not target_repo:
        click.secho("Could not auto-discover repo for this PR. Please provide --repo.", fg="yellow")
        return

    # Fetch fresh details
    details = sdk.get_pr_details(target_repo, number)
    if "error" in details:
        click.secho(f"Error fetching PR details: {details['error']}", fg="red")
        return

    click.secho(f"Pull Request #{details['number']}", bold=True)
    click.echo(f"Title:    {details['title']}")
    click.echo(f"Repo:     {target_repo}")
    click.echo(f"Author:   {details.get('author', {}).get('login', 'unknown')}")
    click.echo(f"Status:   {details['state']}")
    click.echo(f"Created:  {details['createdAt']}")
    click.echo(f"Branch:   {details['headRefName']} -> {details.get('baseRefName', 'unknown')}")
    
    click.echo("-" * 40)
    click.echo("Browser URL:")
    click.secho(f"  {details['url']}", fg="cyan")
    
    if details.get('body'):
        click.echo("-" * 40)
        body = details['body'].strip()
        if len(body) > 500:
            body = body[:497] + "..."
        click.echo(body)

    click.echo("-" * 40)
    click.echo("To open in browser:")
    click.secho(f"  gh pr view {number} --repo {target_repo} --web", fg="green")

@repos.command(name="clone")
@ensure_initialized()
@click.argument("name")
@click.option("--owner", help="GitHub owner (overrides default).")
@click.option("--dest", help="Destination directory (defaults to first search root).")
def clone_repo_cmd(name, owner, dest):
    """Clone a repository from GitHub."""
    cm = sdk.ConfigManager()
    owner = owner or cm.default_owner
    
    if not owner:
        click.secho("Error: No GitHub owner configured. Use 'gtdev init' or --owner.", fg="red")
        return

    github_repo = f"{owner}/{name}" if "/" not in name else name
    
    if not dest:
        dest_root = Path(cm.search_roots[0])
    else:
        dest_root = Path(dest).expanduser().resolve()
        
    dest_path = dest_root / name.split("/")[-1]
    
    click.echo(f"Cloning {github_repo} to {dest_path}...")
    success, msg = sdk.clone_repo(github_repo, dest_path)
    if success:
        click.secho(msg, fg="green")
        # Ensure the root is in search_roots
        if str(dest_root) not in [str(Path(r).expanduser().resolve()) for r in cm.search_roots]:
            click.echo(f"Note: {dest_root} is not in your search roots. Adding it...")
            cm.add_root(str(dest_root))
            cm.save()
    else:
        click.secho(msg, fg="red")

@builds.command(name="show")
@ensure_initialized()
@click.argument("id")
@click.option("--repo", help="GitHub simple name (if not auto-discoverable).")
def show_build_cmd(id, repo):
    """Show details and log command for a specific build."""
    target_repo = repo
    build_data = None
    
    # Try to find which repo and build data this ID belongs to in the cache
    cache_dir = sdk.get_config_dir() / "cache"
    if cache_dir.exists():
        for cache_file in cache_dir.glob("*_builds.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    for run in data:
                        if str(run['databaseId']) == str(id):
                            build_data = run
                            if not target_repo:
                                target_repo = cache_file.name.replace('_builds.json', '').replace('_', '/')
                            break
                    if build_data:
                        break
            except Exception:
                continue
    
    if not target_repo:
        click.secho("Could not auto-discover repo for this ID. Please provide --repo.", fg="yellow")
        return

    # If not in cache or repo provided manually, try a fresh fetch for details
    if not build_data:
        runs = sdk.get_builds(target_repo, refresh=True)
        for run in runs:
            if str(run['databaseId']) == str(id):
                build_data = run
                break

    click.echo(f"Build ID: {id}")
    click.echo(f"Repo:     {target_repo}")
    
    if build_data:
        icon = get_status_icon(build_data['status'], build_data.get('conclusion'))
        click.echo(f"Status:   {icon} {build_data['status']} ({build_data.get('conclusion') or 'pending'})")
        click.echo(f"Branch:   {build_data.get('headBranch', 'unknown')}")
        click.echo(f"Created:  {build_data['createdAt']}")
        click.echo(f"Event:    {build_data.get('event', 'unknown')}")
        click.echo(f"Workflow: {build_data.get('workflowName', 'unknown')}")
        click.echo(f"Title:    {build_data['displayTitle']}")
    
    click.echo("-" * 40)
    
    if build_data and build_data.get('event') == 'workflow_dispatch':
        click.echo("To trigger this workflow again:")
        branch = build_data.get('headBranch', 'main')
        wf = build_data.get('workflowName')
        click.secho(f"  gh workflow run \"{wf}\" --repo {target_repo} --ref {branch}", fg="yellow")
        click.echo("")

    click.echo("To view logs:")
    click.secho(f"  gtdev logs --repo={target_repo} --id={id}", fg="cyan")
    click.echo("\nTo download logs using gh directly:")
    click.secho(f"  gh run view {id} --repo {target_repo} --log > build_{id}.log", fg="green")

@main.command()
@ensure_initialized()
@click.option("--repo", required=True, help="GitHub simple name.")
@click.option("--id", required=True, help="Build/Run ID.")
def logs(repo, id):
    """Fetch logs for a specific build run."""
    if "*" in repo or "/" not in repo:
        matches = sdk.find_local_repos(pattern=repo)
        if not matches:
            click.echo(f"No repo matching {repo} found.")
            return
        repo = matches[0]["github_repo"]
    click.echo(sdk.get_build_logs(repo, id))

if __name__ == "__main__":
    main()
