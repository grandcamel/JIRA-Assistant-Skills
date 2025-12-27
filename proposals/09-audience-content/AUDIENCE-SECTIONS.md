# Who Is This For?

Choose your role to see relevant features, example commands, and time savings.

<details>
<summary><strong>Developers</strong> - CLI-native JIRA, never leave your terminal</summary>

## For Developers

**Stop context-switching to JIRA.**

You are in your IDE. You just fixed a bug. Now you need to update JIRA.

### The Old Way
1. Open browser
2. Navigate to JIRA
3. Search for issue
4. Update status
5. Log time
6. Add comment
7. Back to coding

*Time lost: ~2-3 minutes*

### The New Way
```bash
claude "Close PROJ-123 with 'Fixed null pointer in auth service', log 30 minutes"
```
*Time spent: 3 seconds, never left your terminal*

---

### Daily Workflow Commands

| Task | Command |
|------|---------|
| Check my work | `"What's assigned to me in the current sprint?"` |
| Start a task | `"Start progress on PROJ-123"` |
| Log time | `"Log 2 hours on PROJ-123: Implemented auth fix"` |
| Mark done | `"Close PROJ-123 with resolution Fixed"` |
| Create bug | `"Create high priority bug: Login fails on Safari with error 500"` |
| Quick update | `"Add comment to PROJ-123: PR ready for review"` |

---

### Git Integration

| Task | Command |
|------|---------|
| Get branch name | `"Generate branch name for PROJ-123"` |
| Parse commits | `"Find issue references in recent commits"` |
| Create PR description | `"Generate PR description for PROJ-123"` |
| Link work | `"What issues are mentioned in my uncommitted changes?"` |

---

### Developer Features

- **CLI-native** - Works in any terminal session, no browser windows needed
- **IDE agnostic** - VS Code, JetBrains, Vim, Emacs, whatever you use
- **Profile support** - Switch between dev/staging/prod JIRA instances with `--profile`
- **Git integration** - Generate branch names, parse commits for issue references
- **Batch operations** - Update multiple issues in one command
- **Offline-friendly** - Queue updates and sync when connected

---

### Advanced Developer Queries

```bash
# Find issues I touched recently
"Show issues I commented on in the last week"

# Check dependencies before starting work
"What blocks PROJ-123? Show the full blocker chain"

# Bulk update after a refactor
"Add label 'auth-refactor' to PROJ-100, PROJ-101, PROJ-102"

# Create linked issues
"Create subtask under PROJ-123: Write unit tests for auth service"

# Time tracking
"How much time have I logged this week?"
```

---

### Weekly Time Saved

| Activity | Traditional | With Claude | Savings |
|----------|-------------|-------------|---------|
| Issue updates (10/day) | 20 min | 1 min | 19 min |
| Time logging | 10 min | 30 sec | 9.5 min |
| Status checks | 15 min | 1 min | 14 min |
| Branch naming | 5 min | 10 sec | ~5 min |
| **Weekly Total** | | | **~45 min** |

---

### Why Developers Love It

1. **Never break flow** - Update JIRA without switching windows
2. **Natural language** - No JQL syntax to remember
3. **Fast** - Seconds instead of minutes
4. **Scriptable** - Integrate into your dev scripts and hooks
5. **Consistent** - Same interface across all JIRA instances

</details>

<details>
<summary><strong>Team Leads</strong> - Team visibility in seconds</summary>

## For Team Leads

**See your team's work without meetings.**

No more opening JIRA boards, clicking through filters, or scheduling status syncs. Get the information you need in seconds.

---

### Morning Check-in (60 Seconds)

Replace your 15-minute JIRA review with instant queries:

```bash
# Get the full picture
"Show sprint progress for Team Alpha"

# Find potential bottlenecks
"Who has the most work in progress?"

# Identify blockers early
"What's blocked and why?"

# Check for stale items
"Which issues haven't been updated in 3 days?"
```

---

### Sprint Planning Support

| Task | Command |
|------|---------|
| Find unestimated work | `"Show unestimated stories in backlog"` |
| Check capacity | `"Show current workload by team member"` |
| Move items to sprint | `"Move top 10 priority items to Sprint 42"` |
| Velocity check | `"What's the team velocity for last 3 sprints?"` |
| Scope validation | `"Total story points in Sprint 42 vs team capacity"` |

---

### Daily Management Commands

```bash
# Assignment management
"Reassign PROJ-123 from @alex to @jordan"

# Bulk operations
"Add 'needs-review' label to all In Review items for my team"

# Status checks
"Show all items that moved to Done yesterday"

# Priority management
"Show high priority items that aren't being worked on"
```

---

### Weekly Reporting

| Report | Command |
|--------|---------|
| Sprint status | `"Show sprint progress with completion percentage"` |
| Burndown | `"Generate burndown data for Sprint 42"` |
| Velocity trend | `"Show velocity trend for last 6 sprints"` |
| Bug metrics | `"Bug count by component this quarter"` |
| Export data | `"Export this sprint's completed work to CSV"` |

---

### Team Oversight Queries

```bash
# Workload distribution
"Show issue count per assignee in current sprint"

# Blocked work analysis
"List all blocked items with blocker details"

# Progress tracking
"What's the completion rate for each epic this sprint?"

# Risk identification
"Which items are past their due date?"
```

---

### Quick Actions

| Action | Command |
|--------|---------|
| Escalate | `"Set priority to Highest on PROJ-123"` |
| Reassign | `"Assign PROJ-123 to @teammate"` |
| Add watcher | `"Add me as watcher to all blockers in Sprint 42"` |
| Comment | `"Add comment to PROJ-123: Let's discuss in standup"` |
| Link | `"Link PROJ-123 blocks PROJ-456"` |

---

### Weekly Time Saved

| Activity | Traditional | With Claude | Savings |
|----------|-------------|-------------|---------|
| Morning JIRA review | 15 min/day | 1 min | 70 min/week |
| Stakeholder reports | 30 min/week | 2 min | 28 min |
| Sprint planning prep | 1 hour | 10 min | 50 min |
| Ad-hoc status checks | 20 min/day | 2 min | 90 min/week |
| **Weekly Total** | | | **~4 hours** |

---

### Why Team Leads Love It

1. **Instant visibility** - No clicking through boards and filters
2. **Proactive blocking detection** - Find issues before they derail the sprint
3. **Easy exports** - Stakeholder reports without manual data gathering
4. **Batch operations** - Reassign, relabel, reprioritize in seconds
5. **Time recovery** - Spend less time in JIRA, more time leading

</details>

<details>
<summary><strong>Scrum Masters</strong> - Run ceremonies, not admin</summary>

## For Scrum Masters

**Run ceremonies, not JIRA sessions.**

Focus on facilitation and team dynamics instead of clicking through JIRA boards. Get instant agile metrics and ceremony support.

---

### Sprint Planning (Before the Meeting)

```bash
# Prepare the backlog
"Show prioritized backlog with estimates"

# Check for gaps
"List stories without estimates in the backlog"

# Identify dependencies
"What dependencies exist in top 20 backlog items?"

# Capacity check
"Show team availability for next sprint"

# Create the sprint
"Create Sprint 43 starting next Monday for 2 weeks"
```

---

### Daily Standup (During)

| Standup Question | Command |
|------------------|---------|
| What happened yesterday? | `"Show yesterday's progress for Sprint 43"` |
| What's blocked? | `"What's blocked right now?"` |
| Who needs follow-up? | `"Who has items without updates > 24 hours?"` |
| Sprint health | `"Show current sprint burndown"` |
| Scope changes | `"What was added to Sprint 43 since it started?"` |

---

### Sprint Review (After the Sprint)

```bash
# What shipped?
"Show completed items in Sprint 43 by epic"

# Prepare the demo list
"List completed features with descriptions for Sprint 43"

# Stakeholder report
"Export sprint results for stakeholder presentation"

# Carryover analysis
"What carried over from Sprint 43?"
```

---

### Sprint Retrospective (Analysis)

| Retro Topic | Command |
|-------------|---------|
| Rework analysis | `"Show items that were reopened in Sprint 43"` |
| Review bottleneck | `"Average time in 'In Review' status for Sprint 43?"` |
| Scope changes | `"Which issues had scope changes during Sprint 43?"` |
| Blocked time | `"Total time issues spent blocked in Sprint 43"` |
| Bug injection | `"Bugs created during Sprint 43 vs bugs resolved"` |

---

### Agile Metrics Dashboard

| Metric | Command |
|--------|---------|
| Velocity | `"Show velocity for last 5 sprints"` |
| Burndown | `"Sprint 43 burndown data"` |
| Cycle time | `"Average time from In Progress to Done"` |
| Lead time | `"Average time from creation to Done"` |
| Blocked rate | `"Percentage of issues blocked per sprint"` |
| Scope creep | `"Story points added after sprint start"` |
| Carryover rate | `"What percentage carried over last 3 sprints?"` |

---

### Ceremony Preparation Checklist

```bash
# Sprint Planning Prep
"Show unestimated stories"
"Show backlog sorted by priority"
"Team velocity average for last 3 sprints?"

# Standup Prep
"Blockers in current sprint?"
"Items in review > 24 hours?"

# Review Prep
"Completed items this sprint by epic"
"Sprint goal achievement status"

# Retro Prep
"Items reopened this sprint"
"Average cycle time compared to last sprint"
```

---

### Quick Actions

| Action | Command |
|--------|---------|
| Move to sprint | `"Add PROJ-123 to Sprint 43"` |
| Remove from sprint | `"Remove PROJ-123 from Sprint 43"` |
| Reorder backlog | `"Move PROJ-123 above PROJ-124 in backlog"` |
| Start sprint | `"Start Sprint 43"` |
| Close sprint | `"Close Sprint 43"` |
| Create epic | `"Create epic: User Authentication Redesign"` |

---

### Time Saved Per Sprint

| Activity | Traditional | With Claude | Savings |
|----------|-------------|-------------|---------|
| Sprint planning prep | 2 hours | 20 min | 100 min |
| Daily standup data | 10 min/day | 1 min | 45 min |
| Sprint review prep | 1 hour | 10 min | 50 min |
| Retrospective data | 45 min | 5 min | 40 min |
| Metric gathering | 30 min | 2 min | 28 min |
| **Per Sprint Total** | | | **~4.5 hours** |

---

### Why Scrum Masters Love It

1. **Ceremony focus** - Facilitate discussions, not JIRA navigation
2. **Instant metrics** - Velocity, burndown, cycle time on demand
3. **Data-driven retros** - Facts about the sprint, not just feelings
4. **Less admin** - Sprint creation and management in seconds
5. **Consistent process** - Same queries, predictable results

</details>

<details>
<summary><strong>Product Managers</strong> - Self-serve product data</summary>

## For Product Managers

**Focus on product, not project administration.**

Get instant answers about roadmap status, backlog health, and release progress without waiting for engineering updates or scheduling status meetings.

---

### Roadmap Management

```bash
# Epic status at a glance
"Show all epics for Q1 with completion percentage"

# Feature delivery tracking
"What features shipped last month?"

# Roadmap gaps
"Show epics without target release date"

# Progress by theme
"Show progress on the Authentication initiative"

# Create new initiatives
"Create epic: User Authentication Redesign with Q2 target"
```

---

### Backlog Grooming

| Task | Command |
|------|---------|
| Missing details | `"Show stories without acceptance criteria"` |
| Stale items | `"What's been in backlog > 90 days?"` |
| Prioritization | `"Move FEAT-123 above FEAT-124 in backlog"` |
| Estimation gaps | `"Show unestimated items in backlog"` |
| Dependency check | `"What depends on FEAT-456?"` |

---

### Release Planning

```bash
# Release scope
"Show items targeted for v2.1 release"

# Release readiness
"What's left before we can release v2.1?"

# Risk assessment
"Show blockers for v2.1 release items"

# Release notes prep
"List completed features since v2.0 with descriptions"

# Version management
"Create version v2.2 with target date March 15"
```

---

### Stakeholder Communication

| Need | Command |
|------|---------|
| Release notes | `"Export release notes for v2.1"` |
| Sprint summary | `"Summarize what's shipping this sprint"` |
| Bug metrics | `"Show bug fix rate for last quarter"` |
| Feature progress | `"Progress on the Search Improvements epic"` |
| Team capacity | `"What can we realistically ship by end of quarter?"` |

---

### Customer-Focused Queries

```bash
# Customer requests
"Show all feature requests tagged 'customer-requested'"

# Customer-facing bugs
"List bugs affecting customers, sorted by priority"

# SLA tracking
"Show customer-reported bugs open > 5 days"

# Customer impact
"How many issues are tagged with customer 'Acme Corp'?"
```

---

### Metrics and Reporting

| Metric | Command |
|--------|---------|
| Feature velocity | `"Features shipped per month, last 6 months"` |
| Bug burn rate | `"Bugs resolved vs bugs created this quarter"` |
| Backlog growth | `"Backlog size trend over last 3 months"` |
| Cycle time | `"Average time from Ready to Done for features"` |
| Epic progress | `"Completion percentage for all active epics"` |

---

### Quick Actions

| Action | Command |
|--------|---------|
| Prioritize | `"Set priority to Highest on FEAT-123"` |
| Add to release | `"Add FEAT-123 to v2.1 release"` |
| Create feature | `"Create feature: Dark mode support"` |
| Link items | `"Link FEAT-123 as dependent on FEAT-100"` |
| Add label | `"Add 'customer-requested' label to FEAT-123"` |

---

### Common PM Questions, Answered Instantly

```bash
# "What's shipping?"
"Show items targeted for v2.1 release"

# "What's the status of X?"
"Where is FEAT-456 in the workflow?"

# "When will it be done?"
"Show progress on the Authentication epic with estimated completion"

# "What's blocking us?"
"Show all blockers for items in the current sprint"

# "What do customers want?"
"Show feature requests sorted by customer impact"
```

---

### Weekly Time Saved

| Activity | Traditional | With Claude | Savings |
|----------|-------------|-------------|---------|
| Status gathering | 30 min/day | 2 min | 2+ hours/week |
| Backlog review | 1 hour/week | 10 min | 50 min |
| Stakeholder reports | 2 hours/week | 15 min | 105 min |
| Release planning | 1 hour/week | 10 min | 50 min |
| **Weekly Total** | | | **~5 hours** |

---

### Why Product Managers Love It

1. **Instant answers** - No waiting for engineering updates
2. **Self-serve data** - Export anytime, any format
3. **Backlog control** - Prioritize without developer help
4. **Release visibility** - Know exactly what's shipping and when
5. **Customer focus** - Track customer impact across issues

</details>

<details>
<summary><strong>IT/Ops</strong> - Incident response accelerated</summary>

## For IT/Ops Teams

**Incident response without the JIRA dance.**

When production is down, every second counts. Create incidents, track SLAs, and manage service requests without clicking through forms.

---

### Incident Creation (10 Seconds)

```bash
# Production is down - create incident immediately
"Create urgent incident: Production database unreachable"
```

This creates:
- P1/Highest priority issue
- Proper incident type and labels
- Assigns to on-call (if configured)
- Timestamps for SLA tracking

---

### Incident Management

| Task | Command |
|------|---------|
| View all incidents | `"Show all open incidents by severity"` |
| Link root cause | `"Link INCIDENT-123 to root cause INFRA-456"` |
| Escalate | `"Escalate INCIDENT-123 to @platform-team"` |
| Update status | `"Add comment to INCIDENT-123: Identified root cause - memory leak"` |
| Resolve | `"Resolve INCIDENT-123 with 'Restarted service, added memory monitoring'"` |

---

### Service Desk (JSM) Operations

```bash
# Queue management
"Show my queue sorted by SLA breach time"

# Quick resolution
"Resolve REQ-789 with 'Password reset completed'"

# Customer communication
"Add customer comment to REQ-789: 'Your account has been unlocked'"

# Participant management
"Add @supervisor as watcher on REQ-789"
```

---

### SLA Monitoring

| SLA Check | Command |
|-----------|---------|
| Breaching soon | `"Which requests are about to breach SLA?"` |
| Already breached | `"Show requests with breached SLA"` |
| By time remaining | `"Show queue sorted by time to SLA breach"` |
| SLA metrics | `"Show SLA achievement rate this week"` |
| By request type | `"SLA status for all Password Reset requests"` |

---

### Post-Incident

```bash
# Create follow-up tasks
"Create follow-up task: Update runbook for DB failover"

# Document timeline
"Export incident timeline for INCIDENT-123 for postmortem"

# Pattern analysis
"Show related incidents in last 30 days"

# Preventive actions
"Create story: Implement automated failover for production DB"
```

---

### Queue Management

| Task | Command |
|------|---------|
| My queue | `"Show my pending requests"` |
| Unassigned | `"Show unassigned requests in IT Support queue"` |
| Overdue | `"Show overdue requests in my queue"` |
| By type | `"Show all access requests pending approval"` |
| Assignment | `"Assign REQ-456 to @helpdesk-agent"` |

---

### Common IT/Ops Queries

```bash
# Incident tracking
"Show all P1 incidents created this month"

# Change management
"Show approved change requests scheduled for this week"

# Asset-related issues
"Show all issues linked to the production-db-01 asset"

# Knowledge base
"Search KB for 'VPN connection issues'"

# Customer history
"Show all requests from customer 'john@company.com'"
```

---

### Bulk Operations

```bash
# Close multiple resolved tickets
"Close all requests in Resolved status older than 7 days"

# Reassign during shift change
"Reassign @agent1's queue to @agent2"

# Add labels for tracking
"Add 'security-review' label to all requests mentioning 'password'"

# Priority adjustment
"Set priority to High on all requests mentioning 'VPN'"
```

---

### JSM-Specific Features

| Feature | Command |
|---------|---------|
| Request types | `"Show available request types for IT Support desk"` |
| Customer add | `"Add customer jane@company.com to project"` |
| Approval | `"Approve REQ-456"` |
| Portal link | `"Generate portal link for REQ-456"` |
| Organization | `"Show all requests from Acme Corp organization"` |

---

### Time Saved Per Incident

| Activity | Traditional | With Claude | Savings |
|----------|-------------|-------------|---------|
| Incident creation | 2-3 min | 10 sec | 2.5 min |
| Status updates | 1 min each | 5 sec | 55 sec/update |
| Escalation | 2 min | 10 sec | 1.8 min |
| Post-incident docs | 30 min | 5 min | 25 min |
| Queue review | 10 min | 1 min | 9 min |

---

### Why IT/Ops Teams Love It

1. **Speed during incidents** - Fastest possible issue creation
2. **SLA visibility** - Know what's at risk before it breaches
3. **JSM integration** - Full service desk capabilities
4. **Bulk operations** - Manage queues efficiently
5. **Pattern detection** - Identify recurring issues quickly
6. **Audit trail** - All actions logged for compliance

</details>

---

## Quick Comparison

| Audience | Primary Benefit | Key Feature | Time Saved |
|----------|-----------------|-------------|------------|
| Developers | Never leave terminal | Git integration | ~45 min/week |
| Team Leads | Team visibility | Instant reports | ~4 hours/week |
| Scrum Masters | Ceremony efficiency | Agile metrics | ~4.5 hours/sprint |
| Product Managers | Self-serve data | Roadmap queries | ~5 hours/week |
| IT/Ops | Incident speed | JSM + SLA tracking | Minutes per incident |

---

## Getting Started

Regardless of your role, getting started is the same:

1. **Install Claude Code** - Follow the [installation guide](../README.md#installation)
2. **Configure JIRA credentials** - Set up your API token and site URL
3. **Start asking questions** - Use natural language for any JIRA task

No special configuration needed for your role - just start with the queries that matter most to you.
