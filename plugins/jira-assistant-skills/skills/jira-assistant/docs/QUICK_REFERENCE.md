# JIRA Quick Reference

Quick lookup tables for common JIRA patterns, formats, and types.

---

## JQL Patterns

| Need | JQL |
|------|-----|
| My open issues | `assignee = currentUser() AND status != Done` |
| My in-progress | `assignee = currentUser() AND status = "In Progress"` |
| Recent bugs | `type = Bug AND created >= -7d` |
| Sprint work | `sprint in openSprints()` |
| Blockers | `status = Blocked OR "Flagged" = Impediment` |
| Unestimated stories | `"Story Points" is EMPTY AND type = Story` |
| Updated today | `updated >= startOfDay()` |
| Watching | `watcher = currentUser()` |
| Overdue | `due < now() AND status != Done` |
| No activity in 30 days | `updated <= -30d AND status != Done` |

---

## Time Formats

| Format | Meaning | Example |
|--------|---------|---------|
| `30m` | 30 minutes | `--estimate 30m` |
| `2h` | 2 hours | `--estimate 2h` |
| `1d` | 1 day (8h default) | `--estimate 1d` |
| `1w` | 1 week (5d default) | `--estimate 1w` |
| Combined | Mix units | `1d 4h 30m` |

---

## Issue Types

| Type | Use When |
|------|----------|
| **Epic** | Large feature spanning multiple sprints |
| **Story** | User-facing functionality, estimatable in points |
| **Task** | Technical work, not directly user-facing |
| **Bug** | Defect in existing functionality |
| **Subtask** | Breakdown of a parent issue |

---

## Link Types

| Link | Meaning |
|------|---------|
| **Blocks / Is blocked by** | Dependency - work cannot proceed |
| **Clones / Is cloned by** | Copy relationship |
| **Duplicates / Is duplicated by** | Same issue reported twice |
| **Relates to** | General relationship |

---

## Priority Levels

| Priority | When to Use |
|----------|-------------|
| **Highest** | Production down, critical security issue |
| **High** | Significant impact, needs immediate attention |
| **Medium** | Normal priority, planned work |
| **Low** | Nice to have, minimal impact |
| **Lowest** | Backlog, future consideration |

---

## Status Categories

| Category | Typical Statuses | Board Column |
|----------|------------------|--------------|
| **To Do** | Backlog, Open, To Do | Left |
| **In Progress** | In Progress, In Review, In QA | Middle |
| **Done** | Done, Closed, Released | Right |

---

## Common JQL Functions

| Function | Description | Example |
|----------|-------------|---------|
| `currentUser()` | Logged-in user | `assignee = currentUser()` |
| `membersOf(group)` | Group members | `assignee in membersOf("devs")` |
| `openSprints()` | Active sprints | `sprint in openSprints()` |
| `closedSprints()` | Completed sprints | `sprint in closedSprints()` |
| `futureSprints()` | Planned sprints | `sprint in futureSprints()` |
| `startOfDay()` | Midnight today | `created >= startOfDay()` |
| `endOfDay()` | End of today | `due <= endOfDay()` |
| `startOfWeek()` | Monday of this week | `created >= startOfWeek()` |
| `now()` | Current timestamp | `due < now()` |

---

## Keyboard Shortcuts (Board View)

| Key | Action |
|-----|--------|
| `c` | Create issue |
| `j/k` | Navigate issues |
| `o` | Open issue |
| `a` | Assign to me |
| `i` | Assign to someone |
| `l` | Add label |
| `m` | Comment |
| `/` | Search |

---

*For comprehensive guidance, see [Best Practices Guide](BEST_PRACTICES.md).*
