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
```

### Bulk operations

```bash
# Log standup time to multiple issues
python bulk_log_time.py --issues PROJ-1,PROJ-2,PROJ-3 --time 15m --comment "Sprint planning"

# Log time to JQL results
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

## Related skills

- **jira-issue**: Create and manage issues (can set estimates on creation)
- **jira-search**: Search issues and view time tracking fields
- **jira-agile**: Sprint management with time tracking integration
