---
name: "jira-collaboration"
description: |
  Collaborate on issues: add/edit comments, share attachments, notify users,
  track activity. For team communication and coordination on JIRA issues.
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
keywords:
  - comments
  - attachments
  - notifications
  - watchers
  - activity history
use_when:
  - "starting work on an issue (add comment)"
  - "sharing screenshots or error logs (upload attachment)"
  - "progress is blocked and needs escalation (comment + notify)"
  - "handing off work to teammate (comment + reassign + notify)"
  - "reviewing what changed on an issue (get activity)"
  - "need to add team visibility (manage watchers)"
---

# jira-collaborate

Collaboration features for JIRA issues - comments, attachments, watchers, and notifications.

## When to use this skill

Use this skill when you need to:
- Add, update, or delete comments on issues
- Upload or download attachments
- Manage watchers (add/remove)
- Send notifications to users or groups
- View issue activity and changelog

## What this skill does

**IMPORTANT:** Always use the `jira-as` CLI. Never run Python scripts directly.

1. **Comments**: Add/edit/delete comments with rich text support
2. **Attachments**: Upload and download files
3. **Watchers**: Manage who tracks the issue
4. **Notifications**: Send targeted notifications
5. **Activity History**: View issue changelog
6. **Custom Fields**: Update custom field values

## Available Scripts

### Comments
| Script | Description |
|--------|-------------|
| `add_comment.py` | Add comment with visibility controls |
| `update_comment.py` | Update existing comment |
| `delete_comment.py` | Delete comment (with confirmation) |
| `get_comments.py` | List and search comments |

### Attachments
| Script | Description |
|--------|-------------|
| `upload_attachment.py` | Upload file to issue |
| `download_attachment.py` | Download or list attachments |

### Notifications & Activity
| Script | Description |
|--------|-------------|
| `send_notification.py` | Send notifications to users/groups |
| `get_activity.py` | View issue changelog |

### Watchers & Fields
| Script | Description |
|--------|-------------|
| `manage_watchers.py` | Add/remove watchers |
| `update_custom_fields.py` | Update custom fields |

## Quick Start Examples

```bash
# Add a comment
jira-as collaborate comment add PROJ-123 --body "Starting work on this now"

# Rich text comment
jira-as collaborate comment add PROJ-123 --body "**Bold** text" --format markdown

# Internal comment (role-restricted)
jira-as collaborate comment add PROJ-123 --body "Internal note" --visibility-role Administrators

# List comments
jira-as collaborate comment list PROJ-123
jira-as collaborate comment list PROJ-123 --limit 10 --order asc

# Update a comment (requires comment ID)
jira-as collaborate comment update PROJ-123 --id 10001 --body "Updated text"

# Delete a comment
jira-as collaborate comment delete PROJ-123 --id 10001 --yes

# Upload attachment
jira-as collaborate attachment upload PROJ-123 --file screenshot.png

# Download attachment (use attachment ID from issue details)
jira-as collaborate attachment download PROJ-123 12345 --output ./downloads/

# List watchers
jira-as collaborate watchers PROJ-123 --list

# Add watcher
jira-as collaborate watchers PROJ-123 --add user@example.com

# Remove watcher
jira-as collaborate watchers PROJ-123 --remove user@example.com

# Send notification to watchers
jira-as collaborate notify PROJ-123 --watchers --subject "Update" --body "Issue resolved"

# Send notification to specific users (use account IDs)
jira-as collaborate notify PROJ-123 --user 5b10a2844c20165700ede21g --subject "Review needed"

# Send notification to assignee and reporter
jira-as collaborate notify PROJ-123 --assignee --reporter --subject "Please review"

# Preview notification without sending
jira-as collaborate notify PROJ-123 --watchers --dry-run

# View activity history
jira-as collaborate activity PROJ-123

# View activity with filters
jira-as collaborate activity PROJ-123 --field status --field assignee --output table
jira-as collaborate activity PROJ-123 --field-type custom --limit 10
```

## Common Options

All scripts support:

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show detailed help |

For script-specific options, use `--help` on any script:
```bash
jira-as collaborate comment add --help
jira-as collaborate notify --help
```

See [references/SCRIPT_OPTIONS.md](references/SCRIPT_OPTIONS.md) for full option matrix.

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error (validation, API error, network issue) |

## Troubleshooting

| Error | Solution |
|-------|----------|
| "Comment not found" | Verify comment ID with `get_comments.py` |
| "Attachment not found" | Use `--list` to see available attachments |
| "Permission denied" | Check visibility role/group permissions |
| "User not found" | Use account ID (not email) for watchers |
| "Notification not received" | Use `--dry-run` to verify recipients |

For debug mode: `export JIRA_DEBUG=1`

## Documentation Structure

**Getting Started:** [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) - First 5 minutes

**Common Scenarios:** [docs/scenarios/](docs/scenarios/) - Workflow examples
- [Starting work](docs/scenarios/starting_work.md)
- [Progress update](docs/scenarios/progress_update.md)
- [Escalation](docs/scenarios/blocker_escalation.md)
- [Handoff](docs/scenarios/handoff.md)
- [Sharing evidence](docs/scenarios/sharing_evidence.md)

**Reference:** [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) - Commands and JQL

**Templates:** [docs/TEMPLATES.md](docs/TEMPLATES.md) - Copy-paste ready

**Advanced Topics:** [docs/DEEP_DIVES/](docs/DEEP_DIVES/) - Deep dive guides

**Format Reference:** [references/adf_guide.md](references/adf_guide.md) - Markdown to ADF

## Related Skills

- **jira-issue**: For creating and updating issue fields
- **jira-lifecycle**: For transitioning with comments
- **jira-search**: For finding issues to collaborate on
