# Permission Schemes Guide

Deep-dive reference for JIRA permission scheme management including creation, configuration, and project assignment.

---

## When to Use Permission Scheme Scripts

Use these scripts when you need to:
- View, create, update, or delete permission schemes
- Manage permission grants within schemes
- Assign permission schemes to projects
- List all available JIRA permissions
- Clone existing permission schemes with modifications

---

## Understanding Permission Schemes

### What is a Permission Scheme?

A permission scheme is a collection of permission grants that control who can perform specific actions in JIRA projects. Each company-managed project is associated with one permission scheme.

### Key Concepts

- **Permission**: An action that can be performed (BROWSE_PROJECTS, CREATE_ISSUES, etc.)
- **Grant**: A mapping of a permission to a holder (group, role, user)
- **Holder**: The entity receiving the permission (anyone, group, projectRole, user)
- **Scheme**: A collection of grants that can be assigned to projects

---

## Scripts Reference

| Script | Description |
|--------|-------------|
| `list_permission_schemes.py` | List all permission schemes with optional filtering |
| `get_permission_scheme.py` | Get detailed information about a specific scheme |
| `create_permission_scheme.py` | Create a new permission scheme |
| `update_permission_scheme.py` | Update an existing scheme's metadata or grants |
| `delete_permission_scheme.py` | Delete a permission scheme (must not be in use) |
| `assign_permission_scheme.py` | Assign a scheme to one or more projects |
| `list_permissions.py` | List all available JIRA permissions |

---

## Examples

### List and Inspect Schemes

```bash
# List all permission schemes
python list_permission_schemes.py
python list_permission_schemes.py --show-grants
python list_permission_schemes.py --filter "Development"
python list_permission_schemes.py --show-projects

# Get detailed scheme information
python get_permission_scheme.py 10000
python get_permission_scheme.py "Default Software Scheme"
python get_permission_scheme.py 10000 --show-projects
python get_permission_scheme.py 10000 --export-template grants.json
```

### Create Permission Schemes

```bash
# Create new scheme with description
python create_permission_scheme.py --name "New Scheme" --description "Description"

# Create from template file
python create_permission_scheme.py --name "New Scheme" --template grants.json

# Clone an existing scheme
python create_permission_scheme.py --name "New Scheme" --clone 10000

# Create with inline grants
python create_permission_scheme.py --name "New Scheme" \
  --grant "BROWSE_PROJECTS:anyone" \
  --grant "CREATE_ISSUES:group:jira-developers"
```

### Update Permission Schemes

```bash
# Update name
python update_permission_scheme.py 10000 --name "Updated Name"

# Add permission grant
python update_permission_scheme.py 10000 --add-grant "EDIT_ISSUES:group:developers"

# Remove grant by ID
python update_permission_scheme.py 10000 --remove-grant 10103

# Remove grant by specification
python update_permission_scheme.py 10000 --remove-grant "EDIT_ISSUES:group:testers"
```

### Delete Permission Schemes

```bash
# Delete with confirmation prompt
python delete_permission_scheme.py 10050 --confirm

# Check if scheme can be deleted (not in use)
python delete_permission_scheme.py 10050 --check-only

# Force delete (use with caution)
python delete_permission_scheme.py 10050 --force --confirm
```

### Assign to Projects

```bash
# Assign scheme to single project
python assign_permission_scheme.py --project PROJ --scheme 10050

# Assign to multiple projects
python assign_permission_scheme.py --projects PROJ1,PROJ2 --scheme "Custom Scheme"

# Show current scheme for project
python assign_permission_scheme.py --project PROJ --show-current
```

### List Permissions

```bash
# List all available permissions
python list_permissions.py

# Filter by type
python list_permissions.py --type PROJECT

# Search by name
python list_permissions.py --search "issue"
```

---

## Permission Grant Format

When specifying grants, use the format:
```
PERMISSION:HOLDER_TYPE[:HOLDER_PARAMETER]
```

### Examples

```
BROWSE_PROJECTS:anyone
CREATE_ISSUES:group:jira-developers
EDIT_ISSUES:projectRole:Developers
ADMINISTER_PROJECTS:projectLead
RESOLVE_ISSUES:user:5b10a2844c20165700ede21g
```

---

## Holder Types Reference

| Type | Description | Parameter Required |
|------|-------------|-------------------|
| `anyone` | All users (logged in or anonymous) | No |
| `group` | JIRA group | Group name |
| `projectRole` | Project role | Role name |
| `user` | Specific user | Account ID |
| `projectLead` | Project lead | No |
| `reporter` | Issue reporter | No |
| `currentAssignee` | Current issue assignee | No |
| `applicationRole` | Application role | Role key |

---

## Common Permission Keys

### Project Permissions

| Key | Description |
|-----|-------------|
| `BROWSE_PROJECTS` | View projects and issues |
| `CREATE_ISSUES` | Create issues |
| `EDIT_ISSUES` | Edit issues |
| `DELETE_ISSUES` | Delete issues |
| `ASSIGN_ISSUES` | Assign issues |
| `ASSIGNABLE_USER` | Be assigned to issues |
| `RESOLVE_ISSUES` | Resolve/reopen issues |
| `CLOSE_ISSUES` | Close issues |
| `TRANSITION_ISSUES` | Transition issues |
| `MOVE_ISSUES` | Move issues between projects |
| `LINK_ISSUES` | Link issues |
| `ADD_COMMENTS` | Add comments |
| `EDIT_ALL_COMMENTS` | Edit all comments |
| `DELETE_ALL_COMMENTS` | Delete all comments |
| `CREATE_ATTACHMENTS` | Create attachments |
| `WORK_ON_ISSUES` | Log work on issues |
| `ADMINISTER_PROJECTS` | Administer projects |
| `MANAGE_SPRINTS` | Manage sprints |
| `MANAGE_WATCHERS` | Manage watchers |

---

## Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| List/view schemes | Permission to access Jira |
| Create scheme | Administer Jira (global) |
| Update scheme | Administer Jira (global) |
| Delete scheme | Administer Jira (global) |
| Assign to project | Administer Jira (global) |
| List permissions | None (public endpoint) |

---

## Important Notes

1. **Schemes in use** cannot be deleted - reassign projects first
2. **Default scheme** cannot be deleted - it's the system fallback
3. **Clone operation** creates a complete copy of all grants
4. **Dry-run mode** available on mutating operations to preview changes
5. **Grant IDs** are unique per scheme and used for removal

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| **403 Forbidden** | Insufficient permissions | Verify Administer Jira permission |
| **404 Not Found** | Scheme doesn't exist | Check scheme ID |
| **409 Conflict** | Scheme in use | Reassign projects first |
| **400 Bad Request** | Invalid grant format | Check grant format syntax |

---

## Related Guides

- [BEST_PRACTICES.md](../BEST_PRACTICES.md#permission-schemes) - Permission best practices
- [DECISION-TREE.md](../DECISION-TREE.md#i-want-to-configure-permissions) - Quick script finder
- [QUICK-REFERENCE.md](../QUICK-REFERENCE.md#permissions) - Command syntax reference
- [VOODOO_CONSTANTS.md](../VOODOO_CONSTANTS.md#permission-keys) - Complete permission key reference
