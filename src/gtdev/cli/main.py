import click
from gtdev import sdk

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
        click.echo('%-25s %-30s %s' % (r['name'], r['github_repo'], r['path']))

@main.group()
def builds():
    """Query GitHub Action builds."""
    pass

@builds.command(name='list')
@click.option('--repo', required=True, help='GitHub simple name or pattern.')
@click.option('--limit', default=5, help='Number of builds to show.')
def list_builds_cmd(repo, limit):
    """List recent builds for a repository."""
    if '*' in repo or '/' not in repo:
        profile = sdk.get_user_profile()
        matches = sdk.find_local_repos(profile, pattern=repo)
        if not matches:
            click.echo(f'No repo matching {repo} found.')
            return
        repo = matches[0]['github_repo']
    runs = sdk.get_builds(repo, limit=limit)
    if not runs:
        click.echo('No builds found.')
        return
    header = '%-15s %-12s %-12s %-25s %s' % ('ID', 'STATUS', 'CONCLUSION', 'CREATED', 'TITLE')
    click.echo(header)
    click.echo('-' * 100)
    for r in runs:
        conc = r.get('conclusion') or 'pending'
        click.echo('%-15s %-12s %-12s %-25s %s' % (str(r['databaseId']), r['status'], conc, r['createdAt'], r['displayTitle']))

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
