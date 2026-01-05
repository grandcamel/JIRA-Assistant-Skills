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

**Do not use this skill when:**
- Creating individual stories/tasks without epic context (use jira-issue)
- Searching issues by JQL (use jira-search)
- Transitioning issues through workflow (use jira-lifecycle)
- Managing time tracking/worklogs (use jira-time)
- Discovering field configurations (use jira-fields)

See [Skill Selection Guide](docs/SKILL_SELECTION.md) for detailed guidance.

## What this skill does

**IMPORTANT:** Always use the `jira` CLI. Never run Python scripts directly.

### 1. Epic Management

Create epics with Epic Name and Color fields, link stories/tasks to epics, and track epic progress with story point calculations.

**Scripts:** `create_epic.py`, `add_to_epic.py`, `get_epic.py`

See [epic examples](examples/epic-management.md) for detailed usage.

### 2. Subtask Management

Create subtasks linked to parent issues with automatic project inheritance and time estimate support.

**Scripts:** `create_subtask.py`

### 3. Sprint Management

Create sprints with dates and goals, manage sprint lifecycle (start/close), move issues to sprints or backlog, and track sprint progress.

**Scripts:** `create_sprint.py`, `manage_sprint.py`, `move_to_sprint.py`, `get_sprint.py`

See [sprint examples](examples/sprint-lifecycle.md) for detailed usage.

### 4. Backlog Management

View board backlog with epic grouping, rank issues by priority (before/after/top/bottom).

**Scripts:** `get_backlog.py`, `rank_issue.py`

See [backlog examples](examples/backlog-management.md) for detailed usage.

### 5. Story Points and Estimation

Set story points on single or bulk issues, validate against Fibonacci sequence, get estimation summaries grouped by status or assignee.

**Scripts:** `estimate_issue.py`, `get_estimates.py`

See [estimation examples](examples/estimation.md) for detailed usage.

## Available scripts

### Epic Management
- `create_epic.py` - Create new epic issues with Epic Name and Color
- `add_to_epic.py` - Add or remove issues from epics (bulk operations supported)
- `get_epic.py` - Retrieve epic details with progress and story point calculations

### Subtask Management
- `create_subtask.py` - Create subtasks linked to parent issues

### Sprint Management
- `create_sprint.py` - Create new sprints on Scrum boards
- `manage_sprint.py` - Start, close, and update sprints
- `move_to_sprint.py` - Move issues to sprints or backlog
- `get_sprint.py` - Retrieve sprint details with progress tracking

### Backlog Management
- `rank_issue.py` - Reorder issues in backlog (before/after/top/bottom)
- `get_backlog.py` - Retrieve board backlog with filtering and epic grouping

### Story Points and Estimation
- `estimate_issue.py` - Set story points on issues (single, bulk, JQL)
- `get_estimates.py` - Get story point summaries for sprints, projects, or epics

## Quick examples

```bash
# Create epic and add issues
jira agile epic create --project PROJ --name "MVP" --summary "Mobile App MVP"
jira agile epic add-issues --epic PROJ-100 --issues PROJ-101,PROJ-102

# Create and start sprint
jira agile sprint create --board 123 --name "Sprint 42" --goal "Launch MVP"
jira agile sprint move-issues --sprint 456 --issues PROJ-101,PROJ-102
jira agile sprint manage 456 --start

# Estimate and track
jira agile estimate PROJ-101 --points 5
jira agile estimates --project PROJ
jira agile estimates --sprint 456 --group-by assignee
```

See [Quick Start Guide](docs/QUICK_START.md) for essential workflows.

## Common options

All scripts support:
- `--profile <name>` - Use specific JIRA profile
- `--help` - Show usage and examples

Most scripts also support:
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
