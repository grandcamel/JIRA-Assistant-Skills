# JIRA & JSM Best Practices Guide

Comprehensive guide to JIRA Software and Jira Service Management best practices for effective project and service management.

---

## Table of Contents

1. [Issue Management](#issue-management)
2. [JQL Mastery](#jql-mastery)
3. [Agile & Scrum](#agile--scrum)
4. [Workflow Design](#workflow-design)
5. [Jira Service Management](#jira-service-management)
6. [Time Tracking](#time-tracking)
7. [Automation & Bulk Operations](#automation--bulk-operations)
8. [Team Collaboration](#team-collaboration)
9. [Reporting & Metrics](#reporting--metrics)
10. [Common Pitfalls](#common-pitfalls)

---

## Issue Management

### Writing Effective Summaries

**Do:**
- Start with a verb: "Add", "Fix", "Update", "Remove", "Implement"
- Be specific: "Fix login timeout on mobile Safari" not "Login broken"
- Include context: "Add dark mode toggle to settings page"

**Don't:**
- Use vague terms: "Various fixes", "Updates", "Changes"
- Include implementation details: "Change CSS from flex to grid"
- Write novels: Keep under 80 characters

**Examples:**
| Bad | Good |
|-----|------|
| Login | Fix session timeout on mobile devices |
| API stuff | Add rate limiting to REST endpoints |
| Bug | Fix null pointer in user registration |
| Performance | Optimize database queries for dashboard |

### Writing Effective Descriptions

Use this template:
```markdown
## Problem/Goal
[What is the issue or what needs to be achieved?]

## Context
[Why is this important? What's the impact?]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Notes (optional)
[Any implementation hints or constraints]
```

### Choosing Issue Types

| Type | Use When | Estimate? | Parent? |
|------|----------|-----------|---------|
| **Epic** | Feature spans 2+ sprints, needs breakdown | No | None |
| **Story** | User-facing value, fits in 1 sprint | Yes (points) | Epic |
| **Task** | Technical work, enabler, no direct user value | Yes (points) | Epic |
| **Bug** | Something worked before, now broken | Optional | Epic/None |
| **Subtask** | Breaking down a story/task | Optional (hours) | Story/Task |

### Using Labels Effectively

**Good Label Categories:**
- **Domain:** `security`, `performance`, `accessibility`, `compliance`
- **Priority indicators:** `quick-win`, `tech-debt`, `p0-critical`
- **Team/ownership:** `team-platform`, `team-mobile`, `needs-design`
- **Status qualifiers:** `needs-refinement`, `spike`, `blocked-external`

**Anti-patterns:**
- Don't duplicate status: `in-progress`, `done` (use workflow)
- Don't duplicate type: `bug-label` (use issue type)
- Don't use for assignment: `john-smith` (use assignee field)

### Using Components

Components represent architectural areas:
- `api`, `frontend`, `backend`, `database`
- `auth`, `payments`, `notifications`, `reporting`
- `ios`, `android`, `web`

**Benefits:**
- Filter by component in JQL: `component = api`
- Auto-assign component leads
- Track bugs by area
- Generate component-based reports

---

## JQL Mastery

### Essential Operators

| Operator | Use | Example |
|----------|-----|---------|
| `=` | Exact match | `status = "In Progress"` |
| `!=` | Not equal | `status != Done` |
| `~` | Contains text | `summary ~ login` |
| `!~` | Doesn't contain | `summary !~ test` |
| `IN` | Multiple values | `status IN (Open, "To Do")` |
| `NOT IN` | Exclude values | `priority NOT IN (Low, Lowest)` |
| `IS EMPTY` | No value | `assignee IS EMPTY` |
| `IS NOT EMPTY` | Has value | `"Story Points" IS NOT EMPTY` |
| `WAS` | Historical state | `status WAS "In Progress"` |
| `CHANGED` | Field changed | `status CHANGED` |

### Time-Based Queries

| Need | JQL |
|------|-----|
| Created today | `created >= startOfDay()` |
| Created this week | `created >= startOfWeek()` |
| Created last 7 days | `created >= -7d` |
| Updated in last hour | `updated >= -1h` |
| Due this week | `due >= startOfWeek() AND due <= endOfWeek()` |
| Overdue | `due < now() AND status != Done` |
| No activity in 30 days | `updated <= -30d AND status != Done` |
| Created in Q4 | `created >= 2024-10-01 AND created <= 2024-12-31` |

### User-Based Queries

| Need | JQL |
|------|-----|
| Assigned to me | `assignee = currentUser()` |
| I'm watching | `watcher = currentUser()` |
| I reported | `reporter = currentUser()` |
| Unassigned | `assignee IS EMPTY` |
| Team members | `assignee IN membersOf("developers")` |
| Assigned but not me | `assignee IS NOT EMPTY AND assignee != currentUser()` |

### Sprint & Agile Queries

| Need | JQL |
|------|-----|
| Current sprint | `sprint IN openSprints()` |
| Future sprints | `sprint IN futureSprints()` |
| Closed sprints | `sprint IN closedSprints()` |
| In backlog (no sprint) | `sprint IS EMPTY` |
| Specific sprint | `sprint = "Sprint 42"` |
| Spilled from sprint | `sprint WAS "Sprint 41" AND sprint = "Sprint 42"` |

### Complex Query Patterns

**Sprint Health Check:**
```jql
project = PROJ AND sprint IN openSprints()
AND (
  (status = "In Progress" AND updated <= -3d)
  OR (status = "To Do" AND "Story Points" IS EMPTY)
  OR ("Flagged" = Impediment)
)
ORDER BY priority DESC
```

**Release Readiness:**
```jql
project = PROJ AND fixVersion = "v2.0"
AND status != Done
ORDER BY priority DESC, created ASC
```

**Tech Debt Dashboard:**
```jql
labels IN (tech-debt, refactor)
AND status != Done
AND created <= -90d
ORDER BY created ASC
```

**Stale Issues:**
```jql
status NOT IN (Done, Closed, Resolved)
AND updated <= -30d
AND assignee IS NOT EMPTY
ORDER BY updated ASC
```

---

## Agile & Scrum

### Sprint Planning

**Before Planning:**
1. Backlog refined (stories have acceptance criteria)
2. Stories estimated (story points assigned)
3. Dependencies identified (blockers visible)
4. Capacity calculated (team availability known)

**Capacity Formula:**
```
Sprint Capacity = Team Velocity × 0.8
```
Use 80% to buffer for:
- Meetings, ceremonies
- Unplanned work, bugs
- Learning, mentoring
- Personal time off

**Sprint Goal Template:**
> "By end of sprint, [user/stakeholder] will be able to [capability] so that [value/outcome]."

### Story Point Estimation

**Fibonacci Scale:**
| Points | Meaning | Example |
|--------|---------|---------|
| 1 | Trivial, < 2 hours | Fix typo, config change |
| 2 | Small, half day | Add validation, simple UI tweak |
| 3 | Medium, 1-2 days | New endpoint, component refactor |
| 5 | Large, 2-3 days | Feature with tests, integration |
| 8 | Very large, ~1 week | Complex feature, multiple parts |
| 13 | Too big, should split | Epic-sized work |

**Estimation Tips:**
- Compare to past completed stories
- Include testing, code review, documentation
- Account for uncertainty (unknowns = higher)
- Don't convert to hours (they measure different things)

### Epic Management

**Epic Lifecycle:**
1. **Draft** - Initial idea, rough scope
2. **Refined** - User stories written, acceptance criteria defined
3. **Ready** - Estimated, prioritized, dependencies mapped
4. **In Progress** - Stories being worked in sprints
5. **Done** - All stories complete, value delivered

**Epic Sizing:**
- Target: 2-4 sprints to complete
- If larger: Break into smaller epics
- If smaller: Might just be a story

### Backlog Grooming

**Weekly Grooming Checklist:**
- [ ] Top 20 items refined with acceptance criteria
- [ ] Dependencies identified and linked
- [ ] Blockers flagged and escalated
- [ ] Stories estimated (at least 2 sprints worth)
- [ ] Old items reviewed (archive if stale)

**Definition of Ready:**
- [ ] Clear acceptance criteria
- [ ] Story points estimated
- [ ] No unresolved dependencies
- [ ] Technical approach understood
- [ ] Fits in one sprint

---

## Workflow Design

### Status Naming Conventions

**Use States, Not Actions:**
| Bad (Action) | Good (State) |
|--------------|--------------|
| Review | In Review |
| Test | In QA |
| Deploy | Deploying |
| Approve | Awaiting Approval |

**Standard Status Categories:**
| Category | Color | Statuses |
|----------|-------|----------|
| To Do | Blue | Backlog, To Do, Open |
| In Progress | Yellow | In Progress, In Review, In QA |
| Done | Green | Done, Closed, Released |

### Workflow Patterns

**Simple (3 statuses):**
```
To Do → In Progress → Done
```

**Development (5 statuses):**
```
Backlog → To Do → In Progress → In Review → Done
```

**With QA (6 statuses):**
```
Backlog → To Do → In Progress → In Review → In QA → Done
```

**With Deployment (7 statuses):**
```
Backlog → To Do → In Progress → In Review → In QA → Ready for Deploy → Done
```

### Transition Rules

**On "Start Progress":**
- Require: Assignee
- Auto-set: Start date

**On "Submit for Review":**
- Require: Pull request link (custom field)
- Condition: Subtasks complete

**On "Done":**
- Require: Resolution
- Auto-set: Resolution date
- Post-function: Send notification

### Work In Progress (WIP) Limits

**Recommended Limits:**
| Status | WIP Limit | Reasoning |
|--------|-----------|-----------|
| In Progress | 2 per person | Focus on completion |
| In Review | 1.5× team size | Reviews are quick |
| In QA | Team size | Matches throughput |

**Benefits:**
- Reduces context switching
- Surfaces bottlenecks
- Improves flow/cycle time
- Forces completion before starting

---

## Jira Service Management

### JSM vs JIRA Software

| Aspect | JIRA Software | JSM |
|--------|---------------|-----|
| **Users** | Developers, internal teams | Customers, employees |
| **Issue types** | Epic, Story, Bug, Task | Request, Incident, Problem, Change |
| **Views** | Boards, backlog | Queues, portal |
| **SLAs** | No | Yes (time to first response, resolution) |
| **Customer access** | No portal | Customer portal |
| **Knowledge base** | No | Confluence integration |
| **Automation** | Basic | Advanced with SLA triggers |

### Request Types Best Practices

**Naming:**
- User-friendly: "Get help with..." not "ITHELP-REQ"
- Action-oriented: "Request new software" not "Software request"
- Specific: "Reset password" not "Account issue"

**Field Configuration:**
- Minimize required fields (reduce friction)
- Use dropdown/select where possible
- Add helpful descriptions
- Group related fields

### SLA Configuration

**Common SLAs:**
| SLA | Priority | Goal |
|-----|----------|------|
| Time to First Response | Critical | 15 min |
| Time to First Response | High | 1 hour |
| Time to First Response | Medium | 4 hours |
| Time to First Response | Low | 8 hours |
| Time to Resolution | Critical | 4 hours |
| Time to Resolution | High | 8 hours |
| Time to Resolution | Medium | 24 hours |
| Time to Resolution | Low | 72 hours |

**SLA Best Practices:**
- Pause SLA when waiting on customer
- Use business hours calendars
- Exclude weekends/holidays
- Set escalation rules before breach

### Queue Management

**Standard Queues:**
1. **Unassigned** - New requests needing triage
2. **My Queue** - Assigned to current agent
3. **Breaching Soon** - SLA at risk
4. **Waiting for Customer** - Pending response
5. **By Priority** - Filtered by urgency

**Triage Process:**
1. Review request type and priority
2. Validate customer information
3. Assign to appropriate agent/team
4. Set initial response

---

## Time Tracking

### Estimation Best Practices

**Estimate Types:**
| Field | Meaning | When to Set |
|-------|---------|-------------|
| Original Estimate | Initial prediction | At creation |
| Remaining Estimate | Time left | After work logged |
| Time Spent | Actual work logged | When logging work |

**Common Formats:**
```
30m     → 30 minutes
2h      → 2 hours
1d      → 1 day (typically 8h)
1w      → 1 week (typically 5d)
1d 4h   → 1 day 4 hours
2h 30m  → 2 hours 30 minutes
```

### Worklog Best Practices

**Good Worklog Comments:**
- "Code review for PR #234"
- "Debugging production issue"
- "Sprint planning meeting"
- "Research authentication options"

**Bad Worklog Comments:**
- "Work"
- "" (empty)
- "Stuff"

**Logging Frequency:**
- Daily: Best for accuracy
- End of task: Acceptable
- End of week: Leads to inaccuracies

### Time Reports

**Useful Reports:**
- Time spent by assignee
- Time spent vs estimated (accuracy)
- Time by component (where effort goes)
- Time by issue type (bugs vs features)

---

## Automation & Bulk Operations

### When to Use Bulk Operations

**Good Candidates:**
- Sprint cleanup (move incomplete to next sprint)
- Release tagging (add fix version to issues)
- Reassignment (team member leaving)
- Label cleanup (rename/merge labels)

**Always Use Dry Run:**
```bash
# Preview changes first
python bulk_transition.py --jql "..." --dry-run

# Then execute
python bulk_transition.py --jql "..."
```

### Automation Patterns

**Auto-Assign on Creation:**
```
WHEN: Issue created
IF: Component = "api"
THEN: Assign to "API Team Lead"
```

**Auto-Transition on PR Merge:**
```
WHEN: Development field updated
IF: Contains merged PR
THEN: Transition to "In Review"
```

**SLA Breach Warning:**
```
WHEN: SLA at 75% of goal
THEN:
  - Add comment "SLA warning"
  - Send Slack notification
  - Escalate priority
```

---

## Team Collaboration

### Mentions & Notifications

**When to @mention:**
- Need specific person's input
- Escalating to someone
- Handoff between team members

**When NOT to @mention:**
- Generic updates (use comments)
- Large groups (use mailing lists)
- Automated notifications (use watchers)

### Effective Comments

**Structure:**
```markdown
## Update: [Brief title]

**Status:** On track / Blocked / At risk
**Progress:** Completed X, working on Y
**Next steps:** Will do Z
**Blockers:** [if any]
```

### Issue Linking

**Link Liberally:**
- Related work: "Relates to"
- Dependencies: "Blocks / Is blocked by"
- Duplicates: "Duplicates" (close one)
- Caused by: "Is caused by" (for bugs)

**Benefits:**
- See full picture on any issue
- Navigate related work easily
- Track dependencies
- Identify duplicate effort

---

## Reporting & Metrics

### Key Agile Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Velocity | Points completed / sprint | Consistent |
| Cycle Time | Done date - Start date | Decreasing |
| Lead Time | Done date - Created date | Decreasing |
| Sprint Burndown | Remaining work over time | Smooth decline |
| Escaped Defects | Bugs found post-release | Zero |

### Dashboard Best Practices

**Team Dashboard Should Include:**
- Sprint burndown
- Current sprint scope (issues)
- Blocked items (attention needed)
- Velocity trend (3-5 sprints)

**Manager Dashboard Should Include:**
- Cross-team velocity comparison
- Release progress
- Bug trend (created vs resolved)
- Cycle time trend

---

## Common Pitfalls

### Anti-Patterns to Avoid

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Mega-issues | Can't track progress | Split into smaller issues |
| Status sprawl | 10+ statuses | Simplify workflow |
| Label chaos | Inconsistent labeling | Define label taxonomy |
| Estimate gaming | Always hits estimate exactly | Embrace variance |
| Zombie issues | Old, forgotten, cluttering | Regular grooming |
| Meeting issues | "Attended standup" | Don't track meetings as issues |

### Red Flags

**In Sprint:**
- Same issue "In Progress" for 5+ days
- No comments for 3+ days
- Blocked with no action plan

**In Backlog:**
- Issues older than 6 months
- No acceptance criteria
- No estimate

**In Reports:**
- Velocity swings > 30%
- Cycle time increasing
- Sprint scope changes > 20%

---

## Quick Reference Card

### Keyboard Shortcuts (Board View)

| Key | Action |
|-----|--------|
| `c` | Create issue |
| `j/k` | Navigate issues |
| `o` | Open issue |
| `a` | Assign to me |
| `i` | Assign to someone |
| `l` | Add label |
| `m` | Comment |
| `/` | Search |

### Essential JQL

```jql
# My current work
assignee = currentUser() AND sprint IN openSprints() AND status != Done

# Team blockers
project = PROJ AND (status = Blocked OR "Flagged" = Impediment)

# Backlog health
sprint IS EMPTY AND "Story Points" IS EMPTY AND type IN (Story, Task)

# Release readiness
fixVersion = "v2.0" AND status NOT IN (Done, Closed)
```

---

*Last updated: December 2024*
