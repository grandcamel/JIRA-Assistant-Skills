---
name: "JIRA Bulk Operations"
description: "High-performance bulk operations at scale - transitions, assignments, priorities, cloning with progress tracking. Use when transitioning multiple issues, bulk assigning, or cloning with dry-run preview."
---

# jira-bulk

Bulk operations for JIRA issue management at scale - transitions, assignments, priorities, and cloning.

## When to use this skill

Use this skill when you need to:
- Transition multiple issues through workflow states simultaneously
- Assign multiple issues to a user (or unassign)
- Set priority on multiple issues at once
- Clone issues with their subtasks and links
- Perform any bulk operation with progress tracking
- Execute dry-run previews before making changes
- Handle partial failures gracefully

## What this skill does

This skill provides high-performance bulk operations:

1. **Bulk Transition**: Transition multiple issues to a new status
   - Supports issue keys or JQL queries
   - Optional resolution setting
   - Optional comment during transition
   - Dry-run preview mode
   - Progress tracking and rate limiting

2. **Bulk Assign**: Assign multiple issues to a user
   - Assign to specific user by account ID or email
   - Assign to self using 'self' keyword
   - Unassign issues
   - JQL-based selection

3. **Bulk Set Priority**: Set priority on multiple issues
   - Standard priorities (Highest, High, Medium, Low, Lowest)
   - JQL-based selection
   - Dry-run preview

4. **Bulk Clone**: Clone issues with options
   - Include subtasks
   - Include issue links
   - Clone to different project
   - Add prefix to cloned summaries
   - Dry-run preview

## Available scripts

### Core Bulk Operations
- `bulk_transition.py` - Transition multiple issues to new status
- `bulk_assign.py` - Assign multiple issues to user
- `bulk_set_priority.py` - Set priority on multiple issues
- `bulk_clone.py` - Clone issues with subtasks and links

## Examples

```bash
# Bulk Transition
python bulk_transition.py --issues PROJ-1,PROJ-2,PROJ-3 --to "Done"
python bulk_transition.py --jql "project=PROJ AND status='In Progress'" --to "Done"
python bulk_transition.py --jql "project=PROJ AND type=Bug" --to "Done" --resolution "Fixed"
python bulk_transition.py --issues PROJ-1,PROJ-2 --to "In Review" --comment "Ready for review"
python bulk_transition.py --jql "project=PROJ" --to "Done" --dry-run
python bulk_transition.py --profile staging --jql "sprint=123" --to "Done"

# Bulk Assign
python bulk_assign.py --issues PROJ-1,PROJ-2 --assignee "john.doe"
python bulk_assign.py --jql "project=PROJ AND status=Open" --assignee self
python bulk_assign.py --jql "project=PROJ AND assignee=john" --unassign
python bulk_assign.py --issues PROJ-1 --assignee "john@company.com" --dry-run
python bulk_assign.py --profile staging --jql "project=TEST" --assignee self

# Bulk Set Priority
python bulk_set_priority.py --issues PROJ-1,PROJ-2 --priority High
python bulk_set_priority.py --jql "project=PROJ AND type=Bug" --priority Blocker
python bulk_set_priority.py --jql "labels=urgent" --priority Highest --dry-run
python bulk_set_priority.py --profile staging --issues PROJ-1 --priority Low

# Bulk Clone
python bulk_clone.py --issues PROJ-1,PROJ-2 --include-subtasks
python bulk_clone.py --issues PROJ-1,PROJ-2 --include-links
python bulk_clone.py --issues PROJ-1,PROJ-2 --target-project NEWPROJ
python bulk_clone.py --issues PROJ-1,PROJ-2 --prefix "[Clone]"
python bulk_clone.py --jql "sprint=123" --include-subtasks --include-links
python bulk_clone.py --jql "project=PROJ" --dry-run
```

## Common Options

All scripts support:
- `--profile` - JIRA profile for multi-instance support
- `--dry-run` - Preview changes without making them
- `--max-issues` - Limit number of issues to process (default: 100)

## Advanced Features

### Batch Processing

For large operations (500+ issues), use batch processing to improve reliability:

```bash
# Process in batches of 100 issues
python bulk_transition.py --jql "project=PROJ" --to "Done" --batch-size 100

# Auto-calculated batch size (recommended for very large operations)
python bulk_transition.py --jql "project=PROJ" --to "Done" --max-issues 5000
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--batch-size` | Auto-calculated | Number of issues to process per batch |
| `--max-issues` | 10000 | Maximum total issues to process |

### Checkpoint and Resume

For very large or critical operations, enable checkpointing to allow resumption after interruption:

```bash
# Enable checkpointing for a large operation
python bulk_transition.py --jql "project=PROJ" --to "Done" --enable-checkpoint

# List all pending checkpoints
python bulk_transition.py --list-checkpoints

# Resume an interrupted operation
python bulk_transition.py --resume transition-20231215-143022 --to "Done"
```

| Parameter | Description |
|-----------|-------------|
| `--enable-checkpoint` | Save progress to allow resumption if operation is interrupted |
| `--list-checkpoints` | Show all pending checkpoints that can be resumed |
| `--resume <operation-id>` | Resume a previously interrupted operation by its ID |

Checkpoints are stored in `~/.jira-skills/checkpoints/` and contain:
- Operation ID (timestamp-based identifier)
- Progress percentage and counts
- List of processed issue keys
- Start and last update timestamps

## Rate Limiting

Bulk operations automatically respect JIRA API rate limits:
- Built-in delay between operations
- Exponential backoff on rate limit errors
- Configurable batch sizes

## Partial Failure Handling

When some operations fail:
- Continues processing remaining issues
- Reports success/failure counts
- Detailed error messages for failed items
- Non-zero exit code if any failures

## Configuration

Uses shared configuration from `.claude/settings.json` and `.claude/settings.local.json`.
Requires JIRA credentials via environment variables or settings files.

## Return Values and Exit Codes

### Exit Codes

All bulk scripts use the following exit codes:

| Exit Code | Meaning |
|-----------|---------|
| 0 | All operations completed successfully |
| 1 | One or more operations failed, or validation/configuration error |
| 130 | Operation cancelled by user (Ctrl+C) |

### Return Dictionary Structure

When using bulk functions programmatically, they return a dictionary with:

```python
{
    'success': 5,          # Number of successful operations
    'failed': 2,           # Number of failed operations
    'total': 7,            # Total issues processed
    'errors': {            # Map of issue_key -> error message
        'PROJ-3': 'Transition not available',
        'PROJ-5': 'Permission denied'
    },
    'processed': ['PROJ-1', 'PROJ-2', ...]  # Successfully processed issue keys
}
```

For dry-run mode, the return includes:

```python
{
    'dry_run': True,
    'would_process': 10,   # Number of issues that would be processed
    'success': 0,
    'failed': 0,
    'total': 10,
    'errors': {},
    'processed': []
}
```

## Rate Limiting and Delays

### delay_between_ops Parameter

All bulk operations support a `delay_between_ops` parameter that controls the pause between individual API calls:

```python
# Python API usage
from bulk_transition import bulk_transition

result = bulk_transition(
    issue_keys=['PROJ-1', 'PROJ-2', 'PROJ-3'],
    target_status='Done',
    delay_between_ops=0.5  # 500ms delay between each transition
)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `delay_between_ops` | `0.1` (100ms) | Seconds to wait between processing each issue |

**When to adjust:**
- **Increase** (0.5-1.0s) for large batches or rate-limited instances
- **Decrease** (0.0) for small batches when speed is critical
- **Default** (0.1s) works well for most scenarios

### Built-in Rate Limiting

In addition to `delay_between_ops`, the underlying JIRA client automatically:
- Retries on HTTP 429 (Rate Limit) with exponential backoff
- Retries on 5xx server errors (500, 502, 503, 504)
- Uses up to 3 retry attempts with increasing delays

## Troubleshooting

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Transition not available` | Issue is not in a state that allows the target transition | Check the issue's current status and available transitions with `get_issue.py --show-transitions` |
| `Permission denied` | User lacks permission to perform the operation | Verify JIRA permissions for the project/issue type |
| `Rate limit exceeded (429)` | Too many API requests | Increase `delay_between_ops` or reduce `--batch-size` |
| `Issue not found` | Issue key doesn't exist or user can't access it | Verify issue keys and project access |
| `Invalid JQL` | Malformed JQL query | Test the JQL in JIRA's issue search first |
| `Resolution not found` | Invalid resolution name | Check available resolutions in project settings |

### Timeout Issues

For very large operations that may timeout:

```bash
# Use smaller batch sizes
python bulk_transition.py --jql "project=PROJ" --to "Done" --batch-size 50

# Enable checkpointing to allow resume after timeout
python bulk_transition.py --jql "project=PROJ" --to "Done" --enable-checkpoint --batch-size 50
```

### Partial Failures

When operations partially fail:

1. Review the error summary at the end of execution
2. The `errors` dictionary contains issue-specific failure reasons
3. Use `--dry-run` first to identify potential issues before executing
4. Consider running failed issues in a separate batch after fixing the underlying issue

### Confirmation Prompts

Operations affecting more than 50 issues will prompt for confirmation:

```bash
# Skip confirmation (use with caution)
python bulk_transition.py --jql "project=PROJ" --to "Done" --yes
```

## Best Practices

For comprehensive guidance on bulk operation patterns, dry-run strategies, and batch processing optimization, see [Best Practices Guide](docs/BEST_PRACTICES.md).

## Related skills

- **jira-lifecycle**: For single-issue transitions and assignments
- **jira-search**: For finding issues with JQL
- **jira-issue**: For creating and updating single issues
