# JIRA Skills Safeguards

Safety guidelines, risk definitions, and recovery procedures for JIRA operations.

## Risk Level Definitions

| Symbol | Level | Description | Confirmation Required |
|--------|-------|-------------|----------------------|
| `-` | Safe | Read-only or easily reversible | No |
| `!` | Caution | Modifiable, can be undone | Verbal (explain what will happen) |
| `!!` | Warning | Destructive but recoverable | Explicit ("Are you sure?") |
| `!!!` | Danger | **IRREVERSIBLE** | Explicit + dry-run first |

## Pre-Operation Checklists

### Before Any Bulk Operation

```
[ ] Verify JQL query returns expected issues (run search first)
[ ] Check issue count is within expected range
[ ] Run with --dry-run to preview changes
[ ] Confirm with user before executing
[ ] For >100 issues, discuss batching strategy
```

### Before Delete Operations

```
[ ] Confirm issue key(s) are correct
[ ] Check for subtasks (will also be deleted)
[ ] Check for linked issues (links will be removed)
[ ] Verify user has DELETE_ISSUES permission
[ ] For bulk delete: always --dry-run first
```

### Before Project Operations

```
[ ] Confirm project key
[ ] For delete: verify all issues should be lost
[ ] For archive: confirm project can be restored later
[ ] Check for dependent schemes (permissions, workflows)
```

### Before Permission Changes

```
[ ] Identify current scheme assigned
[ ] List affected projects
[ ] Preview permission grants being changed
[ ] Consider creating new scheme instead of modifying shared one
```

## Recovery Procedures

### Issues

| Problem | Recovery Steps |
|---------|----------------|
| **Issue deleted (single)** | Check trash (Settings > Trash); restore within 30 days |
| **Issue deleted (bulk, no trash)** | No recovery - must recreate manually |
| **Wrong field values** | Use jira-issue update to correct; check activity log for original values |
| **Wrong transition** | Transition back (if workflow allows); may need jira-admin to check transitions |
| **Wrong assignment** | jira-lifecycle assign to correct user |
| **Lost issue content** | Check activity history (jira-collaborate activity ISSUE-KEY) |

### Sprints

| Problem | Recovery Steps |
|---------|----------------|
| **Sprint closed prematurely** | Cannot reopen; move issues to new sprint; consider sprint report for metrics |
| **Wrong issues in sprint** | jira-agile sprint move-issues to correct sprint or backlog |
| **Sprint deleted** | Cannot recover; issues move to backlog |

### Epics

| Problem | Recovery Steps |
|---------|----------------|
| **Issues removed from epic** | jira-agile epic add-issues to re-link |
| **Epic deleted** | Issues lose epic association; recreate epic and re-link |
| **Wrong epic link** | jira-agile epic remove-issues then add-issues to correct epic |

### Boards

| Problem | Recovery Steps |
|---------|----------------|
| **Board configuration changed** | Restore through JIRA UI (Project Settings > Board) |
| **Board deleted** | Recreate board; configure columns and filters |

### Components

| Problem | Recovery Steps |
|---------|----------------|
| **Component deleted** | Issues lose component; recreate with same name |
| **Wrong component lead** | jira-lifecycle component update to fix |

### Versions

| Problem | Recovery Steps |
|---------|----------------|
| **Version released early** | Can unrelease through JIRA UI or API |
| **Version deleted** | Issues lose fixVersion/affectedVersion; recreate |
| **Version archived** | Can unarchive through jira-lifecycle |

### Links

| Problem | Recovery Steps |
|---------|----------------|
| **Link removed** | jira-relationships link to recreate |
| **Wrong link type** | Remove incorrect link, create correct one |
| **Bulk links wrong** | jira-relationships unlink; then re-link correctly |

### Comments

| Problem | Recovery Steps |
|---------|----------------|
| **Comment deleted** | No recovery; content lost |
| **Comment wrong visibility** | jira-collaborate comment update to fix visibility |
| **Wrong comment text** | jira-collaborate comment update with corrected text |

### Attachments

| Problem | Recovery Steps |
|---------|----------------|
| **Attachment deleted** | Must re-upload from original source |
| **Wrong attachment** | Delete incorrect; upload correct file |

### Time Tracking

| Problem | Recovery Steps |
|---------|----------------|
| **Worklog deleted** | Must re-log time with jira-time log |
| **Wrong time logged** | jira-time update-worklog to correct |
| **Wrong estimate** | jira-time estimate to update |

### Service Management

| Problem | Recovery Steps |
|---------|----------------|
| **Customer removed** | jira-jsm customer add to restore access |
| **Organization deleted** | Recreate; re-add customers |
| **Approval recorded wrong** | Cannot change; approvals are audit trail |

### Administration

| Problem | Recovery Steps |
|---------|----------------|
| **Project deleted** | **NO RECOVERY** - all issues permanently lost |
| **Group deleted** | Recreate group; re-add members; update scheme references |
| **Permission scheme changed** | Review current grants; modify or reassign |
| **Automation rule disabled** | jira-admin automation enable |
| **Wrong scheme assigned** | Assign correct scheme; verify project access |

## Confirmation Patterns

### For `!` (Caution) Operations

```
"I'm going to [operation] on [target]. This will [effect]. Proceed?"
```

Example:
```
"I'm going to transition PROJ-123 to 'In Progress'. This will change
the status and may trigger notifications. Proceed?"
```

### For `!!` (Warning) Operations

```
"WARNING: This will [operation] on [target].
This [consequence]. Are you sure you want to proceed?"
```

Example:
```
"WARNING: This will delete the component 'Backend' from project PROJ.
Issues currently assigned to this component will lose that association.
Are you sure you want to proceed?"
```

### For `!!!` (Danger) Operations

```
"DANGER: This is IRREVERSIBLE.

Operation: [operation]
Target: [target]
Effect: [effect]

I strongly recommend running with --dry-run first to preview the changes.
If you've reviewed the dry-run output and want to proceed, confirm by
typing 'yes' or 'proceed'."
```

Example:
```
"DANGER: This is IRREVERSIBLE.

Operation: Bulk delete issues
Target: 47 issues matching 'project = CLEANUP AND created < -90d'
Effect: All 47 issues will be permanently deleted with no recovery option.

I strongly recommend running with --dry-run first to preview the changes.
If you've reviewed the dry-run output and want to proceed, confirm by
typing 'yes' or 'proceed'."
```

## Bulk Operation Safety

### Batch Size Recommendations

| Issue Count | Approach |
|-------------|----------|
| 1-10 | Direct execution (still use --dry-run for destructive ops) |
| 11-50 | Always --dry-run first |
| 51-100 | --dry-run + explicit confirmation |
| 101-500 | Consider batching; checkpoint if available |
| 500+ | Batch with checkpointing; run during off-peak hours |

### Progressive Disclosure for Bulk Operations

1. **First**: Run JQL search to show matching issues
2. **Then**: Show count and ask for confirmation
3. **Next**: Run with --dry-run to preview exact changes
4. **Finally**: Execute after user confirms preview

### Checkpoint Recovery

For large bulk transitions that support checkpointing:

```bash
# List pending checkpoints
jira-as bulk transition --list-checkpoints

# Resume from checkpoint
jira-as bulk transition --resume CHECKPOINT_ID
```

## Emergency Procedures

### Rate Limit (429 Error)

```
1. Stop current operation
2. Wait 1-2 minutes before retry
3. If bulk operation, reduce batch size
4. Consider running during off-peak hours (overnight)
```

### Authentication Failure (401)

```
1. Verify JIRA_API_TOKEN is set and not expired
2. Verify JIRA_EMAIL matches token owner
3. Test with: jira-as admin user search "your.name"
4. Regenerate token at: https://id.atlassian.com/manage-profile/security/api-tokens
```

### Permission Denied (403)

```
1. Check user permissions: jira-as admin permissions check --project PROJ
2. Identify missing permission from error message
3. Request access from JIRA admin or use jira-admin to self-add to role
```

### Operation Timeout

```
1. Check if operation partially completed
2. For search: reduce result count with --max-results
3. For bulk: use smaller batches
4. Check JIRA instance health (may be under load)
```

### Accidental Bulk Operation

If you accidentally started a destructive bulk operation:

```
1. Press Ctrl+C immediately to cancel
2. Check what was changed (jira-search or manual review)
3. Use activity log to identify affected issues
4. Apply recovery procedures for each change type
```

## Audit Trail

JIRA maintains an audit trail for:
- Issue changes (activity history)
- Project changes (project audit log)
- Approvals (immutable approval history)
- User/group changes (admin audit log)

To check what changed:
```bash
# Issue activity
jira-as collaborate activity PROJ-123

# Check recent changes by user
jira-as search query "updatedBy = currentUser() AND updated >= -1h"
```

## Best Practices Summary

1. **Always dry-run** destructive operations
2. **Confirm issue counts** match expectations
3. **Use --max-results** to limit scope during testing
4. **Check permissions** before operations that might fail
5. **Run bulk ops** during off-peak hours
6. **Keep backups** of export data before modifications
7. **Document** what was changed for audit purposes
8. **Test with single item** before bulk operations
