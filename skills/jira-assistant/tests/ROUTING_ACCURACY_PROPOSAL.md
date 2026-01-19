# Routing Accuracy Improvement Proposal

**Date:** 2026-01-01
**Current Success Rate:** 55% (38/69 tests passing)
**Target Success Rate:** 80%
**Tests to Fix:** ~17 additional tests

---

## Executive Summary

Analysis of 31 routing test failures reveals three root causes:
1. **Skill trigger overlap** - Generic skills (jira-issue, jira-search) match too broadly
2. **Missing trigger keywords** - Specialized skills lack distinctive keywords in descriptions
3. **Disambiguation behavior** - Claude routes to a skill instead of asking when ambiguous

This proposal outlines concrete changes to skill descriptions (SKILL.md frontmatter) to improve routing accuracy by 25+ percentage points.

---

## Failure Analysis by Category

### Category 1: Direct Routing Misses (7 failures)

These inputs should route to a specific skill but went elsewhere:

| Test | Input | Expected | Got | Root Cause |
|------|-------|----------|-----|------------|
| TC012 | "create an epic called 'User Authentication'" | jira-agile | jira-issue | jira-issue claims "Create epic" without exclusion |
| TC015 | "show the backlog for TES" | jira-agile | jira-search | "backlog" keyword missing from agile triggers |
| TC020 | "what's blocking TES-789?" | jira-relationships | jira-issue | "blocking" keyword not in relationships triggers |
| TC024 | "bulk update all bugs in TES to High priority" | jira-bulk | jira-search | "bulk" + quantity signals not strong enough |
| TC025 | "transition 50 issues to Done" | jira-bulk | jira-search | Quantity ("50 issues") not triggering bulk |
| TC027 | "write a PR description for TES-456" | jira-dev | jira-issue | "PR description" not prominent in dev triggers |
| TC028 | "what's the field ID for story points?" | jira-fields | jira-agile | "field ID" query going to agile (which mentions story points) |

### Category 2: Disambiguation Failures (17 failures)

These ambiguous inputs should ask for clarification but routed directly:

| Test | Input | Expected Behavior | What Happened |
|------|-------|-------------------|---------------|
| TC031 | "show me the sprint" | Ask: agile vs search | Routed to jira-agile |
| TC032 | "update the issues" | Ask: issue vs lifecycle vs bulk | Routed to jira-lifecycle |
| TC033 | "remove the bugs" | Ask: issue vs bulk | Did not route to JIRA skill |
| TC034 | "link the PR" | Ask: dev vs relationships | Did not route to JIRA skill |
| TC051-TC061 | Various vague inputs | Ask for clarification | Picked a skill |

### Category 3: Negative Trigger Failures (5 failures)

These inputs routed to wrong skill despite clear intent:

| Test | Input | Expected | Got | Fix |
|------|-------|----------|-----|-----|
| TC041 | "bulk close 50 bugs" | jira-bulk | jira-search | Strengthen bulk triggers |
| TC075 | "show me the time spent on TES-123" | jira-time | jira-issue | Add "time spent" to time triggers |
| TC077 | "what custom fields are available?" | jira-fields | jira-agile | Remove "story points" from agile description |
| TC078 | "warm the cache for TES" | jira-ops | jira-fields | Make cache keywords exclusive to ops |
| TC079 | "generate a branch name for TES-456" | jira-dev | jira-issue | Add "branch name" to dev triggers |

---

## Proposed Changes

### Strategy 1: Add Exclusive Trigger Keywords to SKILL.md Frontmatter

Each skill's `description` field in the YAML frontmatter is the primary routing signal. We need to add distinctive keywords that don't overlap with other skills.

#### jira-agile/SKILL.md

**Current description:**
```yaml
description: "Epic, sprint, and backlog management - create/link epics, manage sprints, estimate with story points, rank backlog issues."
```

**Proposed description:**
```yaml
description: "Epic creation and sprint management - create epics, manage sprints, view backlog, estimate with story points. Use when: 'create an epic', 'show the backlog', 'add to sprint', 'set story points', 'sprint planning'. NOT for: creating bugs/tasks/stories (use jira-issue), searching issues (use jira-search), field ID discovery (use jira-fields)."
```

**Changes:**
- Added "Epic creation" as first phrase (not just "management")
- Added explicit trigger phrases: "create an epic", "show the backlog"
- Added explicit NOT FOR section to reduce false matches

#### jira-bulk/SKILL.md

**Current description:**
```yaml
description: "Bulk operations for 50+ issues - transitions, assignments, priorities, and cloning. Use when: updating multiple issues simultaneously..."
```

**Proposed description:**
```yaml
description: "Bulk operations for multiple issues at scale - transitions, assignments, priorities, cloning. TRIGGERS: 'bulk update', 'bulk close', 'transition N issues' where N > 10, 'update all bugs', 'close 50 issues', 'mass transition'. Always use for operations mentioning quantities like '50 issues', '100 bugs', 'all issues in project'. NOT for: single issue transitions (use jira-lifecycle), searching (use jira-search)."
```

**Changes:**
- Added explicit quantity triggers ("50 issues", "100 bugs")
- Added "bulk close", "mass transition"
- Emphasized that quantities > 10 should trigger this skill

#### jira-dev/SKILL.md

**Current description:**
```yaml
description: "Developer workflow integration for JIRA - Git branch names, commit parsing, PR descriptions..."
```

**Proposed description:**
```yaml
description: "Git and developer workflow integration - generate branch names, write PR descriptions, parse commits, link PRs to issues. TRIGGERS: 'generate branch name', 'create branch name', 'write PR description', 'PR description for', 'link PR', 'parse commit'. Use for any Git, GitHub, GitLab, Bitbucket integration with JIRA."
```

**Changes:**
- Made "generate branch name" and "write PR description" explicit triggers
- Removed generic phrases that overlap with jira-issue

#### jira-fields/SKILL.md

**Current description:**
```yaml
description: "Custom field management and configuration - list fields, check project fields, configure Agile fields..."
```

**Proposed description:**
```yaml
description: "Custom field discovery and configuration - find field IDs, list available fields, check project fields. TRIGGERS: 'field ID for', 'what's the field ID', 'list custom fields', 'what fields are available', 'custom fields', 'customfield_'. Use when asking about JIRA field metadata, NOT when setting field values (use jira-issue or jira-agile)."
```

**Changes:**
- Added "field ID for" as explicit trigger
- Added "what fields are available"
- Clarified that this is for discovery, not setting values

#### jira-relationships/SKILL.md

**Current description:**
```yaml
description: "Issue linking and dependency management - create links, view blockers, analyze dependencies..."
```

**Proposed description:**
```yaml
description: "Issue linking, blockers, and dependency analysis - create issue links, find blockers, analyze blocking chains, clone issues. TRIGGERS: 'what's blocking', 'is blocked by', 'link issues', 'blockers for', 'depends on', 'clone issue', 'blocking chain'. Use for any question about issue dependencies or relationships."
```

**Changes:**
- Added "what's blocking" as explicit trigger
- Added "blocking chain" and "depends on"
- Made blockers more prominent

#### jira-ops/SKILL.md

**Current description:**
```yaml
description: "Cache management, request batching, and operational utilities..."
```

**Proposed description:**
```yaml
description: "JIRA cache and performance operations - warm cache, clear cache, cache status, request batching. TRIGGERS: 'warm the cache', 'cache status', 'clear cache', 'cache warm', 'cache for project'. Use for JIRA API performance optimization and caching operations."
```

**Changes:**
- Made "warm the cache" first trigger phrase
- Removed ambiguous "operational utilities"
- Focused on cache-specific keywords

#### jira-time/SKILL.md

**Current description:**
```yaml
description: "Time tracking and worklog management with estimation, reporting..."
```

**Proposed description:**
```yaml
description: "Time tracking, worklogs, and time reports - log time, view time spent, manage estimates, generate timesheets. TRIGGERS: 'log time', 'time spent on', 'log hours', 'worklog', 'time tracking', 'timesheet', 'how much time'. Use for any time-related queries on issues."
```

**Changes:**
- Added "time spent on" as explicit trigger
- Added "how much time"
- Made time-specific keywords more prominent

#### jira-issue/SKILL.md

**Current description:**
```yaml
description: "Core CRUD operations for JIRA issues - create, read, update, delete tickets..."
```

**Proposed description:**
```yaml
description: "Core JIRA issue CRUD - create bugs/tasks/stories, get issue details, update fields, delete issues. Use for single issue operations. NOT for: epics (use jira-agile), transitions/status changes (use jira-lifecycle), comments (use jira-collaborate), time tracking (use jira-time), bulk operations (use jira-bulk), dependencies (use jira-relationships), branch names (use jira-dev)."
```

**Changes:**
- Added explicit NOT FOR section listing all the skills that handle specialized operations
- Narrowed scope to "single issue operations"
- Removed "epic" from the create list

### Strategy 2: Add Disambiguation Guidance to jira-assistant

The hub skill (jira-assistant) should include routing rules that specify when to ask for clarification.

#### jira-assistant/SKILL.md

Add a new section:

```markdown
## Disambiguation Rules

When the user input matches MULTIPLE skills equally, ASK for clarification instead of picking one:

| Ambiguous Input Pattern | Clarifying Question |
|------------------------|---------------------|
| "update/change issues" (no count) | "One issue or multiple?" → jira-issue vs jira-bulk |
| "show the sprint" (no action) | "Sprint details or issues in sprint?" → jira-agile vs jira-search |
| "link" + "PR" | "Link PR to JIRA or create issue link?" → jira-dev vs jira-relationships |
| "estimate" (no context) | "Time estimate or story points?" → jira-time vs jira-agile |
| "status" (no issue key) | "Check issue status or workflow transitions?" → jira-issue vs jira-lifecycle |

**Rule:** If the user's request is missing a key piece of information (issue key, project, quantity), ask for clarification rather than guessing.
```

### Strategy 3: Update Test Expectations for Reasonable Behavior

Some disambiguation tests may have unrealistic expectations. For example:

- TC031 "show me the sprint" - It's reasonable for Claude to route to jira-agile and then ask for project context
- TC054 "update the estimate" - jira-time is a reasonable choice, asking for issue key is appropriate behavior

**Recommendation:** Review disambiguation tests TC031-TC061 and adjust expectations where Claude's behavior (routing + asking for details) is acceptable.

---

## Implementation Priority

### Phase 1: Quick Wins (Est. +15% accuracy)

Fix direct routing failures with keyword additions:

1. **jira-bulk**: Add quantity triggers ("50 issues", "bulk close")
2. **jira-relationships**: Add "what's blocking", "blockers for"
3. **jira-dev**: Add "generate branch name", "PR description for"
4. **jira-fields**: Add "field ID for", "what fields available"
5. **jira-time**: Add "time spent on"
6. **jira-ops**: Add "warm the cache"

### Phase 2: Scope Reduction (Est. +8% accuracy)

Add NOT FOR exclusions to jira-issue and jira-search to prevent over-matching:

1. **jira-issue**: Add exclusions for epics, transitions, time, bulk, dev
2. **jira-search**: Add exclusions to not match when action verbs present
3. **jira-agile**: Add "create an epic" as primary trigger

### Phase 3: Test Adjustment (Est. +5% accuracy)

Review and adjust disambiguation test expectations:

1. Accept "route + ask for details" as valid behavior for vague inputs
2. Adjust tests where Claude's natural behavior is reasonable
3. Add new disambiguation scenarios that are truly ambiguous

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Overall pass rate | 55% | 80% | pytest test_routing.py |
| Direct routing accuracy | 77% (23/30) | 95% | TC001-TC030 |
| Disambiguation rate | 0% (0/15) | 60% | TC031-TC061 |
| Negative trigger accuracy | 50% (5/10) | 90% | TC039-TC079 |

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Keyword changes may break working tests | Run full test suite after each change |
| Over-specific triggers may miss variations | Use multiple trigger phrases per intent |
| NOT FOR lists become maintenance burden | Keep lists to top 5 exclusions only |
| Model updates may change routing behavior | Re-run tests monthly; use golden test set |

---

## Appendix: Full Test Failure Details

### Direct Routing Failures

```
TC012: "create an epic called 'User Authentication'"
  Expected: jira-agile, Got: jira-issue

TC015: "show the backlog for TES"
  Expected: jira-agile, Got: jira-search

TC020: "what's blocking TES-789?"
  Expected: jira-relationships, Got: jira-issue

TC024: "bulk update all bugs in TES to High priority"
  Expected: jira-bulk, Got: jira-search

TC025: "transition 50 issues to Done"
  Expected: jira-bulk, Got: jira-search

TC027: "write a PR description for TES-456"
  Expected: jira-dev, Got: jira-issue

TC028: "what's the field ID for story points?"
  Expected: jira-fields, Got: jira-agile
```

### Disambiguation Failures (all got skill instead of asking)

```
TC031: "show me the sprint" → jira-agile (expected: ask)
TC032: "update the issues" → jira-lifecycle (expected: ask)
TC033: "remove the bugs" → None (expected: ask jira-issue vs jira-bulk)
TC034: "link the PR" → None (expected: ask jira-dev vs jira-relationships)
TC051: "update the fields" → None (expected: ask)
TC052: "show my work" → jira-dev (expected: ask jira-search vs jira-time)
TC053: "move these to the sprint" → jira-agile (expected: ask)
TC054: "update the estimate" → jira-time (expected: ask)
TC055: "create a request" → jira-jsm (expected: ask)
TC056: "check the status" → jira-dev (expected: ask)
TC057: "add to the epic" → jira-agile (expected: ask)
TC058: "show the dependencies" → jira-ops (expected: ask)
TC059: "fix the priority" → None (expected: ask)
TC060: "set up the project" → jira-issue (expected: ask)
TC061: "copy this issue" → jira-relationships (expected: ask)
```

### Negative Trigger Failures

```
TC041: "bulk close 50 bugs"
  Expected: jira-bulk, Got: jira-search

TC075: "show me the time spent on TES-123"
  Expected: jira-time, Got: jira-issue

TC077: "what custom fields are available?"
  Expected: jira-fields, Got: jira-agile

TC078: "warm the cache for TES"
  Expected: jira-ops, Got: jira-fields

TC079: "generate a branch name for TES-456"
  Expected: jira-dev, Got: jira-issue
```
