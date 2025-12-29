# JQL Snippets for Time Tracking

Copy-paste JQL queries for common time tracking scenarios.

---

## Personal Time Queries

```jql
# My work with time logged this week
assignee = currentUser() AND worklogDate >= startOfWeek()

# Issues I logged time to today
worklogAuthor = currentUser() AND worklogDate = startOfDay()

# My issues with no time logged yet
assignee = currentUser() AND status = "In Progress" AND timespent IS EMPTY

# My completed work this month
assignee = currentUser() AND status = Done AND resolved >= startOfMonth()
```

## Team Time Queries

```jql
# Team worklogs this week
worklogAuthor in (membersOf("developers")) AND worklogDate >= startOfWeek()

# Issues with time logged but no assignee
assignee IS EMPTY AND timespent > 0

# Unassigned work in progress
status = "In Progress" AND assignee IS EMPTY
```

## Estimate Accuracy Queries

```jql
# Over estimate by >50%
originalEstimate IS NOT EMPTY AND timespent > originalEstimate * 1.5

# Under estimate by >50% (completed)
originalEstimate IS NOT EMPTY AND timespent < originalEstimate * 0.5 AND status = Done

# Accurate estimates (within 20%)
originalEstimate IS NOT EMPTY
AND timespent >= originalEstimate * 0.8
AND timespent <= originalEstimate * 1.2

# Issues with time but no estimate
timespent > 0 AND originalEstimate IS EMPTY

# Issues with estimate but no time (completed)
originalEstimate IS NOT EMPTY AND timespent IS EMPTY AND status = Done
```

## Stale Work Detection

```jql
# In progress with no recent time (>7 days)
status = "In Progress" AND worklogDate <= -7d

# In progress with no time ever logged
status = "In Progress" AND timespent IS EMPTY

# High time logged but still in progress (>5 days)
status = "In Progress" AND timespent > 144000
```

## Billable Tracking Queries

```jql
# Billable work this month
labels = billable AND worklogDate >= startOfMonth()

# Unbilled work (needs invoice label)
labels = billable AND labels != invoiced-2025-01 AND timespent > 0

# Non-billable time
labels = non-billable AND timespent > 0

# Client-specific time
component = "Client-ACME" AND timespent > 0
```

## Time Threshold Queries

```jql
# Significant time logged (>1 day)
timespent >= 28800

# High time logged (>3 days)
timespent >= 86400

# Very high time (>1 week)
timespent >= 144000

# Quick wins (<1 hour)
timespent > 0 AND timespent < 3600 AND status = Done
```

## Worklog Search Queries

```jql
# Worklogs by specific user
worklogAuthor = "john.doe@company.com"

# Worklogs in date range
worklogDate >= "2025-01-01" AND worklogDate <= "2025-01-31"

# Worklogs with specific text
worklogComment ~ "meeting"

# Worklogs on specific project
project = ACME AND worklogDate >= startOfMonth()
```

## Compliance Monitoring

```jql
# Issues that should have time but don't
status in (Done, Resolved) AND timespent IS EMPTY AND type in (Story, Task, Bug)

# Issues with time logged to wrong status
status = "To Do" AND timespent > 0

# Stale issues (updated but no recent worklogs)
updated >= -7d AND worklogDate <= -14d AND status = "In Progress"
```

## Date-Based Queries

```jql
# Today's worklogs
worklogDate = startOfDay()

# This week's worklogs
worklogDate >= startOfWeek()

# Last week's worklogs
worklogDate >= startOfWeek(-1) AND worklogDate < startOfWeek()

# This month's worklogs
worklogDate >= startOfMonth()

# Specific date range
worklogDate >= "2025-01-01" AND worklogDate <= "2025-01-31"
```

---

**Back to:** [SKILL.md](../../SKILL.md) | [Reporting Guide](../reporting-guide.md)
