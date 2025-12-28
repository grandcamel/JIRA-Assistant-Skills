# Scripts Reference

Complete CLI documentation for all JIRA Assistant Skills scripts.

---

## Core Operations

### jira-issue (4 scripts)

```bash
# Create issue with all details
python .claude/skills/jira-issue/scripts/create_issue.py --project PROJ --type Bug \
  --summary "Login fails on Safari" --priority High \
  --description "Steps to reproduce..." --labels browser,auth

# Get comprehensive view
python .claude/skills/jira-issue/scripts/get_issue.py PROJ-123 --detailed --show-links --show-time

# Update issue
python .claude/skills/jira-issue/scripts/update_issue.py PROJ-123 --priority Highest --labels critical

# Delete issue (with confirmation)
python .claude/skills/jira-issue/scripts/delete_issue.py PROJ-123 --confirm
```

### jira-lifecycle (5 scripts)

```bash
# Workflow transitions
python .claude/skills/jira-lifecycle/scripts/transition_issue.py PROJ-123 --name "In Progress"
python .claude/skills/jira-lifecycle/scripts/resolve_issue.py PROJ-123 --resolution Fixed --comment "Deployed in v2.1"

# Assignments
python .claude/skills/jira-lifecycle/scripts/assign_issue.py PROJ-123 --user alice@company.com
python .claude/skills/jira-lifecycle/scripts/assign_issue.py PROJ-123 --self  # Assign to me

# Reopen
python .claude/skills/jira-lifecycle/scripts/reopen_issue.py PROJ-123 --comment "Found regression"
```

---

## Search & Discovery

### jira-search (17 scripts)

```bash
# Complex queries
python .claude/skills/jira-search/scripts/jql_search.py "sprint in openSprints() AND assignee = currentUser()"

# Saved filters
python .claude/skills/jira-search/scripts/run_filter.py --name "My Team's Blockers"

# Create/manage filters
python .claude/skills/jira-search/scripts/create_filter.py --name "Sprint Blockers" \
  --jql "sprint in openSprints() AND status = Blocked"
python .claude/skills/jira-search/scripts/list_filters.py --favorite

# JQL validation and building
python .claude/skills/jira-search/scripts/jql_validate.py "project = PROJ AND status = Open"
python .claude/skills/jira-search/scripts/jql_autocomplete.py --field status --project PROJ

# Bulk operations
python .claude/skills/jira-search/scripts/bulk_update.py "labels = deprecated" \
  --add-labels archived --remove-labels active

# Export for reporting
python .claude/skills/jira-search/scripts/export_results.py "project = PROJ AND resolved >= -30d" \
  --output monthly.csv --format csv
```

---

## Agile Workflows

### jira-agile (12 scripts)

```bash
# Sprint lifecycle
python .claude/skills/jira-agile/scripts/create_sprint.py --board 42 --name "Sprint 23" --goal "Payment System v2"
python .claude/skills/jira-agile/scripts/start_sprint.py 456
python .claude/skills/jira-agile/scripts/close_sprint.py 456 --move-incomplete-to 457

# Move issues to sprint
python .claude/skills/jira-agile/scripts/move_to_sprint.py --sprint 456 --issues PROJ-1,PROJ-2,PROJ-3

# Backlog management
python .claude/skills/jira-agile/scripts/get_backlog.py --board 42 --group-by epic
python .claude/skills/jira-agile/scripts/rank_issue.py PROJ-10 --before PROJ-5

# Epic management
python .claude/skills/jira-agile/scripts/create_epic.py --project PROJ --name "Authentication Redesign"
python .claude/skills/jira-agile/scripts/get_epic_issues.py PROJ-100

# Estimation
python .claude/skills/jira-agile/scripts/estimate_issue.py PROJ-123 --points 5

# Board operations
python .claude/skills/jira-agile/scripts/list_boards.py --project PROJ
python .claude/skills/jira-agile/scripts/get_sprint.py 456 --show-issues
```

---

## Dependencies & Relationships

### jira-relationships (8 scripts)

```bash
# Linking
python .claude/skills/jira-relationships/scripts/link_issue.py PROJ-1 --blocks PROJ-2
python .claude/skills/jira-relationships/scripts/link_issue.py PROJ-1 --relates-to PROJ-3
python .claude/skills/jira-relationships/scripts/link_issue.py PROJ-1 --duplicates PROJ-99

# Impact analysis
python .claude/skills/jira-relationships/scripts/get_blockers.py PROJ-1 --recursive --max-depth 5
python .claude/skills/jira-relationships/scripts/get_dependencies.py PROJ-1 --output mermaid  # Visualize

# Get all links
python .claude/skills/jira-relationships/scripts/get_links.py PROJ-123

# Cloning
python .claude/skills/jira-relationships/scripts/clone_issue.py PROJ-123 \
  --include-subtasks --include-links --target-project NEWPROJ

# Unlink
python .claude/skills/jira-relationships/scripts/unlink_issue.py PROJ-1 --from PROJ-2
```

---

## Time Tracking

### jira-time (6 scripts)

```bash
# Log work
python .claude/skills/jira-time/scripts/log_work.py PROJ-123 --time "2h 30m" \
  --comment "Implemented retry logic"

# View worklogs
python .claude/skills/jira-time/scripts/get_worklogs.py PROJ-123
python .claude/skills/jira-time/scripts/get_worklogs.py PROJ-123 --author self --since 7d

# Estimates
python .claude/skills/jira-time/scripts/set_estimate.py PROJ-123 --original "8h" --remaining "4h"

# Time reports
python .claude/skills/jira-time/scripts/time_report.py --user self --period week
python .claude/skills/jira-time/scripts/time_report.py --project PROJ --period month --export csv
```

---

## Service Management (JSM)

### jira-jsm (Full ITSM Suite)

```bash
# Service desk discovery
python .claude/skills/jira-jsm/scripts/list_service_desks.py
python .claude/skills/jira-jsm/scripts/list_request_types.py --service-desk 1

# Request lifecycle
python .claude/skills/jira-jsm/scripts/create_request.py --service-desk 1 \
  --request-type "Hardware Request" --summary "New laptop for onboarding"
python .claude/skills/jira-jsm/scripts/get_request.py SD-123

# SLA tracking
python .claude/skills/jira-jsm/scripts/get_sla.py SD-123  # SLA status with breach prediction

# Queue management
python .claude/skills/jira-jsm/scripts/list_queues.py --service-desk 1 --include-counts
python .claude/skills/jira-jsm/scripts/get_queue.py --queue-id 10

# Customer management
python .claude/skills/jira-jsm/scripts/add_customer.py --service-desk 1 --email customer@external.com
python .claude/skills/jira-jsm/scripts/list_customers.py --service-desk 1

# Approvals
python .claude/skills/jira-jsm/scripts/get_approvals.py SD-123
python .claude/skills/jira-jsm/scripts/approve_request.py SD-123 --decision approve --comment "Budget approved"

# Knowledge base
python .claude/skills/jira-jsm/scripts/search_kb.py --service-desk 1 --query "password reset"
```

---

## Bulk Operations

### jira-bulk (4 scripts)

```bash
# Mass transitions (with safety)
python .claude/skills/jira-bulk/scripts/bulk_transition.py \
  --jql "sprint = 456 AND status != Done" --to Done --dry-run
python .claude/skills/jira-bulk/scripts/bulk_transition.py \
  --jql "sprint = 456 AND status != Done" --to Done

# Bulk assignments
python .claude/skills/jira-bulk/scripts/bulk_assign.py \
  --jql "component = Backend AND assignee is EMPTY" --assignee self

# Bulk priority changes
python .claude/skills/jira-bulk/scripts/bulk_priority.py \
  --jql "labels = critical AND priority != Highest" --priority Highest

# Clone entire sprints
python .claude/skills/jira-bulk/scripts/bulk_clone.py \
  --jql "sprint = 456" --include-subtasks --target-project ARCHIVE
```

---

## Developer Integration

### jira-dev (6 scripts)

```bash
# Git branch names
python .claude/skills/jira-dev/scripts/create_branch_name.py PROJ-123
# Output: feature/proj-123-implement-oauth-refresh

python .claude/skills/jira-dev/scripts/create_branch_name.py PROJ-123 --prefix bugfix
# Output: bugfix/proj-123-implement-oauth-refresh

# PR integration
python .claude/skills/jira-dev/scripts/create_pr_description.py PROJ-123 \
  --include-checklist --include-labels
# Output: Full PR template with JIRA context

# Commit linking
python .claude/skills/jira-dev/scripts/link_commit.py PROJ-123 \
  --commit abc123 --repo https://github.com/org/repo

# Parse commits for issue references
python .claude/skills/jira-dev/scripts/parse_commits.py --since HEAD~10
python .claude/skills/jira-dev/scripts/parse_commits.py --branch feature/auth
```

---

## Field Discovery

### jira-fields (4 scripts)

```bash
# List all fields
python .claude/skills/jira-fields/scripts/list_fields.py --type custom
python .claude/skills/jira-fields/scripts/list_fields.py --search "story points"

# Project-specific fields
python .claude/skills/jira-fields/scripts/get_project_fields.py PROJ

# Agile field configuration
python .claude/skills/jira-fields/scripts/configure_agile_fields.py --project PROJ
python .claude/skills/jira-fields/scripts/get_agile_fields.py --board 42
```

---

## Operations & Utilities

### jira-ops (4 scripts)

```bash
# Cache management
python .claude/skills/jira-ops/scripts/cache_warm.py --project PROJ
python .claude/skills/jira-ops/scripts/cache_clear.py --all
python .claude/skills/jira-ops/scripts/cache_status.py

# Project context discovery
python .claude/skills/jira-ops/scripts/discover_project.py PROJ --profile development
```

---

## Common Flags

All scripts support these common flags:

| Flag | Description |
|------|-------------|
| `--profile` | JIRA profile to use (from settings.json) |
| `--help` | Show help message and exit |
| `--dry-run` | Preview changes without making them (where applicable) |
| `--output` | Output format: table, json, csv |
| `--verbose` | Enable verbose output |

---

## Examples

### Daily Developer Workflow

```bash
# Morning: What's on my plate?
python .claude/skills/jira-search/scripts/jql_search.py \
  "assignee = currentUser() AND sprint in openSprints() ORDER BY priority DESC"

# Start work
python .claude/skills/jira-lifecycle/scripts/transition_issue.py PROJ-123 --name "In Progress"

# End of day: Log time
python .claude/skills/jira-time/scripts/log_work.py PROJ-123 --time "4h" --comment "Implemented feature"

# Done? Close it
python .claude/skills/jira-lifecycle/scripts/resolve_issue.py PROJ-123 --resolution Fixed
```

### Sprint Planning

```bash
# Create sprint
python .claude/skills/jira-agile/scripts/create_sprint.py --board 42 --name "Sprint 23"

# Find top priorities
python .claude/skills/jira-search/scripts/jql_search.py \
  "project = PROJ AND status = 'To Do' ORDER BY priority DESC, rank ASC" --limit 20

# Move to sprint
python .claude/skills/jira-agile/scripts/move_to_sprint.py --sprint 456 \
  --issues PROJ-101,PROJ-102,PROJ-103,PROJ-104,PROJ-105

# Start sprint
python .claude/skills/jira-agile/scripts/start_sprint.py 456
```

### Incident Response

```bash
# Create incident
python .claude/skills/jira-issue/scripts/create_issue.py --project INC --type Bug \
  --summary "Production database unreachable" --priority Highest \
  --labels incident,p1,production

# Link to related issues
python .claude/skills/jira-relationships/scripts/link_issue.py INC-123 --relates-to INFRA-456

# Track resolution
python .claude/skills/jira-lifecycle/scripts/transition_issue.py INC-123 --name "In Progress"

# Resolve
python .claude/skills/jira-lifecycle/scripts/resolve_issue.py INC-123 \
  --resolution Fixed --comment "Root cause: Memory leak. Deployed hotfix v2.1.1"
```

---

## See Also

- [Quick Start Guide](quick-start.md) — Get up and running
- [Configuration Guide](configuration.md) — Multi-profile setup
- [Troubleshooting](troubleshooting.md) — Common issues
