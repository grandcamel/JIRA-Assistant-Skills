# Individual Contributor Time Logging Guide

Practical guidance for developers, QA engineers, and individual contributors on daily time logging habits, comment templates, and handling special situations.

---

## Use this guide if you...

- Are a developer, QA engineer, or contractor logging your own time
- Need templates for effective worklog comments
- Want to establish daily time logging habits
- Need to handle retroactive entries or interrupted work

For estimation guidance, see [Estimation Guide](estimation-guide.md).
For team policies and compliance, see [Team Policies](team-policies.md).

---

## Table of Contents

1. [When to Log Time](#when-to-log-time)
2. [Writing Effective Comments](#writing-effective-comments)
3. [Special Cases](#special-cases)
4. [Worklog Visibility](#worklog-visibility)
5. [Daily Workflow Checklist](#daily-workflow-checklist)

---

## When to Log Time

### Daily Logging (Strongly Recommended)

**Why daily:**
- Highest accuracy (details fresh in memory)
- Prevents forgotten activities
- Enables real-time reporting
- Reduces end-of-week rush

**Daily routine:**
```bash
# End-of-day workflow (5 minutes)
# 1. Review what you worked on today
# 2. Log time to each issue

python add_worklog.py PROJ-123 --time 3h --comment "Implemented authentication API"
python add_worklog.py PROJ-124 --time 2h --comment "Code review for payment feature"
python add_worklog.py PROJ-125 --time 1h 30m --comment "Sprint planning meeting"
```

### Task Completion Logging (Acceptable)

Log time immediately when finishing each task:
```bash
# Right after completing a task
python add_worklog.py PROJ-123 --time 2h 15m --comment "Fixed login timeout bug"
```

**Benefits:**
- Still accurate (task context fresh)
- Natural workflow integration
- Clear task boundaries

### Weekly Logging (Not Recommended)

**Problems with weekly logging:**
- 40-60% higher inaccuracy rate
- Forgotten activities (meetings, interruptions)
- Difficulty reconstructing task details
- Poor data for reporting and billing

**If forced to use weekly:** Keep detailed daily notes to reference when logging.

---

## Writing Effective Comments

### Good Worklog Comment Patterns

**Descriptive and specific:**

| Comment | Quality | Reason |
|---------|---------|--------|
| "Code review for PR #234 - authentication module" | Excellent | Specific, traceable, informative |
| "Debugging production timeout issue in payment API" | Excellent | Clear problem, context provided |
| "Sprint planning - prioritized backlog items" | Good | Activity and outcome clear |
| "Research OAuth 2.0 libraries for integration" | Good | Task and purpose clear |
| "Pair programming with Sarah on data migration" | Good | Activity and collaboration noted |

**Poor worklog comments to avoid:**

| Comment | Quality | Problem |
|---------|---------|---------|
| "Work" | Bad | No information |
| "" (empty) | Bad | Completely useless |
| "Stuff" | Bad | Vague, no context |
| "Meeting" | Poor | Which meeting? What outcome? |
| "Coding" | Poor | Expected - what specifically? |

### Comment Templates

**Development work:**
```
Implemented [feature/component]: [brief description]
Fixed [issue/bug]: [root cause]
Refactored [component] to [improvement]
Added [tests/documentation] for [feature]
```

**Collaboration:**
```
Code review for PR #[number] - [component]
Pair programming with [person] on [task]
Knowledge sharing session: [topic]
Design discussion: [feature/decision]
```

**Meetings:**
```
Sprint planning - [key outcomes]
Daily standup - [blockers discussed]
Retrospective - [action items]
Client meeting - [requirements clarified]
```

**Research/Learning:**
```
Research [technology/approach] for [use case]
Spike: Investigating [options] for [problem]
Learning [skill/tool] for [upcoming task]
```

---

## Special Cases

### Non-Issue Time

**Problem:** Meetings, email, admin work don't map to specific issues.

**Solutions:**

**Option 1: Create "overhead" issues**
```bash
# Create issues for recurring activities
PROJ-999: "Team Meetings"
PROJ-998: "Email & Communication"
PROJ-997: "Administrative Tasks"

python add_worklog.py PROJ-999 --time 1h --comment "Daily standup"
python add_worklog.py PROJ-998 --time 30m --comment "Customer support emails"
```

**Option 2: Distribute proportionally to project issues**
```bash
# If you spent 6h on PROJ-123 and 1h in meetings about it
python add_worklog.py PROJ-123 --time 6h --comment "Feature implementation"
python add_worklog.py PROJ-123 --time 1h --comment "Planning meeting for this feature"
```

### Retroactive Time Logging

Log time for past dates using `--started`:

```bash
# Log yesterday's work
python add_worklog.py PROJ-123 --time 4h \
  --started yesterday \
  --comment "Work from previous day (was out sick)"

# Log specific date
python add_worklog.py PROJ-123 --time 3h \
  --started "2025-01-20" \
  --comment "Retroactive entry for Monday"
```

**Best practices:**
- Add note explaining retroactive entry
- Don't go back more than 1 week
- Ensure date falls within reporting period

### Interrupted Work

When logging interrupted or partial work:

```bash
# Log work even if task incomplete
python add_worklog.py PROJ-123 --time 2h \
  --comment "Partial work on authentication - interrupted by production issue" \
  --adjust-estimate leave  # Don't reduce remaining estimate

# Log interruption work
python add_worklog.py PROD-456 --time 1h \
  --comment "Emergency production fix - database connection pool exhausted"
```

### Logging Time with Pomodoro Technique

```bash
# Work in 25-minute intervals
# Log after each pomodoro or batch of pomodoros

# After 3 pomodoros (1h 15m)
python add_worklog.py PROJ-123 --time 1h 15m \
  --comment "Implemented authentication logic (3 pomodoros)"
```

---

## Worklog Visibility

Control who can see sensitive time entries:

```bash
# Restrict to project role
python add_worklog.py PROJ-123 --time 2h \
  --comment "Security vulnerability fix" \
  --visibility-type role --visibility-value Administrators

# Restrict to user group
python add_worklog.py PROJ-124 --time 3h \
  --comment "Confidential client feature" \
  --visibility-type group --visibility-value senior-developers
```

**Use cases:**
- Security work (limit to security team)
- Client-confidential projects
- Executive/strategic planning time
- Sensitive HR or legal matters

---

## Daily Workflow Checklist

### Morning
- [ ] Review sprint board for today's work
- [ ] Check estimates on assigned issues
- [ ] Start timer/tracking for first task

### During Day
- [ ] Log time when switching tasks
- [ ] Add descriptive comments to worklogs
- [ ] Update remaining estimates if needed

### End of Day
- [ ] Log all work completed today
- [ ] Verify total time approximately equals work hours
- [ ] Update issue status if tasks completed

### Weekly
- [ ] Review time logged vs sprint commitment
- [ ] Identify missing estimates
- [ ] Generate time report for review

---

## Related Guides

- [Estimation Guide](estimation-guide.md) - Setting realistic estimates and buffers
- [Team Policies](team-policies.md) - Organizational time tracking requirements
- [Quick Reference: Time Format](reference/time-format-quick-ref.md) - Time format syntax
- [Quick Reference: Error Codes](reference/error-codes.md) - Troubleshooting script errors

---

**Back to:** [SKILL.md](../SKILL.md) | [Best Practices Index](BEST_PRACTICES.md)
