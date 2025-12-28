# Workflow Management Guide

Deep-dive reference for JIRA workflow management including discovery, scheme assignment, and status management.

---

## When to Use Workflow Management Scripts

Use these scripts when you need to:
- **List and discover workflows** in your JIRA instance
- **Get workflow details** including statuses, transitions, and rules
- **Search workflows** by name, scope, or status
- **List and manage workflow schemes** that map workflows to issue types
- **Assign workflow schemes to projects**
- **List and filter statuses** in your JIRA instance
- **Get workflow information for specific issues**

---

## Understanding JIRA Workflows

### Key Concepts

- **Workflow**: A set of statuses and transitions that define how issues move through their lifecycle
- **Status**: A state an issue can be in (e.g., "To Do", "In Progress", "Done")
- **Transition**: The movement from one status to another (e.g., "Start Progress")
- **Workflow Scheme**: Maps workflows to issue types for a project
- **Status Category**: Groups statuses into TODO, IN_PROGRESS, or DONE categories

### Important Limitation

**Workflow creation and modification is NOT supported via the JIRA REST API.** Workflows must be created and edited through the JIRA administration UI. These scripts provide READ operations and scheme assignment only.

---

## Scripts Reference

### Workflow Discovery

| Script | Description |
|--------|-------------|
| `list_workflows.py` | List all workflows with filtering and pagination |
| `get_workflow.py` | Get workflow details including statuses and transitions |
| `search_workflows.py` | Search workflows by name, scope, or status |

### Workflow Scheme Management

| Script | Description |
|--------|-------------|
| `list_workflow_schemes.py` | List all workflow schemes with mappings |
| `get_workflow_scheme.py` | Get scheme details with issue type mappings |
| `assign_workflow_scheme.py` | Assign a workflow scheme to a project |

### Status Management

| Script | Description |
|--------|-------------|
| `list_statuses.py` | List all statuses with filtering by category |

### Issue Workflow Information

| Script | Description |
|--------|-------------|
| `get_workflow_for_issue.py` | Get workflow info for a specific issue |

---

## Examples

### Listing Workflows

```bash
# List all workflows
python list_workflows.py
python list_workflows.py --output json

# Filter by name
python list_workflows.py --name "Software Development"
python list_workflows.py --name "Bug"

# Filter by scope
python list_workflows.py --scope global
python list_workflows.py --scope project

# Show usage information
python list_workflows.py --show-usage

# Pagination
python list_workflows.py --page 1 --page-size 20
python list_workflows.py --all
```

### Getting Workflow Details

```bash
# Get workflow by name
python get_workflow.py --name "Software Development Workflow"

# Get by entity ID
python get_workflow.py --entity-id "c6c7e6b0-19c4-4516-9a47-93f76124d4d4"

# Show statuses
python get_workflow.py --name "Bug Workflow" --show-statuses

# Show transitions with from/to statuses
python get_workflow.py --name "Bug Workflow" --show-transitions

# Show transition rules (conditions, validators, post-functions)
python get_workflow.py --name "Bug Workflow" --show-rules

# Show which schemes use this workflow
python get_workflow.py --name "Bug Workflow" --show-schemes

# Full details
python get_workflow.py --name "Software Development Workflow" \
  --show-statuses --show-transitions --show-rules --show-schemes

# JSON output
python get_workflow.py --name "Bug Workflow" --output json
```

### Searching Workflows

```bash
# Search by name pattern
python search_workflows.py --name "Development"
python search_workflows.py --name "Bug"

# Search with expansion
python search_workflows.py --name "Dev" --expand transitions
python search_workflows.py --expand statuses,transitions

# Filter by scope
python search_workflows.py --scope global
python search_workflows.py --scope project

# Filter by active/inactive status
python search_workflows.py --active-only
python search_workflows.py --inactive-only

# Order results
python search_workflows.py --order-by name
python search_workflows.py --order-by created

# Combined filters
python search_workflows.py --name "Bug" --scope global --active-only

# JSON output
python search_workflows.py --name "Dev" --output json
```

### Listing Workflow Schemes

```bash
# List all workflow schemes
python list_workflow_schemes.py
python list_workflow_schemes.py --output json

# Show issue type mappings
python list_workflow_schemes.py --show-mappings

# Show which projects use each scheme
python list_workflow_schemes.py --show-projects

# Pagination
python list_workflow_schemes.py --page 1 --page-size 10
```

### Getting Workflow Scheme Details

```bash
# Get scheme by ID
python get_workflow_scheme.py --id 10100

# Get by name
python get_workflow_scheme.py --name "Software Development Scheme"

# Show issue type mappings
python get_workflow_scheme.py --id 10100 --show-mappings

# Show projects using this scheme
python get_workflow_scheme.py --id 10100 --show-projects

# Show draft scheme (if exists)
python get_workflow_scheme.py --id 10100 --show-draft

# JSON output
python get_workflow_scheme.py --id 10100 --output json
```

### Assigning Workflow Schemes

```bash
# Show current scheme for a project
python assign_workflow_scheme.py --project PROJ --show-current

# Dry run - preview what would change
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --dry-run

# Assign by scheme ID (requires --confirm)
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --confirm

# Assign by scheme name
python assign_workflow_scheme.py --project PROJ --scheme "Agile Development Scheme" --confirm

# With status migration mappings from file
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 \
  --mappings status_mappings.json --confirm

# Don't wait for completion (async operation)
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --confirm --no-wait

# JSON output
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --dry-run --output json
```

### Listing Statuses

```bash
# List all statuses
python list_statuses.py
python list_statuses.py --output json

# Filter by category
python list_statuses.py --category TODO
python list_statuses.py --category IN_PROGRESS
python list_statuses.py --category DONE

# Filter by workflow
python list_statuses.py --workflow "Software Development Workflow"

# Group by category
python list_statuses.py --group-by category

# Show workflow usage
python list_statuses.py --show-usage

# Search by name
python list_statuses.py --search "Progress"
```

### Getting Workflow for an Issue

```bash
# Get basic workflow info for an issue
python get_workflow_for_issue.py PROJ-123

# Show available transitions from current status
python get_workflow_for_issue.py PROJ-123 --show-transitions

# Show workflow scheme information
python get_workflow_for_issue.py PROJ-123 --show-scheme

# Show everything
python get_workflow_for_issue.py PROJ-123 --show-transitions --show-scheme

# JSON output
python get_workflow_for_issue.py PROJ-123 --output json
```

---

## Status Categories

JIRA groups all statuses into three categories:

| Category | Category Key | Description | Examples |
|----------|--------------|-------------|----------|
| TODO | `new` | Work not yet started | To Do, Open, Backlog |
| IN_PROGRESS | `indeterminate` | Work in progress | In Progress, Code Review, Testing |
| DONE | `done` | Work completed | Done, Closed, Resolved |

---

## Status Migration Mappings

When assigning a new workflow scheme, you may need to provide status migration mappings if issues exist with statuses that don't exist in the new workflow. Create a JSON file with mappings:

```json
[
  {
    "issueTypeId": "10000",
    "statusMigrations": [
      {"oldStatusId": "1", "newStatusId": "10000"},
      {"oldStatusId": "2", "newStatusId": "10001"}
    ]
  },
  {
    "issueTypeId": "10001",
    "statusMigrations": [
      {"oldStatusId": "1", "newStatusId": "10000"}
    ]
  }
]
```

---

## Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| List/view workflows | Administer Jira (global) |
| Get workflow details | Administer Jira (global) |
| Search workflows | Administer Jira (global) |
| List/view workflow schemes | Administer Jira (global) |
| Get workflow scheme details | Administer Jira (global) |
| Assign workflow scheme to project | Administer Jira (global) |
| List/view statuses | Browse Projects |
| Get workflow for issue | Browse Projects |

---

## Important Notes

1. **Workflow creation/modification is NOT supported** via REST API - use JIRA admin UI
2. **Workflow scheme assignment is asynchronous** - may take time for large projects
3. **Status migration may be required** when changing workflow schemes
4. **Default workflow scheme** uses the "jira" built-in workflow for all issue types
5. **Draft schemes** exist when a scheme is being edited but not yet published
6. **Global vs Project scope** - global workflows are available instance-wide
7. **Scheme assignment requires confirmation** - use --dry-run to preview changes

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| **403 Forbidden** | Insufficient permissions | Verify Administer Jira permission |
| **404 Not Found** | Workflow or scheme doesn't exist | Check name or ID |
| **400 Bad Request** | Status migration required | Provide migration mappings |
| **Async Error** | Assignment timed out | Check status later, use --no-wait |

---

## Related Guides

- [BEST_PRACTICES.md](../BEST_PRACTICES.md#workflow-management) - Workflow best practices
- [DECISION-TREE.md](../DECISION-TREE.md#i-want-to-configure-workflows) - Quick script finder
- [QUICK-REFERENCE.md](../QUICK-REFERENCE.md#workflows) - Command syntax reference
