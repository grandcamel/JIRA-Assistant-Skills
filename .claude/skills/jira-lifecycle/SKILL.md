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
- `move_issues_version.py` - Move issues between versions

### Component Management
- `create_component.py` - Create project component
- `get_components.py` - List components with issue counts
- `update_component.py` - Update component details
- `delete_component.py` - Delete component with confirmation

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
