# JQL (JIRA Query Language) Reference

Quick reference for JIRA Query Language syntax and common queries.

## Basic Syntax

```
field operator value
```

Combine with `AND`, `OR`, `NOT`:
```
field1 = value1 AND field2 = value2
field1 = value1 OR field2 = value2
field1 = value1 AND NOT field2 = value2
```

## Common Fields

- `project` - Project key
- `issuetype` / `type` - Issue type
- `status` - Current status
- `priority` - Priority level
- `assignee` - Assigned user
- `reporter` - Reporter user
- `creator` - User who created issue
- `summary` - Issue summary
- `description` - Issue description
- `labels` - Labels/tags
- `component` - Component
- `fixVersion` - Fix version
- `created` - Creation date
- `updated` - Last update date
- `resolved` - Resolution date
- `duedate` - Due date

## Operators

### Equality
- `=` - equals
- `!=` - not equals
- `IS` - is (for null values)
- `IS NOT` - is not

### Comparison
- `>` - greater than
- `>=` - greater than or equal
- `<` - less than
- `<=` - less than or equal

### Text
- `~` - contains text
- `!~` - does not contain
- `~=` - contains (exact match)

### List
- `IN` - in list
- `NOT IN` - not in list

## Common Queries

### By Project & Status
```jql
project = PROJ AND status = "In Progress"
project in (PROJ1, PROJ2) AND status != Done
```

### By Assignee
```jql
assignee = currentUser()
assignee = "user@example.com"
assignee is EMPTY
assignee was currentUser()
```

### By Date
```jql
created >= -7d
created >= "2024-01-01"
updated >= startOfWeek()
duedate < now()
```

### By Type & Priority
```jql
type = Bug AND priority = High
type in (Bug, Task) AND priority in (Highest, High)
```

### By Labels
```jql
labels = urgent
labels in (bug, production)
labels is EMPTY
```

### Text Search
```jql
summary ~ "login"
description ~ "database"
text ~ "error message"
```

## Functions

### Date Functions
- `now()` - Current date/time
- `startOfDay()` - Start of today
- `endOfDay()` - End of today
- `startOfWeek()` - Start of current week
- `endOfWeek()` - End of current week
- `startOfMonth()` - Start of current month
- `endOfMonth()` - End of current month
- `startOfYear()` - Start of current year

### User Functions
- `currentUser()` - Current logged-in user
- `membersOf("group")` - Members of group

### Relative Dates
- `-7d` - 7 days ago
- `-2w` - 2 weeks ago
- `-1M` - 1 month ago
- `-1y` - 1 year ago

## Ordering

```jql
ORDER BY priority DESC
ORDER BY created ASC
ORDER BY priority DESC, created ASC
```

## Advanced Examples

### My Work
```jql
assignee = currentUser() AND status != Done ORDER BY priority DESC
```

### Overdue
```jql
duedate < now() AND status not in (Done, Closed) ORDER BY duedate ASC
```

### Recently Updated
```jql
project = PROJ AND updated >= -7d ORDER BY updated DESC
```

### Unresolved High Priority
```jql
priority in (Highest, High) AND resolution is EMPTY ORDER BY created ASC
```

### Watching
```jql
watcher = currentUser() ORDER BY updated DESC
```

## See Also

- [Official JQL Documentation](https://support.atlassian.com/jira-service-management-cloud/docs/use-advanced-search-with-jira-query-language-jql/)
- `search_examples.md` - More query examples
