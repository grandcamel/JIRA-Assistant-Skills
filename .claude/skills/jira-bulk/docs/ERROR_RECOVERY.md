# Error Recovery Playbook

How to handle failures and recover from bulk operation errors.

---

## Decision Tree: Something Went Wrong

```
Did the operation complete?
|
+-- YES, but some issues failed
|   |
|   +-- How many failed?
|       |
|       +-- 1-5 issues --> Fix manually
|       +-- 6-20 issues --> Re-run on failed issues
|       +-- 20+ issues --> Investigate root cause first
|
+-- NO, operation was interrupted
|   |
|   +-- Was checkpointing enabled?
|       |
|       +-- YES --> Resume with --resume
|       +-- NO --> Re-run full operation (already-processed issues will error as expected)
|
+-- YES, but results are wrong
    |
    +-- Need to rollback
```

---

## Partial Failures

### Understanding the Error Summary

After execution, you'll see:

```
Results:
  Success: 45/50 issues processed
  Failed: 5/50 issues

Errors:
  PROJ-123: Transition not available (issue in 'Done' status)
  PROJ-125: Permission denied (user lacks 'Transition Issues' permission)
  PROJ-130: Invalid resolution 'Deployed' (not available for this issue type)
  PROJ-142: Issue not found (may have been deleted)
  PROJ-145: Rate limit exceeded (429)
```

### Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| **Transition not available** | Issue already in target or wrong source status | Check workflow; skip or transition through intermediate status |
| **Permission denied** | Missing project/issue permissions | Contact JIRA admin |
| **Invalid resolution** | Resolution not available for issue type | Use correct resolution name |
| **Issue not found** | Deleted or no access | Skip issue; verify project access |
| **Rate limit (429)** | Too many requests | Increase `--delay-between-ops` |

### Re-running Failed Issues

```bash
# Collect failed issue keys from error output
python bulk_transition.py --issues PROJ-123,PROJ-125,PROJ-130 --to "Done"
```

---

## Interrupted Operations

### With Checkpointing

```bash
# List pending checkpoints
python bulk_transition.py --list-checkpoints

# Resume
python bulk_transition.py --resume transition-20251226-143022 --to "Done"
```

### Without Checkpointing

Re-run the full operation. Already-processed issues will fail with "already in status" errors, which is expected:

```bash
python bulk_transition.py --jql "project=PROJ" --to "Done"
# Expect errors for already-transitioned issues
```

---

## Rollback Strategies

### Strategy 1: Reverse Operation (Recommended)

For transitions, assignments, and priorities:

```bash
# Original: Moved issues to "Done"
python bulk_transition.py --jql "project=PROJ" --to "Done"

# Rollback: Move back to "In Progress"
python bulk_transition.py \
  --jql "project=PROJ AND status='Done' AND updated >= -1h" \
  --to "In Progress" \
  --comment "Reverting bulk operation"
```

### Strategy 2: Export Before, Restore After

```bash
# BEFORE operation: Export current state
python jql_search.py "project=PROJ" --fields key,status,assignee,priority --format csv > before.csv

# AFTER failure: Use CSV to restore (requires JIRA CSV import or manual scripting)
```

### Strategy 3: Manual Revert

For <10 failures, fix manually in JIRA UI.

---

## Pre-Execution Export

Always export critical data before major operations:

```bash
# Export current state
python jql_search.py \
  "project=PROJ AND status='In Progress'" \
  --fields key,status,assignee,priority,resolution \
  --format csv \
  --output /tmp/before_bulk_update.csv

# Save for potential rollback
```

---

## Verification After Recovery

```bash
# Verify expected state
python jql_search.py \
  "project=PROJ AND status='Done' AND updated >= -1h" \
  --fields key,status

# Compare counts
# Before: 50 issues in "In Progress"
# After: 45 in "Done" (5 failed)
```

---

## Emergency Procedures

### Stop Immediately

Press **Ctrl+C** to interrupt. If checkpointing is enabled, progress is saved.

### Quick Rollback (within 1 hour)

```bash
python bulk_transition.py \
  --jql "project=PROJ AND status='NEWSTATUS' AND updated >= -1h" \
  --to "OLDSTATUS" \
  --comment "Emergency rollback"
```

### Contact Admin

For critical issues requiring backup restore:
1. Document what happened
2. Collect error logs
3. Contact JIRA administrator
4. Request point-in-time restore (last resort)

---

## Prevention

1. **Always dry-run first:** `--dry-run`
2. **Test small batch:** `--max-issues 5`
3. **Enable checkpoints:** `--enable-checkpoint`
4. **Export before:** Save current state to CSV
5. **Document rollback plan:** Before executing

---

## Related Documentation

- [Checkpoint Guide](CHECKPOINT_GUIDE.md) - Resume interrupted operations
- [Safety Checklist](SAFETY_CHECKLIST.md) - Pre-flight verification
- [Best Practices](BEST_PRACTICES.md) - Full guidance
