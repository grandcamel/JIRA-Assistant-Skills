"""
Collaborate commands for jira-as CLI.

Commands for issue collaboration:
- comment: Manage comments (add, list, update, delete)
- attachment: Manage attachments (upload, download)
- watchers: Manage issue watchers
- activity: Get issue activity/changelog
- notify: Send notifications
- update-fields: Update custom fields
"""

import contextlib
import json
import os
from datetime import datetime
from typing import Any

import click

from jira_assistant_skills_lib import (
    UserNotFoundError,
    ValidationError,
    adf_to_text,
    format_json,
    format_table,
    get_jira_client,
    markdown_to_adf,
    print_info,
    print_success,
    resolve_user_to_account_id,
    text_to_adf,
    validate_file_path,
    validate_issue_key,
)

from ..cli_utils import handle_jira_errors

# =============================================================================
# Comment Implementation Functions
# =============================================================================


def _add_comment_impl(
    issue_key: str,
    body: str,
    body_format: str = "text",
    visibility_type: str | None = None,
    visibility_value: str | None = None,
) -> dict:
    """
    Add a comment to an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        body: Comment body
        body_format: Format ('text', 'markdown', or 'adf')
        visibility_type: 'role' or 'group' (None for public)
        visibility_value: Role or group name

    Returns:
        Created comment data
    """
    issue_key = validate_issue_key(issue_key)

    if body_format == "adf":
        comment_body = json.loads(body)
    elif body_format == "markdown":
        comment_body = markdown_to_adf(body)
    else:
        comment_body = text_to_adf(body)

    client = get_jira_client()
    try:
        if visibility_type:
            result = client.add_comment_with_visibility(
                issue_key,
                comment_body,
                visibility_type=visibility_type,
                visibility_value=visibility_value,
            )
        else:
            result = client.add_comment(issue_key, comment_body)
        return result
    finally:
        client.close()


def _get_comments_impl(
    issue_key: str,
    comment_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    order: str = "desc",
) -> dict[str, Any] | list:
    """
    Get comments on an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        comment_id: Optional specific comment ID
        limit: Maximum number of comments
        offset: Starting index
        order: Sort order ('asc' or 'desc')

    Returns:
        Comment data or list of comments
    """
    issue_key = validate_issue_key(issue_key)
    order_by = "+created" if order == "asc" else "-created"

    client = get_jira_client()
    try:
        if comment_id:
            return client.get_comment(issue_key, comment_id)
        return client.get_comments(
            issue_key, max_results=limit, start_at=offset, order_by=order_by
        )
    finally:
        client.close()


def _update_comment_impl(
    issue_key: str,
    comment_id: str,
    body: str,
    body_format: str = "text",
) -> dict[str, Any]:
    """
    Update a comment.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        comment_id: Comment ID to update
        body: New comment body
        body_format: Format ('text', 'markdown', or 'adf')

    Returns:
        Updated comment data
    """
    issue_key = validate_issue_key(issue_key)

    if body_format == "adf":
        comment_body = json.loads(body)
    elif body_format == "markdown":
        comment_body = markdown_to_adf(body)
    else:
        comment_body = text_to_adf(body)

    client = get_jira_client()
    try:
        return client.update_comment(issue_key, comment_id, comment_body)
    finally:
        client.close()


def _delete_comment_impl(
    issue_key: str,
    comment_id: str,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any] | None:
    """
    Delete a comment.

    Args:
        issue_key: Issue key
        comment_id: Comment ID to delete
        force: Skip confirmation
        dry_run: Preview without deleting

    Returns:
        Comment info if not force (for confirmation), None otherwise
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        if dry_run or not force:
            comment = client.get_comment(issue_key, comment_id)

            if dry_run:
                return {
                    "dry_run": True,
                    "id": comment_id,
                    "author": comment.get("author", {}).get("displayName", "Unknown"),
                    "created": comment.get("created", "")[:16],
                    "body": adf_to_text(comment.get("body", {}))[:200],
                }

            return {
                "dry_run": False,
                "id": comment_id,
                "author": comment.get("author", {}).get("displayName", "Unknown"),
                "created": comment.get("created", "")[:16],
                "body": adf_to_text(comment.get("body", {}))[:100],
            }

        client.delete_comment(issue_key, comment_id)
        return None
    finally:
        client.close()


def _format_comment_body(body: dict[str, Any], max_length: int = 50) -> str:
    """Extract and format comment body from ADF."""
    text = adf_to_text(body)
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def _format_comments_table(comments: list[dict[str, Any]]) -> str:
    """Format comments as a table."""
    rows = []
    for comment in comments:
        comment_id = comment.get("id", "N/A")
        author = comment.get("author", {}).get("displayName", "Unknown")
        created = comment.get("created", "")

        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                date_str = created[:16]
        else:
            date_str = "N/A"

        body = comment.get("body", {})
        body_preview = _format_comment_body(body, max_length=60)

        visibility = comment.get("visibility")
        if visibility:
            vis_type = visibility.get("type", "")
            vis_value = visibility.get("value", "")
            body_preview += f" [{vis_type}: {vis_value}]"

        rows.append(
            {
                "id": comment_id,
                "author": author,
                "date": date_str,
                "body": body_preview,
            }
        )

    return format_table(
        rows,
        columns=["id", "author", "date", "body"],
        headers=["ID", "Author", "Date", "Body"],
    )


# =============================================================================
# Attachment Implementation Functions
# =============================================================================


def _upload_attachment_impl(
    issue_key: str,
    file_path: str,
    file_name: str | None = None,
) -> dict | list:
    """
    Upload an attachment to an issue.

    Args:
        issue_key: Issue key
        file_path: Path to file
        file_name: Override filename

    Returns:
        Attachment data
    """
    issue_key = validate_issue_key(issue_key)
    file_path = validate_file_path(file_path, must_exist=True)

    client = get_jira_client()
    try:
        return client.upload_file(
            f"/rest/api/3/issue/{issue_key}/attachments",
            file_path,
            file_name=file_name,
            operation=f"upload attachment to {issue_key}",
        )
    finally:
        client.close()


def _list_attachments_impl(issue_key: str) -> list[dict[str, Any]]:
    """List all attachments for an issue."""
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        return client.get_attachments(issue_key)
    finally:
        client.close()


def _download_attachment_impl(
    issue_key: str,
    attachment_id: str | None = None,
    attachment_name: str | None = None,
    output_dir: str | None = None,
) -> str:
    """
    Download a specific attachment.

    Args:
        issue_key: Issue key
        attachment_id: Attachment ID
        attachment_name: Attachment name (if ID not specified)
        output_dir: Directory to save file

    Returns:
        Path to downloaded file
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        attachments = client.get_attachments(issue_key)

        target = None
        if attachment_id:
            for att in attachments:
                if str(att.get("id")) == str(attachment_id):
                    target = att
                    break
            if not target:
                raise ValidationError(
                    f"Attachment with ID {attachment_id} not found on {issue_key}"
                )
        elif attachment_name:
            for att in attachments:
                if att.get("filename") == attachment_name:
                    target = att
                    break
            if not target:
                raise ValidationError(
                    f"Attachment '{attachment_name}' not found on {issue_key}"
                )
        else:
            raise ValidationError("Either --id or --name must be specified")

        filename = target.get("filename", f"attachment_{target.get('id')}")
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, filename)
        else:
            output_path = filename

        content_url = target.get("content")
        if not content_url:
            raise ValidationError(
                f"No content URL found for attachment {target.get('id')}"
            )

        client.download_file(
            content_url, output_path, operation=f"download attachment {filename}"
        )
        return output_path
    finally:
        client.close()


def _download_all_attachments_impl(
    issue_key: str, output_dir: str | None = None
) -> list[str]:
    """Download all attachments from an issue."""
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        attachments = client.get_attachments(issue_key)

        if not attachments:
            return []

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        downloaded = []
        for att in attachments:
            filename = att.get("filename", f"attachment_{att.get('id')}")
            content_url = att.get("content")

            if not content_url:
                continue

            if output_dir:
                output_path = os.path.join(output_dir, filename)
            else:
                output_path = filename

            if os.path.exists(output_path):
                base, ext = os.path.splitext(output_path)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                output_path = f"{base}_{counter}{ext}"

            client.download_file(
                content_url, output_path, operation=f"download attachment {filename}"
            )
            downloaded.append(output_path)

        return downloaded
    finally:
        client.close()


def _format_attachment_list(attachments: list[dict[str, Any]]) -> str:
    """Format attachments as a table."""
    if not attachments:
        return "No attachments found."

    table_data = []
    for att in attachments:
        size_bytes = att.get("size", 0)
        if size_bytes >= 1048576:
            size_str = f"{size_bytes / 1048576:.1f} MB"
        elif size_bytes >= 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes} B"

        table_data.append(
            {
                "id": att.get("id", ""),
                "filename": att.get("filename", ""),
                "size": size_str,
                "mime_type": att.get("mimeType", ""),
                "created": att.get("created", "")[:10] if att.get("created") else "",
                "author": att.get("author", {}).get("displayName", ""),
            }
        )

    return format_table(
        table_data,
        columns=["id", "filename", "size", "mime_type", "created", "author"],
        headers=["ID", "Filename", "Size", "Type", "Created", "Author"],
    )


# =============================================================================
# Watchers Implementation Functions
# =============================================================================


def _list_watchers_impl(issue_key: str) -> list:
    """List watchers on an issue."""
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        result = client.get(
            f"/rest/api/3/issue/{issue_key}/watchers",
            operation=f"get watchers for {issue_key}",
        )
        return result.get("watchers", [])
    finally:
        client.close()


def _add_watcher_impl(issue_key: str, user: str) -> None:
    """Add a watcher to an issue."""
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        try:
            account_id = resolve_user_to_account_id(client, user)
        except UserNotFoundError as e:
            raise ValidationError(str(e))

        client.post(
            f"/rest/api/3/issue/{issue_key}/watchers",
            data=f'"{account_id}"',
            operation=f"add watcher to {issue_key}",
        )
    finally:
        client.close()


def _remove_watcher_impl(issue_key: str, user: str) -> None:
    """Remove a watcher from an issue."""
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        try:
            account_id = resolve_user_to_account_id(client, user)
        except UserNotFoundError as e:
            raise ValidationError(str(e))

        client.delete(
            f"/rest/api/3/issue/{issue_key}/watchers?accountId={account_id}",
            operation=f"remove watcher from {issue_key}",
        )
    finally:
        client.close()


# =============================================================================
# Activity Implementation Functions
# =============================================================================


def _get_activity_impl(
    issue_key: str, limit: int = 100, offset: int = 0
) -> dict[str, Any]:
    """Get activity/changelog for an issue."""
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        return client.get_changelog(issue_key, max_results=limit, start_at=offset)
    finally:
        client.close()


def _parse_changelog(
    changelog_data: dict[str, Any],
    field_filter: list[str] | None = None,
    field_type_filter: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Parse changelog into simplified format with optional filtering."""
    parsed = []

    for entry in changelog_data.get("values", []):
        author = entry.get("author", {}).get("displayName", "Unknown")
        created = entry.get("created", "")

        for item in entry.get("items", []):
            field = item.get("field", "")
            field_type = item.get("fieldtype", "")
            from_string = item.get("fromString") or ""
            to_string = item.get("toString") or ""

            if field_filter:
                if field.lower() not in [f.lower() for f in field_filter]:
                    continue

            if field_type_filter:
                if field_type.lower() not in [ft.lower() for ft in field_type_filter]:
                    continue

            parsed.append(
                {
                    "type": field,
                    "field": field,
                    "field_type": field_type,
                    "from": from_string,
                    "to": to_string,
                    "author": author,
                    "created": created,
                }
            )

    return parsed


def _display_activity_table(changes: list[dict[str, Any]]) -> str:
    """Format activity as a table."""
    if not changes:
        return "No activity found."

    table_data = []
    for change in changes:
        table_data.append(
            {
                "date": change.get("created", "")[:16],
                "author": change.get("author", ""),
                "field": change.get("field", ""),
                "from": change.get("from", "") or "(none)",
                "to": change.get("to", "") or "(none)",
            }
        )

    return format_table(
        table_data,
        columns=["date", "author", "field", "from", "to"],
        headers=["Date", "Author", "Field", "From", "To"],
    )


# =============================================================================
# Notification Implementation Functions
# =============================================================================


def _send_notification_impl(
    issue_key: str,
    subject: str | None = None,
    body: str | None = None,
    watchers: bool = False,
    assignee: bool = False,
    reporter: bool = False,
    voters: bool = False,
    users: list[str] | None = None,
    groups: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any] | None:
    """
    Send notification about an issue.

    Args:
        issue_key: Issue key
        subject: Notification subject
        body: Notification body
        watchers: Notify watchers
        assignee: Notify assignee
        reporter: Notify reporter
        voters: Notify voters
        users: List of account IDs to notify
        groups: List of group names to notify
        dry_run: Preview without sending

    Returns:
        Notification details for dry_run, None otherwise
    """
    issue_key = validate_issue_key(issue_key)

    if dry_run:
        return {
            "issue_key": issue_key,
            "subject": subject,
            "body": body,
            "recipients": {
                "reporter": reporter,
                "assignee": assignee,
                "watchers": watchers,
                "voters": voters,
                "users": users or [],
                "groups": groups or [],
            },
        }

    to = {
        "reporter": reporter,
        "assignee": assignee,
        "watchers": watchers,
        "voters": voters,
        "users": [],
        "groups": [],
    }

    if users:
        to["users"] = [{"accountId": user_id} for user_id in users]

    if groups:
        to["groups"] = [{"name": group_name} for group_name in groups]

    client = get_jira_client()
    try:
        client.notify_issue(issue_key, subject=subject, text_body=body, to=to)
        return None
    finally:
        client.close()


# =============================================================================
# Custom Fields Implementation Functions
# =============================================================================


def _update_custom_fields_impl(
    issue_key: str,
    field: str | None = None,
    value: str | None = None,
    fields_json: str | None = None,
) -> None:
    """
    Update custom fields on an issue.

    Args:
        issue_key: Issue key
        field: Single field ID
        value: Single field value
        fields_json: JSON string with multiple fields
    """
    issue_key = validate_issue_key(issue_key)

    if fields_json:
        fields = json.loads(fields_json)
    elif field and value is not None:
        with contextlib.suppress(json.JSONDecodeError):
            value = json.loads(value)
        fields = {field: value}
    else:
        raise ValidationError(
            "Either --field and --value, or --fields must be specified"
        )

    client = get_jira_client()
    try:
        client.update_issue(issue_key, fields, notify_users=True)
    finally:
        client.close()


# =============================================================================
# CLI Commands
# =============================================================================


@click.group()
def collaborate():
    """Commands for comments, attachments, and watchers."""
    pass


# =============================================================================
# Comment Subgroup
# =============================================================================


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
@handle_jira_errors
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
        jira-as collaborate comment add PROJ-123 --body "Starting work"
        jira-as collaborate comment add PROJ-123 --body "Internal" --visibility-role Developers
    """
    if visibility_role and visibility_group:
        raise click.UsageError(
            "Cannot specify both --visibility-role and --visibility-group"
        )

    visibility_type = None
    visibility_value = None
    if visibility_role:
        visibility_type = "role"
        visibility_value = visibility_role
    elif visibility_group:
        visibility_type = "group"
        visibility_value = visibility_group

    result = _add_comment_impl(
        issue_key=issue_key,
        body=body,
        body_format=body_format,
        visibility_type=visibility_type,
        visibility_value=visibility_value,
    )

    comment_id = result.get("id", "")
    print_success(f"Added comment to {issue_key} (ID: {comment_id})")

    visibility = result.get("visibility")
    if visibility:
        vis_type = visibility.get("type", "")
        vis_value = visibility.get("value", "")
        click.echo(f"\nVisibility: {vis_value} ({vis_type})")


@comment.command(name="list")
@click.argument("issue_key")
@click.option("--id", "comment_id", help="Get specific comment by ID")
@click.option("--limit", "-l", type=int, default=50, help="Maximum number of comments")
@click.option("--offset", type=int, default=0, help="Starting index for pagination")
@click.option(
    "--order",
    type=click.Choice(["asc", "desc"]),
    default="desc",
    help="Sort order",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def comment_list(
    ctx,
    issue_key: str,
    comment_id: str,
    limit: int,
    offset: int,
    order: str,
    output: str,
):
    """List comments on an issue."""
    result = _get_comments_impl(
        issue_key=issue_key,
        comment_id=comment_id,
        limit=limit,
        offset=offset,
        order=order,
    )

    if comment_id:
        if output == "json":
            click.echo(format_json(result))
        else:
            click.echo(f"Comment {result['id']} on {issue_key}:\n")
            author = result.get("author", {}).get("displayName", "Unknown")
            created = result.get("created", "N/A")[:16]
            click.echo(f"  Author: {author}")
            click.echo(f"  Created: {created}")

            visibility = result.get("visibility")
            if visibility:
                click.echo(
                    f"  Visibility: {visibility.get('type')} - {visibility.get('value')}"
                )
            else:
                click.echo("  Visibility: Public")

            click.echo()
            body_text = adf_to_text(result.get("body", {}))
            click.echo(f"  {body_text}")
    else:
        if output == "json":
            click.echo(format_json(result))
        else:
            total = result.get("total", 0)
            comments = result.get("comments", [])

            click.echo(f"Comments on {issue_key} ({total} total):\n")

            if not comments:
                click.echo("No comments found.")
            else:
                click.echo(_format_comments_table(comments))

                if len(comments) < total:
                    click.echo(
                        f"\nShowing {len(comments)} of {total}. Use --limit and --offset for more."
                    )


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
@handle_jira_errors
def comment_update(ctx, issue_key: str, comment_id: str, body: str, body_format: str):
    """Update a comment."""
    result = _update_comment_impl(
        issue_key=issue_key,
        comment_id=comment_id,
        body=body,
        body_format=body_format,
    )

    click.echo(f"Comment {result['id']} updated on {issue_key}.\n")
    body_text = adf_to_text(result.get("body", {}))
    click.echo(f"Updated body: {body_text}")


@comment.command(name="delete")
@click.argument("issue_key")
@click.option("--id", "-i", "comment_id", required=True, help="Comment ID to delete")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted")
@click.pass_context
@handle_jira_errors
def comment_delete(ctx, issue_key: str, comment_id: str, yes: bool, dry_run: bool):
    """Delete a comment."""
    result = _delete_comment_impl(
        issue_key=issue_key,
        comment_id=comment_id,
        force=yes,
        dry_run=dry_run,
    )

    if result and result.get("dry_run"):
        click.echo(f"[DRY RUN] Would delete comment {comment_id} from {issue_key}:\n")
        click.echo(f"  Author: {result['author']}")
        click.echo(f"  Date: {result['created']}")
        click.echo(f"  Body: {result['body']}")
        click.echo("\nNo changes made (dry-run mode).")
    elif result:
        click.echo(f"\nDelete comment {comment_id} from {issue_key}?\n")
        click.echo(f"  Author: {result['author']}")
        click.echo(f"  Date: {result['created']}")
        click.echo(f"  Body: {result['body']}")
        click.echo()

        if click.confirm("Are you sure?"):
            client = get_jira_client()
            try:
                client.delete_comment(issue_key, comment_id)
            finally:
                client.close()
            print_success(f"Comment {comment_id} deleted from {issue_key}")
        else:
            click.echo("Deletion cancelled.")
    else:
        print_success(f"Comment {comment_id} deleted from {issue_key}")


# =============================================================================
# Attachment Subgroup
# =============================================================================


@collaborate.group()
def attachment():
    """Manage issue attachments."""
    pass


@attachment.command(name="upload")
@click.argument("issue_key")
@click.option("--file", "-f", "file_path", required=True, help="Path to file")
@click.option("--name", "-n", help="Override filename")
@click.pass_context
@handle_jira_errors
def attachment_upload(ctx, issue_key: str, file_path: str, name: str):
    """Upload an attachment to an issue."""
    result = _upload_attachment_impl(
        issue_key=issue_key,
        file_path=file_path,
        file_name=name,
    )

    if isinstance(result, list) and result:
        filename = result[0].get("filename", "")
        print_success(f"Uploaded {filename} to {issue_key}")
    else:
        print_success(f"Uploaded file to {issue_key}")


@attachment.command(name="list")
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
def attachment_list(ctx, issue_key: str, output: str):
    """List attachments on an issue."""
    attachments = _list_attachments_impl(issue_key)

    if output == "json":
        click.echo(json.dumps(attachments, indent=2))
    else:
        click.echo(f"Attachments for {issue_key}:\n")
        click.echo(_format_attachment_list(attachments))


@attachment.command(name="download")
@click.argument("issue_key")
@click.option("--name", "-n", help="Download by filename")
@click.option("--id", "-i", "attachment_id", help="Download by ID")
@click.option("--all", "-a", "download_all", is_flag=True, help="Download all")
@click.option("--output-dir", "-o", help="Directory to save files")
@click.pass_context
@handle_jira_errors
def attachment_download(
    ctx,
    issue_key: str,
    name: str,
    attachment_id: str,
    download_all: bool,
    output_dir: str,
):
    """Download attachments from an issue."""
    if download_all:
        downloaded = _download_all_attachments_impl(issue_key, output_dir=output_dir)

        if downloaded:
            print_success(f"Downloaded {len(downloaded)} attachment(s):")
            for path in downloaded:
                click.echo(f"  - {path}")
        else:
            print_info("No attachments to download.")
    elif name or attachment_id:
        output_path = _download_attachment_impl(
            issue_key,
            attachment_id=attachment_id,
            attachment_name=name,
            output_dir=output_dir,
        )
        print_success(f"Downloaded: {output_path}")
    else:
        raise click.UsageError("Specify --name, --id, or --all")


# =============================================================================
# Watchers Command
# =============================================================================


@collaborate.command(name="watchers")
@click.argument("issue_key")
@click.option("--add", "-a", "add_user", help="Add watcher")
@click.option("--remove", "-r", "remove_user", help="Remove watcher")
@click.option("--list", "-l", "list_watchers", is_flag=True, help="List watchers")
@click.pass_context
@handle_jira_errors
def collaborate_watchers(
    ctx, issue_key: str, add_user: str, remove_user: str, list_watchers: bool
):
    """Manage watchers on an issue."""
    if add_user:
        _add_watcher_impl(issue_key, add_user)
        print_success(f"Added {add_user} as watcher to {issue_key}")
    elif remove_user:
        _remove_watcher_impl(issue_key, remove_user)
        print_success(f"Removed {remove_user} as watcher from {issue_key}")
    else:
        watchers = _list_watchers_impl(issue_key)
        if not watchers:
            click.echo(f"No watchers on {issue_key}")
        else:
            data = [
                {"Name": w.get("displayName", ""), "Email": w.get("emailAddress", "")}
                for w in watchers
            ]
            click.echo(format_table(data))


# =============================================================================
# Activity Command
# =============================================================================


@collaborate.command(name="activity")
@click.argument("issue_key")
@click.option("--limit", "-l", type=int, default=100, help="Max changelog entries")
@click.option("--offset", type=int, default=0, help="Starting position")
@click.option("--field", "-f", multiple=True, help="Filter by field name")
@click.option(
    "--field-type",
    "-t",
    multiple=True,
    type=click.Choice(["jira", "custom"]),
    help="Filter by field type",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def collaborate_activity(
    ctx,
    issue_key: str,
    limit: int,
    offset: int,
    field: tuple,
    field_type: tuple,
    output: str,
):
    """Get activity feed for an issue."""
    changelog = _get_activity_impl(issue_key, limit=limit, offset=offset)

    changes = _parse_changelog(
        changelog,
        field_filter=list(field) if field else None,
        field_type_filter=list(field_type) if field_type else None,
    )

    if output == "json":
        click.echo(json.dumps(changes, indent=2))
    else:
        filter_desc = ""
        if field:
            filter_desc += f" (fields: {', '.join(field)})"
        if field_type:
            filter_desc += f" (types: {', '.join(field_type)})"

        click.echo(f"Activity for {issue_key}{filter_desc}:\n")
        click.echo(_display_activity_table(changes))

        total = changelog.get("total", 0)
        if total > limit:
            click.echo(f"\nUse --offset {offset + limit} to see more (total: {total}).")


# =============================================================================
# Notify Command
# =============================================================================


@collaborate.command(name="notify")
@click.argument("issue_key")
@click.option("--user", "-u", multiple=True, help="Notify user by account ID")
@click.option("--group", "-g", multiple=True, help="Notify group")
@click.option("--watchers", is_flag=True, help="Notify watchers")
@click.option("--assignee", is_flag=True, help="Notify assignee")
@click.option("--reporter", is_flag=True, help="Notify reporter")
@click.option("--voters", is_flag=True, help="Notify voters")
@click.option("--subject", "-s", help="Notification subject")
@click.option("--body", "-b", help="Notification body")
@click.option("--dry-run", is_flag=True, help="Preview without sending")
@click.pass_context
@handle_jira_errors
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
    """Send a notification about an issue."""
    if not any([watchers, assignee, reporter, voters, user, group]):
        raise click.UsageError(
            "Must specify at least one recipient (--watchers, --assignee, --reporter, --voters, --user, or --group)"
        )

    subject = subject or f"Issue Update: {issue_key}"
    body = body or "This is a notification about this issue."

    result = _send_notification_impl(
        issue_key=issue_key,
        subject=subject,
        body=body,
        watchers=watchers,
        assignee=assignee,
        reporter=reporter,
        voters=voters,
        users=list(user) if user else None,
        groups=list(group) if group else None,
        dry_run=dry_run,
    )

    if result:
        click.echo(f"[DRY RUN] Would send notification for {issue_key}:\n")
        click.echo(f"Subject: {result['subject']}")
        click.echo(f"Body: {result['body']}\n")
        click.echo("Recipients:")
        recipients = result["recipients"]
        if recipients["watchers"]:
            click.echo("  - Watchers")
        if recipients["assignee"]:
            click.echo("  - Assignee")
        if recipients["reporter"]:
            click.echo("  - Reporter")
        if recipients["voters"]:
            click.echo("  - Voters")
        if recipients["users"]:
            click.echo(f"  - {len(recipients['users'])} specific user(s)")
        if recipients["groups"]:
            for grp in recipients["groups"]:
                click.echo(f"  - Group: {grp}")
        click.echo("\nNo notification sent (dry-run mode).")
    else:
        click.echo(f"Notification sent for {issue_key}:\n")
        click.echo(f"Subject: {subject}")
        click.echo(f"Body: {body}\n")
        click.echo("Recipients:")
        if watchers:
            click.echo("  - Watchers")
        if assignee:
            click.echo("  - Assignee")
        if reporter:
            click.echo("  - Reporter")
        if voters:
            click.echo("  - Voters")
        if user:
            click.echo(f"  - {len(user)} specific user(s)")
        if group:
            for grp in group:
                click.echo(f"  - Group: {grp}")


# =============================================================================
# Update Fields Command
# =============================================================================


@collaborate.command(name="update-fields")
@click.argument("issue_key")
@click.option("--fields", "-f", required=True, help="Custom fields as JSON string")
@click.pass_context
@handle_jira_errors
def collaborate_update_fields(ctx, issue_key: str, fields: str):
    """Update custom fields on an issue."""
    _update_custom_fields_impl(issue_key=issue_key, fields_json=fields)
    print_success(f"Updated custom fields on {issue_key}")
