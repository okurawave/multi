# Python

import click
from pathlib import Path
from orchestrator import Orchestrator

@click.group()
def cli():
    pass

@cli.command()
@click.option('--project-name', required=True, help='Name of the project directory.')
def new(project_name):
    """Starts a new AI-driven development project."""
    project_path = Path(project_name)
    project_path.mkdir(exist_ok=True)
    try:
        orchestrator = Orchestrator(project_path)
        orchestrator.run()
    except Exception as e:
        click.echo(f"An error occurred: {e}", err=True)

if __name__ == '__main__':
    cli()
