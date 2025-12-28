# Standard JIRA Workflow Pattern

**Use this pattern for:** Basic issue tracking with simple lifecycle.

**Audience:** Teams new to JIRA, small projects, straightforward work tracking.

---

## Workflow Diagram

```
To Do --> In Progress --> Done
  ^          |            |
  |          v            |
  +<-- Stop Progress <----+
             |
             v
          Reopen
```

## Statuses

| Status | Category | Description |
|--------|----------|-------------|
| To Do | To Do (Blue) | Issue created, not started |
| In Progress | In Progress (Yellow) | Active work underway |
| Done | Done (Green) | Work completed |

## Transitions

| From | To | Transition Name |
|------|----|--------------------|
| To Do | In Progress | Start Progress |
| In Progress | Done | Done |
| In Progress | To Do | Stop Progress |
| Done | To Do | Reopen |
| Done | In Progress | Reopen |

## Script Examples

```bash
# Start working on issue
python transition_issue.py PROJ-123 --name "In Progress"

# Complete issue
python transition_issue.py PROJ-123 --name "Done"

# Or with resolution
python resolve_issue.py PROJ-123 --resolution Fixed

# Stop working (return to backlog)
python transition_issue.py PROJ-123 --name "To Do"

# Reopen completed issue
python reopen_issue.py PROJ-123
```

## When to Use

- Simple projects without formal review process
- Quick prototyping or spike work
- Personal task tracking
- Teams just starting with JIRA

## When to Expand

Consider adding more statuses when:
- You need a code review step
- QA/testing is required
- Approval workflows are needed
- Work gets blocked frequently

---

*See [software_dev_workflow.md](software_dev_workflow.md) for a more comprehensive development workflow.*
