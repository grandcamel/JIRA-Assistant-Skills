# JIRA Time Tracking Best Practices

Comprehensive guide to effective time tracking, worklog management, and accurate estimation in JIRA.

---

## Table of Contents

1. [Time Format Reference](#time-format-reference)
2. [Estimation Guidelines](#estimation-guidelines)
3. [Worklog Best Practices](#worklog-best-practices)
4. [Billable vs Non-Billable Tracking](#billable-vs-non-billable-tracking)
5. [Time Reporting Strategies](#time-reporting-strategies)
6. [Team Time Tracking Policies](#team-time-tracking-policies)
7. [Integration with Invoicing](#integration-with-invoicing)
8. [Accuracy Improvement Strategies](#accuracy-improvement-strategies)
9. [Common Pitfalls to Avoid](#common-pitfalls-to-avoid)
10. [Quick Reference Card](#quick-reference-card)

---

## Time Format Reference

### JIRA Time Format Syntax

JIRA accepts human-readable time formats using specific units:

| Format | Meaning | Seconds | Notes |
|--------|---------|---------|-------|
| `30m` | 30 minutes | 1,800 | Minimum unit for most tracking |
| `2h` | 2 hours | 7,200 | Standard hourly tracking |
| `1d` | 1 day | 28,800 | Default: 8 hours per day |
| `1w` | 1 week | 144,000 | Default: 5 days (40 hours) |
| `2d 4h` | 2 days 4 hours | 72,000 | Combined format |
| `1w 3d 2h 30m` | 1 week 3 days 2 hours 30 minutes | 234,000 | Full precision |

### Unit Configuration

**Default JIRA time units** (configurable by administrators):
- 1 minute = 60 seconds
- 1 hour = 60 minutes
- **1 day = 8 hours** (configurable: 6-12 hours common)
- **1 week = 5 days** (configurable: 5-7 days common)

**Note:** Always verify your organization's day/week configuration in JIRA Settings > System > Time Tracking.

### Common Time Values

| Duration | JIRA Format | Use Cases |
|----------|-------------|-----------|
| Quick fix | `15m` or `30m` | Typo fixes, config changes |
| Short task | `1h` to `2h` | Code reviews, small bugs |
| Half day | `4h` | Feature component, complex bug |
| Full day | `1d` (8h) | Full feature implementation |
| Sprint story | `2d` to `3d` | Typical user story |
| Large story | `5d` to `1w` | Complex feature with tests |

### Invalid Formats (Don't Use)

| Incorrect | Correct | Issue |
|-----------|---------|-------|
| `2 hours` | `2h` | Spaces not allowed |
| `1.5h` | `1h 30m` | Decimals not supported |
| `90 minutes` | `1h 30m` | Must use abbreviations |
| `0.5d` | `4h` | No decimal days |

---

## Estimation Guidelines

### Understanding JIRA Time Fields

JIRA uses three interconnected time tracking fields:

| Field | Purpose | When to Set | Auto-Updated |
|-------|---------|-------------|--------------|
| **Original Estimate** | Initial prediction of total effort | At issue creation or planning | No |
| **Remaining Estimate** | Time left to complete work | Updated as work progresses | Optional |
| **Time Spent** | Cumulative time logged via worklogs | When logging work | Yes |

**Relationship:**
```
Progress = Time Spent / Original Estimate
Projected Total = Time Spent + Remaining Estimate
Variance = Projected Total - Original Estimate
```

### Estimation Approaches

#### 1. Bottom-Up Estimation (Recommended)

**Best for:** Detailed planning, high accuracy requirements

**Process:**
1. Break down epics into stories
2. Break down stories into subtasks
3. Estimate only subtasks (in hours)
4. Sum subtasks for story estimate
5. Sum stories for epic estimate

**Example:**
```
Epic: User Authentication (Total: 5d)
├─ Story: Login Form (2d)
│  ├─ Subtask: Create UI component (4h)
│  ├─ Subtask: Add validation logic (3h)
│  ├─ Subtask: Write unit tests (2h)
│  └─ Subtask: Integration testing (3h)
├─ Story: Password Reset (2d)
│  └─ [Subtasks...]
└─ Story: OAuth Integration (1d)
   └─ [Subtasks...]
```

**Benefits:**
- More accurate (smaller units easier to estimate)
- Clear breakdown for developers
- Easy to track progress

#### 2. Story Point to Hours Conversion

**Best for:** Teams using Agile story points but needing time tracking for billing

**Common conversion factors:**
- 1 point = 2-4 hours (team dependent)
- 1 point = 0.5 days (common)
- 1 point = 1 day (conservative)

**Example configuration:**
```bash
# If your team's velocity is 40 points/sprint (2 weeks)
# And team capacity is 200 hours/sprint (5 people × 40h)
# Then: 1 point ≈ 5 hours

python set_estimate.py PROJ-123 --original "2d"  # For a 3-point story
```

**Important:** Track actual conversion over time and adjust based on historical data.

#### 3. T-Shirt Sizing with Hours

Map relative sizes to time ranges for quick estimation:

| Size | Story Points | Time Range | Use Case |
|------|--------------|------------|----------|
| XS | 1 | 1-2h | Trivial fix, config change |
| S | 2 | 2-4h | Small bug, simple feature |
| M | 3 | 4h-1d | Standard story |
| L | 5 | 1-2d | Complex feature |
| XL | 8 | 2-3d | Very large story (consider splitting) |
| XXL | 13+ | 1w+ | Too large - must split |

### Setting Realistic Estimates

**Do:**
- Reference historical data from similar completed issues
- Include time for testing, code review, and documentation
- Account for uncertainty (add buffer for unknowns)
- Use team's past velocity for story-level estimates
- Consider team member experience level

**Don't:**
- Use wishful thinking ("best case scenario")
- Forget non-coding activities (meetings, email, reviews)
- Estimate based on perfect conditions
- Ignore complexity multipliers (legacy code, dependencies)
- Commit to estimates under pressure without analysis

**Buffer Guidelines:**
```
Known implementation = +10% buffer
New technology/library = +30% buffer
Unclear requirements = +50% buffer
Multiple dependencies = +25% buffer
Legacy code refactoring = +40% buffer
```

### Estimate Adjustment Strategies

When logging time, you can control how JIRA updates the remaining estimate:

| Mode | Behavior | Use When | Command Example |
|------|----------|----------|-----------------|
| `auto` | Reduces remaining by time logged | Default for most workflows | `--adjust-estimate auto` |
| `leave` | Doesn't change remaining | Logging time outside issue scope | `--adjust-estimate leave` |
| `new` | Sets remaining to new value | Re-estimating after progress review | `--adjust-estimate new --new-estimate 4h` |
| `manual` | Reduces remaining by specified amount | Custom adjustment needed | `--adjust-estimate manual --reduce-by 1h` |

**Known Issue (JRACLOUD-67539):** JIRA Cloud has a bug where estimates may not update correctly. Workaround:
```bash
# Set both estimates together
python set_estimate.py PROJ-123 --original "2d" --remaining "1d 4h"
```

---

## Worklog Best Practices

### When to Log Time

#### Daily Logging (Strongly Recommended)

**Why daily:**
- Highest accuracy (details fresh in memory)
- Prevents forgotten activities
- Enables real-time reporting
- Reduces end-of-week rush

**Daily routine:**
```bash
# End-of-day workflow (5 minutes)
# 1. Review what you worked on today
# 2. Log time to each issue

python add_worklog.py PROJ-123 --time 3h --comment "Implemented authentication API"
python add_worklog.py PROJ-124 --time 2h --comment "Code review for payment feature"
python add_worklog.py PROJ-125 --time 1h 30m --comment "Sprint planning meeting"
python add_worklog.py PROJ-126 --time 1h --comment "Debugging production issue"
```

#### Task Completion Logging (Acceptable)

Log time immediately when finishing each task:
```bash
# Right after completing a task
python add_worklog.py PROJ-123 --time 2h 15m --comment "Fixed login timeout bug"
```

**Benefits:**
- Still accurate (task context fresh)
- Natural workflow integration
- Clear task boundaries

#### Weekly Logging (Not Recommended)

**Problems with weekly logging:**
- 40-60% higher inaccuracy rate
- Forgotten activities (meetings, interruptions)
- Difficulty reconstructing task details
- Poor data for reporting and billing

**If forced to use weekly:** Keep detailed daily notes to reference when logging.

### Writing Effective Worklog Comments

#### Good Worklog Comment Patterns

**Descriptive and specific:**
| Comment | Quality | Reason |
|---------|---------|--------|
| "Code review for PR #234 - authentication module" | Excellent | Specific, traceable, informative |
| "Debugging production timeout issue in payment API" | Excellent | Clear problem, context provided |
| "Sprint planning - prioritized backlog items" | Good | Activity and outcome clear |
| "Research OAuth 2.0 libraries for integration" | Good | Task and purpose clear |
| "Pair programming with Sarah on data migration" | Good | Activity and collaboration noted |

**Poor worklog comments to avoid:**
| Comment | Quality | Problem |
|---------|---------|---------|
| "Work" | Bad | No information |
| "" (empty) | Bad | Completely useless |
| "Stuff" | Bad | Vague, no context |
| "Meeting" | Poor | Which meeting? What outcome? |
| "Coding" | Poor | Expected - what specifically? |

#### Worklog Comment Templates

**Development work:**
```
Implemented [feature/component]: [brief description]
Fixed [issue/bug]: [root cause]
Refactored [component] to [improvement]
Added [tests/documentation] for [feature]
```

**Collaboration:**
```
Code review for PR #[number] - [component]
Pair programming with [person] on [task]
Knowledge sharing session: [topic]
Design discussion: [feature/decision]
```

**Meetings:**
```
Sprint planning - [key outcomes]
Daily standup - [blockers discussed]
Retrospective - [action items]
Client meeting - [requirements clarified]
```

**Research/Learning:**
```
Research [technology/approach] for [use case]
Spike: Investigating [options] for [problem]
Learning [skill/tool] for [upcoming task]
```

### Worklog Visibility and Security

Control who can see sensitive time entries:

```bash
# Restrict to project role
python add_worklog.py PROJ-123 --time 2h \
  --comment "Security vulnerability fix" \
  --visibility-type role --visibility-value Administrators

# Restrict to user group
python add_worklog.py PROJ-124 --time 3h \
  --comment "Confidential client feature" \
  --visibility-type group --visibility-value senior-developers
```

**Use cases:**
- Security work (limit to security team)
- Client-confidential projects
- Executive/strategic planning time
- Sensitive HR or legal matters

### Handling Special Time Entries

#### Non-Issue Time

**Problem:** Meetings, email, admin work don't map to specific issues.

**Solutions:**

**Option 1: Create "overhead" issues**
```bash
# Create issues for recurring activities
PROJ-999: "Team Meetings"
PROJ-998: "Email & Communication"
PROJ-997: "Administrative Tasks"

python add_worklog.py PROJ-999 --time 1h --comment "Daily standup"
python add_worklog.py PROJ-998 --time 30m --comment "Customer support emails"
```

**Option 2: Distribute proportionally to project issues**
```bash
# If you spent 6h on PROJ-123 and 1h in meetings about it
python add_worklog.py PROJ-123 --time 6h --comment "Feature implementation"
python add_worklog.py PROJ-123 --time 1h --comment "Planning meeting for this feature"
```

#### Retroactive Time Logging

Log time for past dates using `--started`:

```bash
# Log yesterday's work
python add_worklog.py PROJ-123 --time 4h \
  --started yesterday \
  --comment "Work from previous day (was out sick)"

# Log specific date
python add_worklog.py PROJ-123 --time 3h \
  --started "2025-01-20" \
  --comment "Retroactive entry for Monday"
```

**Best practices:**
- Add note explaining retroactive entry
- Don't go back more than 1 week
- Ensure date falls within reporting period

#### Interrupted Work

When logging interrupted or partial work:

```bash
# Log work even if task incomplete
python add_worklog.py PROJ-123 --time 2h \
  --comment "Partial work on authentication - interrupted by production issue" \
  --adjust-estimate leave  # Don't reduce remaining estimate

# Log interruption work
python add_worklog.py PROD-456 --time 1h \
  --comment "Emergency production fix - database connection pool exhausted"
```

---

## Billable vs Non-Billable Tracking

### Native JIRA Limitations

**Important:** JIRA's native time tracking has **no built-in concept of billable/non-billable hours**. All worklogs are treated equally.

**Workarounds:**

#### 1. Use Labels for Billable Tracking

```bash
# Create issues with billable labels
python create_issue.py --summary "Client feature X" \
  --labels billable,client-acme

python create_issue.py --summary "Internal refactoring" \
  --labels non-billable,tech-debt

# Search for billing reports
python jql_search.py "labels = billable AND timespent > 0"
```

**Pros:** Simple, no cost
**Cons:** Manual, no rate tracking, basic reporting

#### 2. Use Components for Client Separation

```bash
# Create components per client
Components: "Client-ACME", "Client-TechCorp", "Internal"

# Search for client time
python jql_search.py "component = 'Client-ACME' AND timespent > 0"
```

**Pros:** Natural project organization
**Cons:** No billable/non-billable distinction within client

#### 3. Separate Projects for Billable Work

```
Project Structure:
├─ ACME-BILL (billable client work)
├─ ACME-INT (internal/non-billable)
├─ TECH-BILL (billable client work)
└─ INTERNAL (company internal work)
```

**Pros:** Clear separation, easy reporting
**Cons:** More projects to manage, overhead

#### 4. Custom Field for Billable Flag

**Admin setup:**
1. Create custom field "Billable" (Yes/No checkbox)
2. Add to issue screens
3. Set default to "No" for safety

**Usage:**
```bash
# Mark issue as billable when creating
python create_issue.py --summary "Client feature" \
  --custom-field "Billable" "Yes"

# Search for billable time
python jql_search.py "Billable = Yes AND timespent > 0"
```

**Pros:** Explicit billable flag, queryable
**Cons:** Requires admin setup, no hourly rates

### Billable Hours Reporting Patterns

#### Export for Invoicing

```bash
# Generate billable time report for client
python time_report.py \
  --project ACME \
  --period this-month \
  --output csv > acme-invoice-2025-01.csv

# Filter by user for contractor billing
python time_report.py \
  --user "contractor@example.com" \
  --period this-month \
  --output json > contractor-hours.json
```

#### Common Report Queries

```jql
# All billable time this month
project = ACME AND labels = billable
AND created >= startOfMonth()
AND timespent > 0

# Unbilled work (no invoice label)
project = ACME AND labels = billable
AND labels != invoiced-2025-01
AND timespent > 0

# By component (client)
component in ("Client-ACME", "Client-TechCorp")
AND timespent > 0
AND created >= "2025-01-01"
```

### Third-Party Tools for Advanced Billing

If you need professional invoicing, consider these JIRA marketplace apps:

| Tool | Key Features | Best For |
|------|--------------|----------|
| **Tempo Timesheets** | Billable/non-billable accounts, billing rates, invoice generation | Enterprise billing |
| **Everhour** | Per-project rates, client invoicing, export to accounting | Small-medium teams |
| **ActivityTimeline** | Timesheet approvals, billing reports, budget tracking | Teams needing approvals |
| **Clerk Invoices** | QuickBooks/Xero integration, invoice templates | Accounting integration |
| **Clockwork** | Tags for billable tracking, client reports | Simple billable tracking |

**Features to look for:**
- Billable/non-billable worklog tagging
- Hourly rate configuration (per user, per project)
- Invoice generation (PDF export)
- Accounting software integration
- Budget tracking and alerts
- Approval workflows

---

## Time Reporting Strategies

### Built-in JIRA Reports

#### 1. Time Tracking Report (Project-Level)

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

#### 2. Worklog Report (Issue-Level)

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

### Command-Line Reporting

#### User Time Reports

```bash
# My time for last week
python time_report.py \
  --user currentUser() \
  --period last-week

# Specific user for this month
python time_report.py \
  --user "john.doe@company.com" \
  --period this-month
```

#### Project Time Reports

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
```

#### Custom Date Ranges

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

### Export Formats

#### CSV for Spreadsheet Analysis

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
2. Create pivot tables (user × project)
3. Calculate totals and averages
4. Generate charts (time by user, by day)

#### JSON for Custom Processing

```bash
# Export to JSON for custom scripts
python time_report.py \
  --project ACME \
  --period this-month \
  --output json > report.json

# Process with jq
cat report.json | jq '.entries[] | select(.author == "John Doe")'
```

### Client Reporting Templates

#### Weekly Client Status Report

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

#### Monthly Invoice Report

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

### Dashboard Widgets

**Recommended gadgets for time tracking dashboard:**

1. **Time Since Chart**
   - Shows time logged over sprint/period
   - Compares planned vs actual
   - Identifies over/under utilization

2. **Workload Pie Chart**
   - Breakdown by assignee
   - Shows team distribution
   - Identifies bottlenecks

3. **Filter Results**
   - Saved filter: "Logged time this week"
   - Quick access to time entries
   - Shows issues with recent worklogs

4. **Time Tracking Report**
   - Estimate accuracy
   - Remaining work
   - At-risk issues

### Advanced Reporting with JQL

#### Time-Based JQL Queries

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

#### Combining Time and Status

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

---

## Team Time Tracking Policies

### Establishing Team Policies

#### Sample Policy Document

```markdown
# Time Tracking Policy - Engineering Team

## Purpose
Accurate time tracking enables:
- Project cost estimation and budgeting
- Client billing and invoicing
- Resource capacity planning
- Process improvement

## Requirements

### Daily Time Logging
- Log time daily, before end of business day
- Minimum: All project work >15 minutes
- Include brief descriptive comment for each entry

### Accuracy
- Log actual time spent, not estimates
- Round to nearest 15-minute increment
- Include all work: coding, testing, meetings, reviews

### Billable vs Non-Billable
- Client project work: Always billable (label: billable)
- Internal tools/infrastructure: Non-billable (label: non-billable)
- Training/learning: Non-billable
- Administrative: Non-billable

### Deadlines
- Daily: Log time by 6 PM same day (preferred)
- Weekly: All time logged by Friday 5 PM
- Monthly: Finalize all time by 2nd business day of new month

## Consequences
- Weekly reminder for incomplete logging
- Manager review for repeated non-compliance
- May affect billable utilization metrics
```

### Onboarding New Team Members

**Week 1 checklist:**
- [ ] JIRA account created with time tracking permissions
- [ ] Time tracking policy document reviewed
- [ ] Training session on worklog scripts completed
- [ ] Practice logging time on training tasks
- [ ] Assigned "time tracking buddy" for questions

**Training script walkthrough:**
```bash
# Day 1: Basic time logging
python add_worklog.py TRAIN-1 --time 2h --comment "JIRA onboarding training"

# Day 2: Time with estimates
python set_estimate.py TRAIN-2 --original "1d"
python add_worklog.py TRAIN-2 --time 4h --comment "Setting up development environment"

# Day 3: Reports
python time_report.py --user currentUser() --period this-week

# Day 4: Corrections
python get_worklogs.py TRAIN-2
python delete_worklog.py TRAIN-2 --worklog-id 12345 --dry-run
```

### Permission Configuration

**Recommended JIRA permission scheme:**

| Permission | User Role | Reason |
|------------|-----------|--------|
| **Work on Issues** | All team members | Log own time |
| **Edit Own Worklogs** | All team members | Fix own mistakes |
| **Edit All Worklogs** | Team leads, Managers | Correct team entries |
| **Delete Own Worklogs** | All team members | Remove incorrect entries |
| **Delete All Worklogs** | Managers only | Prevent data loss |

**Setup via JIRA Admin:**
```
Settings > Issues > Permission Schemes >
  [Your Scheme] > Time Tracking Permissions
```

### Monitoring and Enforcement

#### Weekly Compliance Report

```bash
# Find users who haven't logged time this week
python jql_search.py \
  "worklogAuthor = currentUser() AND worklogDate >= startOfWeek()" \
  --output json | \
  jq '.issues | length'

# Find issues in progress with no time logged
python jql_search.py \
  "status = 'In Progress' AND timespent IS EMPTY"
```

#### Monthly Audit

```jql
# Issues with time logged but no estimate
timespent > 0 AND originalEstimate IS EMPTY

# Issues with estimate but no time logged
originalEstimate IS NOT EMPTY AND timespent IS EMPTY
AND status != "To Do"

# Issues logged to but not assigned
worklogDate >= startOfMonth() AND assignee IS EMPTY
```

### Handling Non-Compliance

**Progressive approach:**

**Level 1: Gentle reminder (automated)**
- Slack/email: "Reminder: Log your time daily"
- Frequency: Weekly if <80% compliance

**Level 2: Manager 1-on-1**
- Discuss barriers to logging time
- Provide additional training if needed
- Set improvement plan

**Level 3: Formal process**
- Document repeated non-compliance
- May affect performance review
- Require daily confirmation

**Note:** Focus on education and process improvement, not punishment.

---

## Integration with Invoicing

### Export for Billing Systems

#### QuickBooks Integration

```bash
# Export timesheet for QuickBooks import
python export_timesheets.py \
  --project ACME \
  --period 2025-01 \
  --format quickbooks \
  --output acme-timesheet.csv

# QuickBooks CSV format:
# Date, Employee, Customer, Service Item, Hours, Notes
```

#### Generic Accounting Export

```bash
# Standard CSV for import
python time_report.py \
  --project ACME \
  --since 2025-01-01 \
  --until 2025-01-31 \
  --output csv > timesheet.csv

# Add hourly rate column in spreadsheet
# Calculate: Hours × Rate = Amount
```

### Invoice Preparation Workflow

#### Step 1: Identify Unbilled Work

```jql
# Work logged but not yet invoiced
project = ACME
AND labels = billable
AND labels != invoiced-2025-01
AND timespent > 0
ORDER BY created ASC
```

#### Step 2: Generate Time Report

```bash
# Export unbilled time
python time_report.py \
  --project ACME \
  --period 2025-01 \
  --group-by issue \
  --output csv > unbilled-work.csv
```

#### Step 3: Review and Validate

```bash
# Check for issues:
# - Missing descriptions
# - Unusual time amounts
# - Wrong project/component

python get_worklogs.py ACME-123
```

#### Step 4: Create Invoice

**Manual process:**
1. Import CSV to invoice template
2. Apply hourly rates
3. Calculate totals
4. Add client-specific formatting

**Automated with Tempo/Everhour:**
1. Mark period for invoicing
2. Generate invoice in-app
3. Export PDF
4. Send to client

#### Step 5: Mark as Invoiced

```bash
# Bulk add invoice label to prevent double-billing
python bulk_update.py \
  --jql "project = ACME AND labels = billable AND labels != invoiced-2025-01" \
  --add-label "invoiced-2025-01"
```

### Handling Client Disputes

**Common scenarios:**

**"These hours seem high"**
- Provide worklog detail report with descriptions
- Show breakdown by task/feature
- Compare to original estimate

**"We didn't authorize this work"**
- Check issue for client approval comments
- Verify work was in scope
- Review change request process

**"What did you do during these hours?"**
- Export worklogs with comments
- Provide detailed task descriptions
- Link to code commits/PRs if available

**Prevention:**
```bash
# Enforce worklog comments
# All worklogs should explain what was done

python add_worklog.py ACME-123 --time 4h \
  --comment "Implemented user authentication flow per requirements in PRD-2025-01"
```

### Retainer and Fixed-Fee Projects

**Retainer tracking:**
```bash
# Track hours against monthly retainer
python time_report.py \
  --project ACME \
  --period this-month \
  --group-by user

# Compare to retainer allocation (e.g., 80 hours/month)
# Alert when approaching limit
```

**Fixed-fee projects:**
```bash
# Track internal hours even if not billing hourly
python time_report.py \
  --project FIXED-PROJECT \
  --period this-month

# Use for profitability analysis:
# Fixed Fee - (Hours × Internal Cost) = Profit/Loss
```

---

## Accuracy Improvement Strategies

### Common Sources of Inaccuracy

| Issue | Impact | Frequency |
|-------|--------|-----------|
| Batch logging (weekly) | 40-60% higher error | Very common |
| Forgetting interruptions | 15-25% underestimation | Common |
| Rounding errors | 5-10% variance | Very common |
| Optimistic estimation | 30-50% underestimation | Common |
| Not logging meetings | 20-30% underestimation | Common |
| Multitasking during work | 10-20% overestimation | Occasional |

### Accuracy Improvement Techniques

#### 1. Use Timer Tools

**Pomodoro technique integration:**
```bash
# Work in 25-minute intervals
# Log after each pomodoro or batch of pomodoros

# After 3 pomodoros (1h 15m)
python add_worklog.py PROJ-123 --time 1h 15m \
  --comment "Implemented authentication logic (3 pomodoros)"
```

**Desktop timer apps:**
- Toggl Track (integrates with JIRA)
- Clockify (free, JIRA plugin)
- Harvest (invoicing features)
- RescueTime (automatic tracking)

#### 2. Create Daily Logging Habits

**Habit stacking:**
- Before lunch: Log morning work
- Before leaving: Log afternoon work
- During standup: Verify yesterday's logging

**Calendar reminders:**
```
9:00 AM - Start timer for first task
12:00 PM - Log time, review morning work
5:00 PM - Log time, review daily work
```

#### 3. Detailed Task Breakdown

**Before starting work:**
```bash
# Set estimate based on subtasks
python set_estimate.py PROJ-123 --original "1d"

# Create subtasks for tracking
PROJ-123-1: "Write tests" (2h)
PROJ-123-2: "Implement logic" (4h)
PROJ-123-3: "Code review" (1h)
PROJ-123-4: "Documentation" (1h)

# Log to subtasks for precision
python add_worklog.py PROJ-123-1 --time 2h 15m --comment "Unit tests complete"
```

#### 4. Log Interruptions Separately

**Dedicated interruption issues:**
```bash
# Create issues for common interruptions
PROJ-998: "Support & Questions"
PROJ-997: "Unplanned Bugs"
PROJ-996: "Production Issues"

# Log interruptions when they occur
python add_worklog.py PROJ-997 --time 30m \
  --comment "Fixed urgent bug in production login flow"
```

#### 5. Review and Adjust Estimates

**Weekly estimate review:**
```bash
# Find issues with significant variance
python jql_search.py \
  "project = PROJ AND originalEstimate IS NOT EMPTY \
   AND (timespent > originalEstimate * 1.5 OR timespent < originalEstimate * 0.5)"

# Analyze patterns:
# - Which types of tasks are consistently over/under?
# - Adjust estimation multipliers accordingly
```

### Measuring Estimation Accuracy

#### Variance Analysis

```bash
# Export issues with time tracking
python jql_search.py \
  "project = PROJ AND originalEstimate IS NOT EMPTY \
   AND status = Done" \
  --output json > completed-issues.json

# Calculate variance in spreadsheet:
# Variance = (Time Spent - Original Estimate) / Original Estimate
# Accuracy = 1 - ABS(Variance)
```

**Acceptable variance ranges:**
- Small tasks (<4h): ±50% acceptable
- Medium tasks (4h-2d): ±30% acceptable
- Large tasks (>2d): ±20% acceptable

#### Team Accuracy Metrics

```jql
# Issues with accurate estimates (within 20%)
originalEstimate IS NOT EMPTY
AND timespent >= originalEstimate * 0.8
AND timespent <= originalEstimate * 1.2

# Calculate team accuracy rate:
# Accuracy % = (Accurate Issues / Total Issues) × 100
```

**Target metrics:**
- New team: 50% accuracy within ±30%
- Mature team: 70% accuracy within ±20%
- Expert team: 80% accuracy within ±10%

### Continuous Improvement Process

**Monthly retrospective questions:**
1. What types of tasks were most over-estimated?
2. What types were most under-estimated?
3. What interruptions/overhead were forgotten?
4. How can we improve estimate accuracy?
5. What time tracking friction exists?

**Action items from retrospectives:**
```markdown
# Example improvements
- Add 30% buffer for tasks touching legacy code
- Create "meeting overhead" issues for all sprints
- Switch to 2-hour minimum estimates (not 30-minute)
- Pair on estimation for complex tasks
- Include testing time in development estimates
```

---

## Common Pitfalls to Avoid

### Time Tracking Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Zombie worklogs** | Logging time to closed issues | Enable workflow validator to prevent |
| **Estimate gymnastics** | Manipulating estimates to match actuals | Accept variance, use for learning |
| **Meeting issue overload** | Logging all meetings to one generic issue | Create per-type meeting issues |
| **Worklog novel writing** | Overly detailed comments (paragraphs) | Keep comments concise (1-2 sentences) |
| **Ghost hours** | Logging time with no real work | Audit regularly, enforce policy |
| **Micromanagement** | Requiring 15-minute increment precision | Allow 30-minute minimum rounding |
| **Batch logging** | Logging entire week on Friday | Require daily logging |
| **Invisible overhead** | Not logging meetings, email, etc. | Create overhead issues |

### Red Flags in Time Data

**For managers to watch for:**

**Issue-level red flags:**
```jql
# Issue has time logged but still "To Do"
status = "To Do" AND timespent > 0

# Issue in progress for weeks with no time logged
status = "In Progress"
AND updated >= -14d
AND timespent IS EMPTY

# Massive variance (>300%)
originalEstimate IS NOT EMPTY
AND timespent > originalEstimate * 3

# Suspiciously round numbers only (always exactly 2h, 4h, 8h)
# Manual review required
```

**User-level red flags:**
```jql
# User logging time but not updating issues
assignee = john.doe
AND worklogDate >= -7d
AND updated <= -7d

# User with no time logged in 2 weeks
worklogAuthor = john.doe
AND worklogDate <= -14d
```

**Project-level red flags:**
- Total time logged < 50% of team capacity
- Total time logged > 120% of team capacity
- No time logged on any issue in past week
- All estimates exactly matching actuals (suspicious)

### Data Quality Issues

#### Missing Estimates

**Problem:**
```jql
# Issues with time logged but no original estimate
timespent > 0 AND originalEstimate IS EMPTY
```

**Fix:**
```bash
# Set estimate retroactively based on actual
python set_estimate.py PROJ-123 --original "2d"

# Or policy: Require estimate before starting work
# Workflow validator: "Original Estimate" required to transition to "In Progress"
```

#### Orphaned Worklogs

**Problem:** Time logged to deleted or moved issues

**Prevention:**
- Restrict who can delete issues
- Require manager approval for deletions
- Use "Close" instead of "Delete"

#### Inconsistent Time Units

**Problem:** Some team members use hours, others use days

**Solution:**
```markdown
# Team standard
- Use hours for <1 day (e.g., 2h, 4h)
- Use days for ≥1 day (e.g., 1d, 2d)
- Always combine if needed (e.g., 1d 4h, not 12h)
```

### Performance and Scalability

#### Large Worklog Queries

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

#### API Rate Limits

**Problem:** Bulk worklog operations hit JIRA API rate limits

**Symptoms:**
- 429 Too Many Requests errors
- Slow performance

**Solution:**
```bash
# Scripts automatically retry with exponential backoff
# But you can reduce load:

# Use smaller batches
python bulk_log_time.py \
  --issues PROJ-1,PROJ-2,PROJ-3 \
  --time 15m \
  --comment "Sprint planning"
# Instead of JQL with 100+ issues
```

---

## Quick Reference Card

### Common Commands

```bash
# Log time to issue
python add_worklog.py PROJ-123 --time 2h --comment "Description"

# Log yesterday's work
python add_worklog.py PROJ-123 --time 3h --started yesterday

# Set estimate
python set_estimate.py PROJ-123 --original "1d" --remaining "4h"

# View worklogs
python get_worklogs.py PROJ-123

# Delete worklog
python delete_worklog.py PROJ-123 --worklog-id 12345 --dry-run

# My time this week
python time_report.py --user currentUser() --period this-week

# Project report
python time_report.py --project ACME --period this-month --output csv

# Bulk log time (with dry-run first!)
python bulk_log_time.py --jql "sprint = 123" --time 15m --comment "Planning" --dry-run
```

### Time Format Quick Reference

```
30m          30 minutes
2h           2 hours
1d           1 day (8 hours)
1w           1 week (40 hours)
1d 4h        1 day 4 hours (12 hours)
2h 30m       2 hours 30 minutes
```

### Useful JQL Queries

```jql
# My work this week
assignee = currentUser() AND worklogDate >= startOfWeek()

# Issues with time but no estimate
timespent > 0 AND originalEstimate IS EMPTY

# Over-budget issues
timespent > originalEstimate

# No time logged in a week (in progress)
status = "In Progress" AND worklogDate <= -7d

# Billable work this month
labels = billable AND worklogDate >= startOfMonth()

# Time logged today
worklogDate = startOfDay()

# High-time issues (>3 days)
timespent >= 86400  # 3 days in seconds
```

### Worklog Adjustment Modes

```bash
# Automatic (default) - reduces remaining by time logged
--adjust-estimate auto

# Leave unchanged - doesn't modify remaining
--adjust-estimate leave

# Set new remaining value
--adjust-estimate new --new-estimate 4h

# Manual reduction
--adjust-estimate manual --reduce-by 1h
```

### Daily Workflow Checklist

**Morning:**
- [ ] Review sprint board for today's work
- [ ] Check estimates on assigned issues
- [ ] Start timer/tracking for first task

**During day:**
- [ ] Log time when switching tasks
- [ ] Add descriptive comments to worklogs
- [ ] Update remaining estimates if needed

**End of day:**
- [ ] Log all work completed today
- [ ] Verify total time ≈ work hours
- [ ] Update issue status if tasks completed

**Weekly:**
- [ ] Review time logged vs sprint commitment
- [ ] Identify missing estimates
- [ ] Generate time report for manager/client

### Estimation Cheat Sheet

| Task Type | Typical Range | Example |
|-----------|---------------|---------|
| Trivial fix | 15m - 1h | Typo, config change |
| Small bug | 1h - 4h | Simple logic error |
| Medium story | 4h - 1d | Standard feature |
| Large story | 1d - 3d | Complex feature |
| Epic | 1w - 1 month | Multiple related features |

**Estimation buffers:**
- Known work: +10%
- New technology: +30%
- Unclear requirements: +50%
- Legacy code: +40%
- External dependencies: +25%

### Permission Quick Reference

**What you can do with standard permissions:**
- Log time to issues assigned to you
- Edit your own worklogs (within time window)
- Delete your own worklogs (within time window)
- View all worklogs on issues you can see

**What requires elevated permissions:**
- Edit other users' worklogs (Edit All Worklogs)
- Delete other users' worklogs (Delete All Worklogs)
- Log time to issues not assigned to you (Work On Issues)
- Change time tracking settings (JIRA Admin)

---

## Additional Resources

### Official Documentation

- [JIRA Time Tracking Guide](https://support.atlassian.com/jira-software-cloud/docs/log-time-on-an-issue/)
- [JIRA API Time Tracking](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-worklogs/)
- [Time Tracking Configuration](https://support.atlassian.com/jira-cloud-administration/docs/configure-time-tracking/)

### Best Practices Articles

- [Time Tracking in Jira: The Ultimate Checklist for 2025](https://community.atlassian.com/forums/App-Central-articles/%EF%B8%8F-Time-Tracking-in-Jira-The-Ultimate-%EF%B8%8F-Checklist-for-2025/ba-p/3090762)
- [Jira Time Tracking Best Practices for 2025](https://community.atlassian.com/forums/App-Central-articles/Jira-Time-Tracking-Best-Practices-for-2025/ba-p/1570432)
- [Time Tracking and Worklog Best Practices in Jira](https://medium.com/@erdemucak/time-tracking-and-worklog-best-practices-in-jira-0db05b59fcc9)

### Tools and Integrations

- [Jira Time Tracking Apps Marketplace](https://marketplace.atlassian.com/search?query=time%20tracking)
- [Track Billable Hours Using Jira Add-ons](https://activitytimeline.com/blog/track-billable-hours)
- [Jira Log Work Best Practices and Tips](https://activitytimeline.com/blog/jira-work-log-best-practices-and-tips)

### Known Issues and Workarounds

- [JRACLOUD-67539](https://jira.atlassian.com/browse/JRACLOUD-67539) - Estimate update bug (workaround: set both original and remaining together)
- [Time Tracking Permissions](https://support.atlassian.com/jira-cloud-administration/docs/configure-time-tracking/) - Configure who can log/edit time

---

**Last updated:** December 2024

**Skill version:** jira-time v1.0

**Related skills:**
- jira-issue: Create issues with estimates
- jira-search: Search issues by time tracking fields
- jira-agile: Sprint time tracking and burndown
- jira-bulk: Bulk time logging operations
