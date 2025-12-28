---
name: "JIRA Issue Management"
description: "Core CRUD operations for JIRA issues - create, read, update, delete tickets. Use when creating bugs, tasks, stories, retrieving issue details, updating fields, or deleting issues."
---

# jira-issue

Core CRUD operations for JIRA issues - create, read, update, and delete tickets.

## When to Use This Skill

Triggers: User asks to...
- Create a new JIRA issue (bug, task, story, epic)
- Retrieve issue details or view issue information
- Update issue fields (summary, description, priority, assignee, labels)
- Delete an issue

## Available Scripts

| Script | Purpose | Key Options |
|--------|---------|-------------|
| `create_issue.py` | Create new issues | `--project`, `--type`, `--summary` (required) |
| `get_issue.py` | Retrieve issue details | `--detailed`, `--show-links`, `--show-time` |
| `update_issue.py` | Modify issue fields | `--summary`, `--priority`, `--assignee` |
| `delete_issue.py` | Remove issues | `--force` (skip confirmation) |

All scripts support `--help` for full option documentation, `--profile` for JIRA instance selection, and `--output json` for programmatic use.

## Templates

Pre-configured templates for common issue types:
- `bug_template.json` - Bug report template
- `task_template.json` - Task template
- `story_template.json` - User story template

## Common Patterns

### Create Issues

```bash
# Basic issue creation
python create_issue.py --project PROJ --type Bug --summary "Login fails on mobile"

# With agile fields
python create_issue.py --project PROJ --type Story --summary "User login" \
  --epic PROJ-100 --story-points 5

# With relationships
python create_issue.py --project PROJ --type Task --summary "Setup database" \
  --blocks PROJ-123 --estimate "2d"
```

### Retrieve Issues

```bash
# Basic retrieval
python get_issue.py PROJ-123

# With full details
python get_issue.py PROJ-123 --detailed --show-links --show-time

# JSON output for scripting
python get_issue.py PROJ-123 --output json
```

### Update Issues

```bash
# Update priority and assignee
python update_issue.py PROJ-123 --priority Critical --assignee self

# Update without notifications
python update_issue.py PROJ-123 --summary "Updated title" --no-notify

# Unassign issue
python update_issue.py PROJ-123 --assignee none
```

### Delete Issues

```bash
# Delete with confirmation
python delete_issue.py PROJ-456

# Force delete (no prompt)
python delete_issue.py PROJ-456 --force
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Error (see error message) |

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid credentials | Verify `JIRA_API_TOKEN` and `JIRA_EMAIL` |
| 403 Forbidden | No permission | Check project permissions with JIRA admin |
| 404 Not Found | Issue doesn't exist | Verify issue key format (PROJ-123) |
| Invalid issue type | Type not in project | Check available types for target project |
| Epic/Sprint errors | Agile fields misconfigured | Verify settings.json agile field IDs |

For credential setup, generate tokens at: `https://id.atlassian.com/manage-profile/security/api-tokens`

## Configuration

Uses shared configuration from `.claude/settings.json` and `.claude/settings.local.json`.
Requires JIRA credentials via environment variables or settings files.

## Related Resources

- [Best Practices Guide](docs/BEST_PRACTICES.md) - Issue content and metadata guidance
- [Field Formats Reference](references/field_formats.md) - ADF and field format details
- [API Reference](references/api_reference.md) - REST API endpoints

## Related Skills

- **jira-lifecycle**: Workflow transitions and status changes
- **jira-search**: JQL queries for finding issues
- **jira-collaborate**: Comments, attachments, watchers
- **jira-agile**: Sprint and epic management
- **jira-relationships**: Issue linking and dependencies
- **jira-time**: Time tracking and worklogs
