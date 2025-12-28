# Error Codes and Troubleshooting

Script exit codes and common error solutions.

---

## Exit Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 0 | Success | Operation completed successfully |
| 1 | Error | API error, permission denied, resource not found |
| 2 | Invalid arguments | Bad command-line usage, missing required arguments |

## Common Errors and Solutions

### Authentication Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Authentication failed" | Invalid token or email | Verify `JIRA_API_TOKEN` and `JIRA_EMAIL` environment variables |
| "Token expired" | API token no longer valid | Generate new token at id.atlassian.com |
| "Permission denied" | Insufficient JIRA permissions | Contact admin for Work on Issues permission |

### Time Format Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid time format" | Unsupported format | Use `2h`, `1d 4h`, not `2 hours` or `1.5h` |
| "Time must be positive" | Zero or negative time | Specify positive duration |
| "Invalid date" | Bad date format | Use `YYYY-MM-DD` or `yesterday` |

### Issue Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Issue not found" | Invalid issue key | Verify issue key exists: `PROJ-123` |
| "Issue does not exist" | Deleted or moved issue | Search for issue by summary |
| "Cannot log time to this issue" | Status or permission restriction | Check issue status and permissions |

### Worklog Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Worklog not found" | Invalid worklog ID | Use `get_worklogs.py` to list valid IDs |
| "Cannot edit worklog" | Missing Edit permission | Request Edit Own/All Worklogs permission |
| "Cannot delete worklog" | Missing Delete permission | Request Delete Own/All Worklogs permission |

### Estimate Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Estimate not updated" | JRACLOUD-67539 bug | Set both original and remaining together |
| "Invalid estimate format" | Bad time format | Use `2d` not `16h` for multi-day estimates |
| "Cannot set estimate" | Issue type restriction | Check if issue type supports time tracking |

### Time Tracking Configuration Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Time tracking is not enabled" | Project setting disabled | Ask admin to enable in Project Settings > Features |
| "Time tracking disabled for issue type" | Issue type setting | Check issue type scheme configuration |

### API Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "429 Too Many Requests" | Rate limit exceeded | Wait and retry; scripts auto-retry |
| "500 Internal Server Error" | JIRA server error | Wait and retry; report to admin if persistent |
| "503 Service Unavailable" | JIRA maintenance | Check status.atlassian.com |
| "Connection timeout" | Network issue | Check network; verify JIRA_SITE_URL |

### Bulk Operation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Some issues failed" | Mixed success/failure | Check output for specific failed issues |
| "JQL returned no results" | Invalid or empty query | Verify JQL syntax and results |
| "Too many results" | JQL too broad | Add filters to narrow results |

## Debugging Tips

### Enable Verbose Output

Most scripts support verbose output for debugging:
```bash
python script.py PROJ-123 --verbose
```

### Check Configuration

Verify your configuration:
```bash
# Check environment variables
echo $JIRA_SITE_URL
echo $JIRA_EMAIL
echo $JIRA_API_TOKEN

# Test basic connectivity
python get_issue.py PROJ-123
```

### Dry Run First

Always use `--dry-run` for destructive operations:
```bash
python delete_worklog.py PROJ-123 --worklog-id 12345 --dry-run
python bulk_log_time.py --jql "..." --time 15m --dry-run
```

### Check Permissions

Test permission by trying simple operations:
```bash
# Can you view the issue?
python get_issue.py PROJ-123

# Can you view worklogs?
python get_worklogs.py PROJ-123

# Can you view time tracking?
python get_time_tracking.py PROJ-123
```

## Getting Help

### Script Help

All scripts support `--help`:
```bash
python add_worklog.py --help
python time_report.py --help
```

### Related Resources

- [SKILL.md](../../SKILL.md) - Full script documentation
- [Team Policies](../team-policies.md) - Permission configuration
- [Atlassian Status](https://status.atlassian.com) - Service status

---

**Back to:** [SKILL.md](../../SKILL.md) | [Best Practices](../BEST_PRACTICES.md)
