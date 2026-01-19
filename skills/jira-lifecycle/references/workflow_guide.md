# JIRA Workflow Guide

**Use this guide when:** Understanding standard JIRA workflows, designing transitions, managing resolution.

**Not for:** Service Management workflows (see [jsm_workflows.md](jsm_workflows.md)).

**Audience:** Developers, team leads, anyone working with standard JIRA.

---

## Overview

JIRA workflows define the lifecycle of issues through different statuses. Each workflow consists of:
- **Statuses**: States an issue can be in (e.g., To Do, In Progress, Done)
- **Transitions**: Actions that move issues between statuses
- **Conditions**: Rules that determine who can execute transitions
- **Validators**: Checks performed before a transition executes
- **Post Functions**: Actions performed after a transition completes

## Standard JIRA Workflow

### Default Workflow States

```
To Do → In Progress → Done
  ↓          ↓          ↓
  └──────────┴──────────→ (Reopen transitions)
```

**Common Statuses:**
- **To Do** - Issue is created, not started
- **In Progress** - Work has begun
- **Done** - Work is completed

### Common Transitions

| From | To | Transition Name |
|------|----|----|
| To Do | In Progress | Start Progress |
| In Progress | Done | Done |
| In Progress | To Do | Stop Progress |
| Done | To Do | Reopen |
| Done | In Progress | Reopen |

## Working with Transitions

### Viewing Available Transitions

```bash
# List all available transitions for an issue
python get_transitions.py PROJ-123
```

Output:
```
Available transitions for PROJ-123:

ID    Name             To Status
---   ---------------- -----------
11    Start Progress   In Progress
21    Done             Done
31    Won't Do         Done
```

### Executing Transitions

**By Transition Name:**
```bash
python transition_issue.py PROJ-123 --name "In Progress"
```

**By Transition ID:**
```bash
python transition_issue.py PROJ-123 --id 11
```

**With Additional Fields:**
```bash
python transition_issue.py PROJ-123 --name "Done" --resolution "Fixed"
```

### Transition Name Matching

The scripts support flexible transition name matching:

1. **Exact Match** (case-insensitive):
   - `--name "done"` matches "Done"
   - `--name "IN PROGRESS"` matches "In Progress"

2. **Partial Match**:
   - `--name "progress"` matches "In Progress" or "Start Progress"
   - `--name "start"` matches "Start Progress"

3. **Ambiguous Matches**:
   - If multiple transitions match, you'll get an error listing all matches
   - Use a more specific name or use transition ID instead

## Resolution Field

When transitioning to Done/Closed, you typically need to set a resolution.

### Common Resolution Values

- **Fixed** - Issue was fixed
- **Won't Fix** - Issue won't be addressed
- **Duplicate** - Duplicate of another issue
- **Cannot Reproduce** - Unable to reproduce the issue
- **Won't Do** - Decided not to do this
- **Done** - Completed as requested

### Setting Resolution

```bash
# Resolve as Fixed
python resolve_issue.py PROJ-123 --resolution "Fixed"

# Resolve as Won't Fix with comment
python resolve_issue.py PROJ-123 --resolution "Won't Fix" --comment "Working as intended"
```

## Custom Workflows

Many JIRA instances use custom workflows with additional statuses and transitions.

### Example: Software Development Workflow

```
Backlog → Selected for Development → In Progress → In Review → In Testing → Done
   ↓              ↓                      ↓            ↓            ↓         ↓
   └──────────────┴──────────────────────┴────────────┴────────────┴─────────→ Rejected
```

### Handling Custom Workflows

The scripts automatically work with custom workflows:

1. **View available transitions** to see what's possible
2. **Use transition names** that match your workflow
3. **Check required fields** if a transition fails

### Required Fields During Transitions

Some transitions require additional fields:

```bash
# If a transition requires a comment
python transition_issue.py PROJ-123 --name "Approve" --comment "LGTM"

# If a transition requires custom fields
python transition_issue.py PROJ-123 --name "Deploy" --fields '{"customfield_10001": "Production"}'
```

## Assignment During Workflow

### Assigning Issues

```bash
# Assign to specific user
python assign_issue.py PROJ-123 --user user@example.com

# Assign to yourself
python assign_issue.py PROJ-123 --self

# Unassign
python assign_issue.py PROJ-123 --unassign
```

### Auto-Assignment

Some workflows have auto-assignment rules:
- Issue automatically assigned when transitioned to "In Progress"
- Issue assigned to reporter when reopened
- Issue assigned to project lead when escalated

These are configured in JIRA and happen automatically.

## Workflow Conditions

Transitions may have conditions that restrict who can execute them:

### Common Conditions

- **Assignee** - Only the assignee can execute
- **Reporter** - Only the reporter can execute
- **Project Role** - Only users with specific role (e.g., Developer, Admin)
- **Permission** - Requires specific permission
- **Field Value** - Requires a field to have a specific value

### Handling Conditions

If you can't execute a transition:
1. Check you have the required permissions
2. Verify you're the assignee/reporter if required
3. Contact your JIRA admin to adjust workflow conditions

## Validators

Validators check that requirements are met before executing a transition:

### Common Validators

- **Field Required** - Specific field must have a value
- **User in Group** - User must be in specific group
- **Permission** - User must have specific permission
- **Subtasks** - All subtasks must be closed
- **Time Logged** - Time must be logged

### Validation Errors

If a transition fails validation:
```
Failed to transition issue PROJ-123: Field 'Fix Version' is required
```

Solution: Provide the required field
```bash
python transition_issue.py PROJ-123 --name "Done" \
  --fields '{"fixVersions": [{"name": "1.0"}]}'
```

## Post Functions

Post functions execute after a successful transition:

### Common Post Functions

- **Update Field** - Automatically set a field value
- **Assign Issue** - Automatically assign to a user
- **Create Issue** - Create a linked issue
- **Fire Event** - Trigger notifications
- **Update Parent** - Update parent issue status

These happen automatically and don't require any action from you.

## Reopening Issues

### Standard Reopen

```bash
python reopen_issue.py PROJ-123
```

The script automatically finds the appropriate reopen transition.

### With Comment

```bash
python reopen_issue.py PROJ-123 --comment "Regression found in version 2.0"
```

### Reopen Workflow Variations

Different JIRA instances may have different reopen transitions:
- **Reopen** - Returns to "Open" or "To Do"
- **Backlog** - Returns to "Backlog"
- **To Do** - Explicitly moves to "To Do" status

The script tries to find the most appropriate transition automatically.

## Best Practices

1. **Check Available Transitions First**
   ```bash
   python get_transitions.py PROJ-123
   ```

2. **Use Descriptive Comments**
   - When transitioning, explain why
   - Helps team understand issue history

3. **Set Resolution Appropriately**
   - Use correct resolution values
   - Be consistent across team

4. **Respect Workflow Intent**
   - Don't skip steps in workflow
   - Follow your team's process

5. **Handle Errors Gracefully**
   - If transition fails, check error message
   - Verify required fields are set
   - Ensure you have permissions

## Troubleshooting

### Transition Not Available

**Problem:** The transition you want isn't listed

**Solutions:**
- Check current status allows this transition
- Verify you have required permissions
- Confirm you're the assignee if required
- Check workflow conditions with JIRA admin

### Required Field Error

**Problem:** "Field X is required"

**Solution:**
```bash
python transition_issue.py PROJ-123 --name "Done" \
  --fields '{"customfield_10001": "value"}'
```

### Permission Denied

**Problem:** "User does not have permission"

**Solutions:**
- Check your project role
- Verify workflow conditions
- Contact JIRA admin for access

### Resolution Not Set

**Problem:** Issue transitioned but resolution is empty

**Solution:** Use the specific scripts:
```bash
# Instead of generic transition
python resolve_issue.py PROJ-123 --resolution "Fixed"
```

## API References

- [Transitions API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-transitions-get)
- [Workflow Schemes](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflow-schemes/)
- [Issue Assignment](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-assignee-put)
