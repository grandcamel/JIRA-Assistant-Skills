# Daily Operations Best Practices

**Use this guide when:** Executing day-to-day lifecycle operations.

**Audience:** Developers, team leads, QA engineers, product managers.

**Not for:** Workflow design (see [WORKFLOW_DESIGN.md](WORKFLOW_DESIGN.md)).

---

## Table of Contents

1. [Assignment Best Practices](#assignment-best-practices)
2. [Version Management](#version-management)
3. [Component Organization](#component-organization)
4. [WIP Limits](#wip-limits)
5. [Resolution Discipline](#resolution-discipline)
6. [Common Pitfalls](#common-pitfalls)
7. [Quick Reference](#quick-reference)

---

## Assignment Best Practices

### Assignment Strategies

**1. Manual Assignment**
```bash
python assign_issue.py PROJ-123 --user john.doe@example.com
python assign_issue.py PROJ-123 --self
```

**2. Component-Based Auto-Assignment**
```bash
python create_component.py PROJ --name "Backend API" \
  --lead john@example.com --assignee-type COMPONENT_LEAD
```

### Assignment Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Unassigned in progress** | No ownership | Require assignee to start |
| **Assign to teams** | Diffusion of responsibility | Assign to individuals |
| **Manager always assignee** | Bottleneck | Delegate to team members |
| **Never reassigning** | People stuck | Enable reassignment |

### Handling Unassigned Issues

```bash
# Find unassigned work
python jql_search.py "assignee IS EMPTY AND status != Done"
```

**Triage strategies:**
1. Daily standup assignment
2. Component lead auto-assignment
3. Round-robin distribution
4. Self-service claiming

---

## Version Management

### Version Naming

**Semantic versioning (recommended):**
```
MAJOR.MINOR.PATCH
v1.0.0 - Initial release
v1.1.0 - Added feature
v1.1.1 - Bug fix
v2.0.0 - Breaking change
```

**Date-based:**
```
2025.01 - January 2025 release
2025.03.15 - March 15, 2025 release
```

### Version Lifecycle

```
Created -> Active -> Released -> Archived
```

**Commands:**
```bash
# Create version
python create_version.py PROJ --name "v2.0.0" \
  --start-date 2025-01-01 --release-date 2025-03-31

# Release version
python release_version.py PROJ --name "v2.0.0" --date 2025-03-31

# Archive old version
python archive_version.py PROJ --name "v1.0.0"
```

### Fix Version vs Affects Version

| Field | Purpose | When to Set |
|-------|---------|-------------|
| **Fix Version** | When fix will be released | At creation or prioritizing |
| **Affects Version** | Which version has the bug | When bug is found |

### Version Planning

```bash
# Create next 3 versions in advance
python create_version.py PROJ --name "v2.1.0" --release-date 2025-04-30
python create_version.py PROJ --name "v2.2.0" --release-date 2025-05-31
python create_version.py PROJ --name "v2.3.0" --release-date 2025-06-30

# Move incomplete issues (dry-run first)
python move_issues_version.py \
  --jql "fixVersion = v2.0.0 AND status != Done" \
  --target "v2.1.0" --dry-run
```

### Release Cadence

| Pattern | Frequency | Best For |
|---------|-----------|----------|
| **Continuous** | As ready | SaaS, web apps |
| **Sprint-based** | Every 2 weeks | Agile teams |
| **Monthly** | 1st of month | Regular cadence |
| **Quarterly** | Every 3 months | Enterprise |

---

## Component Organization

### Component Strategy

| Strategy | Example | Best For |
|----------|---------|----------|
| **Technical areas** | API, Frontend, Database | Engineering teams |
| **Product features** | Auth, Payments, Reports | Product management |
| **Teams** | Platform, Mobile, DevOps | Multi-team projects |

### Component Configuration

```bash
# Create with auto-assignment
python create_component.py PROJ --name "Backend API" \
  --lead john@example.com --assignee-type COMPONENT_LEAD

# List components
python get_components.py PROJ --format table
```

### Component Best Practices

1. **Limit to 5-15 components** - Too many causes confusion
2. **Assign component leads** - Clear ownership and triage
3. **1-2 components per issue** - Clearer accountability
4. **Archive unused components** - Keep list manageable

### Component vs Label

| Use Component | Use Label |
|---------------|-----------|
| Represents architectural area | Cross-cutting concern |
| Has clear owner | No specific owner |
| Long-lived subsystem | Temporary categorization |
| Example: "Backend API" | Example: "tech-debt" |

---

## WIP Limits

### What Are WIP Limits?

Restrict the number of issues in a status at one time.

```
To Do -> In Progress (WIP: 3) -> In Review (WIP: 2) -> Done
```

**Benefits:**
- Reduces context switching
- Encourages finishing before starting new
- Surfaces bottlenecks
- Forces prioritization

### Recommended Limits

**Per-status:**

| Status | WIP Limit | Reasoning |
|--------|-----------|-----------|
| To Do | No limit | Backlog can be large |
| In Progress | 1-2 per person | Focus on completion |
| In Review | 1.5x team size | Reviews are quick |
| Blocked | Monitor closely | Shouldn't accumulate |

**Per-person:**

| Role | WIP Limit |
|------|-----------|
| Developer | 1-2 items |
| QA Engineer | 2-3 items |
| Tech Lead | 3-5 items |

### When WIP Limit Reached

1. **Finish existing work first**
2. **Swarm on blocked items**
3. **Help with reviews**
4. **Identify bottlenecks**

---

## Resolution Discipline

### Common Resolutions

| Resolution | When to Use |
|------------|-------------|
| **Fixed** | Bug fixed, feature implemented |
| **Won't Fix** | Decided not to address |
| **Duplicate** | Same as another issue |
| **Cannot Reproduce** | Unable to replicate |
| **Done** | Work completed as requested |

### Setting Resolution

```bash
# Resolve with comment
python resolve_issue.py PROJ-123 --resolution "Fixed" \
  --comment "Corrected validation logic in user registration"

# Resolve as duplicate
python resolve_issue.py PROJ-456 --resolution "Duplicate" \
  --comment "Duplicate of PROJ-123"
```

### Resolution Best Practices

1. **Always set resolution** when closing
2. **Add resolution comment** explaining outcome
3. **Link duplicates** to original issue
4. **Be specific** with "Won't Fix" reasons

### Reopening Issues

```bash
python reopen_issue.py PROJ-123 \
  --comment "Regression found in v2.1.1"
```

Resolution is cleared on reopen - set again when re-closing.

---

## Common Pitfalls

### Red Flags to Watch

**In sprint/active work:**
- Issue "In Progress" for 7+ days
- 5+ issues assigned to one person
- Issue transitioning backward repeatedly
- Required fields missing on "Done" issues

**In backlog:**
- Issues older than 6 months without grooming
- Hundreds of unassigned issues
- No components or versions set

**In versions:**
- 20+ unreleased versions
- Release dates in the past
- Versions with only 1-2 issues

**In components:**
- Components with 0 issues
- All issues in "Other" component
- No component leads assigned

---

## Quick Reference

### Essential Commands

```bash
# Transitions
python get_transitions.py PROJ-123
python transition_issue.py PROJ-123 --name "In Progress"
python resolve_issue.py PROJ-123 --resolution "Fixed"
python reopen_issue.py PROJ-123

# Assignments
python assign_issue.py PROJ-123 --user john@example.com
python assign_issue.py PROJ-123 --self
python assign_issue.py PROJ-123 --unassign

# Versions
python create_version.py PROJ --name "v2.0.0" --release-date 2025-03-31
python get_versions.py PROJ --format table
python release_version.py PROJ --name "v2.0.0" --date 2025-03-31
python archive_version.py PROJ --name "v1.0.0"

# Components
python create_component.py PROJ --name "API" --lead john@example.com
python get_components.py PROJ --format table
```

### Workflow Checklist

**Before starting work:**
- [ ] Issue has clear acceptance criteria
- [ ] Estimate is set
- [ ] Issue is assigned
- [ ] Component is set
- [ ] Fix version is set

**Before marking done:**
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Resolution is set
- [ ] Resolution comment added

### Health Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| In Progress per person | 1-2 | 3-4 | 5+ |
| Time in "In Progress" | 1-3 days | 4-7 days | 8+ days |
| Unreleased versions | 2-4 | 5-10 | 10+ |
| Issues without components | <5% | 5-20% | 20%+ |

---

## Sources

- [Unito: The Ultimate Guide to Efficiency: Jira Best Practices in 2025](https://unito.io/blog/jira-efficiency-best-practices/)
- [Atlassian: Learn versions with Jira Tutorial](https://www.atlassian.com/agile/tutorials/versions)
- [Atlassian Community: Jira Essentials: Adding work in progress limits](https://community.atlassian.com/t5/Jira-articles/Jira-Essentials-Adding-work-in-progress-limits/ba-p/1621358)

---

*For workflow design, see [WORKFLOW_DESIGN.md](WORKFLOW_DESIGN.md).*
