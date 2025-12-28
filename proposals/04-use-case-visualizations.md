# Use Case Visualizations

## Overview
Use case visualizations demonstrate real-world scenarios where JIRA Assistant Skills solve problems. They help potential users see themselves using the tool.

---

## 1. Workflow Diagrams

### Option 4A: Developer Daily Workflow
**Concept:** Show a developer's typical day with JIRA Assistant

```mermaid
flowchart TD
    START[☀️ Start of Day] --> STANDUP["What's on my plate today?"]
    STANDUP --> |jira-search| LIST[📋 Get assigned issues]

    LIST --> WORK[Start working]
    WORK --> PROGRESS["Start progress on PROJ-123"]
    PROGRESS --> |jira-lifecycle| STATUS[✅ Status updated]

    STATUS --> CODE[Write code...]
    CODE --> DONE["Mark PROJ-123 as done"]
    DONE --> |jira-lifecycle| RESOLVED[✅ Issue resolved]

    RESOLVED --> LOG["Log 4 hours on PROJ-123"]
    LOG --> |jira-time| LOGGED[⏱️ Time logged]

    LOGGED --> EOD[🌙 End of Day]
```

### Option 4B: Sprint Planning Workflow
**Concept:** Scrum Master's sprint planning session

```mermaid
sequenceDiagram
    participant SM as Scrum Master
    participant JA as JIRA Assistant
    participant JIRA as JIRA Cloud

    SM->>JA: "Create sprint 'Sprint 42'<br/>starting Monday"
    JA->>JIRA: Create Sprint
    JIRA-->>JA: Sprint 42 created
    JA-->>SM: ✅ Sprint 42 ready

    SM->>JA: "Move top 10 backlog<br/>stories to Sprint 42"
    JA->>JIRA: Get backlog, Move issues
    JIRA-->>JA: Issues moved
    JA-->>SM: ✅ 10 stories in sprint

    SM->>JA: "Start Sprint 42"
    JA->>JIRA: Activate sprint
    JIRA-->>JA: Sprint active
    JA-->>SM: ✅ Sprint 42 is live!

    Note over SM,JIRA: 3 commands, 2 minutes
```

### Option 4C: Incident Response Flow
**Concept:** IT/Ops handling a production incident

```mermaid
flowchart LR
    ALERT[🚨 Alert!] --> CREATE["Create urgent bug:<br/>'Production down'"]
    CREATE --> |jira-issue| BUG[INCIDENT-999]

    BUG --> ASSIGN["Assign to on-call"]
    ASSIGN --> |jira-lifecycle| ASSIGNED[👤 Assigned]

    ASSIGNED --> INVESTIGATE[Investigate...]
    INVESTIGATE --> LINK["Link to root cause<br/>INFRA-456"]
    LINK --> |jira-relationships| LINKED[🔗 Linked]

    LINKED --> FIX[Apply fix...]
    FIX --> RESOLVE["Resolve with<br/>'Hotfix deployed'"]
    RESOLVE --> |jira-lifecycle| DONE[✅ Resolved]

    DONE --> POSTMORTEM["Create follow-up<br/>task for postmortem"]
    POSTMORTEM --> |jira-issue| TASK[INCIDENT-1000]
```

### Option 4D: Release Preparation
**Concept:** Release manager checking readiness

```mermaid
flowchart TD
    START[📦 Release Check] --> BLOCKERS["What's blocking<br/>the v2.0 release?"]
    BLOCKERS --> |jira-search| FOUND[Found 3 blockers]

    FOUND --> ANALYZE["Show blocker<br/>dependencies"]
    ANALYZE --> |jira-relationships| CHAIN[Dependency chain]

    CHAIN --> ESCALATE["Escalate PROJ-789<br/>to @team-lead"]
    ESCALATE --> |jira-collaborate| NOTIFIED[👤 Team notified]

    NOTIFIED --> BULK["Bulk transition all<br/>ready issues to Done"]
    BULK --> |jira-bulk| CLOSED[47 issues closed]

    CLOSED --> REPORT["Export release notes"]
    REPORT --> |jira-search| CSV[📄 CSV exported]
```

---

## 2. Role-Based Scenarios

### Option 4E: Developer Journey Map
**Concept:** Visual timeline of developer interactions

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DEVELOPER DAY WITH JIRA ASSISTANT                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  9:00 AM          10:30 AM         2:00 PM          4:30 PM    5:00 PM  │
│     │                │                │                │          │      │
│     ▼                ▼                ▼                ▼          ▼      │
│  ┌──────┐        ┌──────┐        ┌──────┐        ┌──────┐    ┌──────┐   │
│  │What's│        │Create│        │Start │        │ Log  │    │What  │   │
│  │my    │        │spike │        │prog  │        │ 3hrs │    │did I │   │
│  │work? │        │ticket│        │PROJ- │        │ on   │    │finish│   │
│  │      │        │      │        │ 456  │        │PROJ- │    │today?│   │
│  └──┬───┘        └──┬───┘        └──┬───┘        │ 456  │    └──┬───┘   │
│     │               │               │            └──┬───┘       │       │
│     ▼               ▼               ▼               ▼           ▼       │
│  jira-search    jira-issue    jira-lifecycle    jira-time   jira-search │
│                                                                          │
│  [5 issues]     [PROJ-789]    [In Progress]     [Logged]    [3 done]    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Option 4F: Team Lead Dashboard View
**Concept:** What a team lead asks throughout the week

```mermaid
mindmap
  root((Team Lead<br/>Weekly))
    Monday
      Sprint health?
      Any blockers?
      Who's overloaded?
    Wednesday
      Stories at risk?
      Need to reprioritize?
      Velocity check
    Friday
      What shipped?
      Carry-over items?
      Retrospective prep
```

### Option 4G: Product Manager Queries
**Concept:** PM's information needs

| Time | Question | Skill | Result |
|------|----------|-------|--------|
| Planning | "Show all stories without estimates" | jira-search | Refinement list |
| Prioritization | "Move FEAT-123 to top of backlog" | jira-agile | Backlog reordered |
| Stakeholder | "What shipped in v2.1?" | jira-search | Release notes |
| Roadmap | "Create epic for Q2 initiative" | jira-agile | Epic created |
| Metrics | "How many bugs closed this month?" | jira-search | Count + export |

---

## 3. Capability Showcase

### Option 4H: Feature Grid
**Concept:** Visual matrix of what's possible

```
┌────────────────────────────────────────────────────────────────────────┐
│                    WHAT CAN YOU DO WITH JIRA ASSISTANT?                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   CREATE    │  │   SEARCH    │  │   UPDATE    │  │   ANALYZE   │   │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤  ├─────────────┤   │
│  │ Bugs        │  │ By JQL      │  │ Status      │  │ Blockers    │   │
│  │ Stories     │  │ By filter   │  │ Assignee    │  │ Dependencies│   │
│  │ Tasks       │  │ Natural     │  │ Priority    │  │ Time spent  │   │
│  │ Epics       │  │ language    │  │ Sprint      │  │ Velocity    │   │
│  │ Subtasks    │  │             │  │ Labels      │  │ Workload    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │    LINK     │  │    TIME     │  │    BULK     │  │   EXPORT    │   │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤  ├─────────────┤   │
│  │ Blocks      │  │ Log work    │  │ Transitions │  │ CSV         │   │
│  │ Relates     │  │ Estimates   │  │ Assignments │  │ JSON        │   │
│  │ Duplicates  │  │ Reports     │  │ Priorities  │  │ Formatted   │   │
│  │ Clones      │  │ Timesheet   │  │ Clone sets  │  │ tables      │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### Option 4I: Command → Result Flow
**Concept:** Show transformation from natural language to outcome

```mermaid
flowchart LR
    subgraph Input["💬 You Say"]
        Q1["Show my high<br/>priority bugs"]
        Q2["Create a story<br/>for login redesign"]
        Q3["What's blocking<br/>the release?"]
    end

    subgraph Processing["🤖 Claude Understands"]
        P1["JQL: assignee=currentUser()<br/>AND type=Bug<br/>AND priority>=High"]
        P2["create_issue.py<br/>--type Story<br/>--summary '...'"]
        P3["Search linked blockers<br/>Traverse dependency tree"]
    end

    subgraph Output["✅ You Get"]
        R1["📋 List of 7 bugs<br/>with details"]
        R2["🎫 PROJ-456 created<br/>ready to refine"]
        R3["🔍 3 blockers found<br/>with recommendations"]
    end

    Q1 --> P1 --> R1
    Q2 --> P2 --> R2
    Q3 --> P3 --> R3
```

---

## 4. Problem-Solution Stories

### Option 4J: Before/After Narrative
**Concept:** Story format showing transformation

```
┌─────────────────────────────────────────────────────────────────────────┐
│ THE MONDAY MORNING STANDUP PROBLEM                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ BEFORE: Sarah's Monday Routine (15 minutes)                              │
│ ─────────────────────────────────────────────                            │
│ 1. Open JIRA                                                  2 min      │
│ 2. Navigate to board                                          1 min      │
│ 3. Filter by assignee (can never remember how)                3 min      │
│ 4. Check each issue status                                    5 min      │
│ 5. Look up sprint velocity (where is that again?)             2 min      │
│ 6. Copy issues to notes for standup                           2 min      │
│                                                                          │
│ AFTER: Sarah's Monday with JIRA Assistant (45 seconds)                   │
│ ──────────────────────────────────────────────────────                   │
│ Sarah: "What's my sprint work and yesterday's progress?"                 │
│                                                                          │
│ Claude: Here's your Sprint 42 status:                                    │
│         • In Progress: PROJ-123, PROJ-124                                │
│         • Completed yesterday: PROJ-120, PROJ-121                        │
│         • Remaining: 13 story points                                     │
│         • Sprint velocity: on track                                      │
│                                                                          │
│ TIME SAVED: 14 minutes per standup × 50 standups/year = 12 hours/year   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Option 4K: Pain Point Resolution
**Concept:** Map common frustrations to solutions

| Pain Point | Old Way | New Way | Skill |
|------------|---------|---------|-------|
| "JQL is confusing" | Google syntax, trial & error | "Show bugs from last week" | jira-search |
| "Status updates are tedious" | Click, click, click, click | "Move PROJ-123 to Done" | jira-lifecycle |
| "Sprint setup takes forever" | Manual drag & drop | "Create sprint with top 10 stories" | jira-agile |
| "Time logging forgotten" | End-of-week scramble | "Log 2 hours on PROJ-123" | jira-time |
| "Blockers hidden" | Manual dependency check | "What's blocking the release?" | jira-relationships |

---

## 5. Integration Scenarios

### Option 4L: Development Pipeline
**Concept:** Show integration with developer tools

```mermaid
flowchart LR
    subgraph IDE["VS Code"]
        CODE[Write Code]
        CC[Claude Code]
    end

    subgraph JIRA_FLOW["JIRA Flow"]
        BRANCH["Get branch name<br/>for PROJ-123"]
        COMMIT["Parse commit<br/>for issue refs"]
        PR["Generate PR<br/>description"]
    end

    subgraph Git["Git/GitHub"]
        GIT_BRANCH[feature/PROJ-123-fix]
        GIT_COMMIT[Commit message]
        GIT_PR[Pull Request]
    end

    CODE --> CC
    CC --> BRANCH --> GIT_BRANCH
    CC --> COMMIT --> GIT_COMMIT
    CC --> PR --> GIT_PR
```

### Option 4M: Service Desk Workflow
**Concept:** IT support ticket handling

```mermaid
sequenceDiagram
    participant C as Customer
    participant SD as Service Desk
    participant JA as JIRA Assistant
    participant IT as IT Team

    C->>SD: Submit request
    SD->>JA: "Show new requests<br/>in queue"
    JA-->>SD: 5 pending requests

    SD->>JA: "Assign REQ-100<br/>to IT-Team"
    JA-->>SD: ✅ Assigned

    IT->>JA: "Show my queue<br/>sorted by SLA"
    JA-->>IT: Priority list with<br/>SLA status

    IT->>JA: "Resolve REQ-100<br/>with 'Password reset'"
    JA-->>IT: ✅ Resolved
    JA-->>C: Auto-notification sent
```

---

## 6. Decision Flowcharts

### Option 4N: "Which Skill Do I Need?"
**Concept:** Help users find the right skill

```mermaid
flowchart TD
    START[What do you want to do?] --> Q1{Create or<br/>modify issues?}

    Q1 --> |Create| Q2{What type?}
    Q1 --> |Modify| Q3{What change?}
    Q1 --> |Find/Search| SEARCH[jira-search]

    Q2 --> |Bug/Story/Task| ISSUE[jira-issue]
    Q2 --> |Epic/Sprint| AGILE[jira-agile]
    Q2 --> |Service Request| JSM[jira-jsm]

    Q3 --> |Status/Workflow| LIFE[jira-lifecycle]
    Q3 --> |Add comment| COLLAB[jira-collaborate]
    Q3 --> |Log time| TIME[jira-time]
    Q3 --> |Link issues| REL[jira-relationships]
    Q3 --> |Bulk change| BULK[jira-bulk]
```

---

## Recommendation

**For README:**
1. **Primary:** Option 4I (Command → Result Flow) - Shows value quickly
2. **Secondary:** Option 4J (Before/After Narrative) - Emotional resonance

**For Documentation:**
1. Option 4A-4D (Workflow Diagrams) - Per-role sections
2. Option 4N (Decision Flowchart) - Skill selection guide

**For Marketing:**
1. Option 4K (Pain Point Resolution) - Feature comparison
2. Option 4E (Developer Journey Map) - Day-in-the-life story
