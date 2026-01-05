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
    help='Target status name (e.g., "Done", "In Progress")',
)
@click.option("--id", "transition_id", help="Transition ID (alternative to --to)")
@click.option("--comment", "-c", help="Add a comment with the transition")
@click.option("--resolution", "-r", help="Resolution (for Done transitions)")
@click.option(
    "--sprint", "-s", type=int, help="Sprint ID to move issue to after transition"
)
@click.option("--fields", help="Additional fields as JSON string")
@click.option(
    "--dry-run", "-n", is_flag=True, help="Preview changes without making them"
)
@click.pass_context
def lifecycle_transition(
    ctx,
    issue_key: str,
    status: str,
    transition_id: str,
    comment: str,
    resolution: str,
    sprint: int,
    fields: str,
    dry_run: bool,
):
    """Transition an issue to a new status.

    Use either --to (status name) or --id (transition ID).

    Examples:
        jira lifecycle transition PROJ-123 --to "In Progress"
        jira lifecycle transition PROJ-123 --to Done --resolution Fixed
        jira lifecycle transition PROJ-123 --id 31
        jira lifecycle transition PROJ-123 --to "In Progress" --dry-run
        jira lifecycle transition PROJ-123 --to "In Progress" --sprint 42
    """
    if not status and not transition_id:
        raise click.UsageError(
            "Specify either --to (status name) or --id (transition ID)"
        )
    if status and transition_id:
        raise click.UsageError("Specify only one of --to or --id, not both")

    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "transition_issue.py"

    script_args = [issue_key]
    if status:
        script_args.extend(["--name", status])
    if transition_id:
        script_args.extend(["--id", transition_id])
    if comment:
        script_args.extend(["--comment", comment])
    if resolution:
        script_args.extend(["--resolution", resolution])
    if sprint:
        script_args.extend(["--sprint", str(sprint)])
    if fields:
        script_args.extend(["--fields", fields])
    if dry_run:
        script_args.append("--dry-run")

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
@click.option("--name", "-n", required=True, help="Version name (e.g., v1.0.0)")
@click.option("--description", "-d", help="Version description")
@click.option("--start-date", help="Start date (YYYY-MM-DD)")
@click.option("--release-date", help="Release date (YYYY-MM-DD)")
@click.option("--released", is_flag=True, help="Mark version as released")
@click.option("--archived", is_flag=True, help="Mark version as archived")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be created without creating"
)
@click.pass_context
def version_create(
    ctx,
    project_key: str,
    name: str,
    description: str,
    start_date: str,
    release_date: str,
    released: bool,
    archived: bool,
    dry_run: bool,
):
    """Create a new version.

    Examples:
        jira lifecycle version create PROJ --name "v1.0.0"
        jira lifecycle version create PROJ --name "v1.0.0" --start-date 2025-01-01
        jira lifecycle version create PROJ --name "v1.0.0" --released --dry-run
    """
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "create_version.py"

    script_args = [project_key, "--name", name]
    if description:
        script_args.extend(["--description", description])
    if start_date:
        script_args.extend(["--start-date", start_date])
    if release_date:
        script_args.extend(["--release-date", release_date])
    if released:
        script_args.append("--released")
    if archived:
        script_args.append("--archived")
    if dry_run:
        script_args.append("--dry-run")

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
@click.option("--name", "-n", required=True, help="Component name")
@click.option("--description", "-d", help="Component description")
@click.option("--lead", "-l", help="Component lead account ID")
@click.option(
    "--assignee-type",
    "-a",
    type=click.Choice(
        ["COMPONENT_LEAD", "PROJECT_LEAD", "PROJECT_DEFAULT", "UNASSIGNED"]
    ),
    help="Default assignee type for issues in this component",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be created without creating"
)
@click.pass_context
def component_create(
    ctx,
    project_key: str,
    name: str,
    description: str,
    lead: str,
    assignee_type: str,
    dry_run: bool,
):
    """Create a new component.

    Examples:
        jira lifecycle component create PROJ --name "API"
        jira lifecycle component create PROJ --name "Backend" --lead 5b10a2844c20165700ede21g
        jira lifecycle component create PROJ --name "Frontend" --assignee-type COMPONENT_LEAD
    """
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "create_component.py"

    script_args = [project_key, "--name", name]
    if description:
        script_args.extend(["--description", description])
    if lead:
        script_args.extend(["--lead", lead])
    if assignee_type:
        script_args.extend(["--assignee-type", assignee_type])
    if dry_run:
        script_args.append("--dry-run")

    run_skill_script_subprocess(script_path, script_args, ctx)


@component.command(name="update")
@click.option("--id", "component_id", required=True, help="Component ID to update")
@click.option("--name", "-n", help="New component name")
@click.option("--description", "-d", help="New description")
@click.option("--lead", "-l", help="New component lead account ID")
@click.option(
    "--assignee-type",
    "-a",
    type=click.Choice(
        ["COMPONENT_LEAD", "PROJECT_LEAD", "PROJECT_DEFAULT", "UNASSIGNED"]
    ),
    help="New default assignee type",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be updated without updating"
)
@click.pass_context
def component_update(
    ctx,
    component_id: str,
    name: str,
    description: str,
    lead: str,
    assignee_type: str,
    dry_run: bool,
):
    """Update a component.

    Requires component ID (use 'jira lifecycle component list PROJ' to find IDs).

    Examples:
        jira lifecycle component update --id 10000 --name "New Name"
        jira lifecycle component update --id 10000 --lead 5b10a2844c20165700ede22h
        jira lifecycle component update --id 10000 --assignee-type PROJECT_LEAD --dry-run
    """
    if not any([name, description, lead, assignee_type]):
        raise click.UsageError(
            "Must specify at least one field to update (--name, --description, --lead, --assignee-type)"
        )

    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "update_component.py"

    script_args = ["--id", component_id]
    if name:
        script_args.extend(["--name", name])
    if description:
        script_args.extend(["--description", description])
    if lead:
        script_args.extend(["--lead", lead])
    if assignee_type:
        script_args.extend(["--assignee-type", assignee_type])
    if dry_run:
        script_args.append("--dry-run")

    run_skill_script_subprocess(script_path, script_args, ctx)


@component.command(name="delete")
@click.option("--id", "component_id", required=True, help="Component ID to delete")
@click.option("--move-to", help="Component ID to move issues to before deletion")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be deleted without deleting"
)
@click.pass_context
def component_delete(
    ctx,
    component_id: str,
    move_to: str,
    yes: bool,
    dry_run: bool,
):
    """Delete a component.

    Requires component ID (use 'jira lifecycle component list PROJ' to find IDs).

    Examples:
        jira lifecycle component delete --id 10000
        jira lifecycle component delete --id 10000 --yes
        jira lifecycle component delete --id 10000 --move-to 10001
        jira lifecycle component delete --id 10000 --dry-run
    """
    script_path = SKILLS_ROOT_DIR / "jira-lifecycle" / "scripts" / "delete_component.py"

    script_args = ["--id", component_id]
    if move_to:
        script_args.extend(["--move-to", move_to])
    if yes:
        script_args.append("--yes")
    if dry_run:
        script_args.append("--dry-run")

    run_skill_script_subprocess(script_path, script_args, ctx)
