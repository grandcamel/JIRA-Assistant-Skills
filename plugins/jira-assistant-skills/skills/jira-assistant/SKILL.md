---
name: "jira-assistant"
description: "JIRA automation hub routing to 14 specialized skills for any JIRA task: issues, workflows, agile, search, time tracking, service management, and more."
version: "2.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# JIRA Assistant

Complete JIRA automation hub that routes to 14 specialized skills for comprehensive JIRA automation.

## Quick Start

Tell me what you need in natural language. I'll route to the appropriate specialized skill and execute your request.

**Examples:**
- "Create a bug in TES for login issues and assign to me"
- "Move PROJ-123 to In Progress"
- "Find all open bugs assigned to me"
- "Log 2 hours on PROJ-456"
- "What's blocking PROJ-789?"

---

## Complete Skill Registry

All 14 available skills with capabilities and status:

| Skill | Purpose | Status | CRUD | Search | Bulk |
|-------|---------|--------|:----:|:------:|:----:|
| `jira-issue` | Core issue operations | Active | CRUD | - | - |
| `jira-lifecycle` | Workflow transitions, versions, components | Active | -RU- | - | - |
| `jira-search` | JQL queries, filters, export | Active | -R-- | Full | - |
| `jira-collaborate` | Comments, attachments, watchers | Active | CRUD | - | - |
| `jira-agile` | Sprints, epics, backlog, boards | Active | CRUD | - | - |
| `jira-relationships` | Issue links, dependencies, cloning | Active | CRUD | - | - |
| `jira-time` | Worklogs, estimates, time reports | Active | CRUD | - | - |
| `jira-jsm` | Service desks, requests, SLAs | Active | CRUD | Queues | - |
| `jira-bulk` | Mass operations at scale | Active | -UD- | - | Full |
| `jira-dev` | Git branches, commits, PRs | Active | CR-- | - | - |
| `jira-fields` | Custom field discovery | Active | -R-- | Fields | - |
| `jira-ops` | Cache, diagnostics, project discovery | Active | -RU- | - | - |
| `jira-admin` | Projects, permissions, workflows, screens | Active | CRUD | - | - |
| `jira-assistant` | This hub - routing & discovery | Active | - | - | - |

**Legend:** C=Create, R=Read, U=Update, D=Delete

---

## Routing Rules

### Primary Routing Table

#### Issue Management
| Need | Skill | Trigger Phrases | Confidence |
|------|-------|-----------------|:----------:|
| Create, read, update, delete issues | `jira-issue` | create issue, get issue, update issue, delete issue, new bug, new task, new story, show issue | High |
| Transitions, workflow, status changes | `jira-lifecycle` | transition, move to, change status, close, reopen, resolve, start, done | High |
| Project/permission/workflow admin | `jira-admin` | create project, project settings, permissions, workflow scheme, screens, issue types, notification scheme | High |

#### Search & Discovery
| Need | Skill | Trigger Phrases | Confidence |
|------|-------|-----------------|:----------:|
| JQL queries, saved filters, export | `jira-search` | search, find issues, JQL, filter, query, list issues, export | High |
| Custom field discovery, field IDs | `jira-fields` | custom field, field ID, what fields, agile fields, list fields | High |

#### Collaboration
| Need | Skill | Trigger Phrases | Confidence |
|------|-------|-----------------|:----------:|
| Comments, attachments, watchers | `jira-collaborate` | comment, attach, upload, watch, notify, add comment, download | High |
| Issue links, dependencies, cloning | `jira-relationships` | link issues, blocks, is blocked by, depends on, clone issue, duplicate, relates to | High |

#### Agile & Planning
| Need | Skill | Trigger Phrases | Confidence |
|------|-------|-----------------|:----------:|
| Sprints, epics, backlog, boards | `jira-agile` | sprint, epic, backlog, story points, board, velocity, add to sprint, create epic | High |
| Time tracking, worklogs, estimates | `jira-time` | log time, worklog, time spent, estimate, remaining time, hours, time report | High |

#### Bulk & Automation
| Need | Skill | Trigger Phrases | Confidence |
|------|-------|-----------------|:----------:|
| Bulk operations (50+ issues) | `jira-bulk` | bulk, batch, multiple issues, mass update, bulk transition, bulk assign | High |
| Git branches, commits, PRs | `jira-dev` | branch name, commit message, PR description, git, pull request | High |

#### Service Management
| Need | Skill | Trigger Phrases | Confidence |
|------|-------|-----------------|:----------:|
| Service desks, requests, SLAs, customers | `jira-jsm` | service desk, request, SLA, customer, queue, approval, knowledge base, portal | High |

#### Operations
| Need | Skill | Trigger Phrases | Confidence |
|------|-------|-----------------|:----------:|
| Cache management, diagnostics | `jira-ops` | cache, warm cache, clear cache, performance, discover project | High |

---

## Disambiguation Rules

When multiple skills might match, use these precedence rules:

### Ambiguous: "Show me the sprint"
| Interpretation | Skill | Confidence | Resolution |
|----------------|-------|:----------:|------------|
| Sprint details (dates, goals) | `jira-agile` | 0.7 | Ask: "Do you want sprint details or issues in the sprint?" |
| Issues in sprint | `jira-search` | 0.6 | |

### Ambiguous: "Link the PR"
| Interpretation | Skill | Confidence | Resolution |
|----------------|-------|:----------:|------------|
| Link GitHub PR to issue | `jira-dev` | 0.8 | Check for GitHub/PR context |
| Create issue link | `jira-relationships` | 0.5 | |

### Ambiguous: "Update the issues"
| Interpretation | Skill | Confidence | Resolution |
|----------------|-------|:----------:|------------|
| Single issue update | `jira-issue` | 0.6 | Ask: "How many issues? For 5+, I'll use bulk operations." |
| Bulk update (5+) | `jira-bulk` | 0.6 | |

### Precedence Matrix

When confidence scores are close (within 0.15), apply these rules:

1. **Explicit skill mention wins**: "use jira-bulk to..." → `jira-bulk`
2. **Quantity determines bulk**: 5+ issues → `jira-bulk`
3. **Recent context**: Just created issue + "assign it" → `jira-issue`
4. **Destructive caution**: Prefer read-only when ambiguous

### Fallback Behavior

If no skill matches with confidence > 0.4:
1. List top 3 possible skills with confidence scores
2. Ask clarifying question
3. Suggest `/jira-assistant-skills:browse-skills` for exploration

---

## Entity Extraction Patterns

Extract these entities from user queries before routing:

### Issue References
```
Pattern: [A-Z][A-Z0-9]+-[0-9]+
Examples: TES-123, PROJ-1, ABC123-999
Extract: issue_keys[]
```

### Project Keys
```
Pattern: [A-Z][A-Z0-9]{1,9}
Context: "in PROJECT", "PROJECT project", "for PROJECT"
Examples: TES, PROJ, MYAPP
Extract: project_key
```

### User References
```
Patterns:
  - @username → resolve to accountId
  - "me", "myself" → currentUser()
  - "unassigned" → null
  - email pattern → resolve to accountId
Extract: user_reference
```

### Time Expressions
```
Patterns:
  - Durations: "2h", "1d 4h", "30m", "1w 2d"
  - Relative: "yesterday", "last week", "this sprint"
  - JQL: "startOfDay(-7d)", "endOfWeek()"
Extract: time_expression, time_seconds
```

### Quantities
```
Patterns:
  - "all" → no limit
  - "first N", "top N" → limit=N
  - "N issues" → expected_count=N
Extract: quantity, is_bulk (true if N > 5)
```

### Priority/Status
```
Patterns:
  - Priority: highest, high, medium, low, lowest, P0-P4, critical, blocker
  - Status: open, in progress, done, closed, blocked, to do
Extract: priority, status
```

---

## Composite Query Parsing

Handle multi-intent queries by segmenting and ordering operations:

### Example: Complex Query
```
User: "Create a bug for the login crash, assign it to me,
       link it to TES-100, and add it to the current sprint"
```

**Parsed Operations:**
| Step | Intent | Skill | Depends On | Entities |
|:----:|--------|-------|:----------:|----------|
| 1 | Create bug | `jira-issue` | - | type=Bug, summary="login crash" |
| 2 | Assign to me | `jira-issue` | Step 1 | assignee=currentUser() |
| 3 | Link to TES-100 | `jira-relationships` | Step 1 | link_type=relates, target=TES-100 |
| 4 | Add to sprint | `jira-agile` | Step 1 | sprint=active |

**Execution Plan:**
1. Create issue → capture `new_issue_key`
2. Update assignee on `new_issue_key`
3. Create link from `new_issue_key` to TES-100
4. Move `new_issue_key` to active sprint

**Pronoun Resolution:**
- "it" after create → refers to newly created issue
- "them" after search → refers to search results

### Common Composite Patterns

| Pattern | Skills Chain | Example |
|---------|--------------|---------|
| Search → Bulk | `jira-search` → `jira-bulk` | "Find all P1 bugs and close them" |
| Create → Link | `jira-issue` → `jira-relationships` | "Create a subtask blocking TES-50" |
| Create → Estimate | `jira-issue` → `jira-time` | "Create a story with 5 point estimate" |
| Search → Export | `jira-search` → (built-in) | "Export all sprint issues to CSV" |
| Clone → Modify | `jira-relationships` → `jira-issue` | "Clone TES-100 and change priority to High" |

---

## Skill Chaining

### Automatic Chains

These skill combinations are automatically recognized:

```yaml
chains:
  search_and_bulk:
    trigger: "find ... and (update|transition|assign|close)"
    flow: jira-search → jira-bulk
    data: search_results.issues → bulk_input.issue_keys

  create_and_link:
    trigger: "create ... (blocking|linked to|depends on)"
    flow: jira-issue → jira-relationships
    data: created.key → link_source

  create_epic_with_stories:
    trigger: "create epic with (N stories|stories)"
    flow: jira-agile → jira-issue (repeat)
    data: epic.key → story.epic_link

  bulk_from_filter:
    trigger: "run filter ... and (update|bulk)"
    flow: jira-search (filter) → jira-bulk
    data: filter_results → bulk_input
```

### Manual Chain Invocation

For complex workflows, invoke skills sequentially:

```
Step 1: Load jira-search
        Execute: Find all bugs created this week
        Store: bug_keys = [TES-1, TES-2, TES-3]

Step 2: Load jira-bulk
        Execute: Transition bug_keys to "In Review"

Step 3: Load jira-collaborate
        Execute: Add comment to each with template
```

---

## Query Normalization

Translate natural language variations to canonical forms:

| User Says | Normalized Query | Skill |
|-----------|------------------|-------|
| "my tickets" | `assignee=currentUser()` | jira-search |
| "what am I working on" | `assignee=currentUser() AND status="In Progress"` | jira-search |
| "stuck issues" | `status=Blocked OR issueFunction in linkedIssuesOf("type=Blocker")` | jira-search |
| "close it" | `transition to Done/Closed` | jira-lifecycle |
| "who's working on TES-123" | `get assignee of TES-123` | jira-issue |
| "add me as watcher" | `add currentUser() to watchers` | jira-collaborate |

### Synonym Mapping

| Term | Canonical | Notes |
|------|-----------|-------|
| ticket, card, item | issue | |
| story points, points, SP | storyPoints | Agile estimate |
| blocked, stuck | has blocker link OR status=Blocked | |
| epic, initiative, theme | epic | Issue type |
| label, tag | label | |
| component, module | component | |

---

## Destructive Operation Safeguards

### High-Risk Operations

These operations require explicit confirmation:

| Operation | Skill | Risk Level | Safeguard |
|-----------|-------|:----------:|-----------|
| Delete issue | `jira-issue` | HIGH | Confirm key, warn if has subtasks/links |
| Bulk transition | `jira-bulk` | HIGH | Show count, require `--confirm` or dry-run first |
| Bulk delete | `jira-bulk` | CRITICAL | Require issue keys explicitly, no wildcards |
| Delete project | `jira-admin` | CRITICAL | Double confirmation, show issue count |
| Remove permissions | `jira-admin` | HIGH | Show affected users |

### Dry-Run Recommendations

Always suggest dry-run for:
- Any bulk operation
- Operations affecting > 10 issues
- Operations with regex/JQL wildcards
- First-time use of destructive commands

```
User: "Close all bugs in TES"
Assistant: "This will close 47 bugs. Run with --dry-run first?

            jira bulk transition "project=TES AND type=Bug" --to Done --dry-run

            Then confirm with:
            jira bulk transition "project=TES AND type=Bug" --to Done --confirm"
```

### Undo Guidance

| Operation | Undo Method |
|-----------|-------------|
| Transition | Transition back (if workflow allows) |
| Update field | Update again with previous value |
| Delete issue | Cannot undo - suggest archive/close instead |
| Add link | Remove link |
| Bulk update | Bulk update with original values (if logged) |

---

## Context Awareness

### Session State

Track these across the conversation:

| Context | Example | Usage |
|---------|---------|-------|
| Current project | TES | "create a bug" → in TES |
| Last issue touched | TES-123 | "assign it" → TES-123 |
| Last search results | [TES-1, TES-2, TES-3] | "update them" → bulk update |
| Active user | currentUser() | "assign to me" |

### Implicit Resolution

```
User: "Create a bug in TES"
→ Context: project=TES, last_issue=TES-456 (created)

User: "Set priority to High"
→ Implicit: TES-456 (last_issue)

User: "Link it to the epic"
→ Ambiguous: which epic? Ask or check parent.
```

### Context Reset

Clear context when:
- User switches projects explicitly
- User says "start fresh" or "new task"
- Conversation idle > 10 minutes

---

## Error Handling Guidance

### Skill-Specific Recovery

| Error | Likely Skill | Recovery |
|-------|--------------|----------|
| "Issue does not exist" | jira-issue | Verify key format, check project access |
| "Transition not available" | jira-lifecycle | Load `jira-lifecycle` to see valid transitions |
| "Permission denied" | any | Check with `jira-admin` → list permissions |
| "Field not found" | jira-issue | Use `jira-fields` to discover field IDs |
| "Rate limited" | any | Wait, use `jira-ops` cache warming |

### Permission Errors

```
Error: "You don't have permission to edit issues"

Recovery:
1. Check current permissions: jira admin list-permissions --project TES
2. If admin: jira admin add-permission --scheme ... --permission EDIT_ISSUES
3. If not admin: Contact project administrator
```

---

## Discoverability

### Interactive Exploration

- `/jira-assistant-skills:browse-skills` - List all skills with descriptions
- `/jira-assistant-skills:skill-info <skill-name>` - Deep dive into specific skill

### "Did You Mean?" Suggestions

When query does not match clearly:

```
User: "Show me the roadmap"
Assistant: "JIRA does not have a native roadmap view. Did you mean:
           - jira-agile: View epics and their child issues?
           - jira-search: Find issues by fix version?
           - External: Check Jira Product Discovery or roadmap plugins?"
```

### Skill Comparison

```
User: "Should I use jira-issue or jira-bulk to update 5 issues?"
Assistant: "For 5 issues:
           - jira-issue: Fine for 1-4 issues, runs sequentially
           - jira-bulk: Better for 5+, parallel execution, has dry-run

           Recommendation: Use jira-bulk with --dry-run first."
```

---

## Configuration

All skills share configuration via environment variables:

- `JIRA_SITE_URL` - Your JIRA instance URL
- `JIRA_EMAIL` - Your Atlassian account email
- `JIRA_API_TOKEN` - Your API token ([generate here](https://id.atlassian.com/manage-profile/security/api-tokens))
- `JIRA_PROFILE` - Optional profile for multi-instance support (dev/staging/prod)

See individual skill documentation for detailed configuration options.

---

## Version History

| Version | Changes |
|---------|---------|
| 2.0.0 | Added disambiguation rules, entity extraction, composite queries, skill chaining, jira-admin |
| 1.0.0 | Initial release with 12 skills |