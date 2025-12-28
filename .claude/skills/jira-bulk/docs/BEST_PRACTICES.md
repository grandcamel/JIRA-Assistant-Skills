# JIRA Bulk Operations Best Practices

Comprehensive guide for safely executing bulk operations on JIRA issues at scale.

---

## Quick Reference Card

### Pre-Flight Commands

```bash
# 1. Test JQL in JIRA UI first
# https://your-company.atlassian.net/issues/?jql=YOUR_QUERY

# 2. Run dry-run preview
python bulk_transition.py --jql "YOUR_JQL" --to "STATUS" --dry-run

# 3. Export current state (for rollback)
python jql_search.py "YOUR_JQL" --fields key,status,assignee --format csv > before.csv

# 4. Test on small batch
python bulk_transition.py --jql "YOUR_JQL ORDER BY created ASC" --to "STATUS" --max-issues 5
```

### Execution Commands

```bash
# Small (<50 issues)
python bulk_transition.py --jql "YOUR_JQL" --to "STATUS"

# Medium (50-500 issues)
python bulk_transition.py --jql "YOUR_JQL" --to "STATUS" --batch-size 100

# Large (500+ issues)
python bulk_transition.py --jql "YOUR_JQL" --to "STATUS" \
  --batch-size 200 --enable-checkpoint --delay-between-ops 0.3
```

### Common Operations

| Operation | Command |
|-----------|---------|
| Transition | `bulk_transition.py --jql "..." --to "STATUS"` |
| Assign | `bulk_assign.py --jql "..." --assignee USER` |
| Unassign | `bulk_assign.py --jql "..." --unassign` |
| Priority | `bulk_set_priority.py --jql "..." --priority LEVEL` |
| Clone | `bulk_clone.py --jql "..." --include-subtasks --include-links` |

### Quick Safety Checklist

```markdown
- [ ] Dry-run executed and reviewed
- [ ] Test batch (5-10 issues) successful
- [ ] JQL verified in JIRA UI
- [ ] Current state exported (if needed)
- [ ] Stakeholders notified (if >50 issues)
```

For complete checklist, see [Safety Checklist](SAFETY_CHECKLIST.md).

---

## Table of Contents

1. [When to Use Bulk Operations](#when-to-use-bulk-operations)
2. [Decision Matrix](#decision-matrix)
3. [Batch Size Recommendations](#batch-size-recommendations)
4. [Rate Limiting Awareness](#rate-limiting-awareness)
5. [Testing in Non-Production](#testing-in-non-production)
6. [Communication Best Practices](#communication-best-practices)
7. [Scheduling Bulk Operations](#scheduling-bulk-operations)
8. [Common Pitfalls to Avoid](#common-pitfalls-to-avoid)

For detailed guides on specific topics:
- [Safety Checklist](SAFETY_CHECKLIST.md) - Pre-flight verification
- [Checkpoint Guide](CHECKPOINT_GUIDE.md) - Resume interrupted operations
- [Error Recovery](ERROR_RECOVERY.md) - Handle failures and rollback

---

## When to Use Bulk Operations

### Good Candidates

**Sprint Management:**
- Moving incomplete sprint items to next sprint
- Closing all done items at sprint end
- Reassigning spilled-over work

**Release Management:**
- Tagging issues with fix version
- Transitioning completed features to "Released"
- Closing old bugs after verification

**Team Transitions:**
- Reassigning issues when team members leave/join
- Redistributing work during team reorganization

**Cleanup Operations:**
- Archiving stale issues (no updates in 90+ days)
- Standardizing labels or components
- Fixing mass data quality issues

### When NOT to Use Bulk Operations

| Scenario | Risk | Better Approach |
|----------|------|----------------|
| Production incidents | Wrong changes = downtime | Manual, deliberate fixes |
| Customer-facing issues | Errors visible externally | Individual updates with review |
| Complex workflow transitions | May trigger unwanted automations | Test individually first |
| Issues with SLA commitments | Could breach SLAs | Coordinate with support team |

---

## Decision Matrix

Use this matrix to determine if a bulk operation is appropriate:

| Criteria | Green Light | Yellow Light | Red Light |
|----------|-------------|--------------|-----------|
| **Volume** | 5-500 issues | 500-2,000 issues | 2,000+ issues |
| **Impact** | Internal workflow | Team visibility | Customer-facing |
| **Reversibility** | Easy to undo | Manual revert needed | Irreversible |
| **Automation risk** | No triggers | Some triggers | Many automations |

**Proceed if:** All Green Light, or mostly Green with 1-2 Yellow

**Get approval if:** Any Red Light, or multiple Yellow Lights

**Do NOT proceed if:** Multiple Red Lights, or production risk + time pressure

---

## Batch Size Recommendations

### JIRA API Limits

| Limit Type | Value | Notes |
|------------|-------|-------|
| **Hard limit per request** | 1,000 issues | Including subtasks |
| **Concurrent requests** | 5 | Across all users |
| **Recommended max per script** | 10,000 issues | Use checkpointing |

### Recommended Batch Sizes

| Total Issues | Batch Size | Rationale |
|--------------|------------|-----------|
| 1-50 | Single batch | No batching needed |
| 50-100 | Single batch | Monitor for errors |
| 100-500 | 100 | Balance speed vs. error recovery |
| 500-1,000 | 200 | Use checkpointing |
| 1,000+ | 200-500 | Required: checkpointing + scheduling |

### When to Reduce Batch Size

- Issues have many custom fields (100+)
- Including subtasks (doubles field count)
- Cloning with links (triples field count)

---

## Rate Limiting Awareness

### Handling 429 Errors

The client handles rate limiting automatically with exponential backoff. If retries fail:

```bash
# Option 1: Increase delay
--delay-between-ops 0.5

# Option 2: Reduce batch size
--batch-size 50

# Option 3: Both
--batch-size 50 --delay-between-ops 0.5
```

### Delay Configuration

| Operation Size | Recommended Delay | Rationale |
|----------------|-------------------|-----------|
| <50 issues | 0.1s (default) | Fast, low risk |
| 50-200 issues | 0.2s | Balance speed/limits |
| 200-500 issues | 0.3s | Avoid rate limiting |
| 500-1,000 issues | 0.5s | Stay under limits |
| 1,000+ issues | 1.0s | Maximum caution |

### Optimal Scheduling

**Best times:**
- Weekend mornings (Saturday 8-10 AM)
- Weekday evenings (7-9 PM)
- During scheduled maintenance

**Avoid:**
- Weekday peak hours (9 AM - 5 PM)
- Sprint ceremonies
- Release deployment windows

---

## Testing in Non-Production

**Golden Rule: Test bulk operations in staging before production.**

### When Staging is Available

1. Verify staging has similar workflow configuration
2. Create test issues matching production scenario
3. Run dry-run in staging
4. Execute and verify results
5. Test rollback procedure
6. Document findings

### When Staging is NOT Available

Use small production test batch:

```bash
# Test on 5-10 issues first
python bulk_transition.py \
  --jql "project=PROJ AND status='In Progress' ORDER BY created ASC" \
  --to "Done" \
  --max-issues 5
```

**Always run a small test batch in production after staging validation.**

---

## Communication Best Practices

### When to Communicate

| Operation Size | Communication Required |
|----------------|------------------------|
| <10 issues | No notification needed |
| 10-50 issues | Inform team lead |
| 50-200 issues | Notify affected team |
| 200-500 issues | Notify multiple teams + managers |
| 500+ issues | Require approval + org-wide notice |

### Pre-Execution Notice Template

```markdown
Subject: [JIRA Bulk Operation] Transitioning 150 issues to 'Done'

Hi Team,

I will be performing a bulk operation on JIRA issues:

**What:** Transitioning 150 completed issues to 'Done' status
**When:** Today, Dec 26 at 2:00 PM EST (off-peak)
**Scope:** project=PROJ AND status='In Progress' AND resolution='Fixed'
**Duration:** Estimated 5-10 minutes
**Impact:** None expected
**Rollback:** Can reverse transition if needed

I've run a dry-run preview and tested on 5 sample issues successfully.

Let me know if you have concerns before 2:00 PM.
```

### Post-Execution Summary Template

```markdown
Subject: [COMPLETE] JIRA Bulk Operation Results

The bulk operation completed successfully:

**Results:**
- Success: 147/150 issues transitioned to 'Done'
- Failed: 3 issues (already in 'Done' status)
- Duration: 6 minutes

All successfully transitioned issues: [Link to JQL query]
```

---

## Scheduling Bulk Operations

### Duration Estimation

```
Duration (seconds) = (Issue Count x Delay) + (Issue Count x Avg API Time)

Example: 500 issues, 0.2s delay, 0.3s API time
= (500 x 0.2) + (500 x 0.3) = 250 seconds = ~4 minutes

Add 20% buffer for retries: 4 min x 1.2 = 5 minutes
```

| Issue Count | Delay | Estimated Duration |
|-------------|-------|-------------------|
| 10 | 0.1s | 5 seconds |
| 50 | 0.1s | 24 seconds |
| 100 | 0.2s | 1 minute |
| 500 | 0.2s | 5 minutes |
| 1,000 | 0.3s | 12 minutes |
| 5,000 | 0.5s | 1.2 hours |

---

## Common Pitfalls to Avoid

### Anti-Patterns

| Pitfall | Problem | Solution |
|---------|---------|----------|
| No dry-run | Unexpected changes | ALWAYS dry-run for >10 issues |
| Untested JQL | Wrong issues affected | Test JQL in JIRA UI first |
| No export | Can't rollback | Export before major changes |
| Peak hour execution | Rate limiting | Schedule off-peak |
| No communication | Team surprised | Notify stakeholders |
| Skipping test batch | Mass failures | Test on 5-10 issues first |

### Common Mistakes

**Mistake 1: Not accounting for subtasks**

```bash
# BAD: Forgets subtasks are included
python bulk_transition.py --jql "project=PROJ AND type=Story" --to "Done"

# GOOD: Exclude or handle subtasks explicitly
python bulk_transition.py --jql "project=PROJ AND type=Story AND subtasks IS EMPTY" --to "Done"
```

**Mistake 2: Triggering unwanted automations**

```bash
# BAD: May trigger 100 Slack notifications
python bulk_transition.py --jql "project=PROJ" --to "Done"

# GOOD: Review automation rules first, or add comment to suppress
python bulk_transition.py --jql "project=PROJ" --to "Done" --comment "[BULK] No notification needed"
```

**Mistake 3: Running multiple operations simultaneously**

```bash
# BAD: All hit rate limits
# Terminal 1: python bulk_transition.py ... &
# Terminal 2: python bulk_assign.py ... &

# GOOD: Run sequentially
python bulk_transition.py ... && sleep 60 && python bulk_assign.py ...
```

### Red Flags - Stop and Re-evaluate

- Dry-run count differs significantly from expectation (>10% variance)
- Many errors in test batch (>20% failure rate)
- Rate limit errors appearing frequently
- Automations triggering unexpectedly
- Team members reporting issues during execution

---

## Additional Resources

### Related Documentation

- [Quick Start](QUICK_START.md) - Get started in 5 minutes
- [Operations Guide](OPERATIONS_GUIDE.md) - Choose the right script
- [Checkpoint Guide](CHECKPOINT_GUIDE.md) - Resume interrupted operations
- [Error Recovery](ERROR_RECOVERY.md) - Handle failures and rollback
- [Safety Checklist](SAFETY_CHECKLIST.md) - Pre-flight verification

### Related Skills

- **jira-lifecycle**: Single-issue transitions and workflow understanding
- **jira-search**: JQL query building and testing
- **jira-ops**: Cache warming before large operations

### External Resources

- [JIRA Rate Limiting Documentation](https://developer.atlassian.com/cloud/jira/platform/rate-limiting/)
- [JIRA Bulk Operation APIs](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-bulk-operations/)

---

*Last updated: December 2025*
