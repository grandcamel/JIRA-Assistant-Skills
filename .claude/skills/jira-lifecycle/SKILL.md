---
name: "JIRA Lifecycle Management"
description: "Workflow and lifecycle management for JIRA issues - transitions, assignments, versions, components. Use when transitioning issues, assigning users, managing versions, or handling components."
---

# jira-lifecycle

Workflow and lifecycle management for JIRA issues - transitions, assignments, and status changes.

## When to use this skill

Use this skill when you need to:
- Transition issues through workflow states (To Do -> In Progress -> Done)
- Assign or reassign issues to team members
- Resolve issues with resolution fields
- Reopen closed issues
- View available transitions for an issue
- Manage issue lifecycle and status
- Create and manage project versions
- Release and archive versions
- Create and manage project components
- Move issues between versions

## What this skill does

This skill provides workflow and lifecycle management operations:

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

6. **Version Management**: Create and manage project versions
   - Create versions with start/release dates
   - Release versions with descriptions
   - Archive old versions
   - Move issues between versions
   - View version details and issue counts
   - Filter by released/unreleased/archived status

7. **Component Management**: Create and manage project components
   - Create components with lead and assignee type
   - Update component details
   - Delete components with optional issue migration
   - View component details and issue counts
   - Filter components by lead

## Available scripts

### Workflow Transitions
- `get_transitions.py` - List available transitions for an issue
- `transition_issue.py` - Transition issue to new status
- `assign_issue.py` - Assign or reassign issues
- `resolve_issue.py` - Resolve issues with resolution
- `reopen_issue.py` - Reopen closed issues

### Version Management
- `create_version.py` - Create project version with dates
- `get_versions.py` - List versions with issue counts
- `release_version.py` - Release version with date/description
- `archive_version.py` - Archive old version
- `move_issues_version.py` - Move issues between versions (supports `--dry-run`)

### Component Management
- `create_component.py` - Create project component
- `get_components.py` - List components with issue counts
- `update_component.py` - Update component details
- `delete_component.py` - Delete component with confirmation (supports `--dry-run`)

## Common Options

All scripts in this skill support these common options:

| Option | Description |
|--------|-------------|
| `--profile PROFILE` | Use a specific JIRA profile from settings (e.g., `development`, `production`) |
| `--format FORMAT` | Output format: `table`, `json`, or `csv` (default: `table`) |
| `--output FILE` | Write output to file instead of stdout |
| `--help` | Show help message and exit |

### Dry Run Support

The following scripts support `--dry-run` to preview changes without executing:

| Script | Dry Run Behavior |
|--------|------------------|
| `move_issues_version.py` | Shows which issues would be moved without modifying them |
| `delete_component.py` | Shows what would be deleted without removing the component |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - operation completed successfully |
| 1 | Error - operation failed (check stderr for details) |

## Examples

```bash
# Workflow Transitions
python get_transitions.py PROJ-123
python transition_issue.py PROJ-123 --name "In Progress"
python transition_issue.py PROJ-123 --name "In Progress" --sprint 42
python transition_issue.py PROJ-123 --id 31
python assign_issue.py PROJ-123 --user user@example.com
python assign_issue.py PROJ-123 --self
python assign_issue.py PROJ-123 --unassign
python resolve_issue.py PROJ-123 --resolution Fixed
python reopen_issue.py PROJ-123

# Version Management
python create_version.py PROJ --name "v1.0.0" --start-date 2025-01-01 --release-date 2025-03-01
python get_versions.py PROJ --format table
python get_versions.py PROJ --released --format json
python release_version.py PROJ --name "v1.0.0" --date 2025-03-15
python archive_version.py PROJ --name "v0.9.0"
python move_issues_version.py --jql "fixVersion = v1.0.0" --target "v1.1.0"
python move_issues_version.py --jql "project = PROJ AND status = Done" --target "v1.0.0" --dry-run

# Component Management
python create_component.py PROJ --name "Backend API" --description "Server-side components"
python create_component.py PROJ --name "UI" --lead accountId123 --assignee-type COMPONENT_LEAD
python get_components.py PROJ --format table
python get_components.py PROJ --id 10000
python update_component.py --id 10000 --name "New Name" --description "Updated"
python delete_component.py --id 10000 --dry-run
python delete_component.py --id 10000 --move-to 10001

# Using profiles
python transition_issue.py PROJ-123 --name "Done" --profile production
python get_versions.py PROJ --profile development --format json
```

## Workflow Compatibility

Works with:
- Standard JIRA workflows
- Custom workflows
- JIRA Service Management workflows
- Simplified workflows

The scripts automatically adapt to different workflow configurations.

## Troubleshooting

### Common Issues

#### "No transition found" error
- **Cause**: The requested transition is not available from the current issue status
- **Solution**: Run `get_transitions.py ISSUE-KEY` to see available transitions from the current status
- **Note**: Workflows may require issues to pass through intermediate states

#### "Transition requires fields" error
- **Cause**: The transition has mandatory fields that must be set
- **Solution**: Use the `--fields` option to provide required field values, or check the transition configuration in JIRA admin

#### "User not found" when assigning
- **Cause**: The user email or account ID is incorrect or the user lacks project access
- **Solution**: Verify the user exists in JIRA and has the necessary project permissions

#### "Cannot resolve issue" error
- **Cause**: The issue is not in a state that allows resolution, or resolution field is not configured
- **Solution**: Transition the issue to an appropriate status first, or check project workflow configuration

#### "Version already exists" error
- **Cause**: A version with the same name already exists in the project
- **Solution**: Use a different version name or update the existing version

#### "Component in use" when deleting
- **Cause**: Issues are assigned to the component being deleted
- **Solution**: Use `--move-to COMPONENT_ID` to migrate issues to another component before deletion

### Debugging Tips

1. **Check current status**: Use `get_transitions.py` to understand available workflow paths
2. **Use dry-run first**: For bulk operations, always test with `--dry-run` before executing
3. **Verify permissions**: Ensure your JIRA account has transition/assignment permissions for the project
4. **Check workflow restrictions**: Some transitions may be restricted by conditions (e.g., only assignee can resolve)

## Configuration

Uses shared configuration from `.claude/settings.json` and `.claude/settings.local.json`.
Requires JIRA credentials via environment variables or settings files.

## Related skills

- **jira-issue**: For creating and updating issues
- **jira-search**: For finding issues to transition
- **jira-collaborate**: For adding comments during transitions
- **jira-agile**: For sprint management and Agile workflows
