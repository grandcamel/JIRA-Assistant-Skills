# JIRA Decision Matrices

Quick reference tables for common JIRA issue management decisions.

---

## Issue Type Decision Matrix

| Type | Use When | Typical Duration | Estimated? | Parent Type | Example |
|------|----------|-----------------|-----------|-------------|---------|
| **Epic** | Feature spans multiple sprints, needs breakdown | 2-6 sprints | No | None | "User Authentication System" |
| **Story** | User-facing value, fits in one sprint | 1-5 days | Yes (points) | Epic | "Users can reset password via email" |
| **Task** | Technical work, enabler, no direct user value | 0.5-3 days | Yes (points) | Epic/None | "Configure Redis cache for sessions" |
| **Bug** | Something worked before, now broken | 0.5-2 days | Optional | Epic/None | "Login fails with special characters" |
| **Subtask** | Breaking down a story/task into smaller pieces | 2-8 hours | Optional (hours) | Story/Task/Bug | "Write unit tests for password validation" |
| **Improvement** | Enhance existing feature, not broken | 1-3 days | Yes (points) | Epic/None | "Add keyboard shortcuts to editor" |
| **Spike** | Research or investigation, outcome unknown | 0.5-2 days | Yes (time-boxed) | Epic/None | "Evaluate authentication libraries" |

---

## Story vs Task Decision

| Scenario | Type | Rationale |
|----------|------|-----------|
| Add login button to homepage | Story | User-facing feature |
| Setup OAuth server configuration | Task | Technical enabler |
| Display user profile picture | Story | User can see the result |
| Optimize database query performance | Task | Internal improvement |
| Enable users to export CSV | Story | User-facing capability |
| Migrate database to PostgreSQL | Task | Technical work, no visible change |

**Quick Rule:** If user can see/experience the change, it's a Story. If it's internal/technical, it's a Task.

---

## Bug Severity Matrix

| Severity | Definition | Response Time | Example |
|----------|-----------|---------------|---------|
| **Critical** | Complete system failure, data loss, security breach | Immediate | "Database corruption on save" |
| **High** | Core feature broken, large user impact, no workaround | Same day | "Cannot complete checkout" |
| **Medium** | Feature broken, moderate impact, workaround exists | 1-3 days | "Filter doesn't work on mobile" |
| **Low** | Minor issue, cosmetic problem, minimal impact | Next sprint | "Button alignment off by 2px" |

---

## Priority Definitions

| Priority | When to Use | Response Expectation | Example Scenarios |
|----------|-------------|---------------------|-------------------|
| **Highest** | Emergency, complete blocker, severe impact | Drop everything, fix immediately | Production down, data loss, security breach |
| **High** | Critical for release, major feature broken | Address within 24 hours | Key feature not working, release blocker |
| **Medium** | Normal priority, scheduled work | Complete in current sprint | Planned features, standard bugs |
| **Low** | Nice to have, minor issue | Backlog, future sprint | Small improvements, cosmetic issues |
| **Lowest** | Future consideration, wishlist | Someday/maybe | Feature requests, minor enhancements |

---

## Priority Decision Framework

Ask these questions in order:

1. **Impact:** How many users are affected?
   - All users → Higher priority
   - Subset of users → Medium priority
   - Edge case → Lower priority

2. **Severity:** What's the consequence?
   - Blocks critical work → Highest
   - Degrades experience → High/Medium
   - Minor inconvenience → Low/Lowest

3. **Urgency:** What's the timeline?
   - Must fix now → Highest
   - Needed for release → High
   - Can wait → Medium/Low

4. **Workaround:** Is there an alternative?
   - No workaround → Higher priority
   - Difficult workaround → Medium priority
   - Easy workaround → Lower priority

---

## Priority vs Severity (Bugs)

| Severity | Priority | Example |
|----------|----------|---------|
| High | Highest | Login broken in production |
| High | Low | Misspelling on rarely-visited page |
| Low | Highest | UI bug affects demo to major client |
| Low | Low | Cosmetic issue on deprecated feature |

**Formula:** Priority = Impact x Urgency (not just severity)

---

## Labels vs Components vs Custom Fields

| Use For | Labels | Components | Custom Fields |
|---------|--------|------------|---------------|
| **Purpose** | Cross-cutting, flexible tags | Structural areas, ownership | Unique queryable data |
| **Examples** | security, tech-debt, quick-win | api, frontend, payment-service | Customer Impact Score |
| **Multiple per issue** | Yes (3-5 recommended) | Yes (1-2 recommended) | Depends on type |
| **Team ownership** | No | Yes (component leads) | No |
| **Reporting** | Basic filtering | Full metrics | Custom queries |
| **Stability** | Flexible, change often | Stable, rename rarely | Permanent |

---

## Field Selection Decision Tree

```
Is this information...

Identifying the issue?
└─ Use: Summary

Explaining details?
└─ Use: Description

Categorizing by area?
├─ Structural/architectural → Components
└─ Flexible/cross-cutting → Labels

Indicating importance?
└─ Use: Priority

Tracking people?
├─ Who does the work → Assignee
├─ Who reported it → Reporter (auto)
└─ Who cares about updates → Watchers

Organizing work?
├─ Epic-level grouping → Epic Link
├─ Sprint planning → Sprint
└─ Release planning → Fix Version

Time-related?
├─ When due → Due Date
├─ How much effort → Original Estimate
└─ Work logged → Time Tracking

Truly unique to your process?
└─ Consider: Custom Field (last resort)
```

---

## Epic Guidelines

### When to Create an Epic

| Create Epic When | Don't Create Epic When |
|------------------|------------------------|
| Feature requires 2+ sprints | Work fits in one sprint (use Story) |
| Work involves multiple teams | Too broad or vague (break into smaller epics) |
| Initiative has distinct phases | No related stories (just use a large Story) |
| Need to track progress across stories | |

### Epic Sizing Guide

| Size | Sprint Count | Recommendation |
|------|--------------|----------------|
| Too Small | < 2 sprints | Consider making it a Story |
| Optimal | 2-4 sprints | Good epic size |
| Acceptable | 5-6 sprints | Monitor for scope creep |
| Too Large | > 6 sprints | Split into multiple epics |

---

## Common Anti-Patterns

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Mega-issues** | Multiple unrelated things in one issue | Split into separate, focused issues |
| **Vague summaries** | "Fix bug" or "Update code" | Be specific: "Fix login timeout on Safari" |
| **Missing acceptance criteria** | Team doesn't know when done | Add clear, testable criteria |
| **Label chaos** | 50+ labels, inconsistent naming | Create label taxonomy, enforce standards |
| **Duplicate information** | Same info in summary, description, comments | Each field has a purpose |
| **Zombie issues** | Open 6+ months, no activity | Regular grooming, close or archive stale issues |
| **Priority inflation** | Everything is Highest | Reserve Highest for true emergencies |

---

## Label Anti-Patterns

| Anti-Pattern | Why It's Bad | Alternative |
|--------------|--------------|-------------|
| Status labels: `in-progress` | Duplicates workflow status | Use workflow states |
| Issue type labels: `bug-label` | Duplicates issue type field | Use issue type |
| Assignment labels: `assigned-to-john` | Duplicates assignee field | Use assignee field |
| Component labels: `backend-label` | Duplicates components | Use components field |
| Priority labels: `high-priority` | Duplicates priority field | Use priority field |
| One-off labels: `discussed-tuesday` | No reusability | Use comments instead |

---

## Quality Metrics Targets

| Metric | Target | Indicates |
|--------|--------|-----------|
| Issues with acceptance criteria | 90%+ | Clarity of requirements |
| Average time to first comment | < 24 hours | Team engagement |
| Issues closed as duplicate | < 5% | Search before create |
| Issues with priority set | 100% | Proper prioritization |
| Description length | > 100 chars | Adequate detail |
| Labels per issue | 1-5 | Appropriate categorization |
| Linked issues | 30%+ | Relationship tracking |

---

## Summary Pattern Cheat Sheet

| Issue Type | Pattern | Examples |
|------------|---------|----------|
| **Bugs** | Fix [problem] in [location] | "Fix 404 error when accessing profile" |
| **Tasks** | [Verb] [object] for [purpose] | "Configure CI pipeline for testing" |
| **Stories** | Users can [action] [object] | "Users can filter results by date" |
| **Epics** | [High-level capability] | "User Authentication System" |

---

*Last updated: December 2025*
