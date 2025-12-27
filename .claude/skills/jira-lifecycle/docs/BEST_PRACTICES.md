# JIRA Lifecycle Management Best Practices

Comprehensive guide to workflow design, transitions, assignments, version management, and component organization for effective JIRA lifecycle management.

---

## Table of Contents

1. [Workflow Design Principles](#workflow-design-principles)
2. [Status Naming Conventions](#status-naming-conventions)
3. [Transition Strategy](#transition-strategy)
4. [Assignment Best Practices](#assignment-best-practices)
5. [Version Management](#version-management)
6. [Component Organization](#component-organization)
7. [Work In Progress (WIP) Limits](#work-in-progress-wip-limits)
8. [Resolution Discipline](#resolution-discipline)
9. [Workflow Patterns by Use Case](#workflow-patterns-by-use-case)
10. [Common Pitfalls](#common-pitfalls)
11. [Quick Reference Card](#quick-reference-card)

---

## Workflow Design Principles

### Keep It Simple

**Start simple, add complexity only when needed:**
- Begin with 3-5 statuses
- Add more only when there's a clear business need
- Avoid "status sprawl" (10+ statuses)
- Each status should represent a distinct phase

**Recommended approach:**
```
Phase 1: To Do → In Progress → Done
Phase 2: Backlog → To Do → In Progress → Done
Phase 3: Backlog → To Do → In Progress → Review → Done
```

### Think in Phases, Not Micro-Steps

**Break processes into phases that represent key decision points:**

| Bad (Micro-steps) | Good (Phases) |
|-------------------|---------------|
| Code written → Code reviewed → Tests written → Tests passing → Merged → Deployed | In Progress → In Review → Done |
| Draft → Manager review → Legal review → Executive review → Published | In Progress → In Review → Approved |

**Why phases work better:**
- Represent collections of smaller steps
- Issues can't move to next phase until current phase requirements are met
- Simpler to understand and use
- Less maintenance overhead

### Standardize Across Teams

**Benefits of standardization:**
- Easier collaboration between teams
- Simpler onboarding for new team members
- Consistent reporting across projects
- Reusable workflow configurations

**How to standardize:**
1. Define organization-wide status names
2. Create shared workflow templates
3. Document standard transitions
4. Regular workflow audits

**Example standard statuses:**
- **Backlog** - Prioritized work queue
- **To Do** - Ready to start
- **In Progress** - Active work
- **In Review** - Peer/code review
- **In QA** - Quality assurance testing
- **Done** - Completed work

### Test Before Publishing

**Workflow testing checklist:**
- [ ] Test all transitions with test issues
- [ ] Verify required fields behave correctly
- [ ] Check permissions and conditions
- [ ] Validate with stakeholders
- [ ] Pilot with small team before rollout
- [ ] Document the workflow for users

---

## Status Naming Conventions

### Use States, Not Actions

Statuses should describe what state an issue is in, not what action to take.

| Bad (Action) | Good (State) | Why Better |
|--------------|--------------|------------|
| Review | In Review | Describes current state |
| Test | In Testing | Shows work is happening |
| Deploy | Ready for Deploy | Clear next step |
| Approve | Awaiting Approval | Indicates waiting state |
| Fix | In Progress | Generic, reusable |

### Use Gerunds for Active Statuses

**For "In Progress" category statuses, use -ing verbs:**

| Instead of | Use |
|------------|-----|
| Develop | Developing |
| Code | Coding |
| Test | Testing |
| Deploy | Deploying |
| Review | Reviewing |

**Why this matters:**
- Clearly shows work is actively happening
- Distinguishes from completed states
- More intuitive for team members

### Naming Pattern Guidelines

**1. Keep names short and concise:**
- **Good:** "In Review", "QA", "Done"
- **Bad:** "Waiting for Product Manager Approval and Documentation Review"

**2. Use generic, reusable names:**
- **Good:** "In Review" (works for code, design, content)
- **Bad:** "In Contract Legal Review" (too specific)

**3. Make names self-explanatory:**
- **Good:** "Awaiting Deployment", "Blocked"
- **Bad:** "Stage 3", "Phase Alpha"

**4. Avoid similar or overlapping names:**
- **Bad:** "In Progress", "Working", "Active" (all mean the same)
- **Good:** "In Progress", "In Review", "In Testing" (distinct phases)

### Status Categories

Every status belongs to one of three categories:

| Category | Color | Purpose | Example Statuses |
|----------|-------|---------|------------------|
| **To Do** | Blue | Work not started | Backlog, To Do, Open, New |
| **In Progress** | Yellow | Active work | In Progress, In Review, In QA, Testing |
| **Done** | Green | Completed work | Done, Closed, Resolved, Released |

**Why categories matter:**
- Boards filter by category
- Reports aggregate by category
- Third-party tools rely on categories

### Common Status Naming Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Past tense names | "Reviewed", "Tested" | Use "In Review", "In Testing" |
| Ambiguous names | "Pending", "Ongoing" | Use "Awaiting Approval", "In Progress" |
| Too many variations | "To Do", "TODO", "ToDo" | Pick one and standardize |
| Acronyms without context | "UAT", "CAB" | Use "User Acceptance Testing", "Awaiting CAB Approval" |

---

## Transition Strategy

### Transition Types

**Linear transitions:**
```
To Do → In Progress → Done
```
- Simple, one-way flow
- Best for straightforward processes
- Minimal complexity

**Circular transitions:**
```
To Do ⇄ In Progress ⇄ In Review → Done
     ↑________________↓
```
- Allow moving backward
- Handle rework scenarios
- More realistic for complex work

**Hub transitions:**
```
   ┌──→ In Review ──┐
To Do → In Progress → Done
   └──→ Blocked ────┘
```
- Multiple paths from one status
- Handles different scenarios
- Requires careful planning

### Transition Naming

**Good transition names are action-oriented:**

| From Status | To Status | Good Name | Bad Name |
|-------------|-----------|-----------|----------|
| To Do | In Progress | Start Progress | Move Forward |
| In Progress | In Review | Submit for Review | Next Step |
| In Review | In Progress | Request Changes | Go Back |
| In Progress | Done | Complete | Finish |
| Done | In Progress | Reopen | Redo |

### Required Fields on Transitions

**Common fields required during transitions:**

| Transition | Required Fields | Reasoning |
|------------|-----------------|-----------|
| Start Progress | Assignee | Someone must own the work |
| Submit for Review | Pull Request Link | Ensures code is ready |
| Mark as Done | Resolution | Documents how issue was resolved |
| Deploy | Environment, Deployment Date | Track deployment details |

**Best practices for required fields:**
1. Only require truly necessary fields
2. Provide clear error messages
3. Set sensible defaults where possible
4. Document requirements for users

### Transition Conditions

**When to use conditions:**
- Restrict who can execute transitions
- Enforce process compliance
- Prevent accidental status changes

**Common condition patterns:**

| Condition Type | Example | Use Case |
|----------------|---------|----------|
| **User-based** | Only assignee can resolve | Ensures owner signs off |
| **Role-based** | Only developers can start progress | Matches team roles |
| **Field-based** | Must have story points to start | Ensures estimation |
| **Subtask-based** | All subtasks must be done | Enforces completeness |
| **Permission-based** | Only admins can cancel | Prevents accidental cancellation |

### Transition Validators

**Common validators:**
1. **Field validator** - Checks field has value
2. **User validator** - Verifies user in correct group
3. **Permission validator** - Ensures user has permission
4. **Date validator** - Confirms date is valid
5. **Regex validator** - Validates field format

**Example validator use cases:**
```bash
# Transition: "Deploy to Production"
Validators:
- Environment field = "Production"
- User in "Release Managers" group
- All subtasks resolved
- Fix Version is set
```

### Post-Functions

**Useful post-functions:**

| Post-Function | When to Use | Example |
|---------------|-------------|---------|
| **Update field** | Auto-set values | Set resolution date when resolved |
| **Assign issue** | Route to next person | Assign to QA when dev complete |
| **Create issue** | Trigger follow-up | Create deployment ticket when approved |
| **Fire event** | Send notifications | Email stakeholders on release |
| **Add comment** | Document change | Add "Automatically closed" comment |

---

## Assignment Best Practices

### Assignment Strategies

**1. Manual Assignment**
```bash
# Assign to specific user
python assign_issue.py PROJ-123 --user john.doe@example.com

# Assign to self
python assign_issue.py PROJ-123 --self
```

**When to use:**
- Small teams where everyone knows who does what
- Ad-hoc work distribution
- Specialized expertise required

**2. Auto-Assignment**

**Common auto-assignment patterns:**

| Trigger | Assignment Rule | Use Case |
|---------|----------------|----------|
| Issue created | Assign to component lead | Route by area |
| Transitioned to "In Progress" | Assign to current user | Claim ownership |
| Transitioned to "In Review" | Assign to tech lead | Peer review |
| Transitioned to "In QA" | Assign to QA team lead | Testing phase |

**3. Round-Robin Assignment**
- Distribute work evenly across team
- Prevents bottlenecks
- Requires automation or app

**4. Component-Based Assignment**
```bash
# Create component with auto-assign
python create_component.py PROJ --name "Backend API" \
  --lead john@example.com --assignee-type COMPONENT_LEAD
```

### Assignment Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Unassigned issues in progress** | No ownership | Require assignee to start work |
| **Assigning to teams** | Diffusion of responsibility | Assign to individuals |
| **Manager always assignee** | Bottleneck | Delegate to team members |
| **Never reassigning** | People stuck | Enable reassignment when needed |
| **Assigning to reporter** | Creator fixes own work | Separate reporting from assignment |

### Assignment Workflow Integration

**Best practices:**
1. **Require assignee before "In Progress"**
   - Ensures someone owns the work
   - Clear accountability

2. **Auto-assign on transition**
   - Streamlines workflow
   - Reduces manual steps

3. **Clear assignee on "Done"**
   - Optional: removes from active work view
   - Debate: some teams keep assignee for history

4. **Reassignment triggers notification**
   - New assignee is notified
   - Previous assignee knows they're off the hook

### Handling Unassigned Issues

**Query for unassigned work:**
```bash
# Find unassigned issues
python jql_search.py "assignee IS EMPTY AND status != Done" --format table
```

**Strategies for triaging:**
1. **Daily triage meeting** - Assign in standup
2. **Component leads** - Auto-assign by component
3. **Round-robin** - Automated distribution
4. **Self-service** - Team members claim work

---

## Version Management

### Version Naming Conventions

**Semantic versioning (recommended):**
```
MAJOR.MINOR.PATCH
  |     |      |
  |     |      └─ Bug fixes
  |     └──────── New features (backward compatible)
  └────────────── Breaking changes

Examples:
- v1.0.0 - Initial release
- v1.1.0 - Added new feature
- v1.1.1 - Bug fix
- v2.0.0 - Breaking change
```

**Date-based versioning:**
```
YYYY.MM or YYYY.MM.DD

Examples:
- 2025.01 - January 2025 release
- 2025.03.15 - March 15, 2025 release
```

**Named releases:**
```
Season/Year or Code names

Examples:
- Spring 2025
- Q1 2025
- Project Aurora
```

**Best practice:** Choose ONE system and stick to it

### Version Lifecycle

**Version states:**

```
Created → Active → Released → Archived
   |        |         |          |
   |        |         |          └─ Hidden from UI, preserved in history
   |        |         └──────────── Fixed release date, no new issues
   |        └────────────────────── Issues being worked on
   └─────────────────────────────── Initial creation
```

**Creating versions:**
```bash
# Create version with dates
python create_version.py PROJ --name "v2.0.0" \
  --start-date 2025-01-01 --release-date 2025-03-31 \
  --description "Major feature release with new dashboard"
```

**Releasing versions:**
```bash
# Release version
python release_version.py PROJ --name "v2.0.0" \
  --date 2025-03-31 --description "Released on schedule"
```

**Archiving versions:**
```bash
# Archive old version
python archive_version.py PROJ --name "v1.0.0"
```

### Fix Version vs Affects Version

| Field | Purpose | When to Set | Example |
|-------|---------|-------------|---------|
| **Fix Version** | When fix will be released | At creation or when prioritizing | Fix in v2.1.0 |
| **Affects Version** | Which version has the bug | When bug is found | Found in v2.0.0 |

**Best practice:**
- Use Fix Version extensively for planning
- Use Affects Version for tracking bug origins
- One issue can have multiple Affects Versions but typically one Fix Version

### Version Planning Best Practices

**1. Plan releases, don't just track them:**
```bash
# Create next 3 versions in advance
python create_version.py PROJ --name "v2.1.0" --release-date 2025-04-30
python create_version.py PROJ --name "v2.2.0" --release-date 2025-05-31
python create_version.py PROJ --name "v2.3.0" --release-date 2025-06-30
```

**2. Use version descriptions:**
- Document release goals
- Note key features
- Track important dates

**3. Monitor version progress:**
```bash
# View versions with issue counts
python get_versions.py PROJ --format table
```

**4. Move issues between versions:**
```bash
# Move incomplete issues to next version (dry-run first)
python move_issues_version.py --jql "fixVersion = v2.0.0 AND status != Done" \
  --target "v2.1.0" --dry-run

# Execute after reviewing
python move_issues_version.py --jql "fixVersion = v2.0.0 AND status != Done" \
  --target "v2.1.0"
```

### Release Cadence Patterns

| Pattern | Frequency | Use Case | Example |
|---------|-----------|----------|---------|
| **Continuous** | As ready | SaaS, web apps | Deploy daily |
| **Sprint-based** | Every 2 weeks | Agile teams | Release per sprint |
| **Monthly** | 1st of month | Regular cadence | v2025.01, v2025.02 |
| **Quarterly** | Every 3 months | Enterprise software | Q1 2025, Q2 2025 |
| **Feature-based** | When features done | Complex products | v2.0 Dashboard, v2.1 API |

### Version Cleanup Strategy

**When to archive:**
- Version is 6+ months old
- All issues are closed
- No longer needed for reports
- Still need audit trail (don't delete, archive)

**Benefits of archiving:**
- Cleaner UI for users
- Faster dropdowns
- Focus on current/future versions
- Preserved in history for reporting

**DON'T delete versions:**
- Loses historical data
- Breaks links in closed issues
- Can't recreate reports

---

## Component Organization

### Component Strategy

**Components represent subsystems or areas of your product/project:**

| Component Strategy | Example | Best For |
|-------------------|---------|----------|
| **Technical areas** | API, Frontend, Database, Mobile | Engineering teams |
| **Product features** | Authentication, Payments, Reporting | Product management |
| **Teams** | Platform, Mobile, DevOps | Multi-team projects |
| **Geographic** | US, EU, APAC | Global teams |
| **Functional** | Development, QA, Documentation | Cross-functional work |

### Component Naming

**Good component names:**
- **Backend API** - Clear, specific
- **iOS App** - Platform identified
- **Payment Processing** - Feature-based
- **Documentation** - Function-based

**Bad component names:**
- **Team 1** - Meaningless to outsiders
- **Misc** - Too vague
- **The thing that does X** - Verbose
- **LEGACY-SYS-2019** - Cryptic

### Component Configuration

**Creating components:**
```bash
# Create component with lead
python create_component.py PROJ --name "Backend API" \
  --description "Server-side REST API and microservices" \
  --lead john@example.com --assignee-type COMPONENT_LEAD
```

**Assignee types:**

| Type | Behavior | Use When |
|------|----------|----------|
| **COMPONENT_LEAD** | Auto-assign to component lead | Clear ownership |
| **PROJECT_LEAD** | Auto-assign to project lead | Centralized triage |
| **PROJECT_DEFAULT** | Use project default assignee | No special routing |
| **UNASSIGNED** | Leave unassigned | Manual assignment |

### Component Best Practices

**1. Limit components per issue:**
- Ideal: 1 component per issue
- Maximum: 2-3 components
- Why: Clearer ownership, better reporting

**2. Assign component leads:**
- Each component should have an owner
- Lead triages issues for that component
- Clear escalation path

**3. Use components for routing:**
```bash
# Create component-based auto-assignment
python create_component.py PROJ --name "Mobile App" \
  --lead mobile-lead@example.com --assignee-type COMPONENT_LEAD
```

**4. Keep component list manageable:**
- 5-15 components is ideal
- Too many = confusion
- Too few = not useful for routing

**5. Archive unused components:**
```bash
# Delete component (migrate issues first)
python delete_component.py --id 10001 --move-to 10002
```

### Component vs Label

| Use Component When | Use Label When |
|--------------------|----------------|
| Represents architectural area | Represents cross-cutting concern |
| Has a clear owner | No specific owner |
| Long-lived subsystem | Temporary categorization |
| Needs auto-assignment | Just for filtering |
| Example: "Backend API" | Example: "tech-debt" |

### Component Reporting

**Useful component-based queries:**

```bash
# Issues by component
python jql_search.py "component = 'Backend API' AND status != Done"

# Unassigned issues in component
python jql_search.py "component = 'Mobile App' AND assignee IS EMPTY"

# Component without issues
python get_components.py PROJ --format table
# (Look for 0 issue count)
```

---

## Work In Progress (WIP) Limits

### What Are WIP Limits?

**WIP Limits restrict the number of issues in a status at one time:**

```
To Do  →  In Progress (WIP: 3)  →  In Review (WIP: 2)  →  Done
  10           🔴🔴🔴                   🟡🟡              ∞
```

**Benefits:**
- Reduces context switching
- Encourages finishing work before starting new
- Surfaces bottlenecks
- Improves flow and cycle time
- Forces prioritization

### Recommended WIP Limits

**Per-status limits:**

| Status | WIP Limit | Reasoning |
|--------|-----------|-----------|
| **To Do** | No limit | Backlog can be large |
| **In Progress** | 1-2 per person | Focus on completion |
| **In Review** | 1.5x team size | Reviews are quick |
| **In Testing** | Team size | Matches throughput |
| **Blocked** | Monitor closely | Shouldn't accumulate |
| **Done** | No limit | Completed work |

**Per-person limits:**

| Role | WIP Limit | Reasoning |
|------|-----------|-----------|
| **Developer** | 1-2 items | Deep focus |
| **QA Engineer** | 2-3 items | Testing multiple features |
| **Tech Lead** | 3-5 items | Reviews + own work |
| **Product Manager** | No strict limit | Coordination role |

### Implementing WIP Limits

**Manual enforcement:**
- Team agreement in standup
- Board visualization (color coding)
- Regular reminders

**Automated enforcement (requires app/plugin):**
- Prevent transitions when limit reached
- Warnings when approaching limit
- Dashboard showing current WIP

### WIP Limit Strategies

**1. Start conservative:**
```
Team of 5 developers
Start with: In Progress WIP = 5 (1 per person)
```

**2. Monitor and adjust:**
- Too strict: Team often blocked
- Too loose: No behavior change
- Just right: Occasional constraint that encourages finishing

**3. Different limits for different types:**

| Issue Type | In Progress Limit | Reasoning |
|------------|-------------------|-----------|
| **Story** | 1 per person | Focus on features |
| **Bug** | 2 per person | Can be quick fixes |
| **Task** | 1 per person | Similar to stories |

**4. Team vs individual limits:**
```
Option A: Team limit of 10 (flexible distribution)
Option B: Individual limit of 2 (strict per person)
```

### Handling WIP Limit Violations

**When WIP limit is reached:**

1. **First priority: Finish existing work**
   - Swarm on blocked items
   - Help with reviews
   - Pair to complete faster

2. **Identify bottlenecks:**
   - Is review taking too long?
   - Is testing backed up?
   - Are issues getting blocked?

3. **Adjust process, not limits:**
   - Add review capacity
   - Improve test automation
   - Address blockers faster

4. **Only increase limits if:**
   - Sustained bottleneck
   - Team composition changed
   - Work nature fundamentally different

### WIP Limits and Priorities

**Priority triage when at WIP limit:**

| Scenario | Action |
|----------|--------|
| **Critical bug comes in** | Pause low-priority work, start bug |
| **High-priority feature** | Finish current work first, then start |
| **Low-priority request** | Add to backlog, don't start |
| **Technical debt** | Only if no higher priorities |

---

## Resolution Discipline

### Common Resolution Values

**Standard resolutions:**

| Resolution | When to Use | Example |
|------------|-------------|---------|
| **Fixed** | Issue resolved successfully | Bug fixed, feature implemented |
| **Won't Fix** | Decided not to address | Edge case, not worth effort |
| **Duplicate** | Same as another issue | Link to original issue |
| **Cannot Reproduce** | Unable to replicate | Bug report lacks info |
| **Won't Do** | Decided not to implement | Feature rejected by stakeholders |
| **Done** | Work completed as requested | Standard completion |

### Setting Resolution

**Using resolve_issue.py:**
```bash
# Resolve as Fixed
python resolve_issue.py PROJ-123 --resolution "Fixed" \
  --comment "Corrected validation logic in user registration"

# Resolve as Won't Fix with explanation
python resolve_issue.py PROJ-123 --resolution "Won't Fix" \
  --comment "Working as designed. Edge case occurs <0.01% of time."

# Resolve as Duplicate
python resolve_issue.py PROJ-456 --resolution "Duplicate" \
  --comment "Duplicate of PROJ-123"
```

### Resolution Best Practices

**1. Always set resolution when closing:**
- Don't leave resolution empty
- Helps with reporting and analytics
- Documents outcome

**2. Add resolution comment:**
```bash
# Good resolution comment
python resolve_issue.py PROJ-123 --resolution "Fixed" \
  --comment "Fixed by updating API endpoint to handle null values. Deployed in v2.1.0."

# Bad resolution comment (empty)
python resolve_issue.py PROJ-123 --resolution "Fixed"
```

**3. Link duplicates:**
```bash
# When resolving as duplicate, link to original
python resolve_issue.py PROJ-456 --resolution "Duplicate"
# Then manually link PROJ-456 → PROJ-123 (Duplicates)
```

**4. Be specific with "Won't Fix":**

| Bad | Good |
|-----|------|
| Won't Fix | Won't Fix - Edge case affecting <1% of users, workaround available |
| Won't Do | Won't Do - Feature conflicts with product roadmap direction |

### Resolution Reporting

**Useful resolution queries:**

```bash
# Fixed issues in last release
python jql_search.py "fixVersion = v2.0.0 AND resolution = Fixed"

# Won't Fix trend (possible feature creep?)
python jql_search.py "resolution = 'Won't Fix' AND resolved >= -30d"

# Duplicates (indicates communication issues?)
python jql_search.py "resolution = Duplicate AND created >= -7d"
```

### Reopening Issues

**When to reopen:**
- Bug recurred
- Feature incomplete
- Solution didn't work

**How to reopen:**
```bash
# Reopen issue
python reopen_issue.py PROJ-123 \
  --comment "Regression found in v2.1.1 - issue still occurs with Safari browser"
```

**Resolution is cleared on reopen** - will need to set again when re-closing

---

## Workflow Patterns by Use Case

### Software Development Workflow

```
Backlog → To Do → In Progress → In Review → In QA → Done
   ↓        ↓          ↓             ↓         ↓      ↓
   └────────┴──────────┴─────────────┴─────────┴──────→ Rejected/Won't Do
```

**Scripts for each transition:**
```bash
# To Do → In Progress
python transition_issue.py PROJ-123 --name "In Progress"
python assign_issue.py PROJ-123 --self

# In Progress → In Review
python transition_issue.py PROJ-123 --name "In Review" \
  --comment "PR: https://github.com/org/repo/pull/456"

# In Review → In QA
python transition_issue.py PROJ-123 --name "In QA"
python assign_issue.py PROJ-123 --user qa-lead@example.com

# In QA → Done
python resolve_issue.py PROJ-123 --resolution "Fixed"
```

### Bug Tracking Workflow

```
Open → Investigating → In Progress → Fixed → Verified → Closed
  ↓         ↓              ↓           ↓        ↓         ↓
  └─────────┴──────────────┴───────────┴────────┴─────────→ Won't Fix / Cannot Reproduce
```

**Key difference:** Verification step before closing

```bash
# Open → Investigating
python transition_issue.py BUG-789 --name "Investigating"
python assign_issue.py BUG-789 --user dev-lead@example.com

# Fixed → Verified
python transition_issue.py BUG-789 --name "Verified"
python assign_issue.py BUG-789 --user qa@example.com

# Verified → Closed
python resolve_issue.py BUG-789 --resolution "Fixed"
```

### Service Desk Workflow (JSM)

```
Waiting for Support → In Progress → Waiting for Customer → Resolved → Closed
         ↓                 ↓                  ↓                ↓
         └─────────────────┴──────────────────┴────────────────→ Cancelled
```

**Customer interaction focus:**

```bash
# Start working on request
python transition_issue.py REQ-456 --name "In Progress"

# Request customer info
python transition_issue.py REQ-456 --name "Waiting for Customer" \
  --comment "Please provide your account number for verification"

# Resolve request
python resolve_issue.py REQ-456 --resolution "Done" \
  --comment "Password reset link sent to registered email"
```

### Incident Management Workflow

```
Open → Investigating → In Progress → Monitoring → Resolved → Closed
  ↓         ↓              ↓             ↓           ↓
  └─────────┴──────────────┴─────────────┴───────────→ False Alarm
```

**Time-sensitive transitions:**

```bash
# Critical incident - start immediately
python transition_issue.py INC-999 --name "Investigating"
python assign_issue.py INC-999 --user oncall-engineer@example.com

# Move to monitoring after fix
python transition_issue.py INC-999 --name "Monitoring" \
  --comment "Fix deployed, monitoring for 24 hours"

# Close after monitoring period
python resolve_issue.py INC-999 --resolution "Fixed"
```

### Release Management Workflow

```
Requested → Planning → Development → Testing → Staging → Production → Done
     ↓          ↓           ↓            ↓         ↓          ↓
     └──────────┴───────────┴────────────┴─────────┴──────────→ Cancelled
```

**With deployment tracking:**

```bash
# Create release version
python create_version.py PROJ --name "v2.5.0" \
  --start-date 2025-02-01 --release-date 2025-02-28

# Transition through stages
python transition_issue.py REL-100 --name "Development"
python transition_issue.py REL-100 --name "Testing"
python transition_issue.py REL-100 --name "Staging"
python transition_issue.py REL-100 --name "Production"

# Mark as done
python resolve_issue.py REL-100 --resolution "Done"
```

---

## Common Pitfalls

### Workflow Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Status sprawl** | 15+ statuses, team confused | Consolidate to 5-7 key statuses |
| **One-way workflows** | Can't handle rework | Allow backward transitions where needed |
| **Skip-friendly workflows** | Too many optional transitions | Enforce key steps |
| **Duplicate statuses** | "In Review" and "Reviewing" | Standardize naming |
| **Permission chaos** | Different rules per project | Centralize workflow management |

### Assignment Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Perpetually unassigned** | No ownership | Require assignee for "In Progress" |
| **Assign to teams** | Diffusion of responsibility | Assign to individuals |
| **Over-assigning** | One person has 30+ issues | Use WIP limits |
| **Never reassigning** | Bottlenecks | Enable fluid reassignment |
| **Ghost assignees** | Assigned to people who left | Regular cleanup |

### Version Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **No versions** | Can't track releases | Create version structure |
| **Too many versions** | 50+ unreleased versions | Archive old, merge duplicates |
| **Inconsistent naming** | "v2.0", "2.1", "February" | Pick one naming scheme |
| **Never releasing** | Versions stay unreleased forever | Regular release cadence |
| **No descriptions** | Can't tell versions apart | Document purpose of each version |

### Component Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **No components** | Can't categorize work | Define 5-10 key components |
| **Too many components** | 30+ components | Consolidate by theme |
| **Inconsistent use** | Some issues have, some don't | Make components required |
| **Component per person** | Tied to individuals | Use architectural areas |
| **Never updated** | Components for old subsystems | Regular component review |

### Resolution Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Empty resolution** | Don't know why closed | Always set resolution |
| **Only use "Done"** | No distinction | Use specific resolutions |
| **No resolution comment** | Missing context | Add explanation |
| **Wrong resolution** | "Fixed" for "Won't Do" | Use accurate resolution |
| **Never reopen** | Regressions get new issues | Reopen original issue |

### Red Flags to Watch For

**In sprint/active work:**
- Issue "In Progress" for 7+ days without update
- 5+ issues assigned to one person
- Issue transitioning backward repeatedly (ping-pong)
- Required fields missing on "Done" issues
- No comments or activity for 3+ days

**In backlog:**
- Issues older than 6 months without grooming
- Hundreds of unassigned issues
- No components or versions set
- Vague summaries ("Fix bug", "Update feature")

**In workflow:**
- >10 available transitions from one status
- Different workflows for same issue type
- Workflow changes monthly
- No documentation of workflow

**In versions:**
- 20+ unreleased versions
- No issues in next version
- Release dates in the past
- Versions with 1-2 issues

**In components:**
- Components with 0 issues
- All issues in "Other" component
- 30+ components in one project
- No component leads assigned

---

## Quick Reference Card

### Essential Transition Commands

```bash
# View available transitions
python get_transitions.py PROJ-123

# Transition by name
python transition_issue.py PROJ-123 --name "In Progress"

# Transition with comment
python transition_issue.py PROJ-123 --name "In Review" \
  --comment "Ready for code review"

# Resolve issue
python resolve_issue.py PROJ-123 --resolution "Fixed"

# Reopen issue
python reopen_issue.py PROJ-123
```

### Essential Assignment Commands

```bash
# Assign to user
python assign_issue.py PROJ-123 --user john@example.com

# Assign to self
python assign_issue.py PROJ-123 --self

# Unassign
python assign_issue.py PROJ-123 --unassign
```

### Essential Version Commands

```bash
# Create version
python create_version.py PROJ --name "v2.0.0" \
  --start-date 2025-01-01 --release-date 2025-03-31

# List versions
python get_versions.py PROJ --format table

# Release version
python release_version.py PROJ --name "v2.0.0" --date 2025-03-31

# Archive version
python archive_version.py PROJ --name "v1.0.0"

# Move issues between versions
python move_issues_version.py \
  --jql "fixVersion = v2.0.0 AND status != Done" \
  --target "v2.1.0" --dry-run
```

### Essential Component Commands

```bash
# Create component
python create_component.py PROJ --name "Backend API" \
  --lead john@example.com --assignee-type COMPONENT_LEAD

# List components
python get_components.py PROJ --format table

# Update component
python update_component.py --id 10000 --name "New Name"

# Delete component
python delete_component.py --id 10000 --move-to 10001
```

### Workflow Status Checklist

**Before starting work:**
- [ ] Issue has clear acceptance criteria
- [ ] Estimate is set
- [ ] Issue is assigned
- [ ] Priority is appropriate
- [ ] Component is set
- [ ] Fix version is set (if planning releases)

**Before marking done:**
- [ ] All acceptance criteria met
- [ ] Tests written and passing
- [ ] Code reviewed (if applicable)
- [ ] Documentation updated
- [ ] Resolution is set
- [ ] Resolution comment added

### Lifecycle Health Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| **In Progress items per person** | 1-2 | 3-4 | 5+ |
| **Time in "In Progress"** | 1-3 days | 4-7 days | 8+ days |
| **Unreleased versions** | 2-4 | 5-10 | 10+ |
| **Issues without components** | <5% | 5-20% | 20%+ |
| **Unassigned "In Progress"** | 0% | 1-5% | 5%+ |
| **Issues without resolution** | 0% | 1-2% | 2%+ |

### Status Category Reference

```
To Do (Blue):
- Backlog
- To Do
- Open
- New
- Selected for Development

In Progress (Yellow):
- In Progress
- In Development
- In Review
- Code Review
- In Testing
- In QA
- Awaiting Approval
- Blocked

Done (Green):
- Done
- Closed
- Resolved
- Released
- Deployed
- Verified
```

---

*Last updated: December 2025*

## Sources

This guide incorporates best practices from:
- [Idalko: A Guide to Jira Workflow Best Practices](https://idalko.com/blog/jira-workflow-best-practices)
- [Unito: The Ultimate Guide to Efficiency: Jira Best Practices in 2025](https://unito.io/blog/jira-efficiency-best-practices/)
- [HeroCoders: Understanding Jira Issue Statuses](https://www.herocoders.com/blog/understanding-jira-issue-statuses)
- [Atlassian: Learn versions with Jira Tutorial](https://www.atlassian.com/agile/tutorials/versions)
- [Apwide: Release Management in Jira 2025](https://www.apwide.com/release-management-in-jira/)
- [DevSamurai: Version and Release Management in Jira](https://www.devsamurai.com/en/version-and-release-management-in-jira/)
- [Atlassian Support: What are Jira components?](https://support.atlassian.com/jira-software-cloud/docs/what-are-jira-components/)
- [Atlassian Community: Jira Essentials: Adding work in progress limits](https://community.atlassian.com/t5/Jira-articles/Jira-Essentials-Adding-work-in-progress-limits/ba-p/1621358)
