# JIRA Skills Decision Tree

Quick reference for routing requests to the correct skill.

## Quick Decision Flowchart

```
START: What does the user want to do?
     |
     v
+--------------------+
| Is it about        |
| MULTIPLE issues?   |---YES---> jira-bulk (if >10 issues)
+--------------------+           jira-search (if finding/querying)
     |
     NO
     v
+--------------------+
| Keywords present?  |
| (see table below)  |---YES---> Route to matching skill
+--------------------+
     |
     NO
     v
+--------------------+
| Issue key          |
| mentioned?         |---YES---> Is it workflow/status change?
+--------------------+              |
     |                              YES --> jira-lifecycle
     NO                             NO  --> jira-issue
     v
+--------------------+
| Project-level      |
| operation?         |---YES---> jira-admin
+--------------------+
     |
     NO
     v
ASK FOR CLARIFICATION
```

## Keyword Routing Table

| Keywords | Primary Skill | Also Consider |
|----------|---------------|---------------|
| **Issue Operations** |||
| show, view, display, get, see, details | jira-issue | - |
| create, new bug/task/story | jira-issue | jira-agile (if epic/subtask) |
| update, edit, modify fields | jira-issue | jira-lifecycle (if status) |
| delete issue | jira-issue | jira-bulk (if multiple) |
| **Search & Discovery** |||
| search, find, query, JQL, filter | jira-search | - |
| export, CSV, JSON | jira-search | jira-time (if timesheet) |
| **Workflow & Status** |||
| transition, move to, change status | jira-lifecycle | jira-bulk (if many) |
| assign, assignee, unassign | jira-lifecycle | jira-bulk (if many) |
| resolve, close, done | jira-lifecycle | - |
| reopen | jira-lifecycle | - |
| version, release, fixVersion | jira-lifecycle | - |
| component | jira-lifecycle | - |
| **Agile & Scrum** |||
| sprint, backlog, board | jira-agile | - |
| epic, create epic, epic link | jira-agile | - |
| subtask, sub-task, child | jira-agile | - |
| story points, estimate points | jira-agile | - |
| velocity | jira-agile | - |
| rank, prioritize backlog | jira-agile | - |
| **Collaboration** |||
| comment, add comment | jira-collaborate | jira-jsm (if request) |
| attachment, upload, file | jira-collaborate | - |
| watcher, watch, notify | jira-collaborate | - |
| activity, changelog, history | jira-collaborate | - |
| **Relationships** |||
| link issues, blocks, blocked by | jira-relationships | - |
| relates to, duplicates | jira-relationships | - |
| dependency, blocker chain | jira-relationships | - |
| clone issue | jira-relationships | jira-bulk (if many) |
| **Time Tracking** |||
| log time, worklog, hours | jira-time | - |
| time spent, time remaining | jira-time | - |
| estimate, original estimate | jira-time | jira-agile (if story points) |
| timesheet, time report | jira-time | - |
| **Service Management** |||
| service desk, portal | jira-jsm | - |
| SLA, breach, response time | jira-jsm | - |
| customer, organization | jira-jsm | - |
| request, incident, change | jira-jsm | jira-issue (if standard) |
| approval, approve, decline | jira-jsm | - |
| knowledge base, KB, article | jira-jsm | - |
| asset, CMDB | jira-jsm | - |
| queue | jira-jsm | - |
| **Developer Integration** |||
| branch name, git branch | jira-dev | - |
| commit, parse commits | jira-dev | - |
| PR, pull request, link PR | jira-dev | - |
| development panel | jira-dev | - |
| **Field Configuration** |||
| custom field, field ID | jira-fields | - |
| agile fields, story points field | jira-fields | - |
| screen, field configuration | jira-fields | jira-admin (if scheme) |
| **Operations** |||
| cache, warm cache, clear cache | jira-ops | - |
| project discovery | jira-ops | - |
| **Administration** |||
| project settings, create project | jira-admin | - |
| permission, permission scheme | jira-admin | - |
| notification scheme | jira-admin | - |
| automation rule | jira-admin | - |
| user, group, membership | jira-admin | - |
| issue type, issue type scheme | jira-admin | - |
| workflow, workflow scheme | jira-admin | - |
| **Bulk Operations** |||
| bulk, mass, batch | jira-bulk | - |
| update all, transition all | jira-bulk | - |
| delete multiple | jira-bulk | - |

## Operation Verb Mapping

| Verb | Read? | Risk Level | Typical Skills |
|------|-------|------------|----------------|
| get, list, show, view, display | Yes | `-` | Any |
| search, find, query, export | Yes | `-` | jira-search |
| create, add, new | No | `-` to `!` | jira-issue, jira-agile |
| update, edit, modify, set | No | `!` | jira-issue, jira-lifecycle |
| transition, move, assign | No | `!` | jira-lifecycle |
| link, unlink | No | `-` to `!` | jira-relationships |
| delete, remove | No | `!!` to `!!!` | jira-issue, jira-bulk |
| bulk * | No | `!!` to `!!!` | jira-bulk |

## Resource Type Signals

| Resource Mentioned | Likely Skill |
|-------------------|--------------|
| Issue key (PROJ-123) | jira-issue or jira-lifecycle |
| JQL query | jira-search |
| Sprint name/ID | jira-agile |
| Epic key | jira-agile |
| Service desk ID | jira-jsm |
| Request key (SD-123) | jira-jsm |
| Board ID | jira-agile |
| Custom field ID | jira-fields |
| Permission scheme | jira-admin |
| Workflow name | jira-admin |
| Worklog ID | jira-time |
| Filter ID | jira-search |

## Ambiguous Request Handling

When a request could match multiple skills, ask for clarification:

### "Show me the sprint"

**Could mean:**
1. Sprint metadata (dates, goal, capacity) -> jira-agile
2. Issues in the sprint -> jira-search

**Ask:** "Do you want sprint details or the issues in the sprint?"

### "Update the issue"

**Could mean:**
1. Change field values -> jira-issue
2. Transition status -> jira-lifecycle
3. Update multiple issues -> jira-bulk

**Ask:** "What would you like to update - fields, status, or multiple issues?"

### "Create an issue in the epic"

**Context determines:**
- Epic explicitly mentioned -> jira-agile (with --epic flag)
- Just creating an issue -> jira-issue

### "Close all bugs in the sprint"

**Route:** jira-bulk (multiple issues + transition)

**Workflow:**
1. First use jira-search to find issues
2. Use jira-bulk transition with --dry-run
3. Confirm, then execute

### "Log time for the team"

**Could mean:**
1. Log time to multiple issues -> jira-time bulk-log
2. Generate team time report -> jira-time report

**Ask:** "Do you want to log time entries or generate a report?"

## Pronoun Resolution

When user says "it", "that issue", or "them":

| Context | Resolution |
|---------|------------|
| 1 issue in last 3 messages | Use that issue |
| Multiple issues mentioned | Ask: "Which issue - X or Y?" |
| Search just returned results | "them" = the results |
| Just created an issue | "it" = the new issue |
| No recent issue context | Ask: "Which issue?" |

## Context Expiration

After 5+ messages or 5+ minutes since last reference:
- Re-confirm rather than assume
- Ask: "Do you mean [ISSUE-KEY] from earlier?"

## Negative Triggers (What Skills Do NOT Handle)

| Skill | Does NOT Handle | Route To |
|-------|-----------------|----------|
| jira-issue | Bulk ops, transitions, comments | jira-bulk, jira-lifecycle, jira-collaborate |
| jira-search | Single issue lookup, modifications | jira-issue, jira-bulk |
| jira-lifecycle | Field updates, bulk transitions | jira-issue, jira-bulk |
| jira-agile | Issue CRUD, JQL, time | jira-issue, jira-search, jira-time |
| jira-bulk | Single issue ops, sprint mgmt | jira-issue, jira-agile |
| jira-collaborate | Field updates, bulk comments | jira-issue, jira-bulk |
| jira-relationships | Field updates, epic linking | jira-issue, jira-agile |
| jira-time | SLA tracking, date searches | jira-jsm, jira-search |
| jira-jsm | Standard issues, non-SD searches | jira-issue, jira-search |
| jira-dev | Field updates, JQL | jira-issue, jira-search |
| jira-fields | Field value updates | jira-issue |
| jira-ops | Project config, issue ops | jira-admin, jira-issue |
| jira-admin | Issue CRUD, bulk ops | jira-issue, jira-bulk |
