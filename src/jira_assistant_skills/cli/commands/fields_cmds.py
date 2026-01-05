import click

from jira_assistant_skills.utils import SKILLS_ROOT_DIR, run_skill_script_subprocess


@click.group()
def fields():
    """Commands for managing JIRA custom fields."""
    pass


@fields.command(name="list")
@click.option(
    "--type", "-t", "field_type", help="Filter by field type (custom, system)"
)
@click.option("--search", "-s", help="Search fields by name")
@click.pass_context
def fields_list(ctx, field_type: str, search: str):
    """List all available fields."""
    script_path = SKILLS_ROOT_DIR / "jira-fields" / "scripts" / "list_fields.py"

    script_args = []
    if field_type:
        script_args.extend(["--type", field_type])
    if search:
        script_args.extend(["--search", search])

    run_skill_script_subprocess(script_path, script_args, ctx)


@fields.command(name="create")
@click.argument("name")
@click.option(
    "--type",
    "-t",
    "field_type",
    required=True,
    help="Field type (text, number, select, etc.)",
)
@click.option("--description", "-d", help="Field description")
@click.option("--searchable", is_flag=True, help="Make field searchable")
@click.pass_context
def fields_create(ctx, name: str, field_type: str, description: str, searchable: bool):
    """Create a new custom field."""
    script_path = SKILLS_ROOT_DIR / "jira-fields" / "scripts" / "create_field.py"

    script_args = [name, "--type", field_type]
    if description:
        script_args.extend(["--description", description])
    if searchable:
        script_args.append("--searchable")

    run_skill_script_subprocess(script_path, script_args, ctx)


@fields.command(name="check-project")
@click.argument("project_key")
@click.option("--field", "-f", help="Check specific field availability")
@click.pass_context
def fields_check_project(ctx, project_key: str, field: str):
    """Check which fields are available for a project."""
    script_path = (
        SKILLS_ROOT_DIR / "jira-fields" / "scripts" / "check_project_fields.py"
    )

    script_args = [project_key]
    if field:
        script_args.extend(["--field", field])

    run_skill_script_subprocess(script_path, script_args, ctx)


@fields.command(name="configure-agile")
@click.argument("project_key")
@click.option("--epic-link", help="Epic Link field ID")
@click.option("--story-points", help="Story Points field ID")
@click.option("--epic-name", help="Epic Name field ID")
@click.option("--sprint", help="Sprint field ID")
@click.pass_context
def fields_configure_agile(
    ctx,
    project_key: str,
    epic_link: str,
    story_points: str,
    epic_name: str,
    sprint: str,
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
    if epic_name:
        script_args.extend(["--epic-name", epic_name])
    if sprint:
        script_args.extend(["--sprint", sprint])

    run_skill_script_subprocess(script_path, script_args, ctx)
