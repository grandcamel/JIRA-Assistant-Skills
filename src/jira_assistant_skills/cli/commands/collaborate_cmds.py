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
@click.argument('issue_key')
@click.option('--body', '-b', required=True, help='Comment text')
@click.option('--format', '-f', 'body_format', type=click.Choice(['text', 'markdown', 'adf']),
              default='text', help='Comment format')
@click.option('--visibility-role', help='Restrict visibility to role')
@click.option('--visibility-group', help='Restrict visibility to group')
@click.pass_context
def comment_add(ctx, issue_key: str, body: str, body_format: str, visibility_role: str, visibility_group: str):
    """Add a comment to an issue.

    Examples:
        jira collaborate comment add PROJ-123 --body "Starting work"
        jira collaborate comment add PROJ-123 --body "Internal note" --visibility-role Developers
    """
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "add_comment.py"

    script_args = [issue_key, "--body", body]
    if body_format != 'text':
        script_args.extend(["--format", body_format])
    if visibility_role:
        script_args.extend(["--visibility-role", visibility_role])
    if visibility_group:
        script_args.extend(["--visibility-group", visibility_group])

    run_skill_script_subprocess(script_path, script_args, ctx)


@comment.command(name="list")
@click.argument('issue_key')
@click.option('--since', '-s', help='Show comments since date')
@click.option('--author', '-a', help='Filter by author')
@click.pass_context
def comment_list(ctx, issue_key: str, since: str, author: str):
    """List comments on an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "get_comments.py"

    script_args = [issue_key]
    if since:
        script_args.extend(["--since", since])
    if author:
        script_args.extend(["--author", author])

    run_skill_script_subprocess(script_path, script_args, ctx)


@comment.command(name="update")
@click.argument('issue_key')
@click.argument('comment_id')
@click.argument('body')
@click.option('--format', '-f', 'body_format', type=click.Choice(['text', 'markdown', 'adf']),
              default='text', help='Comment format')
@click.pass_context
def comment_update(ctx, issue_key: str, comment_id: str, body: str, body_format: str):
    """Update a comment."""
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "update_comment.py"

    script_args = [issue_key, comment_id, body]
    if body_format != 'text':
        script_args.extend(["--format", body_format])

    run_skill_script_subprocess(script_path, script_args, ctx)


@comment.command(name="delete")
@click.argument('issue_key')
@click.argument('comment_id')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation')
@click.pass_context
def comment_delete(ctx, issue_key: str, comment_id: str, force: bool):
    """Delete a comment."""
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "delete_comment.py"

    script_args = [issue_key, comment_id]
    if force:
        script_args.append("--force")

    run_skill_script_subprocess(script_path, script_args, ctx)


# Attachments subgroup
@collaborate.group()
def attachment():
    """Manage issue attachments."""
    pass


@attachment.command(name="upload")
@click.argument('issue_key')
@click.option('--file', '-f', 'file_path', required=True, help='Path to file to upload')
@click.option('--name', '-n', help='Override filename')
@click.pass_context
def attachment_upload(ctx, issue_key: str, file_path: str, name: str):
    """Upload an attachment to an issue.

    Examples:
        jira collaborate attachment upload PROJ-123 --file screenshot.png
        jira collaborate attachment upload PROJ-123 --file doc.pdf --name "Requirements.pdf"
    """
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "upload_attachment.py"

    script_args = [issue_key, "--file", file_path]
    if name:
        script_args.extend(["--name", name])

    run_skill_script_subprocess(script_path, script_args, ctx)


@attachment.command(name="download")
@click.argument('issue_key')
@click.argument('attachment_id')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def attachment_download(ctx, issue_key: str, attachment_id: str, output: str):
    """Download an attachment from an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "download_attachment.py"

    script_args = [issue_key, attachment_id]
    if output:
        script_args.extend(["--output", output])

    run_skill_script_subprocess(script_path, script_args, ctx)


# Watchers commands
@collaborate.command(name="watchers")
@click.argument('issue_key')
@click.option('--add', '-a', 'add_user', help='Add a watcher')
@click.option('--remove', '-r', 'remove_user', help='Remove a watcher')
@click.pass_context
def collaborate_watchers(ctx, issue_key: str, add_user: str, remove_user: str):
    """Manage watchers on an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "manage_watchers.py"

    script_args = [issue_key]
    if add_user:
        script_args.extend(["--add", add_user])
    if remove_user:
        script_args.extend(["--remove", remove_user])

    run_skill_script_subprocess(script_path, script_args, ctx)


# Activity feed
@collaborate.command(name="activity")
@click.argument('issue_key')
@click.option('--since', '-s', help='Show activity since date')
@click.option('--type', '-t', 'activity_type', help='Filter by activity type')
@click.pass_context
def collaborate_activity(ctx, issue_key: str, since: str, activity_type: str):
    """Get activity feed for an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "get_activity.py"

    script_args = [issue_key]
    if since:
        script_args.extend(["--since", since])
    if activity_type:
        script_args.extend(["--type", activity_type])

    run_skill_script_subprocess(script_path, script_args, ctx)


# Notifications
@collaborate.command(name="notify")
@click.argument('issue_key')
@click.option('--users', '-u', help='Comma-separated user IDs or emails')
@click.option('--groups', '-g', help='Comma-separated group names')
@click.option('--subject', '-s', help='Notification subject')
@click.option('--body', '-b', help='Notification body')
@click.pass_context
def collaborate_notify(ctx, issue_key: str, users: str, groups: str, subject: str, body: str):
    """Send a notification about an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "send_notification.py"

    script_args = [issue_key]
    if users:
        script_args.extend(["--users", users])
    if groups:
        script_args.extend(["--groups", groups])
    if subject:
        script_args.extend(["--subject", subject])
    if body:
        script_args.extend(["--body", body])

    run_skill_script_subprocess(script_path, script_args, ctx)


# Custom fields
@collaborate.command(name="update-fields")
@click.argument('issue_key')
@click.option('--fields', '-f', required=True, help='Custom fields as JSON string')
@click.pass_context
def collaborate_update_fields(ctx, issue_key: str, fields: str):
    """Update custom fields on an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-collaborate" / "scripts" / "update_custom_fields.py"
    run_skill_script_subprocess(script_path, [issue_key, "--fields", fields], ctx)
