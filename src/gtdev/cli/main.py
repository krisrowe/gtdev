import click
import os
from gtdev import sdk

def format_path(path):
    """Converts absolute path to tilde-relative if under home."""
    home = os.path.expanduser('~')
    if path.startswith(home):
        return path.replace(home, '~', 1)
    return path

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

    # Discovery identities for user-max-age filtering
    identities = []
    if user_max_age:
        identities = sdk.get_current_identities()

    all_runs = []
    for r in all_repos:
        github_repo = r['github_repo']
        
        # Filter repos by user commit age if requested
        if user_max_age:
            if not sdk.has_recent_commits(r['path'], identities, user_max_age):
                continue

        runs = sdk.get_builds(github_repo, limit=limit, refresh=refresh)
        for run in runs:
            run['repo_name'] = github_repo
            
            # Filter runs by user if requested
            if user:
                actor = run.get('triggering_actor', {}).get('login', '').lower()
                title = run.get('displayTitle', '').lower()
                if user.lower() not in actor and user.lower() not in title:
                    continue
            
            all_runs.append(run)

    if not all_runs:
        click.echo("No builds matching criteria found.")
        return

    # Sort all runs by createdAt descending
    all_runs.sort(key=lambda x: x['createdAt'], reverse=True)
    all_runs = all_runs[:limit]

    header = '%-15s %-12s %-12s %-15s %-20s %-15s %s' % ('ID', 'STATUS', 'CONCLUSION', 'BRANCH', 'CREATED', 'EVENT', 'TITLE')
    click.echo(header)
    click.echo('-' * 120)
    for r in all_runs:
        conc = r.get('conclusion') or 'pending'
        actor = r.get('event', 'unknown')
        branch = r.get('headBranch', 'unknown')
        click.echo('%-15s %-12s %-12s %-15s %-20s %-15s %s' % (
            str(r['databaseId']), r['status'], conc, branch, r['createdAt'], actor, r['displayTitle']
        ))

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
