---
name: "jira-agile-management"
description: "Epic, sprint, and backlog management - create/link epics, manage sprints, estimate with story points, rank backlog issues."
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# jira-agile

Agile and Scrum workflow management for JIRA - epics, sprints, backlogs, and story points.

## Risk Levels

| Operation | Risk | Notes |
|-----------|------|-------|
| List sprints/epics | `-` | Read-only |
| Get backlog/velocity | `-` | Read-only |
| Create epic | `-` | Easily reversible (can delete) |
| Create subtask | `-` | Easily reversible (can delete) |
| Create sprint | `-` | Easily reversible (can delete) |
| Add issues to epic | `!` | Can move to different epic or remove |
| Move issues to sprint | `!` | Can move back to backlog |
| Set story points | `!` | Can update estimate |
| Start sprint | `!` | Sprint state change |
| Close sprint | `!` | Cannot undo - issues move to next sprint |
| Rank issues | `!` | Can re-rank |

**Risk Legend**: `-` Safe, read-only | `!` Caution, modifiable | `!!` Warning, destructive but recoverable | `!!!` Danger, irreversible

## When to use this skill

Use this skill when you need to:
- Create and manage epics for organizing large features
- Link issues to epics for hierarchical planning
- Create subtasks under parent issues
- Track epic progress and story point completion
- Create and manage sprints on Scrum boards
- Move issues between sprints and backlog
- Prioritize and rank backlog issues
- Estimate issues with story points
- Calculate team velocity from completed sprints

**Do not use this skill when:**
- Creating individual stories/tasks without epic context (use jira-issue)
- Searching issues by JQL (use jira-search)
- Transitioning issues through workflow (use jira-lifecycle)
- Managing time tracking/worklogs (use jira-time)
- Discovering field configurations (use jira-fields)

See [Skill Selection Guide](docs/SKILL_SELECTION.md) for detailed guidance.

## What this skill does

**IMPORTANT:** Always use the `jira-as` CLI. Never run Python scripts directly.

### 1. Epic Management

Create epics with Epic Name and Color fields, link stories/tasks to epics, and track epic progress with story point calculations.

See [epic examples](examples/epic-management.md) for detailed usage.

### 2. Subtask Management

Create subtasks linked to parent issues with automatic project inheritance and time estimate support.

### 3. Sprint Management

List and discover sprints for a project, create sprints with dates and goals, manage sprint lifecycle (start/close), move issues to sprints or backlog, and track sprint progress.

See [sprint examples](examples/sprint-lifecycle.md) for detailed usage.

### 4. Backlog Management

View board backlog with epic grouping, rank issues by priority (before/after/top/bottom).

See [backlog examples](examples/backlog-management.md) for detailed usage.

### 5. Story Points and Estimation

Set story points on single or bulk issues, validate against Fibonacci sequence, get estimation summaries grouped by status or assignee.

See [estimation examples](examples/estimation.md) for detailed usage.

### 6. Velocity Tracking

Calculate team velocity from completed sprints. Shows average story points per sprint, trends, and historical data for planning.

## Available Commands

### Epic Management
```bash
jira-as agile epic create --project PROJ --summary "Mobile App MVP"
jira-as agile epic create --project PROJ --summary "MVP" --epic-name "Mobile MVP" --color blue
jira-as agile epic get PROJ-100 --with-children
jira-as agile epic add-issues --epic PROJ-100 --issues PROJ-101,PROJ-102
jira-as agile epic add-issues --epic PROJ-100 --jql "project = PROJ AND type = Story AND status = Open"
jira-as agile epic add-issues --epic PROJ-100 --issues PROJ-101 --dry-run  # Preview changes
```

**Note:** To remove issues from an epic, move them to a different epic or use `jira-as issue update PROJ-103 --epic none` to clear the epic link.

### Subtask Management
```bash
jira-as agile subtask --parent PROJ-101 --summary "Implement login API"
jira-as agile subtask --parent PROJ-101 --summary "Task" --assignee self --estimate 4h
```

### Sprint Management
```bash
jira-as agile sprint list --project DEMO                    # List all sprints for project
jira-as agile sprint list --project DEMO --state active     # Find active sprint
jira-as agile sprint list --board 123 --state closed        # List closed sprints
jira-as agile sprint list --board 123 --max-results 50      # Limit results
jira-as agile sprint get --board 123 --active               # Get active sprint details
jira-as agile sprint get 456 --include-issues               # Get sprint with issues
jira-as agile sprint create --board 123 --name "Sprint 42" --goal "Launch MVP"
jira-as agile sprint create --board 123 --name "Sprint 42" --start-date 2026-02-01 --end-date 2026-02-14
jira-as agile sprint move-issues --sprint 456 --issues PROJ-101,PROJ-102
jira-as agile sprint move-issues --sprint 456 --jql "project = PROJ AND sprint IS EMPTY"
jira-as agile sprint move-issues --backlog --issues PROJ-101,PROJ-102  # Move to backlog
jira-as agile sprint manage --sprint 456 --start
jira-as agile sprint manage --sprint 456 --close --move-incomplete-to 457
jira-as agile sprint manage --sprint 456 --name "Sprint 42 - Revised" --goal "Updated goal"
```

### Backlog Management
```bash
jira-as agile backlog --board 123
jira-as agile backlog --board 123 --group-by epic
jira-as agile backlog --project PROJ                        # Use project instead of board
jira-as agile rank PROJ-101 --before PROJ-100
jira-as agile rank PROJ-101 --after PROJ-102
jira-as agile rank PROJ-101 --top --board 123               # Move to top (requires --board)
jira-as agile rank PROJ-101 --bottom --board 123            # Move to bottom (requires --board)
```

### Story Points and Estimation
```bash
jira-as agile estimate PROJ-101 --points 5
jira-as agile estimates --project PROJ
jira-as agile estimates --sprint 456 --group-by assignee
jira-as agile estimates --epic "Mobile MVP" --group-by status  # Filter by epic name
```

### Velocity Tracking
```bash
jira-as agile velocity --project PROJ                     # Last 3 sprints
jira-as agile velocity --project PROJ -n 5                # Last 5 sprints (-n is short for --sprints)
jira-as agile velocity --project PROJ --sprints 5         # Last 5 sprints
jira-as agile velocity --board 123 --output json          # JSON output
```

All commands support `--help` for full documentation.

## Common options

All commands support:
- `--help` - Show usage and examples

Most commands also support:
- `--output json` - Output as JSON (query and creation commands)
- `--dry-run` - Preview changes (where applicable)

See [Options Reference](docs/OPTIONS.md) for details.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (validation, API, etc.) |
| 130 | Cancelled (Ctrl+C) |

## Integration with other skills

| Skill | Integration |
|-------|-------------|
| jira-issue | Create stories/tasks, then add to epics |
| jira-search | Find issues by JQL for bulk operations |
| jira-lifecycle | Transition epic children through workflow |
| jira-fields | Discover custom field IDs for your instance |

## Custom field IDs

Default Agile field IDs may vary by instance. See [Field Reference](docs/FIELD_REFERENCE.md) for configuration.

## Troubleshooting

See [Troubleshooting Guide](docs/TROUBLESHOOTING.md) for common issues and solutions.

## Best practices

For comprehensive guidance on sprint planning, estimation, and Agile workflows, see [Best Practices Guide](docs/BEST_PRACTICES.md).
