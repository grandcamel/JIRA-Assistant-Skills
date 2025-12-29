---
name: "JIRA Skills Marketplace"
description: "Browse and discover 14 specialized JIRA automation skills - from issue management to service desk operations."
when_to_use: |
  - User wants to see available JIRA skills
  - User asks "what skills are available?"
  - User needs help choosing the right skill
  - User wants to browse JIRA automation capabilities
---

# JIRA Skills Marketplace

Complete catalog of JIRA automation skills for Claude Code. Each skill is production-ready with 100+ Python scripts.

## Skill Categories

### Core Operations

| Skill | Description | Key Commands |
|-------|-------------|--------------|
| **jira-issue** | Issue CRUD operations | Create bugs, tasks, stories; update fields; delete issues |
| **jira-lifecycle** | Workflow transitions | Move issues between statuses; close, reopen, resolve |
| **jira-search** | JQL queries & filters | Find issues; build JQL; save/share filters |

### Collaboration

| Skill | Description | Key Commands |
|-------|-------------|--------------|
| **jira-collaborate** | Comments & attachments | Add comments; upload files; manage watchers |
| **jira-relationships** | Issue linking | Create links; find blockers; clone issues |

### Agile & Planning

| Skill | Description | Key Commands |
|-------|-------------|--------------|
| **jira-agile** | Sprints & epics | Create sprints; manage backlog; story points |
| **jira-time** | Time tracking | Log work; set estimates; time reports |

### Bulk & Automation

| Skill | Description | Key Commands |
|-------|-------------|--------------|
| **jira-bulk** | Mass operations | Bulk transitions; assignments; priority updates |
| **jira-dev** | Git integration | Branch names; commit parsing; PR descriptions |

### Administration

| Skill | Description | Key Commands |
|-------|-------------|--------------|
| **jira-fields** | Field discovery | Find custom fields; configure agile fields |
| **jira-ops** | Cache & utilities | Warm cache; clear cache; diagnostics |
| **jira-admin** | Project admin | Permissions; schemes; configuration |

### Service Management

| Skill | Description | Key Commands |
|-------|-------------|--------------|
| **jira-jsm** | Service desk | Requests; SLAs; queues; customers; approvals |
| **jira-assistant** | Meta-router | Routes to the right skill automatically |

---

## Quick Start Examples

### Developer Workflow
```
"Create a bug: Login fails on Safari"
"Start progress on PROJ-123"
"Log 2 hours on PROJ-456: Fixed auth issue"
"Generate branch name for PROJ-789"
```

### Team Lead Workflow
```
"Show sprint progress for Team Alpha"
"What's blocking the release?"
"Find unestimated stories in backlog"
"Bulk close all resolved issues in PROJ"
```

### Service Desk Workflow
```
"Show my queue sorted by SLA"
"Create urgent request: Database unreachable"
"Approve REQ-123"
```

---

## Skill Details

### jira-issue
**Core CRUD operations for JIRA issues**
- Create issues (bugs, tasks, stories, epics, subtasks)
- Read issue details with all fields
- Update summary, description, priority, labels
- Delete issues (with confirmation)
- Supports ADF (rich text) and markdown

### jira-lifecycle
**Workflow and status management**
- Transition issues between statuses
- Find available transitions
- Handle resolution on close
- Support for custom workflows

### jira-search
**JQL queries and saved filters**
- Execute JQL searches
- Build JQL from natural language
- Create and share filters
- Export results (JSON, CSV)
- Validate JQL syntax

### jira-collaborate
**Team collaboration features**
- Add/edit/delete comments
- Upload and manage attachments
- Add/remove watchers
- Notifications management

### jira-relationships
**Issue linking and dependencies**
- Create issue links (blocks, relates, duplicates)
- Find blocker chains
- Clone issues with links
- Dependency analysis

### jira-agile
**Agile/Scrum workflow support**
- Create and manage sprints
- Epic management
- Backlog prioritization
- Story point estimation
- Board and velocity tracking

### jira-time
**Time tracking and estimation**
- Log work with comments
- Set original/remaining estimates
- Time reports by user/project
- Worklog management

### jira-bulk
**Bulk operations at scale**
- Bulk transitions (with dry-run)
- Mass assignments
- Priority updates
- Bulk cloning
- Rollback support

### jira-dev
**Developer workflow integration**
- Generate Git branch names from issues
- Parse commit messages for issue keys
- Create PR descriptions from issues
- Link commits to issues

### jira-fields
**Custom field management**
- Discover custom fields
- Find field IDs
- Configure agile fields
- Project field mapping

### jira-ops
**Cache and operational utilities**
- Warm project cache
- Clear stale cache
- Request batching
- Performance diagnostics

### jira-admin
**Project administration**
- Permission management
- Scheme configuration
- Project settings

### jira-jsm
**Jira Service Management**
- Service desk operations
- Request lifecycle
- SLA management
- Customer management
- Queue configuration
- Approval workflows
- Knowledge base

### jira-assistant
**Meta-skill router**
- Routes requests to appropriate skill
- Combines multiple skills for complex tasks
- Natural language understanding

---

## Installation

Skills are pre-installed in this project. Just ask Claude to perform any JIRA operation:

```
"Show my open issues"
"Create a task for code review"
"What's blocking PROJ-123?"
```

## Configuration

Set up your JIRA credentials:
```bash
export JIRA_API_TOKEN="your-token"
export JIRA_EMAIL="you@company.com"
export JIRA_SITE_URL="https://company.atlassian.net"
```

---

## Stats

- **14** specialized skills
- **100+** production scripts
- **560+** passing tests
- **0** JQL to memorize
