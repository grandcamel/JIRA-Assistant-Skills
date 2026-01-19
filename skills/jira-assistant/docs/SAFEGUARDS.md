# Safeguards and Error Handling

Guidelines for destructive operations, error recovery, and safe practices.

## Destructive Operation Safeguards

### Risk Levels

| Operation | Skill | Risk Level | Safeguard |
|-----------|-------|:----------:|-----------|
| Delete issue | `jira-issue` | HIGH | Confirm key, warn if has subtasks/links |
| Bulk transition | `jira-bulk` | HIGH | Show count, require `--confirm` or dry-run first |
| Bulk delete | `jira-bulk` | CRITICAL | Require issue keys explicitly, no wildcards |
| Delete project | `jira-admin` | CRITICAL | Double confirmation, show issue count |
| Remove permissions | `jira-admin` | HIGH | Show affected users |

### Dry-Run Recommendations

Always suggest dry-run for:
- Any bulk operation
- Operations affecting > 10 issues
- Operations with regex/JQL wildcards
- First-time use of destructive commands

**Example Interaction:**
```
User: "Close all bugs in TES"
Assistant: "This will close 47 bugs. Run with --dry-run first?

            jira-as bulk transition "project=TES AND type=Bug" --to Done --dry-run

            Then confirm with:
            jira-as bulk transition "project=TES AND type=Bug" --to Done --confirm"
```

### Undo Guidance

| Operation | Undo Method |
|-----------|-------------|
| Transition | Transition back (if workflow allows) |
| Update field | Update again with previous value |
| Delete issue | Cannot undo - suggest archive/close instead |
| Add link | Remove link |
| Bulk update | Bulk update with original values (if logged) |

---

## Error Handling

### Skill-Specific Recovery

| Error | Likely Skill | Recovery |
|-------|--------------|----------|
| "Issue does not exist" | jira-issue | Verify key format, check project access |
| "Transition not available" | jira-lifecycle | Load `jira-lifecycle` to see valid transitions |
| "Permission denied" | any | Check with `jira-admin` → list permissions |
| "Field not found" | jira-issue | Use `jira-fields` to discover field IDs |
| "Rate limited" | any | Wait, use `jira-ops` cache warming |

### Permission Errors

```
Error: "You don't have permission to edit issues"

Recovery:
1. Check current permissions: jira-as admin list-permissions --project TES
2. If admin: jira-as admin add-permission --scheme ... --permission EDIT_ISSUES
3. If not admin: Contact project administrator
```

### Common Error Patterns

| Error Message | Cause | Solution |
|---------------|-------|----------|
| 401 Unauthorized | Invalid/expired token | Regenerate API token |
| 403 Forbidden | Missing permission | Check project role |
| 404 Not Found | Wrong key or no access | Verify issue exists, check permissions |
| 400 Bad Request | Invalid field value | Check field type and allowed values |
| 429 Too Many Requests | Rate limited | Wait and retry, use caching |

---

## Error Response Templates

Use these templates when reporting errors to users:

### Skill Not Found
```
"I don't have a skill called '{name}'. Available skills for JIRA:
- jira-issue, jira-search, jira-agile, jira-lifecycle, jira-collaborate,
  jira-relationships, jira-time, jira-jsm, jira-bulk, jira-dev,
  jira-fields, jira-ops, jira-admin

Did you mean one of these?"
```

### Permission Denied
```
"You don't have permission to {operation} in project {PROJECT}.
You may need to:
- Request access from your JIRA administrator
- Use a different project where you have access

Would you like me to check your permissions with jira-admin?"
```

### Rate Limited
```
"JIRA is rate limiting requests. Please wait {X} seconds before retrying.
For bulk operations, consider using jira-bulk with smaller batch sizes."
```

### Entity Not Found
```
"Issue {KEY} doesn't exist. Possible causes:
- Typo in the issue key
- Issue was deleted
- You don't have access to view it

Would you like me to search for similar issues?"
```

### Skill Execution Failed
```
"The {skill_name} operation failed: {error_message}

Suggestions:
- {recovery_option_1}
- {recovery_option_2}

Try a different approach with {alternative_skill}?"
```

---

## Error Escalation Paths

When an error occurs, escalate to the appropriate skill:

| From Skill | Escalate To | When |
|------------|-------------|------|
| jira-issue | jira-bulk | >10 issues to modify |
| jira-lifecycle | jira-admin | Workflow/permission issues |
| jira-search | jira-fields | Unknown field errors |
| Any skill | jira-ops | Cache/connectivity issues |
| Any skill | jira-admin | Permission denied errors |

---

## Partial Workflow Failure

When a multi-step workflow fails partway:

1. **Stop immediately** - Don't attempt remaining steps
2. **Report what succeeded**: "Created epic TES-100 and story TES-101"
3. **Explain the failure**: "Story 2 failed: field 'customfield_123' is required"
4. **Offer options**:
   - "Fix the issue and continue with remaining stories?"
   - "Keep what was created and stop here?"
   - "Delete TES-100 and TES-101 to start fresh?"

**Default behavior**: Keep successful items. Deletion requires explicit confirmation.

---

## Best Practices

### Before Bulk Operations

1. **Test with small set first**: Use `--max-results 5` to verify
2. **Always dry-run**: See what will change before committing
3. **Check permissions**: Ensure you have edit access to all target issues
4. **Consider timing**: Avoid bulk ops during peak usage

### Confirmation Patterns

For high-risk operations, require explicit confirmation:

```bash
# Dry run first
jira-as bulk assign "project=TES" --to @alice --dry-run

# Review output, then confirm
jira-as bulk assign "project=TES" --to @alice --confirm
```

### Rollback Strategy

Before making bulk changes:
1. Export current state: `jira-as search export "JQL" -o backup.csv`
2. Make changes with logging
3. Keep change log for potential rollback

---

## Skill Interaction Warnings

| Combination | Warning |
|-------------|---------|
| `jira-issue.delete` + `jira-relationships` | Deleting issues breaks existing links |
| `jira-bulk` + large JQL | Consider pagination for >1000 issues |
| `jira-admin.delete-project` | Irreversible - export data first |
| `jira-lifecycle` + bulk | Use `jira-bulk` for >5 transitions |
