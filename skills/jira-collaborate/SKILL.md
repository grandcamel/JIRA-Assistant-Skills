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

## Risk Levels

| Operation | Risk | Notes |
|-----------|------|-------|
| List comments/attachments | `-` | Read-only |
| List watchers | `-` | Read-only |
| View activity history | `-` | Read-only |
| Add comment | `-` | Easily reversible (can delete) |
| Upload attachment | `-` | Easily reversible (can delete) |
| Add watcher | `-` | Can remove watcher |
| Send notification | `-` | Cannot unsend but harmless |
| Update comment | `!` | Previous text lost |
| Update custom fields | `!` | Can be undone via edit |
| Remove watcher | `!` | Can re-add |
| Delete comment | `!!` | Comment text lost |
| Delete attachment | `!!` | File lost, must re-upload |

**Risk Legend**: `-` Safe, read-only | `!` Caution, modifiable | `!!` Warning, destructive but recoverable | `!!!` Danger, irreversible

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

## Available Commands

### Comments
| Command | Description |
|---------|-------------|
| `jira-as collaborate comment add` | Add comment with visibility controls |
| `jira-as collaborate comment update` | Update existing comment |
| `jira-as collaborate comment delete` | Delete comment (with confirmation) |
| `jira-as collaborate comment list` | List and search comments |

### Attachments
| Command | Description |
|---------|-------------|
| `jira-as collaborate attachment list` | List attachments on issue |
| `jira-as collaborate attachment upload` | Upload file to issue |
| `jira-as collaborate attachment download` | Download attachments |

### Notifications & Activity
| Command | Description |
|---------|-------------|
| `jira-as collaborate notify` | Send notifications to users/groups |
| `jira-as collaborate activity` | View issue changelog |

### Watchers & Fields
| Command | Description |
|---------|-------------|
| `jira-as collaborate watchers` | Add/remove/list watchers |
| `jira-as collaborate update-fields` | Update custom fields |

All commands support `--help` for full documentation.

## Quick Start Examples

```bash
# Add a comment
jira-as collaborate comment add PROJ-123 --body "Starting work on this now"

# Rich text comment (--format supports: markdown, wiki, adf)
jira-as collaborate comment add PROJ-123 --body "**Bold** text" --format markdown

# Internal comment (role-restricted)
jira-as collaborate comment add PROJ-123 --body "Internal note" --visibility-role Administrators

# Internal comment (group-restricted)
jira-as collaborate comment add PROJ-123 --body "Team only" --visibility-group jira-developers

# List comments (supports --order asc or desc)
jira-as collaborate comment list PROJ-123
jira-as collaborate comment list PROJ-123 -l 10 --order desc

# Get specific comment by ID
jira-as collaborate comment list PROJ-123 --id 10001

# List comments with pagination
jira-as collaborate comment list PROJ-123 -l 10 --offset 20

# Update a comment (requires comment ID)
jira-as collaborate comment update PROJ-123 --id 10001 --body "Updated text"

# Delete a comment (preview first)
jira-as collaborate comment delete PROJ-123 --id 10001 --dry-run

# Delete a comment (confirmed)
jira-as collaborate comment delete PROJ-123 --id 10001 --yes

# Upload attachment (-f is short for --file)
jira-as collaborate attachment upload PROJ-123 -f screenshot.png
jira-as collaborate attachment upload PROJ-123 --file screenshot.png

# Upload attachment with custom name (-n is short for --name)
jira-as collaborate attachment upload PROJ-123 -f screenshot.png -n evidence-2024.png

# List attachments on issue
jira-as collaborate attachment list PROJ-123

# Download attachment by ID (-o is short for --output-dir)
jira-as collaborate attachment download PROJ-123 --id 12345 -o ./downloads/

# Download attachment by filename
jira-as collaborate attachment download PROJ-123 --name error.log -o ./downloads/

# Download all attachments from issue
jira-as collaborate attachment download PROJ-123 --all -o ./backups/

# List watchers (-l is short for --list)
jira-as collaborate watchers PROJ-123 -l
jira-as collaborate watchers PROJ-123 --list

# Add watcher (-a is short for --add)
jira-as collaborate watchers PROJ-123 -a user@example.com

# Remove watcher (-r is short for --remove)
jira-as collaborate watchers PROJ-123 -r user@example.com

# Send notification to watchers
jira-as collaborate notify PROJ-123 --watchers --subject "Update" --body "Issue resolved"

# Send notification to voters
jira-as collaborate notify PROJ-123 --voters --subject "Vote counted"

# Send notification to a group
jira-as collaborate notify PROJ-123 --group developers --subject "Team update"

# Send notification to specific users (use account IDs or emails)
jira-as collaborate notify PROJ-123 --user user@example.com --subject "Review needed"

# Send notification to assignee and reporter
jira-as collaborate notify PROJ-123 --assignee --reporter --subject "Please review"

# Preview notification without sending
jira-as collaborate notify PROJ-123 --watchers --dry-run

# View activity history
jira-as collaborate activity PROJ-123

# View activity with filters
jira-as collaborate activity PROJ-123 --field status --field assignee --output table
jira-as collaborate activity PROJ-123 --field-type custom --limit 10

# View activity with pagination
jira-as collaborate activity PROJ-123 --limit 10 --offset 20
```

## Common Options

All commands support:

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show detailed help |

For command-specific options, use `--help` on any command:
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
| "Comment not found" | Verify comment ID with `jira-as collaborate comment list ISSUE-KEY` |
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
