# jira-agile Quick Start Guide

Get started with Agile workflows in 5 minutes.

## Prerequisites

- JIRA API token configured (see shared setup)
- Access to a Scrum board with sprint permissions
- Project with Epic issue type enabled

## Essential 5-Minute Workflows

### Workflow 1: Create and Populate an Epic

```bash
# 1. Create the epic
python create_epic.py --project PROJ --summary "User Authentication" --epic-name "Auth"

# 2. Add existing issues to the epic
python add_to_epic.py --epic PROJ-100 --issues PROJ-101,PROJ-102,PROJ-103

# 3. Check epic progress
python get_epic.py PROJ-100 --with-children
```

### Workflow 2: Set Up and Start a Sprint

```bash
# 1. Create the sprint
python create_sprint.py --board 123 --name "Sprint 42" \
  --start 2025-01-20 --end 2025-02-03 --goal "Launch MVP"

# 2. Add issues to the sprint
python move_to_sprint.py --sprint 456 --issues PROJ-101,PROJ-102,PROJ-103

# 3. Start the sprint
python manage_sprint.py --sprint 456 --start
```

### Workflow 3: Estimate and View Summary

```bash
# 1. Estimate issues
python estimate_issue.py PROJ-101 --points 5
python estimate_issue.py PROJ-102 --points 3

# 2. View sprint estimates
python get_estimates.py --sprint 456 --group-by status
```

### Workflow 4: Close Sprint and Carryover

```bash
# 1. Review sprint status
python get_sprint.py 456 --with-issues

# 2. Close and move incomplete work
python manage_sprint.py --sprint 456 --close --move-incomplete-to 457
```

### Workflow 5: Backlog Prioritization

```bash
# 1. View current backlog
python get_backlog.py --board 123 --group-by epic

# 2. Prioritize top items
python rank_issue.py PROJ-201 --top
python rank_issue.py PROJ-202 --before PROJ-201
```

## Quick Reference

| Task | Command |
|------|---------|
| Create epic | `python create_epic.py --project PROJ --summary "..."` |
| Add to epic | `python add_to_epic.py --epic PROJ-100 --issues PROJ-101` |
| Create sprint | `python create_sprint.py --board 123 --name "Sprint 42"` |
| Start sprint | `python manage_sprint.py --sprint 456 --start` |
| Move to sprint | `python move_to_sprint.py --sprint 456 --issues PROJ-101` |
| Estimate | `python estimate_issue.py PROJ-101 --points 5` |
| View backlog | `python get_backlog.py --board 123` |
| Rank issue | `python rank_issue.py PROJ-1 --top` |

## Common Options

All scripts support:
- `--profile <name>` - Use specific JIRA profile
- `--output json` - Output as JSON
- `--dry-run` - Preview changes (where applicable)

## Next Steps

- [Detailed Examples](../examples/README.md) - Full usage examples
- [Best Practices](BEST_PRACTICES.md) - Sprint planning and estimation guidance
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
- [Field Reference](FIELD_REFERENCE.md) - Custom field configuration
