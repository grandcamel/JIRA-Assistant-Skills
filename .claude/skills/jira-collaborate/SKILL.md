# jira-collaborate

Collaboration features for JIRA issues - comments, attachments, watchers, and custom fields.

## When to use this skill

Use this skill when you need to:
- Add, update, or delete comments on issues
- Upload or download attachments
- Manage watchers (add/remove)
- Update custom fields
- Collaborate on issues with team members

## What this skill does

This skill provides collaboration and communication operations:

1. **Comments**: Manage issue comments
   - Add comments with rich text (ADF) or Markdown
   - Add internal comments (visible to specific roles/groups)
   - Update existing comments
   - Delete comments with confirmation
   - View and search comment history

2. **Notifications**: Send notifications to users
   - Notify watchers, assignees, reporters, voters
   - Send to specific users or groups
   - Custom subject and body messages
   - Dry-run mode to preview recipients

3. **Activity History**: View issue changelog
   - Track all field changes over time
   - Filter by change type (status, assignee, priority, etc.)
   - See who made changes and when
   - Export activity history

4. **Attachments**: Handle file attachments
   - Upload files to issues
   - Download attachments
   - List attachments on issues

5. **Watchers**: Manage issue watchers
   - Add watchers to issues
   - Remove watchers
   - List current watchers

6. **Custom Fields**: Update custom field values
   - Set custom field values by type
   - Handle different custom field formats
   - Update multiple custom fields at once

## Available scripts

### Comments
- `add_comment.py` - Add comment to issue with visibility controls
- `update_comment.py` - Update existing comment
- `delete_comment.py` - Delete comment with confirmation/dry-run
- `get_comments.py` - List and search comments

### Notifications & Activity
- `send_notification.py` - Send notifications to users/groups
- `get_activity.py` - View issue changelog and field changes

### Attachments
- `upload_attachment.py` - Upload file to issue
- `download_attachment.py` - Download attachment

### Watchers & Custom Fields
- `manage_watchers.py` - Add/remove watchers
- `update_custom_fields.py` - Update custom fields

## Examples

```bash
# Comments
python add_comment.py PROJ-123 --body "Working on this now"
python add_comment.py PROJ-123 --body "## Update\nFixed the issue" --format markdown
python add_comment.py PROJ-123 --body "Internal note" --visibility-role Administrators
python update_comment.py PROJ-123 --comment-id 10001 --body "Updated comment"
python delete_comment.py PROJ-123 --comment-id 10001 --dry-run
python get_comments.py PROJ-123 --format table

# Notifications
python send_notification.py PROJ-123 --watchers --subject "Update" --body "Issue updated"
python send_notification.py PROJ-123 --users accountId1 accountId2 --body "Please review"
python send_notification.py PROJ-123 --assignee --reporter --dry-run

# Activity History
python get_activity.py PROJ-123 --format table
python get_activity.py PROJ-123 --filter status --format json

# Attachments
python upload_attachment.py PROJ-123 --file screenshot.png
python download_attachment.py PROJ-123 --attachment-id 10001 --output downloaded.png

# Watchers
python manage_watchers.py PROJ-123 --add user@example.com

# Custom Fields
python update_custom_fields.py PROJ-123 --field customfield_10001 --value "Production"
```

## Configuration

Uses shared configuration from `.claude/settings.json` and `.claude/settings.local.json`.
Requires JIRA credentials via environment variables or settings files.

## Related skills

- **jira-issue**: For creating and updating issue fields
- **jira-lifecycle**: For transitioning with comments
- **jira-search**: For finding issues to collaborate on
