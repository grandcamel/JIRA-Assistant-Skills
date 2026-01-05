import click

from jira_assistant_skills.utils import SKILLS_ROOT_DIR, run_skill_script_subprocess


@click.group()
def fields():
    """Commands for managing JIRA custom fields."""
    pass


@fields.command(name="list")
@click.option("--filter", "-f", "filter_pattern", help="Filter fields by name pattern")
@click.option("--agile", "-a", is_flag=True, help="Show only Agile-related fields")
@click.option(
    "--all", "show_all", is_flag=True, help="Show all fields (not just custom)"
)
@click.pass_context
def fields_list(ctx, filter_pattern: str, agile: bool, show_all: bool):
    """List all available fields."""
    script_path = SKILLS_ROOT_DIR / "jira-fields" / "scripts" / "list_fields.py"

    script_args = []
    if filter_pattern:
        script_args.extend(["--filter", filter_pattern])
    if agile:
        script_args.append("--agile")
    if show_all:
        script_args.append("--all")

    run_skill_script_subprocess(script_path, script_args, ctx)


@fields.command(name="create")
@click.option("--name", "-n", required=True, help="Field name")
@click.option(
    "--type",
    "-t",
    "field_type",
    required=True,
    help="Field type (text, number, select, etc.)",
)
@click.option("--description", "-d", help="Field description")
@click.pass_context
def fields_create(ctx, name: str, field_type: str, description: str):
    """Create a new custom field."""
    script_path = SKILLS_ROOT_DIR / "jira-fields" / "scripts" / "create_field.py"

    script_args = ["--name", name, "--type", field_type]
    if description:
        script_args.extend(["--description", description])

    run_skill_script_subprocess(script_path, script_args, ctx)


@fields.command(name="check-project")
@click.argument("project_key")
@click.option("--type", "-t", "issue_type", help="Specific issue type to check")
@click.option(
    "--check-agile", "-a", is_flag=True, help="Check Agile field availability"
)
@click.pass_context
def fields_check_project(ctx, project_key: str, issue_type: str, check_agile: bool):
    """Check which fields are available for a project."""
    script_path = (
        SKILLS_ROOT_DIR / "jira-fields" / "scripts" / "check_project_fields.py"
    )

    script_args = [project_key]
    if issue_type:
        script_args.extend(["--type", issue_type])
    if check_agile:
        script_args.append("--check-agile")

    run_skill_script_subprocess(script_path, script_args, ctx)


@fields.command(name="configure-agile")
@click.argument("project_key")
@click.option("--epic-link", help="Epic Link field ID")
@click.option("--story-points", help="Story Points field ID")
@click.option("--sprint", help="Sprint field ID")
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.pass_context
def fields_configure_agile(
    ctx,
    project_key: str,
    epic_link: str,
    story_points: str,
    sprint: str,
    dry_run: bool,
):
    """Configure Agile field mappings for a project."""
    script_path = (
        SKILLS_ROOT_DIR / "jira-fields" / "scripts" / "configure_agile_fields.py"
    )

    script_args = [project_key]
    if epic_link:
        script_args.extend(["--epic-link", epic_link])
    if story_points:
        script_args.extend(["--story-points", story_points])
    if sprint:
        script_args.extend(["--sprint", sprint])
    if dry_run:
        script_args.append("--dry-run")

    run_skill_script_subprocess(script_path, script_args, ctx)
