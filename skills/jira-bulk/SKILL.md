---
name: "jira-bulk-operations"
description: "Bulk operations for multiple issues at scale. TRIGGERS: 'bulk update', 'bulk close', 'bulk transition', 'bulk assign', 'transition N issues' (N >= 10), 'update all bugs', 'close 50 issues', 'mass transition', 'update multiple issues', quantities like '50 issues', '100 bugs', '20+ tickets'. Use for operations on 10+ issues. NOT FOR: single issue transitions (use jira-lifecycle), searching only without modifications (use jira-search), single issue field updates (use jira-issue)."
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
- 5-10 issues: Preview (default behavior), then re-run with `--yes`
- 50-100 issues: Use `--dry-run` first, then execute with `--yes`
- 500+ issues: Use `--dry-run`, then execute in smaller batches if needed

## Quick Start

```bash
# Preview before making changes (bulk commands run as a preview by default)
jira-as bulk transition --jql "project=PROJ AND status=\"In Progress\"" --to Done --dry-run

# Execute the transition (--yes is required to apply changes)
jira-as bulk transition --jql "project=PROJ AND status=\"In Progress\"" --to Done --yes
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
| `-q/--jql QUERY` | Select issues by JQL | Mutually exclusive with `--issues` |
| `-i/--issues KEYS` | Comma-separated issue keys | Mutually exclusive with `--jql` |
| `-n/--dry-run` | Preview changes | Always use for >10 issues |
| `-y/--yes` | Apply changes (without it, the command only previews) | Required to execute any bulk change |
| `-m/--max-issues N` | Limit scope (default: 100) | Testing, large operations |
| `-o/--output FORMAT` | Output format: text (default), json | JSON for scripting |

### Transition-Only Options

These options are only available for `jira-as bulk transition`:

| Option | Purpose | When to Use |
|--------|---------|-------------|
| `--comment` / `-c` | Add comment with transition | Documenting bulk changes |
| `--resolution` / `-r` | Set resolution (e.g., Fixed) | Closing issues |

## Examples

### Bulk Transition

```bash
# By issue keys
jira-as bulk transition --issues PROJ-1,PROJ-2,PROJ-3 --to Done --yes

# By JQL query
jira-as bulk transition --jql "project=PROJ AND status=\"In Progress\"" --to Done --yes

# With resolution
jira-as bulk transition --jql "type=Bug AND status=Verified" --to Closed --resolution Fixed --yes
```

### Bulk Assign

```bash
# Assign to user
jira-as bulk assign --jql "project=PROJ AND status=Open" --assignee "john.doe" --yes

# Assign to self
jira-as bulk assign --jql "project=PROJ AND assignee IS EMPTY" --assignee self --yes

# Unassign
jira-as bulk assign --jql "assignee=john.leaving" --unassign --yes
```

### Bulk Set Priority

```bash
jira-as bulk set-priority --jql "type=Bug AND labels=critical" --priority Highest --yes

# Output as JSON
jira-as bulk set-priority --jql "type=Bug" --priority High --dry-run -o json
```

### Bulk Clone

```bash
# ALWAYS preview first with dry-run (cloning creates many issues)
jira-as bulk clone --jql "sprint=\"Sprint 42\"" --include-subtasks --dry-run

# After reviewing the preview, execute with --yes
jira-as bulk clone --jql "sprint=\"Sprint 42\"" --include-subtasks --include-links --yes

# Clone to different project
jira-as bulk clone --issues PROJ-1,PROJ-2 --target-project MYAPP --prefix "[Clone]" --yes
```

### Bulk Delete (DESTRUCTIVE)

```bash
# ALWAYS preview first with dry-run
jira-as bulk delete --jql "project=CLEANUP" --dry-run

# Delete by issue keys (preview first)
jira-as bulk delete --issues DEMO-1,DEMO-2,DEMO-3 --dry-run

# Execute deletion (after confirming dry-run output)
jira-as bulk delete --jql "project=CLEANUP" --yes

# Keep subtasks when deleting parent issues (subtasks deleted by default)
jira-as bulk delete --jql "project=CLEANUP" --no-subtasks --dry-run
```

**Safety features:**
- `--dry-run` shows exactly what will be deleted before making changes
- Without `--yes`, every run is a preview - `--yes` is required to actually delete (a warning is printed first)
- Default `--max-issues 100` prevents accidental mass deletion
- Per-issue error tracking with summary of failures

## Scale Recommendations

| Issue Count | Recommended Approach |
|-------------|----------------------|
| <50 | Defaults are fine |
| 50-500 | `--dry-run` first, then execute |
| 500+ | `--dry-run`, then execute in smaller batches if needed |

**Getting rate limit (429) errors?**
- Use `--max-issues` to process in smaller batches
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
| `Transition not available` | Check available transitions with `jira-as lifecycle transitions ISSUE-KEY` |
| `Permission denied` | Verify JIRA project permissions (DELETE_ISSUES required for bulk delete) |
| `Rate limit (429)` | Use `--max-issues` to process in smaller batches or run during off-peak hours |
| `Invalid JQL` | Test JQL in JIRA search first |
| `Cannot delete issue with subtasks` | Subtasks are deleted by default; use `--no-subtasks` to keep them |

For detailed error recovery, see [Error Recovery Playbook](docs/ERROR_RECOVERY.md).

## Documentation

| Guide | When to Use |
|-------|-------------|
| [Quick Start](docs/QUICK_START.md) | Get started in 5 minutes |
| [Operations Guide](docs/OPERATIONS_GUIDE.md) | Choose the right command |
| [Error Recovery](docs/ERROR_RECOVERY.md) | Handle failures |
| [Safety Checklist](docs/SAFETY_CHECKLIST.md) | Pre-flight verification |
| [Best Practices](docs/BEST_PRACTICES.md) | Comprehensive guidance |

## Related Skills

- **jira-lifecycle**: Single-issue transitions and workflow
- **jira-search**: Find issues with JQL queries
- **jira-issue**: Create and update single issues
