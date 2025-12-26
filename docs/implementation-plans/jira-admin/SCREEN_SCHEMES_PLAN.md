# Screen Schemes - TDD Implementation Plan

## Implementation Status

**Overall Status:** NOT STARTED

**Planned Scripts:**
- [ ] `list_screens.py` - List all screens
- [ ] `get_screen.py` - Get screen details with tabs and fields
- [ ] `list_screen_tabs.py` - List tabs for a screen
- [ ] `get_screen_fields.py` - Get fields for a screen tab
- [ ] `add_field_to_screen.py` - Add field to screen tab
- [ ] `remove_field_from_screen.py` - Remove field from screen tab
- [ ] `list_screen_schemes.py` - List all screen schemes
- [ ] `get_screen_scheme.py` - Get screen scheme details
- [ ] `list_issue_type_screen_schemes.py` - List issue type screen schemes
- [ ] `get_issue_type_screen_scheme.py` - Get issue type screen scheme details
- [ ] `get_project_screens.py` - Get screens used by a project

**JiraClient Methods to Add:**
- [ ] `get_screens()` - List all screens
- [ ] `get_screen(screen_id)` - Get screen details
- [ ] `get_screen_tabs(screen_id)` - Get tabs for screen
- [ ] `get_screen_tab_fields(screen_id, tab_id)` - Get fields for tab
- [ ] `add_field_to_screen_tab(screen_id, tab_id, field_id)` - Add field to tab
- [ ] `remove_field_from_screen_tab(screen_id, tab_id, field_id)` - Remove field from tab
- [ ] `get_screen_schemes()` - List screen schemes
- [ ] `get_screen_scheme(scheme_id)` - Get screen scheme details
- [ ] `get_issue_type_screen_schemes()` - List issue type screen schemes
- [ ] `get_issue_type_screen_scheme(scheme_id)` - Get issue type screen scheme details
- [ ] `get_project_issue_type_screen_schemes(project_key)` - Get schemes for project

**Test Coverage:**
- Unit tests: 0/60+ planned
- Live integration tests: Not yet available
- Coverage: Target 85%+

**Last Updated:** 2025-12-26

---

## Overview

**Objective:** Implement comprehensive JIRA screen and screen scheme management functionality using Test-Driven Development (TDD)

**Screens Hierarchy:** Understanding the three-tier structure is critical:

```
Issue Type Screen Schemes (Project Level)
  ├── Maps issue types to Screen Schemes
  ├── Assigned to projects
  └── Example: "Default Issue Type Screen Scheme"
      │
      ├── Issue Type: Bug → Screen Scheme: "Bug Screens"
      ├── Issue Type: Story → Screen Scheme: "Default Screen Scheme"
      └── Issue Type: Epic → Screen Scheme: "Epic Screens"

Screen Schemes (Issue Type Level)
  ├── Maps operations to Screens
  ├── Operations: Create, Edit, View
  └── Example: "Default Screen Scheme"
      │
      ├── Operation: Create → Screen: "Default Screen"
      ├── Operation: Edit → Screen: "Default Screen"
      └── Operation: View → Screen: "Default Screen"

Screens (Field Level)
  ├── Contains Tabs
  ├── Tabs contain Fields
  └── Example: "Default Screen"
      │
      ├── Tab: "Field Tab"
      │   ├── Field: Summary
      │   ├── Field: Description
      │   ├── Field: Assignee
      │   └── Field: Priority
      └── Tab: "Custom Fields"
          ├── Field: Story Points
          └── Field: Sprint
```

**Use Cases:**
- Discover which screens are used by a project
- Add custom fields to screens for specific issue types
- Audit field visibility across different operations (create/edit/view)
- Configure different field sets for different issue types

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
1. **Phase 1: Screen Operations** (CRUD for screens, tabs, and fields)
2. **Phase 2: Screen Schemes** (Screen scheme discovery and management)
3. **Phase 3: Issue Type Screen Schemes** (Project-level scheme management)
4. **Phase 4: Project Screen Discovery** (Find screens used by projects)

---

## JIRA API Reference

### Screens API Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|---------------------|
| GET | `/rest/api/3/screens` | Get all screens | Administer Jira |
| GET | `/rest/api/2/screens` | Get all screens (v2) | Administer Jira |
| POST | `/rest/api/2/screens` | Create screen | Administer Jira |
| PUT | `/rest/api/2/screens/{screenId}` | Update screen | Administer Jira |
| DELETE | `/rest/api/2/screens/{screenId}` | Delete screen | Administer Jira |
| GET | `/rest/api/2/screens/{screenId}/availableFields` | Get available fields | Administer Jira |
| GET | `/rest/api/2/field/{fieldId}/screens` | Get screens for field | Administer Jira |

### Screen Tab Fields API Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|---------------------|
| GET | `/rest/api/2/screens/{screenId}/tabs/{tabId}/fields` | Get all fields for tab | Administer Jira |
| POST | `/rest/api/2/screens/{screenId}/tabs/{tabId}/fields` | Add field to tab | Administer Jira |
| DELETE | `/rest/api/2/screens/{screenId}/tabs/{tabId}/fields/{id}` | Remove field from tab | Administer Jira |
| POST | `/rest/api/2/screens/{screenId}/tabs/{tabId}/fields/{id}/move` | Move field position | Administer Jira |

### Screen Schemes API Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|---------------------|
| GET | `/rest/api/3/screenscheme` | Get screen schemes | Administer Jira |
| POST | `/rest/api/3/screenscheme` | Create screen scheme | Administer Jira |
| PUT | `/rest/api/3/screenscheme/{screenSchemeId}` | Update screen scheme | Administer Jira |
| DELETE | `/rest/api/3/screenscheme/{screenSchemeId}` | Delete screen scheme | Administer Jira |

### Issue Type Screen Schemes API Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|---------------------|
| POST | `/rest/api/3/issuetypescreenscheme` | Create issue type screen scheme | Administer Jira |
| GET | `/rest/api/3/issuetypescreenscheme/mapping` | Get issue type screen scheme items | Administer Jira |
| GET | `/rest/api/3/issuetypescreenscheme/project` | Get schemes for projects | Administer Jira |
| PUT | `/rest/api/3/issuetypescreenscheme/project` | Assign scheme to project | Administer Jira |

---

## API Response Examples

### GET /rest/api/2/screens - List Screens Response

```json
{
  "maxResults": 100,
  "startAt": 0,
  "total": 5,
  "isLast": true,
  "values": [
    {
      "id": 1,
      "name": "Default Screen",
      "description": "The default screen for all issue operations",
      "scope": {
        "type": "PROJECT",
        "project": {
          "id": "10000"
        }
      }
    },
    {
      "id": 2,
      "name": "Resolve Issue Screen",
      "description": "Screen shown when resolving issues"
    },
    {
      "id": 3,
      "name": "Workflow Screen",
      "description": "Screen for workflow transitions"
    }
  ]
}
```

### GET /rest/api/2/screens/{screenId}/tabs/{tabId}/fields - Screen Tab Fields Response

```json
[
  {
    "id": "summary",
    "name": "Summary"
  },
  {
    "id": "issuetype",
    "name": "Issue Type"
  },
  {
    "id": "priority",
    "name": "Priority"
  },
  {
    "id": "description",
    "name": "Description"
  },
  {
    "id": "assignee",
    "name": "Assignee"
  },
  {
    "id": "customfield_10016",
    "name": "Story Points"
  }
]
```

### POST /rest/api/2/screens/{screenId}/tabs/{tabId}/fields - Add Field Request

```json
{
  "fieldId": "customfield_10016"
}
```

### GET /rest/api/3/screenscheme - List Screen Schemes Response

```json
{
  "maxResults": 100,
  "startAt": 0,
  "total": 3,
  "isLast": true,
  "values": [
    {
      "id": 1,
      "name": "Default Screen Scheme",
      "description": "The default screen scheme",
      "screens": {
        "default": 1,
        "edit": 1,
        "view": 1,
        "create": 1
      }
    },
    {
      "id": 2,
      "name": "Bug Screen Scheme",
      "description": "Custom screen scheme for bugs",
      "screens": {
        "default": 2,
        "edit": 2,
        "view": 1
      }
    }
  ]
}
```

### GET /rest/api/3/issuetypescreenscheme/project - Issue Type Screen Schemes Response

```json
{
  "maxResults": 100,
  "startAt": 0,
  "total": 2,
  "isLast": true,
  "values": [
    {
      "issueTypeScreenScheme": {
        "id": "10000",
        "name": "Default Issue Type Screen Scheme",
        "description": "The default issue type screen scheme"
      },
      "projectIds": ["10000", "10001", "10002"]
    },
    {
      "issueTypeScreenScheme": {
        "id": "10001",
        "name": "Software Project Screen Scheme",
        "description": "Screen scheme for software projects"
      },
      "projectIds": ["10003"]
    }
  ]
}
```

---

## Test Infrastructure Setup

### Initial Setup Tasks

- [ ] **Setup 1.1:** Create test infrastructure
  - [ ] Create `tests/test_screen_operations.py`
  - [ ] Create `tests/test_screen_schemes.py`
  - [ ] Create `tests/test_issue_type_screen_schemes.py`
  - [ ] Add screen fixtures to `tests/conftest.py`
  - [ ] Mock screen API endpoints
  - **Commit:** `test(jira-admin): add screen management test fixtures`

- [ ] **Setup 1.2:** Add JiraClient methods for screens
  - [ ] `get_screens()` - List all screens
  - [ ] `get_screen(screen_id)` - Get screen details
  - [ ] `get_screen_tabs(screen_id)` - Get tabs for screen
  - [ ] `get_screen_tab_fields(screen_id, tab_id)` - Get fields for tab
  - [ ] `add_field_to_screen_tab(screen_id, tab_id, field_id)` - Add field
  - [ ] `remove_field_from_screen_tab(screen_id, tab_id, field_id)` - Remove field
  - **Commit:** `feat(shared): add screen API methods to JiraClient`

- [ ] **Setup 1.3:** Add JiraClient methods for screen schemes
  - [ ] `get_screen_schemes()` - List screen schemes
  - [ ] `get_screen_scheme(scheme_id)` - Get scheme details
  - [ ] `get_issue_type_screen_schemes()` - List issue type screen schemes
  - [ ] `get_issue_type_screen_scheme(scheme_id)` - Get scheme details
  - [ ] `get_project_issue_type_screen_schemes(project_key)` - Get schemes for project
  - **Commit:** `feat(shared): add screen scheme API methods to JiraClient`

---

## Phase 1: Screen Operations

### Feature 1.1: List Screens

**Script:** `list_screens.py`

**JIRA API:**
- `GET /rest/api/2/screens` - List all screens

**Test File:** `tests/test_screen_operations.py`

**Test Cases:**
```python
def test_list_all_screens():
    """Test listing all screens."""

def test_list_screens_with_pagination():
    """Test handling paginated screen results."""

def test_filter_screens_by_name():
    """Test filtering screens by name pattern."""

def test_format_text_output():
    """Test human-readable table output."""

def test_format_json_output():
    """Test JSON output format."""

def test_empty_screens():
    """Test output when no screens exist."""

def test_screen_has_required_fields():
    """Test that each screen has id, name, description."""
```

**CLI Interface:**
```bash
# List all screens
python list_screens.py

# Filter by name
python list_screens.py --filter "Default"

# JSON output
python list_screens.py --output json

# Pagination
python list_screens.py --start-at 0 --max-results 50
```

**Output Example:**
```
Available Screens:

ID  Name                      Description
──  ────────────────────────  ──────────────────────────────────
1   Default Screen            The default screen for all operations
2   Resolve Issue Screen      Screen shown when resolving issues
3   Workflow Screen           Screen for workflow transitions
10  Bug Create Screen         Custom screen for creating bugs
11  Epic Screen               Screen for epic issue types

Total: 5 screens
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Lists all screens with ID, name, description
- [ ] Supports text and JSON output
- [ ] Handles pagination correctly
- [ ] Optional name filtering

**Commits:**
1. `test(jira-admin): add failing tests for list_screens`
2. `feat(jira-admin): implement list_screens.py (7/7 tests passing)`

---

### Feature 1.2: Get Screen Details

**Script:** `get_screen.py`

**JIRA API:**
- `GET /rest/api/2/screens/{screenId}` - Get screen details
- `GET /rest/api/2/screens/{screenId}/tabs` - Get screen tabs
- `GET /rest/api/2/screens/{screenId}/tabs/{tabId}/fields` - Get tab fields

**Test Cases:**
```python
def test_get_screen_basic():
    """Test getting basic screen details."""

def test_get_screen_with_tabs():
    """Test including tabs in output."""

def test_get_screen_with_fields():
    """Test including all fields from all tabs."""

def test_get_screen_by_id():
    """Test fetching screen by numeric ID."""

def test_get_screen_not_found():
    """Test error handling for invalid screen ID."""

def test_format_detailed_output():
    """Test detailed human-readable output with tabs and fields."""
```

**CLI Interface:**
```bash
# Get screen details
python get_screen.py 1

# Include tabs
python get_screen.py 1 --show-tabs

# Include all fields
python get_screen.py 1 --show-tabs --show-fields

# JSON output
python get_screen.py 1 --output json
```

**Output Example:**
```
Screen Details:

ID:          1
Name:        Default Screen
Description: The default screen for all operations

Tabs:
  Tab 1: Field Tab
    - summary (Summary)
    - issuetype (Issue Type)
    - priority (Priority)
    - description (Description)
    - assignee (Assignee)
    - reporter (Reporter)
    - labels (Labels)

  Tab 2: Custom Fields
    - customfield_10016 (Story Points)
    - customfield_10014 (Epic Link)

Total Fields: 9
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Shows screen ID, name, description
- [ ] Optional tabs display
- [ ] Optional fields display
- [ ] Handles invalid screen IDs gracefully

**Commits:**
1. `test(jira-admin): add failing tests for get_screen`
2. `feat(jira-admin): implement get_screen.py (6/6 tests passing)`

---

### Feature 1.3: List Screen Tabs

**Script:** `list_screen_tabs.py`

**JIRA API:**
- `GET /rest/api/2/screens/{screenId}/tabs` - Get screen tabs

**Test Cases:**
```python
def test_list_screen_tabs():
    """Test listing all tabs for a screen."""

def test_list_tabs_with_field_count():
    """Test including field count per tab."""

def test_list_tabs_format_text():
    """Test human-readable table output."""

def test_list_tabs_format_json():
    """Test JSON output format."""

def test_screen_not_found():
    """Test error handling for invalid screen ID."""
```

**CLI Interface:**
```bash
# List tabs
python list_screen_tabs.py 1

# Include field counts
python list_screen_tabs.py 1 --show-field-count

# JSON output
python list_screen_tabs.py 1 --output json
```

**Output Example:**
```
Screen Tabs for: Default Screen (ID: 1)

Tab ID  Name            Position  Field Count
──────  ──────────────  ────────  ───────────
10000   Field Tab       0         7
10001   Custom Fields   1         2

Total: 2 tabs
```

**Acceptance Criteria:**
- [ ] All 5 tests pass
- [ ] Lists tab ID, name, position
- [ ] Optional field count display
- [ ] Text and JSON output formats

**Commits:**
1. `test(jira-admin): add failing tests for list_screen_tabs`
2. `feat(jira-admin): implement list_screen_tabs.py (5/5 tests passing)`

---

### Feature 1.4: Get Screen Tab Fields

**Script:** `get_screen_fields.py`

**JIRA API:**
- `GET /rest/api/2/screens/{screenId}/tabs/{tabId}/fields` - Get fields for tab

**Test Cases:**
```python
def test_get_screen_tab_fields():
    """Test getting all fields for a specific tab."""

def test_get_all_screen_fields():
    """Test getting fields from all tabs when no tab specified."""

def test_filter_fields_by_type():
    """Test filtering fields by type (system vs custom)."""

def test_show_field_details():
    """Test showing detailed field information."""

def test_format_text_output():
    """Test human-readable table output."""

def test_format_json_output():
    """Test JSON output format."""
```

**CLI Interface:**
```bash
# Get fields for specific tab
python get_screen_fields.py 1 --tab-id 10000

# Get all fields from all tabs
python get_screen_fields.py 1

# Filter custom fields only
python get_screen_fields.py 1 --type custom

# Show detailed field info
python get_screen_fields.py 1 --show-details

# JSON output
python get_screen_fields.py 1 --output json
```

**Output Example:**
```
Fields for Screen: Default Screen (ID: 1)

Tab: Field Tab
Field ID              Name            Type      Required
────────────────────  ──────────────  ────────  ────────
summary               Summary         system    Yes
issuetype             Issue Type      system    Yes
priority              Priority        system    No
description           Description     system    No
assignee              Assignee        system    No
reporter              Reporter        system    Yes
labels                Labels          system    No

Tab: Custom Fields
Field ID              Name            Type      Required
────────────────────  ──────────────  ────────  ────────
customfield_10016     Story Points    custom    No
customfield_10014     Epic Link       custom    No

Total Fields: 9 (7 system, 2 custom)
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Lists field ID, name, type
- [ ] Can filter to specific tab or all tabs
- [ ] Can filter by field type (system/custom)
- [ ] Text and JSON output formats

**Commits:**
1. `test(jira-admin): add failing tests for get_screen_fields`
2. `feat(jira-admin): implement get_screen_fields.py (6/6 tests passing)`

---

### Feature 1.5: Add Field to Screen

**Script:** `add_field_to_screen.py`

**JIRA API:**
- `GET /rest/api/2/screens/{screenId}/tabs` - Get tabs to find tab ID
- `POST /rest/api/2/screens/{screenId}/tabs/{tabId}/fields` - Add field to tab

**Test Cases:**
```python
def test_add_field_to_tab():
    """Test adding field to specific tab."""

def test_add_field_to_default_tab():
    """Test adding field to first tab when no tab specified."""

def test_add_field_already_exists():
    """Test error handling when field already on screen."""

def test_add_field_invalid_field_id():
    """Test error handling for invalid field ID."""

def test_add_field_dry_run():
    """Test dry-run mode without making changes."""

def test_add_field_with_confirmation():
    """Test confirmation prompt before adding."""
```

**CLI Interface:**
```bash
# Add field to specific tab
python add_field_to_screen.py 1 --field-id customfield_10020 --tab-id 10001

# Add field to first tab (default)
python add_field_to_screen.py 1 --field-id customfield_10020

# Add field with tab name instead of ID
python add_field_to_screen.py 1 --field-id customfield_10020 --tab-name "Custom Fields"

# Dry run
python add_field_to_screen.py 1 --field-id customfield_10020 --dry-run

# With confirmation
python add_field_to_screen.py 1 --field-id customfield_10020 --confirm
```

**Output Example:**
```
Adding field to screen...

Screen:  Default Screen (ID: 1)
Tab:     Custom Fields (ID: 10001)
Field:   customfield_10020 (Sprint)

Field added successfully.

Current fields on tab "Custom Fields":
- customfield_10016 (Story Points)
- customfield_10014 (Epic Link)
- customfield_10020 (Sprint)
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Adds field to specified tab
- [ ] Supports tab ID or tab name
- [ ] Defaults to first tab if not specified
- [ ] Dry-run mode available
- [ ] Confirmation prompt option

**Commits:**
1. `test(jira-admin): add failing tests for add_field_to_screen`
2. `feat(jira-admin): implement add_field_to_screen.py (6/6 tests passing)`

---

### Feature 1.6: Remove Field from Screen

**Script:** `remove_field_from_screen.py`

**JIRA API:**
- `GET /rest/api/2/screens/{screenId}/tabs` - Get tabs
- `GET /rest/api/2/screens/{screenId}/tabs/{tabId}/fields` - Get fields to find field
- `DELETE /rest/api/2/screens/{screenId}/tabs/{tabId}/fields/{id}` - Remove field

**Test Cases:**
```python
def test_remove_field_from_tab():
    """Test removing field from specific tab."""

def test_remove_field_search_all_tabs():
    """Test finding and removing field from any tab."""

def test_remove_field_not_found():
    """Test error handling when field not on screen."""

def test_remove_field_dry_run():
    """Test dry-run mode without making changes."""

def test_remove_required_field_warning():
    """Test warning when removing required field."""

def test_remove_field_with_confirmation():
    """Test confirmation prompt before removal."""
```

**CLI Interface:**
```bash
# Remove field from specific tab
python remove_field_from_screen.py 1 --field-id customfield_10020 --tab-id 10001

# Remove field (search all tabs)
python remove_field_from_screen.py 1 --field-id customfield_10020

# Dry run
python remove_field_from_screen.py 1 --field-id customfield_10020 --dry-run

# Force removal without confirmation
python remove_field_from_screen.py 1 --field-id customfield_10020 --force
```

**Output Example:**
```
Removing field from screen...

Screen:  Default Screen (ID: 1)
Tab:     Custom Fields (ID: 10001)
Field:   customfield_10020 (Sprint)

WARNING: This field may be required by some issue types.

Confirm removal? [y/N]: y

Field removed successfully.

Remaining fields on tab "Custom Fields":
- customfield_10016 (Story Points)
- customfield_10014 (Epic Link)
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Removes field from specified tab
- [ ] Can search all tabs if tab not specified
- [ ] Dry-run mode available
- [ ] Warns about required fields
- [ ] Confirmation prompt option

**Commits:**
1. `test(jira-admin): add failing tests for remove_field_from_screen`
2. `feat(jira-admin): implement remove_field_from_screen.py (6/6 tests passing)`

---

### Phase 1 Completion

- [ ] **Phase 1 Summary:**
  - [ ] 6 scripts implemented
  - [ ] 36 tests passing
  - [ ] Coverage ≥ 85%
  - **Commit:** `docs(jira-admin): complete Phase 1 - Screen Operations`

---

## Phase 2: Screen Schemes

### Feature 2.1: List Screen Schemes

**Script:** `list_screen_schemes.py`

**JIRA API:**
- `GET /rest/api/3/screenscheme` - List screen schemes

**Test File:** `tests/test_screen_schemes.py`

**Test Cases:**
```python
def test_list_all_screen_schemes():
    """Test listing all screen schemes."""

def test_list_schemes_with_pagination():
    """Test handling paginated results."""

def test_filter_schemes_by_name():
    """Test filtering schemes by name pattern."""

def test_show_scheme_mappings():
    """Test showing screen mappings (create/edit/view)."""

def test_format_text_output():
    """Test human-readable table output."""

def test_format_json_output():
    """Test JSON output format."""

def test_empty_screen_schemes():
    """Test output when no screen schemes exist."""
```

**CLI Interface:**
```bash
# List all screen schemes
python list_screen_schemes.py

# Filter by name
python list_screen_schemes.py --filter "Default"

# Show screen mappings
python list_screen_schemes.py --show-screens

# JSON output
python list_screen_schemes.py --output json
```

**Output Example:**
```
Available Screen Schemes:

ID  Name                          Description
──  ────────────────────────────  ────────────────────────────────
1   Default Screen Scheme         The default screen scheme
2   Bug Screen Scheme             Custom screen scheme for bugs
3   Software Development Scheme   Screens for software projects

Total: 3 screen schemes
```

**With --show-screens:**
```
Available Screen Schemes:

ID  Name                      Create Screen      Edit Screen        View Screen
──  ────────────────────────  ─────────────────  ─────────────────  ─────────────────
1   Default Screen Scheme     Default Screen     Default Screen     Default Screen
2   Bug Screen Scheme         Bug Create Screen  Bug Edit Screen    Default Screen
3   Software Dev Scheme       Default Screen     Workflow Screen    Default Screen

Total: 3 screen schemes
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Lists scheme ID, name, description
- [ ] Optional screen mappings display
- [ ] Text and JSON output formats
- [ ] Name filtering support

**Commits:**
1. `test(jira-admin): add failing tests for list_screen_schemes`
2. `feat(jira-admin): implement list_screen_schemes.py (7/7 tests passing)`

---

### Feature 2.2: Get Screen Scheme Details

**Script:** `get_screen_scheme.py`

**JIRA API:**
- `GET /rest/api/3/screenscheme/{screenSchemeId}` - Get scheme details

**Test Cases:**
```python
def test_get_screen_scheme_basic():
    """Test getting basic scheme details."""

def test_get_screen_scheme_with_screens():
    """Test including screen details for each operation."""

def test_get_screen_scheme_by_id():
    """Test fetching scheme by numeric ID."""

def test_get_screen_scheme_not_found():
    """Test error handling for invalid scheme ID."""

def test_format_detailed_output():
    """Test detailed human-readable output."""
```

**CLI Interface:**
```bash
# Get scheme details
python get_screen_scheme.py 1

# Include screen details
python get_screen_scheme.py 1 --show-screen-details

# JSON output
python get_screen_scheme.py 1 --output json
```

**Output Example:**
```
Screen Scheme Details:

ID:          1
Name:        Default Screen Scheme
Description: The default screen scheme

Screen Mappings:
  Create Operation: Default Screen (ID: 1)
  Edit Operation:   Default Screen (ID: 1)
  View Operation:   Default Screen (ID: 1)

Used by Issue Type Screen Schemes:
  - Default Issue Type Screen Scheme (ID: 10000)
  - Software Project Screen Scheme (ID: 10001)
```

**Acceptance Criteria:**
- [ ] All 5 tests pass
- [ ] Shows scheme ID, name, description
- [ ] Shows screen mappings for operations
- [ ] Optional screen details
- [ ] Shows usage information

**Commits:**
1. `test(jira-admin): add failing tests for get_screen_scheme`
2. `feat(jira-admin): implement get_screen_scheme.py (5/5 tests passing)`

---

### Phase 2 Completion

- [ ] **Phase 2 Summary:**
  - [ ] 2 scripts implemented
  - [ ] 12 tests passing
  - [ ] Coverage ≥ 85%
  - **Commit:** `docs(jira-admin): complete Phase 2 - Screen Schemes`

---

## Phase 3: Issue Type Screen Schemes

### Feature 3.1: List Issue Type Screen Schemes

**Script:** `list_issue_type_screen_schemes.py`

**JIRA API:**
- `GET /rest/api/3/issuetypescreenscheme/project` - List schemes with projects

**Test File:** `tests/test_issue_type_screen_schemes.py`

**Test Cases:**
```python
def test_list_all_issue_type_screen_schemes():
    """Test listing all issue type screen schemes."""

def test_list_schemes_with_projects():
    """Test including project associations."""

def test_filter_schemes_by_name():
    """Test filtering schemes by name pattern."""

def test_format_text_output():
    """Test human-readable table output."""

def test_format_json_output():
    """Test JSON output format."""

def test_empty_schemes():
    """Test output when no schemes exist."""
```

**CLI Interface:**
```bash
# List all issue type screen schemes
python list_issue_type_screen_schemes.py

# Show project associations
python list_issue_type_screen_schemes.py --show-projects

# Filter by name
python list_issue_type_screen_schemes.py --filter "Default"

# JSON output
python list_issue_type_screen_schemes.py --output json
```

**Output Example:**
```
Available Issue Type Screen Schemes:

ID     Name                                  Description
─────  ────────────────────────────────────  ────────────────────────────────────
10000  Default Issue Type Screen Scheme      The default scheme
10001  Software Project Screen Scheme        Scheme for software projects
10002  Bug Tracking Screen Scheme            Scheme for bug tracking

Total: 3 issue type screen schemes
```

**With --show-projects:**
```
Available Issue Type Screen Schemes:

ID     Name                                  Projects
─────  ────────────────────────────────────  ────────────────────────────
10000  Default Issue Type Screen Scheme      PROJ, TEST, DEMO (3 projects)
10001  Software Project Screen Scheme        DEV (1 project)
10002  Bug Tracking Screen Scheme            BUG, QA (2 projects)

Total: 3 issue type screen schemes
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Lists scheme ID, name, description
- [ ] Optional project associations display
- [ ] Text and JSON output formats
- [ ] Name filtering support

**Commits:**
1. `test(jira-admin): add failing tests for list_issue_type_screen_schemes`
2. `feat(jira-admin): implement list_issue_type_screen_schemes.py (6/6 tests passing)`

---

### Feature 3.2: Get Issue Type Screen Scheme Details

**Script:** `get_issue_type_screen_scheme.py`

**JIRA API:**
- `GET /rest/api/3/issuetypescreenscheme/mapping` - Get scheme mappings
- `GET /rest/api/3/issuetypescreenscheme/project` - Get scheme with projects

**Test Cases:**
```python
def test_get_issue_type_screen_scheme_basic():
    """Test getting basic scheme details."""

def test_get_scheme_with_mappings():
    """Test including issue type to screen scheme mappings."""

def test_get_scheme_with_projects():
    """Test including associated projects."""

def test_get_scheme_not_found():
    """Test error handling for invalid scheme ID."""

def test_format_detailed_output():
    """Test detailed human-readable output."""
```

**CLI Interface:**
```bash
# Get scheme details
python get_issue_type_screen_scheme.py 10000

# Include issue type mappings
python get_issue_type_screen_scheme.py 10000 --show-mappings

# Include project associations
python get_issue_type_screen_scheme.py 10000 --show-projects

# JSON output
python get_issue_type_screen_scheme.py 10000 --output json
```

**Output Example:**
```
Issue Type Screen Scheme Details:

ID:          10000
Name:        Default Issue Type Screen Scheme
Description: The default issue type screen scheme

Issue Type Mappings:
  Bug           → Bug Screen Scheme (ID: 2)
  Story         → Default Screen Scheme (ID: 1)
  Epic          → Epic Screen Scheme (ID: 3)
  Task          → Default Screen Scheme (ID: 1)
  Default       → Default Screen Scheme (ID: 1)

Associated Projects:
  - PROJ (My Project)
  - TEST (Test Project)
  - DEMO (Demo Project)

Total Issue Types: 5
Total Projects: 3
```

**Acceptance Criteria:**
- [ ] All 5 tests pass
- [ ] Shows scheme ID, name, description
- [ ] Shows issue type to screen scheme mappings
- [ ] Shows associated projects
- [ ] Detailed output format

**Commits:**
1. `test(jira-admin): add failing tests for get_issue_type_screen_scheme`
2. `feat(jira-admin): implement get_issue_type_screen_scheme.py (5/5 tests passing)`

---

### Phase 3 Completion

- [ ] **Phase 3 Summary:**
  - [ ] 2 scripts implemented
  - [ ] 11 tests passing
  - [ ] Coverage ≥ 85%
  - **Commit:** `docs(jira-admin): complete Phase 3 - Issue Type Screen Schemes`

---

## Phase 4: Project Screen Discovery

### Feature 4.1: Get Project Screens

**Script:** `get_project_screens.py`

**JIRA API:**
- `GET /rest/api/3/issuetypescreenscheme/project?projectId={projectId}` - Get scheme for project
- `GET /rest/api/3/issuetypescreenscheme/mapping` - Get issue type mappings
- `GET /rest/api/3/screenscheme/{schemeId}` - Get screen scheme details
- `GET /rest/api/2/screens/{screenId}` - Get screen details

**Test Cases:**
```python
def test_get_project_screens():
    """Test getting all screens used by a project."""

def test_get_screens_by_issue_type():
    """Test showing which screens are used for each issue type."""

def test_get_screens_by_operation():
    """Test showing which screens are used for create/edit/view."""

def test_show_field_summary():
    """Test summarizing fields across all screens."""

def test_project_not_found():
    """Test error handling for invalid project."""

def test_format_detailed_output():
    """Test comprehensive output format."""
```

**CLI Interface:**
```bash
# Get all screens for project
python get_project_screens.py PROJ

# Show breakdown by issue type
python get_project_screens.py PROJ --by-issue-type

# Show breakdown by operation
python get_project_screens.py PROJ --by-operation

# Include field summary
python get_project_screens.py PROJ --show-fields

# JSON output
python get_project_screens.py PROJ --output json
```

**Output Example:**
```
Screens for Project: PROJ (My Project)

Issue Type Screen Scheme: Default Issue Type Screen Scheme (ID: 10000)

Screens by Issue Type:

Bug:
  Create: Bug Create Screen (ID: 10)
  Edit:   Bug Edit Screen (ID: 11)
  View:   Default Screen (ID: 1)

Story:
  Create: Default Screen (ID: 1)
  Edit:   Default Screen (ID: 1)
  View:   Default Screen (ID: 1)

Epic:
  Create: Epic Screen (ID: 12)
  Edit:   Epic Screen (ID: 12)
  View:   Default Screen (ID: 1)

Task:
  Create: Default Screen (ID: 1)
  Edit:   Default Screen (ID: 1)
  View:   Default Screen (ID: 1)

Unique Screens Used: 5
Total Issue Types: 4
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Shows all screens used by project
- [ ] Groups by issue type and operation
- [ ] Optional field summary
- [ ] Handles projects without custom schemes

**Commits:**
1. `test(jira-admin): add failing tests for get_project_screens`
2. `feat(jira-admin): implement get_project_screens.py (6/6 tests passing)`

---

### Phase 4 Completion

- [ ] **Phase 4 Summary:**
  - [ ] 1 script implemented
  - [ ] 6 tests passing
  - [ ] Coverage ≥ 85%
  - **Commit:** `docs(jira-admin): complete Phase 4 - Project Screen Discovery`

---

## Integration & Polish

### Integration Tasks

- [ ] **Integration 1:** Field audit script
  - [ ] Create script to audit which fields appear on which screens
  - [ ] Identify fields that are required but not on screens
  - [ ] Identify fields on screens but not required
  - **Commit:** `feat(jira-admin): add screen field audit utility`

- [ ] **Integration 2:** Bulk field operations
  - [ ] Add field to multiple screens at once
  - [ ] Remove field from multiple screens at once
  - **Commit:** `feat(jira-admin): add bulk screen field operations`

### Documentation Updates

- [ ] **Docs 1:** Create comprehensive examples in ADMINISTRATION_IMPLEMENTATION_PLAN.md
- [ ] **Docs 2:** Update CLAUDE.md with screen management patterns
- [ ] **Docs 3:** Document screen hierarchy and relationships

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 65+ unit tests passing
- [ ] Coverage ≥ 85%

**Scripts:**
- [ ] 11 new scripts implemented
- [ ] All scripts have `--help`
- [ ] All scripts support `--profile`
- [ ] All mutation scripts have `--dry-run`

**Documentation:**
- [ ] Screen hierarchy clearly documented
- [ ] Examples for common use cases
- [ ] Permission requirements documented

---

## Summary Metrics

| Phase | Scripts | Tests | Priority |
|-------|---------|-------|----------|
| 1. Screen Operations | 6 | 36 | High |
| 2. Screen Schemes | 2 | 12 | Medium |
| 3. Issue Type Screen Schemes | 2 | 11 | Medium |
| 4. Project Screen Discovery | 1 | 6 | High |
| **TOTAL** | **11** | **65** | - |

---

## Understanding the Screen Hierarchy

### Three-Tier Architecture

The screen management system in JIRA uses a three-tier architecture that provides flexibility in controlling which fields users see for different issue types and operations:

#### Tier 1: Screens (Field Level)
- **Purpose:** Define which fields are visible and in what order
- **Structure:** Contains tabs, each tab contains fields
- **Scope:** Reusable across multiple schemes
- **Example:** "Default Screen" with tabs "Field Tab" and "Custom Fields"

#### Tier 2: Screen Schemes (Operation Level)
- **Purpose:** Map operations (create, edit, view) to specific screens
- **Structure:** Associates operation types with screens
- **Scope:** Reusable across multiple issue types
- **Example:** "Default Screen Scheme" maps all operations to "Default Screen"

#### Tier 3: Issue Type Screen Schemes (Project Level)
- **Purpose:** Map issue types to screen schemes
- **Structure:** Associates issue types with screen schemes
- **Scope:** Assigned to projects
- **Example:** "Default Issue Type Screen Scheme" maps Bug → "Bug Screen Scheme", Story → "Default Screen Scheme"

### Data Flow Example

When a user creates a Bug issue in project PROJ:

1. **Project Level:** PROJ uses "Default Issue Type Screen Scheme" (ID: 10000)
2. **Issue Type Mapping:** Bug → "Bug Screen Scheme" (ID: 2)
3. **Operation Mapping:** Create → "Bug Create Screen" (ID: 10)
4. **Screen Display:** "Bug Create Screen" shows tabs and fields to the user

### Common Patterns

**Pattern 1: Uniform Screens**
```
Issue Type Screen Scheme: "Default"
  All Issue Types → "Default Screen Scheme"
    All Operations → "Default Screen"
```
Result: Same fields for all issue types and operations

**Pattern 2: Issue Type Specific**
```
Issue Type Screen Scheme: "Software Development"
  Bug → "Bug Screen Scheme" → Different screens per operation
  Story → "Story Screen Scheme" → Different screens per operation
  Epic → "Epic Screen Scheme" → Different screens per operation
```
Result: Different fields for each issue type

**Pattern 3: Operation Specific**
```
Screen Scheme: "Progressive Disclosure"
  Create → "Minimal Screen" (only required fields)
  Edit → "Full Screen" (all fields)
  View → "Read-Only Screen" (display-optimized)
```
Result: Different fields for different operations

---

## Use Case Examples

### Use Case 1: Add Custom Field to All Bug Screens

**Requirement:** Add "Severity" custom field to all screens used when creating bugs

**Steps:**
```bash
# 1. Find which screens are used for bugs in project PROJ
python get_project_screens.py PROJ --by-issue-type

# Output shows:
# Bug → Create: Bug Create Screen (ID: 10)

# 2. Add the field to the screen
python add_field_to_screen.py 10 --field-id customfield_10025 --tab-name "Details"

# 3. Verify the field was added
python get_screen.py 10 --show-tabs --show-fields
```

### Use Case 2: Audit Field Visibility Across Project

**Requirement:** Find all screens used in project and list which fields appear on each

**Steps:**
```bash
# 1. Get comprehensive screen usage for project
python get_project_screens.py PROJ --show-fields --output json > proj_screens.json

# 2. List all unique screens
python list_screens.py --output json > all_screens.json

# 3. For each screen, get detailed field list
for screen_id in 1 10 11 12; do
  python get_screen_fields.py $screen_id --output json > screen_${screen_id}_fields.json
done
```

### Use Case 3: Clone Screen Configuration to New Project

**Requirement:** Set up new project with same screen configuration as existing project

**Steps:**
```bash
# 1. Get screen configuration from reference project
python get_project_screens.py REF --output json > ref_config.json

# 2. Get issue type screen scheme details
python get_issue_type_screen_scheme.py 10000 --show-mappings --output json > scheme_config.json

# 3. For each unique screen, get field configuration
python get_screen_fields.py 1 --output json > screen_1_fields.json

# 4. Use this data to configure new project
# (Future: Create automation script for this)
```

### Use Case 4: Remove Deprecated Field from All Screens

**Requirement:** Remove "Old Priority" custom field from all screens in the system

**Steps:**
```bash
# 1. Find which screens contain the field
# (Future: add find_field_screens.py script)

# 2. For each screen, remove the field
python remove_field_from_screen.py 1 --field-id customfield_10099 --force
python remove_field_from_screen.py 10 --field-id customfield_10099 --force
python remove_field_from_screen.py 11 --field-id customfield_10099 --force
```

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Admin permissions required for all operations | High | High | Document permission requirements clearly |
| Screen IDs vs Tab IDs confusion | Medium | Medium | Clear parameter naming, validation |
| Classic vs Next-Gen project differences | High | Medium | Document limitations for Next-Gen |
| Field removal breaks workflows | Medium | High | Require confirmation, warn about required fields |
| Screen scheme deletion breaks projects | Low | High | Check usage before deletion |

### Permission Requirements

All scripts in this plan require:
- **Jira Administrators** global permission, OR
- **Administer Projects** project permission (for project-scoped screens only)

Without these permissions, API calls will return 403 Forbidden.

### Classic vs Next-Gen Projects

Important limitations:
- Screen schemes only apply to **Classic (Team-Managed) projects**
- **Next-Gen (Company-Managed) projects** use different field configuration
- API may return empty results for Next-Gen projects
- Document this clearly in all script help text

---

## Future Enhancements

### Phase 5: Screen Creation and Management (Future)

**Potential Scripts:**
- `create_screen.py` - Create new screen
- `create_screen_tab.py` - Add tab to screen
- `update_screen.py` - Update screen name/description
- `delete_screen.py` - Delete screen (with safety checks)
- `clone_screen.py` - Clone screen with all fields
- `create_screen_scheme.py` - Create screen scheme
- `update_screen_scheme.py` - Update screen scheme mappings
- `delete_screen_scheme.py` - Delete screen scheme

### Phase 6: Advanced Field Operations (Future)

**Potential Scripts:**
- `find_field_screens.py` - Find all screens containing a field
- `bulk_add_field.py` - Add field to multiple screens
- `bulk_remove_field.py` - Remove field from multiple screens
- `audit_required_fields.py` - Check if required fields are on screens
- `validate_screen_config.py` - Validate screen configuration

---

## References

**Official Documentation:**
- [Jira Cloud Platform REST API - Screens](https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-screens/)
- [Jira Cloud Platform REST API - Screen Schemes](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-screen-schemes/)
- [Jira Cloud Platform REST API - Screen Tab Fields](https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-screen-tab-fields/)
- [Jira Cloud Platform REST API - Issue Type Screen Schemes](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-type-screen-schemes/)

**Community Resources:**
- [New APIs for screens management](https://community.developer.atlassian.com/t/new-apis-for-screens-management/43620)
- [Managing Issue Type Screen Schemes via REST API](https://community.atlassian.com/t5/Jira-questions/Managing-Issue-Type-Screen-Schemes-and-Screen-Schemes-via-REST/qaq-p/2634512)

---

**Document Version:** 1.0
**Created:** 2025-12-26
**Status:** Ready for Implementation
**Estimated Effort:** 4-5 days for all phases
