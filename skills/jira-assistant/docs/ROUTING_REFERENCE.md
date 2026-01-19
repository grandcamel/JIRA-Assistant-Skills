# Routing Reference

Detailed patterns and rules for skill routing in jira-assistant.

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

Handle multi-intent queries by segmenting and ordering operations.

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
| "stuck issues" | `status=Blocked OR has blocker link` | jira-search |
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

### Context Expiration

After 5+ messages or 5+ minutes since last entity reference:
- Re-confirm rather than assume: "Do you mean TES-123 from earlier?"
- Don't guess when context is stale

**Triggers for re-confirmation**:
- 5+ messages since entity was last mentioned
- 5+ minutes elapsed since last reference
- User topic has shifted significantly

### Context Reset

Clear context when:
- User switches projects explicitly
- User says "start fresh" or "new task"
- Session ends or restarts

### Conflicting Context

When recent mentions conflict, most recent explicit mention wins:

```
User: "Search for bugs in TES" → Found TES-100, TES-101
User: "Show me TES-456"  [different issue]
User: "Close it"
→ "it" = TES-456 (most recent explicit mention wins)
```

**Resolution priority**:
1. Most recent explicit issue key
2. Last created/modified issue
3. Search result set (if "them" or plural)
4. Ask for clarification if ambiguous
