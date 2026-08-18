---
name: "jira-issue-management"
description: "Core JIRA issue CRUD - create bugs/tasks/stories, get issue details, update fields, delete issues. TRIGGERS: 'show me [KEY]', 'get issue [KEY]', 'view issue', 'create a bug/task/story', 'update [KEY]', 'delete [KEY]', 'details of [KEY]', 'look up [KEY]', 'what's in [KEY]'. NOT FOR: epics (use jira-agile), transitions/status changes (use jira-lifecycle), comments/attachments (use jira-collaborate), time tracking (use jira-time), bulk operations on 10+ issues (use jira-bulk), dependencies/blockers (use jira-relationships), branch names/PR descriptions (use jira-dev)."
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# jira-issue

Core CRUD operations for JIRA issues - create, read, update, and delete tickets.

## Risk Levels

| Operation | Risk | Notes |
|-----------|------|-------|
| Get/view issue | `-` | Read-only |
| Create issue | `-` | Easily reversible (can delete) |
| Update fields | `!` | Can be undone via edit |
| Delete issue | `!!!` | **PERMANENT** — JIRA Cloud has no issue trash; a confirmation prompt is required |
| Delete with --force | `!!!` | **PERMANENT**, and skips the confirmation prompt |

**Risk Legend**: `-` Safe, read-only | `!` Caution, modifiable | `!!` Warning, destructive but recoverable | `!!!` Danger, irreversible

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
- `jira-as issue transition`: Transition an issue to a new status (alias for `jira-as lifecycle transition`)
- `jira-as issue transitions`: List available transitions, read-only (alias for `jira-as lifecycle transitions`)
- `jira-as issue comment`: Add a comment to an issue (alias for `jira-as collaborate comment add`)

All commands support `--help` for full option documentation.

### Output Options

`-o, --output [text|json]` is available on `issue get`, `issue create`, and `issue transitions`. Other `issue` commands print plain-text output.

## Templates

Pre-configured templates for common issue types:
- `bug_template.json` - Bug report template
- `task_template.json` - Task template
- `story_template.json` - User story template

Use the `--template` option to apply a template during issue creation:

```bash
# Quick bug report using template
jira-as issue create --project PROJ --template bug --summary "Login page error"

# Quick task using template
jira-as issue create --project PROJ --template task --summary "Update documentation"

# Quick story using template
jira-as issue create --project PROJ --template story --summary "User can reset password"
```

## Common Patterns

### Create Issues

```bash
# Basic issue creation
jira-as issue create --project PROJ --type Bug --summary "Login fails on mobile"

# With description
jira-as issue create --project PROJ --type Bug --summary "Login fails on mobile" \
  --description "Users report 500 error when logging in from mobile browsers. See attached screenshot."

# With assignee (use 'self' for current user)
jira-as issue create --project PROJ --type Task --summary "Review PR #42" \
  --assignee self

# With agile fields
jira-as issue create --project PROJ --type Story --summary "User login" \
  --epic PROJ-100 --story-points 5

# With relationships and time estimate
jira-as issue create --project PROJ --type Task --summary "Setup database" \
  --blocks PROJ-123 --estimate "2d"

# With 'relates to' links
jira-as issue create --project PROJ --type Task --summary "Related feature" \
  --relates-to PROJ-456,PROJ-789

# With labels and components
jira-as issue create --project PROJ --type Task --summary "Setup CI pipeline" \
  --labels "backend,infrastructure" --components "Build,DevOps"

# With custom fields (JSON format)
jira-as issue create --project PROJ --type Bug --summary "Critical bug" \
  --custom-fields '{"customfield_10050": "production"}'

# Assign to sprint
jira-as issue create --project PROJ --type Story --summary "Feature X" \
  --sprint 42

# Create as a child of an epic or parent task
jira-as issue create --project PROJ --type Task --summary "Child task" \
  --parent PROJ-100

# For workflows that reject a parent at create time: create without the
# parent, then set it in a follow-up update
jira-as issue create --project PROJ --type Task --summary "Child task" \
  --parent PROJ-100 --parent-via-update

# Preview the payload that would be sent without creating the issue
jira-as issue create --project PROJ --type Bug --summary "Bug" --dry-run

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

# Update description
jira-as issue update PROJ-123 --description "Updated description with **markdown** support"

# Update without notifications
jira-as issue update PROJ-123 --summary "Updated title" --no-notify

# Unassign issue (accepts "none" or "unassigned")
jira-as issue update PROJ-123 --assignee none

# Update labels and components (replaces existing)
jira-as issue update PROJ-123 --labels "urgent,reviewed" --components "API"

# Move issue under a new parent (epic or parent task)
jira-as issue update PROJ-123 --parent PROJ-100

# Remove the parent
jira-as issue update PROJ-123 --parent none

# Update custom fields
jira-as issue update PROJ-123 --custom-fields '{"customfield_10050": "staging"}'
```

**Assignee special values:**
- `self`: Assigns to the current authenticated user
- `none` or `unassigned`: Removes the assignee

**Notification suppression (`--no-notify`):** Suppressing watcher notifications requires the "Administer Jira" global permission. For non-admin users JIRA rejects the whole request with a 403, so the CLI automatically retries without suppression: the update still lands, watchers are notified, and a warning is printed on stderr.

### Rich-Text Custom Fields (ADF)

JIRA Cloud stores rich text as Atlassian Document Format (ADF). The CLI automatically wraps plain-string values for the built-in rich-text fields (`description`, `environment`) in ADF, converting markdown so formatting survives. If your instance has rich-text *custom* fields, list their IDs in the `JIRA_ADF_CUSTOM_FIELDS` environment variable (comma-separated) and their values are auto-wrapped too, on both create and update:

```bash
export JIRA_ADF_CUSTOM_FIELDS="customfield_10050,customfield_10051"

jira-as issue update PROJ-123 \
  --custom-fields '{"customfield_10050": "Deployed to **staging**"}'
```

Values that are already ADF documents pass through untouched.

### Transition and Comment Aliases

For convenience, common lifecycle and collaboration operations are aliased under `issue`, with the same options as the underlying commands:

```bash
# List available transitions (alias for `jira-as lifecycle transitions`)
jira-as issue transitions PROJ-123
jira-as issue transitions PROJ-123 --output json

# Transition to a new status (alias for `jira-as lifecycle transition`)
jira-as issue transition PROJ-123 --to "In Progress"
jira-as issue transition PROJ-123 --to Done --resolution Fixed
jira-as issue transition PROJ-123 --id 31 --dry-run

# Add a comment (alias for `jira-as collaborate comment add`)
jira-as issue comment PROJ-123 --body "Starting work"
jira-as issue comment PROJ-123 --body "**Done**" --format markdown
```

This supports the common create → work → transition → comment flow without switching command groups. For advanced workflow and comment operations (editing/deleting comments, attachments, versions, components), use the full `jira-as lifecycle` and `jira-as collaborate` groups.

### Delete Issues

```bash
# Delete with confirmation
jira-as issue delete PROJ-456

# Force delete (skips confirmation prompt; deletion is PERMANENT)
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

### Agile Field IDs (story points, sprint, epic link)

Custom field IDs for Agile fields often differ per instance — and per project. The `--story-points`, `--sprint`, and `--epic` options resolve their field IDs in priority order (highest first):

1. Per-project overrides in settings: `jira.projects.<KEY>.agile_fields`
2. Global settings block: `jira.agile_fields`
3. Environment variables (`JIRA_STORY_POINTS_FIELD`, `JIRA_SPRINT_FIELD`, `JIRA_EPIC_LINK_FIELD`)
4. Built-in defaults

Example settings entry with a per-project story points override:

```json
{
  "jira": {
    "agile_fields": {
      "story_points": "customfield_10016"
    },
    "projects": {
      "MYAPP": {
        "agile_fields": {
          "story_points": "customfield_10116",
          "sprint": "customfield_10120"
        }
      }
    }
  }
}
```

## Related Resources

Resources in the skill directory (`skills/jira-issue/`):
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
