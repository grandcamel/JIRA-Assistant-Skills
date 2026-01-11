"""
CLI commands for JIRA issue operations.

Provides commands for creating, reading, updating, and deleting JIRA issues.
"""

import json
from importlib import resources
from pathlib import Path

import click

from jira_assistant_skills.cli.cli_utils import parse_comma_list, parse_json_arg
from jira_assistant_skills_lib import (
    JiraError,
    NotFoundError,
    PermissionError,
    format_issue,
    format_json,
    get_agile_fields,
    get_jira_client,
    get_project_defaults,
    has_project_context,
    markdown_to_adf,
    print_error,
    print_success,
    text_to_adf,
    validate_issue_key,
    validate_project_key,
)

# =============================================================================
# Implementation Functions
# =============================================================================


def _load_template(template_name: str) -> dict:
    """
    Load issue template from assets/templates directory.

    Templates are bundled with the package and accessed via importlib.resources.
    """
    # Try importlib.resources first (for installed package)
    try:
        template_path = (
            resources.files("jira_assistant_skills.skills.jira-issue.assets.templates")
            / f"{template_name}_template.json"
        )
        template_content = template_path.read_text()
        return json.loads(template_content)
    except (ModuleNotFoundError, FileNotFoundError, TypeError):
        pass

    # Fallback to file path (for development/editable install)
    # Try relative to this file
    cli_dir = Path(__file__).parent.parent.parent
    template_dir = cli_dir.parent / "skills" / "jira-issue" / "assets" / "templates"
    template_file = template_dir / f"{template_name}_template.json"

    if not template_file.exists():
        # Try the plugin path
        plugin_template = (
            Path(__file__).parent.parent.parent.parent.parent
            / "plugins"
            / "jira-assistant-skills"
            / "skills"
            / "jira-issue"
            / "assets"
            / "templates"
            / f"{template_name}_template.json"
        )
        if plugin_template.exists():
            template_file = plugin_template
        else:
            raise FileNotFoundError(f"Template not found: {template_name}")

    with open(template_file) as f:
        return json.load(f)


def _get_issue_impl(issue_key: str, fields: list[str] | None = None) -> dict:
    """
    Get a JIRA issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        fields: Specific fields to retrieve (default: all)

    Returns:
        Issue data dictionary
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        issue = client.get_issue(issue_key, fields=fields)
        return issue
    finally:
        client.close()


def _create_issue_impl(
    project: str,
    issue_type: str,
    summary: str,
    description: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    labels: list[str] | None = None,
    components: list[str] | None = None,
    template: str | None = None,
    custom_fields: dict | None = None,
    epic: str | None = None,
    sprint: int | None = None,
    story_points: float | None = None,
    blocks: list[str] | None = None,
    relates_to: list[str] | None = None,
    estimate: str | None = None,
    no_defaults: bool = False,
) -> dict:
    """
    Create a new JIRA issue.

    Args:
        project: Project key
        issue_type: Issue type (Bug, Task, Story, etc.)
        summary: Issue summary
        description: Issue description (markdown supported)
        priority: Priority name
        assignee: Assignee account ID or email
        labels: List of labels
        components: List of component names
        template: Template name to use as base
        custom_fields: Additional custom fields
        epic: Epic key to link this issue to
        sprint: Sprint ID to add this issue to
        story_points: Story point estimate
        blocks: List of issue keys this issue blocks
        relates_to: List of issue keys this issue relates to
        estimate: Original time estimate (e.g., '2d', '4h')
        no_defaults: If True, skip applying project context defaults

    Returns:
        Created issue data
    """
    project = validate_project_key(project)

    # Apply project context defaults for unspecified fields
    defaults_applied = []
    if not no_defaults and has_project_context(project):
        defaults = get_project_defaults(project, issue_type)
        if defaults:
            if priority is None and "priority" in defaults:
                priority = defaults["priority"]
                defaults_applied.append("priority")
            if assignee is None and "assignee" in defaults:
                assignee = defaults["assignee"]
                defaults_applied.append("assignee")
            if labels is None and "labels" in defaults:
                labels = defaults["labels"]
                defaults_applied.append("labels")
            if components is None and "components" in defaults:
                components = defaults["components"]
                defaults_applied.append("components")
            if story_points is None and "story_points" in defaults:
                story_points = defaults["story_points"]
                defaults_applied.append("story_points")

    fields = {}

    if template:
        template_data = _load_template(template)
        fields = template_data.get("fields", {})

    fields["project"] = {"key": project}
    fields["issuetype"] = {"name": issue_type}
    fields["summary"] = summary

    if description:
        if description.strip().startswith("{"):
            fields["description"] = json.loads(description)
        elif "\n" in description or any(
            md in description for md in ["**", "*", "#", "`", "["]
        ):
            fields["description"] = markdown_to_adf(description)
        else:
            fields["description"] = text_to_adf(description)

    if priority:
        fields["priority"] = {"name": priority}

    if assignee:
        if assignee.lower() == "self":
            client = get_jira_client()
            account_id = client.get_current_user_id()
            fields["assignee"] = {"accountId": account_id}
            client.close()
        elif "@" in assignee:
            fields["assignee"] = {"emailAddress": assignee}
        else:
            fields["assignee"] = {"accountId": assignee}

    if labels:
        fields["labels"] = labels

    if components:
        fields["components"] = [{"name": comp} for comp in components]

    if custom_fields:
        fields.update(custom_fields)

    # Agile fields - get field IDs from configuration
    if epic or story_points is not None:
        agile_fields = get_agile_fields()

        if epic:
            epic = validate_issue_key(epic)
            fields[agile_fields["epic_link"]] = epic

        if story_points is not None:
            fields[agile_fields["story_points"]] = story_points

    # Time tracking
    if estimate:
        fields["timetracking"] = {"originalEstimate": estimate}

    client = get_jira_client()
    try:
        result = client.create_issue(fields)

        # Add to sprint after creation (sprint assignment requires issue to exist)
        issue_key = result.get("key")
        if sprint:
            client.move_issues_to_sprint(sprint, [issue_key])

        # Create issue links after creation
        links_created = []
        links_failed = []
        if blocks:
            for target_key in blocks:
                target_key = validate_issue_key(target_key)
                try:
                    client.create_link("Blocks", issue_key, target_key)
                    links_created.append(f"blocks {target_key}")
                except (PermissionError, NotFoundError) as e:
                    links_failed.append(f"blocks {target_key}: {e!s}")

        if relates_to:
            for target_key in relates_to:
                target_key = validate_issue_key(target_key)
                try:
                    client.create_link("Relates", issue_key, target_key)
                    links_created.append(f"relates to {target_key}")
                except (PermissionError, NotFoundError) as e:
                    links_failed.append(f"relates to {target_key}: {e!s}")

        if links_created:
            result["links_created"] = links_created
        if links_failed:
            result["links_failed"] = links_failed
        if defaults_applied:
            result["defaults_applied"] = defaults_applied

        return result
    finally:
        client.close()


def _update_issue_impl(
    issue_key: str,
    summary: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    labels: list[str] | None = None,
    components: list[str] | None = None,
    custom_fields: dict | None = None,
    notify_users: bool = True,
) -> None:
    """
    Update a JIRA issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        summary: New summary
        description: New description (markdown supported)
        priority: New priority
        assignee: New assignee (account ID or email)
        labels: New labels (replaces existing)
        components: New components (replaces existing)
        custom_fields: Custom fields to update
        notify_users: Send notifications to watchers
    """
    issue_key = validate_issue_key(issue_key)

    fields = {}

    if summary is not None:
        fields["summary"] = summary

    if description is not None:
        if description.strip().startswith("{"):
            fields["description"] = json.loads(description)
        elif "\n" in description or any(
            md in description for md in ["**", "*", "#", "`", "["]
        ):
            fields["description"] = markdown_to_adf(description)
        else:
            fields["description"] = text_to_adf(description)

    if priority is not None:
        fields["priority"] = {"name": priority}

    if assignee is not None:
        if assignee.lower() in ("none", "unassigned"):
            fields["assignee"] = None
        elif assignee.lower() == "self":
            client = get_jira_client()
            account_id = client.get_current_user_id()
            fields["assignee"] = {"accountId": account_id}
            client.close()
        elif "@" in assignee:
            fields["assignee"] = {"emailAddress": assignee}
        else:
            fields["assignee"] = {"accountId": assignee}

    if labels is not None:
        fields["labels"] = labels

    if components is not None:
        fields["components"] = [{"name": comp} for comp in components]

    if custom_fields:
        fields.update(custom_fields)

    if not fields:
        raise ValueError("No fields specified for update")

    client = get_jira_client()
    try:
        client.update_issue(issue_key, fields, notify_users=notify_users)
    finally:
        client.close()


def _delete_issue_impl(issue_key: str, force: bool = False) -> dict | None:
    """
    Delete a JIRA issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        force: Skip confirmation prompt

    Returns:
        Issue info dict if not force (for confirmation display), None otherwise
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        if not force:
            # Get issue details for confirmation
            try:
                issue = client.get_issue(
                    issue_key, fields=["summary", "issuetype", "status"]
                )
                return {
                    "key": issue_key,
                    "summary": issue.get("fields", {}).get("summary", ""),
                    "type": issue.get("fields", {})
                    .get("issuetype", {})
                    .get("name", ""),
                    "status": issue.get("fields", {}).get("status", {}).get("name", ""),
                }
            except JiraError:
                return {"key": issue_key}
        else:
            client.delete_issue(issue_key)
            return None
    finally:
        client.close()


def _confirm_and_delete(issue_key: str) -> None:
    """Actually delete the issue after confirmation."""
    issue_key = validate_issue_key(issue_key)
    client = get_jira_client()
    try:
        client.delete_issue(issue_key)
    finally:
        client.close()


# =============================================================================
# Click Command Group
# =============================================================================


@click.group()
def issue():
    """Commands for interacting with Jira issues."""
    pass


# =============================================================================
# Get Issue Command
# =============================================================================


@issue.command(name="get")
@click.argument("issue_key")
@click.option("--fields", "-f", help="Comma-separated list of fields to retrieve")
@click.option(
    "--detailed",
    "-d",
    is_flag=True,
    help="Show detailed information including description",
)
@click.option(
    "--show-links",
    "-l",
    is_flag=True,
    help="Show issue links (blocks, relates to, etc.)",
)
@click.option("--show-time", "-t", is_flag=True, help="Show time tracking information")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    help="Output format (text, json)",
)
@click.pass_context
def get_issue(
    ctx,
    issue_key: str,
    fields: str,
    detailed: bool,
    show_links: bool,
    show_time: bool,
    output: str,
):
    """Get the details of a specific issue."""
    try:
        # Parse fields
        field_list = parse_comma_list(fields)

        # Adjust field list based on flags
        show_detailed = detailed or show_links or show_time
        if show_links and field_list is not None and "issuelinks" not in field_list:
            field_list.append("issuelinks")
        if show_time and field_list is not None and "timetracking" not in field_list:
            field_list.append("timetracking")

        # Get issue
        issue = _get_issue_impl(issue_key=issue_key, fields=field_list)

        # Output formatting
        output_format = (
            output if output else (ctx.obj.get("OUTPUT", "text") if ctx.obj else "text")
        )
        if output_format == "json":
            click.echo(format_json(issue))
        else:
            click.echo(format_issue(issue, detailed=show_detailed))

            # Show time tracking if requested
            if show_time:
                tt = issue.get("fields", {}).get("timetracking", {})
                if tt:
                    click.echo("\nTime Tracking:")
                    if tt.get("originalEstimate"):
                        click.echo(
                            f"  Original Estimate:  {tt.get('originalEstimate')}"
                        )
                    if tt.get("remainingEstimate"):
                        click.echo(
                            f"  Remaining Estimate: {tt.get('remainingEstimate')}"
                        )
                    if tt.get("timeSpent"):
                        click.echo(f"  Time Spent:         {tt.get('timeSpent')}")
                else:
                    click.echo("\nTime Tracking: Not configured or no data")

    except JiraError as e:
        print_error(e)
        ctx.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        ctx.exit(1)


# =============================================================================
# Create Issue Command
# =============================================================================


@issue.command(name="create")
@click.option("--project", "-p", required=True, help="Project key (e.g., PROJ, DEV)")
@click.option(
    "--type",
    "-t",
    "issue_type",
    required=True,
    help="Issue type (Bug, Task, Story, etc.)",
)
@click.option("--summary", "-s", required=True, help="Issue summary (title)")
@click.option("--description", "-d", help="Issue description (supports markdown)")
@click.option("--priority", help="Priority (Highest, High, Medium, Low, Lowest)")
@click.option("--assignee", "-a", help='Assignee (account ID, email, or "self")')
@click.option("--labels", "-l", help="Comma-separated labels")
@click.option("--components", "-c", help="Comma-separated component names")
@click.option(
    "--template",
    type=click.Choice(["bug", "task", "story"]),
    help="Use a predefined template",
)
@click.option("--custom-fields", help="Custom fields as JSON string")
@click.option("--epic", "-e", help="Epic key to link this issue to (e.g., PROJ-100)")
@click.option("--sprint", type=int, help="Sprint ID to add this issue to")
@click.option("--story-points", type=float, help="Story point estimate")
@click.option("--blocks", help="Comma-separated issue keys this issue blocks")
@click.option("--relates-to", help="Comma-separated issue keys this issue relates to")
@click.option("--estimate", help="Original time estimate (e.g., 2d, 4h, 1w)")
@click.option("--no-defaults", is_flag=True, help="Disable project context defaults")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    help="Output format (text, json)",
)
@click.pass_context
def create_issue(
    ctx,
    project: str,
    issue_type: str,
    summary: str,
    description: str,
    priority: str,
    assignee: str,
    labels: str,
    components: str,
    template: str,
    custom_fields: str,
    epic: str,
    sprint: int,
    story_points: float,
    blocks: str,
    relates_to: str,
    estimate: str,
    no_defaults: bool,
    output: str,
):
    """Create a new JIRA issue."""
    try:
        # Parse comma-separated and JSON arguments
        labels_list = parse_comma_list(labels)
        components_list = parse_comma_list(components)
        custom_fields_dict = parse_json_arg(custom_fields)
        blocks_list = parse_comma_list(blocks)
        relates_to_list = parse_comma_list(relates_to)

        result = _create_issue_impl(
            project=project,
            issue_type=issue_type,
            summary=summary,
            description=description,
            priority=priority,
            assignee=assignee,
            labels=labels_list,
            components=components_list,
            template=template,
            custom_fields=custom_fields_dict,
            epic=epic,
            sprint=sprint,
            story_points=story_points,
            blocks=blocks_list,
            relates_to=relates_to_list,
            estimate=estimate,
            no_defaults=no_defaults,
        )

        issue_key = result.get("key")

        # Output formatting
        output_format = (
            output if output else (ctx.obj.get("OUTPUT", "text") if ctx.obj else "text")
        )
        if output_format == "json":
            click.echo(json.dumps(result, indent=2))
        else:
            print_success(f"Created issue: {issue_key}")
            base_url = result.get("self", "").split("/rest/api/")[0]
            click.echo(f"URL: {base_url}/browse/{issue_key}")
            defaults_applied = result.get("defaults_applied", [])
            if defaults_applied:
                click.echo(f"Defaults applied: {', '.join(defaults_applied)}")
            links_created = result.get("links_created", [])
            if links_created:
                click.echo(f"Links: {', '.join(links_created)}")
            links_failed = result.get("links_failed", [])
            if links_failed:
                click.echo(f"Links failed: {', '.join(links_failed)}")

    except JiraError as e:
        print_error(e)
        ctx.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        ctx.exit(1)


# =============================================================================
# Update Issue Command
# =============================================================================


@issue.command(name="update")
@click.argument("issue_key")
@click.option("--summary", "-s", help="New summary (title)")
@click.option("--description", "-d", help="New description (supports markdown)")
@click.option("--priority", help="New priority (Highest, High, Medium, Low, Lowest)")
@click.option(
    "--assignee", "-a", help='New assignee (account ID, email, "self", or "none")'
)
@click.option("--labels", "-l", help="Comma-separated labels (replaces existing)")
@click.option(
    "--components", "-c", help="Comma-separated component names (replaces existing)"
)
@click.option("--custom-fields", help="Custom fields as JSON string")
@click.option("--no-notify", is_flag=True, help="Do not send notifications to watchers")
@click.pass_context
def update_issue(
    ctx,
    issue_key: str,
    summary: str,
    description: str,
    priority: str,
    assignee: str,
    labels: str,
    components: str,
    custom_fields: str,
    no_notify: bool,
):
    """Update a JIRA issue."""
    try:
        # Parse comma-separated and JSON arguments
        labels_list = parse_comma_list(labels)
        components_list = parse_comma_list(components)
        custom_fields_dict = parse_json_arg(custom_fields)

        _update_issue_impl(
            issue_key=issue_key,
            summary=summary,
            description=description,
            priority=priority,
            assignee=assignee,
            labels=labels_list,
            components=components_list,
            custom_fields=custom_fields_dict,
            notify_users=not no_notify,
        )

        print_success(f"Updated issue: {issue_key}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)
    except JiraError as e:
        print_error(e)
        ctx.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        ctx.exit(1)


# =============================================================================
# Delete Issue Command
# =============================================================================


@issue.command(name="delete")
@click.argument("issue_key")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete_issue(ctx, issue_key: str, force: bool):
    """Delete a JIRA issue."""
    try:
        if force:
            # Direct delete without confirmation
            _delete_issue_impl(issue_key, force=True)
            print_success(f"Deleted issue: {issue_key}")
        else:
            # Get issue info for confirmation
            issue_info = _delete_issue_impl(issue_key, force=False)

            if issue_info:
                click.echo(f"\nIssue: {issue_info.get('key', issue_key)}")
                if issue_info.get("type"):
                    click.echo(f"Type: {issue_info['type']}")
                if issue_info.get("status"):
                    click.echo(f"Status: {issue_info['status']}")
                if issue_info.get("summary"):
                    click.echo(f"Summary: {issue_info['summary']}")
                click.echo()

            if click.confirm("Are you sure you want to delete this issue?"):
                _confirm_and_delete(issue_key)
                print_success(f"Deleted issue: {issue_key}")
            else:
                click.echo("Deletion cancelled.")

    except JiraError as e:
        print_error(e)
        ctx.exit(1)
    except click.Abort:
        click.echo("\nDeletion cancelled.")
    except Exception as e:
        print_error(e, debug=True)
        ctx.exit(1)
