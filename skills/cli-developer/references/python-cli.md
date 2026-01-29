# Python CLI Development

## Typer (Recommended - Modern)

FastAPI-style CLI framework with automatic help generation.

```python
#!/usr/bin/env python3
import typer
from typing import Optional
from enum import Enum

app = typer.Typer()

class Environment(str, Enum):
    dev = "development"
    staging = "staging"
    prod = "production"

@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    template: str = typer.Option("default", help="Project template"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing"),
):
    """Initialize a new project"""
    typer.echo(f"Creating {name} from {template}")
    if force:
        typer.echo("Force mode enabled")

@app.command()
def deploy(
    environment: Environment = typer.Argument(..., help="Target environment"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only"),
    config: Optional[typer.FileText] = typer.Option(None, help="Config file"),
):
    """Deploy to environment"""
    if dry_run:
        typer.echo(f"Would deploy to: {environment.value}")
    else:
        typer.echo(f"Deploying to {environment.value}...")

# Nested commands
config_app = typer.Typer()
app.add_typer(config_app, name="config", help="Manage configuration")

@config_app.command("get")
def config_get(key: str):
    """Get config value"""
    typer.echo(f"Value: {get_config(key)}")

@config_app.command("set")
def config_set(key: str, value: str):
    """Set config value"""
    set_config(key, value)
    typer.echo(f"Set {key} = {value}")

if __name__ == "__main__":
    app()
```

## Click (Widely Used)

Powerful, composable CLI framework.

```python
import click

@click.group()
@click.version_option()
def cli():
    """My awesome CLI tool"""
    pass

@cli.command()
@click.argument('name')
@click.option('--template', default='default', help='Project template')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing')
def init(name, template, force):
    """Initialize a new project"""
    click.echo(f"Creating {name} from {template}")

@cli.command()
@click.argument('environment', type=click.Choice(['dev', 'staging', 'prod']))
@click.option('--dry-run', is_flag=True, help='Preview only')
@click.option('--config', type=click.File('r'), help='Config file')
def deploy(environment, dry_run, config):
    """Deploy to environment"""
    if dry_run:
        click.secho(f"Would deploy to: {environment}", fg='yellow')
    else:
        click.secho(f"Deploying to {environment}...", fg='green')

# Nested groups
@cli.group()
def config():
    """Manage configuration"""
    pass

@config.command('get')
@click.argument('key')
def config_get(key):
    """Get config value"""
    click.echo(get_config(key))

@config.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """Set config value"""
    set_config(key, value)

if __name__ == '__main__':
    cli()
```

## Rich Terminal Output

Beautiful terminal formatting and progress indicators.

```python
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint

console = Console()

# Styled output
console.print("[bold blue]Info:[/] Starting deployment...")
console.print("[bold green]Success:[/] Deployment complete!")
console.print("[bold yellow]Warning:[/] Deprecated flag used")
console.print("[bold red]Error:[/] Deployment failed")

# Tables
table = Table(title="Deployments")
table.add_column("Environment", style="cyan")
table.add_column("Status", style="magenta")
table.add_column("Time", style="green")

table.add_row("Production", "✓ Success", "2m 34s")
table.add_row("Staging", "✗ Failed", "1m 12s")
console.print(table)

# Panels
console.print(Panel.fit(
    "Deploy to production?",
    title="Confirmation",
    border_style="red"
))

# Syntax highlighting
code = '''
def deploy(env: str):
    print(f"Deploying to {env}")
'''
console.print(Syntax(code, "python", theme="monokai"))

# Progress bars
with Progress() as progress:
    task = progress.add_task("[cyan]Deploying...", total=100)
    for i in range(100):
        do_work()
        progress.update(task, advance=1)

# Spinners
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
) as progress:
    task = progress.add_task("Installing dependencies...")
    install_dependencies()
```

## Interactive Prompts (questionary)

```python
import questionary

# Text input
name = questionary.text(
    "Project name:",
    default="my-project",
    validate=lambda x: len(x) > 0 or "Name required"
).ask()

# Select from list
environment = questionary.select(
    "Select environment:",
    choices=["development", "staging", "production"],
    default="development"
).ask()

# Checkbox (multi-select)
features = questionary.checkbox(
    "Select features:",
    choices=[
        questionary.Choice("TypeScript", checked=True),
        questionary.Choice("ESLint", checked=True),
        questionary.Choice("Prettier", checked=True),
        questionary.Choice("Jest", checked=False),
    ]
).ask()

# Confirmation
confirmed = questionary.confirm(
    "Deploy to production?",
    default=False
).ask()

if confirmed:
    deploy()

# Password
password = questionary.password("Enter password:").ask()
```

## Argparse (Standard Library)

Built-in argument parsing (verbose but no dependencies).

```python
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        prog='mycli',
        description='My awesome CLI tool',
    )
    parser.add_argument('--version', action='version', version='1.0.0')

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize project')
    init_parser.add_argument('name', help='Project name')
    init_parser.add_argument('--template', default='default', help='Template')
    init_parser.add_argument('-f', '--force', action='store_true')

    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy')
    deploy_parser.add_argument(
        'environment',
        choices=['dev', 'staging', 'prod'],
        help='Target environment'
    )
    deploy_parser.add_argument('--dry-run', action='store_true')
    deploy_parser.add_argument('--config', type=argparse.FileType('r'))

    args = parser.parse_args()

    if args.command == 'init':
        init(args.name, args.template, args.force)
    elif args.command == 'deploy':
        deploy(args.environment, args.dry_run, args.config)

if __name__ == '__main__':
    main()
```

## Error Handling

```python
import typer
import sys
from pathlib import Path

app = typer.Typer()

@app.command()
def deploy():
    try:
        perform_deploy()
    except PermissionError as e:
        typer.secho("Permission denied", fg=typer.colors.RED, err=True)
        typer.echo("Try running with sudo or check file permissions")
        raise typer.Exit(code=77)
    except FileNotFoundError as e:
        typer.secho(f"File not found: {e.filename}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=127)
    except Exception as e:
        typer.secho(f"Deployment failed: {e}", fg=typer.colors.RED, err=True)
        if os.getenv('DEBUG'):
            import traceback
            traceback.print_exc()
        raise typer.Exit(code=1)

# Handle KeyboardInterrupt (Ctrl+C)
def main():
    try:
        app()
    except KeyboardInterrupt:
        typer.echo("\nOperation cancelled")
        sys.exit(130)

if __name__ == "__main__":
    main()
```

## Configuration Management

```python
from pathlib import Path
from typing import Any
import json
import os

class Config:
    def __init__(self):
        self.config_paths = [
            Path("/etc/mycli/config.json"),          # System
            Path.home() / ".config" / "mycli" / "config.json",  # User
            Path.cwd() / "mycli.json",               # Project
        ]

    def load(self) -> dict[str, Any]:
        config = self._defaults()

        # Load from files (lowest to highest priority)
        for path in self.config_paths:
            if path.exists():
                with path.open() as f:
                    config.update(json.load(f))

        # Override with environment variables
        for key in config.keys():
            env_var = f"MYCLI_{key.upper()}"
            if env_var in os.environ:
                config[key] = os.environ[env_var]

        return config

    def _defaults(self) -> dict[str, Any]:
        return {
            "environment": "development",
            "verbose": False,
            "timeout": 30,
        }
```

## Setup.py / pyproject.toml

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "mycli"
version = "1.0.0"
description = "My awesome CLI tool"
requires-python = ">=3.10"
dependencies = [
    "typer[all]>=0.9.0",
    "rich>=13.0.0",
    "questionary>=2.0.0",
]

[project.scripts]
mycli = "mycli.cli:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]
```

## Testing CLIs

```python
from typer.testing import CliRunner
from mycli.cli import app

runner = CliRunner()

def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "1.0.0" in result.stdout

def test_init():
    result = runner.invoke(app, ["init", "my-project"])
    assert result.exit_code == 0
    assert "Creating my-project" in result.stdout

def test_init_with_template():
    result = runner.invoke(app, ["init", "my-project", "--template", "react"])
    assert result.exit_code == 0
    assert "react" in result.stdout

def test_invalid_command():
    result = runner.invoke(app, ["invalid"])
    assert result.exit_code != 0
```

## Progress Bars (tqdm)

```python
from tqdm import tqdm
import time

# Simple progress bar
for i in tqdm(range(100), desc="Processing"):
    process_item(i)

# Custom format
with tqdm(total=100, desc="Downloading", unit="MB") as pbar:
    for chunk in download_chunks():
        pbar.update(len(chunk))

# Multiple progress bars
from tqdm import trange

for epoch in trange(10, desc="Epochs"):
    for batch in trange(100, desc="Batches", leave=False):
        train_batch(batch)
```
