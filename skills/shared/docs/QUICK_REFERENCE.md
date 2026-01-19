# JIRA Skills Quick Reference

One-page cheat sheet for common operations.

## CLI Command Quick Reference

### Issue Operations (jira-issue)

```bash
# View issue
jira-as issue get PROJ-123
jira-as issue get PROJ-123 --detailed --show-links --show-time

# Create issue
jira-as issue create --project PROJ --type Bug --summary "Title"
jira-as issue create --project PROJ --type Story --summary "Title" --epic PROJ-100 --story-points 5

# Update issue
jira-as issue update PROJ-123 --priority High --assignee self
jira-as issue update PROJ-123 --labels "urgent,reviewed"

# Delete issue
jira-as issue delete PROJ-123
jira-as issue delete PROJ-123 --force
```

### Search & Filters (jira-search)

```bash
# Execute JQL
jira-as search query "project = PROJ AND status = Open"
jira-as search query "assignee = currentUser() AND sprint in openSprints()"

# Build JQL
jira-as search build --project PROJ --status Open --assignee currentUser()

# Export results
jira-as search export "project = PROJ" -o report.csv
jira-as search export "project = PROJ" -o data.json --format json

# Saved filters
jira-as search filter list --favourite
jira-as search filter create "My Filter" "project = PROJ" --favourite
jira-as search filter run 10042
```

### Workflow & Lifecycle (jira-lifecycle)

```bash
# Transitions
jira-as lifecycle transitions PROJ-123
jira-as lifecycle transition PROJ-123 --to "In Progress"
jira-as lifecycle transition PROJ-123 --to Done --resolution Fixed

# Assignments
jira-as lifecycle assign PROJ-123 --self
jira-as lifecycle assign PROJ-123 --user email@example.com
jira-as lifecycle assign PROJ-123 --unassign

# Versions
jira-as lifecycle version list PROJ
jira-as lifecycle version create PROJ --name "v2.0.0"
jira-as lifecycle version release PROJ "v1.0.0"

# Components
jira-as lifecycle component list PROJ
jira-as lifecycle component create PROJ --name "API"
```

### Agile & Scrum (jira-agile)

```bash
# Sprints
jira-as agile sprint list --project PROJ
jira-as agile sprint get --board 123 --active
jira-as agile sprint create --board 123 --name "Sprint 42"
jira-as agile sprint move-issues --sprint 456 --issues PROJ-1,PROJ-2

# Epics
jira-as agile epic create --project PROJ --summary "Epic Title"
jira-as agile epic get PROJ-100 --with-children
jira-as agile epic add-issues --epic PROJ-100 --issues PROJ-101,PROJ-102

# Subtasks
jira-as agile subtask --parent PROJ-101 --summary "Subtask"

# Backlog & Estimation
jira-as agile backlog --board 123
jira-as agile rank PROJ-101 --before PROJ-100
jira-as agile estimate PROJ-101 --points 5
jira-as agile velocity --project PROJ
```

### Collaboration (jira-collaborate)

```bash
# Comments
jira-as collaborate comment add PROJ-123 --body "Comment text"
jira-as collaborate comment list PROJ-123
jira-as collaborate comment delete PROJ-123 --id 10001 --yes

# Attachments
jira-as collaborate attachment upload PROJ-123 --file screenshot.png
jira-as collaborate attachment download PROJ-123 12345 --output ./

# Watchers
jira-as collaborate watchers PROJ-123 --list
jira-as collaborate watchers PROJ-123 --add user@example.com

# Activity
jira-as collaborate activity PROJ-123
```

### Relationships (jira-relationships)

```bash
# Link issues
jira-as relationships link PROJ-1 --blocks PROJ-2
jira-as relationships link PROJ-1 --relates-to PROJ-2
jira-as relationships get-links PROJ-123
jira-as relationships unlink PROJ-1 PROJ-2

# Blockers & Dependencies
jira-as relationships get-blockers PROJ-123 --recursive
jira-as relationships get-dependencies PROJ-123 --output mermaid

# Clone
jira-as relationships clone PROJ-123 --clone-subtasks --clone-links
```

### Time Tracking (jira-time)

```bash
# Log time
jira-as time log PROJ-123 --time 2h
jira-as time log PROJ-123 --time "1d 4h" --comment "Description"

# View worklogs
jira-as time worklogs PROJ-123
jira-as time tracking PROJ-123

# Estimates
jira-as time estimate PROJ-123 --original "2d" --remaining "1d"

# Reports
jira-as time report --user currentUser() --period this-week
jira-as time export --project PROJ --period last-month -o timesheet.csv

# Bulk
jira-as time bulk-log --issues PROJ-1,PROJ-2 --time 15m --dry-run
```

### Bulk Operations (jira-bulk)

```bash
# Always dry-run first!
jira-as bulk transition --jql "project=PROJ" --to Done --dry-run
jira-as bulk transition --jql "project=PROJ" --to Done

jira-as bulk assign --jql "project=PROJ" --assignee self --dry-run
jira-as bulk set-priority --jql "type=Bug" --priority High --dry-run
jira-as bulk clone --jql "sprint='Sprint 42'" --include-subtasks --dry-run
jira-as bulk delete --jql "project=CLEANUP" --dry-run  # DANGER!
```

### Service Management (jira-jsm)

```bash
# Service desks
jira-as jsm service-desk list
jira-as jsm request-type list 1

# Requests
jira-as jsm request create 1 10 --summary "Title" --description "Details"
jira-as jsm request get SD-123
jira-as jsm request comment SD-123 "Comment text"

# SLA & Approvals
jira-as jsm sla get SD-123
jira-as jsm approval approve SD-124 1001 --comment "Approved" --yes
```

### Developer Integration (jira-dev)

```bash
# Branch names
jira-as dev branch-name PROJ-123
jira-as dev branch-name PROJ-123 --prefix bugfix --output git

# Commits & PRs
jira-as dev parse-commits "feat(PROJ-123): add login"
jira-as dev pr-description PROJ-123 --include-checklist
jira-as dev link-pr PROJ-123 --pr https://github.com/org/repo/pull/456
```

### Field Management (jira-fields)

```bash
jira-as fields list
jira-as fields list --agile
jira-as fields check-project PROJ --check-agile
jira-as fields configure-agile PROJ --dry-run
```

### Operations (jira-ops)

```bash
jira-as ops discover-project PROJ
jira-as ops cache-status
jira-as ops cache-warm --all
jira-as ops cache-clear --force
```

### Administration (jira-admin)

```bash
# Projects
jira-as admin project list
jira-as admin project create
jira-as admin project delete PROJ --dry-run

# Users & Groups
jira-as admin user search "name"
jira-as admin group list
jira-as admin group add-user GROUP --user email@example.com

# Permissions
jira-as admin permission-scheme list
jira-as admin permissions check --project PROJ

# Automation
jira-as admin automation list --project PROJ
jira-as admin automation enable RULE_ID
```

## Common JQL Patterns

### Basic Queries

```jql
# My open issues
assignee = currentUser() AND status != Done

# Project bugs
project = PROJ AND type = Bug

# Created this week
created >= startOfWeek()

# Updated recently
updated >= -7d
```

### Sprint Queries

```jql
# Current sprint
sprint in openSprints()

# Specific sprint
sprint = "Sprint 42"

# Backlog (not in any sprint)
sprint is EMPTY AND project = PROJ
```

### Time-Based Queries

```jql
# Last 24 hours
created >= -24h

# This month
created >= startOfMonth()

# Date range
created >= "2025-01-01" AND created <= "2025-01-31"
```

### Status & Workflow

```jql
# Not started
status = "To Do"

# In progress
status in ("In Progress", "In Review")

# Completed
status = Done OR resolution is not EMPTY
```

### Assignments

```jql
# Unassigned
assignee is EMPTY

# Assigned to me
assignee = currentUser()

# Recently assigned to me
assignee changed TO currentUser() AFTER -7d
```

### Labels & Components

```jql
# Has label
labels = urgent

# Multiple labels
labels in (urgent, critical)

# Has component
component = API
```

### Relationships

```jql
# Has links
issueLinks is not EMPTY

# Epic children
"Epic Link" = PROJ-100

# Subtasks of parent
parent = PROJ-101
```

## Issue Field Shortcuts

| Field | JQL Name | CLI Flag |
|-------|----------|----------|
| Summary | summary | --summary |
| Description | description | --description |
| Priority | priority | --priority |
| Assignee | assignee | --assignee |
| Reporter | reporter | --reporter |
| Labels | labels | --labels |
| Components | component | --components |
| Fix Version | fixVersion | --fix-version |
| Affected Version | affectedVersion | --affected-version |
| Epic Link | "Epic Link" | --epic |
| Story Points | "Story Points" | --story-points, --points |
| Sprint | sprint | --sprint |

## Error Code Meanings

| Code | Meaning | Common Solution |
|------|---------|-----------------|
| 400 | Bad Request | Check input format, required fields |
| 401 | Unauthorized | Verify API token and email |
| 403 | Forbidden | Check permissions; use jira-admin permissions check |
| 404 | Not Found | Verify issue key, project exists |
| 409 | Conflict | Resource exists or state conflict |
| 429 | Rate Limited | Wait and retry; reduce batch size |
| 500 | Server Error | JIRA issue; retry later |

## Workflow Transition Syntax

```bash
# By status name
jira-as lifecycle transition PROJ-123 --to "In Progress"

# By transition ID
jira-as lifecycle transition PROJ-123 --id 31

# With resolution
jira-as lifecycle transition PROJ-123 --to Done --resolution Fixed

# With custom fields
jira-as lifecycle transition PROJ-123 --to Done --fields '{"customfield_10001": "value"}'
```

## Time Format Reference

| Format | Example | Duration |
|--------|---------|----------|
| Minutes | 30m | 30 minutes |
| Hours | 2h | 2 hours |
| Days | 1d | 8 hours |
| Weeks | 1w | 40 hours |
| Combined | 1d 4h 30m | 12.5 hours |

## Common Flags

| Flag | Purpose | Example |
|------|---------|---------|
| --help | Show help | jira-as issue --help |
| --output, -o | Output format | --output json |
| --dry-run | Preview only | --dry-run |
| --force, -f | Skip confirmation | --force |
| --yes | Confirm action | --yes |
| --max-results | Limit results | --max-results 100 |
| --fields | Select fields | --fields key,summary,status |

## Risk Level Quick Reference

| Symbol | Meaning | Action |
|--------|---------|--------|
| `-` | Safe | Proceed |
| `!` | Caution | Explain effect |
| `!!` | Warning | Confirm + dry-run |
| `!!!` | Danger | Dry-run + explicit confirm |
