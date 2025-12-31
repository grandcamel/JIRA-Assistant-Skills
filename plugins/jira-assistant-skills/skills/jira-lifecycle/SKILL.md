---
name: "JIRA Lifecycle Management"
description: "Manage issue lifecycle through workflow transitions and status changes. Control who does what and when via assignments, versions, and components."
---

# jira-lifecycle

Workflow and lifecycle management for JIRA issues.

## Quick Discovery

**Use this skill to:** Drive issues through workflows, assign ownership, manage releases and components.

**Not for:** Creating/editing issue content (use jira-issue) or finding issues (use jira-search).

**Also see:** [Workflow Guide](references/workflow_guide.md) | [JSM Workflows](references/jsm_workflows.md) | [Best Practices](docs/BEST_PRACTICES.md)

## What this skill does

7 script categories for complete lifecycle management:

| Category | Purpose | Example |
|----------|---------|---------|
| **Transitions** | Move issues between statuses | `transition_issue.py PROJ-123 --name "In Progress"` |
| **Assignments** | Control ownership | `assign_issue.py PROJ-123 --user user@example.com` |
| **Resolution** | Mark issues complete | `resolve_issue.py PROJ-123 --resolution Fixed` |
| **Reopen** | Restore resolved issues | `reopen_issue.py PROJ-123` |
| **Versions** | Plan and track releases | `create_version.py PROJ --name "v2.0.0"` |
| **Components** | Organize by subsystem | `create_component.py PROJ --name "API"` |
| **Discovery** | View available options | `get_transitions.py PROJ-123` |

Each script supports `--help` for full option documentation.

## Available scripts

### Workflow Transitions
- `get_transitions.py` - List available transitions for an issue
- `transition_issue.py` - Transition issue to new status
- `assign_issue.py` - Assign or reassign issues
- `resolve_issue.py` - Resolve issues with resolution
- `reopen_issue.py` - Reopen closed issues

### Version Management
- `create_version.py` - Create project version with dates
- `get_versions.py` - List versions with issue counts
- `release_version.py` - Release version with date/description
- `archive_version.py` - Archive old version
- `move_issues_version.py` - Move issues between versions (supports `--dry-run`)

### Component Management
- `create_component.py` - Create project component
- `get_components.py` - List components with issue counts
- `update_component.py` - Update component details
- `delete_component.py` - Delete component with confirmation (supports `--dry-run`)

## Common Options

All scripts in this skill support these common options:

| Option | Description |
|--------|-------------|
| `--profile PROFILE` | Use a specific JIRA profile from settings (e.g., `development`, `production`) |
| `--format FORMAT` | Output format: `table`, `json`, or `csv` (default: `table`) |
| `--output FILE` | Write output to file instead of stdout |
| `--help` | Show help message and exit |

### Dry Run Support

The following scripts support `--dry-run` to preview changes without executing:

| Script | Dry Run Behavior |
|--------|------------------|
| `move_issues_version.py` | Shows which issues would be moved without modifying them |
| `delete_component.py` | Shows what would be deleted without removing the component |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - operation completed successfully |
| 1 | Error - operation failed (check stderr for details) |

## Examples

See [examples/LIFECYCLE_EXAMPLES.md](examples/LIFECYCLE_EXAMPLES.md) for comprehensive copy-paste examples.

## Workflow Compatibility

Works with standard JIRA workflows, custom workflows, JIRA Service Management workflows, and simplified workflows. Scripts automatically adapt to different configurations.

## Troubleshooting

See [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) for common issues and solutions.

**Quick fixes:**
- "No transition found" - Run `get_transitions.py ISSUE-KEY` to see available transitions
- "Transition requires fields" - Use `--fields '{"field": "value"}'` option
- "User not found" - Verify user email and project permissions

## Configuration

Requires JIRA credentials via environment variables (`JIRA_SITE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`).

## Best Practices

See [docs/BEST_PRACTICES.md](docs/BEST_PRACTICES.md) for:
- [Workflow Design](docs/WORKFLOW_DESIGN.md) - For JIRA admins designing workflows
- [Daily Operations](docs/DAILY_OPERATIONS.md) - For developers and team leads

## Workflow Patterns

Pre-built patterns in [references/patterns/](references/patterns/):
- [standard_workflow.md](references/patterns/standard_workflow.md) - Simple 3-status workflow
- [software_dev_workflow.md](references/patterns/software_dev_workflow.md) - Development with review/QA
- [jsm_request_workflow.md](references/patterns/jsm_request_workflow.md) - Service desk requests
- [incident_workflow.md](references/patterns/incident_workflow.md) - Incident management

## Related skills

- **jira-issue**: For creating and updating issues
- **jira-search**: For finding issues to transition
- **jira-collaborate**: For adding comments during transitions
- **jira-agile**: For sprint management and Agile workflows
