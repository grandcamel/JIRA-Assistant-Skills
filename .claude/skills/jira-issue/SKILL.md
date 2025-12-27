---
name: "JIRA Issue Management"
description: "Core CRUD operations for JIRA issues - create, read, update, delete tickets. Use when creating bugs, tasks, stories, retrieving issue details, updating fields, or deleting issues."
---

# jira-issue

Core CRUD operations for JIRA issues - create, read, update, and delete tickets.

## When to use this skill

Use this skill when you need to:
- Create new JIRA issues (bugs, tasks, stories, etc.)
- Retrieve details about existing issues
- Update issue fields (summary, description, priority, labels, etc.)
- Delete issues
- View issue information in a readable format

## What this skill does

This skill provides fundamental issue management operations:

1. **Create Issues**: Create new JIRA tickets with customizable fields including:
   - Issue type (Bug, Task, Story, etc.)
   - Summary and description (supports Markdown via ADF conversion)
   - Priority, assignee, labels
   - Custom fields
   - Template-based creation for common issue types
   - Agile fields (epic, sprint, story points)
   - Issue links (blocks, relates to)
   - Time estimates

2. **Get Issues**: Retrieve and display issue details including:
   - All standard fields (summary, status, assignee, etc.)
   - Custom fields
   - Formatted output (detailed or summary view)
   - Issue links and relationships
   - Time tracking information
   - JSON export option

3. **Update Issues**: Modify existing issue fields:
   - Change summary, description, priority
   - Update assignee, labels, components
   - Set custom field values
   - Optional notification control

4. **Delete Issues**: Remove issues with confirmation prompts

## Available scripts

- `create_issue.py` - Create new JIRA issues
- `get_issue.py` - Retrieve and display issue details
- `update_issue.py` - Update issue fields
- `delete_issue.py` - Delete issues

## Templates

Pre-configured templates for common issue types:
- `bug_template.json` - Bug report template
- `task_template.json` - Task template
- `story_template.json` - User story template

## Common Options

All scripts support these common options:

| Option | Description |
|--------|-------------|
| `--profile` | JIRA profile to use (default: from config) |
| `--output, -o` | Output format: `text` (default) or `json` |
| `--help` | Show help message and exit |

## CLI Options by Script

### create_issue.py

| Option | Short | Description |
|--------|-------|-------------|
| `--project` | `-p` | **Required.** Project key (e.g., PROJ, DEV) |
| `--type` | `-t` | **Required.** Issue type (Bug, Task, Story, etc.) |
| `--summary` | `-s` | **Required.** Issue summary (title) |
| `--description` | `-d` | Issue description (supports markdown) |
| `--priority` | | Priority (Highest, High, Medium, Low, Lowest) |
| `--assignee` | `-a` | Assignee (account ID, email, or "self") |
| `--labels` | `-l` | Comma-separated labels |
| `--components` | `-c` | Comma-separated component names |
| `--template` | | Use a predefined template: bug, task, story |
| `--custom-fields` | | Custom fields as JSON string |
| `--epic` | `-e` | Epic key to link this issue to (e.g., PROJ-100) |
| `--sprint` | | Sprint ID to add this issue to |
| `--story-points` | `--points` | Story point estimate (float) |
| `--blocks` | | Comma-separated issue keys this issue blocks |
| `--relates-to` | | Comma-separated issue keys this issue relates to |
| `--estimate` | | Original time estimate (e.g., 2d, 4h, 1w) |

### get_issue.py

| Option | Short | Description |
|--------|-------|-------------|
| `issue_key` | | **Required.** Issue key (e.g., PROJ-123) |
| `--fields` | `-f` | Comma-separated list of fields to retrieve |
| `--detailed` | `-d` | Show detailed information including description |
| `--show-links` | `-l` | Show issue links (blocks, relates to, etc.) |
| `--show-time` | `-t` | Show time tracking information |

### update_issue.py

| Option | Short | Description |
|--------|-------|-------------|
| `issue_key` | | **Required.** Issue key (e.g., PROJ-123) |
| `--summary` | `-s` | New summary (title) |
| `--description` | `-d` | New description (supports markdown) |
| `--priority` | | New priority (Highest, High, Medium, Low, Lowest) |
| `--assignee` | `-a` | New assignee (account ID, email, "self", or "none") |
| `--labels` | `-l` | Comma-separated labels (replaces existing) |
| `--components` | `-c` | Comma-separated component names (replaces existing) |
| `--custom-fields` | | Custom fields as JSON string |
| `--no-notify` | | Do not send notifications to watchers |

### delete_issue.py

| Option | Short | Description |
|--------|-------|-------------|
| `issue_key` | | **Required.** Issue key (e.g., PROJ-123) |
| `--force` | `-f` | Skip confirmation prompt |

## Examples

```bash
# Create a bug
python create_issue.py --project PROJ --type Bug --summary "Login fails on mobile" --priority High

# Create an issue assigned to yourself
python create_issue.py --project PROJ --type Task --summary "Review PR" --assignee self

# Create a story with agile fields
python create_issue.py --project PROJ --type Story --summary "User login" --epic PROJ-100 --story-points 5

# Create a task that blocks another issue
python create_issue.py --project PROJ --type Task --summary "Setup database" --blocks PROJ-123

# Create a task with related issues
python create_issue.py --project PROJ --type Task --summary "Refactor auth" --relates-to PROJ-456,PROJ-789

# Create a task with time estimate
python create_issue.py --project PROJ --type Task --summary "Write tests" --estimate "2d"

# Create a task in a specific sprint
python create_issue.py --project PROJ --type Task --summary "Sprint work" --sprint 42

# Get issue details
python get_issue.py PROJ-123

# Get issue with links and time tracking
python get_issue.py PROJ-123 --show-links --show-time

# Get issue as JSON
python get_issue.py PROJ-123 --output json

# Update issue priority and assignee
python update_issue.py PROJ-123 --priority Critical --assignee self

# Unassign an issue
python update_issue.py PROJ-123 --assignee none

# Update without notifying watchers
python update_issue.py PROJ-123 --summary "Updated title" --no-notify

# Delete an issue
python delete_issue.py PROJ-456

# Delete without confirmation
python delete_issue.py PROJ-456 --force
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success - operation completed successfully |
| 1 | Error - operation failed (see error message for details) |

## Configuration

Uses shared configuration from `.claude/settings.json` and `.claude/settings.local.json`.
Requires JIRA credentials via environment variables or settings files.

## Troubleshooting

### Authentication Errors

**Error**: `401 Unauthorized` or `AuthenticationError`

**Solutions**:
- Verify `JIRA_API_TOKEN` environment variable is set correctly
- Ensure the token was generated at `https://id.atlassian.com/manage-profile/security/api-tokens`
- Check that `JIRA_EMAIL` matches the email associated with the token
- Verify the token has not expired

### Permission Errors

**Error**: `403 Forbidden` or `PermissionError`

**Solutions**:
- Verify you have permission to create/edit issues in the target project
- Check project permissions with your JIRA administrator
- Ensure the issue type is available in the project's scheme

### Issue Not Found

**Error**: `404 Not Found` or `NotFoundError`

**Solutions**:
- Verify the issue key format is correct (e.g., PROJ-123)
- Check that the issue exists and has not been deleted
- Ensure you have permission to view the issue

### Invalid Issue Type

**Error**: `Issue type 'X' is not valid for project 'Y'`

**Solutions**:
- Check available issue types for the project
- Use correct case for issue type names (e.g., "Bug" not "bug")
- Verify the issue type scheme configured for the project

### Validation Errors

**Error**: `ValidationError: Invalid issue key format`

**Solutions**:
- Issue keys must match pattern `PROJECT-NUMBER` (e.g., PROJ-123)
- Project key must be uppercase letters only
- Issue number must be a positive integer

### Epic/Sprint Errors

**Error**: `Epic link field not found` or `Sprint assignment failed`

**Solutions**:
- Verify agile fields are configured in settings.json
- Check that the epic exists and is of type "Epic"
- Ensure the sprint ID is valid and belongs to an active board
- Confirm you have permission to modify sprint assignments

### Time Estimate Format

**Error**: `Invalid time estimate format`

**Solutions**:
- Use JIRA time format: `1w` (week), `2d` (days), `4h` (hours), `30m` (minutes)
- Combine units: `1d 4h`, `2h 30m`
- Time tracking must be enabled for the project

## Related skills

- **jira-lifecycle**: For workflow transitions and status changes
- **jira-search**: For finding issues with JQL queries
- **jira-collaborate**: For comments, attachments, and collaboration features
- **jira-agile**: For sprint and epic management
- **jira-relationships**: For issue linking and dependencies
- **jira-time**: For time tracking and worklogs
