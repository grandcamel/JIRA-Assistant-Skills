---
name: "jira-lifecycle-management"
description: "Manage issue lifecycle through workflow transitions and status changes. Control who does what and when via assignments, versions, and components."
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# jira-lifecycle

Workflow and lifecycle management for JIRA issues.

## Quick Discovery

**Use this skill to:** Drive issues through workflows, assign ownership, manage releases and components.

**Not for:** Creating/editing issue content (use jira-issue) or finding issues (use jira-search).

**Also see:** [Workflow Guide](references/workflow_guide.md) | [JSM Workflows](references/jsm_workflows.md) | [Best Practices](docs/BEST_PRACTICES.md)

## What this skill does

**IMPORTANT:** Always use the `jira` CLI. Never run Python scripts directly.

7 command categories for complete lifecycle management:

| Category | Purpose | Example |
|----------|---------|---------|
| **Transitions** | Move issues between statuses | `jira lifecycle transition PROJ-123 --to "In Progress"` |
| **Assignments** | Control ownership | `jira lifecycle assign PROJ-123 --self` or `--user email` |
| **Resolution** | Mark issues complete | `jira lifecycle resolve PROJ-123 --resolution Fixed` |
| **Reopen** | Restore resolved issues | `jira lifecycle reopen PROJ-123` |
| **Versions** | Plan and track releases | `jira lifecycle version create PROJ "v2.0.0"` |
| **Components** | Organize by subsystem | `jira lifecycle component create PROJ "API"` |
| **Discovery** | View available options | `jira lifecycle transitions PROJ-123` |

All commands support `--help` for full option documentation.

## Available Commands

### Workflow Transitions
```bash
jira lifecycle transitions PROJ-123                    # List available transitions
jira lifecycle transition PROJ-123 --to "In Progress"  # Transition issue
jira lifecycle transition PROJ-123 --to Done --resolution Fixed  # With resolution
```

### Assignments
```bash
jira lifecycle assign PROJ-123 --self                  # Assign to yourself
jira lifecycle assign PROJ-123 --user email@example.com  # Assign to user
jira lifecycle assign PROJ-123 --unassign              # Remove assignee
```

### Resolution
```bash
jira lifecycle resolve PROJ-123 --resolution Fixed     # Resolve issue
jira lifecycle reopen PROJ-123                         # Reopen issue
```

### Version Management
```bash
jira lifecycle version list PROJ                       # List versions
jira lifecycle version create PROJ "v2.0.0" --start-date 2024-01-01
jira lifecycle version release PROJ "v1.0.0"
jira lifecycle version archive PROJ "v0.9.0"
```

### Component Management
```bash
jira lifecycle component list PROJ                     # List components
jira lifecycle component create PROJ "API"
jira lifecycle component update PROJ "API" --lead user@example.com
jira lifecycle component delete PROJ "Legacy" --force
```

## Common Options

All commands support these options:

| Option | Description |
|--------|-------------|
| `--profile, -p` | Use a specific JIRA profile |
| `--help` | Show help message and exit |

Query commands (`transitions`, `version list`, `component list`) also support `--output` for `text`, `json`, or `table` output.

### Dry Run Support

Some commands support `--dry-run` to preview changes:

```bash
jira lifecycle assign PROJ-123 --self --dry-run
jira lifecycle component delete PROJ "API" --dry-run
```

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
- "No transition found" - Run `jira lifecycle transitions ISSUE-KEY` to see available transitions
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
