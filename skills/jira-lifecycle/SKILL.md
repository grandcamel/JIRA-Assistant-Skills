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

## Risk Levels

| Operation | Risk | Notes |
|-----------|------|-------|
| List transitions | `-` | Read-only |
| List versions/components | `-` | Read-only |
| Transition issue | `!` | Can transition back |
| Assign/unassign | `!` | Can reassign |
| Resolve issue | `!` | Can reopen |
| Reopen issue | `!` | Can resolve again |
| Create version/component | `-` | Easily reversible |
| Update version/component | `!` | Can be undone |
| Release version | `!` | Can unrelease |
| Archive version | `!` | Can unarchive |
| Delete component | `!!` | Issues lose component association |

**Risk Legend**: `-` Safe, read-only | `!` Caution, modifiable | `!!` Warning, destructive but recoverable | `!!!` Danger, irreversible

## Quick Discovery

**Use this skill to:** Drive issues through workflows, assign ownership, manage releases and components.

**Not for:** Creating/editing issue content (use jira-issue) or finding issues (use jira-search).

**Also see:** [Workflow Guide](references/workflow_guide.md) | [JSM Workflows](references/jsm_workflows.md) | [Best Practices](docs/BEST_PRACTICES.md)

## What this skill does

**IMPORTANT:** Always use the `jira-as` CLI. Never run Python scripts directly.

7 command categories for complete lifecycle management:

| Category | Purpose | Example |
|----------|---------|---------|
| **Transitions** | Move issues between statuses | `jira-as lifecycle transition PROJ-123 --to "In Progress"` |
| **Assignments** | Control ownership | `jira-as lifecycle assign PROJ-123 --self` or `--user email` |
| **Resolution** | Mark issues complete | `jira-as lifecycle resolve PROJ-123 --resolution Fixed` |
| **Reopen** | Restore resolved issues | `jira-as lifecycle reopen PROJ-123` |
| **Versions** | Plan and track releases | `jira-as lifecycle version create PROJ --name "v2.0.0"` |
| **Components** | Organize by subsystem | `jira-as lifecycle component create PROJ --name "API"` |
| **Discovery** | View available options | `jira-as lifecycle transitions PROJ-123` |

All commands support `--help` for full option documentation.

## Available Commands

### Workflow Transitions
```bash
jira-as lifecycle transitions PROJ-123                    # List available transitions
jira-as lifecycle transitions PROJ-123 --output json      # Output as JSON
jira-as lifecycle transition PROJ-123 --to "In Progress"  # Transition by status name
jira-as lifecycle transition PROJ-123 --id 31             # Transition by ID
jira-as lifecycle transition PROJ-123 --to Done --resolution Fixed  # With resolution
jira-as lifecycle transition PROJ-123 --to "In Progress" --comment "Starting work"  # With comment
jira-as lifecycle transition PROJ-123 --to "In Progress" --sprint 42  # Move to sprint after transition
jira-as lifecycle transition PROJ-123 --to Done --dry-run             # Preview without executing
jira-as lifecycle transition PROJ-123 --to Done --fields '{"customfield_10001": "value"}'  # With custom fields
```

### Assignments
```bash
jira-as lifecycle assign PROJ-123 --self                  # Assign to yourself
jira-as lifecycle assign PROJ-123 --user email@example.com  # Assign to user
jira-as lifecycle assign PROJ-123 --unassign              # Remove assignee
```

### Resolution
```bash
jira-as lifecycle resolve PROJ-123                         # Resolve issue (may require --resolution)
jira-as lifecycle resolve PROJ-123 --resolution Fixed      # Resolve with specific resolution
jira-as lifecycle resolve PROJ-123 --resolution Fixed --comment "Fixed in v1.2.0"  # With comment
jira-as lifecycle reopen PROJ-123                          # Reopen issue
jira-as lifecycle reopen PROJ-123 --comment "Reopening for additional work"  # Reopen with comment
```

### Version Management
```bash
jira-as lifecycle version list PROJ                       # List versions
jira-as lifecycle version list PROJ --output json         # Output as JSON
jira-as lifecycle version list PROJ --unreleased          # Show only unreleased versions
jira-as lifecycle version list PROJ --archived            # Include archived versions
jira-as lifecycle version create PROJ --name "v2.0.0"     # Create version
jira-as lifecycle version create PROJ --name "v2.0.0" --description "Major release"  # With description
jira-as lifecycle version create PROJ --name "v2.0.0" --start-date 2026-01-01 --release-date 2026-03-01
jira-as lifecycle version create PROJ --name "v2.0.0" --released --dry-run  # Preview creation
jira-as lifecycle version create PROJ --name "v2.0.0" --archived  # Create as archived
jira-as lifecycle version release PROJ "v1.0.0"           # Release a version
jira-as lifecycle version release PROJ "v1.0.0" --move-unfixed "v1.1.0"  # Move unfixed issues to another version
jira-as lifecycle version archive PROJ "v0.9.0"           # Archive a version
```

### Component Management

**Note:** Component update and delete operations require the component ID (not name). Use `jira-as lifecycle component list PROJ` to find component IDs. The `--lead` option requires an account ID, not email.

```bash
jira-as lifecycle component list PROJ                     # List components (shows IDs)
jira-as lifecycle component list PROJ --output json       # Output as JSON
jira-as lifecycle component create PROJ --name "API"      # Create component
jira-as lifecycle component create PROJ --name "API" --description "REST API layer"  # With description
jira-as lifecycle component create PROJ --name "Backend" --lead 5b10a2844c20165700ede21g
jira-as lifecycle component create PROJ --name "Frontend" --assignee-type COMPONENT_LEAD
jira-as lifecycle component update --id 10000 --name "New Name"           # Update by ID
jira-as lifecycle component update --id 10000 --description "Updated description"  # Update description
jira-as lifecycle component update --id 10000 --lead 5b10a2844c20165700ede22h
jira-as lifecycle component update --id 10000 --assignee-type PROJECT_LEAD --dry-run
jira-as lifecycle component delete --id 10000             # Delete with confirmation prompt
jira-as lifecycle component delete --id 10000 --yes       # Delete without confirmation
jira-as lifecycle component delete --id 10000 --move-to 10001  # Move issues before deletion
jira-as lifecycle component delete --id 10000 --dry-run   # Preview deletion
```

## Common Options

All commands support these options:

| Option | Description |
|--------|-------------|
| `--help` | Show help message and exit |

### Output Formats by Command

| Command | Supported Formats |
|---------|-------------------|
| `transitions` | text, json |
| `transition` | text, json |
| `assign` | text, json |
| `resolve` | text, json |
| `reopen` | text, json |
| `version list` | table, json |
| `version create/release/archive` | text, json |
| `component list` | table, json |
| `component create/update/delete` | text, json |

### Dry Run Support

Most modification commands support `--dry-run` to preview changes without executing:

```bash
jira-as lifecycle transition PROJ-123 --to Done --dry-run
jira-as lifecycle assign PROJ-123 --self --dry-run
jira-as lifecycle version create PROJ --name "v1.0.0" --dry-run
jira-as lifecycle component create PROJ --name "API" --dry-run
jira-as lifecycle component update --id 10000 --name "New Name" --dry-run
jira-as lifecycle component delete --id 10000 --dry-run
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
- "No transition found" - Run `jira-as lifecycle transitions ISSUE-KEY` to see available transitions
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
