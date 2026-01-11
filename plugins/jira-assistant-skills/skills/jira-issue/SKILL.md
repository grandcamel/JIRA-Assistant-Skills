---
name: "jira-issue-management"
description: "JIRA issue operations: create, read, update, delete. ALWAYS use this skill when user wants to: (1) create new bugs/tasks/stories, (2) show/view/display/get/see/retrieve/check issue details or information, (3) look up issues, (4) update issue fields, (5) delete issues. Especially trigger when user says 'show me', 'get', 'view', 'details of', 'look at', or references 'the bug/issue/task we just created'."
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# jira-issue

Core CRUD operations for JIRA issues - create, read, update, and delete tickets.

## ⚠️ PRIMARY USE CASE: Viewing Issue Details

**This skill MUST be invoked when the user wants to see issue information.**

**CRITICAL**: When user asks to view/show/get/see issue details, you MUST:
1. Load this skill immediately (if not already loaded)
2. Use the `jira-as issue get` command to retrieve the issue
3. Display the full issue information to the user

Common phrases that REQUIRE invoking this skill:
- "Show me [the issue/bug/task]" → Use `jira-as issue get`
- "Get details of [issue]" → Use `jira-as issue get`
- "View [the issue we created]" → Use `jira-as issue get`
- "What's in [issue key]?" → Use `jira-as issue get`
- "Display issue information" → Use `jira-as issue get`
- "Look up [issue]" → Use `jira-as issue get`
- "See [the bug]" → Use `jira-as issue get`
- "Details of the bug/task/issue" → Use `jira-as issue get`

## When to Use This Skill

Triggers: User asks to...
- **View/show/display/get/retrieve/see/check issue details** ← Most common use case
- Create a new JIRA issue (bug, task, story, epic)
- Look up or examine an issue
- Update issue fields (summary, description, priority, assignee, labels)
- Delete an issue

**Context awareness**: If the user refers to "the issue/bug/task we just created" or uses pronouns like "it", resolve to the most recently created/mentioned issue in the conversation and retrieve its details.

## Available Commands

This skill provides the following commands via the `jira-as issue` CLI:

- `jira-as issue create`: Create new issues
- `jira-as issue get`: Retrieve issue details
- `jira-as issue update`: Modify issue fields
- `jira-as issue delete`: Remove issues

All commands support `--help` for full option documentation.

### Global Options

All commands inherit global options from the parent `jira-as` command:
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
jira-as issue create --project PROJ --type Bug --summary "Login fails on mobile"

# With agile fields (--points is an alias for --story-points)
jira-as issue create --project PROJ --type Story --summary "User login" \
  --epic PROJ-100 --story-points 5

# With relationships and time estimate
jira-as issue create --project PROJ --type Task --summary "Setup database" \
  --blocks PROJ-123 --estimate "2d"

# With labels and components
jira-as issue create --project PROJ --type Task --summary "Setup CI pipeline" \
  --labels "backend,infrastructure" --components "Build,DevOps"

# With custom fields (JSON format)
jira-as issue create --project PROJ --type Bug --summary "Critical bug" \
  --custom-fields '{"customfield_10050": "production"}'

# Assign to sprint
jira-as issue create --project PROJ --type Story --summary "Feature X" \
  --sprint 42

# Create without project context defaults
jira-as issue create --project PROJ --type Bug --summary "Bug" --no-defaults
```

### Retrieve Issues

```bash
# Basic retrieval
jira-as issue get PROJ-123

# With full details
jira-as issue get PROJ-123 --detailed --show-links --show-time

# Retrieve specific fields only
jira-as issue get PROJ-123 --fields "summary,status,priority,assignee"

# JSON output for scripting
jira-as issue get PROJ-123 --output json
```

**Note:** Using `--show-links` or `--show-time` automatically enables detailed view.

### Update Issues

```bash
# Update priority and assignee
jira-as issue update PROJ-123 --priority Critical --assignee self

# Update without notifications
jira-as issue update PROJ-123 --summary "Updated title" --no-notify

# Unassign issue (accepts "none" or "unassigned")
jira-as issue update PROJ-123 --assignee none

# Update labels and components (replaces existing)
jira-as issue update PROJ-123 --labels "urgent,reviewed" --components "API"

# Update custom fields
jira-as issue update PROJ-123 --custom-fields '{"customfield_10050": "staging"}'
```

**Assignee special values:**
- `self`: Assigns to the current authenticated user
- `none` or `unassigned`: Removes the assignee

### Delete Issues

```bash
# Delete with confirmation
jira-as issue delete PROJ-456

# Force delete (no prompt)
jira-as issue delete PROJ-456 --force
```

## Example Workflows

### Create and View Issue

This is the most common workflow - create an issue, then immediately view its details:

```bash
# 1. Create a bug
jira-as issue create --project DEMO --type Bug --summary "Login fails on mobile" --priority High

# Output: Created DEMO-105

# 2. View the details of the bug we just created
jira-as issue get DEMO-105

# Output shows:
# - Issue Key: DEMO-105
# - Type: Bug
# - Summary: Login fails on mobile
# - Priority: High
# - Status: Open (or whatever the initial status is)
# - And all other fields
```

**When user says "Show me the details of the bug we just created"**, this skill should:
1. Identify the most recently created issue from context (e.g., DEMO-105)
2. Execute: `jira-as issue get DEMO-105`
3. Display the full issue details including key, type, summary, priority, status, etc.

## Shell Completion

To enable shell completion for the `jira-as` CLI, add the appropriate command to your shell's configuration file (e.g., `.bashrc`, `.zshrc`, `config.fish`).

**Bash:**
```bash
eval "$(_JIRA_AS_COMPLETE=bash_source jira-as)"
```

**Zsh:**
```bash
eval "$(_JIRA_AS_COMPLETE=zsh_source jira-as)"
```

**Fish:**
```bash
_JIRA_AS_COMPLETE=fish_source jira-as | source
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
