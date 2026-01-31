---
name: "jira-time-tracking"
description: "Time tracking and worklog management with estimation, reporting, and billing integration. Use for logging work, managing estimates, generating reports, bulk operations, and team time tracking policies."
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# JIRA Time Tracking Skill

## Risk Levels

| Operation | Risk | Notes |
|-----------|------|-------|
| View worklogs | `-` | Read-only |
| View time tracking | `-` | Read-only |
| Generate reports | `-` | Read-only |
| Export timesheets | `-` | Read-only (local file) |
| Log time | `-` | Easily reversible (can delete) |
| Update worklog | `!` | Previous value lost |
| Set estimates | `!` | Can update again |
| Bulk log time | `!` | Creates multiple worklogs |
| Delete worklog | `!!` | Time data lost, can re-log |

**Risk Legend**: `-` Safe, read-only | `!` Caution, modifiable | `!!` Warning, destructive but recoverable | `!!!` Danger, irreversible

## When to use this skill

Use the **jira-time** skill when you need to:
- Log time spent working on JIRA issues
- View, update, or delete work log entries
- Set or update time estimates (original and remaining)
- Generate time reports for billing, invoicing, or tracking
- Export timesheets to CSV or JSON format
- Bulk log time across multiple issues

## What this skill does

**IMPORTANT:** Always use the `jira-as` CLI. Never run Python scripts directly.

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

## Available Commands

| Command | Description |
|---------|-------------|
| `jira-as time log` | Add a time entry to an issue |
| `jira-as time worklogs` | List all worklogs for an issue |
| `jira-as time update-worklog` | Modify an existing worklog |
| `jira-as time delete-worklog` | Remove a worklog entry |
| `jira-as time estimate` | Set original/remaining time estimates |
| `jira-as time tracking` | View time tracking summary |
| `jira-as time report` | Generate time reports |
| `jira-as time export` | Export time data to CSV/JSON |
| `jira-as time bulk-log` | Log time to multiple issues |

All commands support `--help` for full documentation.

## Common Options

All commands support these common options:

| Option | Description | Availability |
|--------|-------------|--------------|
| `-o/--output` | Output format: text (default), json | log, worklogs, update-worklog, delete-worklog, tracking, bulk-log |
| `-f/--format` | Output format: text, json, csv | report (text/csv/json), export (csv/json only) |
| `--help` | Show help message with all available options | All commands |

### Worklog-specific options

| Option | Description |
|--------|-------------|
| `-t/--time TIME` | Time spent (e.g., 2h, 1d 4h, 30m) |
| `-c/--comment TEXT` | Description of work performed |
| `-s/--started DATE` | When work was started (default: now) |
| `--adjust-estimate MODE` | How to adjust remaining estimate: auto, leave, new, manual |
| `--new-estimate TIME` | New remaining estimate (for adjust=new or adjust=manual) |
| `--increase-by TIME` | Amount to increase estimate (for adjust=manual with delete-worklog) |
| `--visibility-type TYPE` | Worklog visibility: role or group |
| `--visibility-value TEXT` | Role name or group name for visibility |
| `-w/--worklog-id ID` | Worklog ID (for update/delete operations) |

### Worklog filter options

| Option | Description |
|--------|-------------|
| `-s/--since DATE` | Start date for filtering worklogs |
| `-u/--until DATE` | End date for filtering worklogs |
| `-a/--author USER` | Filter by worklog author |

### Report-specific options

| Option | Description |
|--------|-------------|
| `--period PERIOD` | Time period: today, yesterday, this-week, last-week, this-month, last-month, or YYYY-MM format |
| `-u/--user USER` | Filter by user (use currentUser() for yourself) |
| `-p/--project PROJECT` | Filter by project key |
| `-s/--since DATE` | Start date for filtering |
| `--until DATE` | End date for filtering |
| `-g/--group-by FIELD` | Group results by: issue, day, or user |

### Export-specific options

| Option | Description |
|--------|-------------|
| `-o/--output FILE` | Output file path (e.g., timesheets.csv) |
| `-f/--format FORMAT` | File format: csv (default) or json |

### Bulk-log-specific options

| Option | Description |
|--------|-------------|
| `-j/--jql JQL` | JQL query to select issues |
| `-i/--issues LIST` | Comma-separated issue keys |
| `-n/--dry-run` | Preview without making changes |
| `-f/--force` | Skip confirmation prompt |

## Exit Codes

All commands return standard exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success - operation completed successfully |
| 1 | Error - operation failed (check error message for details) |
| 2 | Invalid arguments - incorrect command-line usage |

## Examples

### Log time to an issue

```bash
# Log 2 hours of work
jira-as time log PROJ-123 -t 2h

# Log time with a comment
jira-as time log PROJ-123 -t "1d 4h" -c "Debugging authentication issue"

# Log time for yesterday
jira-as time log PROJ-123 -t 2h -s yesterday

# Log time without adjusting estimate
jira-as time log PROJ-123 -t 2h --adjust-estimate leave

# Log time and set new remaining estimate
jira-as time log PROJ-123 -t 2h --adjust-estimate new --new-estimate 4h

# Log time with visibility restriction
jira-as time log PROJ-123 -t 2h --visibility-type role --visibility-value Developers

# Output as JSON
jira-as time log PROJ-123 -t 2h -o json
```

### View worklogs

```bash
# List all worklogs for an issue
jira-as time worklogs PROJ-123

# Filter by author (-a is short for --author)
jira-as time worklogs PROJ-123 -a currentUser()
jira-as time worklogs PROJ-123 --author currentUser()

# Filter by date range (-s, -u are short forms)
jira-as time worklogs PROJ-123 -s 2026-01-01 -u 2026-01-31
jira-as time worklogs PROJ-123 --since 2026-01-01 --until 2026-01-31

# Output as JSON
jira-as time worklogs PROJ-123 -o json
```

### Manage estimates

```bash
# Set original estimate
jira-as time estimate PROJ-123 --original 2d

# Set remaining estimate
jira-as time estimate PROJ-123 --remaining "1d 4h"

# Set both estimates together (recommended)
jira-as time estimate PROJ-123 --original 2d --remaining 1d

# View time tracking summary
jira-as time tracking PROJ-123

# View time tracking as JSON
jira-as time tracking PROJ-123 -o json
```

### Update worklogs

```bash
# Update time on existing worklog
jira-as time update-worklog PROJ-123 -w 12345 -t 3h

# Update worklog comment
jira-as time update-worklog PROJ-123 -w 12345 -c "Updated description"

# Update worklog start time
jira-as time update-worklog PROJ-123 -w 12345 -s 2025-01-15

# Update with automatic estimate adjustment
jira-as time update-worklog PROJ-123 -w 12345 -t 4h --adjust-estimate auto

# Update and set new remaining estimate
jira-as time update-worklog PROJ-123 -w 12345 -t 4h --adjust-estimate new --new-estimate 2d

# Output as JSON
jira-as time update-worklog PROJ-123 -w 12345 -t 3h -o json
```

### Generate reports

```bash
# My time for last week
jira-as time report -u currentUser() --period last-week

# Project time for this month
jira-as time report -p PROJ --period this-month

# Report for specific month using YYYY-MM format
jira-as time report -p PROJ --period 2025-01

# Export to CSV for billing
jira-as time report -p PROJ -s 2025-01-01 --until 2025-01-31 -f csv > timesheet.csv

# Group by day for daily summary
jira-as time report -p PROJ --period this-week -g day

# Group by user for team summary
jira-as time report -p PROJ --period this-month -g user -f json

# JSON output for scripting (pipe to jq for processing)
jira-as time report -p PROJ --period this-week -f json | jq ".worklogs[] | {user: .author, hours: .timeSpentSeconds/3600}"
```

### Export timesheets

```bash
# Export last month's timesheets to CSV
jira-as time export -p PROJ --period last-month -o timesheets.csv

# Export specific month using YYYY-MM format
jira-as time export -p PROJ --period 2025-01 -o january.csv

# Export to JSON for integration
jira-as time export -p PROJ -s 2025-01-01 --until 2025-01-31 -f json -o timesheets.json

# Export user's timesheets for billing
jira-as time export -u alice@company.com --period this-month -o billing.csv
```

**Note:** For export, `-o/--output` specifies the file path and `-f/--format` specifies the format (csv or json).

### Bulk operations

```bash
# Preview bulk time logging (dry run)
jira-as time bulk-log -i PROJ-1,PROJ-2 -t 15m -c "Sprint planning" -n

# Log standup time to multiple issues
jira-as time bulk-log -i PROJ-1,PROJ-2 -t 15m -c "Sprint planning"

# Log time to JQL results with dry run
jira-as time bulk-log -j "sprint = 456" -t 15m -c "Daily standup" -n

# Execute after confirming dry run output
jira-as time bulk-log -j "sprint = 456" -t 15m -c "Daily standup"

# Skip confirmation prompt with force flag
jira-as time bulk-log -i PROJ-1,PROJ-2 -t 15m -c "Team meeting" -f

# Output results as JSON
jira-as time bulk-log -i PROJ-1,PROJ-2 -t 15m -c "Meeting" -o json
```

### Delete worklogs

```bash
# Preview worklog deletion (dry run)
jira-as time delete-worklog PROJ-123 -w 12345 --dry-run

# Delete with automatic estimate adjustment
jira-as time delete-worklog PROJ-123 -w 12345 --adjust-estimate auto

# Delete without modifying estimate
jira-as time delete-worklog PROJ-123 -w 12345 --adjust-estimate leave

# Delete and set new remaining estimate
jira-as time delete-worklog PROJ-123 -w 12345 --adjust-estimate new --new-estimate 3d

# Delete and increase estimate by specific amount (manual mode)
jira-as time delete-worklog PROJ-123 -w 12345 --adjust-estimate manual --increase-by 2h

# Delete without confirmation prompt
jira-as time delete-worklog PROJ-123 -w 12345 --yes
```

## Dry Run Support

The following commands support `--dry-run` for previewing changes without making modifications:

| Command | Dry Run Behavior |
|---------|------------------|
| `jira-as time bulk-log` | Shows which issues would receive worklogs and the time that would be logged |
| `jira-as time delete-worklog` | Shows worklog details that would be deleted and estimate impact |

**Dry-Run Pattern**: Always use `-n/--dry-run` first when performing bulk operations or deleting worklogs. This preview-before-execute workflow prevents accidental data changes:

```bash
# Step 1: Preview the operation
jira-as time bulk-log -j "sprint = 456" -t 15m -n

# Step 2: Review the output carefully
# Step 3: Execute only after confirming the preview is correct
jira-as time bulk-log -j "sprint = 456" -t 15m -c "Daily standup"
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
The worklog ID may be incorrect or the worklog was already deleted. Use `jira-as time worklogs ISSUE-KEY` to list valid worklog IDs.

#### Estimates not updating correctly
JIRA Cloud has a known bug (JRACLOUD-67539) where estimates may not update as expected. Workaround: Set both original and remaining estimates together:
```bash
jira-as time estimate PROJ-123 --original "2d" --remaining "1d"
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
When using bulk time logging:
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
When performing bulk operations on large result sets, the CLI automatically retries with exponential backoff on 429 errors. To reduce load:
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
jira-as time bulk-log -i PROJ-1,PROJ-2 -t 15m
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
jira-as time estimate PROJ-123 --original 2d --remaining "1d 4h"
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
