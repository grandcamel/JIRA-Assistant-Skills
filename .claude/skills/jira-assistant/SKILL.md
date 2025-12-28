---
name: "JIRA Assistant"
description: "JIRA automation hub routing to 12 specialized skills for any JIRA task: issues, workflows, agile, search, time tracking, service management, and more."
when_to_use: |
  - Need to work with JIRA in any capacity
  - Unsure which JIRA skill applies to your task
  - Managing issues, workflows, agile, search, time tracking, or service management
  - Need to combine multiple JIRA operations in one flow
---

# JIRA Assistant

Complete JIRA automation hub that routes to 12 specialized skills for comprehensive JIRA automation.

## Quick Start

Tell me what you need in natural language. I'll load the appropriate specialized skill and execute your request.

**Examples:**
- "Create a bug in TES for login issues and assign to me"
- "Move PROJ-123 to In Progress"
- "Find all open bugs assigned to me"
- "Log 2 hours on PROJ-456"
- "What's blocking PROJ-789?"

---

## Skill Routing Guide

### Issue Management

| Need | Skill | Triggers |
|------|-------|----------|
| Create, read, update, delete issues | `jira-issue` | "create issue", "get issue", "update issue", "delete issue", "new bug", "new task", "new story" |
| Transitions, workflow, status changes | `jira-lifecycle` | "transition", "move to", "change status", "close", "reopen", "resolve" |

### Search & Discovery

| Need | Skill | Triggers |
|------|-------|----------|
| JQL queries, saved filters, search | `jira-search` | "search", "find issues", "JQL", "filter", "query" |
| Custom field discovery, field IDs | `jira-fields` | "custom field", "field ID", "what fields", "agile fields" |

### Collaboration

| Need | Skill | Triggers |
|------|-------|----------|
| Comments, attachments, watchers | `jira-collaborate` | "comment", "attach", "upload", "watch", "notify" |
| Issue links, dependencies, cloning | `jira-relationships` | "link issues", "blocks", "is blocked by", "depends on", "clone", "duplicate" |

### Agile & Planning

| Need | Skill | Triggers |
|------|-------|----------|
| Sprints, epics, backlog, boards | `jira-agile` | "sprint", "epic", "backlog", "story points", "board", "velocity" |
| Time tracking, worklogs, estimates | `jira-time` | "log time", "worklog", "time spent", "estimate", "remaining time" |

### Bulk & Automation

| Need | Skill | Triggers |
|------|-------|----------|
| Bulk operations at scale | `jira-bulk` | "bulk", "batch", "multiple issues", "mass update", "bulk transition" |
| Git branches, commits, PRs | `jira-dev` | "branch name", "commit message", "PR description", "git" |

### Service Management

| Need | Skill | Triggers |
|------|-------|----------|
| Service desks, requests, SLAs, customers | `jira-jsm` | "service desk", "request", "SLA", "customer", "queue", "approval", "knowledge base" |

### Operations

| Need | Skill | Triggers |
|------|-------|----------|
| Cache management, diagnostics | `jira-ops` | "cache", "warm cache", "clear cache", "performance" |

---

## How This Works

1. **You describe your task** in natural language
2. **I identify** which specialized skill applies based on the routing table above
3. **I invoke** that skill (e.g., `Skill: jira-issue`)
4. **The skill loads** with detailed scripts and instructions
5. **I execute** your request using the loaded capabilities

---

## Script Execution

For command syntax, parameter patterns, and error prevention, see [Script Execution Guidelines](docs/SCRIPT_EXECUTION.md).

---

## Multi-Skill Operations

Some tasks require multiple skills. I'll load them sequentially:

**Example: "Create an epic with 3 stories and estimate them"**
1. Load `jira-agile` - Create the epic
2. Load `jira-issue` - Create the stories linked to the epic
3. Load `jira-time` - Set estimates on each story

**Example: "Find all bugs from last week and bulk-transition them to Done"**
1. Load `jira-search` - Find the issues with JQL
2. Load `jira-bulk` - Bulk transition the results

---

## Quick Reference

For JQL patterns, time formats, issue types, and link types, see [Quick Reference Guide](docs/QUICK_REFERENCE.md).

---

## Best Practices

For comprehensive guidance on issue organization, agile estimation, JSM usage, and workflow design, see [Best Practices Guide](docs/BEST_PRACTICES.md).

---

## Configuration

All skills share configuration from:
- Environment: `JIRA_API_TOKEN`, `JIRA_EMAIL`, `JIRA_SITE_URL`
- Settings: `.claude/settings.local.json` or `.claude/settings.json`
- Profiles: Support for multiple JIRA instances (dev/staging/prod)

See individual skill documentation for detailed configuration options.
