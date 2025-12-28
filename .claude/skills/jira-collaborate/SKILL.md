---
name: "JIRA Collaboration"
description: |
  Collaborate on issues: add/edit comments, share attachments, notify users,
  track activity. For team communication and coordination on JIRA issues.
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
python add_comment.py PROJ-123 --body "Starting work on this now"

# Rich text comment
python add_comment.py PROJ-123 --body "**Bold** text" --format markdown

# Internal comment (role-restricted)
python add_comment.py PROJ-123 --body "Internal note" --visibility-role Administrators

# Upload attachment
python upload_attachment.py PROJ-123 --file screenshot.png

# List attachments
python download_attachment.py PROJ-123 --list

# Download all attachments
python download_attachment.py PROJ-123 --all --output-dir ./downloads

# Add watcher
python manage_watchers.py PROJ-123 --add user@example.com

# Send notification (preview first)
python send_notification.py PROJ-123 --watchers --dry-run
python send_notification.py PROJ-123 --watchers --subject "Update" --body "Issue resolved"

# View activity history
python get_activity.py PROJ-123 --format table
```

## Common Options

All scripts support:

| Option | Description |
|--------|-------------|
| `--profile <name>` | JIRA profile to use |
| `--help`, `-h` | Show detailed help |

For script-specific options, use `--help` on any script:
```bash
python add_comment.py --help
python send_notification.py --help
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
