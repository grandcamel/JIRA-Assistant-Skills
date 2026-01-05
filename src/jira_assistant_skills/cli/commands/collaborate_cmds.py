import click

from jira_assistant_skills.utils import SKILLS_ROOT_DIR, run_skill_script_subprocess


@click.group()
def collaborate():
    """Commands for comments, attachments, and watchers."""
    pass


# Comments subgroup
@collaborate.group()
def comment():
    """Manage issue comments."""
    pass


@comment.command(name="add")
@click.argument("issue_key")
@click.option("--body", "-b", required=True, help="Comment text")
@click.option(
    "--format",
    "-f",
    "body_format",
    type=click.Choice(["text", "markdown", "adf"]),
    default="text",
    help="Comment format",
)
@click.option("--visibility-role", help="Restrict visibility to role")
@click.option("--visibility-group", help="Restrict visibility to group")
@click.pass_context
def comment_add(
    ctx,
    issue_key: str,
    body: str,
    body_format: str,
    visibility_role: str,
    visibility_group: str,
):
    """Add a comment to an issue.

    Examples:
        jira collaborate comment add PROJ-123 --body "Starting work"
        jira collaborate comment add PROJ-123 --body "Internal note" --visibility-role Developers
    """
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "add_comment.py"

    script_args = [issue_key, "--body", body]
    if body_format != "text":
        script_args.extend(["--format", body_format])
    if visibility_role:
        script_args.extend(["--visibility-role", visibility_role])
    if visibility_group:
        script_args.extend(["--visibility-group", visibility_group])

    run_skill_script_subprocess(script_path, script_args, ctx)


@comment.command(name="list")
@click.argument("issue_key")
@click.option("--id", help="Get specific comment by ID")
@click.option(
    "--limit",
    "-l",
    type=int,
    default=50,
    help="Maximum number of comments to return (default: 50)",
)
@click.option(
    "--offset", type=int, default=0, help="Starting index for pagination (default: 0)"
)
@click.option(
    "--order",
    type=click.Choice(["asc", "desc"]),
    default="desc",
    help="Sort order: asc (oldest first) or desc (newest first)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
def comment_list(
    ctx, issue_key: str, id: str, limit: int, offset: int, order: str, output: str
):
    """List comments on an issue.

    Examples:
        jira collaborate comment list PROJ-123
        jira collaborate comment list PROJ-123 --id 10001
        jira collaborate comment list PROJ-123 --limit 10 --order asc
    """
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "get_comments.py"

    script_args = [issue_key]
    if id:
        script_args.extend(["--id", id])
    if limit != 50:
        script_args.extend(["--limit", str(limit)])
    if offset != 0:
        script_args.extend(["--offset", str(offset)])
    if order != "desc":
        script_args.extend(["--order", order])
    if output != "text":
        script_args.extend(["--output", output])

    run_skill_script_subprocess(script_path, script_args, ctx)


@comment.command(name="update")
@click.argument("issue_key")
@click.option("--id", "-i", "comment_id", required=True, help="Comment ID to update")
@click.option("--body", "-b", required=True, help="New comment body")
@click.option(
    "--format",
    "-f",
    "body_format",
    type=click.Choice(["text", "markdown", "adf"]),
    default="text",
    help="Comment format",
)
@click.pass_context
def comment_update(ctx, issue_key: str, comment_id: str, body: str, body_format: str):
    """Update a comment.

    Examples:
        jira collaborate comment update PROJ-123 --id 10001 --body "Updated text"
        jira collaborate comment update PROJ-123 --id 10001 --body "**Bold**" --format markdown
    """
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "update_comment.py"

    script_args = [issue_key, "--id", comment_id, "--body", body]
    if body_format != "text":
        script_args.extend(["--format", body_format])

    run_skill_script_subprocess(script_path, script_args, ctx)


@comment.command(name="delete")
@click.argument("issue_key")
@click.option("--id", "-i", "comment_id", required=True, help="Comment ID to delete")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be deleted without deleting"
)
@click.pass_context
def comment_delete(ctx, issue_key: str, comment_id: str, yes: bool, dry_run: bool):
    """Delete a comment.

    Examples:
        jira collaborate comment delete PROJ-123 --id 10001
        jira collaborate comment delete PROJ-123 --id 10001 --yes
        jira collaborate comment delete PROJ-123 --id 10001 --dry-run
    """
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "delete_comment.py"

    script_args = [issue_key, "--id", comment_id]
    if yes:
        script_args.append("--yes")
    if dry_run:
        script_args.append("--dry-run")

    run_skill_script_subprocess(script_path, script_args, ctx)


# Attachments subgroup
@collaborate.group()
def attachment():
    """Manage issue attachments."""
    pass


@attachment.command(name="upload")
@click.argument("issue_key")
@click.option("--file", "-f", "file_path", required=True, help="Path to file to upload")
@click.option("--name", "-n", help="Override filename")
@click.pass_context
def attachment_upload(ctx, issue_key: str, file_path: str, name: str):
    """Upload an attachment to an issue.

    Examples:
        jira collaborate attachment upload PROJ-123 --file screenshot.png
        jira collaborate attachment upload PROJ-123 --file doc.pdf --name "Requirements.pdf"
    """
    script_path = (
        SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "upload_attachment.py"
    )

    script_args = [issue_key, "--file", file_path]
    if name:
        script_args.extend(["--name", name])

    run_skill_script_subprocess(script_path, script_args, ctx)


@attachment.command(name="download")
@click.argument("issue_key")
@click.argument("attachment_id")
@click.option("--output", "-o", help="Output file path")
@click.pass_context
def attachment_download(ctx, issue_key: str, attachment_id: str, output: str):
    """Download an attachment from an issue."""
    script_path = (
        SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "download_attachment.py"
    )

    script_args = [issue_key, attachment_id]
    if output:
        script_args.extend(["--output", output])

    run_skill_script_subprocess(script_path, script_args, ctx)


# Watchers commands
@collaborate.command(name="watchers")
@click.argument("issue_key")
@click.option("--add", "-a", "add_user", help="Add watcher (account ID or email)")
@click.option(
    "--remove", "-r", "remove_user", help="Remove watcher (account ID or email)"
)
@click.option(
    "--list", "-l", "list_watchers", is_flag=True, help="List current watchers"
)
@click.pass_context
def collaborate_watchers(
    ctx, issue_key: str, add_user: str, remove_user: str, list_watchers: bool
):
    """Manage watchers on an issue.

    Examples:
        jira collaborate watchers PROJ-123 --list
        jira collaborate watchers PROJ-123 --add user@example.com
        jira collaborate watchers PROJ-123 --remove user@example.com
    """
    script_path = (
        SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "manage_watchers.py"
    )

    script_args = [issue_key]
    if add_user:
        script_args.extend(["--add", add_user])
    elif remove_user:
        script_args.extend(["--remove", remove_user])
    elif list_watchers:
        script_args.append("--list")
    else:
        # Default to listing watchers if no action specified
        script_args.append("--list")

    run_skill_script_subprocess(script_path, script_args, ctx)


# Activity feed
@collaborate.command(name="activity")
@click.argument("issue_key")
@click.option(
    "--limit",
    "-l",
    type=int,
    default=100,
    help="Maximum number of changelog entries (default: 100)",
)
@click.option(
    "--offset",
    type=int,
    default=0,
    help="Starting position for pagination (default: 0)",
)
@click.option(
    "--field", "-f", multiple=True, help="Filter by field name (can be repeated)"
)
@click.option(
    "--field-type",
    "-t",
    type=click.Choice(["jira", "custom"]),
    multiple=True,
    help="Filter by field type: jira (built-in) or custom",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def collaborate_activity(
    ctx,
    issue_key: str,
    limit: int,
    offset: int,
    field: tuple,
    field_type: tuple,
    output: str,
):
    """Get activity feed for an issue.

    Examples:
        jira collaborate activity PROJ-123
        jira collaborate activity PROJ-123 --limit 10
        jira collaborate activity PROJ-123 --field status --field assignee
        jira collaborate activity PROJ-123 --field-type custom --output json
    """
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "get_activity.py"

    script_args = [issue_key]
    if limit != 100:
        script_args.extend(["--limit", str(limit)])
    if offset != 0:
        script_args.extend(["--offset", str(offset)])
    for f in field:
        script_args.extend(["--field", f])
    for ft in field_type:
        script_args.extend(["--field-type", ft])
    if output != "table":
        script_args.extend(["--output", output])

    run_skill_script_subprocess(script_path, script_args, ctx)


# Notifications
@collaborate.command(name="notify")
@click.argument("issue_key")
@click.option(
    "--user",
    "-u",
    multiple=True,
    help="Notify specific user by account ID (can be repeated)",
)
@click.option(
    "--group", "-g", multiple=True, help="Notify group by name (can be repeated)"
)
@click.option("--watchers", is_flag=True, help="Notify all watchers")
@click.option("--assignee", is_flag=True, help="Notify assignee")
@click.option("--reporter", is_flag=True, help="Notify reporter")
@click.option("--voters", is_flag=True, help="Notify voters")
@click.option("--subject", "-s", help="Notification subject")
@click.option("--body", "-b", help="Notification body")
@click.option("--dry-run", is_flag=True, help="Show what would be sent without sending")
@click.pass_context
def collaborate_notify(
    ctx,
    issue_key: str,
    user: tuple,
    group: tuple,
    watchers: bool,
    assignee: bool,
    reporter: bool,
    voters: bool,
    subject: str,
    body: str,
    dry_run: bool,
):
    """Send a notification about an issue.

    Examples:
        jira collaborate notify PROJ-123 --watchers
        jira collaborate notify PROJ-123 --assignee --reporter --subject "Please review"
        jira collaborate notify PROJ-123 --user 5b10a2844c20165700ede21g --group developers
        jira collaborate notify PROJ-123 --watchers --dry-run
    """
    script_path = (
        SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "send_notification.py"
    )

    script_args = [issue_key]
    for u in user:
        script_args.extend(["--user", u])
    for g in group:
        script_args.extend(["--group", g])
    if watchers:
        script_args.append("--watchers")
    if assignee:
        script_args.append("--assignee")
    if reporter:
        script_args.append("--reporter")
    if voters:
        script_args.append("--voters")
    if subject:
        script_args.extend(["--subject", subject])
    if body:
        script_args.extend(["--body", body])
    if dry_run:
        script_args.append("--dry-run")

    run_skill_script_subprocess(script_path, script_args, ctx)


# Custom fields
@collaborate.command(name="update-fields")
@click.argument("issue_key")
@click.option("--fields", "-f", required=True, help="Custom fields as JSON string")
@click.pass_context
def collaborate_update_fields(ctx, issue_key: str, fields: str):
    """Update custom fields on an issue."""
    script_path = (
        SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "update_custom_fields.py"
    )
    run_skill_script_subprocess(script_path, [issue_key, "--fields", fields], ctx)
