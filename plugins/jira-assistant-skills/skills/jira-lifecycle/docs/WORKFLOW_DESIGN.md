# Workflow Design Best Practices

**Use this guide when:** Designing or improving your team's JIRA workflow.

**Audience:** JIRA admins, workflow designers, team leads.

**Not for:** Day-to-day lifecycle operations (see [DAILY_OPERATIONS.md](DAILY_OPERATIONS.md)).

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Status Naming Conventions](#status-naming-conventions)
3. [Transition Strategy](#transition-strategy)
4. [Conditions and Validators](#conditions-and-validators)
5. [Post-Functions](#post-functions)
6. [Workflow Patterns](#workflow-patterns)
7. [Testing and Rollout](#testing-and-rollout)

---

## Design Principles

### Keep It Simple

**Start simple, add complexity only when needed:**
- Begin with 3-5 statuses
- Add more only when there's a clear business need
- Avoid "status sprawl" (10+ statuses)
- Each status should represent a distinct phase

**Recommended progression:**
```
Phase 1: To Do -> In Progress -> Done
Phase 2: Backlog -> To Do -> In Progress -> Done
Phase 3: Backlog -> To Do -> In Progress -> Review -> Done
```

### Think in Phases, Not Micro-Steps

**Break processes into phases that represent key decision points:**

| Bad (Micro-steps) | Good (Phases) |
|-------------------|---------------|
| Code written -> Code reviewed -> Tests written -> Tests passing -> Merged -> Deployed | In Progress -> In Review -> Done |
| Draft -> Manager review -> Legal review -> Executive review -> Published | In Progress -> In Review -> Approved |

**Why phases work better:**
- Represent collections of smaller steps
- Issues can't move to next phase until current phase requirements are met
- Simpler to understand and use
- Less maintenance overhead

### Standardize Across Teams

**Benefits:**
- Easier collaboration between teams
- Simpler onboarding for new team members
- Consistent reporting across projects
- Reusable workflow configurations

**How to standardize:**
1. Define organization-wide status names
2. Create shared workflow templates
3. Document standard transitions
4. Regular workflow audits

**Standard status examples:**
- **Backlog** - Prioritized work queue
- **To Do** - Ready to start
- **In Progress** - Active work
- **In Review** - Peer/code review
- **In QA** - Quality assurance testing
- **Done** - Completed work

---

## Status Naming Conventions

### Use States, Not Actions

Statuses describe what state an issue is in, not what action to take.

| Bad (Action) | Good (State) | Why Better |
|--------------|--------------|------------|
| Review | In Review | Describes current state |
| Test | In Testing | Shows work is happening |
| Deploy | Ready for Deploy | Clear next step |
| Approve | Awaiting Approval | Indicates waiting state |

### Use Gerunds for Active Statuses

For "In Progress" category statuses, use -ing verbs:

| Instead of | Use |
|------------|-----|
| Develop | Developing |
| Code | Coding |
| Test | Testing |
| Review | Reviewing |

### Naming Guidelines

1. **Keep names short and concise:**
   - Good: "In Review", "QA", "Done"
   - Bad: "Waiting for Product Manager Approval and Documentation Review"

2. **Use generic, reusable names:**
   - Good: "In Review" (works for code, design, content)
   - Bad: "In Contract Legal Review" (too specific)

3. **Make names self-explanatory:**
   - Good: "Awaiting Deployment", "Blocked"
   - Bad: "Stage 3", "Phase Alpha"

4. **Avoid similar or overlapping names:**
   - Bad: "In Progress", "Working", "Active" (all mean the same)
   - Good: "In Progress", "In Review", "In Testing" (distinct phases)

### Status Categories

Every status belongs to one of three categories:

| Category | Color | Purpose | Example Statuses |
|----------|-------|---------|------------------|
| **To Do** | Blue | Work not started | Backlog, To Do, Open, New |
| **In Progress** | Yellow | Active work | In Progress, In Review, In QA |
| **Done** | Green | Completed work | Done, Closed, Resolved |

**Why categories matter:**
- Boards filter by category
- Reports aggregate by category
- Third-party tools rely on categories

---

## Transition Strategy

### Transition Types

**Linear transitions:**
```
To Do -> In Progress -> Done
```
- Simple, one-way flow
- Best for straightforward processes

**Circular transitions:**
```
To Do <-> In Progress <-> In Review -> Done
```
- Allow moving backward
- Handle rework scenarios

**Hub transitions:**
```
       +-> In Review --+
To Do -> In Progress -> Done
       +-> Blocked ----+
```
- Multiple paths from one status
- Handles different scenarios

### Transition Naming

**Good transition names are action-oriented:**

| From Status | To Status | Good Name | Bad Name |
|-------------|-----------|-----------|----------|
| To Do | In Progress | Start Progress | Move Forward |
| In Progress | In Review | Submit for Review | Next Step |
| In Review | In Progress | Request Changes | Go Back |
| In Progress | Done | Complete | Finish |

### Required Fields on Transitions

| Transition | Required Fields | Reasoning |
|------------|-----------------|-----------|
| Start Progress | Assignee | Someone must own the work |
| Submit for Review | Pull Request Link | Ensures code is ready |
| Mark as Done | Resolution | Documents how issue was resolved |

**Best practices:**
1. Only require truly necessary fields
2. Provide clear error messages
3. Set sensible defaults where possible
4. Document requirements for users

---

## Conditions and Validators

### Transition Conditions

**When to use conditions:**
- Restrict who can execute transitions
- Enforce process compliance
- Prevent accidental status changes

**Common condition patterns:**

| Condition Type | Example | Use Case |
|----------------|---------|----------|
| **User-based** | Only assignee can resolve | Ensures owner signs off |
| **Role-based** | Only developers can start | Matches team roles |
| **Field-based** | Must have story points | Ensures estimation |
| **Subtask-based** | All subtasks must be done | Enforces completeness |

### Validators

**Common validators:**
1. **Field validator** - Checks field has value
2. **User validator** - Verifies user in correct group
3. **Permission validator** - Ensures user has permission
4. **Date validator** - Confirms date is valid
5. **Regex validator** - Validates field format

**Example validator setup:**
```
Transition: "Deploy to Production"
Validators:
- Environment field = "Production"
- User in "Release Managers" group
- All subtasks resolved
- Fix Version is set
```

---

## Post-Functions

**Useful post-functions:**

| Post-Function | When to Use | Example |
|---------------|-------------|---------|
| **Update field** | Auto-set values | Set resolution date when resolved |
| **Assign issue** | Route to next person | Assign to QA when dev complete |
| **Create issue** | Trigger follow-up | Create deployment ticket |
| **Fire event** | Send notifications | Email stakeholders on release |
| **Add comment** | Document change | Add "Automatically closed" comment |

---

## Workflow Patterns

### Simple Workflow (3 statuses)

```
To Do -> In Progress -> Done
```

Best for: Personal tracking, simple projects, getting started.

### Development Workflow (6 statuses)

```
Backlog -> To Do -> In Progress -> In Review -> In QA -> Done
```

Best for: Engineering teams with code review and testing.

### Service Desk Workflow

```
Waiting for Support -> In Progress -> Waiting for Customer -> Resolved -> Closed
```

Best for: Customer support, help desks, service requests.

### Incident Workflow

```
Open -> Investigating -> In Progress -> Monitoring -> Resolved -> Closed
```

Best for: SRE, DevOps, incident management.

See [references/patterns/](../references/patterns/) for detailed pattern documentation.

---

## Testing and Rollout

### Testing Checklist

- [ ] Test all transitions with test issues
- [ ] Verify required fields behave correctly
- [ ] Check permissions and conditions
- [ ] Validate with stakeholders
- [ ] Pilot with small team before rollout
- [ ] Document the workflow for users

### Rollout Strategy

1. **Create test project** with the new workflow
2. **Pilot with 2-3 team members** for 1 sprint
3. **Gather feedback** and adjust
4. **Document** all transitions and conditions
5. **Train team** on new workflow
6. **Roll out** to full team
7. **Monitor** and iterate

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Status sprawl** | 15+ statuses, team confused | Consolidate to 5-7 |
| **One-way workflows** | Can't handle rework | Allow backward transitions |
| **Skip-friendly** | Too many optional paths | Enforce key steps |
| **Duplicate statuses** | "In Review" and "Reviewing" | Standardize naming |
| **Permission chaos** | Different rules per project | Centralize management |

---

## Sources

- [Idalko: A Guide to Jira Workflow Best Practices](https://idalko.com/blog/jira-workflow-best-practices)
- [HeroCoders: Understanding Jira Issue Statuses](https://www.herocoders.com/blog/understanding-jira-issue-statuses)

---

*For day-to-day operations, see [DAILY_OPERATIONS.md](DAILY_OPERATIONS.md).*
