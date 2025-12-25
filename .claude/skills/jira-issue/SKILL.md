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

2. **Get Issues**: Retrieve and display issue details including:
   - All standard fields (summary, status, assignee, etc.)
   - Custom fields
   - Formatted output (detailed or summary view)
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

## Examples

```bash
# Create a bug
python create_issue.py --project PROJ --type Bug --summary "Login fails on mobile" --priority High

# Get issue details
python get_issue.py PROJ-123

# Update issue priority
python update_issue.py PROJ-123 --priority Critical --labels "urgent,security"

# Delete an issue
python delete_issue.py PROJ-456
```

## Configuration

Uses shared configuration from `.claude/settings.json` and `.claude/settings.local.json`.
Requires JIRA credentials via environment variables or settings files.

## Related skills

- **jira-lifecycle**: For workflow transitions and status changes
- **jira-search**: For finding issues with JQL queries
- **jira-collaborate**: For comments, attachments, and collaboration features
