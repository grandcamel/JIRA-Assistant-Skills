import click

from jira_assistant_skills.utils import SKILLS_ROOT_DIR, run_skill_script_subprocess


@click.group()
def ops():
    """Commands for cache management and operational utilities."""
    pass


@ops.command(name="cache-status")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed cache statistics")
@click.pass_context
def ops_cache_status(ctx, detailed: bool):
    """Show cache status and statistics."""
    script_path = SKILLS_ROOT_DIR / "jira-ops" / "scripts" / "cache_status.py"

    script_args = []
    if detailed:
        script_args.append("--detailed")

    run_skill_script_subprocess(script_path, script_args, ctx)


@ops.command(name="cache-clear")
@click.option("--type", "-t", "cache_type", help="Clear specific cache type")
@click.option("--older-than", help="Clear entries older than (e.g., 1d, 2h)")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def ops_cache_clear(ctx, cache_type: str, older_than: str, force: bool):
    """Clear cache entries."""
    script_path = SKILLS_ROOT_DIR / "jira-ops" / "scripts" / "cache_clear.py"

    script_args = []
    if cache_type:
        script_args.extend(["--type", cache_type])
    if older_than:
        script_args.extend(["--older-than", older_than])
    if force:
        script_args.append("--force")

    run_skill_script_subprocess(script_path, script_args, ctx)


@ops.command(name="cache-warm")
@click.argument("project_key")
@click.option("--type", "-t", "cache_type", help="Warm specific cache type")
@click.option("--max-issues", "-m", type=int, help="Maximum issues to cache")
@click.pass_context
def ops_cache_warm(ctx, project_key: str, cache_type: str, max_issues: int):
    """Pre-warm cache for a project."""
    script_path = SKILLS_ROOT_DIR / "jira-ops" / "scripts" / "cache_warm.py"

    script_args = [project_key]
    if cache_type:
        script_args.extend(["--type", cache_type])
    if max_issues:
        script_args.extend(["--max-issues", str(max_issues)])

    run_skill_script_subprocess(script_path, script_args, ctx)


@ops.command(name="discover-project")
@click.argument("project_key")
@click.option("--save", "-s", is_flag=True, help="Save discovered context to config")
@click.pass_context
def ops_discover_project(ctx, project_key: str, save: bool):
    """Discover project configuration and capabilities."""
    script_path = SKILLS_ROOT_DIR / "jira-ops" / "scripts" / "discover_project.py"

    script_args = [project_key]
    if save:
        script_args.append("--save")

    run_skill_script_subprocess(script_path, script_args, ctx)
