# Lifecycle Management Troubleshooting

**Use this guide when:** Encountering errors with transitions, assignments, versions, or components.

**Not for:** JIRA authentication issues (see shared/SETUP.md) or search queries (see jira-search).

---

## Transition Errors

### "No transition found" error

**Cause:** The requested transition is not available from the current issue status.

**Solutions:**
1. Run `get_transitions.py ISSUE-KEY` to see available transitions
2. Check if the issue needs to pass through intermediate states
3. Verify your workflow allows this transition from current status

```bash
# View available transitions
python get_transitions.py PROJ-123

# Output shows what's possible from current status
```

### "Transition requires fields" error

**Cause:** The transition has mandatory fields that must be set.

**Solutions:**
1. Use the `--fields` option to provide required values
2. Check transition configuration in JIRA admin

```bash
# Provide required fields
python transition_issue.py PROJ-123 --name "Done" \
  --fields '{"resolution": {"name": "Fixed"}}'

# For custom fields
python transition_issue.py PROJ-123 --name "Deploy" \
  --fields '{"customfield_10001": "Production"}'
```

### "Permission denied" for transition

**Cause:** User lacks permission or doesn't meet workflow conditions.

**Solutions:**
1. Check your project role permissions
2. Verify you're the assignee/reporter if required by workflow
3. Contact JIRA admin to adjust workflow conditions

### Transition not appearing in list

**Cause:** Workflow conditions hiding the transition.

**Common conditions:**
- Only assignee can execute
- Only specific project roles
- Issue must have certain field values
- All subtasks must be closed

---

## Assignment Errors

### "User not found" when assigning

**Cause:** User email or account ID incorrect, or user lacks project access.

**Solutions:**
1. Verify the exact email address in JIRA
2. Check user has permission to be assigned issues in this project
3. Try using account ID instead of email

```bash
# Find correct user format
python assign_issue.py PROJ-123 --user john.doe@company.com

# Or use account ID
python assign_issue.py PROJ-123 --user 5b10ac8d82e05b22cc7d4ef5
```

### Cannot assign to yourself

**Cause:** Your user may not have assignment permissions.

**Solutions:**
1. Verify you have "Assignable User" permission in the project
2. Check project role permissions

---

## Resolution Errors

### "Cannot resolve issue" error

**Cause:** Issue not in a state that allows resolution, or resolution field not configured.

**Solutions:**
1. Transition to appropriate status first (often "In Progress" or "Done")
2. Check project workflow configuration
3. Verify resolution field is enabled for the issue type

```bash
# Check available transitions first
python get_transitions.py PROJ-123

# Then resolve
python resolve_issue.py PROJ-123 --resolution Fixed
```

### Resolution not set after transition

**Cause:** Transition doesn't set resolution automatically.

**Solution:** Use `resolve_issue.py` instead of `transition_issue.py`:

```bash
# This sets resolution properly
python resolve_issue.py PROJ-123 --resolution "Fixed"
```

---

## Version Errors

### "Version already exists" error

**Cause:** A version with the same name exists in the project.

**Solutions:**
1. Use a different version name
2. Update the existing version instead

```bash
# Check existing versions
python get_versions.py PROJ --format table

# Use unique name
python create_version.py PROJ --name "v1.0.1"
```

### Cannot release version

**Cause:** Version may have unreleased issues or be archived.

**Solutions:**
1. Move incomplete issues to another version first
2. Unarchive the version if archived

```bash
# Move incomplete issues first
python move_issues_version.py \
  --jql "fixVersion = 'v1.0.0' AND status != Done" \
  --target "v1.1.0"

# Then release
python release_version.py PROJ --name "v1.0.0" --date 2025-03-15
```

---

## Component Errors

### "Component in use" when deleting

**Cause:** Issues are assigned to the component being deleted.

**Solution:** Migrate issues to another component first:

```bash
# Migrate issues to another component
python delete_component.py --id 10000 --move-to 10001
```

### Cannot create component

**Cause:** Insufficient permissions or invalid lead.

**Solutions:**
1. Verify you have project administration permissions
2. Check the lead user exists and has project access

---

## General Debugging Tips

### 1. Check current status first

```bash
python get_transitions.py PROJ-123
```

### 2. Use dry-run for bulk operations

```bash
python move_issues_version.py --jql "fixVersion = v1.0.0" \
  --target "v1.1.0" --dry-run
```

### 3. Verify permissions

Ensure your JIRA account has:
- Transition permission for the project
- Assignment permission (if assigning)
- Resolve Issues permission (if resolving)
- Administer Projects (for versions/components)

### 4. Check workflow restrictions

Some transitions may be restricted by:
- User conditions (only assignee can resolve)
- Field conditions (must have estimate)
- Subtask conditions (all subtasks closed)
- Permission conditions (specific roles only)

### 5. Review workflow in JIRA

1. Go to Project Settings > Workflows
2. View the workflow diagram
3. Check transition conditions and validators

---

## Error Reference

| Error Message | Common Cause | Quick Fix |
|---------------|--------------|-----------|
| No transition found | Wrong status | Run `get_transitions.py` |
| Transition requires fields | Missing required field | Add `--fields` option |
| User not found | Invalid email | Verify user in JIRA |
| Cannot resolve | Wrong status | Transition first, then resolve |
| Version exists | Duplicate name | Use unique version name |
| Component in use | Has issues | Use `--move-to` option |
| Permission denied | Insufficient rights | Check project permissions |

---

*For workflow design guidance, see [BEST_PRACTICES.md](../docs/BEST_PRACTICES.md).*
