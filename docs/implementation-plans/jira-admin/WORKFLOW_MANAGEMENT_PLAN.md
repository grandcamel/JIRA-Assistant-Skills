# Jira Admin - Workflow Management - TDD Implementation Plan

## Implementation Status

**Overall Status:** ⏳ NOT STARTED

**Planned Scripts:**
- ⏳ `list_workflows.py` - List all workflows with pagination support
- ⏳ `get_workflow.py` - Get workflow details with statuses and transitions
- ⏳ `search_workflows.py` - Search workflows with filtering options
- ⏳ `get_workflow_schemes.py` - Get workflow scheme details
- ⏳ `list_workflow_schemes.py` - List all workflow schemes
- ⏳ `assign_workflow_scheme.py` - Assign workflow scheme to project
- ⏳ `list_statuses.py` - List all statuses across workflows
- ⏳ `get_workflow_for_issue.py` - Get workflow information for a specific issue

**JiraClient Methods to Add:**
- ⏳ `get_workflows()` - List all workflows
- ⏳ `get_workflow(entity_id)` - Get workflow details
- ⏳ `search_workflows(query_params)` - Search workflows
- ⏳ `get_workflow_schemes()` - List workflow schemes
- ⏳ `get_workflow_scheme(scheme_id)` - Get workflow scheme details
- ⏳ `get_workflow_scheme_for_project(project_key)` - Get project's workflow scheme
- ⏳ `assign_workflow_scheme(project_key, scheme_id, mappings)` - Assign scheme to project
- ⏳ `get_all_statuses()` - Get all statuses
- ⏳ `create_workflow_scheme_draft(scheme_id)` - Create draft for modification
- ⏳ `publish_workflow_scheme_draft(scheme_id, mappings)` - Publish draft changes

**Test Coverage:**
- Unit tests: 0/50+ planned
- Live integration tests: Not yet implemented
- Coverage: Target 85%+

**Last Updated:** 2025-12-26

---

## Overview

**Objective:** Implement comprehensive workflow discovery, inspection, and scheme management for JIRA using Test-Driven Development (TDD)

**Scope:** This implementation focuses on **read operations** and **workflow scheme assignment**. Creating or modifying workflows via REST API is extremely limited and requires UI-based workflow designer.

**Key Limitations:**
- **Workflow Creation:** Not supported via REST API (requires UI-based workflow designer or Java API)
- **Workflow Modification:** Limited to draft-based workflow scheme updates
- **Transition Configuration:** Cannot modify conditions, validators, post-functions via REST API
- **Status Creation:** Can only view statuses, not create them via standard REST API

**Supported Operations:**
- ✅ List and search workflows
- ✅ Get workflow details (statuses, transitions)
- ✅ List and get workflow schemes
- ✅ Assign workflow schemes to projects
- ✅ List all statuses across the instance
- ✅ Get workflow information for specific issues
- ⚠️ Create/modify workflows (NOT SUPPORTED - requires UI)
- ⚠️ Configure transitions (NOT SUPPORTED - requires UI)

**Approach:**
1. Write failing tests first for each feature
2. Implement minimum code to pass tests
3. Refactor while keeping tests green
4. Commit after each successful test suite
5. Update documentation as features complete

**Testing Stack:**
- **Framework:** pytest
- **Mocking:** unittest.mock / responses library
- **Coverage Target:** 85%+
- **Test Location:** `.claude/skills/jira-admin/tests/`

**Feature Priority:**
1. **Phase 4.1: List Workflows** (Foundation - discover available workflows)
2. **Phase 4.2: Get Workflow Details** (Inspect statuses and transitions)
3. **Phase 4.3: Search Workflows** (Filter and query workflows)
4. **Phase 4.4: Workflow Schemes** (List and get workflow schemes)
5. **Phase 4.5: Assign Workflow Schemes** (Assign schemes to projects)
6. **Phase 4.6: Status Operations** (List and query statuses)
7. **Phase 4.7: Workflow for Issues** (Get workflow for specific issues)

---

## JIRA API Reference

### Endpoints

| Method | Endpoint | Description | Limitations | Priority |
|--------|----------|-------------|-------------|----------|
| GET | `/rest/api/3/workflow` | List all workflows | Admin permission required | **Critical** |
| POST | `/rest/api/3/workflows` | Bulk get workflows (with details) | Admin permission required | **Critical** |
| GET | `/rest/api/3/workflow/search` | Search workflows with transitions | Recommended over GET /workflow | **Critical** |
| DELETE | `/rest/api/3/workflow/{entityId}` | Delete workflow | Cannot delete active workflows | Medium |
| GET | `/rest/api/3/workflow/{workflowId}/workflowSchemes` | Get schemes using workflow | - | High |
| POST | `/rest/api/3/workflows/create` | Bulk create workflows | Limited support, use with caution | Low |
| POST | `/rest/api/3/workflows/update` | Bulk update workflows | Draft-based updates only | Low |
| GET | `/rest/api/3/workflowscheme` | List workflow schemes | Admin permission required | **Critical** |
| GET | `/rest/api/3/workflowscheme/{id}` | Get workflow scheme details | - | High |
| GET | `/rest/api/3/workflowscheme/project` | Get scheme for project | - | **Critical** |
| POST | `/rest/api/3/workflowscheme/project/switch` | Switch project workflow scheme | Experimental, async operation | High |
| POST | `/rest/api/3/workflowscheme/{id}/createdraft` | Create draft of scheme | For modification | Medium |
| POST | `/rest/api/3/workflowscheme/{id}/draft/publish` | Publish draft scheme | Requires status mappings | Medium |
| GET | `/rest/api/3/status` | Get all statuses | Only returns statuses in active workflows | High |
| GET | `/rest/api/2/issue/{issueIdOrKey}/transitions` | Get available transitions for issue | - | High |

### Permission Requirements

**Global Permissions Required:**
- **Administer Jira** - Required for most workflow operations
  - List workflows
  - Get workflow details
  - List workflow schemes
  - Assign workflow schemes

**Project Permissions:**
- **Administer Projects** - May be sufficient for project-specific operations
- **Browse Projects** - Required to view workflow transitions for issues

### Important API Notes

1. **Workflow Search vs. List:**
   - `GET /rest/api/3/workflow/search` is the recommended endpoint
   - Returns workflows with full transition details
   - Better performance than bulk get workflows

2. **Bulk Operations:**
   - `POST /rest/api/3/workflows` - Accepts list of workflow IDs, returns full details
   - Useful for getting multiple workflow details in one call
   - Supports status layout properties (x/y positions for visual designer)

3. **Workflow Scheme Assignment:**
   - `POST /rest/api/3/workflowscheme/project/switch` is experimental but recommended
   - Handles asynchronous operations with progress tracking
   - Accepts issue status migration mappings
   - Returns task ID for tracking long-running operations

4. **Workflow History (New in 2025):**
   - Historical workflow data only available from Oct 30, 2025 onwards
   - `GET /rest/api/3/workflow/{workflowId}/history` - List historical versions
   - `GET /rest/api/3/workflow/{workflowId}/version/{versionNumber}` - Get specific version

5. **Deprecation Warnings:**
   - Workflow transition properties (`/rest/api/3/workflow/transitions/{transitionId}/properties`) will be removed June 1, 2026
   - Some workflow creation APIs will be removed February 1, 2026
   - Use bulk workflow operations instead

---

## API Response Structures

### Workflow Object

```json
{
  "id": {
    "name": "Software Development Workflow",
    "entityId": "c6c7e6b0-19c4-4516-9a47-93f76124d4d4"
  },
  "description": "Workflow for software development projects",
  "version": {
    "versionNumber": 3,
    "id": "12345"
  },
  "scope": {
    "type": "GLOBAL",
    "project": null
  },
  "isDefault": false,
  "transitions": [
    {
      "id": "11",
      "name": "Start Progress",
      "description": "Move issue to In Progress",
      "from": ["10000"],
      "to": "10001",
      "type": "DIRECTED",
      "screen": null,
      "rules": {
        "conditions": [],
        "validators": [],
        "postFunctions": []
      }
    }
  ],
  "statuses": [
    {
      "id": "10000",
      "name": "To Do",
      "statusCategory": "TODO",
      "statusReference": "1",
      "layout": {
        "x": 100,
        "y": 200
      }
    },
    {
      "id": "10001",
      "name": "In Progress",
      "statusCategory": "IN_PROGRESS",
      "statusReference": "3",
      "layout": {
        "x": 300,
        "y": 200
      }
    },
    {
      "id": "10002",
      "name": "Done",
      "statusCategory": "DONE",
      "statusReference": "10001",
      "layout": {
        "x": 500,
        "y": 200
      }
    }
  ],
  "created": "2025-01-15T10:30:00.000+0000",
  "updated": "2025-11-20T14:45:00.000+0000"
}
```

### Workflow Scheme Object

```json
{
  "id": 10100,
  "name": "Software Development Scheme",
  "description": "Workflow scheme for software projects",
  "defaultWorkflow": "jira",
  "issueTypeMappings": {
    "10000": "Software Development Workflow",
    "10001": "Bug Workflow",
    "10002": "Epic Workflow"
  },
  "draft": false,
  "lastModified": "2025-11-15T09:20:00.000+0000",
  "lastModifiedUser": {
    "accountId": "557058:12345678-1234-1234-1234-123456789012",
    "displayName": "John Admin"
  },
  "issueTypes": {
    "10000": {
      "id": "10000",
      "name": "Story",
      "workflow": "Software Development Workflow"
    },
    "10001": {
      "id": "10001",
      "name": "Bug",
      "workflow": "Bug Workflow"
    }
  },
  "self": "https://site.atlassian.net/rest/api/3/workflowscheme/10100"
}
```

### Status Object

```json
{
  "id": "10000",
  "name": "To Do",
  "description": "Work that needs to be done",
  "iconUrl": "https://site.atlassian.net/images/icons/statuses/generic.png",
  "statusCategory": {
    "id": 2,
    "key": "new",
    "colorName": "blue-gray",
    "name": "To Do",
    "self": "https://site.atlassian.net/rest/api/3/statuscategory/2"
  },
  "scope": {
    "type": "GLOBAL",
    "project": null
  },
  "self": "https://site.atlassian.net/rest/api/3/status/10000"
}
```

### Workflow Scheme Assignment Request

```json
{
  "workflowSchemeId": "10100",
  "issueTypeMappings": [
    {
      "issueTypeId": "10000",
      "statusMigrations": [
        {
          "oldStatusId": "1",
          "newStatusId": "10000"
        },
        {
          "oldStatusId": "3",
          "newStatusId": "10001"
        }
      ]
    }
  ]
}
```

---

## Test Infrastructure Setup

### Initial Setup Tasks

- [ ] **Setup 4.1:** Create test infrastructure
  - [ ] Create `tests/test_workflow_management.py`
  - [ ] Create workflow fixtures in `tests/conftest.py`
  - [ ] Create workflow scheme fixtures
  - [ ] Create status fixtures
  - [ ] Mock JiraClient workflow methods
  - **Commit:** `test(jira-admin): add workflow management test fixtures`

- [ ] **Setup 4.2:** Add JiraClient methods
  - [ ] `get_workflows()` - List all workflows
  - [ ] `get_workflow(entity_id)` - Get workflow details
  - [ ] `search_workflows(query_params)` - Search workflows
  - [ ] `get_workflow_schemes()` - List workflow schemes
  - [ ] `get_workflow_scheme(scheme_id)` - Get workflow scheme
  - [ ] `get_workflow_scheme_for_project(project_key)` - Get project scheme
  - [ ] `assign_workflow_scheme(project_key, scheme_id, mappings)` - Assign scheme
  - [ ] `get_all_statuses()` - Get all statuses
  - **Commit:** `feat(shared): add workflow management methods to JiraClient`

---

## Phase 4.1: List Workflows

### Feature 4.1.1: List All Workflows

**Script:** `list_workflows.py`

**JIRA API:**
- `GET /rest/api/3/workflow` - List workflows (basic info)
- `POST /rest/api/3/workflows` - Bulk get workflows (with details)

**Test File:** `tests/test_workflow_management.py`

**Test Cases:**
```python
def test_list_workflows_basic():
    """Test listing all workflows with basic information."""
    # Should return list of workflows with name, entityId, description

def test_list_workflows_with_details():
    """Test listing workflows with full details (statuses, transitions)."""
    # Use bulk get workflows to include transition details

def test_list_workflows_filter_by_name():
    """Test filtering workflows by name pattern."""

def test_list_workflows_filter_by_scope():
    """Test filtering by global vs project-scoped workflows."""

def test_list_workflows_show_usage():
    """Test showing which projects use each workflow."""

def test_list_workflows_pagination():
    """Test handling paginated results."""

def test_list_workflows_format_table():
    """Test human-readable table output."""

def test_list_workflows_format_json():
    """Test JSON output format."""

def test_list_workflows_no_permission():
    """Test error handling when user lacks admin permission."""
```

**CLI Interface:**
```bash
# List all workflows (basic info)
python list_workflows.py

# Include full details (statuses, transitions)
python list_workflows.py --details

# Filter by name
python list_workflows.py --filter "Software"

# Filter by scope
python list_workflows.py --scope global
python list_workflows.py --scope project

# Show which projects use each workflow
python list_workflows.py --show-usage

# JSON output
python list_workflows.py --output json

# With profile
python list_workflows.py --profile production
```

**Output Example:**
```
Workflows:

Name                              Type    Statuses  Transitions  Last Modified
────────────────────────────────  ──────  ────────  ───────────  ─────────────
Software Development Workflow     Global  5         12           2025-11-20
Bug Workflow                      Global  4         8            2025-10-15
Simple Workflow                   Global  3         4            2025-01-10
Custom Project Workflow           Project 6         15           2025-12-01

Total: 4 workflows
```

**Acceptance Criteria:**
- [ ] All 9 tests pass
- [ ] Lists all accessible workflows
- [ ] Supports filtering by name and scope
- [ ] Optional details mode shows statuses/transitions
- [ ] Shows workflow usage across projects
- [ ] Handles pagination for large instances
- [ ] Clear error message for permission issues

**Commits:**
1. `test(jira-admin): add failing tests for list_workflows`
2. `feat(jira-admin): implement list_workflows.py (9/9 tests passing)`

---

## Phase 4.2: Get Workflow Details

### Feature 4.2.1: Get Workflow Details

**Script:** `get_workflow.py`

**JIRA API:**
- `GET /rest/api/3/workflow/search` - Get workflow with transitions
- `POST /rest/api/3/workflows` - Bulk get (single workflow with full details)

**Test Cases:**
```python
def test_get_workflow_by_name():
    """Test getting workflow details by workflow name."""

def test_get_workflow_by_entity_id():
    """Test getting workflow by entity ID."""

def test_get_workflow_show_statuses():
    """Test displaying all statuses in workflow."""

def test_get_workflow_show_transitions():
    """Test displaying all transitions with from/to statuses."""

def test_get_workflow_show_transition_rules():
    """Test showing conditions, validators, post-functions for transitions."""

def test_get_workflow_show_schemes():
    """Test showing which workflow schemes use this workflow."""

def test_get_workflow_format_diagram():
    """Test ASCII diagram output of workflow states/transitions."""

def test_get_workflow_format_json():
    """Test JSON output format."""

def test_get_workflow_not_found():
    """Test error handling for non-existent workflow."""
```

**CLI Interface:**
```bash
# Get workflow by name
python get_workflow.py "Software Development Workflow"

# Get by entity ID
python get_workflow.py --entity-id "c6c7e6b0-19c4-4516-9a47-93f76124d4d4"

# Show statuses
python get_workflow.py "Software Development Workflow" --show-statuses

# Show transitions
python get_workflow.py "Software Development Workflow" --show-transitions

# Show transition rules (conditions, validators, post-functions)
python get_workflow.py "Software Development Workflow" --show-rules

# Show which schemes use this workflow
python get_workflow.py "Software Development Workflow" --show-schemes

# ASCII diagram
python get_workflow.py "Software Development Workflow" --diagram

# JSON output
python get_workflow.py "Software Development Workflow" --output json
```

**Output Example:**
```
Workflow: Software Development Workflow
Entity ID: c6c7e6b0-19c4-4516-9a47-93f76124d4d4
Description: Workflow for software development projects
Type: Global
Version: 3
Created: 2025-01-15
Last Modified: 2025-11-20

Statuses (5):
┌─────────────┬──────────────────┬──────────┐
│ ID          │ Name             │ Category │
├─────────────┼──────────────────┼──────────┤
│ 10000       │ To Do            │ TODO     │
│ 10001       │ In Progress      │ IN_PROG  │
│ 10002       │ Code Review      │ IN_PROG  │
│ 10003       │ Testing          │ IN_PROG  │
│ 10004       │ Done             │ DONE     │
└─────────────┴──────────────────┴──────────┘

Transitions (12):
┌────┬──────────────────┬─────────────┬──────────────┐
│ ID │ Name             │ From        │ To           │
├────┼──────────────────┼─────────────┼──────────────┤
│ 11 │ Start Progress   │ To Do       │ In Progress  │
│ 21 │ Send to Review   │ In Progress │ Code Review  │
│ 31 │ Approve          │ Code Review │ Testing      │
│ 41 │ Send to Testing  │ In Progress │ Testing      │
│ 51 │ Complete         │ Testing     │ Done         │
│ 61 │ Reopen           │ Done        │ To Do        │
└────┴──────────────────┴─────────────┴──────────────┘

Used by Workflow Schemes (2):
- Software Development Scheme (ID: 10100)
- Agile Development Scheme (ID: 10101)
```

**Acceptance Criteria:**
- [ ] All 9 tests pass
- [ ] Gets workflow by name or entity ID
- [ ] Shows all statuses with categories
- [ ] Shows all transitions with from/to mapping
- [ ] Optional display of transition rules
- [ ] Shows which schemes use the workflow
- [ ] Optional ASCII diagram output
- [ ] Clear error for non-existent workflow

**Commits:**
1. `test(jira-admin): add failing tests for get_workflow`
2. `feat(jira-admin): implement get_workflow.py (9/9 tests passing)`

---

## Phase 4.3: Search Workflows

### Feature 4.3.1: Search Workflows with Filters

**Script:** `search_workflows.py`

**JIRA API:**
- `GET /rest/api/3/workflow/search` - Search workflows with query parameters

**Test Cases:**
```python
def test_search_workflows_by_name():
    """Test searching workflows by name pattern."""

def test_search_workflows_by_status():
    """Test finding workflows containing specific status."""

def test_search_workflows_expand_transitions():
    """Test expanding transition details in results."""

def test_search_workflows_filter_global():
    """Test filtering to global workflows only."""

def test_search_workflows_filter_project():
    """Test filtering to project-scoped workflows."""

def test_search_workflows_format_table():
    """Test table output format."""

def test_search_workflows_format_json():
    """Test JSON output format."""
```

**CLI Interface:**
```bash
# Search by name
python search_workflows.py --name "Development"

# Find workflows containing a specific status
python search_workflows.py --status "In Progress"

# Expand transition details
python search_workflows.py --expand transitions

# Filter by scope
python search_workflows.py --scope global
python search_workflows.py --scope project

# Combined search
python search_workflows.py --name "Software" --scope global --expand transitions

# JSON output
python search_workflows.py --name "Dev" --output json
```

**Output Example:**
```
Search Results: 2 workflows matching "Development"

Name                           Type    Statuses  Transitions  Modified
─────────────────────────────  ──────  ────────  ───────────  ──────────
Software Development Workflow  Global  5         12           2025-11-20
Agile Development Workflow     Global  4         10           2025-10-05
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Search by workflow name pattern
- [ ] Filter by workflow scope (global/project)
- [ ] Find workflows containing specific status
- [ ] Optional expansion of transition details
- [ ] Table and JSON output formats

**Commits:**
1. `test(jira-admin): add failing tests for search_workflows`
2. `feat(jira-admin): implement search_workflows.py (7/7 tests passing)`

---

## Phase 4.4: Workflow Schemes

### Feature 4.4.1: List Workflow Schemes

**Script:** `list_workflow_schemes.py`

**JIRA API:**
- `GET /rest/api/3/workflowscheme` - List all workflow schemes

**Test Cases:**
```python
def test_list_workflow_schemes_all():
    """Test listing all workflow schemes."""

def test_list_workflow_schemes_show_mappings():
    """Test showing issue type to workflow mappings."""

def test_list_workflow_schemes_show_projects():
    """Test showing which projects use each scheme."""

def test_list_workflow_schemes_filter_by_name():
    """Test filtering schemes by name pattern."""

def test_list_workflow_schemes_include_drafts():
    """Test including draft schemes in results."""

def test_list_workflow_schemes_format_table():
    """Test table output format."""

def test_list_workflow_schemes_format_json():
    """Test JSON output format."""
```

**CLI Interface:**
```bash
# List all workflow schemes
python list_workflow_schemes.py

# Show issue type mappings
python list_workflow_schemes.py --show-mappings

# Show which projects use each scheme
python list_workflow_schemes.py --show-projects

# Filter by name
python list_workflow_schemes.py --filter "Software"

# Include draft schemes
python list_workflow_schemes.py --include-drafts

# JSON output
python list_workflow_schemes.py --output json
```

**Output Example:**
```
Workflow Schemes:

ID     Name                          Default Workflow  Issue Types  Projects  Modified
─────  ────────────────────────────  ────────────────  ───────────  ────────  ──────────
10100  Software Development Scheme   jira              5            3         2025-11-15
10101  Agile Development Scheme      jira              4            2         2025-10-20
10102  Simple Workflow Scheme        jira              3            5         2025-09-10

Total: 3 workflow schemes
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Lists all workflow schemes
- [ ] Shows issue type mappings
- [ ] Shows projects using each scheme
- [ ] Filter by scheme name
- [ ] Optional inclusion of drafts
- [ ] Table and JSON output

**Commits:**
1. `test(jira-admin): add failing tests for list_workflow_schemes`
2. `feat(jira-admin): implement list_workflow_schemes.py (7/7 tests passing)`

---

### Feature 4.4.2: Get Workflow Scheme Details

**Script:** `get_workflow_scheme.py`

**JIRA API:**
- `GET /rest/api/3/workflowscheme/{id}` - Get workflow scheme details

**Test Cases:**
```python
def test_get_workflow_scheme_by_id():
    """Test getting workflow scheme by ID."""

def test_get_workflow_scheme_by_name():
    """Test getting workflow scheme by name."""

def test_get_workflow_scheme_show_mappings():
    """Test showing all issue type to workflow mappings."""

def test_get_workflow_scheme_show_projects():
    """Test showing all projects using this scheme."""

def test_get_workflow_scheme_format_table():
    """Test table output format."""

def test_get_workflow_scheme_format_json():
    """Test JSON output format."""

def test_get_workflow_scheme_not_found():
    """Test error handling for non-existent scheme."""
```

**CLI Interface:**
```bash
# Get by ID
python get_workflow_scheme.py --id 10100

# Get by name
python get_workflow_scheme.py "Software Development Scheme"

# Show mappings
python get_workflow_scheme.py 10100 --show-mappings

# Show projects
python get_workflow_scheme.py 10100 --show-projects

# JSON output
python get_workflow_scheme.py 10100 --output json
```

**Output Example:**
```
Workflow Scheme: Software Development Scheme
ID: 10100
Description: Workflow scheme for software projects
Default Workflow: jira
Last Modified: 2025-11-15 09:20:00
Modified By: John Admin

Issue Type Mappings (5):
┌────────────┬────────────────────────────────────┐
│ Issue Type │ Workflow                           │
├────────────┼────────────────────────────────────┤
│ Story      │ Software Development Workflow      │
│ Bug        │ Bug Workflow                       │
│ Epic       │ Epic Workflow                      │
│ Task       │ jira (default)                     │
│ Sub-task   │ jira (default)                     │
└────────────┴────────────────────────────────────┘

Used by Projects (3):
- PROJ (My Project)
- DEV (Development Project)
- TEST (Test Project)
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Gets scheme by ID or name
- [ ] Shows all issue type mappings
- [ ] Shows which projects use the scheme
- [ ] Table and JSON output formats
- [ ] Clear error for non-existent scheme

**Commits:**
1. `test(jira-admin): add failing tests for get_workflow_scheme`
2. `feat(jira-admin): implement get_workflow_scheme.py (7/7 tests passing)`

---

## Phase 4.5: Assign Workflow Schemes

### Feature 4.5.1: Assign Workflow Scheme to Project

**Script:** `assign_workflow_scheme.py`

**JIRA API:**
- `POST /rest/api/3/workflowscheme/project/switch` - Switch project workflow scheme (experimental)
- `GET /rest/api/3/workflowscheme/project` - Get current project scheme

**Test Cases:**
```python
def test_assign_workflow_scheme_basic():
    """Test assigning workflow scheme to project."""

def test_assign_workflow_scheme_with_mappings():
    """Test providing status migration mappings."""

def test_assign_workflow_scheme_dry_run():
    """Test dry-run mode shows what would change."""

def test_assign_workflow_scheme_confirm_required():
    """Test confirmation is required for live operation."""

def test_assign_workflow_scheme_show_current():
    """Test showing current workflow scheme before assignment."""

def test_assign_workflow_scheme_async_tracking():
    """Test tracking asynchronous assignment operation."""

def test_assign_workflow_scheme_invalid_project():
    """Test error handling for invalid project."""

def test_assign_workflow_scheme_invalid_scheme():
    """Test error handling for invalid workflow scheme."""
```

**CLI Interface:**
```bash
# Show current workflow scheme for project
python assign_workflow_scheme.py --project PROJ --show-current

# Assign new workflow scheme
python assign_workflow_scheme.py --project PROJ --scheme-id 10100 --confirm

# Assign by scheme name
python assign_workflow_scheme.py --project PROJ --scheme "Software Development Scheme" --confirm

# Dry run (show what would change)
python assign_workflow_scheme.py --project PROJ --scheme-id 10100 --dry-run

# With status migration mappings
python assign_workflow_scheme.py --project PROJ --scheme-id 10100 \
  --mappings mappings.json --confirm

# Track async operation
python assign_workflow_scheme.py --project PROJ --scheme-id 10100 \
  --confirm --track-progress
```

**Status Mappings File (mappings.json):**
```json
{
  "issueTypeMappings": [
    {
      "issueTypeId": "10000",
      "statusMigrations": [
        {"oldStatusId": "1", "newStatusId": "10000"},
        {"oldStatusId": "3", "newStatusId": "10001"},
        {"oldStatusId": "10001", "newStatusId": "10004"}
      ]
    },
    {
      "issueTypeId": "10001",
      "statusMigrations": [
        {"oldStatusId": "1", "newStatusId": "10000"},
        {"oldStatusId": "10001", "newStatusId": "10004"}
      ]
    }
  ]
}
```

**Output Example:**
```
Current Workflow Scheme for Project PROJ:
  Scheme ID: 10050
  Scheme Name: Default Workflow Scheme
  Default Workflow: jira

New Workflow Scheme:
  Scheme ID: 10100
  Scheme Name: Software Development Scheme
  Default Workflow: jira

This will change workflows for the following issue types:
  - Story: jira → Software Development Workflow
  - Bug: jira → Bug Workflow
  - Epic: jira → Epic Workflow

Status migrations will be applied according to mappings.json

WARNING: This operation cannot be undone. All issues will be migrated.

Confirm assignment? [y/N]: y

✓ Workflow scheme assignment initiated (Task ID: WFS-12345)
✓ Tracking progress... (10%)
✓ Tracking progress... (45%)
✓ Tracking progress... (78%)
✓ Tracking progress... (100%)
✓ Workflow scheme successfully assigned to project PROJ
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Assigns workflow scheme to project
- [ ] Shows current scheme before assignment
- [ ] Dry-run mode shows changes without applying
- [ ] Requires explicit confirmation for live operation
- [ ] Supports status migration mappings
- [ ] Tracks async operation progress
- [ ] Clear errors for invalid project/scheme

**Commits:**
1. `test(jira-admin): add failing tests for assign_workflow_scheme`
2. `feat(jira-admin): implement assign_workflow_scheme.py (8/8 tests passing)`

---

## Phase 4.6: Status Operations

### Feature 4.6.1: List All Statuses

**Script:** `list_statuses.py`

**JIRA API:**
- `GET /rest/api/3/status` - Get all statuses

**Test Cases:**
```python
def test_list_statuses_all():
    """Test listing all statuses across workflows."""

def test_list_statuses_filter_by_category():
    """Test filtering by status category (TODO, IN_PROGRESS, DONE)."""

def test_list_statuses_filter_by_workflow():
    """Test filtering to statuses in specific workflow."""

def test_list_statuses_show_usage():
    """Test showing which workflows use each status."""

def test_list_statuses_group_by_category():
    """Test grouping statuses by category."""

def test_list_statuses_format_table():
    """Test table output format."""

def test_list_statuses_format_json():
    """Test JSON output format."""
```

**CLI Interface:**
```bash
# List all statuses
python list_statuses.py

# Filter by category
python list_statuses.py --category TODO
python list_statuses.py --category IN_PROGRESS
python list_statuses.py --category DONE

# Filter by workflow
python list_statuses.py --workflow "Software Development Workflow"

# Show which workflows use each status
python list_statuses.py --show-usage

# Group by category
python list_statuses.py --group-by category

# JSON output
python list_statuses.py --output json
```

**Output Example:**
```
Statuses by Category:

TODO (5):
┌───────┬──────────────┬─────────────────┬───────────┐
│ ID    │ Name         │ Category        │ Workflows │
├───────┼──────────────┼─────────────────┼───────────┤
│ 10000 │ To Do        │ TODO            │ 12        │
│ 10005 │ Backlog      │ TODO            │ 8         │
│ 10010 │ Open         │ TODO            │ 15        │
│ 10015 │ New          │ TODO            │ 10        │
│ 10020 │ Waiting      │ TODO            │ 6         │
└───────┴──────────────┴─────────────────┴───────────┘

IN_PROGRESS (4):
┌───────┬──────────────┬─────────────────┬───────────┐
│ ID    │ Name         │ Category        │ Workflows │
├───────┼──────────────┼─────────────────┼───────────┤
│ 10001 │ In Progress  │ IN_PROGRESS     │ 14        │
│ 10002 │ Code Review  │ IN_PROGRESS     │ 7         │
│ 10003 │ Testing      │ IN_PROGRESS     │ 9         │
│ 10004 │ Reviewing    │ IN_PROGRESS     │ 5         │
└───────┴──────────────┴─────────────────┴───────────┘

DONE (3):
┌───────┬──────────────┬─────────────────┬───────────┐
│ ID    │ Name         │ Category        │ Workflows │
├───────┼──────────────┼─────────────────┼───────────┤
│ 10100 │ Done         │ DONE            │ 18        │
│ 10101 │ Closed       │ DONE            │ 12        │
│ 10102 │ Resolved     │ DONE            │ 10        │
└───────┴──────────────┴─────────────────┴───────────┘

Total: 12 statuses
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Lists all statuses in active workflows
- [ ] Filter by status category
- [ ] Filter by workflow
- [ ] Shows workflow usage count
- [ ] Group by category option
- [ ] Table and JSON output

**Commits:**
1. `test(jira-admin): add failing tests for list_statuses`
2. `feat(jira-admin): implement list_statuses.py (7/7 tests passing)`

---

## Phase 4.7: Workflow for Issues

### Feature 4.7.1: Get Workflow Information for Issue

**Script:** `get_workflow_for_issue.py`

**JIRA API:**
- `GET /rest/api/2/issue/{issueIdOrKey}/transitions` - Get available transitions
- `GET /rest/api/3/workflowscheme/project` - Get project's workflow scheme
- `GET /rest/api/3/workflow/search` - Get workflow details

**Test Cases:**
```python
def test_get_workflow_for_issue_basic():
    """Test getting workflow information for an issue."""

def test_get_workflow_for_issue_show_current_status():
    """Test showing issue's current status."""

def test_get_workflow_for_issue_show_transitions():
    """Test showing available transitions from current status."""

def test_get_workflow_for_issue_show_workflow_name():
    """Test showing which workflow the issue uses."""

def test_get_workflow_for_issue_show_scheme():
    """Test showing the workflow scheme for the project."""

def test_get_workflow_for_issue_format_table():
    """Test table output format."""

def test_get_workflow_for_issue_invalid_issue():
    """Test error handling for invalid issue key."""
```

**CLI Interface:**
```bash
# Get workflow info for issue
python get_workflow_for_issue.py PROJ-123

# Show available transitions
python get_workflow_for_issue.py PROJ-123 --show-transitions

# Show workflow scheme
python get_workflow_for_issue.py PROJ-123 --show-scheme

# JSON output
python get_workflow_for_issue.py PROJ-123 --output json
```

**Output Example:**
```
Issue: PROJ-123
Type: Story
Current Status: In Progress (10001)

Workflow Information:
  Workflow: Software Development Workflow
  Workflow Scheme: Software Development Scheme (ID: 10100)

Available Transitions (3):
┌────┬──────────────────┬──────────────┐
│ ID │ Name             │ To Status    │
├────┼──────────────────┼──────────────┤
│ 21 │ Send to Review   │ Code Review  │
│ 41 │ Send to Testing  │ Testing      │
│ 71 │ Stop Progress    │ To Do        │
└────┴──────────────────┴──────────────┘
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Shows issue's current status
- [ ] Shows workflow name
- [ ] Shows available transitions
- [ ] Shows workflow scheme
- [ ] Table and JSON output
- [ ] Clear error for invalid issue

**Commits:**
1. `test(jira-admin): add failing tests for get_workflow_for_issue`
2. `feat(jira-admin): implement get_workflow_for_issue.py (7/7 tests passing)`

---

## Phase Completion Summary

### Phase 4 Completion

- [ ] **Phase 4 Summary:**
  - [ ] 8 scripts implemented
  - [ ] 59 tests passing
  - [ ] Coverage ≥ 85%
  - [ ] All JiraClient methods added
  - **Final Commit:** `feat(jira-admin): complete Phase 4 - Workflow Management (8 scripts, 59/59 tests passing)`

---

## Integration & Documentation

### Integration Tasks

- [ ] **Integration 4.1:** Workflow discovery wizard
  - [ ] Interactive script to discover workflows across projects
  - [ ] Recommends workflow standardization
  - **Commit:** `feat(jira-admin): add workflow discovery wizard`

- [ ] **Integration 4.2:** Workflow scheme migration helper
  - [ ] Analyzes current project workflows
  - [ ] Generates status migration mappings
  - [ ] Validates mappings before applying
  - **Commit:** `feat(jira-admin): add workflow scheme migration helper`

### Documentation Updates

- [ ] **Docs 4.1:** Update SKILL.md for jira-admin
  - [ ] Document workflow management scripts
  - [ ] Add workflow examples
  - [ ] Document limitations clearly

- [ ] **Docs 4.2:** Update CLAUDE.md
  - [ ] Add workflow management patterns
  - [ ] Document API limitations
  - [ ] Add workflow scheme assignment guidance

- [ ] **Docs 4.3:** Update GAP_ANALYSIS.md
  - [ ] Mark workflow management as complete
  - [ ] Document what's not possible via API

---

## API Limitations and Workarounds

### What You CANNOT Do via REST API

1. **Create New Workflows:**
   - **Limitation:** Creating workflows via REST API is extremely limited
   - **Workaround:** Use JIRA UI workflow designer
   - **Alternative:** For simple workflows, use workflow templates during project creation

2. **Modify Workflow Transitions:**
   - **Limitation:** Cannot add/remove/modify transitions via REST API
   - **Workaround:** Use JIRA UI workflow designer
   - **Alternative:** Create workflow scheme drafts for limited modifications

3. **Configure Transition Rules:**
   - **Limitation:** Cannot configure conditions, validators, post-functions via REST API
   - **Workaround:** Use JIRA UI workflow designer or ScriptRunner

4. **Create New Statuses:**
   - **Limitation:** Status creation not supported in standard REST API
   - **Workaround:** Use JIRA UI or Workflow Designer

5. **Modify Workflow Scheme Mappings (Except via Draft):**
   - **Limitation:** Direct modification requires draft-publish cycle
   - **Workaround:** Use create draft → modify → publish pattern

### What You CAN Do via REST API

1. **Discovery:**
   - ✅ List all workflows
   - ✅ Get workflow details (statuses, transitions)
   - ✅ Search workflows
   - ✅ Get workflow usage

2. **Workflow Schemes:**
   - ✅ List workflow schemes
   - ✅ Get workflow scheme details
   - ✅ Get project's workflow scheme
   - ✅ Assign workflow scheme to project

3. **Status Operations:**
   - ✅ List all statuses
   - ✅ Get status details
   - ✅ Filter statuses by category

4. **Issue-Level Operations:**
   - ✅ Get available transitions for issue
   - ✅ Transition issues (already covered in jira-lifecycle)
   - ✅ Get workflow information for issue

### Recommended Approach

For comprehensive workflow management, use this hybrid approach:

1. **Use REST API for:**
   - Discovery and inspection
   - Workflow scheme assignment
   - Bulk operations
   - Automation and scripting

2. **Use JIRA UI for:**
   - Creating new workflows
   - Modifying workflow transitions
   - Configuring transition rules
   - Creating new statuses

3. **Use ScriptRunner for:**
   - Advanced workflow automation
   - Custom transition post-functions
   - Workflow event listeners

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 59 unit tests passing
- [ ] Coverage ≥ 85%
- [ ] Live integration tests (optional)

**Scripts:**
- [ ] 8 new scripts implemented
- [ ] All scripts have `--help`
- [ ] All scripts support `--profile`
- [ ] All mutation scripts have `--dry-run` and `--confirm`

**Documentation:**
- [ ] Implementation plan complete
- [ ] SKILL.md updated with workflow examples
- [ ] CLAUDE.md updated with workflow patterns
- [ ] Limitations clearly documented

**JiraClient Methods:**
- [ ] 10 new methods added to shared library
- [ ] All methods include docstrings
- [ ] Error handling for permission issues

---

## Summary Metrics

| Script | Tests | Priority | Complexity |
|--------|-------|----------|------------|
| list_workflows.py | 9 | **Critical** | Medium |
| get_workflow.py | 9 | High | Medium |
| search_workflows.py | 7 | High | Low |
| list_workflow_schemes.py | 7 | **Critical** | Low |
| get_workflow_scheme.py | 7 | High | Low |
| assign_workflow_scheme.py | 8 | High | High |
| list_statuses.py | 7 | High | Low |
| get_workflow_for_issue.py | 7 | Medium | Medium |
| **TOTAL** | **59** | - | - |

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Admin permissions required | High | High | Document permission requirements clearly |
| Workflow creation not supported | High | Medium | Document limitations, provide UI guidance |
| Async workflow scheme assignment | Medium | Medium | Implement progress tracking |
| API deprecations (June 2026) | Medium | Low | Use recommended bulk operations |
| Status listing incomplete | Medium | Medium | Document limitation (only active workflows) |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Incorrect status mappings | Medium | High | Require explicit mappings file, dry-run mode |
| Breaking existing projects | Low | Critical | Require confirmation, show current state |
| Large instance performance | Medium | Medium | Implement pagination, caching |

---

## References

### Official Documentation

- [Jira Cloud REST API - Workflows](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflows/)
- [Jira Cloud Platform Changelog](https://developer.atlassian.com/cloud/jira/platform/changelog/)
- [New Workflow REST APIs Announcement](https://community.developer.atlassian.com/t/new-workflow-rest-apis-in-jira-cloud/30697)
- [Workflow Scheme Switching API](https://developer.atlassian.com/cloud/jira/platform/changelog/) (Experimental)

### Community Resources

- [How to change project's workflow via REST API](https://community.atlassian.com/forums/Jira-questions/How-to-change-jira-project-s-workflow-via-REST-API/qaq-p/598536)
- [Creating workflows via REST API limitations](https://community.developer.atlassian.com/t/how-can-i-create-a-connect-workflow-via-rest-api/64307)
- [Workflow Scheme Draft Publish](https://community.developer.atlassian.com/t/help-with-workflow-scheme-draft-publish-rest-api/94518)

### API Deprecation Notices

- Workflow transition properties endpoints will be removed **June 1, 2026**
- Some workflow creation APIs will be removed **February 1, 2026**
- Workflow history only available from **October 30, 2025** onwards

---

**Document Version:** 1.0
**Created:** 2025-12-26
**Status:** Ready for Implementation
**Estimated Effort:** 3-4 days for full implementation
**Prerequisites:** Phase 1 (Project Management) should be complete for workflow scheme assignment to projects
