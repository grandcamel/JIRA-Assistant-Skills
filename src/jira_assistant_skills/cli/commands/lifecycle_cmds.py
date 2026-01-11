"""
Lifecycle commands for jira-as CLI.

Commands for issue workflow and lifecycle management:
- transition: Transition issues to new status
- transitions: List available transitions
- assign: Assign/unassign issues
- resolve: Resolve issues
- reopen: Reopen resolved issues
- version: Version/release management subgroup
- component: Component management subgroup
"""

import json
from datetime import datetime
from typing import Any

import click

from jira_assistant_skills_lib import (
    ValidationError,
    find_transition_by_keywords,
    find_transition_by_name,
    format_json,
    format_table,
    format_transitions,
    get_jira_client,
    get_project_context,
    get_valid_transitions,
    has_project_context,
    print_info,
    print_success,
    text_to_adf,
    validate_issue_key,
    validate_transition_id,
)

from ..cli_utils import handle_jira_errors, parse_json_arg

# =============================================================================
# Transition Implementation Functions
# =============================================================================


def _get_context_workflow_hint(
    project_key: str,
    issue_type: str,
    current_status: str,
) -> str:
    """
    Get workflow hint from project context if available.

    Args:
        project_key: Project key
        issue_type: Issue type name
        current_status: Current status name

    Returns:
        String with expected transitions from context, or empty string if no context
    """
    if not has_project_context(project_key):
        return ""

    context = get_project_context(project_key)
    if not context.has_context():
        return ""

    valid_transitions = get_valid_transitions(context, issue_type, current_status)
    if not valid_transitions:
        return ""

    lines = ["\nExpected transitions from project context:"]
    for t in valid_transitions:
        lines.append(f"  - {t.get('name')} → {t.get('to_status')}")

    return "\n".join(lines)


def _transition_issue_impl(
    issue_key: str,
    transition_id: str | None = None,
    transition_name: str | None = None,
    resolution: str | None = None,
    comment: str | None = None,
    fields: dict | None = None,
    sprint_id: int | None = None,
    dry_run: bool = False,
) -> dict:
    """
    Transition an issue to a new status.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        transition_id: Transition ID
        transition_name: Transition name (alternative to ID)
        resolution: Resolution to set (for Done transitions)
        comment: Comment to add
        fields: Additional fields to set
        sprint_id: Sprint ID to move issue to after transition
        dry_run: If True, preview changes without making them

    Returns:
        Dictionary with transition details
    """
    issue_key = validate_issue_key(issue_key)

    if not transition_id and not transition_name:
        raise ValidationError("Either --id or --to must be specified")

    client = get_jira_client()
    try:
        # Get issue details first for context hints
        issue = client.get_issue(issue_key, fields=["status", "issuetype", "project"])
        current_status = (
            issue.get("fields", {}).get("status", {}).get("name", "Unknown")
        )
        issue_type = issue.get("fields", {}).get("issuetype", {}).get("name", "Unknown")
        project_key = (
            issue.get("fields", {})
            .get("project", {})
            .get("key", issue_key.split("-")[0])
        )

        transitions = client.get_transitions(issue_key)

        if not transitions:
            context_hint = _get_context_workflow_hint(
                project_key, issue_type, current_status
            )
            raise ValidationError(
                f"No transitions available for {issue_key} (status: {current_status}){context_hint}"
            )

        if transition_name:
            transition = find_transition_by_name(transitions, transition_name)
            transition_id = transition["id"]
        else:
            transition_id = validate_transition_id(transition_id)
            matching = [t for t in transitions if t["id"] == transition_id]
            if not matching:
                available = format_transitions(transitions)
                context_hint = _get_context_workflow_hint(
                    project_key, issue_type, current_status
                )
                raise ValidationError(
                    f"Transition ID '{transition_id}' not available.\n\n{available}{context_hint}"
                )
            transition = matching[0]

        transition_fields = fields or {}

        if resolution:
            transition_fields["resolution"] = {"name": resolution}

        if comment:
            transition_fields["comment"] = text_to_adf(comment)

        target_status = transition.get("to", {}).get(
            "name", transition.get("name", "Unknown")
        )

        result = {
            "issue_key": issue_key,
            "transition": transition.get("name"),
            "transition_id": transition_id,
            "current_status": current_status,
            "target_status": target_status,
            "resolution": resolution,
            "comment": comment is not None,
            "sprint_id": sprint_id,
            "dry_run": dry_run,
        }

        if dry_run:
            print_info(f"[DRY RUN] Would transition {issue_key}:")
            click.echo(f"  Current status: {current_status}")
            click.echo(f"  Target status: {target_status}")
            click.echo(f"  Transition: {transition.get('name')}")
            if resolution:
                click.echo(f"  Resolution: {resolution}")
            if comment:
                click.echo("  Comment: (would add comment)")
            if sprint_id:
                click.echo(f"  Sprint: Would move to sprint {sprint_id}")

            context_hint = _get_context_workflow_hint(
                project_key, issue_type, target_status
            )
            if context_hint:
                click.echo(
                    f"\n  After transition, expected options:{context_hint.replace(chr(10), chr(10) + '  ')}"
                )

            return result

        client.transition_issue(
            issue_key,
            transition_id,
            fields=transition_fields if transition_fields else None,
        )

        if sprint_id:
            client.move_issues_to_sprint(sprint_id, [issue_key])

        return result
    finally:
        client.close()


def _get_transitions_impl(issue_key: str) -> list:
    """
    Get available transitions for an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)

    Returns:
        List of available transitions
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        return client.get_transitions(issue_key)
    finally:
        client.close()


def _assign_issue_impl(
    issue_key: str,
    user: str | None = None,
    assign_to_self: bool = False,
    unassign: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    Assign or reassign an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        user: User account ID or email
        assign_to_self: Assign to current user
        unassign: Remove assignee
        dry_run: If True, preview changes without making them

    Returns:
        Dictionary with assignment details
    """
    issue_key = validate_issue_key(issue_key)

    if sum([bool(user), assign_to_self, unassign]) != 1:
        raise ValidationError("Specify exactly one of: --user, --self, or --unassign")

    client = get_jira_client()
    try:
        if unassign:
            account_id = None
            action = "unassign"
            target_display = "Unassigned"
        elif assign_to_self:
            account_id = "-1"
            action = "assign to self"
            target_display = "yourself"
        else:
            account_id = user
            action = f"assign to {user}"
            target_display = user

        # Get current assignee for dry-run display
        issue = client.get_issue(issue_key, fields=["assignee"])
        current_assignee = issue.get("fields", {}).get("assignee")
        current_display = (
            current_assignee.get("displayName", "Unknown")
            if current_assignee
            else "Unassigned"
        )

        result = {
            "issue_key": issue_key,
            "action": action,
            "current_assignee": current_display,
            "target_assignee": target_display,
            "dry_run": dry_run,
        }

        if dry_run:
            print_info(f"[DRY RUN] Would {action} for {issue_key}:")
            click.echo(f"  Current assignee: {current_display}")
            click.echo(f"  New assignee: {target_display}")
            return result

        client.assign_issue(issue_key, account_id)
        return result
    finally:
        client.close()


# Keywords for resolve/reopen transitions
RESOLVE_KEYWORDS = ["done", "resolve", "close", "complete"]
REOPEN_KEYWORDS = ["reopen", "to do", "todo", "open", "backlog"]


def _resolve_issue_impl(
    issue_key: str,
    resolution: str = "Fixed",
    comment: str | None = None,
) -> None:
    """
    Resolve an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        resolution: Resolution value (Fixed, Won't Fix, Duplicate, etc.)
        comment: Optional comment
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        transitions = client.get_transitions(issue_key)

        if not transitions:
            raise ValidationError(f"No transitions available for {issue_key}")

        transition = find_transition_by_keywords(
            transitions, RESOLVE_KEYWORDS, prefer_exact="done"
        )

        if not transition:
            available = format_transitions(transitions)
            raise ValidationError(
                f"No resolution transition found for {issue_key}.\n"
                f"Available transitions:\n{available}"
            )

        fields = {"resolution": {"name": resolution}}

        if comment:
            fields["comment"] = text_to_adf(comment)

        client.transition_issue(issue_key, transition["id"], fields=fields)
    finally:
        client.close()


def _reopen_issue_impl(issue_key: str, comment: str | None = None) -> None:
    """
    Reopen a closed or resolved issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        comment: Optional comment explaining why issue was reopened
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        transitions = client.get_transitions(issue_key)

        if not transitions:
            raise ValidationError(f"No transitions available for {issue_key}")

        transition = find_transition_by_keywords(
            transitions, REOPEN_KEYWORDS, prefer_exact="reopen"
        )

        # If no exact 'reopen', try 'to do' as secondary preference
        if transition and "reopen" not in transition["name"].lower():
            todo_trans = find_transition_by_keywords(
                transitions, ["to do", "todo"], prefer_exact="to do"
            )
            if todo_trans:
                transition = todo_trans

        if not transition:
            available = format_transitions(transitions)
            raise ValidationError(
                f"No reopen transition found for {issue_key}.\n"
                f"Available transitions:\n{available}"
            )

        fields = None
        if comment:
            fields = {"comment": text_to_adf(comment)}

        client.transition_issue(issue_key, transition["id"], fields=fields)
    finally:
        client.close()


# =============================================================================
# Version Implementation Functions
# =============================================================================


def _get_versions_impl(
    project: str,
    released: bool | None = None,
    unreleased: bool | None = None,
    archived: bool | None = None,
) -> list[dict[str, Any]]:
    """
    Get all versions for a project with optional filtering.

    Args:
        project: Project key (e.g., PROJ)
        released: Filter for released versions only
        unreleased: Filter for unreleased versions only
        archived: Filter for archived versions only

    Returns:
        List of version data
    """
    client = get_jira_client()
    try:
        versions = client.get_versions(project)

        # Apply filters
        if released:
            versions = [v for v in versions if v.get("released")]
        elif unreleased:
            versions = [v for v in versions if not v.get("released")]

        if archived:
            versions = [v for v in versions if v.get("archived")]

        return versions
    finally:
        client.close()


def _create_version_impl(
    project: str,
    name: str,
    description: str | None = None,
    start_date: str | None = None,
    release_date: str | None = None,
    released: bool = False,
    archived: bool = False,
    dry_run: bool = False,
) -> dict[str, Any] | None:
    """
    Create a project version.

    Args:
        project: Project key (e.g., PROJ)
        name: Version name (e.g., v1.0.0)
        description: Optional description
        start_date: Optional start date (YYYY-MM-DD)
        release_date: Optional release date (YYYY-MM-DD)
        released: Mark as released
        archived: Mark as archived
        dry_run: If True, preview without creating

    Returns:
        Created version data, or None for dry-run
    """
    if dry_run:
        print_info(f"[DRY RUN] Would create version in project {project}:")
        click.echo(f"  Name: {name}")
        if description:
            click.echo(f"  Description: {description}")
        if start_date:
            click.echo(f"  Start Date: {start_date}")
        if release_date:
            click.echo(f"  Release Date: {release_date}")
        click.echo(f"  Released: {released}")
        click.echo(f"  Archived: {archived}")
        click.echo("\nNo version created (dry-run mode).")
        return None

    client = get_jira_client()
    try:
        return client.create_version(
            project=project,
            name=name,
            description=description,
            start_date=start_date,
            release_date=release_date,
            released=released,
            archived=archived,
        )
    finally:
        client.close()


def _release_version_impl(
    project_key: str,
    version_name: str,
    move_unfixed: str | None = None,
) -> dict[str, Any]:
    """
    Release a version by name.

    Args:
        project_key: Project key
        version_name: Version name
        move_unfixed: Version name to move unfixed issues to

    Returns:
        Updated version data
    """
    client = get_jira_client()
    try:
        versions = client.get_versions(project_key)

        # Find version by name
        version_id = None
        for v in versions:
            if v["name"] == version_name:
                version_id = v["id"]
                break

        if not version_id:
            raise ValidationError(
                f"Version '{version_name}' not found in project {project_key}"
            )

        release_date = datetime.now().strftime("%Y-%m-%d")
        result = client.update_version(
            version_id, released=True, releaseDate=release_date
        )

        # Handle move_unfixed if specified
        if move_unfixed:
            # Find target version
            target_id = None
            for v in versions:
                if v["name"] == move_unfixed:
                    target_id = v["id"]
                    break
            if target_id:
                # Move unfixed issues would require additional API calls
                pass

        return result
    finally:
        client.close()


def _archive_version_impl(
    project_key: str,
    version_name: str,
) -> dict[str, Any]:
    """
    Archive a version by name.

    Args:
        project_key: Project key
        version_name: Version name

    Returns:
        Updated version data
    """
    client = get_jira_client()
    try:
        versions = client.get_versions(project_key)

        # Find version by name
        version_id = None
        for v in versions:
            if v["name"] == version_name:
                version_id = v["id"]
                break

        if not version_id:
            raise ValidationError(
                f"Version '{version_name}' not found in project {project_key}"
            )

        return client.update_version(version_id, archived=True)
    finally:
        client.close()


# =============================================================================
# Component Implementation Functions
# =============================================================================


def _get_components_impl(project: str) -> list[dict[str, Any]]:
    """
    Get all components for a project.

    Args:
        project: Project key (e.g., PROJ)

    Returns:
        List of component data
    """
    client = get_jira_client()
    try:
        return client.get_components(project)
    finally:
        client.close()


def _create_component_impl(
    project: str,
    name: str,
    description: str | None = None,
    lead_account_id: str | None = None,
    assignee_type: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any] | None:
    """
    Create a project component.

    Args:
        project: Project key (e.g., PROJ)
        name: Component name
        description: Optional description
        lead_account_id: Optional component lead account ID
        assignee_type: Optional default assignee type
        dry_run: If True, preview without creating

    Returns:
        Created component data, or None for dry-run
    """
    if dry_run:
        print_info(f"[DRY RUN] Would create component in project {project}:")
        click.echo(f"  Name: {name}")
        if description:
            click.echo(f"  Description: {description}")
        if lead_account_id:
            click.echo(f"  Lead Account ID: {lead_account_id}")
        if assignee_type:
            click.echo(f"  Assignee Type: {assignee_type}")
        click.echo("\nNo component created (dry-run mode).")
        return None

    client = get_jira_client()
    try:
        return client.create_component(
            project=project,
            name=name,
            description=description,
            lead_account_id=lead_account_id,
            assignee_type=assignee_type,
        )
    finally:
        client.close()


def _update_component_impl(
    component_id: str,
    name: str | None = None,
    description: str | None = None,
    lead_account_id: str | None = None,
    assignee_type: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any] | None:
    """
    Update a component.

    Args:
        component_id: Component ID
        name: Optional new name
        description: Optional new description
        lead_account_id: Optional new lead account ID
        assignee_type: Optional new assignee type
        dry_run: If True, preview without updating

    Returns:
        Updated component data, or None for dry-run
    """
    if not any([name, description, lead_account_id, assignee_type]):
        raise ValidationError(
            "Must specify at least one field to update (--name, --description, --lead, --assignee-type)"
        )

    if dry_run:
        print_info(f"[DRY RUN] Would update component {component_id}:")
        if name:
            click.echo(f"  Name: {name}")
        if description:
            click.echo(f"  Description: {description}")
        if lead_account_id:
            click.echo(f"  Lead Account ID: {lead_account_id}")
        if assignee_type:
            click.echo(f"  Assignee Type: {assignee_type}")
        click.echo("\nNo component updated (dry-run mode).")
        return None

    update_data = {}
    if name:
        update_data["name"] = name
    if description:
        update_data["description"] = description
    if lead_account_id:
        update_data["leadAccountId"] = lead_account_id
    if assignee_type:
        update_data["assigneeType"] = assignee_type

    client = get_jira_client()
    try:
        return client.update_component(component_id, **update_data)
    finally:
        client.close()


def _delete_component_impl(
    component_id: str,
    move_to: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any] | None:
    """
    Delete a component.

    Args:
        component_id: Component ID to delete
        move_to: Optional component ID to move issues to
        force: Skip confirmation
        dry_run: If True, preview without deleting

    Returns:
        Component info if not force (for confirmation), None otherwise
    """
    client = get_jira_client()
    try:
        if dry_run:
            component = client.get_component(component_id)
            print_info(f"[DRY RUN] Would delete component {component_id}:")
            click.echo(f"  Name: {component['name']}")
            if component.get("description"):
                click.echo(f"  Description: {component['description']}")
            if move_to:
                click.echo(f"  Move issues to: {move_to}")
            click.echo("\nNo component deleted (dry-run mode).")
            return None

        if not force:
            component = client.get_component(component_id)
            return {
                "id": component_id,
                "name": component.get("name", "Unknown"),
                "description": component.get("description", ""),
                "move_to": move_to,
            }

        kwargs = {}
        if move_to:
            kwargs["moveIssuesTo"] = move_to

        client.delete_component(component_id, **kwargs)
        return None
    finally:
        client.close()


# =============================================================================
# CLI Commands
# =============================================================================


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
@handle_jira_errors
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
        jira-as lifecycle transition PROJ-123 --to "In Progress"
        jira-as lifecycle transition PROJ-123 --to Done --resolution Fixed
        jira-as lifecycle transition PROJ-123 --id 31
        jira-as lifecycle transition PROJ-123 --to "In Progress" --dry-run
        jira-as lifecycle transition PROJ-123 --to "In Progress" --sprint 42
    """
    if not status and not transition_id:
        raise click.UsageError(
            "Specify either --to (status name) or --id (transition ID)"
        )
    if status and transition_id:
        raise click.UsageError("Specify only one of --to or --id, not both")

    fields_dict = parse_json_arg(fields)

    _transition_issue_impl(
        issue_key=issue_key,
        transition_id=transition_id,
        transition_name=status,
        resolution=resolution,
        comment=comment,
        fields=fields_dict,
        sprint_id=sprint,
        dry_run=dry_run,
    )

    if not dry_run:
        target = status or f"transition {transition_id}"
        msg = f"Transitioned {issue_key} to {target}"
        if sprint:
            msg += f" and moved to sprint {sprint}"
        print_success(msg)


@lifecycle.command(name="transitions")
@click.argument("issue_key")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def lifecycle_get_transitions(ctx, issue_key: str, output: str):
    """Get available transitions for an issue."""
    transitions = _get_transitions_impl(issue_key)

    if not transitions:
        click.echo(f"No transitions available for {issue_key}")
        return

    if output == "json":
        click.echo(format_json(transitions))
    else:
        click.echo(f"\nAvailable transitions for {issue_key}:\n")
        click.echo(format_transitions(transitions))


@lifecycle.command(name="assign")
@click.argument("issue_key")
@click.option(
    "--user", "-u", help="User to assign (account ID, email, or display name)"
)
@click.option("--self", "-s", "assign_self", is_flag=True, help="Assign to yourself")
@click.option("--unassign", is_flag=True, help="Remove assignee")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without making changes")
@click.pass_context
@handle_jira_errors
def lifecycle_assign(
    ctx, issue_key: str, user: str, assign_self: bool, unassign: bool, dry_run: bool
):
    """Assign an issue to a user.

    Use exactly one of: --user, --self, or --unassign.

    Examples:
        jira-as lifecycle assign PROJ-123 --self
        jira-as lifecycle assign PROJ-123 --user john@example.com
        jira-as lifecycle assign PROJ-123 --unassign
    """
    if sum([bool(user), assign_self, unassign]) != 1:
        raise click.UsageError("Specify exactly one of: --user, --self, or --unassign")

    _assign_issue_impl(
        issue_key=issue_key,
        user=user,
        assign_to_self=assign_self,
        unassign=unassign,
        dry_run=dry_run,
    )

    if not dry_run:
        if unassign:
            print_success(f"Unassigned {issue_key}")
        elif assign_self:
            print_success(f"Assigned {issue_key} to you")
        else:
            print_success(f"Assigned {issue_key} to {user}")


@lifecycle.command(name="resolve")
@click.argument("issue_key")
@click.option("--resolution", "-r", default="Done", help="Resolution type")
@click.option("--comment", "-c", help="Resolution comment")
@click.pass_context
@handle_jira_errors
def lifecycle_resolve(ctx, issue_key: str, resolution: str, comment: str):
    """Resolve an issue."""
    _resolve_issue_impl(issue_key=issue_key, resolution=resolution, comment=comment)
    print_success(f"Resolved {issue_key} as {resolution}")


@lifecycle.command(name="reopen")
@click.argument("issue_key")
@click.option("--comment", "-c", help="Reopen comment")
@click.pass_context
@handle_jira_errors
def lifecycle_reopen(ctx, issue_key: str, comment: str):
    """Reopen a resolved issue."""
    _reopen_issue_impl(issue_key=issue_key, comment=comment)
    print_success(f"Reopened {issue_key}")


# =============================================================================
# Version Subgroup
# =============================================================================


@lifecycle.group()
def version():
    """Manage project versions/releases."""
    pass


@version.command(name="list")
@click.argument("project_key")
@click.option("--unreleased", "-u", is_flag=True, help="Show only unreleased versions")
@click.option("--archived", "-a", is_flag=True, help="Include archived versions")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def version_list(ctx, project_key: str, unreleased: bool, archived: bool, output: str):
    """List project versions."""
    versions = _get_versions_impl(
        project=project_key,
        unreleased=unreleased,
        archived=archived,
    )

    if output == "json":
        click.echo(json.dumps(versions, indent=2))
    else:
        click.echo(f"Versions for project {project_key}:\n")

        if not versions:
            click.echo("No versions found.")
            return

        table_data = []
        for v in versions:
            table_data.append(
                {
                    "id": v.get("id", ""),
                    "name": v.get("name", ""),
                    "description": (v.get("description", "") or "")[:40],
                    "released": "Yes" if v.get("released") else "No",
                    "archived": "Yes" if v.get("archived") else "No",
                    "release_date": v.get("releaseDate", ""),
                }
            )

        click.echo(
            format_table(
                table_data,
                columns=[
                    "id",
                    "name",
                    "description",
                    "released",
                    "archived",
                    "release_date",
                ],
                headers=[
                    "ID",
                    "Name",
                    "Description",
                    "Released",
                    "Archived",
                    "Release Date",
                ],
            )
        )
        click.echo(f"\nTotal: {len(versions)} version(s)")


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
@handle_jira_errors
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
        jira-as lifecycle version create PROJ --name "v1.0.0"
        jira-as lifecycle version create PROJ --name "v1.0.0" --start-date 2025-01-01
        jira-as lifecycle version create PROJ --name "v1.0.0" --released --dry-run
    """
    result = _create_version_impl(
        project=project_key,
        name=name,
        description=description,
        start_date=start_date,
        release_date=release_date,
        released=released,
        archived=archived,
        dry_run=dry_run,
    )

    if result:
        version_id = result.get("id", "")
        print_success(
            f"Created version '{name}' in project {project_key} (ID: {version_id})"
        )


@version.command(name="release")
@click.argument("project_key")
@click.argument("version_name")
@click.option("--move-unfixed", help="Move unfixed issues to this version")
@click.pass_context
@handle_jira_errors
def version_release(ctx, project_key: str, version_name: str, move_unfixed: str):
    """Release a version."""
    result = _release_version_impl(
        project_key=project_key,
        version_name=version_name,
        move_unfixed=move_unfixed,
    )

    print_success(f"Released version '{result['name']}' (ID: {result['id']})")
    click.echo(f"\nRelease Date: {result.get('releaseDate', 'N/A')}")


@version.command(name="archive")
@click.argument("project_key")
@click.argument("version_name")
@click.pass_context
@handle_jira_errors
def version_archive(ctx, project_key: str, version_name: str):
    """Archive a version."""
    result = _archive_version_impl(project_key=project_key, version_name=version_name)
    print_success(f"Archived version '{result['name']}' (ID: {result['id']})")


# =============================================================================
# Component Subgroup
# =============================================================================


@lifecycle.group()
def component():
    """Manage project components."""
    pass


@component.command(name="list")
@click.argument("project_key")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def component_list(ctx, project_key: str, output: str):
    """List project components."""
    components = _get_components_impl(project_key)

    if output == "json":
        click.echo(json.dumps(components, indent=2))
    else:
        click.echo(f"Components for project {project_key}:\n")

        if not components:
            click.echo("No components found.")
            return

        table_data = []
        for c in components:
            lead = c.get("lead", {})
            table_data.append(
                {
                    "id": c.get("id", ""),
                    "name": c.get("name", ""),
                    "description": (c.get("description", "") or "")[:40],
                    "lead": lead.get("displayName", "") if lead else "",
                }
            )

        click.echo(
            format_table(
                table_data,
                columns=["id", "name", "description", "lead"],
                headers=["ID", "Name", "Description", "Lead"],
            )
        )
        click.echo(f"\nTotal: {len(components)} component(s)")


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
@handle_jira_errors
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
        jira-as lifecycle component create PROJ --name "API"
        jira-as lifecycle component create PROJ --name "Backend" --lead 5b10a2844c20165700ede21g
        jira-as lifecycle component create PROJ --name "Frontend" --assignee-type COMPONENT_LEAD
    """
    result = _create_component_impl(
        project=project_key,
        name=name,
        description=description,
        lead_account_id=lead,
        assignee_type=assignee_type,
        dry_run=dry_run,
    )

    if result:
        component_id = result.get("id", "")
        print_success(
            f"Created component '{name}' in project {project_key} (ID: {component_id})"
        )


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
@handle_jira_errors
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

    Requires component ID (use 'jira-as lifecycle component list PROJ' to find IDs).

    Examples:
        jira-as lifecycle component update --id 10000 --name "New Name"
        jira-as lifecycle component update --id 10000 --lead 5b10a2844c20165700ede22h
        jira-as lifecycle component update --id 10000 --assignee-type PROJECT_LEAD --dry-run
    """
    result = _update_component_impl(
        component_id=component_id,
        name=name,
        description=description,
        lead_account_id=lead,
        assignee_type=assignee_type,
        dry_run=dry_run,
    )

    if result:
        component_name = result.get("name", component_id)
        print_success(f"Updated component '{component_name}' (ID: {result['id']})")


@component.command(name="delete")
@click.option("--id", "component_id", required=True, help="Component ID to delete")
@click.option("--move-to", help="Component ID to move issues to before deletion")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be deleted without deleting"
)
@click.pass_context
@handle_jira_errors
def component_delete(
    ctx,
    component_id: str,
    move_to: str,
    yes: bool,
    dry_run: bool,
):
    """Delete a component.

    Requires component ID (use 'jira-as lifecycle component list PROJ' to find IDs).

    Examples:
        jira-as lifecycle component delete --id 10000
        jira-as lifecycle component delete --id 10000 --yes
        jira-as lifecycle component delete --id 10000 --move-to 10001
        jira-as lifecycle component delete --id 10000 --dry-run
    """
    result = _delete_component_impl(
        component_id=component_id,
        move_to=move_to,
        force=yes,
        dry_run=dry_run,
    )

    if result:
        # Need confirmation
        click.echo(f"\nDelete component {component_id}?")
        click.echo(f"  Name: {result['name']}")
        if result.get("description"):
            click.echo(f"  Description: {result['description']}")
        if move_to:
            click.echo(f"  Move issues to component: {move_to}")
        click.echo()

        if click.confirm("Are you sure?"):
            # Actually delete
            client = get_jira_client()
            try:
                kwargs = {}
                if move_to:
                    kwargs["moveIssuesTo"] = move_to
                client.delete_component(component_id, **kwargs)
            finally:
                client.close()
            print_success(f"Deleted component {component_id}")
        else:
            click.echo("Deletion cancelled.")
    elif not dry_run:
        print_success(f"Deleted component {component_id}")
