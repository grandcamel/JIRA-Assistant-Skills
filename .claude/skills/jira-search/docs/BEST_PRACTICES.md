# JIRA Search & JQL Best Practices Guide

Comprehensive guide to mastering JIRA Query Language (JQL) for efficient search, filtering, and issue discovery.

---

## Table of Contents

1. [JQL Fundamentals](#jql-fundamentals)
2. [Operator Reference](#operator-reference)
3. [Common Query Patterns](#common-query-patterns)
4. [Advanced JQL Techniques](#advanced-jql-techniques)
5. [Performance Optimization](#performance-optimization)
6. [Filter Management](#filter-management)
7. [Export & Reporting](#export--reporting)
8. [Common Pitfalls](#common-pitfalls)
9. [Quick Reference Card](#quick-reference-card)

---

## JQL Fundamentals

### Basic Syntax

JQL queries follow a simple pattern:
```
field operator value
```

Combine multiple conditions with logical operators:
```jql
field1 = value1 AND field2 = value2
field1 = value1 OR field2 = value2
NOT field1 = value1
```

### Query Structure Best Practices

**Do:**
- Use parentheses for complex logic: `(A OR B) AND C`
- Quote values with spaces: `status = "In Progress"`
- Use uppercase for operators: `AND`, `OR`, `NOT`
- Order clauses from most to least restrictive

**Don't:**
- Mix OR and AND without parentheses
- Use ambiguous field names
- Write overly complex single queries (use saved filters instead)

**Examples:**
```jql
# Good - Clear structure
project = PROJ AND (status = Open OR status = "In Progress") AND priority = High

# Bad - Ambiguous precedence
project = PROJ AND status = Open OR status = "In Progress" AND priority = High
```

---

## Operator Reference

### Equality Operators

| Operator | Description | Example | Use Case |
|----------|-------------|---------|----------|
| `=` | Equals | `status = Done` | Exact match |
| `!=` | Not equals | `status != Done` | Exclusion (avoid for performance) |
| `IS` | Is (null check) | `assignee IS EMPTY` | Check for empty values |
| `IS NOT` | Is not (null check) | `assignee IS NOT EMPTY` | Check for non-empty values |

### Comparison Operators

| Operator | Description | Example | Use Case |
|----------|-------------|---------|----------|
| `>` | Greater than | `created > 2025-01-01` | After date |
| `>=` | Greater or equal | `priority >= High` | At least this value |
| `<` | Less than | `duedate < now()` | Before date/time |
| `<=` | Less or equal | `created <= -7d` | Within timeframe |

### Text Operators

| Operator | Description | Example | Use Case |
|----------|-------------|---------|----------|
| `~` | Contains | `summary ~ login` | Text search (case-insensitive) |
| `!~` | Not contains | `summary !~ test` | Exclude text |
| `~=` | Exact match | `summary ~= "Login Bug"` | Exact phrase match |

### List Operators

| Operator | Description | Example | Use Case |
|----------|-------------|---------|----------|
| `IN` | In list | `status IN (Open, "To Do")` | Multiple values |
| `NOT IN` | Not in list | `priority NOT IN (Low, Lowest)` | Exclude multiple |

### Historical Operators

| Operator | Description | Example | Use Case |
|----------|-------------|---------|----------|
| `WAS` | Was value | `status WAS "In Progress"` | Ever had this value |
| `WAS IN` | Was in list | `status WAS IN (Open, Blocked)` | Ever had any of these |
| `WAS NOT` | Was not value | `assignee WAS NOT EMPTY` | Never had this value |
| `WAS NOT IN` | Was not in list | `status WAS NOT IN (Done, Closed)` | Never had any of these |
| `CHANGED` | Field changed | `status CHANGED` | Any change occurred |

**Historical Operators Work On:**
- Assignee
- Fix Version
- Priority
- Reporter
- Resolution
- Status
- Sprint (limited support)

**Historical Operators DON'T Work On:**
- Custom fields (most)
- Description
- Comments
- Labels
- Components

### Change Tracking Operators

| Operator | Description | Example | Use Case |
|----------|-------------|---------|----------|
| `CHANGED` | Field changed | `status CHANGED` | Find any changes |
| `CHANGED BY` | Changed by user | `priority CHANGED BY john.doe` | Who made change |
| `CHANGED FROM` | Changed from value | `status CHANGED FROM Open` | What it changed from |
| `CHANGED TO` | Changed to value | `status CHANGED TO Done` | What it changed to |
| `CHANGED AFTER` | Changed after date | `assignee CHANGED AFTER -7d` | Recent changes |
| `CHANGED BEFORE` | Changed before date | `status CHANGED BEFORE 2025-01-01` | Old changes |
| `CHANGED DURING` | Changed in range | `status CHANGED DURING (startOfWeek(), now())` | Time window |

**Examples:**
```jql
# Find issues that moved from In Progress to Done this week
status CHANGED FROM "In Progress" TO Done DURING (startOfWeek(), now())

# Find issues reassigned in the last 7 days
assignee CHANGED AFTER -7d

# Find issues where priority was escalated by a manager
priority CHANGED FROM Medium TO High BY manager@company.com
```

---

## Common Query Patterns

### Personal Queries

| Query Type | JQL | Use Case |
|------------|-----|----------|
| My open work | `assignee = currentUser() AND status != Done` | Daily standup |
| My watching | `watcher = currentUser() ORDER BY updated DESC` | Track interests |
| I reported | `reporter = currentUser() AND status NOT IN (Done, Closed)` | Follow-ups |
| Mentions me | `comment ~ currentUser() AND assignee != currentUser()` | Collaboration |

### Time-Based Queries

| Query Type | JQL | Use Case |
|------------|-----|----------|
| Created today | `created >= startOfDay()` | Daily activity |
| Updated this week | `updated >= startOfWeek()` | Weekly review |
| Last 7 days | `created >= -7d` | Week overview |
| This month | `created >= startOfMonth() AND created <= endOfMonth()` | Monthly metrics |
| Overdue | `duedate < now() AND status != Done` | Action needed |
| Stale (30+ days) | `updated <= -30d AND status NOT IN (Done, Closed)` | Cleanup candidates |
| Recently resolved | `resolved >= -7d ORDER BY resolved DESC` | Completed work |
| No activity (14d) | `updated <= -14d AND status = "In Progress"` | Stuck issues |

**Time Function Reference:**
```jql
# Absolute dates
created >= "2025-01-01"
created <= "2025-12-31"

# Relative dates
created >= -7d      # 7 days ago
created >= -2w      # 2 weeks ago
created >= -1M      # 1 month ago
created >= -1y      # 1 year ago

# Date boundaries
created >= startOfDay()
created >= startOfWeek()      # Monday
created >= startOfMonth()
created >= startOfYear()
created >= endOfDay()
created >= endOfWeek()        # Sunday

# With offsets
created >= startOfDay(-7d)    # Start of day 7 days ago
created >= startOfWeek(-1w)   # Start of previous week
```

### User-Based Queries

| Query Type | JQL | Use Case |
|------------|-----|----------|
| Assigned to me | `assignee = currentUser()` | My work |
| Unassigned | `assignee IS EMPTY AND status = Open` | Needs triage |
| Team members | `assignee IN membersOf("developers")` | Team workload |
| Not me | `assignee IS NOT EMPTY AND assignee != currentUser()` | Others' work |
| Changed owner | `assignee CHANGED DURING (-7d, now())` | Handoffs |
| Multiple owners | `assignee WAS NOT currentUser()` | Collaboration |

### Sprint & Agile Queries

| Query Type | JQL | Use Case |
|------------|-----|----------|
| Active sprint | `sprint IN openSprints()` | Current work |
| Future sprints | `sprint IN futureSprints()` | Planned work |
| Past sprints | `sprint IN closedSprints()` | Historical data |
| Backlog | `sprint IS EMPTY AND status != Done` | Not planned |
| Specific sprint | `sprint = "Sprint 42"` | Sprint review |
| Carried over | `sprint WAS "Sprint 41" AND sprint = "Sprint 42"` | Scope creep |
| Sprint incomplete | `sprint IN closedSprints() AND status != Done` | Incomplete work |

### Priority & Type Queries

| Query Type | JQL | Use Case |
|------------|-----|----------|
| Critical bugs | `type = Bug AND priority IN (Highest, High) AND status != Done` | Urgent work |
| P0 issues | `priority = Highest AND status NOT IN (Done, Closed)` | Blocker triage |
| Stories only | `type = Story ORDER BY priority DESC` | Feature work |
| Technical debt | `type = Task AND labels IN (tech-debt, refactor)` | Debt tracking |
| Subtasks | `issuetype IN subTaskIssueTypes()` | Breakdown items |

### Status & Workflow Queries

| Query Type | JQL | Use Case |
|------------|-----|----------|
| In progress | `status = "In Progress"` | Active work |
| Multiple states | `status IN (Open, "To Do", Backlog)` | Not started |
| Blocked | `status = Blocked OR labels = blocked` | Impediments |
| Ready for review | `status = "In Review" AND updated >= -2d` | Recent reviews |
| Status changed | `status CHANGED FROM "In Progress" TO Done DURING (startOfWeek(), now())` | Completed this week |

### Project & Version Queries

| Query Type | JQL | Use Case |
|------------|-----|----------|
| Multiple projects | `project IN (PROJ1, PROJ2, PROJ3)` | Portfolio view |
| Fix version | `fixVersion = "2.0" AND status != Done` | Release scope |
| Unreleased | `fixVersion IN unreleasedVersions()` | Pending releases |
| Released | `fixVersion IN releasedVersions()` | Shipped work |
| No version | `fixVersion IS EMPTY AND type != Epic` | Needs planning |

### Label & Component Queries

| Query Type | JQL | Use Case |
|------------|-----|----------|
| Single label | `labels = production` | Tagged items |
| Multiple labels | `labels IN (bug, urgent, hotfix)` | Multiple tags |
| No labels | `labels IS EMPTY` | Needs tagging |
| Component | `component = Backend` | Area of work |
| Multiple components | `component IN (API, Database)` | Multiple areas |

---

## Advanced JQL Techniques

### Subqueries and Linked Issues

**Find issues linked to a specific issue:**
```jql
issuekey IN linkedIssues(PROJ-123)
```

**Find issues linked by specific link type:**
```jql
issuekey IN linkedIssues(PROJ-123, "blocks")
issuekey IN linkedIssues(PROJ-123, "is blocked by")
```

**Find issues that block current sprint:**
```jql
issuekey IN linkedIssues("sprint IN openSprints()", "blocks")
```

**Find epics with incomplete stories:**
```jql
issuetype = Epic AND issuekey IN linkedIssues("status != Done", "Epic-Story Link")
```

### Wildcards and Pattern Matching

**Summary wildcards:**
```jql
summary ~ "login*"      # Starts with "login"
summary ~ "*error*"     # Contains "error"
summary ~ "fix*bug"     # Pattern matching
```

**Project key patterns:**
```jql
project IN (PROJ*)      # All projects starting with PROJ
```

**Note:** Wildcard support is limited. Text operators (`~`) are better for most cases.

### Complex Boolean Logic

**Find high-priority work across projects:**
```jql
(project = PROJ1 OR project = PROJ2)
AND (priority = Highest OR (priority = High AND labels = urgent))
AND status NOT IN (Done, Closed)
ORDER BY priority DESC, created ASC
```

**Sprint health check:**
```jql
project = PROJ AND sprint IN openSprints()
AND (
  (status = "In Progress" AND updated <= -3d) OR
  (status = "To Do" AND "Story Points" IS EMPTY) OR
  (status = Blocked) OR
  (assignee IS EMPTY)
)
ORDER BY priority DESC
```

**Release readiness:**
```jql
fixVersion = "v2.0"
AND status NOT IN (Done, Closed)
AND (
  priority IN (Highest, High) OR
  labels IN (must-have, blocker)
)
ORDER BY priority DESC, created ASC
```

### Custom Field Queries

**Story points:**
```jql
"Story Points" IS EMPTY AND type = Story
"Story Points" > 8
"Story Points" IN (1, 2, 3, 5)
```

**Custom date fields:**
```jql
"Deployment Date" >= startOfMonth()
"Deployment Date" <= endOfMonth()
```

**Custom select fields:**
```jql
"Severity" = Critical
"Team" IN ("Team Alpha", "Team Beta")
```

**Multi-select custom fields:**
```jql
"Affected Modules" IN (Database, API)
```

### Historical Analysis Queries

**Issues that bounced back:**
```jql
status = "In Progress" AND status WAS Done
```

**Priority escalations:**
```jql
priority = Highest AND priority WAS NOT Highest
ORDER BY priority CHANGED DESC
```

**Reassignment patterns:**
```jql
assignee CHANGED AFTER -30d
AND assignee CHANGED BY currentUser()
ORDER BY assignee CHANGED DESC
```

**Status regressions:**
```jql
status WAS Done AND status != Done
ORDER BY status CHANGED DESC
```

### Combining Multiple Criteria

**Tech debt older than 90 days:**
```jql
labels IN (tech-debt, refactor)
AND status != Done
AND created <= -90d
ORDER BY created ASC
```

**High-value quick wins:**
```jql
priority IN (High, Highest)
AND "Story Points" <= 3
AND status = "To Do"
ORDER BY priority DESC, "Story Points" ASC
```

**Stale high-priority issues:**
```jql
priority IN (Highest, High)
AND status NOT IN (Done, Closed)
AND updated <= -14d
ORDER BY priority DESC, updated ASC
```

**Cross-team dependencies:**
```jql
project = PROJ1
AND issuekey IN linkedIssues("project != PROJ1", "blocks")
ORDER BY priority DESC
```

---

## Performance Optimization

### Use Indexed Fields

**Indexed fields (fast):**
- `project`
- `issuetype` / `type`
- `status`
- `priority`
- `assignee`
- `reporter`
- `created`
- `updated`
- `resolved`

**Non-indexed fields (slower):**
- `labels` (complex field)
- `description` (text search)
- `comment` (text search)
- Many custom fields

**Best Practice:**
```jql
# Good - Uses indexed fields first
project = PROJ AND status = Open AND assignee = currentUser()

# Less optimal - Non-indexed field first
labels = urgent AND project = PROJ AND status = Open
```

### Limit Query Scope

**Always specify project when possible:**
```jql
# Good - Limited scope
project = PROJ AND status = Open

# Less optimal - Searches entire instance
status = Open AND assignee = currentUser()
```

**Use project lists for multi-project queries:**
```jql
# Good - Explicit project list
project IN (PROJ1, PROJ2, PROJ3) AND status = Open

# Less optimal - Searches all projects
status = Open
```

### Avoid Negations

**Negations are slow:**
```jql
# Slow - Negative operator
status != Done

# Faster - Positive operator
status IN (Open, "In Progress", "To Do", Blocked)
```

**Replace NOT with positive conditions:**
```jql
# Slow
priority != Low AND priority != Lowest

# Faster
priority IN (Highest, High, Medium)
```

### Optimize OR vs AND

**AND in sub-clauses, OR in main clauses:**
```jql
# Good - OR in main clause
(project = PROJ1 AND status = Open) OR (project = PROJ2 AND status = "In Progress")

# Less optimal - AND in main clause with complex OR
project = PROJ1 AND (status = Open OR status = "In Progress" OR status = Blocked)
```

### Use Functions Wisely

**Expensive functions (use sparingly):**
- `linkedIssues()` - Requires multiple recursions
- `issueHistory()` - Requires history lookup
- `portfolioChildIssuesOf()` - Deep hierarchy traversal

**Efficient functions:**
- `currentUser()` - Simple lookup
- `startOfDay()`, `endOfDay()` - Date calculations
- `membersOf()` - Group membership lookup

**Best Practice:**
```jql
# Good - Simple function with indexed fields
project = PROJ AND assignee = currentUser() AND status != Done

# Less optimal - Complex function first
issuekey IN linkedIssues(PROJ-123) AND status = Open
```

### Build Queries Incrementally

Test performance by adding clauses one at a time:
```jql
# Step 1: Base query
project = PROJ

# Step 2: Add status
project = PROJ AND status = Open

# Step 3: Add assignee
project = PROJ AND status = Open AND assignee IS NOT EMPTY

# Step 4: Add labels (if slow, consider alternatives)
project = PROJ AND status = Open AND assignee IS NOT EMPTY AND labels = urgent
```

### Optimize Text Searches

**Limit text search scope:**
```jql
# Good - Specific field
summary ~ "login error"

# Less optimal - All text fields
text ~ "login error"
```

**Use exact matches when possible:**
```jql
# Good - Exact match
summary ~= "Login Bug"

# Less optimal - Contains search
summary ~ "login bug"
```

### Performance Monitoring

**Identify slow queries:**
1. Run query and note execution time
2. Add clauses one at a time
3. Identify which clause slows down the query
4. Replace or optimize that clause

**Set reasonable limits:**
```bash
# Limit results for faster queries
python jql_search.py "project = PROJ" --max-results 100
```

---

## Filter Management

### Filter Organization Strategies

**Naming Conventions:**
```
[Category] - [Purpose] - [Owner/Team]

Examples:
Sprint - Active Work - Team Alpha
Release - v2.0 Blockers - Product
Reports - Weekly Metrics - Management
Personal - My Open Issues - john.doe
Alerts - P0 Unassigned - Support
```

**Filter Categories:**
- **Personal:** Individual work filters
- **Team:** Shared team filters
- **Sprint:** Sprint-specific filters
- **Release:** Version/release tracking
- **Reports:** Metrics and dashboards
- **Alerts:** Monitoring and notifications
- **Archive:** Old but kept for reference

### Creating Effective Filters

**Good filter characteristics:**
- Clear, descriptive name
- Well-documented description
- Uses relative dates (stays current)
- Properly scoped to project/team
- Ordered results logically

**Example:**
```bash
# Create a well-structured filter
python create_filter.py \
  "Sprint - Active High Priority - Team Alpha" \
  "project = PROJ AND sprint IN openSprints() AND priority IN (Highest, High) AND status != Done ORDER BY priority DESC, created ASC" \
  --description "High priority work in current sprint for Team Alpha. Refreshed daily." \
  --favourite
```

### Filter Sharing Best Practices

**Sharing Levels:**
| Level | Use When | Example |
|-------|----------|---------|
| **Private** | Personal filters | My daily work |
| **Project** | Team collaboration | Team sprint board |
| **Group** | Department-wide | Engineering metrics |
| **Public** | Company-wide | Release status |

**Security Considerations:**
```bash
# Share with project team
python share_filter.py 10042 --project PROJ

# Share with specific role (more restrictive)
python share_filter.py 10042 --project PROJ --role Developers

# Share with group
python share_filter.py 10042 --group engineering

# Public sharing - use cautiously
python share_filter.py 10042 --global
```

**Warning:** Public filters are visible on the internet. Never share filters containing:
- Sensitive customer data
- Security issues
- Financial information
- Personal information

### Filter Maintenance

**Regular Review Schedule:**
- **Weekly:** Personal filters (update as needed)
- **Monthly:** Team filters (ensure relevance)
- **Quarterly:** Global filters (archive unused)

**Maintenance Checklist:**
- [ ] Remove filters unused for 90+ days
- [ ] Update filter descriptions
- [ ] Verify sharing permissions are correct
- [ ] Test filter performance
- [ ] Update filter names for clarity
- [ ] Archive old release/sprint filters

**Example maintenance:**
```bash
# List your filters to review
python get_filters.py --mine

# Update filter description
python update_filter.py 10042 --description "Updated: Now includes priority sorting"

# Remove outdated filter
python delete_filter.py 10045 --yes
```

### Filter Subscriptions

**Use subscriptions for:**
- Daily standup reports
- Weekly team metrics
- SLA breach alerts
- Release readiness checks

**Best practices:**
- Subscribe only relevant stakeholders
- Use descriptive email subjects
- Set appropriate frequency
- Include filter criteria in email

**Example:**
```bash
# View who's subscribed
python filter_subscriptions.py 10042
```

### Organizing with Favorites

**Favorite filters should be:**
- Used daily or weekly
- Quick access needed
- Most important to your work

**Keep favorites list short:**
- Maximum 5-10 filters
- Remove seasonal filters when done
- Update as priorities change

```bash
# Add to favorites
python favourite_filter.py 10042 --add

# Remove from favorites
python favourite_filter.py 10042 --remove
```

---

## Export & Reporting

### Choosing Export Format

| Format | Best For | File Size | Processing |
|--------|----------|-----------|------------|
| **CSV** | Excel, spreadsheets | Small | Easy |
| **JSON** | APIs, programmatic | Medium | Moderate |
| **JSON Lines** | Big data, streaming | Large | Advanced |

### CSV Export Best Practices

**Optimize field selection:**
```bash
# Good - Only needed fields
python export_results.py "project = PROJ" \
  --output report.csv \
  --fields key,summary,status,priority,assignee,created

# Less optimal - All fields (slower, larger)
python export_results.py "project = PROJ" --output report.csv
```

**Common field combinations:**
```bash
# Bug report
--fields key,summary,priority,status,assignee,created,resolved

# Sprint report
--fields key,summary,status,assignee,Story Points,sprint

# Time tracking
--fields key,summary,Time Spent,Original Estimate,Remaining Estimate

# Release report
--fields key,summary,fixVersion,status,priority,assignee
```

### Large Dataset Export

**Size guidelines:**
| Result Count | Method | Estimated Time |
|--------------|--------|---------------|
| < 100 | `export_results.py` | < 5 seconds |
| 100-1000 | `export_results.py` | 5-30 seconds |
| 1000-5000 | `export_results.py` with field limit | 30s-2min |
| 5000-50000 | `streaming_export.py` with checkpoints | 2-20 minutes |
| > 50000 | Split by date ranges | 20+ minutes |

**Streaming export for large datasets:**
```bash
# Basic streaming export
python streaming_export.py "project = PROJ" --output report.csv

# With checkpoints (resumable)
python streaming_export.py "project = PROJ" \
  --output report.csv \
  --enable-checkpoint

# Resume interrupted export
python streaming_export.py --resume export-20251226-143022

# List pending exports
python streaming_export.py --list-checkpoints
```

### Optimizing Export Performance

**1. Split by date ranges:**
```bash
# Export by quarter
python export_results.py "project = PROJ AND created >= 2025-01-01 AND created < 2025-04-01" \
  --output q1-2025.csv

python export_results.py "project = PROJ AND created >= 2025-04-01 AND created < 2025-07-01" \
  --output q2-2025.csv
```

**2. Limit fields:**
```bash
# Minimal export (faster)
python export_results.py "project = PROJ" \
  --output minimal.csv \
  --fields key,summary,status \
  --max-results 10000
```

**3. Use JSON Lines for processing:**
```bash
# Export to JSONL
python streaming_export.py "project = PROJ" \
  --output data.jsonl \
  --format jsonl

# Process with jq
cat data.jsonl | jq -r 'select(.priority == "High") | .key'
```

### Export for Reporting

**Weekly team report:**
```bash
python export_results.py \
  "project = PROJ AND resolved >= startOfWeek() AND resolved <= endOfWeek()" \
  --output weekly-completed.csv \
  --fields key,summary,type,assignee,resolved
```

**Sprint retrospective data:**
```bash
python export_results.py \
  "sprint = 'Sprint 42'" \
  --output sprint-42-all.csv \
  --fields key,summary,status,Story Points,assignee,created,resolved
```

**Bug analysis:**
```bash
python export_results.py \
  "project = PROJ AND type = Bug AND created >= -30d" \
  --output monthly-bugs.csv \
  --fields key,summary,priority,status,component,created,resolved,Time Spent
```

**Release tracking:**
```bash
python export_results.py \
  "fixVersion = 'v2.0' AND status NOT IN (Done, Closed)" \
  --output release-2.0-remaining.csv \
  --fields key,summary,priority,status,assignee,Story Points
```

### Scheduled Exports

**Automate with cron:**
```bash
# Add to crontab
# Daily export at 6 AM
0 6 * * * cd /path/to/scripts && python export_results.py "project = PROJ AND updated >= -1d" --output /reports/daily-$(date +\%Y\%m\%d).csv

# Weekly export on Monday at 8 AM
0 8 * * 1 cd /path/to/scripts && python export_results.py "project = PROJ AND resolved >= startOfWeek()" --output /reports/weekly-$(date +\%Y-W\%V).csv
```

---

## Common Pitfalls

### Syntax Errors

| Mistake | Problem | Solution |
|---------|---------|----------|
| `status = In Progress` | Space in value | `status = "In Progress"` |
| `assignee = null` | Wrong null syntax | `assignee IS EMPTY` |
| `created = -7d` | Wrong operator | `created >= -7d` |
| `and status = Open` | Lowercase operator | `AND status = Open` |
| `summary contains "error"` | Wrong operator | `summary ~ "error"` |

### Logic Errors

**Ambiguous precedence:**
```jql
# Ambiguous - What gets grouped?
status = Open OR status = "In Progress" AND priority = High

# Clear - Use parentheses
(status = Open OR status = "In Progress") AND priority = High
```

**Empty result sets:**
```jql
# Problem - Contradictory conditions
status = Done AND status = Open

# Solution - Use OR for alternatives
status = Done OR status = Open

# Problem - Too restrictive
project = PROJ AND sprint IN openSprints() AND status = Done AND created >= -1d

# Solution - Remove unnecessary constraints
project = PROJ AND sprint IN openSprints() AND status = Done
```

### Performance Pitfalls

**1. Scanning all issues:**
```jql
# Slow - No project filter
assignee = currentUser()

# Faster - Project scoped
project IN (PROJ1, PROJ2) AND assignee = currentUser()
```

**2. Using negations:**
```jql
# Slow - Multiple negations
status != Done AND status != Closed AND status != Resolved

# Faster - Positive list
status IN (Open, "In Progress", "To Do", Blocked)
```

**3. Text search on all fields:**
```jql
# Slow - Searches all text fields
text ~ "error message"

# Faster - Specific field
summary ~ "error message" OR description ~ "error message"
```

**4. Complex functions first:**
```jql
# Slow - Function first
issuekey IN linkedIssues(PROJ-123) AND project = PROJ

# Faster - Indexed field first
project = PROJ AND issuekey IN linkedIssues(PROJ-123)
```

### Historical Query Pitfalls

**Using WAS on unsupported fields:**
```jql
# Doesn't work - Labels don't support WAS
labels WAS urgent

# Alternative - Use CHANGED
labels IN (urgent) AND labels CHANGED
```

**Confusing WAS and CHANGED:**
```jql
# WAS - Returns issues that currently have OR ever had value
status WAS "In Progress"

# CHANGED - Returns issues that had value but changed from it
status CHANGED FROM "In Progress"
```

### Filter Management Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Filter sprawl** | Too many filters | Regular cleanup, naming conventions |
| **Absolute dates** | Becomes outdated | Use relative dates: `created >= -7d` |
| **Over-sharing** | Security risk | Share only what's necessary |
| **No description** | Unclear purpose | Always add descriptions |
| **Long names** | Hard to find | Keep names concise |

### Export Pitfalls

**1. Exporting all fields:**
```bash
# Slow and large
python export_results.py "project = PROJ" --output big.csv

# Faster and smaller
python export_results.py "project = PROJ" \
  --output optimized.csv \
  --fields key,summary,status
```

**2. No pagination limit:**
```bash
# Can timeout on large projects
python export_results.py "project = PROJ" --output all.csv

# Better - Set reasonable limit
python export_results.py "project = PROJ" \
  --output sample.csv \
  --max-results 5000
```

**3. Not using checkpoints:**
```bash
# Risk losing all progress if interrupted
python streaming_export.py "project = PROJ" --output huge.csv

# Better - Enable checkpoints
python streaming_export.py "project = PROJ" \
  --output huge.csv \
  --enable-checkpoint
```

### Common Query Mistakes

**Forgetting quotes for multi-word values:**
```jql
# Wrong
status = In Progress

# Right
status = "In Progress"
```

**Using = instead of ~ for text search:**
```jql
# Wrong - Exact match only
summary = "login"

# Right - Contains match
summary ~ "login"
```

**Date comparison errors:**
```jql
# Wrong - Creates date in future
created >= -7d

# This is correct - created date is greater than or equal to 7 days ago
created >= -7d

# For "created within last 7 days", use:
created >= -7d

# For "older than 7 days", use:
created <= -7d
```

**Custom field syntax:**
```jql
# Wrong - No quotes
Story Points > 5

# Right - Quote custom field names
"Story Points" > 5
```

---

## Quick Reference Card

### Most Useful Operators

```jql
=           equals
!=          not equals
~           contains text
IN          in list
IS EMPTY    no value
WAS         historical value
CHANGED     field changed
>=          greater than or equal
ORDER BY    sort results
```

### Essential Functions

```jql
currentUser()           # Logged-in user
membersOf("group")      # Group members
startOfDay()            # Today 00:00
startOfWeek()           # This Monday
startOfMonth()          # This month start
now()                   # Current time
-7d                     # 7 days ago
-1w                     # 1 week ago
openSprints()           # Active sprints
linkedIssues(KEY)       # Linked issues
```

### Daily Queries

```jql
# My work today
assignee = currentUser() AND updated >= startOfDay()

# Team's active sprint
project = PROJ AND sprint IN openSprints() AND status != Done

# High priority unassigned
project = PROJ AND priority IN (Highest, High) AND assignee IS EMPTY

# Overdue issues
duedate < now() AND status NOT IN (Done, Closed)

# Recent bugs
type = Bug AND created >= -7d ORDER BY priority DESC
```

### Performance Checklist

- [ ] Specify project explicitly
- [ ] Use indexed fields (project, status, assignee)
- [ ] Avoid negations (!=, NOT)
- [ ] Limit text searches to specific fields
- [ ] Use positive conditions over negations
- [ ] Add parentheses for complex logic
- [ ] Test incrementally when building complex queries

### Export Quick Commands

```bash
# Small export (< 1000 issues)
python export_results.py "JQL_QUERY" --output report.csv

# Large export (> 5000 issues)
python streaming_export.py "JQL_QUERY" \
  --output report.csv \
  --enable-checkpoint

# Minimal fields export
python export_results.py "JQL_QUERY" \
  --output report.csv \
  --fields key,summary,status
```

### Filter Management Commands

```bash
# Create filter
python create_filter.py "Filter Name" "JQL_QUERY" --favourite

# List my filters
python get_filters.py --mine

# Share filter
python share_filter.py FILTER_ID --project PROJ

# Run filter
python run_filter.py --name "Filter Name"

# Update filter
python update_filter.py FILTER_ID --jql "NEW_JQL"

# Delete filter
python delete_filter.py FILTER_ID
```

### Common Field Names

```
project                 # Project key
issuetype, type        # Issue type
status                 # Current status
priority               # Priority level
assignee               # Assigned user
reporter               # Reporter
created                # Creation date
updated                # Last update
resolved               # Resolution date
duedate                # Due date
labels                 # Labels
component              # Component
fixVersion             # Fix version
sprint                 # Sprint
"Story Points"         # Story points (custom field)
```

### Keyboard Shortcuts for JQL

While editing JQL in JIRA web UI:
- `Ctrl + Space` - Autocomplete
- `Tab` - Cycle through suggestions
- `Enter` - Run query
- `Ctrl + Enter` - New line (for complex queries)

---

## Additional Resources

### Official Documentation
- [Atlassian JQL Guide](https://www.atlassian.com/software/jira/guides/jql/overview)
- [JQL Cheat Sheet](https://www.atlassian.com/software/jira/guides/jql/cheat-sheet)
- [JQL Operators Reference](https://support.atlassian.com/jira-software-cloud/docs/jql-operators/)
- [JQL Optimization Recommendations](https://support.atlassian.com/jira-software-cloud/docs/jql-optimization-recommendations/)

### Internal Documentation
- `jql_reference.md` - Complete JQL syntax reference
- `search_examples.md` - Practical query examples
- `SKILL.md` - Skill capabilities and script reference

### Tools
- `jql_fields.py` - List available fields
- `jql_functions.py` - List available functions
- `jql_validate.py` - Validate JQL syntax
- `jql_interactive.py` - Interactive query builder
- `jql_history.py` - Save and reuse queries

---

*Last updated: December 2025*
*Based on JIRA Cloud API and best practices*

## Sources

This guide was compiled from the following sources:
- [Use advanced search with Jira Query Language (JQL) | Atlassian Support](https://support.atlassian.com/jira-service-management-cloud/docs/use-advanced-search-with-jira-query-language-jql/)
- [JQL Cheat Sheet | Atlassian](https://www.atlassian.com/software/jira/guides/jql/cheat-sheet)
- [Advanced JQL Tips and Best Practices | University of Waterloo](https://uwaterloo.ca/atlassian/blog/advanced-jql-tips-and-best-practices)
- [Master Jira Query Language (JQL): A Comprehensive Guide](https://www.salto.io/blog-posts/jira-jql-guide)
- [JQL operators | Jira Cloud | Atlassian Support](https://support.atlassian.com/jira-software-cloud/docs/jql-operators/)
- [Jira History Searches: When JQL Works & When Doesn't | SaaSJet](https://saasjet.com/blog/jira-history-searches-when-jql-works-when-doesnt/)
- [JQL optimization recommendations | Atlassian Support](https://support.atlassian.com/jira-software-cloud/docs/jql-optimization-recommendations/)
- [Manage filters | Atlassian Support](https://support.atlassian.com/jira-software-cloud/docs/manage-filters/)
