import click

from jira_assistant_skills.utils import SKILLS_ROOT_DIR, run_skill_script_subprocess


@click.group()
def lifecycle():
    """Commands for issue workflow and lifecycle management."""
    pass


@lifecycle.command(name="transition")
@click.argument("issue_key")
@click.option(
    "--to",
    "-t",
    "status",
    required=True,
    help='Target status name (e.g., "Done", "In Progress")',
)
@click.option("--comment", "-c", help="Add a comment with the transition")
@click.option("--resolution", "-r", help="Resolution (for Done transitions)")
@click.pass_context
def lifecycle_transition(
    ctx, issue_key: str, status: str, comment: str, resolution: str
):
    """Transition an issue to a new status.

    Examples:
        jira lifecycle transition PROJ-123 --to "In Progress"
        jira lifecycle transition PROJ-123 --to Done --resolution Fixed
    """
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "transition_issue.py"

    script_args = [issue_key, status]
    if comment:
        script_args.extend(["--comment", comment])
    if resolution:
        script_args.extend(["--resolution", resolution])

    run_skill_script_subprocess(script_path, script_args, ctx)


@lifecycle.command(name="transitions")
@click.argument("issue_key")
@click.pass_context
def lifecycle_get_transitions(ctx, issue_key: str):
    """Get available transitions for an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "get_transitions.py"
    run_skill_script_subprocess(script_path, [issue_key], ctx)


@lifecycle.command(name="assign")
@click.argument("issue_key")
@click.option(
    "--user", "-u", help="User to assign (account ID, email, or display name)"
)
@click.option("--self", "-s", "assign_self", is_flag=True, help="Assign to yourself")
@click.option("--unassign", is_flag=True, help="Remove assignee")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without making changes")
@click.pass_context
def lifecycle_assign(
    ctx, issue_key: str, user: str, assign_self: bool, unassign: bool, dry_run: bool
):
    """Assign an issue to a user.

    Use exactly one of: --user, --self, or --unassign.

    Examples:
        jira lifecycle assign PROJ-123 --self
        jira lifecycle assign PROJ-123 --user john@example.com
        jira lifecycle assign PROJ-123 --unassign
    """
    if sum([bool(user), assign_self, unassign]) != 1:
        raise click.UsageError("Specify exactly one of: --user, --self, or --unassign")

    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "assign_issue.py"

    script_args = [issue_key]
    if user:
        script_args.extend(["--user", user])
    if assign_self:
        script_args.append("--self")
    if unassign:
        script_args.append("--unassign")
    if dry_run:
        script_args.append("--dry-run")

    run_skill_script_subprocess(script_path, script_args, ctx)


@lifecycle.command(name="resolve")
@click.argument("issue_key")
@click.option("--resolution", "-r", default="Done", help="Resolution type")
@click.option("--comment", "-c", help="Resolution comment")
@click.pass_context
def lifecycle_resolve(ctx, issue_key: str, resolution: str, comment: str):
    """Resolve an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "resolve_issue.py"

    script_args = [issue_key, "--resolution", resolution]
    if comment:
        script_args.extend(["--comment", comment])

    run_skill_script_subprocess(script_path, script_args, ctx)


@lifecycle.command(name="reopen")
@click.argument("issue_key")
@click.option("--comment", "-c", help="Reopen comment")
@click.pass_context
def lifecycle_reopen(ctx, issue_key: str, comment: str):
    """Reopen a resolved issue."""
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "reopen_issue.py"

    script_args = [issue_key]
    if comment:
        script_args.extend(["--comment", comment])

    run_skill_script_subprocess(script_path, script_args, ctx)


# Version management subgroup
@lifecycle.group()
def version():
    """Manage project versions/releases."""
    pass


@version.command(name="list")
@click.argument("project_key")
@click.option("--unreleased", "-u", is_flag=True, help="Show only unreleased versions")
@click.option("--archived", "-a", is_flag=True, help="Include archived versions")
@click.pass_context
def version_list(ctx, project_key: str, unreleased: bool, archived: bool):
    """List project versions."""
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "get_versions.py"

    script_args = [project_key]
    if unreleased:
        script_args.append("--unreleased")
    if archived:
        script_args.append("--archived")

    run_skill_script_subprocess(script_path, script_args, ctx)


@version.command(name="create")
@click.argument("project_key")
@click.argument("name")
@click.option("--description", "-d", help="Version description")
@click.option("--start-date", help="Start date (YYYY-MM-DD)")
@click.option("--release-date", help="Release date (YYYY-MM-DD)")
@click.pass_context
def version_create(
    ctx,
    project_key: str,
    name: str,
    description: str,
    start_date: str,
    release_date: str,
):
    """Create a new version."""
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "create_version.py"

    script_args = [project_key, name]
    if description:
        script_args.extend(["--description", description])
    if start_date:
        script_args.extend(["--start-date", start_date])
    if release_date:
        script_args.extend(["--release-date", release_date])

    run_skill_script_subprocess(script_path, script_args, ctx)


@version.command(name="release")
@click.argument("project_key")
@click.argument("version_name")
@click.option("--move-unfixed", help="Move unfixed issues to this version")
@click.pass_context
def version_release(ctx, project_key: str, version_name: str, move_unfixed: str):
    """Release a version."""
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "release_version.py"

    script_args = [project_key, version_name]
    if move_unfixed:
        script_args.extend(["--move-unfixed", move_unfixed])

    run_skill_script_subprocess(script_path, script_args, ctx)


@version.command(name="archive")
@click.argument("project_key")
@click.argument("version_name")
@click.pass_context
def version_archive(ctx, project_key: str, version_name: str):
    """Archive a version."""
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "archive_version.py"
    run_skill_script_subprocess(script_path, [project_key, version_name], ctx)


# Component management subgroup
@lifecycle.group()
def component():
    """Manage project components."""
    pass


@component.command(name="list")
@click.argument("project_key")
@click.pass_context
def component_list(ctx, project_key: str):
    """List project components."""
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "get_components.py"
    run_skill_script_subprocess(script_path, [project_key], ctx)


@component.command(name="create")
@click.argument("project_key")
@click.argument("name")
@click.option("--description", "-d", help="Component description")
@click.option("--lead", "-l", help="Component lead (account ID or email)")
@click.pass_context
def component_create(ctx, project_key: str, name: str, description: str, lead: str):
    """Create a new component."""
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "create_component.py"

    script_args = [project_key, name]
    if description:
        script_args.extend(["--description", description])
    if lead:
        script_args.extend(["--lead", lead])

    run_skill_script_subprocess(script_path, script_args, ctx)


@component.command(name="update")
@click.argument("project_key")
@click.argument("component_name")
@click.option("--name", "-n", "new_name", help="New component name")
@click.option("--description", "-d", help="New description")
@click.option("--lead", "-l", help="New component lead")
@click.pass_context
def component_update(
    ctx,
    project_key: str,
    component_name: str,
    new_name: str,
    description: str,
    lead: str,
):
    """Update a component."""
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "update_component.py"

    script_args = [project_key, component_name]
    if new_name:
        script_args.extend(["--name", new_name])
    if description:
        script_args.extend(["--description", description])
    if lead:
        script_args.extend(["--lead", lead])

    run_skill_script_subprocess(script_path, script_args, ctx)


@component.command(name="delete")
@click.argument("project_key")
@click.argument("component_name")
@click.option("--move-to", help="Move issues to this component")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def component_delete(
    ctx, project_key: str, component_name: str, move_to: str, force: bool
):
    """Delete a component."""
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "delete_component.py"

    script_args = [project_key, component_name]
    if move_to:
        script_args.extend(["--move-to", move_to])
    if force:
        script_args.append("--force")

    run_skill_script_subprocess(script_path, script_args, ctx)
