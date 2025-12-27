# JIRA Bulk Operations Best Practices

Comprehensive guide for safely executing bulk operations on JIRA issues at scale.

---

## Table of Contents

1. [When to Use Bulk Operations](#when-to-use-bulk-operations)
2. [Decision Matrix](#decision-matrix)
3. [Safety Checklist](#safety-checklist)
4. [Batch Size Recommendations](#batch-size-recommendations)
5. [Dry-Run Strategy](#dry-run-strategy)
6. [Error Recovery Strategies](#error-recovery-strategies)
7. [Rate Limiting Awareness](#rate-limiting-awareness)
8. [Rollback Planning](#rollback-planning)
9. [Testing in Non-Production](#testing-in-non-production)
10. [Communication Best Practices](#communication-best-practices)
11. [Scheduling Bulk Operations](#scheduling-bulk-operations)
12. [Common Pitfalls to Avoid](#common-pitfalls-to-avoid)
13. [Quick Reference Card](#quick-reference-card)

---

## When to Use Bulk Operations

### Good Candidates for Bulk Operations

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
- Updating component ownership

**Cleanup Operations:**
- Archiving stale issues (no updates in 90+ days)
- Standardizing labels or components
- Fixing mass data quality issues

**Project Migrations:**
- Cloning issues to new project structure
- Standardizing priorities across teams
- Updating custom field values

### When NOT to Use Bulk Operations

| Scenario | Risk | Better Approach |
|----------|------|----------------|
| Production incidents | Wrong changes = downtime | Manual, deliberate fixes |
| Customer-facing issues | Errors visible externally | Individual updates with review |
| Complex workflow transitions | May trigger unwanted automations | Test individually first |
| Issues with SLA commitments | Could breach SLAs | Coordinate with support team |
| Cross-project dependencies | May break dependent work | Update dependencies first |

---

## Decision Matrix

Use this matrix to determine if a bulk operation is appropriate:

| Criteria | Green Light | Yellow Light | Red Light |
|----------|-------------|--------------|-----------|
| **Volume** | 5-500 issues | 500-2,000 issues | 2,000+ issues |
| **Impact** | Internal workflow | Team visibility | Customer-facing |
| **Reversibility** | Easy to undo | Manual revert needed | Irreversible |
| **Automation risk** | No triggers | Some triggers | Many automations |
| **Time sensitivity** | Can wait | Need soon | Urgent |
| **Data quality** | Well-validated | Some unknowns | Uncertain data |

**Proceed if:**
- All Green Light, or
- Mostly Green with 1-2 Yellow (use extra caution)

**Get approval before proceeding if:**
- Any Red Light present, or
- Multiple Yellow Lights

**Do NOT proceed if:**
- Multiple Red Lights, or
- Production risk + time pressure

---

## Safety Checklist

Use this checklist before executing any bulk operation:

### Pre-Flight Checklist

```markdown
## Planning Phase
- [ ] Defined clear objective (what needs to change and why)
- [ ] Identified target issues with JQL query
- [ ] Verified JQL returns expected issues (run in JIRA search)
- [ ] Counted affected issues (is it within expected range?)
- [ ] Reviewed automation rules that may trigger
- [ ] Identified stakeholders to notify
- [ ] Determined rollback strategy
- [ ] Scheduled during low-usage window if possible

## Validation Phase
- [ ] Tested JQL query in JIRA UI (manual search)
- [ ] Ran dry-run preview (`--dry-run`)
- [ ] Reviewed dry-run output completely
- [ ] Verified sample of issues manually
- [ ] Checked for edge cases (linked issues, subtasks, etc.)
- [ ] Confirmed no production incidents in progress

## Approval Phase (if >100 issues or high impact)
- [ ] Documented operation in ticket/wiki
- [ ] Got approval from team lead
- [ ] Notified affected team members
- [ ] Set expectations for completion time

## Execution Phase
- [ ] Exported current state for rollback (if needed)
- [ ] Enabled checkpoint for large operations (>500 issues)
- [ ] Started with small test batch (10-20 issues)
- [ ] Verified test batch results
- [ ] Proceeded with full operation
- [ ] Monitored progress and errors

## Post-Execution Phase
- [ ] Reviewed success/failure counts
- [ ] Investigated any errors
- [ ] Spot-checked random sample of updated issues
- [ ] Verified automations triggered correctly
- [ ] Notified stakeholders of completion
- [ ] Documented any issues encountered
```

### Risk Assessment

**Low Risk (proceed with dry-run):**
- 5-50 issues
- Internal workflow updates
- Easy to manually revert

**Medium Risk (require approval):**
- 50-500 issues
- Affects team visibility
- Some automation triggers

**High Risk (require approval + staging test):**
- 500+ issues
- Customer-facing impact
- Complex workflow changes
- Multiple automations involved

---

## Batch Size Recommendations

### JIRA API Limits

| Limit Type | Value | Notes |
|------------|-------|-------|
| **Hard limit per request** | 1,000 issues | Including subtasks |
| **Concurrent requests** | 5 | Across all users |
| **Field limit** | 1,500,000 total | Combined across all issues |
| **Recommended max per script** | 10,000 issues | Use checkpointing |

### Recommended Batch Sizes

| Total Issues | Batch Size | Rationale |
|--------------|------------|-----------|
| 1-50 | Single batch | No batching needed |
| 50-100 | Single batch | Monitor for errors |
| 100-500 | 100 | Balance speed vs. error recovery |
| 500-1,000 | 100-200 | Stay under API limits |
| 1,000-5,000 | 200-500 | Use checkpointing |
| 5,000+ | 500 | Required: checkpointing + scheduling |

### Batch Configuration Examples

```bash
# Small operation: Single batch
python bulk_transition.py --jql "project=PROJ AND status='To Do'" --to "Done"

# Medium operation: Auto-calculated batching
python bulk_transition.py --jql "project=PROJ" --to "Done" --max-issues 500

# Large operation: Explicit batching with checkpointing
python bulk_transition.py \
  --jql "project=PROJ" \
  --to "Done" \
  --batch-size 200 \
  --enable-checkpoint \
  --max-issues 5000

# Very large operation: Multiple runs with offset
python bulk_transition.py --jql "project=PROJ ORDER BY created ASC" --to "Done" --max-issues 1000
# Wait for completion, then run again - JQL will return next batch
```

### Field Limit Considerations

The 1,500,000 field limit applies to the total number of fields across all issues in a single request:

```
Max issues per batch = 1,500,000 / (avg fields per issue)

Example:
- If each issue has 15,000 fields → max 100 issues per batch
- If each issue has 150 fields → max 1,000 issues per batch
- Typical issue has 50-100 fields → safe up to 1,000 issues
```

**When to reduce batch size:**
- Issues have many custom fields (100+)
- Including subtasks (doubles field count)
- Cloning with links (triples field count)

---

## Dry-Run Strategy

**ALWAYS use dry-run for operations affecting >10 issues.**

### Dry-Run Workflow

```bash
# Step 1: Run dry-run preview
python bulk_transition.py \
  --jql "project=PROJ AND status='In Progress'" \
  --to "Done" \
  --dry-run

# Step 2: Review output carefully
# - Verify issue count matches expectation
# - Spot-check random issues in the list
# - Confirm no unexpected issues included

# Step 3: Test on small batch first
python bulk_transition.py \
  --jql "project=PROJ AND status='In Progress' ORDER BY created ASC" \
  --to "Done" \
  --max-issues 10

# Step 4: Verify test batch results in JIRA UI

# Step 5: Execute full operation
python bulk_transition.py \
  --jql "project=PROJ AND status='In Progress'" \
  --to "Done"
```

### What to Look For in Dry-Run Output

```bash
# Example dry-run output
[DRY RUN] Would process 47 issue(s):
  - PROJ-123: Fix login timeout
  - PROJ-124: Update API documentation
  - PROJ-125: Refactor authentication
  ...
```

**Verify:**
1. **Count**: Does the number match your expectation?
2. **Sample**: Are the first 5-10 issues correct?
3. **Outliers**: Any unexpected issues in the list?
4. **Keys**: Correct project prefix?
5. **Scope**: All issues from intended JQL query?

### Dry-Run Limitations

**Dry-run does NOT:**
- Validate workflow transitions (may fail during execution)
- Check field permissions (may fail if user lacks access)
- Test automation triggers (won't show what automations run)
- Verify data constraints (may fail on unique field violations)

**Therefore, always test with small batch first!**

---

## Error Recovery Strategies

JIRA lacks native rollback, so plan for error recovery upfront.

### Pre-Execution: Export Current State

```bash
# Export current values before bulk update
python jql_search.py \
  "project=PROJ AND status='In Progress'" \
  --fields key,status,assignee,priority \
  --format csv \
  --output /tmp/before_bulk_update.csv

# Save for rollback if needed
```

### During Execution: Partial Failure Handling

All bulk scripts continue processing after errors and report:

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

**Recovery Actions:**

1. **Review error messages** - Determine if errors are expected
2. **Fix underlying issues** - Adjust permissions, workflow, etc.
3. **Re-run on failed issues** - Use `--issues PROJ-123,PROJ-125,...`
4. **Manual correction** - For 1-5 failures, fix manually

### Post-Execution: Verification

```bash
# Verify expected state after bulk operation
python jql_search.py \
  "project=PROJ AND status='Done' AND updated >= -1h" \
  --show-changes

# Compare counts before/after
# Before: "project=PROJ AND status='In Progress'" → 50 issues
# After: "project=PROJ AND status='Done' AND updated >= -1h" → 45 issues
# Failed: 5 issues → investigate manually
```

### Rollback Strategies

Since JIRA has no native rollback, use these approaches:

| Strategy | Use Case | Implementation |
|----------|----------|----------------|
| **Export + Re-import** | Field value changes | Use CSV export/import |
| **Reverse bulk operation** | Transitions, assignments | Run opposite operation |
| **Manual revert** | <10 failures | Fix individually |
| **Third-party app** | Complex revert | Use "Issue History for Jira" app |
| **Restore from backup** | Critical errors | Contact JIRA admin (last resort) |

#### Example: Reverse Bulk Transition

```bash
# Original operation: Moved 50 issues to "Done"
python bulk_transition.py --jql "project=PROJ AND status='In Progress'" --to "Done"

# Rollback: Move them back to "In Progress"
python bulk_transition.py \
  --jql "project=PROJ AND status='Done' AND updated >= -1h" \
  --to "In Progress" \
  --comment "Reverting bulk transition"
```

#### Example: Restore Assignees from Export

```bash
# Before bulk assignment, export current assignees
python jql_search.py "project=PROJ" --fields key,assignee --format csv > before.csv

# After bulk assignment, restore from CSV
# (requires custom script or JIRA CSV import)
```

### Checkpoint and Resume

For large operations (>500 issues), enable checkpointing:

```bash
# Enable checkpoint for resumability
python bulk_transition.py \
  --jql "project=PROJ" \
  --to "Done" \
  --enable-checkpoint

# If interrupted (network, timeout, Ctrl+C), resume:
python bulk_transition.py --list-checkpoints

# Output:
# Pending checkpoints:
#   transition-20251226-143022 (Progress: 450/1000 issues, 45% complete)

python bulk_transition.py --resume transition-20251226-143022 --to "Done"
```

**When to use checkpoints:**
- Operations affecting >500 issues
- Unreliable network connection
- Long-running operations (>5 minutes)
- Critical operations requiring completion guarantee

---

## Rate Limiting Awareness

### JIRA Cloud Rate Limits

JIRA Cloud uses a **points-based rate limiting model**:

| Rate Limit Type | Limit | Time Window |
|-----------------|-------|-------------|
| **Burst rate** | Varies by endpoint | Seconds |
| **Hourly quota** | Varies by plan | 1 hour |
| **Per-issue writes** | 60 per issue | 1 minute |
| **Concurrent requests** | 5 for bulk APIs | At any time |

### Handling 429 Errors

When you receive HTTP 429 (Rate Limit Exceeded):

```
Error: Rate limit exceeded (429)
Retry-After: 30 seconds
```

**Built-in retry logic handles this automatically:**
- Exponential backoff (1s, 2s, 4s)
- Up to 3 retry attempts
- Respects `Retry-After` header

**If retries fail, adjust delay:**

```bash
# Increase delay between operations to 500ms
python bulk_transition.py \
  --jql "project=PROJ" \
  --to "Done" \
  --delay-between-ops 0.5

# Or reduce batch size
python bulk_transition.py \
  --jql "project=PROJ" \
  --to "Done" \
  --batch-size 50
```

### Delay Configuration

| Operation Size | Recommended Delay | Rationale |
|----------------|-------------------|-----------|
| <50 issues | 0.1s (default) | Fast, low risk |
| 50-200 issues | 0.2s | Balance speed/limits |
| 200-500 issues | 0.3s | Avoid rate limiting |
| 500-1,000 issues | 0.5s | Stay well under limits |
| 1,000+ issues | 1.0s | Maximum caution |

### Optimal Scheduling

**Best times for bulk operations:**
- **Off-peak hours**: Evenings, weekends (check your timezone)
- **Low-usage periods**: During team meetings, holidays
- **Maintenance windows**: Coordinated with JIRA admins

**Avoid:**
- **Peak hours**: Weekday mornings, after lunch
- **Sprint ceremonies**: Planning, retrospectives
- **Release windows**: When teams are actively updating JIRA
- **Incident response**: When system is under load

---

## Rollback Planning

### Rollback Decision Tree

```
Can the operation be easily reversed?
│
├─ YES (e.g., transition, assignment, priority)
│   └─ Execute reverse bulk operation
│
├─ PARTIAL (e.g., labels, components)
│   ├─ Small batch? → Manual revert
│   └─ Large batch? → Export + re-import or use app
│
└─ NO (e.g., deletion, complex workflow)
    ├─ Export critical data first
    ├─ Test in staging
    └─ Consider if bulk is appropriate
```

### Reversible Operations

| Operation | Reverse Method | Notes |
|-----------|----------------|-------|
| **Transition** | Reverse transition | May require different workflow path |
| **Assignment** | Reassign to original | Export assignees first |
| **Priority** | Set to original priority | Export priorities first |
| **Labels** (add) | Remove labels | Simple to reverse |
| **Labels** (remove) | Re-add labels | Need original list |
| **Component** (add) | Remove component | Simple to reverse |
| **Fix version** (add) | Remove version | Simple to reverse |

### Non-Reversible Operations

| Operation | Risk | Mitigation |
|-----------|------|------------|
| **Deletion** | CRITICAL | Test in staging, backup data, require approval |
| **Clone** | Moderate | Can delete clones, but links may persist |
| **Custom field** (complex) | High | Export before, test thoroughly |
| **Workflow** (complex) | High | May trigger many automations |

### Rollback Template

Document your rollback plan before executing:

```markdown
## Rollback Plan for [Operation Name]

**Operation:** [Bulk transition 500 issues to 'Done']
**Date:** [2025-12-26]
**Executor:** [John Doe]

### Pre-Execution Export
- [ ] Exported current state to: /path/to/export.csv
- [ ] Verified export contains all affected issues
- [ ] Saved JQL query for re-running operation

### Rollback Procedure
If rollback needed within 24 hours:
1. Run reverse transition: `python bulk_transition.py --jql "..." --to "In Progress"`
2. Verify issue count matches original
3. Spot-check 10 random issues

If rollback needed after 24 hours:
1. Use CSV import to restore original values
2. Manual review of automation-triggered changes
3. Contact JIRA admin for backup restore (last resort)

### Success Criteria
- [ ] All issues in expected status
- [ ] No unexpected side effects from automations
- [ ] Stakeholders notified of completion
```

---

## Testing in Non-Production

**Golden Rule: Test bulk operations in staging before production.**

### Staging Environment Checklist

```markdown
## Staging Test Plan

### Environment Verification
- [ ] Staging JIRA instance available
- [ ] Similar workflow configuration to production
- [ ] Test data available (or can be created)
- [ ] Same custom fields as production
- [ ] Same automation rules (or disabled)

### Test Execution
- [ ] Created test issues matching production scenario
- [ ] Ran dry-run in staging
- [ ] Executed bulk operation on test issues
- [ ] Verified results match expectations
- [ ] Checked for automation side effects
- [ ] Tested rollback procedure
- [ ] Documented any issues encountered

### Production Readiness
- [ ] All staging tests passed
- [ ] Rollback procedure validated
- [ ] JQL query adjusted for production data
- [ ] Timing estimated based on staging run
- [ ] Stakeholders notified of upcoming change
```

### When Staging is Not Available

If you don't have a staging environment:

1. **Use small production test batch:**
   ```bash
   # Test on 5-10 issues first
   python bulk_transition.py \
     --jql "project=PROJ AND status='In Progress' ORDER BY created ASC" \
     --to "Done" \
     --max-issues 5
   ```

2. **Create test project in production:**
   - Create temporary project for testing
   - Clone a few representative issues
   - Test bulk operation
   - Verify results
   - Delete test project

3. **Use personal sandbox:**
   - Create issues in your personal project
   - Test bulk operation behavior
   - Note: Won't test automations or permissions

### Staging vs. Production Differences

**Be aware of:**
- Different user permissions (staging may be more permissive)
- Different automation rules (may be disabled in staging)
- Different data quality (staging may be cleaner)
- Different workflow customizations
- Different API rate limits (staging may be more lenient)

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

### Communication Templates

#### Pre-Execution Notice

```markdown
Subject: [JIRA Bulk Operation] Transitioning 150 issues to 'Done'

Hi Team,

I will be performing a bulk operation on JIRA issues:

**What:** Transitioning 150 completed issues to 'Done' status
**When:** Today, Dec 26 at 2:00 PM EST (off-peak)
**Scope:** project=PROJ AND status='In Progress' AND resolution='Fixed'
**Duration:** Estimated 5-10 minutes
**Impact:** None expected, all issues already completed
**Rollback:** Can reverse transition if needed

**Why:** Sprint cleanup - moving verified fixes to Done status

I've run a dry-run preview and tested on 5 sample issues successfully.

Let me know if you have any concerns before 2:00 PM.

Thanks,
[Your Name]
```

#### Post-Execution Summary

```markdown
Subject: [COMPLETE] JIRA Bulk Operation Results

Hi Team,

The bulk operation completed successfully:

**Results:**
- ✓ Success: 147/150 issues transitioned to 'Done'
- ✗ Failed: 3 issues (already in 'Done' status)
- Duration: 6 minutes

**Failed Issues:**
- PROJ-123: Already in 'Done' status
- PROJ-456: Already in 'Done' status
- PROJ-789: Already in 'Done' status

These failures were expected and require no action.

All successfully transitioned issues: [Link to JQL query]

Thanks,
[Your Name]
```

#### Error Escalation

```markdown
Subject: [URGENT] JIRA Bulk Operation - Errors Encountered

Hi [Manager],

I encountered unexpected errors during a bulk operation:

**Operation:** Bulk transition to 'Done'
**Expected:** 150 issues
**Results:** 45 succeeded, 105 failed
**Error:** "Permission denied" for most issues

**Immediate Actions Taken:**
1. Stopped further processing
2. Verified my permissions (appear correct)
3. Checked JIRA status (no incidents reported)

**Next Steps:**
1. Need JIRA admin to verify permission configuration
2. May need to revert 45 successful transitions
3. Investigating root cause before re-attempting

**Impact:**
- 45 issues incorrectly transitioned (can revert)
- Sprint velocity calculation may be affected
- Team members may see incorrect issue counts

Please advise on priority and whether to proceed with rollback.

Thanks,
[Your Name]
```

### Stakeholder Matrix

| Stakeholder | When to Notify | Information Needed |
|-------------|----------------|-------------------|
| **Team Lead** | >10 issues | Operation type, count, timing |
| **Team Members** | >50 issues | Impact on their work, estimated duration |
| **Product Manager** | >200 issues | Business justification, risk assessment |
| **JIRA Admin** | >500 issues or high risk | Technical details, resource usage |
| **Organization** | Critical operations | All of the above + approval required |

---

## Scheduling Bulk Operations

### Timing Considerations

**Optimal Times:**
```
Best:
- Weekend mornings (Saturday 8-10 AM)
- Weekday evenings (7-9 PM)
- Public holidays (if team is off)

Good:
- Weekday early morning (6-8 AM)
- Weekday late afternoon (5-7 PM)
- During scheduled maintenance

Avoid:
- Weekday peak hours (9 AM - 5 PM)
- Sprint planning/retro times
- Release deployment windows
- Known high-traffic periods
```

### Scheduling Strategies

#### Immediate Execution (for small operations)

```bash
# Small operation: Execute immediately
python bulk_transition.py --jql "project=PROJ" --to "Done" --max-issues 20
```

#### Scheduled Execution (for large operations)

```bash
# Option 1: Use cron (Unix/Linux/Mac)
# Edit crontab: crontab -e
# Run every Saturday at 8 AM
0 8 * * 6 /usr/bin/python3 /path/to/bulk_transition.py --jql "project=PROJ" --to "Done"

# Option 2: Use at command (Unix/Linux/Mac)
# Run today at 7 PM
echo "python bulk_transition.py --jql 'project=PROJ' --to 'Done'" | at 19:00

# Option 3: Use Task Scheduler (Windows)
# Create scheduled task via GUI or schtasks command
```

#### Distributed Execution (for very large operations)

```bash
# Split into time windows to avoid rate limiting
# Window 1: Saturday 8:00 AM - Process 1000 issues
python bulk_transition.py --jql "project=PROJ ORDER BY created ASC" --to "Done" --max-issues 1000

# Window 2: Saturday 10:00 AM - Process next 1000 issues
python bulk_transition.py --jql "project=PROJ ORDER BY created ASC" --to "Done" --max-issues 1000

# Window 3: Saturday 12:00 PM - Process remaining issues
python bulk_transition.py --jql "project=PROJ ORDER BY created ASC" --to "Done" --max-issues 1000
```

### Duration Estimation

Use these formulas to estimate operation duration:

```
Duration (seconds) = (Issue Count × Delay) + (Issue Count × Avg API Response Time)

Example:
- 500 issues
- 0.2s delay between operations
- 0.3s average API response time
- Duration = (500 × 0.2) + (500 × 0.3) = 100 + 150 = 250 seconds ≈ 4 minutes

Add 20% buffer for retries and errors: 4 min × 1.2 = 5 minutes
```

| Issue Count | Delay | Estimated Duration | With Buffer |
|-------------|-------|-------------------|-------------|
| 10 | 0.1s | 4 seconds | 5 seconds |
| 50 | 0.1s | 20 seconds | 24 seconds |
| 100 | 0.2s | 50 seconds | 1 minute |
| 500 | 0.2s | 4 minutes | 5 minutes |
| 1,000 | 0.3s | 10 minutes | 12 minutes |
| 5,000 | 0.5s | 1 hour | 1.2 hours |

---

## Common Pitfalls to Avoid

### Anti-Patterns

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **No dry-run** | Unexpected changes | ALWAYS dry-run for >10 issues |
| **Untested JQL** | Wrong issues affected | Test JQL in JIRA UI first |
| **No export** | Can't rollback | Export before major changes |
| **Peak hour execution** | Rate limiting, team disruption | Schedule off-peak |
| **No communication** | Team surprised | Notify affected stakeholders |
| **Skipping test batch** | Mass failures | Test on 5-10 issues first |
| **Ignoring errors** | Partial failure goes unnoticed | Review error summary |
| **Too large batch** | Timeout or rate limit | Use recommended batch sizes |
| **No checkpoint** | Can't resume after interruption | Enable for >500 issues |
| **Production YOLO** | No staging test | Test in staging or small prod batch |

### Common Mistakes

**Mistake 1: Not accounting for subtasks**

```bash
# BAD: Forgets that subtasks are included in count
python bulk_transition.py --jql "project=PROJ AND type=Story" --to "Done"
# If stories have subtasks, actual count may be 2-3× expected

# GOOD: Account for subtasks explicitly
python bulk_transition.py --jql "project=PROJ AND type=Story AND subtasks IS EMPTY" --to "Done"
# Or transition subtasks separately first
```

**Mistake 2: Triggering unwanted automations**

```bash
# BAD: Bulk transition without checking automation rules
python bulk_transition.py --jql "project=PROJ" --to "Done"
# May trigger 100 Slack notifications, emails, etc.

# GOOD: Review automation rules first, consider disabling temporarily
# Or add comment to suppress notifications
python bulk_transition.py --jql "project=PROJ" --to "Done" --comment "[BULK] No notification needed"
```

**Mistake 3: Not verifying permissions**

```bash
# BAD: Assumes you have permission for all operations
python bulk_assign.py --jql "project=PROJ" --assignee john.doe

# GOOD: Test on small batch first to verify permissions
python bulk_assign.py --jql "project=PROJ ORDER BY created ASC" --assignee john.doe --max-issues 5
```

**Mistake 4: Ignoring issue links and dependencies**

```bash
# BAD: Closes issues without checking blockers
python bulk_transition.py --jql "type=Bug AND priority=Low" --to "Closed"
# May close bugs that are blocking active work

# GOOD: Exclude linked issues
python bulk_transition.py --jql "type=Bug AND priority=Low AND issueFunction NOT IN linkedIssuesOf('status IN (Open, \"In Progress\")')" --to "Closed"
```

**Mistake 5: Rate limiting yourself**

```bash
# BAD: Running multiple bulk operations simultaneously
# Terminal 1: python bulk_transition.py --jql "..." --to "Done" &
# Terminal 2: python bulk_assign.py --jql "..." --assignee john &
# Terminal 3: python bulk_set_priority.py --jql "..." --priority High &
# Result: All hit rate limits and fail

# GOOD: Run operations sequentially or space them out
python bulk_transition.py --jql "..." --to "Done" && \
  sleep 60 && \
  python bulk_assign.py --jql "..." --assignee john
```

### Red Flags

**Stop and re-evaluate if you see:**

- Dry-run count differs significantly from expectation (>10% variance)
- Many errors in test batch (>20% failure rate)
- Operation taking much longer than estimated
- Rate limit errors appearing frequently
- Automations triggering unexpectedly
- Team members reporting issues during execution
- JIRA performance degradation during operation

**Immediate actions:**
1. Stop the operation (Ctrl+C if using checkpoint)
2. Review what's gone wrong
3. Notify stakeholders
4. Assess whether to rollback
5. Investigate and fix root cause
6. Re-plan the operation

---

## Quick Reference Card

### Pre-Flight Commands

```bash
# Test JQL in JIRA UI first
# https://your-company.atlassian.net/issues/?jql=YOUR_QUERY

# Run dry-run preview
python bulk_transition.py --jql "YOUR_JQL" --to "STATUS" --dry-run

# Export current state
python jql_search.py "YOUR_JQL" --fields key,status,assignee --format csv > before.csv

# Test on small batch
python bulk_transition.py --jql "YOUR_JQL ORDER BY created ASC" --to "STATUS" --max-issues 5
```

### Execution Commands

```bash
# Small operation (<50 issues)
python bulk_transition.py --jql "YOUR_JQL" --to "STATUS"

# Medium operation (50-500 issues)
python bulk_transition.py --jql "YOUR_JQL" --to "STATUS" --batch-size 100

# Large operation (500+ issues)
python bulk_transition.py \
  --jql "YOUR_JQL" \
  --to "STATUS" \
  --batch-size 200 \
  --enable-checkpoint \
  --delay-between-ops 0.3

# Resume interrupted operation
python bulk_transition.py --resume operation-id --to "STATUS"
```

### Verification Commands

```bash
# Count affected issues
python jql_search.py "YOUR_JQL" --fields key --format json | jq '.total'

# Verify results
python jql_search.py "YOUR_JQL AND updated >= -1h" --show-changes

# Check for errors
# Review console output for "Failed: X/Y issues"
```

### Rollback Commands

```bash
# Reverse transition
python bulk_transition.py --jql "project=PROJ AND status='Done' AND updated >= -1h" --to "In Progress"

# Reverse assignment
python bulk_assign.py --jql "project=PROJ AND assignee=john AND updated >= -1h" --unassign

# Reverse priority
python bulk_set_priority.py --jql "project=PROJ AND priority=High AND updated >= -1h" --priority Medium
```

### Safety Checklist (Quick)

```markdown
- [ ] Dry-run executed and reviewed
- [ ] Test batch (5-10 issues) successful
- [ ] JQL verified in JIRA UI
- [ ] Current state exported (if needed)
- [ ] Stakeholders notified (if >50 issues)
- [ ] Scheduled during off-peak (if >200 issues)
- [ ] Rollback plan documented
```

### Decision Flow

```
1. Is this >10 issues?
   NO → Execute directly
   YES → Continue to 2

2. Is this >100 issues OR high impact?
   NO → Dry-run + test batch → Execute
   YES → Continue to 3

3. Is staging available?
   YES → Test in staging first
   NO → Continue to 4

4. Get approval + notify stakeholders
   → Export current state
   → Dry-run + test batch
   → Schedule off-peak
   → Execute with checkpointing
   → Verify results
   → Notify completion
```

### Common Operations Quick Ref

| Operation | Command Template |
|-----------|------------------|
| **Transition** | `python bulk_transition.py --jql "..." --to "STATUS"` |
| **Assign** | `python bulk_assign.py --jql "..." --assignee USER` |
| **Unassign** | `python bulk_assign.py --jql "..." --unassign` |
| **Priority** | `python bulk_set_priority.py --jql "..." --priority LEVEL` |
| **Clone** | `python bulk_clone.py --jql "..." --include-subtasks --include-links` |

### Rate Limit Quick Fix

```bash
# If getting rate limit errors (429):

# Option 1: Increase delay
--delay-between-ops 0.5

# Option 2: Reduce batch size
--batch-size 50

# Option 3: Both
--batch-size 50 --delay-between-ops 0.5
```

### Emergency Rollback

```bash
# Stop operation: Ctrl+C (if checkpointed, can resume later)

# Quick rollback (within 1 hour):
python bulk_transition.py \
  --jql "project=PROJ AND status='NEWSTATUS' AND updated >= -1h" \
  --to "OLDSTATUS" \
  --comment "Reverting bulk operation"

# Verify rollback:
python jql_search.py "project=PROJ AND status='OLDSTATUS' AND updated >= -5m"
```

---

## Additional Resources

### Related Documentation

- **jira-lifecycle skill**: For single-issue transitions and workflow understanding
- **jira-search skill**: For JQL query building and testing
- **jira-ops skill**: For cache warming before large operations

### External Resources

- [JIRA Rate Limiting Documentation](https://developer.atlassian.com/cloud/jira/platform/rate-limiting/)
- [JIRA Bulk Operation APIs](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-bulk-operations/)
- [JIRA Bulk Operation FAQs](https://developer.atlassian.com/cloud/jira/platform/bulk-operation-additional-examples-and-faqs/)

### Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Transition not available | Issue not in correct status | Check workflow with `get_issue.py --show-transitions` |
| Permission denied | Missing permissions | Verify project permissions in JIRA |
| Rate limit (429) | Too many requests | Increase `--delay-between-ops` or reduce `--batch-size` |
| Timeout | Operation too large | Enable `--checkpoint` and reduce `--batch-size` |
| Invalid JQL | Syntax error | Test JQL in JIRA UI search first |
| Wrong issue count | JQL includes unexpected issues | Review dry-run output, check for subtasks |

---

*Last updated: December 2025*
