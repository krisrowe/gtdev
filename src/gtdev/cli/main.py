import click
import os
import json
from datetime import datetime
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

@click.group()
def main():
    """gtdev CLI."""
    pass

@main.command()
def init():
    """Initialize the gtdev workspace."""
    click.echo(sdk.init_workspace())

@main.group()
def repos():
    """Manage local and GitHub repositories."""
    pass

@repos.command(name='list')
@click.option('--pattern', default='*', help='Filter by name or GitHub simple name.')
def list_repos_cmd(pattern):
    """List local repositories and their GitHub mappings."""
    profile = sdk.get_user_profile()
    repos = sdk.find_local_repos(profile, pattern=pattern)
    if not repos:
        click.echo('No repositories found.')
        return
    header = '%-25s %-30s %s' % ('NAME', 'GITHUB REPO', 'LOCAL PATH')
    click.echo(header)
    click.echo('-' * 100)
    for r in repos:
        path = format_path(r['path'])
        click.echo('%-25s %-30s %s' % (r['name'], r['github_repo'], path))

@main.group()
def builds():
    """Query GitHub Action builds."""
    pass

@builds.command(name='list')
@click.option('--repo', default='*', help='GitHub simple name or pattern.')
@click.option('--user', help='Contains match on email, name, or triggering actor.')
@click.option('--user-max-age', type=int, help='Max age in hours for commits from current user.')
@click.option('--limit', default=10, type=int, help='Number of builds to show.')
@click.option('--refresh', is_flag=True, help='Skip cache and fetch fresh data.')
def list_builds_cmd(repo, user, user_max_age, limit, refresh):
    """List recent builds for repositories."""
    profile = sdk.get_user_profile()
    all_repos = sdk.find_local_repos(profile, pattern=repo)
    
    if not all_repos:
        click.echo(f"No repositories matching '{repo}' found.")
        return

    identities = sdk.get_current_identities() if user_max_age else []
    all_runs = []
    
    for r in all_repos:
        github_repo = r['github_repo']
        if user_max_age and not sdk.has_recent_commits(r['path'], identities, user_max_age):
            continue

        runs = sdk.get_builds(github_repo, limit=limit, refresh=refresh)
        for run in runs:
            run['repo_name'] = github_repo
            actor = run.get('event', 'unknown').lower()
            title = run.get('displayTitle', '').lower()
            if user and user.lower() not in actor and user.lower() not in title:
                continue
            all_runs.append(run)

    if not all_runs:
        click.echo("No builds matching criteria found.")
        return

    all_runs.sort(key=lambda x: x['createdAt'], reverse=True)
    all_runs = all_runs[:limit]

    header = '%-12s %-4s %-20s %-15s %-12s %s' % ('ID', '⚡', 'REPO', 'BRANCH', 'CREATED', 'TITLE')
    click.echo(header)
    click.echo('-' * 100)
    for r in all_runs:
        icon = get_status_icon(r['status'], r.get('conclusion'))
        repo_display = (r['repo_name'][:17] + '...') if len(r['repo_name']) > 20 else r['repo_name']
        branch = r.get('headBranch', 'unknown')
        date = format_date(r['createdAt'])
        click.echo('%-12s %-2s %-20s %-15s %-12s %s' % (
            str(r['databaseId']), icon, repo_display, branch, date, r['displayTitle']
        ))

@builds.command(name='show')
@click.argument('id')
@click.option('--repo', help='GitHub simple name (if not auto-discoverable).')
def show_build_cmd(id, repo):
    """Show details and log command for a specific build."""
    target_repo = repo
    if not target_repo:
        # Try to find which repo this ID belongs to in the cache
        cache_dir = sdk.get_config_dir() / "cache"
        if cache_dir.exists():
            for cache_file in cache_dir.glob("*_builds.json"):
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        if any(str(run['databaseId']) == str(id) for run in data):
                            target_repo = cache_file.name.replace('_builds.json', '').replace('_', '/')
                            break
                except Exception:
                    continue
    
    if not target_repo:
        click.secho("Could not auto-discover repo for this ID. Please provide --repo.", fg="yellow")
        return

    click.echo(f"Build ID: {id}")
    click.echo(f"Repo:     {target_repo}")
    click.echo("-" * 40)
    click.echo("To view logs:")
    click.secho(f"  gtdev logs --repo={target_repo} --id={id}", fg="cyan")
    click.echo("\nTo download logs using gh directly:")
    click.secho(f"  gh run view {id} --repo {target_repo} --log > build_{id}.log", fg="green")

@main.command()
@click.option('--repo', required=True, help='GitHub simple name.')
@click.option('--id', required=True, help='Build/Run ID.')
def logs(repo, id):
    """Fetch logs for a specific build run."""
    if '*' in repo or '/' not in repo:
        profile = sdk.get_user_profile()
        matches = sdk.find_local_repos(profile, pattern=repo)
        if not matches:
            click.echo(f'No repo matching {repo} found.')
            return
        repo = matches[0]['github_repo']
    click.echo(sdk.get_build_logs(repo, id))

if __name__ == '__main__':
    main()
