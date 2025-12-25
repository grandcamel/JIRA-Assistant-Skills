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
   - Update existing comments
   - Delete comments
   - View comment history

2. **Attachments**: Handle file attachments
   - Upload files to issues
   - Download attachments
   - List attachments on issues

3. **Watchers**: Manage issue watchers
   - Add watchers to issues
   - Remove watchers
   - List current watchers

4. **Custom Fields**: Update custom field values
   - Set custom field values by type
   - Handle different custom field formats
   - Update multiple custom fields at once

## Available scripts

- `add_comment.py` - Add comment to issue
- `update_comment.py` - Update existing comment
- `delete_comment.py` - Delete comment
- `upload_attachment.py` - Upload file to issue
- `download_attachment.py` - Download attachment
- `manage_watchers.py` - Add/remove watchers
- `update_custom_fields.py` - Update custom fields

## Examples

```bash
# Add comment
python add_comment.py PROJ-123 --body "Working on this now"

# Add comment with Markdown
python add_comment.py PROJ-123 --body "## Update\nFixed the issue" --format markdown

# Upload attachment
python upload_attachment.py PROJ-123 --file screenshot.png

# Download attachment
python download_attachment.py PROJ-123 --attachment-id 10001 --output downloaded.png

# Add watcher
python manage_watchers.py PROJ-123 --add user@example.com

# Update custom field
python update_custom_fields.py PROJ-123 --field customfield_10001 --value "Production"
```

## Configuration

Uses shared configuration from `.claude/settings.json` and `.claude/settings.local.json`.
Requires JIRA credentials via environment variables or settings files.

## Related skills

- **jira-issue**: For creating and updating issue fields
- **jira-lifecycle**: For transitioning with comments
- **jira-search**: For finding issues to collaborate on
