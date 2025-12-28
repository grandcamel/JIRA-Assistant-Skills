# JIRA Issue Management Best Practices

Comprehensive guide to creating, managing, and maintaining high-quality JIRA issues for effective project tracking and team collaboration.

## When to Use This Guide

Use this guide when:
- Creating new JIRA issues (design before creating)
- Maintaining issue quality (improving existing issues)
- Training team members on issue standards
- Auditing project issue quality
- Troubleshooting issues with descriptions, priorities, or assignments

This guide focuses on **issue content and metadata quality**. For operational commands, see [SKILL.md](../SKILL.md). For quick decision lookups, see [Decision Matrices](DECISION_MATRICES.md).

---

## Table of Contents

1. [Writing Effective Summaries](#writing-effective-summaries)
2. [Writing Effective Descriptions](#writing-effective-descriptions)
3. [Choosing Issue Types](#choosing-issue-types)
4. [Setting Priorities](#setting-priorities)
5. [Using Labels and Components](#using-labels-and-components)
6. [Custom Fields](#custom-fields)
7. [Issue Lifecycle](#issue-lifecycle)
8. [Common Pitfalls](#common-pitfalls)
9. [Quick Reference](#quick-reference)

---

## Writing Effective Summaries

The summary is your headline - crisp, clear, and captures the issue's essence at a glance.

### Core Principles

**Do:**
- Start with an action verb: Add, Fix, Update, Remove, Implement, Optimize
- Be specific: "Fix login timeout on mobile Safari" not "Login broken"
- Keep under 80 characters
- Make it scannable without opening the issue

**Don't:**
- Use vague terms: "Various fixes", "Updates", "Work"
- Include implementation details in summary
- Duplicate information from labels or components

### Summary Patterns by Type

| Type | Pattern | Example |
|------|---------|---------|
| Bug | Fix [problem] in [location] | "Fix 404 error when accessing profile" |
| Task | [Verb] [object] for [purpose] | "Configure CI pipeline for testing" |
| Story | [User] can [action] [object] | "Users can filter results by date" |
| Epic | [High-level capability] | "User Authentication System" |

---

## Writing Effective Descriptions

The description provides detailed context, requirements, and acceptance criteria.

### Essential Structure

Every description should have at minimum:
1. **Problem/Goal** - What needs to change
2. **Context** - Why it matters
3. **Acceptance Criteria** - How we know it's done

### Templates

For detailed templates with examples, see:
- [Standard Template](templates/description-standard.md) - General issues
- [Bug Report Template](templates/description-bug.md) - Defects and regressions
- [User Story Template](templates/description-story.md) - User-facing features
- [Task Template](templates/description-task.md) - Technical work

### Description Guidelines

**Be Clear and Concise:**
- Use simple, straightforward language
- Break complex information into sections
- Use bullet points and numbered lists

**Provide Context:**
- Explain the "why" behind the work
- Include business impact and user value
- Link to related issues and documentation

**Be Specific:**
- Include exact error messages in code blocks
- Specify versions, environments, configurations
- Attach screenshots, logs, or recordings

---

## Choosing Issue Types

Different issue types serve different purposes. See [Decision Matrices](DECISION_MATRICES.md#issue-type-decision-matrix) for the complete comparison table.

### Quick Guide

| Type | One-liner |
|------|-----------|
| **Epic** | Multi-sprint initiative with child stories |
| **Story** | User-facing value, fits in one sprint |
| **Task** | Technical work, no direct user visibility |
| **Bug** | Something that worked is now broken |
| **Subtask** | Breakdown of parent into 2-8 hour pieces |

### Story vs Task

**Use Story** when the user can see or experience the result.
**Use Task** when work is internal or technical.

Example: "Add login button" = Story. "Configure OAuth" = Task.

---

## Setting Priorities

Priority indicates the order in which issues should be addressed. See [Decision Matrices](DECISION_MATRICES.md#priority-definitions) for detailed definitions.

### Priority Quick Reference

| Priority | When to Use |
|----------|-------------|
| Highest | Production down, data loss, security breach |
| High | Core feature broken, release blocker |
| Medium | Normal scheduled work, planned features |
| Low | Nice to have, minor improvements |
| Lowest | Future wishlist items |

### Priority Formula

**Priority = Impact x Urgency** (not just severity)

A cosmetic bug (low severity) affecting a major client demo (high urgency) = High priority.

---

## Using Labels and Components

### Labels

Labels are flexible tags for cross-cutting categorization.

**Good label categories:**
- Domain: `security`, `performance`, `accessibility`
- Status qualifiers: `needs-refinement`, `blocked-external`
- Team: `team-platform`, `needs-design-review`
- Business: `customer-request`, `quick-win`

**Naming convention:** lowercase with hyphens: `tech-debt`, `needs-review`

**Limit:** 3-5 labels per issue

### Components

Components represent structural areas of the project.

**Use for:**
- Architectural modules: `api`, `frontend`, `backend`
- Product areas: `auth`, `payments`, `notifications`
- Team ownership with auto-assignment

**Keep stable:** Don't rename frequently. Limit to 5-15 per project.

### Labels vs Components

| Labels | Components |
|--------|------------|
| Cross-cutting concerns | Structural divisions |
| Flexible, change often | Stable, rename rarely |
| Multiple per issue | 1-2 per issue |
| No team ownership | Can have component leads |

See [Decision Matrices](DECISION_MATRICES.md#labels-vs-components-vs-custom-fields) for detailed comparison.

---

## Custom Fields

Custom fields extend JIRA's data model. Use judiciously.

### Before Creating a Custom Field

Ask:
1. Can I use Summary, Description, Labels, or Components instead?
2. Will I query or report on this data?
3. Is this truly unique to my process?
4. Will it be used long-term?

### Alternatives to Custom Fields

| Need | Alternative |
|------|-------------|
| Categorization | Components or Labels |
| Team assignment | Components with leads |
| Status qualifier | Labels like `waiting-customer` |
| Free-form notes | Comments or Description |
| Due tracking | Due Date field |
| Approval status | Workflow states |

### If You Must Create Custom Fields

- Use generic, reusable names: `Customer Impact` not `Marketing Impact`
- Include units: `Effort (hours)` not `Effort`
- Use project-specific contexts when possible
- Document purpose and valid values
- Audit quarterly and remove unused fields

---

## Issue Lifecycle

### Creation Checklist

- [ ] Searched for duplicates
- [ ] Clear summary (< 80 chars, starts with verb)
- [ ] Complete description (problem, context, acceptance criteria)
- [ ] Correct issue type
- [ ] Appropriate priority
- [ ] Relevant labels and components
- [ ] Linked to related issues

### Maintenance Best Practices

**Weekly grooming:**
- Review unassigned issues
- Update stale priorities
- Link related issues
- Archive outdated issues

**When updating:**
- Add comments explaining changes
- Update description to reflect current understanding
- Notify affected team members

**When NOT to update:**
- Don't change issue type after creation
- Don't remove historical comments
- Don't overwrite original requirements without tracking

### Deletion Guidelines

**Delete only when:**
- True duplicate (link to original first)
- Created in error
- Spam or test data

**Don't delete:**
- Resolved issues (they provide history)
- Issues with logged time
- Issues linked to commits/PRs

---

## Common Pitfalls

See [Decision Matrices](DECISION_MATRICES.md#common-anti-patterns) for the complete list.

### Top Issues to Avoid

1. **Mega-issues** - Multiple unrelated things in one issue
   - Solution: Split into separate, focused issues

2. **Vague summaries** - "Fix bug" or "Update code"
   - Solution: Be specific with action verb and context

3. **Missing acceptance criteria** - Team doesn't know when done
   - Solution: Add clear, testable criteria

4. **Priority inflation** - Everything is Highest
   - Solution: Reserve Highest for true emergencies

5. **Zombie issues** - Open 6+ months with no activity
   - Solution: Regular grooming, close or archive stale issues

---

## Quick Reference

### Summary Patterns

```
Bugs:       "Fix [problem] in [location]"
Tasks:      "[Verb] [object] for [purpose]"
Stories:    "Users can [action] [object]"
Epics:      "[High-level capability]"
```

### Priority Quick Decision

```
Highest  → System down, data loss, security breach
High     → Core feature broken, release blocker
Medium   → Standard work, planned features
Low      → Minor issues, small improvements
Lowest   → Future wishlist items
```

### Issue Creation Command

```bash
python create_issue.py --project PROJ --type Bug \
  --summary "Fix login timeout" --priority High
```

### Quality Targets

| Metric | Target |
|--------|--------|
| Issues with acceptance criteria | 90%+ |
| Issues with priority set | 100% |
| Description length | > 100 chars |
| Labels per issue | 1-5 |

---

## Related Resources

### Internal
- [SKILL.md](../SKILL.md) - Operational commands
- [Decision Matrices](DECISION_MATRICES.md) - Quick lookup tables
- [Description Templates](templates/) - Detailed templates
- [Field Formats](../references/field_formats.md) - API field formats

### External
- [JIRA REST API v3](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [JIRA Best Practices](https://www.atlassian.com/software/jira/guides/getting-started/best-practices)

---

*Last updated: December 2025*
