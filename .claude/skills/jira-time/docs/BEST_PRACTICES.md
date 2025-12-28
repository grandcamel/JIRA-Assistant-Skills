# JIRA Time Tracking Best Practices

Navigation hub for comprehensive time tracking guidance. Choose your role and use case to find relevant documentation.

---

## Quick Start

New to time tracking? Start here:

1. **Set up credentials**: Configure `JIRA_API_TOKEN`, `JIRA_EMAIL`, `JIRA_SITE_URL`
2. **Log your first worklog**: `python add_worklog.py PROJ-123 --time 2h --comment "Description"`
3. **Check your time**: `python time_report.py --user currentUser() --period this-week`

For script documentation and examples, see [SKILL.md](../SKILL.md).

---

## Choose Your Guide

### By Role

| Role | Primary Guide | Focus Areas |
|------|--------------|-------------|
| **Developer / IC** | [IC Time Logging](ic-time-logging.md) | Daily habits, comment templates, special cases |
| **Team Lead** | [Team Policies](team-policies.md) | Policies, monitoring, onboarding |
| **Manager** | [Team Policies](team-policies.md) | Compliance, enforcement, permissions |
| **Finance** | [Billing Integration](billing-integration.md) | Invoicing, billable tracking, exports |
| **PM / Analyst** | [Reporting Guide](reporting-guide.md) | Reports, dashboards, JQL queries |
| **JIRA Admin** | [Team Policies](team-policies.md) | Permissions, workflow validators |

### By Task

| Task | Guide | Key Section |
|------|-------|-------------|
| Log time to issue | [SKILL.md](../SKILL.md) | Examples |
| Write good worklog comments | [IC Time Logging](ic-time-logging.md) | Writing Effective Comments |
| Set estimates | [Estimation Guide](estimation-guide.md) | Setting Realistic Estimates |
| Generate reports | [Reporting Guide](reporting-guide.md) | Command-Line Reporting |
| Export for invoicing | [Billing Integration](billing-integration.md) | Invoice Preparation Workflow |
| Configure team policies | [Team Policies](team-policies.md) | Establishing Team Policies |
| Find time format syntax | [Time Format Quick Ref](reference/time-format-quick-ref.md) | - |
| Debug script errors | [Error Codes](reference/error-codes.md) | - |

---

## Guides Overview

### [IC Time Logging Guide](ic-time-logging.md)

For individual contributors (developers, QA, contractors).

- When to log time (daily vs task completion)
- Writing effective worklog comments with templates
- Handling special cases (retroactive, interrupted work)
- Worklog visibility and security

**~200 lines** | **Time to read: 10 minutes**

### [Estimation Guide](estimation-guide.md)

For product managers, team leads, and estimation coaches.

- Understanding JIRA time fields (original, remaining, spent)
- Estimation approaches (bottom-up, story points, T-shirt sizing)
- Buffer guidelines by task type
- Measuring and improving estimate accuracy

**~250 lines** | **Time to read: 15 minutes**

### [Team Policies Guide](team-policies.md)

For managers, team leads, and JIRA administrators.

- Sample policy document template
- Onboarding checklists and training scripts
- Permission configuration matrix
- Monitoring queries and compliance enforcement

**~200 lines** | **Time to read: 12 minutes**

### [Billing Integration Guide](billing-integration.md)

For finance teams, billing admins, and project managers.

- Billable tracking strategies (labels, components, custom fields)
- Invoice preparation workflow (5 steps)
- Third-party tool comparison (Tempo, Everhour, etc.)
- Handling client disputes

**~300 lines** | **Time to read: 18 minutes**

### [Reporting Guide](reporting-guide.md)

For data analysts, project managers, and reporting admins.

- Built-in JIRA reports overview
- Command-line reporting (user, project, date ranges)
- Export formats (CSV, JSON)
- Dashboard configuration and JQL queries

**~250 lines** | **Time to read: 15 minutes**

---

## Quick Reference Files

Lookup tables for common queries:

| Reference | Content | Lines |
|-----------|---------|-------|
| [Time Format](reference/time-format-quick-ref.md) | Format syntax, common values | ~80 |
| [JQL Snippets](reference/jql-snippets.md) | Copy-paste queries | ~100 |
| [Permission Matrix](reference/permission-matrix.md) | Role-based permissions | ~60 |
| [Error Codes](reference/error-codes.md) | Troubleshooting guide | ~100 |

---

## Common Commands

```bash
# Log time to issue
python add_worklog.py PROJ-123 --time 2h --comment "Description"

# Log yesterday's work
python add_worklog.py PROJ-123 --time 3h --started yesterday

# Set estimate
python set_estimate.py PROJ-123 --original "1d" --remaining "4h"

# View worklogs
python get_worklogs.py PROJ-123

# Delete worklog (dry-run first!)
python delete_worklog.py PROJ-123 --worklog-id 12345 --dry-run

# My time this week
python time_report.py --user currentUser() --period this-week

# Project report to CSV
python time_report.py --project ACME --period this-month --output csv

# Bulk log time (dry-run first!)
python bulk_log_time.py --jql "sprint = 123" --time 15m --comment "Planning" --dry-run
```

---

## Key Concepts

### Time Fields Relationship

```
Original Estimate: Initial prediction (set at planning)
Time Spent: Cumulative worklogs (auto-updated)
Remaining Estimate: Time left (optionally auto-decremented)

Progress = Time Spent / Original Estimate
Variance = (Time Spent + Remaining) - Original Estimate
```

### Estimate Adjustment Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `auto` | Reduces remaining by time logged | Default workflow |
| `leave` | No change to remaining | Out-of-scope work |
| `new` | Sets remaining to new value | Re-estimation |
| `manual` | Reduces remaining by specified amount | Custom adjustment |

### Known Issue: JRACLOUD-67539

Estimates may not update correctly in JIRA Cloud. Workaround:
```bash
python set_estimate.py PROJ-123 --original "2d" --remaining "1d 4h"
```

---

## Additional Resources

### Official Documentation

- [JIRA Time Tracking Guide](https://support.atlassian.com/jira-software-cloud/docs/log-time-on-an-issue/)
- [JIRA API Time Tracking](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-worklogs/)
- [Time Tracking Configuration](https://support.atlassian.com/jira-cloud-administration/docs/configure-time-tracking/)

### Community Resources

- [Time Tracking in Jira: The Ultimate Checklist](https://community.atlassian.com/forums/App-Central-articles/)
- [Jira Time Tracking Best Practices](https://community.atlassian.com/forums/App-Central-articles/)

### Related Skills

- **jira-issue**: Create issues with estimates
- **jira-search**: Search issues by time tracking fields
- **jira-agile**: Sprint time tracking and burndown
- **jira-bulk**: Bulk time logging operations

---

**Last updated:** December 2024

**Skill version:** jira-time v1.0

**Back to:** [SKILL.md](../SKILL.md)
