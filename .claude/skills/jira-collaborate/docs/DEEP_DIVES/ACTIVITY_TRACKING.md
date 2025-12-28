# Activity Tracking Deep Dive

[Back to Index](../INDEX.md) | [Back to Quick Reference](../QUICK_REFERENCE.md)

---

Advanced guidance on using activity history and changelog.

## What Gets Tracked

**Tracked automatically:**
- All field changes (status, assignee, priority, etc.)
- Comments added/edited/deleted
- Attachments added/removed
- Links created/removed
- Watchers added/removed
- Custom field updates
- Workflow transitions

**Every change records:** User and timestamp

## Viewing Activity History

```bash
# View all activity on issue
python get_activity.py PROJ-123

# View in table format
python get_activity.py PROJ-123 --format table

# Filter by change type
python get_activity.py PROJ-123 --filter status
python get_activity.py PROJ-123 --filter assignee
python get_activity.py PROJ-123 --filter priority

# Export to JSON for analysis
python get_activity.py PROJ-123 --format json > history.json

# Export to CSV
python get_activity.py PROJ-123 --format csv > history.csv
```

## Analyzing Activity Patterns

| Question | How to Find |
|----------|-------------|
| How long was this in each status? | Filter by status changes, calculate time deltas |
| How many times was it reassigned? | Filter by assignee changes, count occurrences |
| Who has touched this issue? | List all unique users in changelog |
| When was priority escalated? | Filter by priority changes |
| What was the original scope? | View earliest description/summary |

## Best Practices for Maintainable History

**Encourage detailed updates:**
- Add meaningful comments when making significant changes
- Explain WHY changes happened, not just WHAT
- Link to related issues, PRs, or documentation

**Example of good documentation:**

```markdown
[Status changed: To Do -> In Progress]

Starting work on this. Found that PROJ-456 needs to be completed first
due to dependency on new authentication library. Coordinating with @team-lead.

Expected completion: End of sprint after PROJ-456 is done.
```

## Real-Time Activity Protocol

When making significant field changes, add comment explaining why:

```bash
# Transition issue and add context
python transition_issue.py PROJ-123 --transition "In Review"
python add_comment.py PROJ-123 --body "Moved to In Review. PR #234 ready. @reviewer please check."

# Reassign with handoff
python update_issue.py PROJ-123 --assignee alice@company.com
python add_comment.py PROJ-123 --body "@alice taking over from @bob. See Dec 24 comment for context."
```

## Retrospective Analysis

**Questions to ask:**
- Why did PROJ-123 move from "In Progress" back to "To Do"?
- Why was PROJ-456 reassigned 4 times?
- Why was PROJ-789's priority changed 3 times?

**Actionable insights:**
- Improve definition of ready
- Clarify ownership assignments
- Better initial estimation
- Identify systemic blockers

## Audit Trail for Compliance

**JIRA changelog provides:**
- Complete field change history
- User attribution
- Precise timestamps
- Old and new values

**Changelog does NOT provide:**
- Why changes were made (add comments!)
- Approval artifacts (use comments/attachments)
- External system correlation (link in comments)

**Best practice for audit compliance:**

```markdown
## Change Justification

**Change:** Priority increased from Medium to Critical
**Reason:** Production outage affecting 50% of users
**Approver:** @incident-manager
**Incident ticket:** INC-789
**Impact:** Requires immediate resolution per SLA

Attachment: incident_report_2025-12-26.pdf
```

## Changelog Export for Reporting

```bash
# Export issues in sprint with history
python jql_search.py "sprint = 'Sprint 42'" --format json > sprint42.json

# For each issue, get detailed history
for issue in PROJ-123 PROJ-124 PROJ-125; do
  python get_activity.py $issue --format json > "${issue}_history.json"
done
```

**Metrics to track:**
- Cycle time (created to done)
- Status dwell time (time in each status)
- Rework rate (backwards transitions)
- Collaboration rate (number of unique contributors)

---

[Back to Index](../INDEX.md) | [Back to Quick Reference](../QUICK_REFERENCE.md)
