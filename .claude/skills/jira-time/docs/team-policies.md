# Team Time Tracking Policies Guide

Guidance for engineering managers, team leads, and JIRA administrators on establishing, monitoring, and enforcing time tracking policies.

---

## Use this guide if you...

- Are a manager establishing time tracking requirements
- Need to onboard new team members on time logging
- Want to configure JIRA permissions for time tracking
- Need to monitor compliance and handle non-compliance
- Are setting up workflow validators for time tracking

For individual contributor guidance, see [IC Time Logging Guide](ic-time-logging.md).
For estimation practices, see [Estimation Guide](estimation-guide.md).

---

## Table of Contents

1. [Establishing Team Policies](#establishing-team-policies)
2. [Sample Policy Document](#sample-policy-document)
3. [Onboarding Checklist](#onboarding-checklist)
4. [Permission Configuration](#permission-configuration)
5. [Monitoring and Enforcement](#monitoring-and-enforcement)
6. [Handling Non-Compliance](#handling-non-compliance)

---

## Establishing Team Policies

### Key Policy Decisions

Before drafting a policy, decide on:

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Logging frequency | Daily, per-task, weekly | Daily (highest accuracy) |
| Minimum time unit | 15m, 30m, 1h | 15m for billing, 30m for internal |
| Comment requirements | Required, optional | Required (for audit trail) |
| Billable tracking | Labels, components, custom field | Custom field (if available) |
| Retroactive window | 1 day, 1 week, unlimited | 1 week (balance flexibility/accuracy) |

### Policy Communication

1. Document in team wiki/Confluence
2. Review in team meeting
3. Include in onboarding checklist
4. Post reminder in team Slack channel
5. Add to JIRA project description

---

## Sample Policy Document

```markdown
# Time Tracking Policy - Engineering Team

## Purpose
Accurate time tracking enables:
- Project cost estimation and budgeting
- Client billing and invoicing
- Resource capacity planning
- Process improvement

## Requirements

### Daily Time Logging
- Log time daily, before end of business day
- Minimum: All project work >15 minutes
- Include brief descriptive comment for each entry

### Accuracy
- Log actual time spent, not estimates
- Round to nearest 15-minute increment
- Include all work: coding, testing, meetings, reviews

### Billable vs Non-Billable
- Client project work: Always billable (label: billable)
- Internal tools/infrastructure: Non-billable (label: non-billable)
- Training/learning: Non-billable
- Administrative: Non-billable

### Deadlines
- Daily: Log time by 6 PM same day (preferred)
- Weekly: All time logged by Friday 5 PM
- Monthly: Finalize all time by 2nd business day of new month

## Consequences
- Weekly reminder for incomplete logging
- Manager review for repeated non-compliance
- May affect billable utilization metrics
```

---

## Onboarding Checklist

### Week 1 Checklist

- [ ] JIRA account created with time tracking permissions
- [ ] Time tracking policy document reviewed and signed
- [ ] Training session on worklog scripts completed
- [ ] Practice logging time on training tasks
- [ ] Assigned "time tracking buddy" for questions

### Training Script Walkthrough

```bash
# Day 1: Basic time logging
python add_worklog.py TRAIN-1 --time 2h --comment "JIRA onboarding training"

# Day 2: Time with estimates
python set_estimate.py TRAIN-2 --original "1d"
python add_worklog.py TRAIN-2 --time 4h --comment "Setting up development environment"

# Day 3: Reports
python time_report.py --user currentUser() --period this-week

# Day 4: Corrections
python get_worklogs.py TRAIN-2
python delete_worklog.py TRAIN-2 --worklog-id 12345 --dry-run
```

### First Month Goals

1. Achieve 90%+ daily logging compliance
2. Use descriptive comments on all worklogs
3. Set estimates before starting work
4. Generate personal weekly time report

---

## Permission Configuration

### Recommended JIRA Permission Scheme

| Permission | User Role | Reason |
|------------|-----------|--------|
| **Work on Issues** | All team members | Log own time |
| **Edit Own Worklogs** | All team members | Fix own mistakes |
| **Edit All Worklogs** | Team leads, Managers | Correct team entries |
| **Delete Own Worklogs** | All team members | Remove incorrect entries |
| **Delete All Worklogs** | Managers only | Prevent data loss |

### Setup via JIRA Admin

```
Settings > Issues > Permission Schemes >
  [Your Scheme] > Time Tracking Permissions
```

### Time Window Restrictions

Consider using workflow validators or third-party apps to:
- Prevent logging time more than 7 days in the past
- Require worklog comment (not empty)
- Require estimate before logging time
- Prevent logging time to closed issues

---

## Monitoring and Enforcement

### Weekly Compliance Report

```bash
# Find users who haven't logged time this week
python jql_search.py \
  "worklogAuthor = currentUser() AND worklogDate >= startOfWeek()" \
  --output json | jq '.issues | length'

# Find issues in progress with no time logged
python jql_search.py \
  "status = 'In Progress' AND timespent IS EMPTY"
```

### JQL Queries for Monitoring

```jql
# Issues with time logged but no estimate
timespent > 0 AND originalEstimate IS EMPTY

# Issues with estimate but no time logged (completed)
originalEstimate IS NOT EMPTY AND timespent IS EMPTY
AND status != "To Do"

# Issues logged to but not assigned
worklogDate >= startOfMonth() AND assignee IS EMPTY

# Issues with time but still "To Do"
status = "To Do" AND timespent > 0

# In progress for weeks with no recent time
status = "In Progress"
AND updated >= -14d
AND worklogDate <= -14d
```

### Monthly Audit Checklist

- [ ] Review users with <80% logging compliance
- [ ] Identify issues with missing estimates
- [ ] Check for orphaned worklogs (deleted issues)
- [ ] Verify billable/non-billable categorization
- [ ] Export time reports for invoicing

---

## Handling Non-Compliance

### Progressive Approach

**Level 1: Gentle reminder (automated)**
- Slack/email: "Reminder: Log your time daily"
- Frequency: Weekly if <80% compliance

**Level 2: Manager 1-on-1**
- Discuss barriers to logging time
- Provide additional training if needed
- Set improvement plan with specific goals

**Level 3: Formal process**
- Document repeated non-compliance
- May affect performance review
- Require daily confirmation of time logged

### Common Barriers and Solutions

| Barrier | Solution |
|---------|----------|
| "Too busy to log time" | Set calendar reminder; use timer apps |
| "Don't know how to log" | Additional training; pair with buddy |
| "Forget at end of day" | Slack bot reminder; workflow habit |
| "Issues don't map to my work" | Create overhead issues; discuss with PM |
| "Estimates feel like micromanagement" | Explain purpose; focus on project needs |

### Important Note

Focus on education and process improvement, not punishment. Time tracking should be:
- Easy (scripts, integrations)
- Valuable (team sees reports used)
- Consistent (same expectations for all)
- Reasonable (not excessive precision)

---

## Workflow Validators (Optional)

### Require Estimate to Start Work

Configure workflow to require Original Estimate before transitioning to "In Progress":
```
Transition: To Do -> In Progress
Condition: originalEstimate IS NOT EMPTY
Error: "Please set an estimate before starting work"
```

### Require Time Logged to Close

Configure workflow to require time logged before closing:
```
Transition: In Progress -> Done
Condition: timespent > 0
Error: "Please log time before closing this issue"
```

---

## Related Guides

- [IC Time Logging Guide](ic-time-logging.md) - For individual contributors
- [Estimation Guide](estimation-guide.md) - Estimation approaches and accuracy
- [Reporting Guide](reporting-guide.md) - Team time reports and analytics
- [Quick Reference: Permission Matrix](reference/permission-matrix.md) - Permission details

---

**Back to:** [SKILL.md](../SKILL.md) | [Best Practices Index](BEST_PRACTICES.md)
