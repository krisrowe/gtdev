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

if __name__ == "__main__":
    main()
