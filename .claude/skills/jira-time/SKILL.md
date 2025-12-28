---
name: "JIRA Time Tracking"
description: "Time tracking and worklog management with estimation, reporting, and billing integration. Use for logging work, managing estimates, generating reports, bulk operations, and team time tracking policies."
---

# JIRA Time Tracking Skill

## When to use this skill

Use the **jira-time** skill when you need to:
- Log time spent working on JIRA issues
- View, update, or delete work log entries
- Set or update time estimates (original and remaining)
- Generate time reports for billing, invoicing, or tracking
- Export timesheets to CSV or JSON format
- Bulk log time across multiple issues

## What this skill does

The jira-time skill provides comprehensive time tracking and worklog management:

### Worklog Management
- **Add worklogs** - Log time with optional comments and date/time
- **View worklogs** - List all time entries for an issue
- **Update worklogs** - Modify existing time entries
- **Delete worklogs** - Remove time entries with estimate adjustment

### Time Estimates
- **Set estimates** - Configure original and remaining estimates
- **View time tracking** - See complete time tracking summary with progress

### Reporting
- **Time reports** - Generate reports by user, project, or date range
- **Export timesheets** - Export to CSV/JSON for billing systems
- **Bulk operations** - Log time to multiple issues at once

## Available scripts

| Script | Description |
|--------|-------------|
| `add_worklog.py` | Add a time entry to an issue |
| `get_worklogs.py` | List all worklogs for an issue |
| `update_worklog.py` | Modify an existing worklog |
| `delete_worklog.py` | Remove a worklog entry |
| `set_estimate.py` | Set original/remaining time estimates |
| `get_time_tracking.py` | View time tracking summary |
| `time_report.py` | Generate time reports |
| `export_timesheets.py` | Export time data to CSV/JSON |
| `bulk_log_time.py` | Log time to multiple issues |

## Common Options

All scripts support these common options:

| Option | Description |
|--------|-------------|
| `--profile PROFILE` | Use specific JIRA profile (development, staging, production) |
| `--output FORMAT` | Output format: table (default), json, or csv |
| `--help` | Show help message with all available options |

### Worklog-specific options

| Option | Description |
|--------|-------------|
| `--time TIME` | Time spent (e.g., 2h, 1d 4h, 30m) |
| `--comment TEXT` | Description of work performed |
| `--started DATE` | When work was started (default: now) |
| `--adjust-estimate MODE` | How to adjust remaining estimate: auto, leave, new, manual |

### Report-specific options

| Option | Description |
|--------|-------------|
| `--period PERIOD` | Time period: today, this-week, last-week, this-month, 2025-01 |
| `--user USER` | Filter by user (use currentUser() for yourself) |
| `--project PROJECT` | Filter by project key |
| `--since DATE` | Start date for filtering |
| `--until DATE` | End date for filtering |

## Exit Codes

All scripts return standard exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success - operation completed successfully |
| 1 | Error - operation failed (check error message for details) |
| 2 | Invalid arguments - incorrect command-line usage |

## Examples

### Log time to an issue

```bash
# Log 2 hours of work
python add_worklog.py PROJ-123 --time 2h

# Log time with a comment
python add_worklog.py PROJ-123 --time "1d 4h" --comment "Debugging authentication issue"

# Log time for yesterday
python add_worklog.py PROJ-123 --time 2h --started yesterday

# Log time without adjusting estimate
python add_worklog.py PROJ-123 --time 2h --adjust-estimate leave
```

### View worklogs

```bash
# List all worklogs for an issue
python get_worklogs.py PROJ-123

# Filter by author
python get_worklogs.py PROJ-123 --author currentUser()

# Filter by date range
python get_worklogs.py PROJ-123 --since 2025-01-01 --until 2025-01-31

# Output as JSON
python get_worklogs.py PROJ-123 --output json
```

### Manage estimates

```bash
# Set original estimate
python set_estimate.py PROJ-123 --original "2d"

# Set remaining estimate
python set_estimate.py PROJ-123 --remaining "1d 4h"

# View time tracking summary
python get_time_tracking.py PROJ-123
```

### Generate reports

```bash
# My time for last week
python time_report.py --user currentUser() --period last-week

# Project time for this month
python time_report.py --project PROJ --period this-month

# Export to CSV for billing
python time_report.py --project PROJ --period 2025-01 --output csv > timesheet.csv

# Export detailed CSV with all fields
python time_report.py --project PROJ --period this-month --output csv --include-issue-details
```

### Bulk operations

```bash
# Preview bulk time logging (dry run)
python bulk_log_time.py --issues PROJ-1,PROJ-2,PROJ-3 --time 15m --comment "Sprint planning" --dry-run

# Log standup time to multiple issues
python bulk_log_time.py --issues PROJ-1,PROJ-2,PROJ-3 --time 15m --comment "Sprint planning"

# Log time to JQL results with dry run
python bulk_log_time.py --jql "sprint = 456" --time 15m --comment "Daily standup" --dry-run

# Execute after confirming dry run output
python bulk_log_time.py --jql "sprint = 456" --time 15m --comment "Daily standup"
```

### Delete worklogs

```bash
# Preview worklog deletion (dry run)
python delete_worklog.py PROJ-123 --worklog-id 12345 --dry-run

# Delete with automatic estimate adjustment
python delete_worklog.py PROJ-123 --worklog-id 12345 --adjust-estimate auto

# Delete without modifying estimate
python delete_worklog.py PROJ-123 --worklog-id 12345 --adjust-estimate leave
```

## Dry Run Support

The following scripts support `--dry-run` for previewing changes without making modifications:

| Script | Dry Run Behavior |
|--------|------------------|
| `bulk_log_time.py` | Shows which issues would receive worklogs and the time that would be logged |
| `delete_worklog.py` | Shows worklog details that would be deleted and estimate impact |

**Dry-Run Pattern**: Always use `--dry-run` first when performing bulk operations or deleting worklogs. This preview-before-execute workflow prevents accidental data changes:

```bash
# Step 1: Preview the operation
python bulk_log_time.py --jql "sprint = 456" --time 15m --dry-run

# Step 2: Review the output carefully
# Step 3: Execute only after confirming the preview is correct
python bulk_log_time.py --jql "sprint = 456" --time 15m --comment "Daily standup"
```

## Time format

JIRA accepts human-readable time formats:
- `30m` - 30 minutes
- `2h` - 2 hours
- `1d` - 1 day (8 hours by default)
- `1w` - 1 week (5 days by default)
- `2d 4h 30m` - Combined format

## Configuration

Time tracking must be enabled in your JIRA project. If you receive an error about time tracking being disabled, ask your JIRA administrator to enable it.

### Profile support

All scripts support the `--profile` flag:

```bash
python add_worklog.py PROJ-123 --time 2h --profile production
```

## Troubleshooting

### Common Issues

#### "Time tracking is not enabled"
Time tracking must be enabled at the project level. Contact your JIRA administrator to enable it in Project Settings > Features > Time Tracking.

#### "Cannot log time to this issue"
Possible causes:
- The issue is in a status that doesn't allow time logging
- You don't have permission to log work on this issue
- The issue type doesn't support time tracking

#### "Worklog not found"
The worklog ID may be incorrect or the worklog was already deleted. Use `get_worklogs.py ISSUE-KEY` to list valid worklog IDs.

#### Estimates not updating correctly
JIRA Cloud has a known bug (JRACLOUD-67539) where estimates may not update as expected. Workaround: Set both original and remaining estimates together using `set_estimate.py`:
```bash
python set_estimate.py PROJ-123 --original "2d" --remaining "1d"
```

#### Time logged but not showing in reports
- Check the `--started` date - worklogs are associated with the start date, not creation date
- Verify the correct `--period` filter is being used
- Ensure the user has permission to view the issue's worklogs

#### "Invalid time format"
Use JIRA's standard time notation:
- Correct: `2h`, `1d 4h`, `30m`, `1w 2d`
- Incorrect: `2 hours`, `1.5h`, `90 minutes`

#### Bulk operation failures
When using `bulk_log_time.py`:
1. Always use `--dry-run` first to preview changes
2. Check that all issues in the JQL results are accessible
3. Verify time tracking is enabled on all target projects

### Permission Requirements

To use time tracking features, you typically need:
- **Browse Projects** - View issues and worklogs
- **Work On Issues** - Add worklogs to issues
- **Edit All Worklogs** - Modify/delete any user's worklogs (admin)
- **Delete All Worklogs** - Delete any user's worklogs (admin)

For detailed permission matrix, see [Permission Matrix](docs/reference/permission-matrix.md).

### Advanced Troubleshooting

#### API rate limits
When performing bulk operations on large result sets, scripts automatically retry with exponential backoff on 429 errors. To reduce load:
- Use smaller date ranges for reports
- Filter JQL to limit results before bulk operations

#### Timezone issues
Worklogs use UTC internally. If time appears on wrong date:
- Check your JIRA timezone settings
- Use explicit `--started` date when needed

#### Bulk operation timeouts
Large JQL result sets may timeout:
```bash
# Use smaller batches instead of one large query
python bulk_log_time.py --issues PROJ-1,PROJ-2,PROJ-3 --time 15m
```

#### Worklog visibility issues
If worklogs are logged but others cannot see them:
- Check worklog visibility settings
- Verify issue security scheme permissions

For complete error code reference, see [Error Codes](docs/reference/error-codes.md).

## Common Questions

**Why is my estimate not updating?**
JIRA Cloud bug (JRACLOUD-67539). Set both estimates together:
```bash
python set_estimate.py PROJ-123 --original "2d" --remaining "1d 4h"
```

**How do I log time for someone else?**
You need "Edit All Worklogs" permission. Most users can only log their own time.

**Can I bill partial hours?**
Yes. Use minutes for precision: `1h 45m` (not `1.75h`). JIRA doesn't support decimal hours.

**How does --adjust-estimate work?**

| Mode | Effect |
|------|--------|
| `auto` | Reduces remaining by time logged |
| `leave` | No change to remaining estimate |
| `new` | Sets remaining to a new value |
| `manual` | Reduces remaining by specified amount |

## Advanced Guides

For specific roles and use cases, see:

| Guide | Audience | Topics |
|-------|----------|--------|
| [IC Time Logging](docs/ic-time-logging.md) | Developers, QA | Daily habits, comment templates, special cases |
| [Estimation Guide](docs/estimation-guide.md) | PMs, Team Leads | Approaches, accuracy metrics, buffers |
| [Team Policies](docs/team-policies.md) | Managers, Admins | Policy templates, onboarding, compliance |
| [Billing Integration](docs/billing-integration.md) | Finance, PMs | Invoicing, billable tracking, exports |
| [Reporting Guide](docs/reporting-guide.md) | Analysts, PMs | Reports, dashboards, JQL queries |

### Quick Reference

| Reference | Content |
|-----------|---------|
| [Time Format](docs/reference/time-format-quick-ref.md) | Format syntax, common values |
| [JQL Snippets](docs/reference/jql-snippets.md) | Copy-paste queries for time tracking |
| [Permission Matrix](docs/reference/permission-matrix.md) | Role-based permissions |
| [Error Codes](docs/reference/error-codes.md) | Troubleshooting guide |

## Best Practices

For comprehensive guidance on time logging workflows, estimate management, and reporting patterns, see [Best Practices Guide](docs/BEST_PRACTICES.md) (navigation hub to all guides).

## Related skills

- **jira-issue**: Create and manage issues (can set estimates on creation)
- **jira-search**: Search issues and view time tracking fields
- **jira-agile**: Sprint management with time tracking integration
- **jira-bulk**: Bulk operations at scale with dry-run support
