---
name: "jira-issue-management"
description: "Core CRUD operations for JIRA issues - create, read, update, delete tickets. Use when creating bugs, tasks, stories, retrieving issue details, updating fields, or deleting issues."
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# jira-issue

Core CRUD operations for JIRA issues - create, read, update, and delete tickets.

## When to Use This Skill

Triggers: User asks to...
- Create a new JIRA issue (bug, task, story, epic)
- Retrieve issue details or view issue information
- Update issue fields (summary, description, priority, assignee, labels)
- Delete an issue

## Available Commands

This skill provides the following commands via the `jira issue` CLI:

- `jira issue create`: Create new issues
- `jira issue get`: Retrieve issue details
- `jira issue update`: Modify issue fields
- `jira issue delete`: Remove issues

All commands support `--help` for full option documentation.

### Global Options

All commands inherit global options from the parent `jira` command:
- `--profile, -p`: Select JIRA profile (e.g., `jira --profile dev issue get PROJ-123`)
- `--output, -o`: Output format for `get` and `create` commands (text, json)

## Templates

Pre-configured templates for common issue types:
- `bug_template.json` - Bug report template
- `task_template.json` - Task template
- `story_template.json` - User story template

## Common Patterns

### Create Issues

```bash
# Basic issue creation
jira issue create --project PROJ --type Bug --summary "Login fails on mobile"

# With agile fields (--points is an alias for --story-points)
jira issue create --project PROJ --type Story --summary "User login" \
  --epic PROJ-100 --story-points 5

# With relationships and time estimate
jira issue create --project PROJ --type Task --summary "Setup database" \
  --blocks PROJ-123 --estimate "2d"

# With labels and components
jira issue create --project PROJ --type Task --summary "Setup CI pipeline" \
  --labels "backend,infrastructure" --components "Build,DevOps"

# With custom fields (JSON format)
jira issue create --project PROJ --type Bug --summary "Critical bug" \
  --custom-fields '{"customfield_10050": "production"}'

# Assign to sprint
jira issue create --project PROJ --type Story --summary "Feature X" \
  --sprint 42

# Create without project context defaults
jira issue create --project PROJ --type Bug --summary "Bug" --no-defaults
```

### Retrieve Issues

```bash
# Basic retrieval
jira issue get PROJ-123

# With full details
jira issue get PROJ-123 --detailed --show-links --show-time

# Retrieve specific fields only
jira issue get PROJ-123 --fields "summary,status,priority,assignee"

# JSON output for scripting
jira issue get PROJ-123 --output json
```

**Note:** Using `--show-links` or `--show-time` automatically enables detailed view.

### Update Issues

```bash
# Update priority and assignee
jira issue update PROJ-123 --priority Critical --assignee self

# Update without notifications
jira issue update PROJ-123 --summary "Updated title" --no-notify

# Unassign issue (accepts "none" or "unassigned")
jira issue update PROJ-123 --assignee none

# Update labels and components (replaces existing)
jira issue update PROJ-123 --labels "urgent,reviewed" --components "API"

# Update custom fields
jira issue update PROJ-123 --custom-fields '{"customfield_10050": "staging"}'
```

**Assignee special values:**
- `self`: Assigns to the current authenticated user
- `none` or `unassigned`: Removes the assignee

### Delete Issues

```bash
# Delete with confirmation
jira issue delete PROJ-456

# Force delete (no prompt)
jira issue delete PROJ-456 --force
```

## Shell Completion

To enable shell completion for the `jira` CLI, add the appropriate command to your shell's configuration file (e.g., `.bashrc`, `.zshrc`, `config.fish`).

**Bash:**
```bash
eval "$(_JIRA_COMPLETE=bash_source jira)"
```

**Zsh:**
```bash
eval "$(_JIRA_COMPLETE=zsh_source jira)"
```

**Fish:**
```bash
_JIRA_COMPLETE=fish_source jira | source
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

Requires JIRA credentials via environment variables (`JIRA_SITE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`).

## Related Resources

Resources in the skill directory (`plugins/jira-assistant-skills/skills/jira-issue/`):
- `docs/BEST_PRACTICES.md` - Issue content and metadata guidance
- `references/field_formats.md` - ADF and field format details
- `references/api_reference.md` - REST API endpoints

## Related Skills

- **jira-lifecycle**: Workflow transitions and status changes
- **jira-search**: JQL queries for finding issues
- **jira-collaborate**: Comments, attachments, watchers
- **jira-agile**: Sprint and epic management
- **jira-relationships**: Issue linking and dependencies
- **jira-time**: Time tracking and worklogs
