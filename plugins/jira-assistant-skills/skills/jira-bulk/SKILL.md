---
name: "jira-bulk-operations"
description: "Bulk operations for 50+ issues - transitions, assignments, priorities, and cloning. Use when: updating multiple issues simultaneously (dry-run preview included), needing rollback safety, or coordinating team changes. Handles partial failures gracefully."
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# jira-bulk

Bulk operations for JIRA issue management at scale - transitions, assignments, priorities, and cloning.

## When to use this skill

Use this skill when you need to:
- Transition **multiple issues** through workflow states simultaneously
- Assign **multiple issues** to a user (or unassign)
- Set priority on **multiple issues** at once
- Clone issues with their subtasks and links
- Execute operations with **dry-run preview** before making changes
- Handle **partial failures** gracefully with progress tracking

**Scale guidance:**
- 5-10 issues: Run directly, no special options needed
- 50-100 issues: Use `--dry-run` first, then execute
- 500+ issues: Use batching + checkpointing for reliability

## Quick Start

```bash
# Preview before making changes
jira bulk transition --jql "project=PROJ AND status='In Progress'" --to "Done" --dry-run

# Execute the transition
jira bulk transition --jql "project=PROJ AND status='In Progress'" --to "Done"
```

For more patterns, see [Quick Start Guide](docs/QUICK_START.md).

## Available Scripts

| Script | Purpose | Example |
|--------|---------|---------|
| `bulk_transition.py` | Move issues to new status | `--jql "..." --to "Done"` |
| `bulk_assign.py` | Assign issues to user | `--jql "..." --assignee john` |
| `bulk_set_priority.py` | Set issue priority | `--jql "..." --priority High` |
| `bulk_clone.py` | Clone issues | `--jql "..." --include-subtasks` |

For help choosing, see [Operations Guide](docs/OPERATIONS_GUIDE.md).

## Common Options

All scripts support these options:

| Option | Purpose | When to Use |
|--------|---------|-------------|
| `--dry-run` | Preview changes | Always use for >10 issues |
| `--profile` | JIRA instance | Multi-environment setups |
| `--max-issues N` | Limit scope | Testing, large operations |
| `--batch-size N` | Control batching | 500+ issues or rate limits |
| `--enable-checkpoint` | Allow resume | 500+ issues, unreliable network |
| `--delay-between-ops N` | Throttle requests | Rate limit (429) errors |

## Examples

### Bulk Transition

```bash
# By issue keys
jira bulk transition --issues PROJ-1,PROJ-2,PROJ-3 --to "Done"

# By JQL query
jira bulk transition --jql "project=PROJ AND status='In Progress'" --to "Done"

# With resolution
jira bulk transition --jql "type=Bug AND status='Verified'" --to "Closed" --resolution "Fixed"
```

### Bulk Assign

```bash
# Assign to user
jira bulk assign --jql "project=PROJ AND status=Open" --assignee "john.doe"

# Assign to self
jira bulk assign --jql "project=PROJ AND assignee IS EMPTY" --assignee self

# Unassign
jira bulk assign --jql "assignee=john.leaving" --unassign
```

### Bulk Set Priority

```bash
jira bulk set-priority --jql "type=Bug AND labels=critical" --priority Highest
```

### Bulk Clone

```bash
# Clone with subtasks and links
jira bulk clone --jql "sprint='Sprint 42'" --include-subtasks --include-links

# Clone to different project
jira bulk clone --issues PROJ-1,PROJ-2 --target-project NEWPROJ --prefix "[Clone]"
```

## Parameter Tuning Guide

**How many issues?**

| Issue Count | Recommended Setup |
|-------------|-------------------|
| <50 | Defaults are fine |
| 50-500 | `--dry-run` first, then execute |
| 500-1,000 | `--batch-size 200 --enable-checkpoint` |
| 1,000+ | `--batch-size 200 --enable-checkpoint --delay-between-ops 0.3` |

**Getting rate limit (429) errors?**
- Increase delay: `--delay-between-ops 0.5`
- Reduce batch: `--batch-size 50`
- Or both

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All operations successful |
| 1 | Some failures or validation error |
| 130 | Cancelled by user (Ctrl+C) |

## Troubleshooting

| Error | Solution |
|-------|----------|
| `Transition not available` | Check issue status with `get_issue.py --show-transitions` |
| `Permission denied` | Verify JIRA project permissions |
| `Rate limit (429)` | Increase `--delay-between-ops` or reduce `--batch-size` |
| `Invalid JQL` | Test JQL in JIRA search first |

For detailed error recovery, see [Error Recovery Playbook](docs/ERROR_RECOVERY.md).

## Documentation

| Guide | When to Use |
|-------|-------------|
| [Quick Start](docs/QUICK_START.md) | Get started in 5 minutes |
| [Operations Guide](docs/OPERATIONS_GUIDE.md) | Choose the right script |
| [Checkpoint Guide](docs/CHECKPOINT_GUIDE.md) | Resume interrupted operations |
| [Error Recovery](docs/ERROR_RECOVERY.md) | Handle failures |
| [Safety Checklist](docs/SAFETY_CHECKLIST.md) | Pre-flight verification |
| [Best Practices](docs/BEST_PRACTICES.md) | Comprehensive guidance |

## Related Skills

- **jira-lifecycle**: Single-issue transitions and workflow
- **jira-search**: Find issues with JQL queries
- **jira-issue**: Create and update single issues
