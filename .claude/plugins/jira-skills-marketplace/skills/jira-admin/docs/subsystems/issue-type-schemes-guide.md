# Issue Type Schemes Guide

Deep-dive reference for JIRA issue type scheme management including creation, configuration, and project assignment.

---

## When to Use Issue Type Scheme Scripts

Use these scripts when you need to:
- **List all issue type schemes** in your JIRA instance
- **Get scheme details** including which issue types are included
- **Create new schemes** with specific issue types
- **Update scheme metadata** (name, description, default type)
- **Delete unused schemes**
- **View scheme-to-project mappings**
- **Assign schemes to projects**
- **Add or remove issue types** from schemes
- **Reorder issue types** within schemes

---

## Understanding Issue Type Schemes

### What are Issue Type Schemes?

Issue type schemes define which issue types are available in a project:

- **Default Scheme**: Contains all issue types, used when no specific scheme is assigned
- **Custom Schemes**: Tailored collections of issue types for specific project needs
- **Default Issue Type**: The issue type pre-selected when creating new issues
- **Scheme Assignment**: Company-managed projects can have one scheme; team-managed projects manage their own types

---

## Scripts Reference

### Scheme CRUD Operations

| Script | Description |
|--------|-------------|
| `list_issue_type_schemes.py` | List all schemes with pagination |
| `get_issue_type_scheme.py` | Get scheme details with issue type list |
| `create_issue_type_scheme.py` | Create a new scheme with issue types |
| `update_issue_type_scheme.py` | Update scheme name, description, or default type |
| `delete_issue_type_scheme.py` | Delete an unused scheme |

### Scheme Assignment

| Script | Description |
|--------|-------------|
| `get_project_issue_type_scheme.py` | Get the scheme assigned to a project |
| `assign_issue_type_scheme.py` | Assign a scheme to a project |
| `get_issue_type_scheme_mappings.py` | List scheme-to-issue-type mappings |

### Scheme Issue Type Management

| Script | Description |
|--------|-------------|
| `add_issue_types_to_scheme.py` | Add issue types to an existing scheme |
| `remove_issue_type_from_scheme.py` | Remove an issue type from a scheme |
| `reorder_issue_types_in_scheme.py` | Change the order of issue types in a scheme |

---

## Examples

### Listing Schemes

```bash
# List all issue type schemes
python list_issue_type_schemes.py

# With pagination
python list_issue_type_schemes.py --start-at 0 --max-results 100

# Filter by scheme IDs
python list_issue_type_schemes.py --scheme-ids 10000 10001

# Order by name
python list_issue_type_schemes.py --order-by name

# Output as JSON
python list_issue_type_schemes.py --format json
```

### Getting Scheme Details

```bash
# Get scheme by ID
python get_issue_type_scheme.py 10001

# Include issue type mappings
python get_issue_type_scheme.py 10001 --include-items

# Output as JSON
python get_issue_type_scheme.py 10001 --format json
```

### Creating Schemes

```bash
# Create with required fields
python create_issue_type_scheme.py \
  --name "Development Scheme" \
  --issue-type-ids 10001 10002 10003

# Create with description and default type
python create_issue_type_scheme.py \
  --name "Support Scheme" \
  --description "Issue types for support projects" \
  --issue-type-ids 10001 10004 10005 \
  --default-issue-type-id 10004

# Output created scheme as JSON
python create_issue_type_scheme.py \
  --name "New Scheme" \
  --issue-type-ids 10001 \
  --format json
```

### Updating Schemes

```bash
# Update name
python update_issue_type_scheme.py 10001 --name "Updated Scheme Name"

# Update description
python update_issue_type_scheme.py 10001 --description "New description"

# Change default issue type
python update_issue_type_scheme.py 10001 --default-issue-type-id 10002

# Update multiple fields
python update_issue_type_scheme.py 10001 \
  --name "Production Scheme" \
  --description "For production projects" \
  --default-issue-type-id 10003
```

### Deleting Schemes

```bash
# Delete with confirmation prompt
python delete_issue_type_scheme.py 10050

# Force delete without confirmation
python delete_issue_type_scheme.py 10050 --force

# Use specific profile
python delete_issue_type_scheme.py 10050 --profile production
```

### Project Scheme Assignment

```bash
# Get scheme for a project
python get_project_issue_type_scheme.py --project-id 10000

# Get for multiple projects
python get_project_issue_type_scheme.py --project-ids 10000 10001 10002

# Output as JSON
python get_project_issue_type_scheme.py --project-id 10000 --format json

# Assign scheme to project
python assign_issue_type_scheme.py --scheme-id 10001 --project-id 10000

# Dry run to preview assignment
python assign_issue_type_scheme.py --scheme-id 10001 --project-id 10000 --dry-run

# Force without confirmation
python assign_issue_type_scheme.py --scheme-id 10001 --project-id 10000 --force
```

### Scheme Mappings

```bash
# Get all mappings
python get_issue_type_scheme_mappings.py

# Filter by scheme IDs
python get_issue_type_scheme_mappings.py --scheme-ids 10000 10001

# With pagination
python get_issue_type_scheme_mappings.py --start-at 0 --max-results 100

# Output as JSON
python get_issue_type_scheme_mappings.py --format json
```

### Managing Issue Types in Schemes

```bash
# Add issue types to a scheme
python add_issue_types_to_scheme.py --scheme-id 10001 --issue-type-ids 10003

# Add multiple issue types
python add_issue_types_to_scheme.py --scheme-id 10001 --issue-type-ids 10003 10004 10005

# Remove issue type from scheme (with confirmation)
python remove_issue_type_from_scheme.py --scheme-id 10001 --issue-type-id 10003

# Force remove without confirmation
python remove_issue_type_from_scheme.py --scheme-id 10001 --issue-type-id 10003 --force

# Reorder: move issue type to first position
python reorder_issue_types_in_scheme.py --scheme-id 10001 --issue-type-id 10003

# Reorder: move issue type after another
python reorder_issue_types_in_scheme.py --scheme-id 10001 --issue-type-id 10003 --after 10001
```

---

## Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| List/view schemes | Administer Jira (global) |
| Get scheme details | Administer Jira (global) |
| Create scheme | Administer Jira (global) |
| Update scheme | Administer Jira (global) |
| Delete scheme | Administer Jira (global) |
| Assign to project | Administer Jira (global) |
| Add/remove issue types | Administer Jira (global) |
| Reorder issue types | Administer Jira (global) |

---

## Important Notes

1. **Default Issue Type Scheme** cannot be deleted - it's the system fallback
2. **Schemes in use** by projects cannot be deleted - reassign projects first
3. **Cannot remove the default issue type** from a scheme
4. **Cannot remove the last issue type** from a scheme - at least one must remain
5. **Team-managed projects** don't use issue type schemes - they manage types directly
6. **Assigning a scheme may fail** if the project has issues using types not in the new scheme
7. **Issue type order** in the scheme determines display order in the UI

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| **403 Forbidden** | Insufficient permissions | Verify Administer Jira permission |
| **404 Not Found** | Scheme doesn't exist | Check scheme ID |
| **409 Conflict** | Scheme in use | Reassign projects first |
| **400 Bad Request** | Invalid issue type ID | Verify issue type exists |

---

## Related Guides

- [BEST_PRACTICES.md](../BEST_PRACTICES.md#issue-types--schemes) - Issue type scheme best practices
- [issue-types-guide.md](./issue-types-guide.md) - Managing individual issue types
- [DECISION-TREE.md](../DECISION-TREE.md#i-want-to-configure-issue-type-schemes) - Quick script finder
- [QUICK-REFERENCE.md](../QUICK-REFERENCE.md#issue-type-schemes) - Command syntax reference
