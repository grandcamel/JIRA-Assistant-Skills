# Billing and Finance Integration Guide

Guidance for finance teams, billing administrators, and project managers on billable tracking, invoicing workflows, and client billing.

---

## Use this guide if you...

- Need to track billable vs non-billable hours
- Are preparing client invoices from JIRA time data
- Want to integrate JIRA with accounting systems
- Need to handle client billing disputes
- Manage retainer or fixed-fee projects

For time tracking basics, see [IC Time Logging Guide](ic-time-logging.md).
For reporting capabilities, see [Reporting Guide](reporting-guide.md).

---

## Table of Contents

1. [Native JIRA Limitations](#native-jira-limitations)
2. [Billable Tracking Strategies](#billable-tracking-strategies)
3. [Billable Hours Reporting](#billable-hours-reporting)
4. [Third-Party Tools](#third-party-tools)
5. [Invoice Preparation Workflow](#invoice-preparation-workflow)
6. [Handling Client Disputes](#handling-client-disputes)
7. [Retainer and Fixed-Fee Projects](#retainer-and-fixed-fee-projects)

---

## Native JIRA Limitations

**Important:** JIRA's native time tracking has **no built-in concept of billable/non-billable hours**. All worklogs are treated equally.

This means you must implement your own tracking mechanism using one of these approaches:
- Labels
- Components
- Separate projects
- Custom fields (recommended if available)

---

## Billable Tracking Strategies

### Option 1: Use Labels

```bash
# Create issues with billable labels
python create_issue.py --summary "Client feature X" \
  --labels billable,client-acme

python create_issue.py --summary "Internal refactoring" \
  --labels non-billable,tech-debt

# Search for billing reports
python jql_search.py "labels = billable AND timespent > 0"
```

| Pros | Cons |
|------|------|
| Simple, no cost | Manual labeling |
| No admin setup needed | No rate tracking |
| Easy to query | Basic reporting only |

### Option 2: Use Components

```bash
# Create components per client
Components: "Client-ACME", "Client-TechCorp", "Internal"

# Search for client time
python jql_search.py "component = 'Client-ACME' AND timespent > 0"
```

| Pros | Cons |
|------|------|
| Natural project organization | No billable/non-billable within client |
| Good for multi-client projects | Component management overhead |

### Option 3: Separate Projects

```
Project Structure:
 -- ACME-BILL (billable client work)
 -- ACME-INT (internal/non-billable)
 -- TECH-BILL (billable client work)
 -- INTERNAL (company internal work)
```

| Pros | Cons |
|------|------|
| Clear separation | More projects to manage |
| Easy reporting | Project key clutter |
| Obvious billing status | Overhead for small clients |

### Option 4: Custom Field (Recommended)

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

| Pros | Cons |
|------|------|
| Explicit billable flag | Requires admin setup |
| Queryable with JQL | No hourly rates |
| Consistent tracking | Extra field to manage |

---

## Billable Hours Reporting

### Export for Invoicing

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

### Common Report Queries

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

### Export Formats

**CSV for spreadsheet analysis:**
```bash
python time_report.py \
  --project ACME \
  --period this-month \
  --output csv > report.csv

# CSV columns:
# Issue Key, Issue Summary, Author, Date, Time Spent, Seconds
```

**JSON for custom processing:**
```bash
python time_report.py \
  --project ACME \
  --period this-month \
  --output json > report.json

# Process with jq
cat report.json | jq '.entries[] | select(.author == "John Doe")'
```

---

## Third-Party Tools

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

## Invoice Preparation Workflow

### Step 1: Identify Unbilled Work

```jql
# Work logged but not yet invoiced
project = ACME
AND labels = billable
AND labels != invoiced-2025-01
AND timespent > 0
ORDER BY created ASC
```

### Step 2: Generate Time Report

```bash
# Export unbilled time
python time_report.py \
  --project ACME \
  --period 2025-01 \
  --group-by issue \
  --output csv > unbilled-work.csv
```

### Step 3: Review and Validate

```bash
# Check for issues:
# - Missing descriptions
# - Unusual time amounts
# - Wrong project/component

python get_worklogs.py ACME-123
```

**Validation checklist:**
- [ ] All worklogs have descriptive comments
- [ ] Time amounts are reasonable
- [ ] Correct billable categorization
- [ ] No duplicate entries

### Step 4: Create Invoice

**Manual process:**
1. Import CSV to invoice template
2. Apply hourly rates
3. Calculate totals
4. Add client-specific formatting
5. Generate PDF

**Automated with Tempo/Everhour:**
1. Mark period for invoicing
2. Generate invoice in-app
3. Export PDF
4. Send to client

### Step 5: Mark as Invoiced

```bash
# Bulk add invoice label to prevent double-billing
python bulk_update.py \
  --jql "project = ACME AND labels = billable AND labels != invoiced-2025-01" \
  --add-label "invoiced-2025-01"
```

### Invoice Report Template

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

---

## Handling Client Disputes

### Common Scenarios

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

### Prevention Strategies

**Enforce descriptive worklog comments:**
```bash
python add_worklog.py ACME-123 --time 4h \
  --comment "Implemented user authentication flow per requirements in PRD-2025-01"
```

**Regular client communication:**
- Weekly status reports with hours logged
- Approval for work exceeding estimates
- Clear change request process

**Documentation trail:**
- Link worklogs to requirements documents
- Reference ticket numbers in comments
- Keep approval emails/chats

---

## Retainer and Fixed-Fee Projects

### Retainer Tracking

```bash
# Track hours against monthly retainer
python time_report.py \
  --project ACME \
  --period this-month \
  --group-by user

# Compare to retainer allocation (e.g., 80 hours/month)
# Alert when approaching limit
```

**Retainer monitoring queries:**
```jql
# Hours logged this month for retainer project
project = ACME-RETAINER
AND worklogDate >= startOfMonth()

# Track against 80h/month limit in spreadsheet
```

### Fixed-Fee Projects

```bash
# Track internal hours even if not billing hourly
python time_report.py \
  --project FIXED-PROJECT \
  --period this-month

# Use for profitability analysis:
# Fixed Fee - (Hours x Internal Cost) = Profit/Loss
```

**Profitability tracking:**
```bash
# Export all time for fixed project
python time_report.py \
  --project FIXED-PROJECT \
  --output csv > fixed-project-hours.csv

# In spreadsheet:
# Total Hours x Internal Rate = Cost
# Fixed Fee - Cost = Profit/Loss
```

### Budget Alerts

Set up monitoring for budget consumption:

```jql
# Fixed project with time logged
project = FIXED-PROJECT AND timespent > 0
```

Calculate percentage consumed:
```
Budget Used = (Time Spent / Budgeted Hours) x 100
```

Trigger alerts at:
- 50% consumed (mid-project check)
- 75% consumed (scope review needed)
- 90% consumed (scope change or additional billing)

---

## Accounting System Integration

### QuickBooks Integration

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

### Generic Accounting Export

```bash
# Standard CSV for import
python time_report.py \
  --project ACME \
  --since 2025-01-01 \
  --until 2025-01-31 \
  --output csv > timesheet.csv

# Add hourly rate column in spreadsheet
# Calculate: Hours x Rate = Amount
```

---

## Related Guides

- [IC Time Logging Guide](ic-time-logging.md) - Effective worklog comments for billing
- [Reporting Guide](reporting-guide.md) - Advanced report generation
- [Team Policies](team-policies.md) - Billable tracking policies
- [Quick Reference: JQL Snippets](reference/jql-snippets.md) - Billing-related queries

---

**Back to:** [SKILL.md](../SKILL.md) | [Best Practices Index](BEST_PRACTICES.md)
