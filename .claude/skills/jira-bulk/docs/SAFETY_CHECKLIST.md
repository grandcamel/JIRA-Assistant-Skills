# Bulk Operations Safety Checklist

Use this checklist before executing any bulk operation affecting >50 issues.

---

## Quick Checklist (Fast Track)

For operations affecting 50-200 issues:

```markdown
- [ ] JQL tested in JIRA UI (returns expected issues)
- [ ] Dry-run executed and reviewed
- [ ] Test batch (5-10 issues) successful
- [ ] Affected team notified
- [ ] Rollback plan identified
```

---

## Full Checklist

For operations affecting >200 issues or high-impact changes:

### Planning Phase

```markdown
- [ ] Clear objective defined (what and why)
- [ ] Target issues identified with JQL query
- [ ] JQL verified in JIRA search (correct count)
- [ ] Automation rules reviewed (Slack, email, etc.)
- [ ] Stakeholders identified
- [ ] Rollback strategy determined
- [ ] Scheduled during low-usage window
```

### Validation Phase

```markdown
- [ ] JQL query tested in JIRA UI
- [ ] Dry-run preview executed: `--dry-run`
- [ ] Dry-run output fully reviewed
- [ ] Sample of 5-10 issues verified manually
- [ ] Edge cases considered (subtasks, linked issues)
- [ ] No production incidents in progress
```

### Approval Phase (if >200 issues or high impact)

```markdown
- [ ] Operation documented in ticket/wiki
- [ ] Team lead approval obtained
- [ ] Affected team members notified
- [ ] Completion time communicated
```

### Execution Phase

```markdown
- [ ] Current state exported for rollback: `jql_search.py ... --format csv > before.csv`
- [ ] Checkpointing enabled (if >500 issues): `--enable-checkpoint`
- [ ] Test batch successful: `--max-issues 10`
- [ ] Test batch results verified in JIRA
- [ ] Full operation executed
- [ ] Progress monitored
```

### Post-Execution Phase

```markdown
- [ ] Success/failure counts reviewed
- [ ] Errors investigated
- [ ] Random sample spot-checked (5-10 issues)
- [ ] Automations verified (triggered correctly)
- [ ] Stakeholders notified of completion
- [ ] Issues encountered documented
```

---

## Risk Assessment

| Criteria | Low Risk | Medium Risk | High Risk |
|----------|----------|-------------|-----------|
| **Issue count** | 5-50 | 50-500 | 500+ |
| **Impact** | Internal workflow | Team visibility | Customer-facing |
| **Reversibility** | Easy | Manual revert | Irreversible |
| **Automation triggers** | None | Some | Many |

**Proceed if:** All Low Risk, or mostly Low with 1-2 Medium

**Get approval if:** Any High Risk, or multiple Medium

**Do NOT proceed if:** Multiple High Risk, or production risk + time pressure

---

## Pre-Operation Commands

```bash
# 1. Test JQL in JIRA UI first
# https://your-company.atlassian.net/issues/?jql=YOUR_QUERY

# 2. Run dry-run
python bulk_transition.py --jql "YOUR_JQL" --to "STATUS" --dry-run

# 3. Export current state
python jql_search.py "YOUR_JQL" --fields key,status,assignee --format csv > before.csv

# 4. Test small batch
python bulk_transition.py --jql "YOUR_JQL ORDER BY created ASC" --to "STATUS" --max-issues 5
```

---

## Rollback Plan Template

```markdown
## Rollback Plan for [Operation Name]

**Operation:** [Bulk transition 500 issues to 'Done']
**Date:** [YYYY-MM-DD]
**Executor:** [Your Name]

### Pre-Execution
- [ ] Exported to: /path/to/before.csv
- [ ] Saved JQL: [query]

### Rollback Procedure (if needed within 24h)
1. Run: `python bulk_transition.py --jql "project=PROJ AND status='Done' AND updated >= -1h" --to "In Progress"`
2. Verify count matches original
3. Spot-check 10 issues

### Rollback Procedure (if needed after 24h)
1. Use CSV import to restore
2. Manual review of automation changes
3. Contact JIRA admin for backup (last resort)
```

---

## Related Documentation

- [Quick Start](QUICK_START.md) - Get started in 5 minutes
- [Error Recovery](ERROR_RECOVERY.md) - Handle failures
- [Best Practices](BEST_PRACTICES.md) - Full guidance
