# JIRA Admin: Issue Type Schemes - TDD Implementation Plan

## Implementation Status

**Overall Status:** PLANNED (Not yet implemented)

**Planned Scripts:**
- `list_issue_types.py` - List all issue types
- `get_issue_type.py` - Get issue type details
- `create_issue_type.py` - Create new issue type
- `update_issue_type.py` - Update issue type properties
- `delete_issue_type.py` - Delete issue type
- `list_issue_type_schemes.py` - List all issue type schemes
- `get_issue_type_scheme.py` - Get issue type scheme details
- `create_issue_type_scheme.py` - Create new issue type scheme
- `update_issue_type_scheme.py` - Update issue type scheme
- `delete_issue_type_scheme.py` - Delete issue type scheme
- `assign_issue_type_scheme.py` - Assign scheme to project(s)
- `get_scheme_mapping.py` - Get issue type to scheme mappings

**JiraClient Methods to Add:**
- `get_issue_types()` - List all issue types
- `get_issue_type()` - Get issue type details
- `create_issue_type()` - Create issue type
- `update_issue_type()` - Update issue type
- `delete_issue_type()` - Delete issue type
- `get_issue_type_schemes()` - List issue type schemes
- `get_issue_type_scheme()` - Get scheme details
- `get_issue_type_scheme_for_projects()` - Get schemes for projects
- `create_issue_type_scheme()` - Create scheme
- `update_issue_type_scheme()` - Update scheme
- `delete_issue_type_scheme()` - Delete scheme
- `assign_issue_type_scheme()` - Assign scheme to project
- `add_issue_types_to_scheme()` - Add issue types to scheme
- `remove_issue_type_from_scheme()` - Remove issue type from scheme
- `reorder_issue_types_in_scheme()` - Change issue type order
- `get_issue_type_scheme_mappings()` - Get scheme-to-type mappings

**Test Coverage:**
- Unit tests: Target 85%+ coverage
- Live integration tests: Required for scheme operations
- Coverage location: `.claude/skills/jira-admin/tests/`

**Last Updated:** 2025-12-26

---

## Overview

**Objective:** Implement comprehensive JIRA issue type and issue type scheme management using Test-Driven Development (TDD)

**What are Issue Types?**
Issue types define the kind of work items in JIRA (e.g., Story, Bug, Task, Epic, Subtask). They represent different types of work and can have different workflows, fields, and screen configurations.

**What are Issue Type Schemes?**
Issue type schemes are collections of issue types that can be assigned to projects. They determine which issue types are available in a project. Each project must have exactly one issue type scheme.

**Hierarchy Levels:**
- **Level 1 (Epic)**: High-level initiatives (`hierarchyLevel: 1`)
- **Level 0 (Standard)**: Regular work items like Story, Task, Bug (`hierarchyLevel: 0`)
- **Level -1 (Subtask)**: Child work items (`hierarchyLevel: -1`, `subtask: true`)

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
1. **Phase 1: Issue Type Operations** (CRUD for issue types)
2. **Phase 2: Issue Type Scheme Operations** (CRUD for schemes)
3. **Phase 3: Scheme Assignment** (Assign schemes to projects)
4. **Phase 4: Advanced Management** (Ordering, mapping, validation)

---

## JIRA API Reference

### Issue Type Endpoints

| Method | Endpoint | Description | Admin Required |
|--------|----------|-------------|----------------|
| GET | `/rest/api/3/issuetype` | Get all issue types | No |
| GET | `/rest/api/3/issuetype/{id}` | Get issue type by ID | No |
| POST | `/rest/api/3/issuetype` | Create issue type | **Yes** |
| PUT | `/rest/api/3/issuetype/{id}` | Update issue type | **Yes** |
| DELETE | `/rest/api/3/issuetype/{id}` | Delete issue type | **Yes** |
| GET | `/rest/api/3/issuetype/{id}/alternatives` | Get alternative issue types | No |
| GET | `/rest/api/3/project/{projectIdOrKey}/issuetypes` | Get issue types for project | No |

### Issue Type Scheme Endpoints

| Method | Endpoint | Description | Admin Required |
|--------|----------|-------------|----------------|
| GET | `/rest/api/3/issuetypescheme` | Get all issue type schemes | **Yes** |
| POST | `/rest/api/3/issuetypescheme` | Create issue type scheme | **Yes** |
| GET | `/rest/api/3/issuetypescheme/{issueTypeSchemeId}` | Get issue type scheme items | **Yes** |
| PUT | `/rest/api/3/issuetypescheme/{issueTypeSchemeId}` | Update issue type scheme | **Yes** |
| DELETE | `/rest/api/3/issuetypescheme/{issueTypeSchemeId}` | Delete issue type scheme | **Yes** |
| GET | `/rest/api/3/issuetypescheme/project` | Get issue type schemes for projects | **Yes** |
| PUT | `/rest/api/3/issuetypescheme/project` | Assign issue type scheme to project | **Yes** |
| GET | `/rest/api/3/issuetypescheme/mapping` | Get issue type scheme items | **Yes** |
| PUT | `/rest/api/3/issuetypescheme/{issueTypeSchemeId}/issuetype` | Add issue types to scheme | **Yes** |
| DELETE | `/rest/api/3/issuetypescheme/{issueTypeSchemeId}/issuetype/{issueTypeId}` | Remove issue type from scheme | **Yes** |
| PUT | `/rest/api/3/issuetypescheme/{issueTypeSchemeId}/issuetype/move` | Change order of issue types | **Yes** |

### Permissions & Scopes

**Required Permission:** Administer Jira global permission

**OAuth 2.0 Scopes:**
- **Classic:** `manage:jira-configuration`
- **Granular:** `read:issue-type-scheme:jira`, `write:issue-type-scheme:jira`, `read:issue-type:jira`, `write:issue-type:jira`

**Note:** When using Basic auth (email + API token), permissions depend only on the user's Jira account permissions.

---

## API Request/Response Examples

### 1. Get All Issue Types

**Request:**
```bash
GET /rest/api/3/issuetype
```

**Response:**
```json
[
  {
    "id": "10000",
    "name": "Epic",
    "description": "A big user story that needs to be broken down",
    "iconUrl": "https://site.atlassian.net/images/icons/issuetypes/epic.svg",
    "subtask": false,
    "hierarchyLevel": 1,
    "avatarId": 10307,
    "entityId": "uuid-1234",
    "scope": {
      "type": "PROJECT",
      "project": {
        "id": "10000"
      }
    }
  },
  {
    "id": "10001",
    "name": "Story",
    "description": "A user story",
    "iconUrl": "https://site.atlassian.net/images/icons/issuetypes/story.svg",
    "subtask": false,
    "hierarchyLevel": 0,
    "avatarId": 10308
  },
  {
    "id": "10002",
    "name": "Task",
    "description": "A task that needs to be done",
    "iconUrl": "https://site.atlassian.net/images/icons/issuetypes/task.svg",
    "subtask": false,
    "hierarchyLevel": 0,
    "avatarId": 10318
  },
  {
    "id": "10003",
    "name": "Bug",
    "description": "A problem that impairs or prevents functionality",
    "iconUrl": "https://site.atlassian.net/images/icons/issuetypes/bug.svg",
    "subtask": false,
    "hierarchyLevel": 0,
    "avatarId": 10303
  },
  {
    "id": "10004",
    "name": "Subtask",
    "description": "A subtask of another issue",
    "iconUrl": "https://site.atlassian.net/images/icons/issuetypes/subtask.svg",
    "subtask": true,
    "hierarchyLevel": -1,
    "avatarId": 10316
  }
]
```

**Key Fields:**
- `hierarchyLevel`: `-1` (subtask), `0` (standard), `1` (epic), `2+` (custom levels for Premium/Enterprise)
- `subtask`: Boolean flag for subtask types
- `scope`: Project-specific vs global issue types

### 2. Create Issue Type

**Request:**
```bash
POST /rest/api/3/issuetype
Content-Type: application/json

{
  "name": "Incident",
  "description": "An unplanned interruption or reduction in quality of service",
  "type": "standard",
  "hierarchyLevel": 0
}
```

**Request Body Parameters:**
- `name` (string, required): Issue type name (max 60 characters)
- `description` (string, optional): Description
- `type` (string, optional): `standard` or `subtask` (default: `standard`)
- `hierarchyLevel` (integer, optional): `-1` for subtask, `0` for standard, `1` for epic

**Response:**
```json
{
  "id": "10005",
  "name": "Incident",
  "description": "An unplanned interruption or reduction in quality of service",
  "iconUrl": "https://site.atlassian.net/images/icons/issuetypes/story.svg",
  "subtask": false,
  "hierarchyLevel": 0,
  "avatarId": 10308
}
```

**Status:** `201 Created`

### 3. Get All Issue Type Schemes

**Request:**
```bash
GET /rest/api/3/issuetypescheme?startAt=0&maxResults=50
```

**Query Parameters:**
- `startAt` (integer): Starting index (default: 0)
- `maxResults` (integer): Max results per page (default: 50)
- `id` (array): Filter by scheme IDs
- `orderBy` (string): Order by field (e.g., `name`, `-name` for descending)
- `expand` (string): Expand additional fields

**Response:**
```json
{
  "maxResults": 50,
  "startAt": 0,
  "total": 2,
  "isLast": true,
  "values": [
    {
      "id": "10000",
      "name": "Default Issue Type Scheme",
      "description": "Default issue type scheme is the list of global issue types. All newly created issue types will automatically be added to this scheme.",
      "defaultIssueTypeId": "10001",
      "isDefault": true
    },
    {
      "id": "10001",
      "name": "Software Development Scheme",
      "description": "Issue types for software development projects",
      "defaultIssueTypeId": "10001",
      "isDefault": false
    }
  ]
}
```

### 4. Create Issue Type Scheme

**Request:**
```bash
POST /rest/api/3/issuetypescheme
Content-Type: application/json

{
  "name": "Kanban Issue Type Scheme",
  "description": "A collection of issue types suited to use in a kanban style project",
  "issueTypeIds": ["10001", "10002", "10003"],
  "defaultIssueTypeId": "10002"
}
```

**Request Body Parameters:**
- `name` (string, required): Scheme name
- `description` (string, optional): Scheme description
- `issueTypeIds` (array of strings, required): Issue type IDs to include
- `defaultIssueTypeId` (string, optional): Default issue type ID

**Response:**
```json
{
  "issueTypeSchemeId": "10002"
}
```

**Status:** `201 Created`

### 5. Get Issue Type Schemes for Projects

**Request:**
```bash
GET /rest/api/3/issuetypescheme/project?projectId=10000&projectId=10001
```

**Query Parameters:**
- `projectId` (array): Project IDs (1 to 100 IDs)
- `startAt` (integer): Starting index
- `maxResults` (integer): Max results per page

**Response:**
```json
{
  "maxResults": 50,
  "startAt": 0,
  "total": 2,
  "isLast": true,
  "values": [
    {
      "issueTypeScheme": {
        "id": "10000",
        "name": "Default Issue Type Scheme",
        "description": "Default issue type scheme",
        "defaultIssueTypeId": "10001",
        "isDefault": true
      },
      "projectIds": ["10000"]
    },
    {
      "issueTypeScheme": {
        "id": "10002",
        "name": "Kanban Issue Type Scheme",
        "description": "Kanban-specific issue types",
        "defaultIssueTypeId": "10002",
        "isDefault": false
      },
      "projectIds": ["10001"]
    }
  ]
}
```

### 6. Assign Issue Type Scheme to Project

**Request:**
```bash
PUT /rest/api/3/issuetypescheme/project
Content-Type: application/json

{
  "issueTypeSchemeId": "10002",
  "projectId": "10001"
}
```

**Request Body:**
- `issueTypeSchemeId` (string, required): Issue type scheme ID
- `projectId` (string, required): Project ID

**Response:** `204 No Content` on success

**Important Constraint:**
- Only works for classic projects (not next-gen/team-managed)
- If any issues in the project use issue types not in the new scheme, the operation will fail
- Must update those issues first to use types from the new scheme

### 7. Get Issue Type Scheme Mappings

**Request:**
```bash
GET /rest/api/3/issuetypescheme/mapping?startAt=0&maxResults=100
```

**Query Parameters:**
- `startAt` (integer): Starting index
- `maxResults` (integer): Max results per page
- `issueTypeSchemeId` (array): Filter by scheme IDs

**Response:**
```json
{
  "maxResults": 100,
  "startAt": 0,
  "total": 4,
  "isLast": true,
  "values": [
    {
      "issueTypeSchemeId": "10000",
      "issueTypeId": "10000"
    },
    {
      "issueTypeSchemeId": "10000",
      "issueTypeId": "10001"
    },
    {
      "issueTypeSchemeId": "10000",
      "issueTypeId": "10002"
    },
    {
      "issueTypeSchemeId": "10001",
      "issueTypeId": "10001"
    }
  ]
}
```

### 8. Add Issue Types to Scheme

**Request:**
```bash
PUT /rest/api/3/issuetypescheme/{issueTypeSchemeId}/issuetype
Content-Type: application/json

{
  "issueTypeIds": ["10003", "10004"]
}
```

**Response:** `204 No Content` on success

### 9. Remove Issue Type from Scheme

**Request:**
```bash
DELETE /rest/api/3/issuetypescheme/{issueTypeSchemeId}/issuetype/{issueTypeId}
```

**Response:** `204 No Content` on success

**Note:** Cannot remove the default issue type or the last remaining issue type from a scheme.

### 10. Reorder Issue Types in Scheme

**Request:**
```bash
PUT /rest/api/3/issuetypescheme/{issueTypeSchemeId}/issuetype/move
Content-Type: application/json

{
  "issueTypeId": "10002",
  "after": "10001"
}
```

**Request Body:**
- `issueTypeId` (string, required): Issue type ID to move
- `after` (string, optional): Issue type ID to position after (omit to move to first)

**Response:** `204 No Content` on success

---

## Phase 1: Issue Type Operations

**Objective:** Implement CRUD operations for issue types

**Duration:** 2-3 days

### Phase 1.1: List Issue Types (4 hours)

**Script:** `list_issue_types.py`

**JiraClient Method:**
```python
def get_issue_types(self) -> List[Dict[str, Any]]:
    """
    Get all issue types.

    Returns:
        List of issue type dictionaries
    """
    return self.get(
        '/rest/api/3/issuetype',
        operation='get issue types'
    )
```

**Test Cases:**
```python
def test_get_issue_types_success():
    """Should return list of issue types"""

def test_get_issue_types_filters_subtasks():
    """Should support filtering to subtask types only"""

def test_get_issue_types_filters_standard():
    """Should support filtering to standard types only"""

def test_get_issue_types_by_hierarchy():
    """Should support filtering by hierarchy level"""

def test_get_issue_types_formats_table():
    """Should format output as table with hierarchy info"""
```

**CLI Usage:**
```bash
# List all issue types
python list_issue_types.py

# List only subtask types
python list_issue_types.py --subtask-only

# List only standard types (exclude subtasks)
python list_issue_types.py --standard-only

# List by hierarchy level
python list_issue_types.py --hierarchy-level 0

# JSON output
python list_issue_types.py --format json

# Show scope information
python list_issue_types.py --show-scope
```

**Output Example:**
```
Issue Types (5 total)

ID      Name        Hierarchy  Subtask  Description
10000   Epic        1          No       A big user story
10001   Story       0          No       A user story
10002   Task        0          No       A task that needs to be done
10003   Bug         0          No       A problem that impairs functionality
10004   Subtask     -1         Yes      A subtask of another issue
```

### Phase 1.2: Get Issue Type Details (3 hours)

**Script:** `get_issue_type.py`

**JiraClient Method:**
```python
def get_issue_type(self, issue_type_id: str) -> Dict[str, Any]:
    """
    Get issue type by ID.

    Args:
        issue_type_id: Issue type ID

    Returns:
        Issue type details
    """
    return self.get(
        f'/rest/api/3/issuetype/{issue_type_id}',
        operation='get issue type'
    )
```

**Test Cases:**
```python
def test_get_issue_type_success():
    """Should return issue type details"""

def test_get_issue_type_not_found():
    """Should raise NotFoundError for invalid ID"""

def test_get_issue_type_shows_hierarchy():
    """Should display hierarchy level information"""

def test_get_issue_type_shows_scope():
    """Should display scope (global vs project-specific)"""
```

**CLI Usage:**
```bash
# Get issue type by ID
python get_issue_type.py 10000

# JSON output
python get_issue_type.py 10000 --format json

# Show alternative issue types
python get_issue_type.py 10000 --show-alternatives
```

### Phase 1.3: Create Issue Type (5 hours)

**Script:** `create_issue_type.py`

**JiraClient Method:**
```python
def create_issue_type(
    self,
    name: str,
    description: Optional[str] = None,
    issue_type: str = 'standard',
    hierarchy_level: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create new issue type.

    Args:
        name: Issue type name
        description: Issue type description
        issue_type: 'standard' or 'subtask'
        hierarchy_level: -1 (subtask), 0 (standard), 1 (epic), etc.

    Returns:
        Created issue type details
    """
    data = {
        'name': name,
        'type': issue_type
    }

    if description:
        data['description'] = description

    if hierarchy_level is not None:
        data['hierarchyLevel'] = hierarchy_level

    return self.post(
        '/rest/api/3/issuetype',
        data=data,
        operation='create issue type'
    )
```

**Test Cases:**
```python
def test_create_issue_type_standard():
    """Should create standard issue type"""

def test_create_issue_type_subtask():
    """Should create subtask issue type"""

def test_create_issue_type_with_hierarchy():
    """Should create issue type with specific hierarchy level"""

def test_create_issue_type_name_too_long():
    """Should raise ValidationError for name > 60 chars"""

def test_create_issue_type_requires_admin():
    """Should raise PermissionError without admin rights"""
```

**CLI Usage:**
```bash
# Create standard issue type
python create_issue_type.py "Incident" --description "Service interruption"

# Create subtask type
python create_issue_type.py "Sub-bug" --type subtask

# Create with specific hierarchy level
python create_issue_type.py "Initiative" --hierarchy-level 2

# JSON output
python create_issue_type.py "Feature" --format json
```

### Phase 1.4: Update Issue Type (4 hours)

**Script:** `update_issue_type.py`

**JiraClient Method:**
```python
def update_issue_type(
    self,
    issue_type_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    avatar_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Update issue type.

    Args:
        issue_type_id: Issue type ID
        name: New name
        description: New description
        avatar_id: New avatar ID

    Returns:
        Updated issue type details
    """
    data = {}

    if name:
        data['name'] = name
    if description is not None:
        data['description'] = description
    if avatar_id:
        data['avatarId'] = avatar_id

    return self.put(
        f'/rest/api/3/issuetype/{issue_type_id}',
        data=data,
        operation='update issue type'
    )
```

**Test Cases:**
```python
def test_update_issue_type_name():
    """Should update issue type name"""

def test_update_issue_type_description():
    """Should update issue type description"""

def test_update_issue_type_avatar():
    """Should update issue type avatar"""

def test_update_issue_type_not_found():
    """Should raise NotFoundError for invalid ID"""

def test_update_issue_type_requires_admin():
    """Should raise PermissionError without admin rights"""
```

**CLI Usage:**
```bash
# Update issue type name
python update_issue_type.py 10005 --name "Service Incident"

# Update description
python update_issue_type.py 10005 --description "Critical service interruption"

# Update avatar
python update_issue_type.py 10005 --avatar-id 10307
```

### Phase 1.5: Delete Issue Type (4 hours)

**Script:** `delete_issue_type.py`

**JiraClient Method:**
```python
def delete_issue_type(
    self,
    issue_type_id: str,
    alternative_issue_type_id: Optional[str] = None
) -> None:
    """
    Delete issue type.

    Args:
        issue_type_id: Issue type ID to delete
        alternative_issue_type_id: Alternative issue type for existing issues
    """
    params = {}
    if alternative_issue_type_id:
        params['alternativeIssueTypeId'] = alternative_issue_type_id

    self.delete(
        f'/rest/api/3/issuetype/{issue_type_id}',
        params=params,
        operation='delete issue type'
    )
```

**Test Cases:**
```python
def test_delete_issue_type_success():
    """Should delete unused issue type"""

def test_delete_issue_type_with_alternative():
    """Should delete and migrate issues to alternative type"""

def test_delete_issue_type_not_found():
    """Should raise NotFoundError for invalid ID"""

def test_delete_issue_type_in_use():
    """Should fail if type is in use without alternative"""

def test_delete_issue_type_requires_admin():
    """Should raise PermissionError without admin rights"""
```

**CLI Usage:**
```bash
# Delete unused issue type
python delete_issue_type.py 10005

# Delete with alternative type for migration
python delete_issue_type.py 10005 --alternative 10002

# Dry run (show what would be deleted)
python delete_issue_type.py 10005 --dry-run

# Force delete with confirmation
python delete_issue_type.py 10005 --force
```

**Phase 1 Commit Message:**
```
feat(jira-admin): implement issue type CRUD operations (20/20 tests passing)

- Add list_issue_types.py with hierarchy filtering
- Add get_issue_type.py for issue type details
- Add create_issue_type.py with subtask support
- Add update_issue_type.py for name/description/avatar
- Add delete_issue_type.py with migration support
- Add 5 JiraClient methods for issue type management
- Tests cover standard types, subtasks, and hierarchy levels
```

---

## Phase 2: Issue Type Scheme Operations

**Objective:** Implement CRUD operations for issue type schemes

**Duration:** 2-3 days

### Phase 2.1: List Issue Type Schemes (4 hours)

**Script:** `list_issue_type_schemes.py`

**JiraClient Method:**
```python
def get_issue_type_schemes(
    self,
    start_at: int = 0,
    max_results: int = 50,
    scheme_ids: Optional[List[str]] = None,
    order_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get all issue type schemes.

    Args:
        start_at: Starting index for pagination
        max_results: Maximum results per page
        scheme_ids: Filter by scheme IDs
        order_by: Order by field (e.g., 'name', '-name')

    Returns:
        Paginated list of schemes
    """
    params = {
        'startAt': start_at,
        'maxResults': max_results
    }

    if scheme_ids:
        params['id'] = scheme_ids
    if order_by:
        params['orderBy'] = order_by

    return self.get(
        '/rest/api/3/issuetypescheme',
        params=params,
        operation='get issue type schemes'
    )
```

**Test Cases:**
```python
def test_get_issue_type_schemes_success():
    """Should return paginated schemes"""

def test_get_issue_type_schemes_pagination():
    """Should support pagination parameters"""

def test_get_issue_type_schemes_filter_by_ids():
    """Should filter by scheme IDs"""

def test_get_issue_type_schemes_ordering():
    """Should support ordering by name"""

def test_get_issue_type_schemes_requires_admin():
    """Should raise PermissionError without admin rights"""
```

**CLI Usage:**
```bash
# List all schemes
python list_issue_type_schemes.py

# Paginate results
python list_issue_type_schemes.py --start-at 50 --max-results 25

# Filter by IDs
python list_issue_type_schemes.py --ids 10000,10001

# Order by name
python list_issue_type_schemes.py --order-by name

# Order by name descending
python list_issue_type_schemes.py --order-by -name

# JSON output
python list_issue_type_schemes.py --format json
```

### Phase 2.2: Get Issue Type Scheme Details (4 hours)

**Script:** `get_issue_type_scheme.py`

**JiraClient Method:**
```python
def get_issue_type_scheme(
    self,
    scheme_id: str,
    expand: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get issue type scheme items.

    Args:
        scheme_id: Issue type scheme ID
        expand: Fields to expand

    Returns:
        Scheme details with issue types
    """
    params = {}
    if expand:
        params['expand'] = expand

    return self.get(
        f'/rest/api/3/issuetypescheme/{scheme_id}',
        params=params,
        operation='get issue type scheme'
    )
```

**Test Cases:**
```python
def test_get_issue_type_scheme_success():
    """Should return scheme details"""

def test_get_issue_type_scheme_with_expand():
    """Should expand additional fields"""

def test_get_issue_type_scheme_not_found():
    """Should raise NotFoundError for invalid ID"""

def test_get_issue_type_scheme_shows_issue_types():
    """Should display associated issue types"""
```

**CLI Usage:**
```bash
# Get scheme details
python get_issue_type_scheme.py 10000

# Show issue types in scheme
python get_issue_type_scheme.py 10000 --show-issue-types

# JSON output
python get_issue_type_scheme.py 10000 --format json
```

### Phase 2.3: Create Issue Type Scheme (5 hours)

**Script:** `create_issue_type_scheme.py`

**JiraClient Method:**
```python
def create_issue_type_scheme(
    self,
    name: str,
    issue_type_ids: List[str],
    description: Optional[str] = None,
    default_issue_type_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create issue type scheme.

    Args:
        name: Scheme name
        issue_type_ids: List of issue type IDs
        description: Scheme description
        default_issue_type_id: Default issue type ID

    Returns:
        Created scheme with ID
    """
    data = {
        'name': name,
        'issueTypeIds': issue_type_ids
    }

    if description:
        data['description'] = description
    if default_issue_type_id:
        data['defaultIssueTypeId'] = default_issue_type_id

    return self.post(
        '/rest/api/3/issuetypescheme',
        data=data,
        operation='create issue type scheme'
    )
```

**Test Cases:**
```python
def test_create_issue_type_scheme_success():
    """Should create scheme with issue types"""

def test_create_issue_type_scheme_with_default():
    """Should set default issue type"""

def test_create_issue_type_scheme_missing_name():
    """Should raise ValidationError without name"""

def test_create_issue_type_scheme_missing_types():
    """Should raise ValidationError without issue type IDs"""

def test_create_issue_type_scheme_invalid_type_id():
    """Should raise ValidationError for invalid issue type ID"""
```

**CLI Usage:**
```bash
# Create scheme
python create_issue_type_scheme.py "Dev Scheme" \
  --issue-types 10001,10002,10003 \
  --description "For development projects"

# Create with default type
python create_issue_type_scheme.py "Kanban Scheme" \
  --issue-types 10001,10002 \
  --default-type 10002

# JSON output
python create_issue_type_scheme.py "Support Scheme" \
  --issue-types 10000,10003 \
  --format json
```

### Phase 2.4: Update Issue Type Scheme (4 hours)

**Script:** `update_issue_type_scheme.py`

**JiraClient Method:**
```python
def update_issue_type_scheme(
    self,
    scheme_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    default_issue_type_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update issue type scheme.

    Args:
        scheme_id: Scheme ID
        name: New name
        description: New description
        default_issue_type_id: New default issue type

    Returns:
        Empty response on success
    """
    data = {}

    if name:
        data['name'] = name
    if description is not None:
        data['description'] = description
    if default_issue_type_id:
        data['defaultIssueTypeId'] = default_issue_type_id

    return self.put(
        f'/rest/api/3/issuetypescheme/{scheme_id}',
        data=data,
        operation='update issue type scheme'
    )
```

**Test Cases:**
```python
def test_update_issue_type_scheme_name():
    """Should update scheme name"""

def test_update_issue_type_scheme_description():
    """Should update scheme description"""

def test_update_issue_type_scheme_default_type():
    """Should update default issue type"""

def test_update_issue_type_scheme_not_found():
    """Should raise NotFoundError for invalid ID"""
```

**CLI Usage:**
```bash
# Update scheme name
python update_issue_type_scheme.py 10001 --name "Updated Scheme"

# Update description
python update_issue_type_scheme.py 10001 --description "New description"

# Update default type
python update_issue_type_scheme.py 10001 --default-type 10002
```

### Phase 2.5: Delete Issue Type Scheme (4 hours)

**Script:** `delete_issue_type_scheme.py`

**JiraClient Method:**
```python
def delete_issue_type_scheme(self, scheme_id: str) -> None:
    """
    Delete issue type scheme.

    Args:
        scheme_id: Scheme ID to delete
    """
    self.delete(
        f'/rest/api/3/issuetypescheme/{scheme_id}',
        operation='delete issue type scheme'
    )
```

**Test Cases:**
```python
def test_delete_issue_type_scheme_success():
    """Should delete unused scheme"""

def test_delete_issue_type_scheme_not_found():
    """Should raise NotFoundError for invalid ID"""

def test_delete_issue_type_scheme_in_use():
    """Should fail if scheme is assigned to projects"""

def test_delete_issue_type_scheme_default():
    """Should fail for default scheme"""
```

**CLI Usage:**
```bash
# Delete scheme
python delete_issue_type_scheme.py 10001

# Dry run
python delete_issue_type_scheme.py 10001 --dry-run

# Force delete with confirmation
python delete_issue_type_scheme.py 10001 --force
```

**Phase 2 Commit Message:**
```
feat(jira-admin): implement issue type scheme CRUD (20/20 tests passing)

- Add list_issue_type_schemes.py with pagination
- Add get_issue_type_scheme.py for scheme details
- Add create_issue_type_scheme.py with default type
- Add update_issue_type_scheme.py for scheme properties
- Add delete_issue_type_scheme.py with safety checks
- Add 5 JiraClient methods for scheme management
```

---

## Phase 3: Scheme Assignment

**Objective:** Assign issue type schemes to projects and retrieve mappings

**Duration:** 1-2 days

### Phase 3.1: Get Schemes for Projects (3 hours)

**Script:** `get_project_issue_type_schemes.py`

**JiraClient Method:**
```python
def get_issue_type_scheme_for_projects(
    self,
    project_ids: List[str],
    start_at: int = 0,
    max_results: int = 50
) -> Dict[str, Any]:
    """
    Get issue type schemes for projects.

    Args:
        project_ids: List of project IDs (1-100)
        start_at: Starting index
        max_results: Maximum results per page

    Returns:
        Schemes assigned to projects
    """
    if len(project_ids) > 100:
        raise ValidationError("Maximum 100 project IDs allowed")

    params = {
        'projectId': project_ids,
        'startAt': start_at,
        'maxResults': max_results
    }

    return self.get(
        '/rest/api/3/issuetypescheme/project',
        params=params,
        operation='get project issue type schemes'
    )
```

**Test Cases:**
```python
def test_get_project_schemes_single():
    """Should get scheme for single project"""

def test_get_project_schemes_multiple():
    """Should get schemes for multiple projects"""

def test_get_project_schemes_too_many():
    """Should raise ValidationError for > 100 projects"""

def test_get_project_schemes_pagination():
    """Should support pagination"""
```

**CLI Usage:**
```bash
# Get scheme for project
python get_project_issue_type_schemes.py --project-id 10000

# Get schemes for multiple projects
python get_project_issue_type_schemes.py --project-ids 10000,10001,10002

# JSON output
python get_project_issue_type_schemes.py --project-id 10000 --format json
```

### Phase 3.2: Assign Scheme to Project (4 hours)

**Script:** `assign_issue_type_scheme.py`

**JiraClient Method:**
```python
def assign_issue_type_scheme(
    self,
    scheme_id: str,
    project_id: str
) -> None:
    """
    Assign issue type scheme to project.

    Args:
        scheme_id: Issue type scheme ID
        project_id: Project ID

    Note:
        Only works for classic projects.
        Fails if issues use types not in the new scheme.
    """
    data = {
        'issueTypeSchemeId': scheme_id,
        'projectId': project_id
    }

    self.put(
        '/rest/api/3/issuetypescheme/project',
        data=data,
        operation='assign issue type scheme'
    )
```

**Test Cases:**
```python
def test_assign_scheme_success():
    """Should assign scheme to project"""

def test_assign_scheme_team_managed():
    """Should fail for team-managed projects"""

def test_assign_scheme_incompatible_issues():
    """Should fail if issues use types not in scheme"""

def test_assign_scheme_not_found():
    """Should raise NotFoundError for invalid scheme/project"""

def test_assign_scheme_validates_compatibility():
    """Should validate issue compatibility before assignment"""
```

**CLI Usage:**
```bash
# Assign scheme to project
python assign_issue_type_scheme.py --scheme 10001 --project PROJ

# Assign with validation
python assign_issue_type_scheme.py --scheme 10001 --project PROJ --validate

# Dry run (check compatibility)
python assign_issue_type_scheme.py --scheme 10001 --project PROJ --dry-run

# Force assignment (migrate incompatible issues)
python assign_issue_type_scheme.py --scheme 10001 --project PROJ --force
```

### Phase 3.3: Get Scheme Mappings (3 hours)

**Script:** `get_scheme_mapping.py`

**JiraClient Method:**
```python
def get_issue_type_scheme_mappings(
    self,
    start_at: int = 0,
    max_results: int = 100,
    scheme_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get issue type to scheme mappings.

    Args:
        start_at: Starting index
        max_results: Maximum results per page
        scheme_ids: Filter by scheme IDs

    Returns:
        Mappings of issue types to schemes

    Note:
        Only returns mappings for classic projects.
    """
    params = {
        'startAt': start_at,
        'maxResults': max_results
    }

    if scheme_ids:
        params['issueTypeSchemeId'] = scheme_ids

    return self.get(
        '/rest/api/3/issuetypescheme/mapping',
        params=params,
        operation='get issue type scheme mappings'
    )
```

**Test Cases:**
```python
def test_get_mappings_all():
    """Should get all mappings"""

def test_get_mappings_by_scheme():
    """Should filter by scheme IDs"""

def test_get_mappings_pagination():
    """Should support pagination"""
```

**CLI Usage:**
```bash
# Get all mappings
python get_scheme_mapping.py

# Filter by scheme
python get_scheme_mapping.py --scheme 10001

# Multiple schemes
python get_scheme_mapping.py --schemes 10000,10001

# JSON output
python get_scheme_mapping.py --format json
```

**Phase 3 Commit Message:**
```
feat(jira-admin): implement issue type scheme assignment (12/12 tests passing)

- Add get_project_issue_type_schemes.py for project lookups
- Add assign_issue_type_scheme.py with validation
- Add get_scheme_mapping.py for scheme-to-type mappings
- Add 3 JiraClient methods for scheme assignment
- Include compatibility checks before assignment
```

---

## Phase 4: Advanced Management

**Objective:** Add/remove issue types, reorder, and advanced operations

**Duration:** 1-2 days

### Phase 4.1: Add Issue Types to Scheme (3 hours)

**JiraClient Method:**
```python
def add_issue_types_to_scheme(
    self,
    scheme_id: str,
    issue_type_ids: List[str]
) -> None:
    """
    Add issue types to scheme.

    Args:
        scheme_id: Scheme ID
        issue_type_ids: List of issue type IDs to add
    """
    data = {
        'issueTypeIds': issue_type_ids
    }

    self.put(
        f'/rest/api/3/issuetypescheme/{scheme_id}/issuetype',
        data=data,
        operation='add issue types to scheme'
    )
```

**Test Cases:**
```python
def test_add_issue_types_single():
    """Should add single issue type"""

def test_add_issue_types_multiple():
    """Should add multiple issue types"""

def test_add_issue_types_duplicate():
    """Should handle duplicate issue type gracefully"""
```

**CLI Integration:** Add to `update_issue_type_scheme.py`
```bash
python update_issue_type_scheme.py 10001 --add-types 10003,10004
```

### Phase 4.2: Remove Issue Type from Scheme (3 hours)

**JiraClient Method:**
```python
def remove_issue_type_from_scheme(
    self,
    scheme_id: str,
    issue_type_id: str
) -> None:
    """
    Remove issue type from scheme.

    Args:
        scheme_id: Scheme ID
        issue_type_id: Issue type ID to remove

    Note:
        Cannot remove default issue type or last issue type.
    """
    self.delete(
        f'/rest/api/3/issuetypescheme/{scheme_id}/issuetype/{issue_type_id}',
        operation='remove issue type from scheme'
    )
```

**Test Cases:**
```python
def test_remove_issue_type_success():
    """Should remove issue type from scheme"""

def test_remove_default_issue_type():
    """Should fail when removing default issue type"""

def test_remove_last_issue_type():
    """Should fail when removing last issue type"""
```

**CLI Integration:** Add to `update_issue_type_scheme.py`
```bash
python update_issue_type_scheme.py 10001 --remove-type 10003
```

### Phase 4.3: Reorder Issue Types (3 hours)

**JiraClient Method:**
```python
def reorder_issue_types_in_scheme(
    self,
    scheme_id: str,
    issue_type_id: str,
    after: Optional[str] = None
) -> None:
    """
    Reorder issue types in scheme.

    Args:
        scheme_id: Scheme ID
        issue_type_id: Issue type ID to move
        after: Issue type ID to position after (None = move to first)
    """
    data = {
        'issueTypeId': issue_type_id
    }

    if after:
        data['after'] = after

    self.put(
        f'/rest/api/3/issuetypescheme/{scheme_id}/issuetype/move',
        data=data,
        operation='reorder issue types'
    )
```

**Test Cases:**
```python
def test_reorder_to_first():
    """Should move issue type to first position"""

def test_reorder_after_type():
    """Should move issue type after another"""

def test_reorder_invalid_after():
    """Should fail if 'after' type not in scheme"""
```

**CLI Integration:** Add to `update_issue_type_scheme.py`
```bash
# Move to first position
python update_issue_type_scheme.py 10001 --reorder 10003 --position first

# Move after another type
python update_issue_type_scheme.py 10001 --reorder 10003 --after 10001
```

**Phase 4 Commit Message:**
```
feat(jira-admin): add issue type scheme management operations (9/9 tests passing)

- Add add_issue_types_to_scheme() to JiraClient
- Add remove_issue_type_from_scheme() to JiraClient
- Add reorder_issue_types_in_scheme() to JiraClient
- Integrate operations into update_issue_type_scheme.py
- Tests cover add, remove, reorder scenarios
```

---

## Considerations & Constraints

### Subtask Handling

**Hierarchy Levels:**
- Subtask types have `hierarchyLevel: -1` and `subtask: true`
- Cannot have subtasks as parents
- Must validate hierarchy when creating relationships

**Validation Rules:**
```python
def validate_issue_type_hierarchy(issue_type: Dict[str, Any]) -> None:
    """Validate issue type hierarchy constraints"""
    if issue_type.get('subtask'):
        if issue_type.get('hierarchyLevel', -1) != -1:
            raise ValidationError("Subtask must have hierarchyLevel -1")
```

### Classic vs Team-Managed Projects

**Important Constraints:**
- Issue type schemes only work for **classic projects**
- Team-managed (next-gen) projects have their own issue type configuration
- Assignment will fail for team-managed projects with clear error message

**Validation:**
```python
def validate_classic_project(project_key: str, client: JiraClient) -> None:
    """Ensure project is classic (not team-managed)"""
    project = client.get(f'/rest/api/3/project/{project_key}')
    if project.get('simplified'):
        raise ValidationError(
            f"Project {project_key} is team-managed. "
            "Issue type schemes only work with classic projects."
        )
```

### Scheme Assignment Validation

**Pre-Assignment Check:**
Before assigning a scheme, validate that all existing issues use types in the new scheme:

```python
def validate_scheme_compatibility(
    project_id: str,
    scheme_id: str,
    client: JiraClient
) -> List[str]:
    """
    Check if project issues are compatible with scheme.

    Returns:
        List of incompatible issue type IDs (empty if compatible)
    """
    # Get scheme's issue types
    scheme = client.get_issue_type_scheme(scheme_id)
    scheme_type_ids = {t['id'] for t in scheme['issueTypes']}

    # Get project's current issue types in use
    jql = f'project = {project_id}'
    issues = client.jql_search(jql, fields='issuetype')

    used_type_ids = {i['fields']['issuetype']['id']
                     for i in issues['issues']}

    # Find incompatible types
    return list(used_type_ids - scheme_type_ids)
```

**Migration Strategy:**
If incompatible issues exist, provide migration options:
1. Update issues to use types from new scheme
2. Add missing types to the new scheme
3. Abort the operation

### Default Issue Type

**Rules:**
- Every scheme must have a default issue type
- Default type cannot be removed from scheme
- When creating issues, default type is used if no type specified

**Enforcement:**
```python
def validate_default_issue_type(
    scheme_id: str,
    issue_type_id: str,
    client: JiraClient
) -> None:
    """Prevent removal of default issue type"""
    scheme = client.get_issue_type_scheme(scheme_id)
    if scheme.get('defaultIssueTypeId') == issue_type_id:
        raise ValidationError(
            f"Cannot remove default issue type {issue_type_id}. "
            "Set a different default type first."
        )
```

### Pagination Handling

**Best Practices:**
- Default `maxResults: 50` for schemes
- Support `startAt` for large result sets
- Implement `--all` flag to fetch all pages automatically

**Auto-Pagination:**
```python
def get_all_schemes(client: JiraClient) -> List[Dict[str, Any]]:
    """Fetch all schemes with automatic pagination"""
    schemes = []
    start_at = 0
    max_results = 50

    while True:
        response = client.get_issue_type_schemes(
            start_at=start_at,
            max_results=max_results
        )
        schemes.extend(response['values'])

        if response['isLast']:
            break

        start_at += max_results

    return schemes
```

### Error Handling

**Common Errors:**

| Status | Error Type | Scenario |
|--------|------------|----------|
| 400 | ValidationError | Invalid scheme/type configuration |
| 401 | AuthenticationError | Invalid credentials |
| 403 | PermissionError | Missing Administer Jira permission |
| 404 | NotFoundError | Scheme/type/project not found |
| 409 | ConflictError | Scheme name conflict |

**Example Error Messages:**
```python
# Permission error
"Administer Jira global permission required. "
"Check permissions at https://your-site.atlassian.net/secure/admin/ViewGlobalPermissions.jspa"

# Incompatible issues
"Cannot assign scheme: 15 issues use types not in the new scheme. "
"Incompatible types: Bug (10003), Task (10002). "
"Update these issues first or add the types to the scheme."

# Team-managed project
"Project PROJ is team-managed. Issue type schemes only work with classic projects. "
"Convert to classic or configure issue types in project settings."
```

---

## Testing Strategy

### Unit Tests

**Structure:**
```
.claude/skills/jira-admin/tests/
├── unit/
│   ├── test_list_issue_types.py
│   ├── test_get_issue_type.py
│   ├── test_create_issue_type.py
│   ├── test_update_issue_type.py
│   ├── test_delete_issue_type.py
│   ├── test_list_issue_type_schemes.py
│   ├── test_get_issue_type_scheme.py
│   ├── test_create_issue_type_scheme.py
│   ├── test_update_issue_type_scheme.py
│   ├── test_delete_issue_type_scheme.py
│   ├── test_assign_issue_type_scheme.py
│   └── test_jira_client_admin.py
└── live_integration/
    ├── conftest.py
    ├── test_issue_type_lifecycle.py
    └── test_issue_type_scheme_lifecycle.py
```

**Mock Responses:**
Store common API responses in fixtures:
```python
# tests/fixtures/issue_type_responses.py
EPIC_RESPONSE = {
    "id": "10000",
    "name": "Epic",
    "hierarchyLevel": 1,
    "subtask": False,
    "description": "A big user story"
}

SUBTASK_RESPONSE = {
    "id": "10004",
    "name": "Subtask",
    "hierarchyLevel": -1,
    "subtask": True,
    "description": "A subtask"
}
```

### Live Integration Tests

**Prerequisites:**
- JIRA admin account for test instance
- Dedicated test project (e.g., `ADMINTEST`)
- Cleanup after tests

**Lifecycle Test Example:**
```python
def test_issue_type_scheme_full_lifecycle(jira_client):
    """Test complete scheme lifecycle: create, update, assign, delete"""

    # Create scheme
    scheme = jira_client.create_issue_type_scheme(
        name="Test Scheme",
        issue_type_ids=["10001", "10002"],
        default_issue_type_id="10001"
    )
    scheme_id = scheme['issueTypeSchemeId']

    try:
        # Update scheme
        jira_client.update_issue_type_scheme(
            scheme_id,
            name="Updated Test Scheme"
        )

        # Add issue type
        jira_client.add_issue_types_to_scheme(
            scheme_id,
            ["10003"]
        )

        # Assign to project
        jira_client.assign_issue_type_scheme(
            scheme_id,
            "10000"
        )

        # Verify assignment
        projects = jira_client.get_issue_type_scheme_for_projects(
            ["10000"]
        )
        assert projects['values'][0]['issueTypeScheme']['id'] == scheme_id

    finally:
        # Cleanup
        jira_client.delete_issue_type_scheme(scheme_id)
```

**Test Coverage Goals:**
- **Issue Types:** 20+ tests (CRUD, hierarchy, subtasks)
- **Schemes:** 20+ tests (CRUD, assignment, mappings)
- **Advanced:** 9+ tests (add/remove types, reordering)
- **Integration:** 10+ live tests (full lifecycles)

---

## Effort Estimates

### Phase Breakdown

| Phase | Description | Hours | Days |
|-------|-------------|-------|------|
| Phase 1.1 | List issue types | 4 | 0.5 |
| Phase 1.2 | Get issue type | 3 | 0.4 |
| Phase 1.3 | Create issue type | 5 | 0.6 |
| Phase 1.4 | Update issue type | 4 | 0.5 |
| Phase 1.5 | Delete issue type | 4 | 0.5 |
| **Phase 1 Total** | **Issue Type CRUD** | **20** | **2.5** |
| Phase 2.1 | List schemes | 4 | 0.5 |
| Phase 2.2 | Get scheme | 4 | 0.5 |
| Phase 2.3 | Create scheme | 5 | 0.6 |
| Phase 2.4 | Update scheme | 4 | 0.5 |
| Phase 2.5 | Delete scheme | 4 | 0.5 |
| **Phase 2 Total** | **Scheme CRUD** | **21** | **2.6** |
| Phase 3.1 | Get project schemes | 3 | 0.4 |
| Phase 3.2 | Assign scheme | 4 | 0.5 |
| Phase 3.3 | Get mappings | 3 | 0.4 |
| **Phase 3 Total** | **Scheme Assignment** | **10** | **1.3** |
| Phase 4.1 | Add types to scheme | 3 | 0.4 |
| Phase 4.2 | Remove type from scheme | 3 | 0.4 |
| Phase 4.3 | Reorder types | 3 | 0.4 |
| **Phase 4 Total** | **Advanced Management** | **9** | **1.2** |
| **Integration Tests** | Live testing | 8 | 1.0 |
| **Documentation** | Update docs | 4 | 0.5 |
| **TOTAL** | | **72** | **9.1** |

**Assumptions:**
- Developer familiar with JIRA API and TDD
- Tests written first (TDD approach)
- Access to JIRA Cloud admin account
- 8-hour work days

---

## Example CLI Usage

### Common Workflows

#### 1. Discover Available Issue Types
```bash
# List all issue types
python list_issue_types.py

# Show only standard types (exclude subtasks)
python list_issue_types.py --standard-only

# Show with hierarchy information
python list_issue_types.py --show-hierarchy
```

#### 2. Create Custom Issue Type
```bash
# Create a standard issue type
python create_issue_type.py "Incident" \
  --description "Service interruption or degradation" \
  --hierarchy-level 0

# Create a subtask type
python create_issue_type.py "Investigation" \
  --description "Investigation subtask" \
  --type subtask
```

#### 3. Create Issue Type Scheme
```bash
# Create scheme for support projects
python create_issue_type_scheme.py "Support Scheme" \
  --description "For customer support projects" \
  --issue-types 10001,10003,10005 \
  --default-type 10005

# Verify creation
python get_issue_type_scheme.py 10010 --show-issue-types
```

#### 4. Assign Scheme to Project
```bash
# Check current scheme
python get_project_issue_type_schemes.py --project-id 10000

# Dry run to check compatibility
python assign_issue_type_scheme.py --scheme 10010 --project 10000 --dry-run

# Assign scheme
python assign_issue_type_scheme.py --scheme 10010 --project 10000

# Verify assignment
python get_project_issue_type_schemes.py --project-id 10000
```

#### 5. Modify Scheme
```bash
# Add issue type to scheme
python update_issue_type_scheme.py 10010 --add-types 10004

# Remove issue type from scheme
python update_issue_type_scheme.py 10010 --remove-type 10003

# Reorder issue types
python update_issue_type_scheme.py 10010 \
  --reorder 10005 --after 10001

# Update scheme properties
python update_issue_type_scheme.py 10010 \
  --name "Customer Support Scheme" \
  --description "Updated description"
```

#### 6. Bulk Operations
```bash
# List all schemes with mappings
python list_issue_type_schemes.py --show-mappings

# Get mappings for specific scheme
python get_scheme_mapping.py --scheme 10010

# Export to JSON
python list_issue_type_schemes.py --format json > schemes.json
```

#### 7. Cleanup and Deletion
```bash
# Delete unused issue type
python delete_issue_type.py 10006 --dry-run
python delete_issue_type.py 10006 --force

# Delete scheme (must not be assigned to projects)
python delete_issue_type_scheme.py 10010 --dry-run
python delete_issue_type_scheme.py 10010 --force
```

---

## References

**JIRA Cloud REST API Documentation:**
- [Issue Types API Group](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-types/)
- [Issue Type Schemes API Group](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-type-schemes/)
- [New REST APIs Announcement](https://community.developer.atlassian.com/t/new-rest-apis-for-issue-type-schemes-and-workflow-schemes-management/40497)

**Atlassian Documentation:**
- [What are Issue Types?](https://support.atlassian.com/jira-cloud-administration/docs/what-are-issue-types/)
- [Configure Issue Type Hierarchy](https://support.atlassian.com/jira-cloud-administration/docs/configure-the-issue-type-hierarchy/)
- [Add, Edit, Delete Issue Type Schemes](https://support.atlassian.com/jira-cloud-administration/docs/add-edit-and-delete-an-issue-type-scheme/)
- [How to Detect Subtask Issue Types](https://community.developer.atlassian.com/t/how-to-detect-subtask-issue-type/50387)

**Community Resources:**
- [Issue Type Schemes via REST](https://community.developer.atlassian.com/t/issue-type-schemes-via-rest/1270)
- [Hierarchy Levels Deprecation Notice](https://developer.atlassian.com/cloud/jira/platform/deprecation-notice-hierarchy-levels/)

---

## Success Criteria

**Definition of Done:**
- All 12 scripts implemented and executable
- 17 JiraClient methods added to shared library
- 49+ unit tests passing (85%+ coverage)
- 10+ live integration tests passing
- Documentation complete (SKILL.md, examples)
- All scripts support `--help`, `--format json`, `--dry-run`
- Error messages include troubleshooting hints
- Compatible with existing project patterns

**Quality Checklist:**
- [ ] All tests pass
- [ ] Code follows project conventions
- [ ] Scripts are executable (`chmod +x`)
- [ ] Help text includes examples
- [ ] Errors provide actionable guidance
- [ ] Pagination handled correctly
- [ ] Subtask types validated properly
- [ ] Classic vs team-managed projects distinguished
- [ ] Scheme compatibility validated before assignment
- [ ] Default issue type constraints enforced
- [ ] Live tests include cleanup
- [ ] Documentation updated

**Deliverables:**
1. 12 Python scripts in `.claude/skills/jira-admin/scripts/`
2. 17 JiraClient methods in `shared/scripts/lib/jira_client.py`
3. 49+ tests in `.claude/skills/jira-admin/tests/`
4. Updated `.claude/skills/jira-admin/SKILL.md`
5. This implementation plan as reference

---

**End of Implementation Plan**
