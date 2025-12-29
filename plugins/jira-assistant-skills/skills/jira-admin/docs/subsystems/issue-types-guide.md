# Issue Types Guide

Deep-dive reference for JIRA issue type management including creation, configuration, and deletion.

---

## When to Use Issue Type Scripts

Use these scripts when you need to:
- **List all issue types** in your JIRA instance
- **Get details** about a specific issue type
- **Create new issue types** (standard, subtask, or epic)
- **Update existing issue types** (name, description, avatar)
- **Delete issue types** with migration to alternatives

---

## Understanding Issue Types

### Hierarchy Levels

Issue types define the nature of work items in JIRA:

| Hierarchy Level | Type | Description |
|-----------------|------|-------------|
| -1 | Subtask | Child issues that must have a parent |
| 0 | Standard | Regular issues (Bug, Task, Story) |
| 1 | Epic | Container issues that group other issues |

### Standard vs Custom Issue Types

- **Standard Issue Types**: Built-in types like Story, Bug, Task, Epic, Subtask
- **Custom Issue Types**: User-created types for specific workflows

---

## Scripts Reference

| Script | Description |
|--------|-------------|
| `list_issue_types.py` | List all issue types with filtering by hierarchy |
| `get_issue_type.py` | Get detailed issue type information |
| `create_issue_type.py` | Create a new issue type |
| `update_issue_type.py` | Update issue type name, description, or avatar |
| `delete_issue_type.py` | Delete an issue type with optional migration |

---

## Examples

### Listing Issue Types

```bash
# List all issue types
python list_issue_types.py

# List only subtask types
python list_issue_types.py --subtask-only

# List only standard types (no subtasks or epics)
python list_issue_types.py --standard-only

# Filter by hierarchy level
python list_issue_types.py --hierarchy-level 0

# Output as JSON
python list_issue_types.py --format json

# Use specific profile
python list_issue_types.py --profile production
```

### Getting Issue Type Details

```bash
# Get issue type by ID
python get_issue_type.py 10001

# Get with alternative types (for migration planning)
python get_issue_type.py 10001 --show-alternatives

# Output as JSON
python get_issue_type.py 10001 --format json
```

### Creating Issue Types

```bash
# Create standard issue type
python create_issue_type.py --name "Feature Request" --description "Customer feature requests"

# Create subtask type
python create_issue_type.py --name "Technical Task" --type subtask --description "Technical implementation task"

# Create with specific hierarchy level
python create_issue_type.py --name "Initiative" --hierarchy-level 1

# Output created type as JSON
python create_issue_type.py --name "Support Issue" --format json
```

### Updating Issue Types

```bash
# Update name
python update_issue_type.py 10001 --name "Updated Name"

# Update description
python update_issue_type.py 10001 --description "New description"

# Update avatar
python update_issue_type.py 10001 --avatar-id 10204

# Update multiple fields
python update_issue_type.py 10001 --name "Feature" --description "Product feature"
```

### Deleting Issue Types

```bash
# Delete with confirmation prompt
python delete_issue_type.py 10050

# Delete and migrate existing issues to alternative type
python delete_issue_type.py 10050 --alternative-id 10001

# Force delete without confirmation
python delete_issue_type.py 10050 --force

# Use specific profile
python delete_issue_type.py 10050 --alternative-id 10001 --profile production
```

---

## Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| List/view issue types | Browse projects |
| Get issue type details | Browse projects |
| Create issue type | Administer Jira (global) |
| Update issue type | Administer Jira (global) |
| Delete issue type | Administer Jira (global) |

---

## Important Notes

1. **Issue type names must be unique** and <= 60 characters
2. **Deleting issue types** requires migrating existing issues to an alternative type
3. **System issue types** (Story, Bug, Task, Epic, Subtask) cannot be deleted
4. **Hierarchy levels** determine parent-child relationships (-1=subtask, 0=standard, 1=epic)
5. **Avatar IDs** can be obtained from the JIRA administration UI

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| **403 Forbidden** | Insufficient permissions | Verify Administer Jira permission |
| **404 Not Found** | Issue type doesn't exist | Check issue type ID |
| **409 Conflict** | Name already exists | Choose a different name |
| **400 Bad Request** | Invalid hierarchy level | Use -1, 0, or 1 |

---

## Related Guides

- [BEST_PRACTICES.md](../BEST_PRACTICES.md#issue-types--schemes) - Issue type best practices
- [issue-type-schemes-guide.md](./issue-type-schemes-guide.md) - Managing issue type schemes
- [DECISION-TREE.md](../DECISION-TREE.md#i-want-to-manage-issue-types) - Quick script finder
- [QUICK-REFERENCE.md](../QUICK-REFERENCE.md#issue-types) - Command syntax reference
