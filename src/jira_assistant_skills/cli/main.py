import os

import click


# --- Global Options Design ---
@click.group(invoke_without_command=True)
@click.version_option(version="1.0.0")  # Use importlib.metadata for robustness later
@click.option(
    "--profile",
    "-p",
    type=str,
    envvar="JIRA_PROFILE",
    help="JIRA profile to use from ~/.claude/settings.json",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json", "table"]),
    default="text",
    help="Output format (default: text)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-essential output")
@click.pass_context
def cli(ctx, profile: str, output: str, verbose: bool, quiet: bool):
    """Jira Assistant Skills CLI.

    Use --help on any command for more information.
    """
    ctx.ensure_object(dict)
    ctx.obj["PROFILE"] = profile
    ctx.obj["OUTPUT"] = output
    ctx.obj["VERBOSE"] = verbose
    ctx.obj["QUIET"] = quiet

    # Set environment variables for subprocess calls to inherit global options
    env_prefix = "JIRA"  # This will be dynamic for other services
    if profile:
        os.environ[f"{env_prefix}_PROFILE"] = profile
    if output:
        os.environ[f"{env_prefix}_OUTPUT"] = output
    if verbose:
        os.environ[f"{env_prefix}_VERBOSE"] = "true"
    if quiet:
        os.environ[f"{env_prefix}_QUIET"] = "true"

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# --- Explicitly import command groups ---
from .commands.admin_cmds import admin
from .commands.agile_cmds import agile
from .commands.bulk_cmds import bulk
from .commands.collaborate_cmds import collaborate
from .commands.dev_cmds import dev
from .commands.fields_cmds import fields
from .commands.issue_cmds import issue
from .commands.jsm_cmds import jsm
from .commands.lifecycle_cmds import lifecycle
from .commands.ops_cmds import ops
from .commands.relationships_cmds import relationships
from .commands.search_cmds import search
from .commands.time_cmds import time

cli.add_command(issue)
cli.add_command(search)
cli.add_command(lifecycle)
cli.add_command(fields)
cli.add_command(ops)
cli.add_command(bulk)
cli.add_command(dev)
cli.add_command(relationships)
cli.add_command(time)
cli.add_command(collaborate)
cli.add_command(agile)
cli.add_command(jsm)
cli.add_command(admin)
