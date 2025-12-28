# Common Agile Workflows

Multi-step workflows combining jira-agile with other skills.

## Epic-Driven Development

A complete workflow for feature development organized by epics.

### Step 1: Create Epic

```bash
python create_epic.py --project PROJ \
  --summary "User Management" \
  --epic-name "Auth" \
  --color blue \
  --priority High
```

### Step 2: Create Stories (using jira-issue skill)

```bash
python create_issue.py --project PROJ --type Story \
  --summary "User authentication" --labels auth

python create_issue.py --project PROJ --type Story \
  --summary "Password reset flow" --labels auth
```

### Step 3: Link Stories to Epic

```bash
python add_to_epic.py --epic PROJ-100 --jql "project=PROJ AND labels=auth"
```

### Step 4: Break Down into Subtasks

```bash
python create_subtask.py --parent PROJ-101 --summary "API endpoints"
python create_subtask.py --parent PROJ-101 --summary "Database schema"
python create_subtask.py --parent PROJ-101 --summary "Unit tests"
```

### Step 5: Track Progress

```bash
python get_epic.py PROJ-100 --with-children
```

## Sprint Planning Workflow

Complete sprint setup from backlog to active sprint.

### Step 1: View and Prioritize Backlog

```bash
# View current backlog
python get_backlog.py --board 123 --group-by epic

# Prioritize top items
python rank_issue.py PROJ-201 --top
```

### Step 2: Estimate Stories

```bash
# Estimate individual stories
python estimate_issue.py PROJ-201 --points 5

# Bulk estimate similar items
python estimate_issue.py --jql "labels=quick-win" --points 2 --dry-run
```

### Step 3: Create Sprint

```bash
python create_sprint.py --board 123 --name "Sprint 42" \
  --start 2025-01-20 --end 2025-02-03 \
  --goal "Launch user authentication MVP"
```

### Step 4: Populate Sprint

```bash
# Add high-priority items
python move_to_sprint.py --sprint 456 \
  --jql "project=PROJ AND status='To Do' AND priority IN (High, Highest)" \
  --dry-run

# Confirm and execute
python move_to_sprint.py --sprint 456 \
  --jql "project=PROJ AND status='To Do' AND priority IN (High, Highest)"
```

### Step 5: Review and Start

```bash
# Review sprint content
python get_sprint.py 456 --with-issues

# Start the sprint
python manage_sprint.py --sprint 456 --start
```

## Sprint Close and Retrospective

End-of-sprint workflow with carryover.

### Step 1: Review Sprint Status

```bash
python get_sprint.py 456 --with-issues
python get_estimates.py --sprint 456 --group-by status
```

### Step 2: Close Sprint

```bash
# Close and move incomplete work to next sprint
python manage_sprint.py --sprint 456 --close --move-incomplete-to 457
```

### Step 3: Create Retrospective Actions (using jira-issue)

```bash
python create_issue.py --project PROJ \
  --type Task \
  --summary "ACTION: Add unit test requirement to DoD" \
  --labels retro-action
```

## Release Planning with Epics

Organize features for a release.

### Step 1: Create Release Epics

```bash
python create_epic.py --project PROJ --summary "SAML Authentication" --epic-name "SAML"
python create_epic.py --project PROJ --summary "User Provisioning" --epic-name "Provision"
```

### Step 2: Estimate Epics

```bash
python get_estimates.py --epic PROJ-100
python get_estimates.py --epic PROJ-101
```

### Step 3: Track Release Progress

```bash
# View all release epics (using jira-search)
python jql_search.py "fixVersion = 'v2.0' AND type = Epic"

# Track individual epic progress
python get_epic.py PROJ-100 --with-children
```

## See Also

- [Quick Start](QUICK_START.md) - Essential workflows
- [Best Practices](BEST_PRACTICES.md) - Agile methodology guidance
- [Examples](../examples/README.md) - Detailed command examples
