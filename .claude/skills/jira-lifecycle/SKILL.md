# jira-lifecycle

Workflow and lifecycle management for JIRA issues - transitions, assignments, and status changes.

## When to use this skill

Use this skill when you need to:
- Transition issues through workflow states (To Do → In Progress → Done)
- Assign or reassign issues to team members
- Resolve issues with resolution fields
- Reopen closed issues
- View available transitions for an issue
- Manage issue lifecycle and status

## What this skill does

This skill provides workflow management operations:

1. **Get Transitions**: View available transitions for an issue
   - Lists all valid status changes
   - Shows transition IDs and target statuses
   - Identifies required fields for each transition

2. **Transition Issues**: Move issues through workflow states
   - Smart transition matching (by name or ID)
   - Set fields during transition (resolution, comment, etc.)
   - Handle transition-specific required fields
   - Support for custom workflows
   - Optional sprint assignment during transition

3. **Assign Issues**: Assign or reassign issues
   - Assign to specific users
   - Unassign issues
   - Assign to self
   - Support for both account ID and email

4. **Resolve Issues**: Mark issues as resolved/done
   - Set resolution field (Fixed, Won't Fix, Duplicate, etc.)
   - Automatically finds correct transition
   - Optional resolution comment

5. **Reopen Issues**: Reopen closed or resolved issues
   - Finds appropriate reopen transition
   - Handles different workflow configurations

## Available scripts

- `get_transitions.py` - List available transitions for an issue
- `transition_issue.py` - Transition issue to new status
- `assign_issue.py` - Assign or reassign issues
- `resolve_issue.py` - Resolve issues with resolution
- `reopen_issue.py` - Reopen closed issues

## Examples

```bash
# View available transitions
python get_transitions.py PROJ-123

# Transition to In Progress
python transition_issue.py PROJ-123 --name "In Progress"

# Transition and move to sprint in one operation
python transition_issue.py PROJ-123 --name "In Progress" --sprint 42

# Transition by ID
python transition_issue.py PROJ-123 --id 31

# Assign to user
python assign_issue.py PROJ-123 --user user@example.com

# Assign to self
python assign_issue.py PROJ-123 --self

# Unassign
python assign_issue.py PROJ-123 --unassign

# Resolve as Fixed
python resolve_issue.py PROJ-123 --resolution Fixed

# Reopen issue
python reopen_issue.py PROJ-123
```

## Workflow Compatibility

Works with:
- Standard JIRA workflows
- Custom workflows
- JIRA Service Management workflows
- Simplified workflows

The scripts automatically adapt to different workflow configurations.

## Configuration

Uses shared configuration from `.claude/settings.json` and `.claude/settings.local.json`.
Requires JIRA credentials via environment variables or settings files.

## Related skills

- **jira-issue**: For creating and updating issues
- **jira-search**: For finding issues to transition
- **jira-collaborate**: For adding comments during transitions
- **jira-agile**: For sprint management and Agile workflows
