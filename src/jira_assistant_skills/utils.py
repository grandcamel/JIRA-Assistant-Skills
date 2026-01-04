import click
from click.exceptions import Exit
import subprocess
import sys
import os
import importlib.resources
from pathlib import Path

# --- Robust SKILLS_ROOT_DIR Resolution ---
# Skills can be located in two places:
# 1. Bundled in package: site-packages/jira_assistant_skills/skills/ (pip install from PyPI)
# 2. Project structure: project_root/plugins/jira-assistant-skills/skills/ (editable install)
def _resolve_skills_root() -> Path:
    """Resolve the skills root directory, checking bundled location first."""
    try:
        with importlib.resources.path('jira_assistant_skills', '__init__.py') as p:
            package_dir = p.parent

            # Option 1: Skills bundled in package (pip install from PyPI)
            bundled_skills = package_dir / 'skills'
            if bundled_skills.exists() and bundled_skills.is_dir():
                return bundled_skills.resolve()

            # Option 2: Editable install - navigate to project root
            # p.parent is jira_assistant_skills/
            # p.parent.parent is src/ or site-packages/
            # p.parent.parent.parent is project root (if src/ layout)
            if p.parent.parent.name == 'src':
                project_root = p.parent.parent.parent
            else:
                project_root = p.parent.parent

            project_skills = project_root / 'plugins' / 'jira-assistant-skills' / 'skills'
            if project_skills.exists():
                return project_skills.resolve()

            # Fallback: return bundled path even if it doesn't exist yet
            return bundled_skills.resolve()

    except (ImportError, ModuleNotFoundError, FileNotFoundError):
        # Fallback for direct execution or unusual development setups
        project_root = Path(__file__).resolve().parents[2]
        return (project_root / 'plugins' / 'jira-assistant-skills' / 'skills').resolve()

SKILLS_ROOT_DIR = _resolve_skills_root()


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

