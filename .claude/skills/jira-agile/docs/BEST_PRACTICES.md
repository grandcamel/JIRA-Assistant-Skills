# JIRA Agile & Scrum Best Practices Guide

Comprehensive guide to JIRA Agile and Scrum best practices for effective sprint planning, epic management, backlog refinement, and team velocity optimization.

---

## Table of Contents

1. [Sprint Planning](#sprint-planning)
2. [Story Point Estimation](#story-point-estimation)
3. [Epic Management](#epic-management)
4. [Backlog Refinement](#backlog-refinement)
5. [Board Configuration](#board-configuration)
6. [Velocity Tracking & Forecasting](#velocity-tracking--forecasting)
7. [Definition of Ready & Done](#definition-of-ready--done)
8. [Sprint Retrospectives](#sprint-retrospectives)
9. [Release Planning with Epics](#release-planning-with-epics)
10. [Common Pitfalls](#common-pitfalls)
11. [Quick Reference Card](#quick-reference-card)

---

## Sprint Planning

### Before Sprint Planning

**Pre-Planning Checklist:**
- [ ] Backlog refined with acceptance criteria
- [ ] Top 20+ items estimated with story points
- [ ] Dependencies identified and linked
- [ ] Team capacity calculated
- [ ] Previous sprint reviewed
- [ ] Product owner prepared with priorities

**Capacity Formula:**
```
Sprint Capacity = (Team Size × Sprint Days × Hours per Day × Focus Factor)

Where:
- Team Size: Number of developers
- Sprint Days: Working days (typically 10 for 2-week sprint)
- Hours per Day: Productive hours (typically 6-7)
- Focus Factor: 0.7-0.8 (buffer for meetings, unexpected work)

Example: 5 developers × 10 days × 6 hours × 0.8 = 240 hours
```

**Velocity-Based Capacity:**
```
Sprint Capacity = Team Velocity × 0.8
```
Use 80% to buffer for:
- Scrum ceremonies and meetings
- Code reviews and collaboration
- Unplanned work and urgent bugs
- Learning, mentoring, and growth
- Personal time off and sick days

### Sprint Planning Meeting

**Recommended Duration:**
| Sprint Length | Planning Time |
|---------------|---------------|
| 1 week | 1 hour |
| 2 weeks | 2 hours |
| 3 weeks | 3 hours |
| 4 weeks | 4 hours |

**Required Attendees:**
- Product Owner (presents priorities)
- Scrum Master (facilitates meeting)
- Development Team (commits to work)

**Sprint Goal Template:**
> "By end of sprint, [user/stakeholder] will be able to [capability] so that [value/outcome]."

**Examples:**
- "By end of sprint, users will be able to reset their password via email so that they can regain account access."
- "By end of sprint, customers will be able to export reports as PDF so that they can share data with stakeholders."
- "By end of sprint, the API will support rate limiting so that we can prevent service abuse."

### In Jira: Sprint Planning Steps

```bash
# 1. Create the sprint
python create_sprint.py --board 123 --name "Sprint 42" \
  --start 2025-01-20 --end 2025-02-03 \
  --goal "Launch user authentication MVP"

# 2. Add high-priority items to sprint
python move_to_sprint.py --sprint 456 \
  --jql "project=PROJ AND status='To Do' AND priority IN (High, Highest)" \
  --rank top --dry-run

# 3. Review and confirm
python get_sprint.py 456 --with-issues

# 4. Start the sprint
python manage_sprint.py --sprint 456 --start
```

### Sprint Commitment Guidelines

**Do:**
- Commit to what the team believes is achievable
- Include buffer for code review and testing
- Account for known absences
- Reference historical velocity
- Leave room for urgent bugs

**Don't:**
- Over-commit to please stakeholders
- Ignore team's actual capacity
- Forget about non-development work
- Skip estimation for "small" tasks
- Add unestimated work to sprint

---

## Story Point Estimation

### Fibonacci Scale

The Fibonacci sequence (1, 2, 3, 5, 8, 13, 21) works because gaps between numbers grow progressively wider, reflecting how uncertainty increases with complexity.

| Points | Complexity | Time Range | Example |
|--------|-----------|------------|---------|
| **1** | Trivial | 1-2 hours | Fix typo, config change, CSS tweak |
| **2** | Small | Half day | Add field validation, update copy |
| **3** | Medium-Small | 1 day | Simple API endpoint, basic UI component |
| **5** | Medium | 2-3 days | Feature with tests, database migration |
| **8** | Large | 3-5 days | Complex feature, multiple integration points |
| **13** | Very Large | 1 week | Major feature, requires design/research |
| **21** | Too Large | 2+ weeks | Should be split into smaller stories |

**Important:** Story points measure **complexity and uncertainty**, not just time. Include:
- Development effort
- Testing and QA
- Code review
- Documentation
- Technical risk/unknowns

### T-Shirt Sizing

Use for early-stage estimation or epic-level planning:

| Size | Story Points | Use When |
|------|--------------|----------|
| **XS** | 1-2 | Simple configuration or content changes |
| **S** | 3-5 | Single component or straightforward feature |
| **M** | 8-13 | Standard feature with normal complexity |
| **L** | 20-30 | Large feature spanning multiple components |
| **XL** | 40+ | Epic-sized work (should be broken down) |

**Conversion to Fibonacci:**
- XS → 1 or 2
- S → 3 or 5
- M → 8
- L → 13 or 21
- XL → Break into smaller epics

### Planning Poker

**Process:**
1. Product owner reads user story
2. Team asks clarifying questions
3. Each member privately selects estimate card
4. All reveal simultaneously
5. Discuss high/low outliers
6. Re-vote until consensus (usually 2-3 rounds)

**Benefits:**
- Engages entire team
- Surfaces different perspectives
- Reduces anchoring bias
- Builds shared understanding

### Estimation Best Practices

**Do:**
- Compare to past completed stories (reference stories)
- Estimate as a team, not individually
- Use relative sizing (compare stories to each other)
- Re-estimate if story changes significantly
- Track actual vs estimated for learning

**Don't:**
- Convert points to hours (defeats the purpose)
- Estimate in a vacuum without team input
- Use points for individual performance reviews
- Change historical estimates after completion
- Estimate without acceptance criteria

### In Jira: Setting Story Points

```bash
# Single issue estimation
python estimate_issue.py PROJ-101 --points 5

# Bulk estimation for similar stories
python estimate_issue.py --jql "sprint=456 AND type=Story" --points 3 --dry-run

# With Fibonacci validation
python estimate_issue.py PROJ-101 --points 5 --validate-fibonacci

# View sprint estimates
python get_estimates.py --sprint 456 --group-by status
```

---

## Epic Management

### Epic Lifecycle

| Stage | Description | Actions |
|-------|-------------|---------|
| **1. Draft** | Initial idea, rough scope | Write epic summary, add to backlog |
| **2. Discovery** | Research and validation | Spike work, gather requirements, assess feasibility |
| **3. Refined** | Stories written | Break into user stories, add acceptance criteria |
| **4. Ready** | Estimated and prioritized | Estimate all stories, map dependencies, prioritize |
| **5. In Progress** | Stories in active sprints | Track progress, adjust as needed |
| **6. Done** | All stories complete | Value delivered, epic closed |

### Epic Sizing Guidelines

**Ideal Epic Size:**
- **Target:** 2-4 sprints to complete
- **Minimum:** At least 3-5 user stories
- **Maximum:** No more than 6 months of work

**If too large:**
- Break into smaller epics
- Create epic hierarchy (parent epic → child epics)
- Prioritize and sequence delivery

**If too small:**
- Consider making it a story instead
- Combine with related work
- Evaluate if it provides standalone value

### Epic Template

```markdown
# Epic Name: [Short, memorable name]

## Business Goal
[Why are we doing this? What problem does it solve?]

## Target Users
[Who will benefit from this?]

## Success Criteria
- [ ] Measurable outcome 1
- [ ] Measurable outcome 2
- [ ] Measurable outcome 3

## Scope
**In Scope:**
- Feature A
- Feature B

**Out of Scope:**
- Feature C (future epic)
- Feature D (not needed)

## Dependencies
- Blocks: [Other epics/stories]
- Blocked by: [Prerequisites]

## Estimated Timeline
Target: Q2 2025 (Sprints 15-18)
```

### Epic Progress Tracking

**Key Metrics:**
- **Issue Completion:** X/Y issues done (percentage)
- **Story Points:** Completed/Total points
- **Scope Change:** Stories added/removed
- **Blockers:** Number of blocked issues
- **Burn Rate:** Points completed per sprint

### In Jira: Epic Management

```bash
# Create epic with full details
python create_epic.py --project PROJ \
  --summary "User Authentication System" \
  --description "## Goal\nSecure login with OAuth support" \
  --epic-name "Auth" \
  --color blue \
  --assignee self \
  --priority High

# Add stories to epic
python add_to_epic.py --epic PROJ-100 \
  --jql "project=PROJ AND labels=auth AND type=Story"

# Track epic progress
python get_epic.py PROJ-100 --with-children

# Example output:
# Epic: PROJ-100
# Summary: User Authentication System
# Progress: 12/20 issues (60%)
# Story Points: 45/80 (56%)
```

### Epic Color Coding

Use colors strategically for visual organization:

| Color | Use For |
|-------|---------|
| **Blue** | Core features, platform work |
| **Green** | Customer-facing improvements |
| **Yellow** | Technical debt, refactoring |
| **Red** | Critical fixes, security |
| **Purple** | Infrastructure, DevOps |
| **Orange** | Experimental, research |

---

## Backlog Refinement

### Refinement Schedule

**Recommended Frequency:**
- **Two-week sprints:** One 1-hour session mid-sprint
- **One-week sprints:** 30-minute session midweek
- **Timing:** 2-3 days before sprint planning

**Don't refine:**
- Too far in advance (priorities change)
- During sprint planning (wastes time)
- Without team participation

### Weekly Refinement Checklist

**Process:**
- [ ] Review top 20-30 backlog items
- [ ] Add acceptance criteria to undefined stories
- [ ] Break down large stories (>13 points)
- [ ] Estimate new items with team
- [ ] Identify and link dependencies
- [ ] Flag blockers and escalate
- [ ] Archive/remove stale items (>6 months)
- [ ] Re-prioritize based on business value

**Time Budget:**
- **Maximum 15 minutes per item**
- **If longer:** Schedule separate discussion

### Backlog Health: DEEP Framework

A healthy backlog should be **DEEP:**

| Attribute | Meaning | How to Achieve |
|-----------|---------|----------------|
| **Detailed** | Top items have acceptance criteria | Refine top 2-3 sprints worth |
| **Estimated** | Items sized with story points | Estimate during refinement |
| **Emergent** | Backlog evolves over time | Regular reprioritization |
| **Prioritized** | Highest value items at top | Sort by business value |

### Acceptance Criteria Template

```markdown
## User Story
As a [user type], I want [goal] so that [benefit].

## Acceptance Criteria
**Given** [initial context]
**When** [action taken]
**Then** [expected outcome]

**Examples:**
1. Given I'm on the login page
   When I enter valid credentials
   Then I'm redirected to my dashboard

2. Given I enter an invalid password
   When I click "Login"
   Then I see error message "Invalid credentials"

3. Given I click "Forgot Password"
   When I enter my email
   Then I receive password reset link
```

### Refinement Anti-Patterns

**Avoid:**
- **Dream vault:** Adding every idea without evaluation
- **Stale backlog:** Items older than 6 months with no progress
- **No owner:** Items without clear product owner
- **Analysis paralysis:** Over-analyzing before starting
- **Mid-sprint changes:** Adding work during active sprint

### In Jira: Backlog Refinement

```bash
# View backlog grouped by epic
python get_backlog.py --board 123 --group-by epic

# Find unestimated items
python jql_search.py "sprint IS EMPTY AND 'Story Points' IS EMPTY AND type IN (Story, Task)"

# Bulk estimate similar items
python estimate_issue.py --jql "labels=quick-win" --points 2 --dry-run

# Prioritize items
python rank_issue.py PROJ-201 --top  # Move to top priority
python rank_issue.py PROJ-205 --before PROJ-201  # Insert before item
```

---

## Board Configuration

### Scrum vs Kanban

| Aspect | Scrum Board | Kanban Board |
|--------|-------------|--------------|
| **Timeboxes** | Fixed sprints (1-4 weeks) | Continuous flow |
| **Planning** | Sprint planning ceremony | Pull work when capacity available |
| **Commitment** | Sprint backlog commitment | No sprint commitment |
| **Changes** | Locked sprint scope | Can change priorities anytime |
| **Metrics** | Velocity, burndown | Cycle time, throughput |
| **WIP Limits** | Sprint capacity | Column-based limits |
| **Best for** | Predictable delivery, releases | Support, operations, continuous delivery |

### Recommended Workflow Statuses

**Simple Workflow (3 statuses):**
```
To Do → In Progress → Done
```

**Development Workflow (5 statuses):**
```
Backlog → To Do → In Progress → In Review → Done
```

**Full Workflow (7 statuses):**
```
Backlog → To Do → In Progress → In Review → In QA → Ready for Deploy → Done
```

**Use States, Not Actions:**
| Bad (Action) | Good (State) |
|--------------|--------------|
| Review | In Review |
| Test | In QA |
| Deploy | Ready for Deploy |
| Approve | Awaiting Approval |

### Work In Progress (WIP) Limits

**Benefits:**
- Reduces context switching
- Surfaces bottlenecks
- Improves cycle time
- Forces completion before starting new work
- Increases collaboration

**Setting WIP Limits:**

**Formula:** `WIP Limit = 2/3 to 3/4 × Team Size`

**Example for 9-person team:**
- Minimum: 6 items
- Maximum: 7 items

**Recommended Limits by Status:**
| Status | WIP Limit | Reasoning |
|--------|-----------|-----------|
| **To Do** | Unlimited | Backlog staging area |
| **In Progress** | 2 per person | Focus on completion |
| **In Review** | 1.5× team size | Reviews are quick |
| **In QA** | Team size | Matches throughput |
| **Done** | Unlimited | Completed work |

**When WIP limit exceeded:**
- Stop starting new work
- Focus on completing in-progress items
- Investigate bottleneck
- Team swarms on blocked items

### Board Columns and Swim Lanes

**Column Configuration:**
- Map each status to a column
- Group related statuses (To Do + Backlog)
- Add "Waiting" column for blocked items

**Swim Lane Strategies:**
| Use | Description | Example |
|-----|-------------|---------|
| **Priority** | Separate critical work | Expedite / High / Normal |
| **Epic** | Group by feature | Auth Epic / API Epic |
| **Assignee** | Personal queues | Alice / Bob / Charlie |
| **Type** | Separate work types | Bug / Story / Task |

### Board Filters

**Useful Filters:**
```jql
# My current work
assignee = currentUser() AND sprint IN openSprints() AND status != Done

# Team blockers
project = PROJ AND (status = Blocked OR "Flagged" = Impediment)

# High priority unassigned
sprint IN openSprints() AND assignee IS EMPTY AND priority IN (High, Highest)

# Issues needing review
sprint IN openSprints() AND status = "In Review" AND updated <= -2d
```

---

## Velocity Tracking & Forecasting

### Understanding Velocity

**Velocity** = Total story points completed per sprint

**Key Principles:**
- Velocity is team-specific (don't compare teams)
- Use 3-5 sprint rolling average
- Velocity stabilizes after 3-4 sprints
- Used for capacity planning, not performance

### Calculating Team Velocity

```
Sprint Velocity = Sum of story points for all completed items

Example Sprint 42:
- PROJ-101: 5 points (Done)
- PROJ-102: 8 points (Done)
- PROJ-103: 3 points (Done)
- PROJ-104: 5 points (In Progress - NOT counted)

Velocity = 5 + 8 + 3 = 16 points
```

**Rolling Average Velocity:**
```
Average Velocity = (Sprint N + Sprint N-1 + Sprint N-2) / 3

Example:
- Sprint 40: 18 points
- Sprint 41: 15 points
- Sprint 42: 16 points

Average = (18 + 15 + 16) / 3 = 16.3 points per sprint
```

### Forecasting with Velocity

**Formula:**
```
Sprints Required = Total Remaining Points / Average Velocity

Example:
- Epic has 80 points remaining
- Team velocity: 16 points/sprint
- Sprints needed: 80 / 16 = 5 sprints
```

**Add buffer for uncertainty:**
- **Low confidence:** Add 50% buffer
- **Medium confidence:** Add 25% buffer
- **High confidence:** Add 10% buffer

### Velocity Trends to Monitor

| Trend | Meaning | Action |
|-------|---------|--------|
| **Increasing** | Team improving efficiency | Sustainable? Check for quality issues |
| **Decreasing** | Capacity or complexity issues | Investigate: Scope creep? Technical debt? |
| **Stable** | Predictable delivery | Ideal for forecasting |
| **Volatile** | Inconsistent estimation or capacity | Review estimation process |
| **>30% swing** | Red flag | Deep dive into root cause |

### Burndown Chart Best Practices

**Ideal Burndown:**
- Smooth downward slope
- Crosses zero on last day of sprint
- Minor daily fluctuations acceptable

**Warning Signs:**
| Pattern | Issue | Solution |
|---------|-------|----------|
| **Flat line** | No progress | Daily standup - identify blockers |
| **Trending up** | Scope creep | Stop adding work, focus on commitment |
| **Steep drop at end** | Last-minute completion | Earlier demos, better breakdown |
| **Never reaches zero** | Over-commitment | Reduce sprint capacity |

### In Jira: Velocity Tracking

```bash
# Get sprint summary with velocity
python get_sprint.py 456 --with-issues --output json

# Get epic estimates for forecasting
python get_estimates.py --epic PROJ-100

# Analyze backlog size
python get_backlog.py --board 123 --output json | grep "Story Points"
```

**Manual Velocity Calculation:**
1. Go to Reports → Velocity Chart
2. Review last 5 sprints
3. Calculate average committed vs completed
4. Use average completed for capacity planning

---

## Definition of Ready & Done

### Definition of Ready (DoR)

Stories are "Ready" when they meet these criteria before sprint planning:

**Checklist:**
- [ ] User story written in "As a... I want... so that..." format
- [ ] Clear acceptance criteria defined (Given/When/Then)
- [ ] Story points estimated by team
- [ ] Dependencies identified and linked
- [ ] No unresolved blockers
- [ ] Mockups/designs attached (if UI work)
- [ ] Technical approach discussed and understood
- [ ] Fits within one sprint (≤13 points)
- [ ] Business value understood
- [ ] Test approach identified

**Benefits:**
- Reduces mid-sprint blockers
- Improves sprint planning efficiency
- Sets clear expectations
- Minimizes wasted effort

### Definition of Done (DoD)

Stories are "Done" when they meet these criteria:

**Development DoD:**
- [ ] Code written and peer-reviewed
- [ ] Unit tests written and passing
- [ ] Integration tests passing
- [ ] Code merged to main branch
- [ ] No critical linting errors
- [ ] Technical documentation updated

**Quality DoD:**
- [ ] Acceptance criteria verified
- [ ] Manual testing completed
- [ ] Cross-browser tested (if UI)
- [ ] Accessibility standards met
- [ ] Security review passed (if needed)
- [ ] Performance benchmarks met

**Delivery DoD:**
- [ ] Deployed to staging environment
- [ ] Demo completed for stakeholders
- [ ] User documentation updated
- [ ] Product owner approved
- [ ] Metrics/monitoring in place
- [ ] Ready for production release

**Team-Specific Additions:**
- Design review completed
- Localization/translation done
- Analytics events implemented
- Feature flag configured

### DoR vs DoD in Practice

| Aspect | Definition of Ready | Definition of Done |
|--------|--------------------|--------------------|
| **When** | Before sprint planning | Before marking "Done" |
| **Who owns** | Product Owner | Development Team |
| **Focus** | Ready to start work | Ready to ship |
| **Checklist type** | Pre-work validation | Completion criteria |

### In Jira: Implementing DoR/DoD

**Using Custom Fields:**
1. Create "DoR Checklist" field
2. Create "DoD Checklist" field
3. Add to issue screens

**Using Subtasks:**
```bash
# Create DoD subtasks automatically
python create_subtask.py --parent PROJ-101 --summary "Write unit tests"
python create_subtask.py --parent PROJ-101 --summary "Update documentation"
python create_subtask.py --parent PROJ-101 --summary "Deploy to staging"
```

**Using Workflow Validators:**
- Block "Start Progress" transition if DoR not met
- Block "Done" transition if DoD not met
- Require resolution field for Done status

---

## Sprint Retrospectives

### Retrospective Timing

**When:** End of every sprint, before planning next sprint

**Duration:**
- 1-week sprint: 45 minutes
- 2-week sprint: 1.5 hours
- 3-week sprint: 2 hours

**Attendees:**
- Scrum Master (facilitates)
- Development Team (required)
- Product Owner (optional)

### Retrospective Format

**Classic Structure:**

**1. Set the Stage (5 min)**
- Review sprint goal
- Set retrospective focus
- Establish safe environment

**2. Gather Data (15 min)**
- What went well?
- What didn't go well?
- What puzzles us?

**3. Generate Insights (20 min)**
- Why did these things happen?
- What patterns emerge?
- What's within our control?

**4. Decide Actions (15 min)**
- What will we try next sprint?
- Who owns each action?
- How will we measure success?

**5. Close (5 min)**
- Summarize action items
- Appreciation round

### Retrospective Techniques

**Start/Stop/Continue:**
| Category | Question |
|----------|----------|
| **Start** | What should we start doing? |
| **Stop** | What should we stop doing? |
| **Continue** | What's working that we should keep? |

**4 Ls:**
- **Loved:** What did you love?
- **Learned:** What did you learn?
- **Lacked:** What was missing?
- **Longed for:** What do you wish we had?

**Sailboat:**
- **Wind (helps):** What's propelling us forward?
- **Anchor (hinders):** What's slowing us down?
- **Rocks (risks):** What obstacles are ahead?
- **Island (goal):** Where are we headed?

### Action Items Best Practices

**SMART Actions:**
- **Specific:** Clear, concrete action
- **Measurable:** Observable outcome
- **Achievable:** Within team's control
- **Relevant:** Addresses identified issue
- **Time-bound:** Complete by next retro

**Examples:**
| Vague | SMART |
|-------|-------|
| "Better communication" | "Daily standup at 9:30 AM sharp, max 15 min" |
| "Reduce bugs" | "Add unit tests for all new API endpoints" |
| "Improve velocity" | "Refine backlog 2 days before sprint planning" |

### Tracking Retro Actions in Jira

```bash
# Create action item as task
python create_issue.py --project PROJ \
  --type Task \
  --summary "ACTION: Add unit test requirement to DoD" \
  --labels retro-action \
  --assignee alice@company.com \
  --priority Medium

# Review open retro actions
python jql_search.py "labels=retro-action AND status != Done"
```

### Retrospective Anti-Patterns

**Avoid:**
- **Blame game:** Focus on systems, not people
- **Same issues every sprint:** Need deeper root cause analysis
- **No action items:** Every retro should have 1-3 actions
- **Too many actions:** Can't improve everything at once
- **No follow-up:** Review previous actions first
- **Leadership present:** May stifle honest feedback
- **Skipping retros:** Continuous improvement requires regular reflection

---

## Release Planning with Epics

### Release Structure

**Hierarchy:**
```
Release (Fix Version)
├── Epic 1
│   ├── Story 1.1
│   ├── Story 1.2
│   └── Story 1.3
├── Epic 2
│   ├── Story 2.1
│   └── Story 2.2
└── Epic 3
    └── Story 3.1
```

### Release Planning Process

**1. Define Release Goal**
```markdown
## Release: v2.0 - Q2 2025

**Target Users:** Enterprise customers
**Business Goal:** Enable SSO for large organizations
**Key Features:**
- SAML authentication
- User provisioning
- Audit logging
```

**2. Identify Epics**
- List all epics needed for release
- Estimate each epic (story points or t-shirt)
- Sequence epics by dependency

**3. Sprint Allocation**
```
Release Timeline: 6 sprints (12 weeks)

Sprint 15-16: Epic A (Auth Framework)
Sprint 17-18: Epic B (SAML Integration)
Sprint 19: Epic C (User Provisioning)
Sprint 20: Hardening, bug fixes
```

**4. Track Progress**
- Monitor epic completion weekly
- Re-forecast based on velocity
- Adjust scope if needed

### Release Sizing

**Formula:**
```
Release Size = Sum of all epic story points

Epic Breakdown:
- Epic A: 45 points
- Epic B: 60 points
- Epic C: 30 points
- Bug buffer: 15 points

Total: 150 points
```

**Sprints Required:**
```
Sprints = Total Points / Team Velocity

Example:
- Release: 150 points
- Velocity: 25 points/sprint
- Sprints: 150 / 25 = 6 sprints
```

**Add buffer:**
- **Greenfield:** Add 20% buffer
- **Existing codebase:** Add 30% buffer
- **Legacy system:** Add 50% buffer

### In Jira: Release Planning

**Using Fix Versions:**
```bash
# Create release version
# (Done via Jira UI: Project Settings → Releases)

# Tag epics for release
python update_issue.py PROJ-100 --fix-version "v2.0"
python update_issue.py PROJ-101 --fix-version "v2.0"

# View release readiness
python jql_search.py "fixVersion = 'v2.0' AND status != Done" \
  --show-links --output json

# Track release progress
python get_epic.py PROJ-100 --with-children
python get_estimates.py --epic PROJ-100
```

**Release Board Filter:**
```jql
fixVersion = "v2.0" AND status NOT IN (Done, Closed)
ORDER BY epic ASC, rank ASC
```

### Release Health Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Scope completion** | Done points / Total points | >90% |
| **Velocity trend** | Current vs average | Within 20% |
| **Bug ratio** | Bugs / Features | <20% |
| **Carry-over rate** | Incomplete / Committed | <10% |
| **Epic completion** | Done epics / Total epics | 100% |

### Release Risk Management

**High-Risk Indicators:**
- Velocity decreasing >20%
- Multiple epics behind schedule
- Critical dependencies unresolved
- Key team members unavailable
- Scope creep >15% of original

**Mitigation Strategies:**
1. **Scope reduction:** Cut non-critical features
2. **Sprint extension:** Add 1-2 sprints to timeline
3. **Resource addition:** Temporary team augmentation
4. **Parallel work:** Split dependencies where possible
5. **Early release:** Ship MVP, defer enhancements

---

## Common Pitfalls

### Anti-Patterns to Avoid

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Mega-stories** | Can't complete in one sprint | Break into smaller stories (≤8 points) |
| **Goldilocks estimation** | Always hits estimate exactly | Embrace variance, track actuals |
| **Zombie backlog** | Items older than 6 months | Archive stale items quarterly |
| **Scope creep** | Adding work mid-sprint | Lock sprint after planning |
| **Hero culture** | Single person completes everything | Pair programming, knowledge sharing |
| **No subtasks** | Large stories with unclear progress | Break down into subtasks |
| **Skipping retros** | No continuous improvement | Make retros mandatory |
| **Status sprawl** | 10+ workflow statuses | Simplify to 5-7 statuses |
| **Meeting issues** | Tracking ceremonies as stories | Only track deliverable work |

### Red Flags in Sprint

**During Sprint:**
- Same issue "In Progress" for 5+ days → Check for blockers
- No comments for 3+ days → Assignee may need help
- Blocked with no action plan → Escalate immediately
- Burndown chart trending up → Scope creep, stop adding work
- Multiple failed pull requests → Technical approach issue

**At Sprint Review:**
- <70% sprint goal achieved → Over-commitment or blockers
- Multiple stories "almost done" → Definition of Done unclear
- No demo-able features → Stories too large or infrastructure-heavy
- Stakeholder surprised by results → Communication breakdown

### Red Flags in Backlog

**Backlog Health Issues:**
- Items older than 6 months → Archive or prioritize
- No acceptance criteria → Not ready for estimation
- No estimate on top 20 items → Refinement not happening
- All items same priority → Prioritization not done
- Many "In Progress" stories → WIP limit exceeded

### Red Flags in Metrics

**Velocity Issues:**
- Velocity swings >30% → Estimation inconsistency
- Velocity trending down →Technical debt or team capacity
- Committed >> Completed → Chronic over-commitment

**Cycle Time Issues:**
- Cycle time increasing → Process bottlenecks
- High variance in cycle time → Inconsistent story sizing
- Time in "In Review" >2 days → Review process bottleneck

**Sprint Scope Issues:**
- Scope changes >20% → Poor planning or unclear requirements
- Carry-over rate >15% → Over-commitment or blockers

### Recovering from Common Issues

**Over-Committed Sprint:**
1. Identify lowest-priority items
2. Move to next sprint immediately
3. Focus team on remaining work
4. Reduce commitment next sprint

**Blocked Work:**
1. Flag issue immediately
2. Assign owner to resolve blocker
3. Context-switch to other work
4. Update blocker daily until resolved

**Technical Debt Backlog:**
1. Allocate 20% of each sprint to tech debt
2. Create tech debt epics
3. Track and communicate impact
4. Prioritize highest-impact debt

**Estimation Drift:**
1. Review recent completed stories
2. Re-calibrate with reference stories
3. Run estimation workshop
4. Track actual vs estimated for learning

---

## Quick Reference Card

### Sprint Planning Checklist

**Pre-Planning:**
- [ ] Backlog refined (top 20 items)
- [ ] Stories estimated
- [ ] Dependencies identified
- [ ] Team capacity calculated
- [ ] Sprint goal drafted

**During Planning:**
- [ ] Review sprint goal
- [ ] Commit to stories (up to capacity)
- [ ] Break down stories to subtasks
- [ ] Identify risks and blockers
- [ ] Team agrees on commitment

**Post-Planning:**
- [ ] Sprint started in Jira
- [ ] Board updated
- [ ] Kickoff meeting scheduled

### Story Point Fibonacci Quick Guide

```
1  → Trivial (1-2 hours)
2  → Small (half day)
3  → Medium-small (1 day)
5  → Medium (2-3 days)
8  → Large (3-5 days)
13 → Very large (1 week)
21 → Too large - SPLIT
```

### Essential Jira Scripts

```bash
# SPRINT MANAGEMENT
# Create sprint
python create_sprint.py --board 123 --name "Sprint 42" --start 2025-01-20 --end 2025-02-03

# Add issues to sprint
python move_to_sprint.py --sprint 456 --jql "project=PROJ AND status='To Do'"

# Start sprint
python manage_sprint.py --sprint 456 --start

# Close sprint
python manage_sprint.py --sprint 456 --close --move-incomplete-to 457

# EPIC MANAGEMENT
# Create epic
python create_epic.py --project PROJ --summary "Feature X" --epic-name "X"

# Add to epic
python add_to_epic.py --epic PROJ-100 --jql "project=PROJ AND labels=feature-x"

# View epic progress
python get_epic.py PROJ-100 --with-children

# ESTIMATION
# Estimate single issue
python estimate_issue.py PROJ-101 --points 5

# Bulk estimate
python estimate_issue.py --jql "sprint=456 AND type=Story" --points 3 --dry-run

# View estimates
python get_estimates.py --sprint 456 --group-by status

# BACKLOG MANAGEMENT
# View backlog
python get_backlog.py --board 123 --group-by epic

# Rank issues
python rank_issue.py PROJ-101 --top
python rank_issue.py PROJ-102 --before PROJ-101
```

### Essential JQL Queries

```jql
# My current sprint work
assignee = currentUser() AND sprint IN openSprints() AND status != Done

# Sprint health check
project = PROJ AND sprint IN openSprints()
AND (
  (status = "In Progress" AND updated <= -3d)
  OR (status = "To Do" AND "Story Points" IS EMPTY)
  OR ("Flagged" = Impediment)
)
ORDER BY priority DESC

# Unestimated backlog items
sprint IS EMPTY AND "Story Points" IS EMPTY AND type IN (Story, Task)
ORDER BY priority DESC

# Epic progress
"Epic Link" = PROJ-100 ORDER BY status ASC, rank ASC

# Release readiness
fixVersion = "v2.0" AND status NOT IN (Done, Closed)
ORDER BY priority DESC, epic ASC

# Stale items (cleanup candidates)
status NOT IN (Done, Closed) AND updated <= -90d
ORDER BY updated ASC

# Velocity tracking (last sprint)
sprint = "Sprint 42" AND status IN (Done, Closed)

# Items spilled from previous sprint
sprint WAS "Sprint 41" AND sprint = "Sprint 42"
```

### Keyboard Shortcuts (Jira Board)

| Key | Action |
|-----|--------|
| `c` | Create issue |
| `j/k` | Navigate issues |
| `o` | Open issue detail |
| `a` | Assign to me |
| `i` | Assign to someone |
| `l` | Add label |
| `m` | Add comment |
| `/` | Quick search |
| `n` | Next issue |
| `p` | Previous issue |
| `z` | Toggle detail view |

### Estimation Reference Stories

Keep 3-5 reference stories for each point value:

**Example Reference Set:**
- **1 point:** Update button text, fix typo
- **2 points:** Add form validation, update config
- **3 points:** Simple API endpoint, basic component
- **5 points:** Feature with tests, database change
- **8 points:** Complex feature, multiple integrations
- **13 points:** Major feature requiring research

### Team Capacity Calculator

```
Individual Capacity = Sprint Days × Daily Hours × Focus Factor

Example (2-week sprint):
- Sprint days: 10
- Daily hours: 6
- Focus factor: 0.75
= 10 × 6 × 0.75 = 45 hours

Team Capacity = Individual Capacity × Team Size
= 45 hours × 5 people = 225 hours

Story Point Capacity = Team Velocity × 0.8
= 20 points × 0.8 = 16 points
```

### Daily Standup Template

**Each team member answers:**
1. **Yesterday:** What did I complete?
2. **Today:** What will I work on?
3. **Blockers:** What's preventing progress?

**Time limit:** 15 minutes max, 1-2 minutes per person

### Sprint Retrospective Action Template

```markdown
## Action: [Specific, actionable item]

**Problem:** [Issue identified in retro]
**Owner:** [Team member name]
**Success Criteria:** [How we'll know it's working]
**Due:** [Next retro or specific date]

Example:
## Action: Add automated linting to CI pipeline

**Problem:** Code review delays due to style inconsistencies
**Owner:** Bob
**Success Criteria:** All PRs auto-check style, <5% need manual style feedback
**Due:** Sprint 43
```

---

## Sources & Further Reading

This guide synthesizes best practices from industry-leading Agile and Scrum resources:

**Atlassian Agile Guides:**
- [How to create and use sprints in Jira](https://www.atlassian.com/agile/tutorials/sprints)
- [Sprint Planning Best Practices](https://www.atlassian.com/agile/scrum/sprint-planning)
- [Backlog Refinement Guide](https://www.atlassian.com/agile/scrum/backlog-refinement)
- [Fibonacci Story Points](https://www.atlassian.com/agile/project-management/fibonacci-story-points)
- [Working with WIP limits for Kanban](https://www.atlassian.com/agile/kanban/wip-limits)

**Agile Estimation Resources:**
- [Fibonacci story points: A practical guide](https://blog.logrocket.com/product-management/fibonacci-story-points-guide/)
- [Agile Estimation Techniques: T-Shirt Sizing](https://www.easyagile.com/blog/agile-estimation-techniques)
- [Story Points vs. T-Shirt Sizing](https://agileseekers.com/blog/story-point-vs-thshirt-sizing)

**JIRA-Specific Best Practices:**
- [10 Jira Sprint Planning Best Practices](https://ones.com/blog/jira-sprint-planning-best-practices/)
- [5 Best Practices for Jira Backlog Refinement](https://www.ricksoft-inc.com/post/5-best-practices-for-effective-jira-backlog-refinement/)
- [Backlog Grooming Guide for Jira](https://titanapps.io/blog/jira-backlog-grooming-refinement/)

**Scrum with Kanban:**
- [Professional Scrum with Kanban - WIP Optimization](https://www.scrum.org/resources/blog/professional-scrum-kanban-psk-dont-just-limit-wip-optimize-it-post-1-3)
- [Limiting Work in Progress in Scrum](https://www.scrum.org/resources/blog/limiting-work-progress-wip-scrum-kanban-what-when-who-how)

---

*Last updated: December 2025*
*Version: 1.0*
*Maintained by: JIRA Agile Skill Team*
