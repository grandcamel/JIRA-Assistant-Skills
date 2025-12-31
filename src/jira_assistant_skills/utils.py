import click
from click.exceptions import Exit
import subprocess
import sys
import os
import importlib.resources
from pathlib import Path

# --- Robust SKILLS_ROOT_DIR Resolution ---
# This path is relative to the *project root* where pyproject.toml and 'plugins' reside.
# It assumes the package is installed in editable mode from the project root
# or that 'plugins' is copied alongside the installed package.
try:
    # This attempts to get the root of the 'jira_assistant_skills' package
    # then navigates up to the project root, then down to plugins/jira-assistant-skills/skills
    with importlib.resources.path('jira_assistant_skills', '__init__.py') as p:
        # p is like /path/to/site-packages/jira_assistant_skills/__init__.py or /path/to/project/src/jira_assistant_skills/__init__.py
        # p.parent is /path/to/site-packages/jira_assistant_skills or /path/to/project/src/jira_assistant_skills
        # p.parent.parent is /path/to/site-packages or /path/to/project/src
        # p.parent.parent.parent is /path/to or /path/to/project (project root)
        project_root = p.parent.parent.parent if p.parent.parent.name == 'src' else p.parent.parent # Adjust based on src layout
        SKILLS_ROOT_DIR = (project_root / 'plugins' / 'jira-assistant-skills' / 'skills').resolve()
except (ImportError, ModuleNotFoundError, FileNotFoundError):
    # Fallback for direct execution or unusual development setups
    # This assumes utils.py is in src/jira_assistant_skills/
    # Path(__file__).resolve().parents[0] is src/jira_assistant_skills/
    # Path(__file__).resolve().parents[1] is src/
    # Path(__file__).resolve().parents[2] is project root
    project_root = Path(__file__).resolve().parents[2]
    SKILLS_ROOT_DIR = (project_root / 'plugins' / 'jira-assistant-skills' / 'skills').resolve()


# Helper for subprocess calls (centralized error handling)
def run_skill_script_subprocess(script_path: Path, args: list[str], ctx: click.Context):
    """
    Executes a skill script via subprocess.

    Args:
        script_path: Path to the skill script.
        args: List of arguments to pass to the script's main(argv) function.
        ctx: Click context for propagating global options and exit.
    """
    if not script_path.exists():
        click.echo(f"Error: Script not found: {script_path}", err=True)
        ctx.exit(2) # Standard exit code for script not found

    command = [sys.executable, str(script_path)] + args
    try:
        # Propagate global options via environment variables
        env = os.environ.copy()
        env_prefix = "JIRA" # This will be dynamic for other services
        if ctx.obj.get('PROFILE'): env[f'{env_prefix}_PROFILE'] = ctx.obj['PROFILE']
        if ctx.obj.get('OUTPUT'): env[f'{env_prefix}_OUTPUT'] = ctx.obj['OUTPUT']
        if ctx.obj.get('VERBOSE'): env[f'{env_prefix}_VERBOSE'] = 'true'
        if ctx.obj.get('QUIET'): env[f'{env_prefix}_QUIET'] = 'true'

        if ctx.obj.get('VERBOSE'):
            click.echo(f"Running: {' '.join(command)}", err=True)
        result = subprocess.run(
            command,
            check=False, # We handle return code
            stdout=None, # Inherit stdout/stderr
            stderr=None,
            env=env
        )
        ctx.exit(result.returncode)
    except Exit:
        # Re-raise Click's Exit exception (raised by ctx.exit)
        raise
    except Exception as e:
        click.echo(f"Error executing script {script_path.name}: {e}", err=True)
        ctx.exit(1) # General error

