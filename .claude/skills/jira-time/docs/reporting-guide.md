# Time Reporting and Analytics Guide

Comprehensive guidance on built-in JIRA reports, command-line reporting, export formats, dashboards, and advanced JQL queries for time data.

---

## Use this guide if you...

- Need to generate time reports for projects or users
- Want to export timesheets to CSV or JSON
- Are building dashboards for time tracking visibility
- Need advanced JQL queries for time-based filtering
- Create client or management reports

For billing-specific reports, see [Billing Integration Guide](billing-integration.md).
For team policy reporting, see [Team Policies](team-policies.md).

---

## Table of Contents

1. [Built-in JIRA Reports](#built-in-jira-reports)
2. [Command-Line Reporting](#command-line-reporting)
3. [Export Formats](#export-formats)
4. [Client Reporting Templates](#client-reporting-templates)
5. [Dashboard Widgets](#dashboard-widgets)
6. [Advanced JQL for Time Queries](#advanced-jql-for-time-queries)

---

## Built-in JIRA Reports

### Time Tracking Report (Project-Level)

**Access:** Project sidebar > Reports > Time Tracking Report

**Shows:**
- Original estimate vs time spent per issue
- Remaining estimate
- Accuracy of estimates
- Issues over/under estimated

**Use for:**
- Sprint retrospectives (estimate accuracy)
- Identifying estimation patterns
- Capacity planning

### Worklog Report (Issue-Level)

**Access:** Issue detail > Worklogs tab

**Shows:**
- All worklog entries for an issue
- Who logged time
- When work was done
- Time per entry

**Use for:**
- Detailed task breakdown
- Verifying time entries
- Audit trail

### Sprint Report (Agile)

**Access:** Board > Reports > Sprint Report

**Shows:**
- Completed vs incomplete work
- Story points and time breakdown
- Scope changes during sprint

**Use for:**
- Sprint velocity tracking
- Commitment vs delivery analysis

---

## Command-Line Reporting

### User Time Reports

```bash
# My time for last week
python time_report.py \
  --user currentUser() \
  --period last-week

# Specific user for this month
python time_report.py \
  --user "john.doe@company.com" \
  --period this-month

# Multiple users (via JQL)
python time_report.py \
  --jql "worklogAuthor in (john, jane)" \
  --period this-week
```

### Project Time Reports

```bash
# Project total for this month
python time_report.py \
  --project ACME \
  --period this-month

# Group by user to see team breakdown
python time_report.py \
  --project ACME \
  --period this-month \
  --group-by user

# Group by issue for detailed breakdown
python time_report.py \
  --project ACME \
  --period this-month \
  --group-by issue
```

### Custom Date Ranges

```bash
# Specific date range
python time_report.py \
  --project ACME \
  --since 2025-01-01 \
  --until 2025-01-31

# Quarter report
python time_report.py \
  --project ACME \
  --since 2025-01-01 \
  --until 2025-03-31 \
  --group-by day
```

### Report Period Options

| Period | Description |
|--------|-------------|
| `today` | Current day only |
| `this-week` | Monday to today |
| `last-week` | Previous Monday to Sunday |
| `this-month` | 1st of month to today |
| `last-month` | Previous full month |
| `2025-01` | Specific month |
| Custom | Use `--since` and `--until` |

---

## Export Formats

### CSV for Spreadsheet Analysis

```bash
# Export to CSV
python time_report.py \
  --project ACME \
  --period this-month \
  --output csv > report.csv

# CSV columns:
# Issue Key, Issue Summary, Author, Date, Time Spent, Seconds
```

**Excel/Google Sheets analysis:**
1. Import CSV
2. Create pivot tables (user x project)
3. Calculate totals and averages
4. Generate charts (time by user, by day)

### JSON for Custom Processing

```bash
# Export to JSON for custom scripts
python time_report.py \
  --project ACME \
  --period this-month \
  --output json > report.json

# Process with jq
cat report.json | jq '.entries[] | select(.author == "John Doe")'

# Calculate total hours with jq
cat report.json | jq '[.entries[].seconds] | add / 3600'
```

### Detailed Export with Issue Fields

```bash
# Include issue details in export
python time_report.py \
  --project ACME \
  --period this-month \
  --output csv \
  --include-issue-details > detailed-report.csv

# Additional columns: Status, Priority, Component, Epic
```

---

## Client Reporting Templates

### Weekly Client Status Report

```markdown
# Client: ACME Corp
# Week: January 15-21, 2025

## Time Summary
Total Hours: 32h
- Development: 24h
- Meetings: 4h
- Testing: 4h

## Work Completed
- [ACME-123] User authentication (8h) - Complete
- [ACME-124] Payment integration (12h) - In progress
- [ACME-125] Dashboard widgets (4h) - Complete

## Upcoming Work
- [ACME-124] Payment integration (4h remaining)
- [ACME-126] Reporting module (est. 16h)
```

**Generate data:**
```bash
python time_report.py --project ACME --period this-week --group-by issue
```

### Monthly Invoice Report

```markdown
# Invoice: ACME Corp - January 2025

## Summary
Total Hours: 128h
Rate: $150/hour
Total Amount: $19,200

## Breakdown by Task
| Issue | Description | Hours | Amount |
|-------|-------------|-------|--------|
| ACME-123 | Authentication system | 24h | $3,600 |
| ACME-124 | Payment gateway | 32h | $4,800 |
| ACME-125 | Admin dashboard | 40h | $6,000 |
| ACME-126 | Reporting module | 32h | $4,800 |
```

**Generate data:**
```bash
python time_report.py \
  --project ACME \
  --since 2025-01-01 \
  --until 2025-01-31 \
  --group-by issue \
  --output csv
```

### Team Utilization Report

```markdown
# Team Utilization - January 2025

## Summary
Team Capacity: 800h (5 people x 160h)
Time Logged: 720h
Utilization: 90%

## By Team Member
| Member | Hours | Utilization | Billable |
|--------|-------|-------------|----------|
| Alice | 152h | 95% | 140h |
| Bob | 144h | 90% | 120h |
| Carol | 160h | 100% | 155h |
| David | 128h | 80% | 100h |
| Eve | 136h | 85% | 130h |
```

**Generate data:**
```bash
python time_report.py \
  --project ACME \
  --period this-month \
  --group-by user \
  --output csv
```

---

## Dashboard Widgets

### Recommended Gadgets for Time Tracking Dashboard

**1. Time Since Chart**
- Shows time logged over sprint/period
- Compares planned vs actual
- Identifies over/under utilization

**2. Workload Pie Chart**
- Breakdown by assignee
- Shows team distribution
- Identifies bottlenecks

**3. Filter Results**
- Saved filter: "Logged time this week"
- Quick access to time entries
- Shows issues with recent worklogs

**4. Time Tracking Report**
- Estimate accuracy
- Remaining work
- At-risk issues

### Dashboard Configuration

**Team Time Tracking Dashboard:**
```
Layout:
+---------------------------+---------------------------+
| Time Logged This Week     | Team Workload             |
| (Pie Chart)               | (Bar Chart by User)       |
+---------------------------+---------------------------+
| Issues In Progress        | Estimate Accuracy         |
| (Filter Results)          | (Time Tracking Report)    |
+---------------------------+---------------------------+
| Recent Worklogs           | At-Risk Issues            |
| (Activity Stream)         | (Over Estimate Filter)    |
+---------------------------+---------------------------+
```

**Saved Filters for Dashboard:**
```jql
# Issues with time logged this week
worklogDate >= startOfWeek()

# In progress with no recent time
status = "In Progress" AND worklogDate <= -3d

# Over estimate by >50%
timespent > originalEstimate * 1.5

# My work this sprint
assignee = currentUser() AND sprint in openSprints()
```

---

## Advanced JQL for Time Queries

### Time-Based JQL Queries

```jql
# Issues with no time logged but in progress
status = "In Progress" AND timespent IS EMPTY

# Issues over original estimate
timeestimate < timespent

# Issues with time logged today
worklogDate = startOfDay()

# Issues with time logged by specific user this week
worklogAuthor = currentUser()
AND worklogDate >= startOfWeek()

# Issues with significant time (>1 day)
timespent >= 28800  # 28800 seconds = 8 hours
```

### Combining Time and Status

```jql
# In progress but no recent time logged
status = "In Progress"
AND worklogDate <= -7d

# Done but under 1 hour logged (possible missing time)
status = Done
AND timespent < 3600

# High time but still in progress (possible blocking)
status = "In Progress"
AND timespent > 144000  # >5 days
```

### User and Team Queries

```jql
# My work with time this week
assignee = currentUser()
AND worklogDate >= startOfWeek()

# Team work with worklogs
assignee in (membersOf("developers"))
AND worklogDate >= startOfMonth()

# Unassigned but has time logged
assignee IS EMPTY
AND timespent > 0
```

### Estimate Analysis Queries

```jql
# Issues with time but no estimate
timespent > 0 AND originalEstimate IS EMPTY

# Issues over estimate by >50%
originalEstimate IS NOT EMPTY
AND timespent > originalEstimate * 1.5

# Issues under estimate by >50%
originalEstimate IS NOT EMPTY
AND timespent < originalEstimate * 0.5
AND status = Done

# Accurate estimates (within 20%)
originalEstimate IS NOT EMPTY
AND timespent >= originalEstimate * 0.8
AND timespent <= originalEstimate * 1.2
```

### Worklog-Specific Queries

```jql
# Issues with worklogs by specific user
worklogAuthor = "john.doe@company.com"

# Issues with worklogs in date range
worklogDate >= "2025-01-01"
AND worklogDate <= "2025-01-31"

# Issues with worklogs containing text
worklogComment ~ "meeting"
```

---

## Performance Tips

### Large Dataset Queries

**Problem:** Time reports on projects with thousands of issues timeout

**Solution:**
```bash
# Use smaller date ranges
python time_report.py \
  --project LARGE-PROJ \
  --since 2025-01-01 \
  --until 2025-01-07  # One week at a time

# Or filter by user
python time_report.py \
  --project LARGE-PROJ \
  --user currentUser() \
  --period this-month
```

### API Rate Limits

**Symptoms:**
- 429 Too Many Requests errors
- Slow performance

**Solution:**
```bash
# Scripts automatically retry with exponential backoff
# But you can reduce load by using smaller batches
# and filtering to specific date ranges
```

---

## Related Guides

- [IC Time Logging Guide](ic-time-logging.md) - Logging best practices
- [Billing Integration Guide](billing-integration.md) - Billing-specific reports
- [Team Policies](team-policies.md) - Compliance monitoring
- [Quick Reference: JQL Snippets](reference/jql-snippets.md) - Copy-paste queries

---

**Back to:** [SKILL.md](../SKILL.md) | [Best Practices Index](BEST_PRACTICES.md)
