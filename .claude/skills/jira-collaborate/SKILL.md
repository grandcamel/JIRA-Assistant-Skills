---
name: "JIRA Collaboration"
description: "Collaboration features for JIRA issues - comments, attachments, watchers, notifications. Use when adding comments, uploading/downloading attachments, managing watchers, or sending notifications."
---

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
   - Download attachments by ID or filename
   - Download all attachments at once
   - List attachments on issues with metadata

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
- `download_attachment.py` - Download attachments from issue
  - `--list` - List all attachments with ID, filename, size, type, author
  - `--id <ID>` - Download specific attachment by ID
  - `--name <filename>` - Download specific attachment by filename
  - `--all` - Download all attachments from the issue
  - `--output-dir <path>` - Directory to save downloaded files
  - `--output text|json` - Output format for `--list` (default: text)

### Watchers & Custom Fields
- `manage_watchers.py` - Add/remove watchers
- `update_custom_fields.py` - Update custom fields

## Common Options

All scripts support these common options:

| Option | Description |
|--------|-------------|
| `--profile <name>` | JIRA profile to use (default: from config) |
| `--help`, `-h` | Show help message and exit |

### Comment Scripts
| Option | Description |
|--------|-------------|
| `--format text\|markdown\|adf` | Input format for comment body |
| `--visibility-role <role>` | Restrict visibility to role (e.g., Administrators) |
| `--visibility-group <group>` | Restrict visibility to group |

### Notification Scripts
| Option | Description |
|--------|-------------|
| `--dry-run` | Preview recipients without sending |
| `--watchers` | Notify all watchers |
| `--assignee` | Notify assignee |
| `--reporter` | Notify reporter |
| `--users <ids>` | Notify specific users by account ID |
| `--groups <names>` | Notify specific groups |

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

# Attachments - Upload
python upload_attachment.py PROJ-123 --file screenshot.png

# Attachments - Download
python download_attachment.py PROJ-123 --list
python download_attachment.py PROJ-123 --list --output json
python download_attachment.py PROJ-123 --name screenshot.png
python download_attachment.py PROJ-123 --id 12345
python download_attachment.py PROJ-123 --all --output-dir ./downloads

# Watchers
python manage_watchers.py PROJ-123 --add user@example.com

# Custom Fields
python update_custom_fields.py PROJ-123 --field customfield_10001 --value "Production"
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error (validation, API error, network issue) |

Error details are printed to stderr with troubleshooting hints when available.

## Troubleshooting

### Common Issues

**"Comment not found" error**
- Verify the comment ID exists on the issue using `get_comments.py`
- Comment IDs are numeric (e.g., 10001)
- Comments may have been deleted by another user

**"Attachment not found" error**
- Use `download_attachment.py PROJ-123 --list` to see available attachments
- Verify the attachment ID or filename is correct
- Filenames are case-sensitive

**"Permission denied" when adding internal comments**
- Internal comments require appropriate JIRA permissions
- Verify the visibility role/group exists in your JIRA instance
- Check that your user has the "Browse projects" permission for internal comments

**"User not found" when adding watchers**
- Use the account ID (not email) for programmatic access
- Verify the user has access to the project
- External users may not be able to watch issues

**Notification not received**
- Check notification scheme settings in JIRA
- Verify recipients have email notifications enabled
- Use `--dry-run` to preview recipient list before sending

**Large file upload fails**
- JIRA Cloud has a 10MB attachment limit by default
- Check your instance's attachment settings
- Consider compressing files before upload

### Debug Mode

For additional debugging information, set the environment variable:
```bash
export JIRA_DEBUG=1
```

## Configuration

Uses shared configuration from `.claude/settings.json` and `.claude/settings.local.json`.
Requires JIRA credentials via environment variables or settings files.

## Related skills

- **jira-issue**: For creating and updating issue fields
- **jira-lifecycle**: For transitioning with comments
- **jira-search**: For finding issues to collaborate on
