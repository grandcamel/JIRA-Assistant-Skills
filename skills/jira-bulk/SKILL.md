---
name: "jira-bulk-operations"
description: "Bulk operations for 50+ issues - transitions, assignments, priorities, cloning, and deletion. Use when: updating multiple issues simultaneously (dry-run preview included), needing rollback safety, or coordinating team changes. Handles partial failures gracefully."
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# jira-bulk

Bulk operations for JIRA issue management at scale - transitions, assignments, priorities, cloning, and deletion.

## Risk Levels

| Operation | Risk | Notes |
|-----------|------|-------|
| Dry-run any operation | `-` | Preview only, no changes |
| Bulk transition | `!!` | Affects many issues; use --dry-run first |
| Bulk assign | `!!` | Affects many issues; use --dry-run first |
| Bulk set-priority | `!!` | Affects many issues; use --dry-run first |
| Bulk clone | `!` | Creates many issues; can delete |
| Bulk delete | `!!!` | **IRREVERSIBLE** - issues permanently lost |

**Risk Legend**: `-` Safe, read-only | `!` Caution, modifiable | `!!` Warning, destructive but recoverable | `!!!` Danger, irreversible

**CRITICAL**: Always use `--dry-run` before executing bulk operations. Bulk delete is permanent and cannot be undone.

## When to use this skill

**IMPORTANT:** Always use the `jira-as` CLI. Never run Python scripts directly.

Use this skill when you need to:
- Transition **multiple issues** through workflow states simultaneously
- Assign **multiple issues** to a user (or unassign)
- Set priority on **multiple issues** at once
- Clone issues with their subtasks and links
- **Delete multiple issues** permanently (with dry-run preview)
- Execute operations with **dry-run preview** before making changes
- Handle **partial failures** gracefully with progress tracking

**Scale guidance:**
- 5-10 issues: Run directly, no special options needed
- 50-100 issues: Use `--dry-run` first, then execute
- 500+ issues (transitions only): Use `--batch-size` and `--enable-checkpoint` for reliability

## Quick Start

```bash
# Preview before making changes
jira-as bulk transition --jql "project=PROJ AND status='In Progress'" --to "Done" --dry-run

# Execute the transition
jira-as bulk transition --jql "project=PROJ AND status='In Progress'" --to "Done"
```

For more patterns, see [Quick Start Guide](docs/QUICK_START.md).

## Available Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `jira-as bulk transition` | Move issues to new status | `--jql "..." --to "Done"` |
| `jira-as bulk assign` | Assign issues to user | `--jql "..." --assignee john` |
| `jira-as bulk set-priority` | Set issue priority | `--jql "..." --priority High` |
| `jira-as bulk clone` | Clone issues | `--jql "..." --include-subtasks` |
| `jira-as bulk delete` | **Delete issues permanently** | `--jql "..." --dry-run` |

All commands support `--help` for full documentation.

## Common Options

All commands support these options:

| Option | Purpose | When to Use |
|--------|---------|-------------|
| `--dry-run` | Preview changes | Always use for >10 issues |
| `--force` / `-f` | Skip confirmation | Scripted automation |
| `--max-issues N` | Limit scope (default: 100) | Testing, large operations |

### Transition-Only Options

These options are only available for `jira-as bulk transition`:

| Option | Purpose | When to Use |
|--------|---------|-------------|
| `--batch-size N` | Control batching | 500+ issues or rate limits |
| `--enable-checkpoint` | Allow resume | 500+ issues, unreliable network |
| `--resume ID` | Resume from checkpoint | After interrupted operation |
| `--list-checkpoints` | List pending checkpoints | Before resuming |

## Examples

### Bulk Transition

```bash
# By issue keys
jira-as bulk transition --issues PROJ-1,PROJ-2,PROJ-3 --to "Done"

# By JQL query
jira-as bulk transition --jql "project=PROJ AND status='In Progress'" --to "Done"

# With resolution
jira-as bulk transition --jql "type=Bug AND status='Verified'" --to "Closed" --resolution "Fixed"
```

### Bulk Assign

```bash
# Assign to user
jira-as bulk assign --jql "project=PROJ AND status=Open" --assignee "john.doe"

# Assign to self
jira-as bulk assign --jql "project=PROJ AND assignee IS EMPTY" --assignee self

# Unassign
jira-as bulk assign --jql "assignee=john.leaving" --unassign
```

### Bulk Set Priority

```bash
jira-as bulk set-priority --jql "type=Bug AND labels=critical" --priority Highest
```

### Bulk Clone

```bash
# Clone with subtasks and links
jira-as bulk clone --jql "sprint='Sprint 42'" --include-subtasks --include-links

# Clone to different project
jira-as bulk clone --issues PROJ-1,PROJ-2 --target-project NEWPROJ --prefix "[Clone]"
```

### Bulk Delete (DESTRUCTIVE)

```bash
# ALWAYS preview first with dry-run
jira-as bulk delete --jql "project=CLEANUP" --dry-run

# Delete by issue keys (preview first)
jira-as bulk delete --issues DEMO-1,DEMO-2,DEMO-3 --dry-run

# Execute deletion (after confirming dry-run output)
jira-as bulk delete --jql "project=CLEANUP" --yes

# Delete without subtasks
jira-as bulk delete --jql "project=CLEANUP" --no-subtasks --dry-run
```

**Safety features:**
- `--dry-run` shows exactly what will be deleted before making changes
- Confirmation required for >10 issues (lower than other operations)
- Default `--max-issues 100` prevents accidental mass deletion
- Per-issue error tracking with summary of failures

## Parameter Tuning Guide (Transitions Only)

The batching and checkpointing features are only available for `jira-as bulk transition`.
Other commands (assign, set-priority, clone) process issues sequentially with built-in rate limiting.

**How many issues?**

| Issue Count | Recommended Setup |
|-------------|-------------------|
| <50 | Defaults are fine |
| 50-500 | `--dry-run` first, then execute |
| 500-1,000 | `--batch-size 200 --enable-checkpoint` |
| 1,000+ | `--batch-size 200 --enable-checkpoint` |

**Getting rate limit (429) errors?**
- Reduce batch size: `--batch-size 50`
- Consider running during off-peak hours

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All operations successful |
| 1 | Some failures or validation error |
| 130 | Cancelled by user (Ctrl+C) |

## Troubleshooting

| Error | Solution |
|-------|----------|
| `Transition not available` | Check issue status with `jira-as issue get ISSUE-KEY --show-transitions` |
| `Permission denied` | Verify JIRA project permissions (DELETE_ISSUES required for bulk delete) |
| `Rate limit (429)` | Reduce `--batch-size` or run during off-peak hours (transitions only) |
| `Invalid JQL` | Test JQL in JIRA search first |
| `Cannot delete issue with subtasks` | Use `--no-subtasks` or ensure subtask deletion is enabled (default) |

For detailed error recovery, see [Error Recovery Playbook](docs/ERROR_RECOVERY.md).

## Documentation

| Guide | When to Use |
|-------|-------------|
| [Quick Start](docs/QUICK_START.md) | Get started in 5 minutes |
| [Operations Guide](docs/OPERATIONS_GUIDE.md) | Choose the right command |
| [Checkpoint Guide](docs/CHECKPOINT_GUIDE.md) | Resume interrupted operations |
| [Error Recovery](docs/ERROR_RECOVERY.md) | Handle failures |
| [Safety Checklist](docs/SAFETY_CHECKLIST.md) | Pre-flight verification |
| [Best Practices](docs/BEST_PRACTICES.md) | Comprehensive guidance |

## Related Skills

- **jira-lifecycle**: Single-issue transitions and workflow
- **jira-search**: Find issues with JQL queries
- **jira-issue**: Create and update single issues
