# JQL Search Examples

Practical JQL query examples for common scenarios.

## Personal Queries

**My open issues:**
```jql
assignee = currentUser() AND status != Done
```

**Issues I reported:**
```jql
reporter = currentUser()
```

**Issues I'm watching:**
```jql
watcher = currentUser()
```

**Issues I commented on:**
```jql
comment ~ currentUser()
```

## Time-Based Queries

**Created today:**
```jql
created >= startOfDay()
```

**Updated in last 7 days:**
```jql
updated >= -7d
```

**Resolved this week:**
```jql
resolved >= startOfWeek() AND resolved <= endOfWeek()
```

**Overdue:**
```jql
duedate < now() AND status != Done
```

## Project & Status Queries

**All open issues in project:**
```jql
project = PROJ AND status in (Open, "In Progress", Reopened)
```

**Issues in multiple projects:**
```jql
project in (PROJ1, PROJ2, PROJ3)
```

**Recently resolved:**
```jql
status changed to Resolved during (startOfWeek(), endOfWeek())
```

## Priority & Type Queries

**Critical bugs:**
```jql
type = Bug AND priority in (Highest, High) AND status != Done
```

**All stories:**
```jql
type = Story ORDER BY priority DESC
```

## Assignment Queries

**Unassigned issues:**
```jql
project = PROJ AND assignee is EMPTY
```

**Assigned to team:**
```jql
assignee in membersOf("developers")
```

**Recently reassigned:**
```jql
assignee changed during (-7d, now())
```

## Label & Component Queries

**Specific label:**
```jql
labels = production
```

**Multiple labels:**
```jql
labels in (bug, urgent, hotfix)
```

**Specific component:**
```jql
component = Backend
```

## Text Search Queries

**Summary contains:**
```jql
summary ~ "login"
```

**Description or summary:**
```jql
text ~ "database error"
```

**Specific error message:**
```jql
description ~ "NullPointerException"
```

## Complex Queries

**High priority unassigned bugs:**
```jql
type = Bug AND priority = High AND assignee is EMPTY AND status != Done
```

**Stale issues (not updated in 30 days):**
```jql
updated <= -30d AND status != Done
```

**Issues missing estimates:**
```jql
project = PROJ AND "Story Points" is EMPTY AND type = Story
```

**Blocked issues:**
```jql
status = Blocked OR labels = blocked
```

## Sprint & Agile Queries

**Current sprint:**
```jql
sprint in openSprints()
```

**Specific sprint:**
```jql
sprint = "Sprint 23"
```

**Backlog items:**
```jql
sprint is EMPTY AND status != Done
```

## Version Queries

**Fix version:**
```jql
fixVersion = "1.0"
```

**Unreleased:**
```jql
fixVersion in unreleasedVersions()
```

**Released versions:**
```jql
fixVersion in releasedVersions()
```

## Usage with Scripts

```bash
# My open issues
python jql_search.py "assignee = currentUser() AND status != Done"

# Export overdue issues
python export_results.py "duedate < now() AND status != Done" --output overdue.csv

# Bulk update stale issues
python bulk_update.py "updated <= -30d AND status = Open" --add-labels "stale"
```
