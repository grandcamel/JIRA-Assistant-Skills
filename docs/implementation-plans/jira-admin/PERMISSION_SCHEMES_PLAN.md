# Permission Schemes - TDD Implementation Plan

## Overview

**Objective:** Implement comprehensive JIRA permission scheme management for security configuration, permission grant operations, and project permission assignment using Test-Driven Development (TDD).

**Component:** jira-admin skill - Phase 3: Permission Schemes

**API Coverage:** Permission Schemes API (`/rest/api/3/permissionscheme`), Permissions API (`/rest/api/3/permissions`), Project Permission Scheme API

**Permission Requirements:** Most operations require "Administer Jira" global permission. Some read operations only require "Permission to access Jira".

**OAuth Scopes Required:**
- Read operations: `read:permission-scheme:jira`, `read:application-role:jira`, `read:field:jira`, `read:group:jira`, `read:permission:jira`
- Write operations: `write:permission-scheme:jira` (plus all read scopes)

---

## Background: Permission Schemes in JIRA

### What are Permission Schemes?

Permission schemes define what users can do within JIRA projects. Each project is assigned exactly one permission scheme, which determines who can:
- View/browse the project
- Create, edit, delete issues
- Manage sprints and versions
- Administer the project
- And 30+ other operations

### Permission Grant Structure

A permission scheme contains multiple **permission grants**. Each grant has:

1. **Permission** (string): The permission key (e.g., "BROWSE_PROJECTS", "CREATE_ISSUES", "ADMINISTER_PROJECTS")
2. **Holder** (object): Who gets this permission
   - **type** (string): "user", "group", "projectRole", "applicationRole", "anyone", "projectLead", "reporter", "currentAssignee"
   - **parameter** (string): Depends on type:
     - For "group": group name (e.g., "jira-developers")
     - For "user": user account ID
     - For "projectRole": role name (e.g., "Developers")
     - For "anyone", "projectLead": parameter is null
   - **value** (string): Internal ID/UUID (auto-populated by JIRA)

**Example Grant:**
```json
{
  "permission": "ADMINISTER_PROJECTS",
  "holder": {
    "type": "group",
    "parameter": "jira-administrators"
  }
}
```

### Common JIRA Permission Types

**Project Permissions:**
- `BROWSE_PROJECTS` - View projects and issues
- `CREATE_ISSUES` - Create issues
- `EDIT_ISSUES` - Edit issues
- `DELETE_ISSUES` - Delete issues
- `ASSIGN_ISSUES` - Assign issues to users
- `ASSIGNABLE_USER` - Be assigned to issues
- `RESOLVE_ISSUES` - Resolve/reopen issues
- `CLOSE_ISSUES` - Close issues
- `MODIFY_REPORTER` - Modify issue reporter
- `TRANSITION_ISSUES` - Transition issues through workflow
- `MOVE_ISSUES` - Move issues between projects
- `LINK_ISSUES` - Link issues
- `MANAGE_WATCHERS` - Manage watchers
- `VIEW_VOTERS_AND_WATCHERS` - View voters and watchers
- `ADD_COMMENTS` - Add comments
- `EDIT_ALL_COMMENTS` - Edit all comments
- `EDIT_OWN_COMMENTS` - Edit own comments
- `DELETE_ALL_COMMENTS` - Delete all comments
- `DELETE_OWN_COMMENTS` - Delete own comments
- `CREATE_ATTACHMENTS` - Create attachments
- `DELETE_ALL_ATTACHMENTS` - Delete all attachments
- `DELETE_OWN_ATTACHMENTS` - Delete own attachments
- `WORK_ON_ISSUES` - Log work on issues
- `EDIT_ALL_WORKLOGS` - Edit all worklogs
- `EDIT_OWN_WORKLOGS` - Edit own worklogs
- `DELETE_ALL_WORKLOGS` - Delete all worklogs
- `DELETE_OWN_WORKLOGS` - Delete own worklogs
- `ADMINISTER_PROJECTS` - Administer projects
- `MANAGE_SPRINTS` - Manage sprints
- `VIEW_DEV_TOOLS` - View development tools
- `VIEW_READONLY_WORKFLOW` - View read-only workflow
- `SCHEDULE_ISSUES` - Schedule issues (set due date)
- `SET_ISSUE_SECURITY` - Set issue security

**Typical Permission Scheme Examples:**

1. **Default Software Development Scheme:**
   - BROWSE_PROJECTS → Anyone
   - CREATE_ISSUES → Authenticated users
   - EDIT_ISSUES → Reporter, Assignee, Project role: Developers
   - ADMINISTER_PROJECTS → Project role: Administrators

2. **Restricted Internal Scheme:**
   - BROWSE_PROJECTS → Group: employees
   - CREATE_ISSUES → Group: employees
   - EDIT_ISSUES → Reporter, Project role: Developers
   - ADMINISTER_PROJECTS → Group: jira-administrators

---

## API Endpoints

### 1. Get All Permission Schemes

**Endpoint:** `GET /rest/api/3/permissionscheme`

**Description:** Returns all permission schemes with basic metadata.

**Query Parameters:**
- `expand` (string): Use "permissions" to include grants, "user,group,projectRole" to expand holder details

**Required Permissions:** Permission to access Jira

**Response Example:**
```json
{
  "permissionSchemes": [
    {
      "expand": "permissions,user,group,projectRole",
      "id": 10000,
      "self": "https://your-domain.atlassian.net/rest/api/3/permissionscheme/10000",
      "name": "Default Software Scheme",
      "description": "Default permission scheme for software projects"
    },
    {
      "id": 10001,
      "self": "https://your-domain.atlassian.net/rest/api/3/permissionscheme/10001",
      "name": "Internal Projects Scheme",
      "description": "Restricted scheme for internal projects"
    }
  ]
}
```

---

### 2. Get Permission Scheme

**Endpoint:** `GET /rest/api/3/permissionscheme/{schemeId}`

**Description:** Returns a permission scheme identified by its ID, including all permission grants.

**Path Parameters:**
- `schemeId` (integer): The ID of the permission scheme

**Query Parameters:**
- `expand` (string): Options: "permissions" (default), "user,group,projectRole,field,all"

**Required Permissions:** Permission to access Jira

**Response Example:**
```json
{
  "expand": "permissions,user,group,projectRole",
  "id": 10000,
  "self": "https://your-domain.atlassian.net/rest/api/3/permissionscheme/10000",
  "name": "Default Software Scheme",
  "description": "Default permission scheme for software projects",
  "permissions": [
    {
      "id": 10100,
      "self": "https://your-domain.atlassian.net/rest/api/3/permissionscheme/10000/permission/10100",
      "holder": {
        "type": "group",
        "parameter": "jira-developers",
        "value": "ca85fac0-d974-40ca-a615-7af99c48d24f",
        "expand": "group"
      },
      "permission": "ADMINISTER_PROJECTS"
    },
    {
      "id": 10101,
      "self": "https://your-domain.atlassian.net/rest/api/3/permissionscheme/10000/permission/10101",
      "holder": {
        "type": "anyone",
        "parameter": null
      },
      "permission": "BROWSE_PROJECTS"
    },
    {
      "id": 10102,
      "self": "https://your-domain.atlassian.net/rest/api/3/permissionscheme/10000/permission/10102",
      "holder": {
        "type": "projectRole",
        "parameter": "Developers",
        "value": "10360"
      },
      "permission": "CREATE_ISSUES"
    }
  ]
}
```

---

### 3. Create Permission Scheme

**Endpoint:** `POST /rest/api/3/permissionscheme`

**Description:** Creates a new permission scheme. Can be created with or without initial permission grants.

**Required Permissions:** Administer Jira global permission

**Request Body:**
```json
{
  "name": "Custom Development Scheme",
  "description": "Permission scheme for development projects",
  "permissions": [
    {
      "holder": {
        "type": "group",
        "parameter": "jira-developers"
      },
      "permission": "ADMINISTER_PROJECTS"
    },
    {
      "holder": {
        "type": "anyone"
      },
      "permission": "BROWSE_PROJECTS"
    },
    {
      "holder": {
        "type": "group",
        "parameter": "jira-developers"
      },
      "permission": "CREATE_ISSUES"
    }
  ]
}
```

**Response Example:**
```json
{
  "expand": "permissions,user,group,projectRole",
  "id": 10050,
  "self": "https://your-domain.atlassian.net/rest/api/3/permissionscheme/10050",
  "name": "Custom Development Scheme",
  "description": "Permission scheme for development projects",
  "permissions": [
    {
      "id": 10200,
      "self": "https://your-domain.atlassian.net/rest/api/3/permissionscheme/10050/permission/10200",
      "holder": {
        "type": "group",
        "parameter": "jira-developers",
        "value": "ca85fac0-d974-40ca-a615-7af99c48d24f",
        "expand": "group"
      },
      "permission": "ADMINISTER_PROJECTS"
    }
  ]
}
```

**Response Status:** 201 Created

---

### 4. Update Permission Scheme

**Endpoint:** `PUT /rest/api/3/permissionscheme/{schemeId}`

**Description:** Updates a permission scheme's name and description. To modify grants, use the permission grant endpoints.

**Path Parameters:**
- `schemeId` (integer): The ID of the permission scheme

**Required Permissions:** Administer Jira global permission

**Request Body:**
```json
{
  "name": "Updated Scheme Name",
  "description": "Updated description"
}
```

**Response Example:**
```json
{
  "expand": "permissions,user,group,projectRole",
  "id": 10050,
  "self": "https://your-domain.atlassian.net/rest/api/3/permissionscheme/10050",
  "name": "Updated Scheme Name",
  "description": "Updated description",
  "permissions": []
}
```

**Response Status:** 200 OK

---

### 5. Delete Permission Scheme

**Endpoint:** `DELETE /rest/api/3/permissionscheme/{schemeId}`

**Description:** Deletes a permission scheme. Cannot delete schemes that are assigned to projects.

**Path Parameters:**
- `schemeId` (integer): The ID of the permission scheme

**Required Permissions:** Administer Jira global permission

**Response Status:** 204 No Content

**Error Response (if in use):**
```json
{
  "errorMessages": ["The permission scheme cannot be deleted because it is used by one or more projects."],
  "errors": {}
}
```

---

### 6. Get Permission Scheme Grants

**Endpoint:** `GET /rest/api/3/permissionscheme/{schemeId}/permission`

**Description:** Returns all permission grants for a permission scheme.

**Path Parameters:**
- `schemeId` (integer): The ID of the permission scheme

**Query Parameters:**
- `expand` (string): Options: "permissions", "user,group,projectRole,field,all"

**Required Permissions:** Permission to access Jira

**Response Example:**
```json
{
  "permissions": [
    {
      "id": 10100,
      "self": "https://your-domain.atlassian.net/rest/api/3/permissionscheme/10000/permission/10100",
      "holder": {
        "type": "group",
        "parameter": "jira-developers",
        "value": "ca85fac0-d974-40ca-a615-7af99c48d24f"
      },
      "permission": "ADMINISTER_PROJECTS"
    }
  ]
}
```

---

### 7. Create Permission Grant

**Endpoint:** `POST /rest/api/3/permissionscheme/{schemeId}/permission`

**Description:** Creates a permission grant in a permission scheme.

**Path Parameters:**
- `schemeId` (integer): The ID of the permission scheme

**Required Permissions:** Administer Jira global permission

**Request Body:**
```json
{
  "holder": {
    "type": "group",
    "parameter": "jira-developers"
  },
  "permission": "EDIT_ISSUES"
}
```

**Response Example:**
```json
{
  "id": 10103,
  "self": "https://your-domain.atlassian.net/rest/api/3/permissionscheme/10000/permission/10103",
  "holder": {
    "type": "group",
    "parameter": "jira-developers",
    "value": "ca85fac0-d974-40ca-a615-7af99c48d24f",
    "expand": "group"
  },
  "permission": "EDIT_ISSUES"
}
```

**Response Status:** 201 Created

---

### 8. Delete Permission Grant

**Endpoint:** `DELETE /rest/api/3/permissionscheme/{schemeId}/permission/{permissionId}`

**Description:** Deletes a permission grant from a permission scheme.

**Path Parameters:**
- `schemeId` (integer): The ID of the permission scheme
- `permissionId` (integer): The ID of the permission grant

**Required Permissions:** Administer Jira global permission

**Response Status:** 204 No Content

---

### 9. Get All Permissions

**Endpoint:** `GET /rest/api/3/permissions`

**Description:** Returns all permissions available in the JIRA instance, including custom permissions.

**Required Permissions:** None (public endpoint)

**Response Example:**
```json
{
  "permissions": {
    "ADMINISTER_PROJECTS": {
      "key": "ADMINISTER_PROJECTS",
      "name": "Administer Projects",
      "type": "PROJECT",
      "description": "Ability to administer a project in Jira."
    },
    "BROWSE_PROJECTS": {
      "key": "BROWSE_PROJECTS",
      "name": "Browse Projects",
      "type": "PROJECT",
      "description": "Ability to browse projects and the issues within them."
    },
    "CREATE_ISSUES": {
      "key": "CREATE_ISSUES",
      "name": "Create Issues",
      "type": "PROJECT",
      "description": "Ability to create issues."
    }
  }
}
```

---

### 10. Get Project's Permission Scheme

**Endpoint:** `GET /rest/api/3/project/{projectKeyOrId}/permissionscheme`

**Description:** Gets the permission scheme associated with the project.

**Path Parameters:**
- `projectKeyOrId` (string): The project ID or project key

**Query Parameters:**
- `expand` (string): Options: "permissions", "user,group,projectRole,field,all"

**Required Permissions:** Administer Jira global permission or Administer project permission

**Response Example:**
```json
{
  "expand": "permissions,user,group,projectRole",
  "id": 10000,
  "self": "https://your-domain.atlassian.net/rest/api/3/permissionscheme/10000",
  "name": "Default Software Scheme",
  "description": "Default permission scheme for software projects",
  "permissions": [
    {
      "id": 10100,
      "holder": {
        "type": "group",
        "parameter": "jira-developers"
      },
      "permission": "ADMINISTER_PROJECTS"
    }
  ]
}
```

---

### 11. Assign Permission Scheme to Project

**Endpoint:** `PUT /rest/api/3/project/{projectKeyOrId}/permissionscheme`

**Description:** Assigns a permission scheme with a project. This replaces the project's current permission scheme.

**Path Parameters:**
- `projectKeyOrId` (string): The project ID or project key

**Required Permissions:** Administer Jira global permission

**Request Body:**
```json
{
  "id": 10050
}
```

**Response Example:**
```json
{
  "expand": "permissions,user,group,projectRole",
  "id": 10050,
  "self": "https://your-domain.atlassian.net/rest/api/3/permissionscheme/10050",
  "name": "Custom Development Scheme",
  "description": "Permission scheme for development projects"
}
```

**Response Status:** 200 OK

---

## Proposed Scripts

### 1. list_permission_schemes.py

**Purpose:** List all permission schemes with optional filtering and detailed information.

**CLI Interface:**
```bash
# List all schemes
python list_permission_schemes.py

# List with detailed grants
python list_permission_schemes.py --show-grants

# Filter by name pattern
python list_permission_schemes.py --filter "Development"

# Show which projects use each scheme
python list_permission_schemes.py --show-projects

# Output as JSON
python list_permission_schemes.py --output json

# Output as CSV
python list_permission_schemes.py --output csv
```

**Output Format (Table):**
```
ID     Name                          Description                              Grants
-----  ---------------------------   --------------------------------------   ------
10000  Default Software Scheme       Default for software projects           25
10001  Internal Projects Scheme      Restricted for internal projects        18
10050  Custom Development Scheme     Permission scheme for dev projects      12
```

**Output Format (Detailed):**
```
Permission Scheme: Default Software Scheme (ID: 10000)
Description: Default permission scheme for software projects
Grants: 25 permission grants
Projects: PROJ1, PROJ2, DEV (3 projects)

Permissions:
  - BROWSE_PROJECTS → anyone
  - CREATE_ISSUES → group: jira-developers
  - EDIT_ISSUES → group: jira-developers, projectRole: Developers
  - ADMINISTER_PROJECTS → group: jira-administrators
  ...
```

**Implementation Notes:**
- Use `GET /rest/api/3/permissionscheme` with `expand=permissions`
- To show projects, iterate through projects and check their permission schemes (no direct reverse lookup API)
- Cache project lookups for performance

---

### 2. get_permission_scheme.py

**Purpose:** Get detailed information about a specific permission scheme, including all permission grants.

**CLI Interface:**
```bash
# Get by ID
python get_permission_scheme.py 10000

# Get by name (exact match)
python get_permission_scheme.py "Default Software Scheme"

# Get by name (fuzzy match)
python get_permission_scheme.py "Software" --fuzzy

# Show expanded holder details
python get_permission_scheme.py 10000 --expand-holders

# Show which projects use this scheme
python get_permission_scheme.py 10000 --show-projects

# Output as JSON
python get_permission_scheme.py 10000 --output json

# Export grants as template
python get_permission_scheme.py 10000 --export-template grants_template.json
```

**Output Format:**
```
Permission Scheme: Default Software Scheme
ID: 10000
Description: Default permission scheme for software projects
Self: https://your-domain.atlassian.net/rest/api/3/permissionscheme/10000

Used by 3 projects: PROJ1, PROJ2, DEV

Permission Grants (25):

  BROWSE_PROJECTS
    → anyone

  CREATE_ISSUES
    → group: jira-developers (ca85fac0-d974-40ca-a615-7af99c48d24f)

  EDIT_ISSUES
    → group: jira-developers (ca85fac0-d974-40ca-a615-7af99c48d24f)
    → projectRole: Developers (10360)

  ADMINISTER_PROJECTS
    → group: jira-administrators (9f4b7d8e-1234-5678-90ab-cdef12345678)

  ...
```

**Implementation Notes:**
- Use `GET /rest/api/3/permissionscheme/{schemeId}` with `expand=permissions,user,group,projectRole`
- Support both ID and name lookup (name requires listing all schemes first)
- Group grants by permission type for readability

---

### 3. create_permission_scheme.py

**Purpose:** Create a new permission scheme with optional initial grants.

**CLI Interface:**
```bash
# Create basic scheme (no grants)
python create_permission_scheme.py --name "New Scheme" --description "Description"

# Create from template file
python create_permission_scheme.py --name "New Scheme" --template grants_template.json

# Create with inline grants
python create_permission_scheme.py --name "New Scheme" \
  --grant "BROWSE_PROJECTS:anyone" \
  --grant "CREATE_ISSUES:group:jira-developers" \
  --grant "ADMINISTER_PROJECTS:group:jira-administrators"

# Clone from existing scheme
python create_permission_scheme.py --name "New Scheme" --clone 10000

# Clone from existing scheme by name
python create_permission_scheme.py --name "New Scheme" --clone "Default Software Scheme"

# Dry run
python create_permission_scheme.py --name "New Scheme" --template grants.json --dry-run
```

**Grant Format:**
```
PERMISSION:HOLDER_TYPE:HOLDER_PARAMETER

Examples:
  BROWSE_PROJECTS:anyone
  CREATE_ISSUES:group:jira-developers
  EDIT_ISSUES:projectRole:Developers
  ADMINISTER_PROJECTS:projectLead
```

**Template File Format (JSON):**
```json
{
  "name": "Custom Development Scheme",
  "description": "Permission scheme for development projects",
  "permissions": [
    {
      "holder": {"type": "anyone"},
      "permission": "BROWSE_PROJECTS"
    },
    {
      "holder": {"type": "group", "parameter": "jira-developers"},
      "permission": "CREATE_ISSUES"
    },
    {
      "holder": {"type": "projectRole", "parameter": "Developers"},
      "permission": "EDIT_ISSUES"
    }
  ]
}
```

**Implementation Notes:**
- Use `POST /rest/api/3/permissionscheme`
- Validate permission keys against `GET /rest/api/3/permissions`
- Validate holder parameters (check groups/roles exist)
- For clone operations, fetch existing scheme and modify name/description

---

### 4. update_permission_scheme.py

**Purpose:** Update permission scheme metadata (name, description) and manage grants.

**CLI Interface:**
```bash
# Update name
python update_permission_scheme.py 10000 --name "Updated Name"

# Update description
python update_permission_scheme.py 10000 --description "Updated description"

# Update both
python update_permission_scheme.py 10000 --name "New Name" --description "New description"

# Add grant
python update_permission_scheme.py 10000 --add-grant "EDIT_ISSUES:group:jira-developers"

# Remove grant (by grant ID)
python update_permission_scheme.py 10000 --remove-grant 10103

# Remove grant (by permission and holder)
python update_permission_scheme.py 10000 --remove-grant "EDIT_ISSUES:group:jira-developers"

# Add multiple grants
python update_permission_scheme.py 10000 \
  --add-grant "LINK_ISSUES:group:jira-developers" \
  --add-grant "ASSIGN_ISSUES:projectRole:Developers"

# Replace all grants from template
python update_permission_scheme.py 10000 --replace-grants grants_template.json --confirm

# Dry run
python update_permission_scheme.py 10000 --add-grant "EDIT_ISSUES:group:testers" --dry-run
```

**Implementation Notes:**
- Use `PUT /rest/api/3/permissionscheme/{schemeId}` for name/description
- Use `POST /rest/api/3/permissionscheme/{schemeId}/permission` to add grants
- Use `DELETE /rest/api/3/permissionscheme/{schemeId}/permission/{permissionId}` to remove grants
- For remove by permission/holder, need to fetch all grants first to find ID
- `--replace-grants` requires confirmation as it deletes all existing grants

---

### 5. delete_permission_scheme.py

**Purpose:** Delete a permission scheme (must not be in use by projects).

**CLI Interface:**
```bash
# Delete by ID (requires confirmation)
python delete_permission_scheme.py 10050 --confirm

# Delete by name
python delete_permission_scheme.py "Custom Scheme" --confirm

# Force delete (unassign from projects first)
python delete_permission_scheme.py 10050 --force --confirm

# Check if scheme can be deleted
python delete_permission_scheme.py 10050 --check-only
```

**Output:**
```
Checking permission scheme: Custom Development Scheme (ID: 10050)

Projects using this scheme (2):
  - PROJ1 (Project One)
  - PROJ2 (Project Two)

Cannot delete: Scheme is in use by 2 projects.

To delete this scheme:
1. Reassign projects to a different scheme using assign_permission_scheme.py
2. Run this command again with --confirm

Or use --force to automatically reassign projects to the default scheme.
```

**Implementation Notes:**
- Use `DELETE /rest/api/3/permissionscheme/{schemeId}`
- Check project usage before deletion (iterate projects, check permission schemes)
- `--force` should reassign projects to default scheme (ID 0 or configurable)
- Require `--confirm` for destructive operations

---

### 6. assign_permission_scheme.py

**Purpose:** Assign a permission scheme to one or more projects.

**CLI Interface:**
```bash
# Assign to single project
python assign_permission_scheme.py --project PROJ --scheme 10050

# Assign by scheme name
python assign_permission_scheme.py --project PROJ --scheme "Custom Development Scheme"

# Assign to multiple projects
python assign_permission_scheme.py --projects PROJ1,PROJ2,PROJ3 --scheme 10050

# Assign to all projects matching pattern
python assign_permission_scheme.py --project-pattern "DEV-*" --scheme 10050 --confirm

# Show current scheme for project
python assign_permission_scheme.py --project PROJ --show-current

# Dry run
python assign_permission_scheme.py --project PROJ --scheme 10050 --dry-run
```

**Output:**
```
Assigning permission scheme: Custom Development Scheme (ID: 10050)

To projects:
  - PROJ1 (Project One) - currently using: Default Software Scheme (10000)
  - PROJ2 (Project Two) - currently using: Default Software Scheme (10000)

Confirm assignment? [y/N]: y

Success:
  ✓ PROJ1 - Permission scheme updated
  ✓ PROJ2 - Permission scheme updated

2 projects updated successfully.
```

**Implementation Notes:**
- Use `PUT /rest/api/3/project/{projectKeyOrId}/permissionscheme`
- For multiple projects, show current schemes and require confirmation
- Support project key patterns (list all projects, filter by pattern)
- Validate scheme exists before attempting assignment

---

### 7. list_permissions.py

**Purpose:** List all available permissions in JIRA instance (including custom permissions).

**CLI Interface:**
```bash
# List all permissions
python list_permissions.py

# Filter by type
python list_permissions.py --type PROJECT

# Search by name
python list_permissions.py --search "issue"

# Output as JSON
python list_permissions.py --output json

# Export as reference
python list_permissions.py --export permissions_reference.json
```

**Output Format:**
```
JIRA Permissions (34):

Project Permissions:
  BROWSE_PROJECTS
    Name: Browse Projects
    Description: Ability to browse projects and the issues within them.

  CREATE_ISSUES
    Name: Create Issues
    Description: Ability to create issues.

  EDIT_ISSUES
    Name: Edit Issues
    Description: Ability to edit issues.

  ...

Global Permissions:
  ADMINISTER
    Name: Jira Administrators
    Description: Ability to perform most administration functions (excluding import & export, SMTP configuration, etc.)

  ...
```

**Implementation Notes:**
- Use `GET /rest/api/3/permissions`
- Group by permission type (PROJECT, GLOBAL, etc.)
- Cache results as permissions rarely change

---

### 8. compare_permission_schemes.py

**Purpose:** Compare two permission schemes to identify differences.

**CLI Interface:**
```bash
# Compare two schemes by ID
python compare_permission_schemes.py 10000 10050

# Compare by name
python compare_permission_schemes.py "Default Software Scheme" "Custom Development Scheme"

# Show only differences
python compare_permission_schemes.py 10000 10050 --diff-only

# Export diff as JSON
python compare_permission_schemes.py 10000 10050 --output json

# Compare project's scheme with a target scheme
python compare_permission_schemes.py --project PROJ --target-scheme 10050
```

**Output Format:**
```
Comparing Permission Schemes:

Scheme A: Default Software Scheme (ID: 10000)
Scheme B: Custom Development Scheme (ID: 10050)

Permissions in A but not in B (5):
  - MANAGE_SPRINTS → group: jira-developers
  - VIEW_DEV_TOOLS → group: jira-developers
  - SCHEDULE_ISSUES → projectRole: Developers
  - SET_ISSUE_SECURITY → group: jira-administrators
  - MODIFY_REPORTER → group: jira-administrators

Permissions in B but not in A (2):
  - LINK_ISSUES → group: jira-developers
  - ADD_COMMENTS → anyone

Permissions with different holders (3):
  EDIT_ISSUES
    A: group: jira-developers
    B: group: jira-developers, projectRole: Developers

  DELETE_ISSUES
    A: group: jira-administrators
    B: group: jira-administrators, projectRole: Administrators

  WORK_ON_ISSUES
    A: projectRole: Developers
    B: group: jira-developers

Identical permissions (18):
  - BROWSE_PROJECTS → anyone
  - CREATE_ISSUES → group: jira-developers
  ...
```

**Implementation Notes:**
- Fetch both schemes with full grant details
- Normalize grants for comparison (permission + holder type + holder parameter)
- Group differences by category: unique to A, unique to B, different holders
- Useful for auditing, migration planning, troubleshooting

---

### 9. audit_permission_scheme.py

**Purpose:** Audit a permission scheme for security issues and best practices.

**CLI Interface:**
```bash
# Audit specific scheme
python audit_permission_scheme.py 10000

# Audit all schemes
python audit_permission_scheme.py --all

# Check specific issues
python audit_permission_scheme.py 10000 --check overly-permissive --check missing-admin

# Output as report
python audit_permission_scheme.py 10000 --output report --export audit_report.txt
```

**Audit Checks:**
1. **Overly permissive:**
   - ADMINISTER_PROJECTS granted to "anyone"
   - DELETE_ISSUES granted to "anyone"
   - Critical permissions granted to large groups

2. **Missing essential permissions:**
   - No BROWSE_PROJECTS grant
   - No ADMINISTER_PROJECTS grant
   - EDIT_ISSUES without CREATE_ISSUES

3. **Orphaned holders:**
   - Grants referencing deleted groups
   - Grants referencing deleted users
   - Grants referencing deleted project roles

4. **Best practices:**
   - Principle of least privilege
   - Separation of duties
   - Comment permissions match issue permissions

**Output Format:**
```
Permission Scheme Audit: Default Software Scheme (ID: 10000)

Security Issues (2):
  ⚠ HIGH: DELETE_ISSUES granted to "anyone"
    Risk: Any user can delete issues
    Recommendation: Restrict to administrators or project leads

  ⚠ MEDIUM: ADMINISTER_PROJECTS granted to group "jira-developers" (50 members)
    Risk: Large group with administrative access
    Recommendation: Use project role or smaller group

Configuration Issues (1):
  ℹ INFO: EDIT_ALL_COMMENTS granted but EDIT_OWN_COMMENTS not granted
    Recommendation: Grant EDIT_OWN_COMMENTS to allow users to edit their own comments

Orphaned Grants (0):
  ✓ No orphaned grants found

Best Practices (3):
  ✓ BROWSE_PROJECTS granted to appropriate holders
  ✓ Separation of duties maintained (admin vs user permissions)
  ℹ Consider granting VIEW_VOTERS_AND_WATCHERS to improve transparency

Summary:
  - 2 security issues found
  - 1 configuration issue found
  - 0 orphaned grants
  - Overall Score: 7/10
```

**Implementation Notes:**
- Fetch scheme with full grant details
- Validate each holder still exists (check groups, users, roles)
- Apply security rules based on permission sensitivity
- Group findings by severity (HIGH, MEDIUM, LOW, INFO)

---

## Test Cases

### Test File: test_list_permission_schemes.py

```python
def test_list_all_permission_schemes():
    """Test listing all permission schemes"""
    # Should return list of all schemes with ID, name, description

def test_list_permission_schemes_with_grants():
    """Test listing schemes with grant counts"""
    # --show-grants should include number of grants per scheme

def test_list_permission_schemes_filter_by_name():
    """Test filtering schemes by name pattern"""
    # --filter "Development" should only show matching schemes

def test_list_permission_schemes_show_projects():
    """Test showing which projects use each scheme"""
    # --show-projects should list projects per scheme

def test_list_permission_schemes_json_output():
    """Test JSON output format"""
    # --output json should return valid JSON

def test_list_permission_schemes_csv_output():
    """Test CSV output format"""
    # --output csv should return valid CSV with headers

def test_list_permission_schemes_no_results():
    """Test handling when no schemes match filter"""
    # Should display appropriate message

def test_list_permission_schemes_api_error():
    """Test handling API errors gracefully"""
    # Should catch JiraError and display user-friendly message
```

---

### Test File: test_get_permission_scheme.py

```python
def test_get_permission_scheme_by_id():
    """Test getting scheme by numeric ID"""
    # Should return full scheme details with all grants

def test_get_permission_scheme_by_name():
    """Test getting scheme by exact name"""
    # Should lookup ID from name then fetch scheme

def test_get_permission_scheme_by_name_fuzzy():
    """Test getting scheme by fuzzy name match"""
    # --fuzzy should match partial names

def test_get_permission_scheme_expand_holders():
    """Test expanding holder details"""
    # --expand-holders should show full group/user details

def test_get_permission_scheme_show_projects():
    """Test showing projects using scheme"""
    # --show-projects should list all projects

def test_get_permission_scheme_export_template():
    """Test exporting grants as template"""
    # --export-template should create valid JSON template file

def test_get_permission_scheme_not_found():
    """Test error handling for non-existent scheme"""
    # Should display clear error message

def test_get_permission_scheme_ambiguous_name():
    """Test error when multiple schemes match name"""
    # Should list matches and prompt for clarification

def test_get_permission_scheme_json_output():
    """Test JSON output format"""
    # --output json should return valid JSON
```

---

### Test File: test_create_permission_scheme.py

```python
def test_create_permission_scheme_basic():
    """Test creating scheme with name and description only"""
    # Should create empty scheme (no grants)

def test_create_permission_scheme_with_inline_grants():
    """Test creating scheme with --grant arguments"""
    # Should parse grant strings and add to scheme

def test_create_permission_scheme_from_template():
    """Test creating scheme from JSON template file"""
    # Should read template and create scheme with all grants

def test_create_permission_scheme_clone():
    """Test cloning existing scheme by ID"""
    # Should copy all grants from source scheme

def test_create_permission_scheme_clone_by_name():
    """Test cloning existing scheme by name"""
    # Should lookup source scheme then clone

def test_create_permission_scheme_validate_permissions():
    """Test validation of permission keys"""
    # Should reject invalid permission keys

def test_create_permission_scheme_validate_holders():
    """Test validation of holder parameters"""
    # Should verify groups, roles exist

def test_create_permission_scheme_dry_run():
    """Test dry run mode"""
    # --dry-run should validate but not create

def test_create_permission_scheme_duplicate_name():
    """Test error handling for duplicate names"""
    # Should allow (JIRA permits duplicate names but warn user)

def test_create_permission_scheme_invalid_grant_format():
    """Test error for malformed grant strings"""
    # Should display clear parsing error

def test_create_permission_scheme_invalid_template():
    """Test error handling for invalid template JSON"""
    # Should validate JSON schema
```

---

### Test File: test_update_permission_scheme.py

```python
def test_update_permission_scheme_name():
    """Test updating scheme name only"""
    # Should update name, preserve description and grants

def test_update_permission_scheme_description():
    """Test updating scheme description only"""
    # Should update description, preserve name and grants

def test_update_permission_scheme_both():
    """Test updating both name and description"""
    # Should update both fields

def test_update_permission_scheme_add_grant():
    """Test adding single grant"""
    # Should add grant without affecting existing grants

def test_update_permission_scheme_add_multiple_grants():
    """Test adding multiple grants in one command"""
    # Should add all specified grants

def test_update_permission_scheme_remove_grant_by_id():
    """Test removing grant by grant ID"""
    # Should delete specified grant

def test_update_permission_scheme_remove_grant_by_spec():
    """Test removing grant by permission and holder"""
    # Should lookup grant ID then delete

def test_update_permission_scheme_replace_grants():
    """Test replacing all grants from template"""
    # Should delete all existing grants, add new ones

def test_update_permission_scheme_dry_run():
    """Test dry run mode"""
    # --dry-run should validate but not modify

def test_update_permission_scheme_not_found():
    """Test error handling for non-existent scheme"""
    # Should display clear error message

def test_update_permission_scheme_invalid_grant():
    """Test error for invalid grant specification"""
    # Should reject invalid permission or holder

def test_update_permission_scheme_requires_confirmation():
    """Test that replace-grants requires --confirm"""
    # Should prompt or reject without --confirm
```

---

### Test File: test_delete_permission_scheme.py

```python
def test_delete_permission_scheme_by_id():
    """Test deleting scheme by ID with confirmation"""
    # Should delete scheme successfully

def test_delete_permission_scheme_by_name():
    """Test deleting scheme by name with confirmation"""
    # Should lookup ID then delete

def test_delete_permission_scheme_requires_confirmation():
    """Test that deletion requires --confirm"""
    # Should reject without --confirm

def test_delete_permission_scheme_in_use():
    """Test error when scheme is used by projects"""
    # Should display error with project list

def test_delete_permission_scheme_force():
    """Test force delete (unassign projects first)"""
    # Should reassign projects then delete scheme

def test_delete_permission_scheme_check_only():
    """Test check-only mode"""
    # --check-only should report usage without deleting

def test_delete_permission_scheme_not_found():
    """Test error handling for non-existent scheme"""
    # Should display clear error message

def test_delete_permission_scheme_default_scheme():
    """Test preventing deletion of default scheme"""
    # Should reject with warning (if applicable)
```

---

### Test File: test_assign_permission_scheme.py

```python
def test_assign_permission_scheme_single_project():
    """Test assigning scheme to one project"""
    # Should update project's permission scheme

def test_assign_permission_scheme_by_name():
    """Test assigning scheme using scheme name"""
    # Should lookup scheme ID then assign

def test_assign_permission_scheme_multiple_projects():
    """Test assigning scheme to multiple projects"""
    # Should update all specified projects

def test_assign_permission_scheme_project_pattern():
    """Test assigning to projects matching pattern"""
    # Should find projects by pattern then assign

def test_assign_permission_scheme_show_current():
    """Test showing current scheme for project"""
    # --show-current should display current assignment

def test_assign_permission_scheme_dry_run():
    """Test dry run mode"""
    # --dry-run should validate but not assign

def test_assign_permission_scheme_project_not_found():
    """Test error handling for non-existent project"""
    # Should display clear error message

def test_assign_permission_scheme_scheme_not_found():
    """Test error handling for non-existent scheme"""
    # Should display clear error message

def test_assign_permission_scheme_insufficient_permissions():
    """Test error when user lacks permissions"""
    # Should display permission error with troubleshooting
```

---

### Test File: test_list_permissions.py

```python
def test_list_all_permissions():
    """Test listing all available permissions"""
    # Should return all permissions with details

def test_list_permissions_filter_by_type():
    """Test filtering permissions by type"""
    # --type PROJECT should only show project permissions

def test_list_permissions_search():
    """Test searching permissions by name"""
    # --search "issue" should match all issue-related permissions

def test_list_permissions_json_output():
    """Test JSON output format"""
    # --output json should return valid JSON

def test_list_permissions_export():
    """Test exporting permissions reference"""
    # --export should create reference file
```

---

### Test File: test_compare_permission_schemes.py

```python
def test_compare_two_schemes_by_id():
    """Test comparing schemes by ID"""
    # Should show differences and similarities

def test_compare_two_schemes_by_name():
    """Test comparing schemes by name"""
    # Should lookup IDs then compare

def test_compare_schemes_diff_only():
    """Test showing only differences"""
    # --diff-only should hide identical grants

def test_compare_schemes_json_output():
    """Test JSON diff output"""
    # --output json should return structured diff

def test_compare_project_scheme_with_target():
    """Test comparing project's scheme with target"""
    # Should fetch project's scheme then compare

def test_compare_identical_schemes():
    """Test comparing identical schemes"""
    # Should report no differences
```

---

### Test File: test_audit_permission_scheme.py

```python
def test_audit_single_scheme():
    """Test auditing one scheme"""
    # Should check all audit rules and report findings

def test_audit_all_schemes():
    """Test auditing all schemes"""
    # --all should audit every scheme in instance

def test_audit_detect_overly_permissive():
    """Test detecting overly permissive grants"""
    # Should flag dangerous "anyone" grants

def test_audit_detect_missing_essential():
    """Test detecting missing essential permissions"""
    # Should flag schemes without BROWSE or ADMINISTER

def test_audit_detect_orphaned_holders():
    """Test detecting orphaned group/role references"""
    # Should flag grants with non-existent holders

def test_audit_check_best_practices():
    """Test checking best practice compliance"""
    # Should recommend improvements

def test_audit_output_report():
    """Test report output format"""
    # --output report should generate readable report
```

---

## Phase Breakdown

### Phase 1: Core Operations (Week 1)

**Deliverables:**
- `list_permission_schemes.py` (8 tests)
- `get_permission_scheme.py` (9 tests)
- `list_permissions.py` (5 tests)
- Shared library additions in `lib/permission_helpers.py`:
  - `parse_grant_string()` - Parse grant format strings
  - `format_grant()` - Format grant for display
  - `validate_permission()` - Validate permission key
  - `validate_holder()` - Validate holder type/parameter
  - `find_scheme_by_name()` - Lookup scheme by name

**Test Coverage:** 22 unit tests

**Effort Estimate:** 16-20 hours

**Acceptance Criteria:**
- [ ] All 22 tests passing
- [ ] Can list and view all permission schemes
- [ ] Can lookup permissions by name or ID
- [ ] Output formatting (table, JSON, CSV)
- [ ] Error handling for API failures

---

### Phase 2: Scheme Modification (Week 2)

**Deliverables:**
- `create_permission_scheme.py` (11 tests)
- `update_permission_scheme.py` (12 tests)
- `delete_permission_scheme.py` (8 tests)
- Template file support (JSON schema validation)
- Grant string parser (PERMISSION:TYPE:PARAMETER)

**Test Coverage:** 31 unit tests

**Effort Estimate:** 20-24 hours

**Acceptance Criteria:**
- [ ] All 31 tests passing
- [ ] Can create schemes from scratch or templates
- [ ] Can clone existing schemes
- [ ] Can add/remove individual grants
- [ ] Can update scheme metadata
- [ ] Can delete unused schemes
- [ ] Dry-run support for all operations

---

### Phase 3: Project Assignment (Week 3)

**Deliverables:**
- `assign_permission_scheme.py` (9 tests)
- Project pattern matching support
- Bulk assignment with confirmation
- Current scheme lookup

**Test Coverage:** 9 unit tests

**Effort Estimate:** 12-16 hours

**Acceptance Criteria:**
- [ ] All 9 tests passing
- [ ] Can assign schemes to single or multiple projects
- [ ] Can assign by project key pattern
- [ ] Shows current assignments before changing
- [ ] Requires confirmation for bulk operations

---

### Phase 4: Advanced Features (Week 4)

**Deliverables:**
- `compare_permission_schemes.py` (6 tests)
- `audit_permission_scheme.py` (7 tests)
- Comprehensive auditing rules
- Diff visualization

**Test Coverage:** 13 unit tests

**Effort Estimate:** 16-20 hours

**Acceptance Criteria:**
- [ ] All 13 tests passing
- [ ] Can compare any two schemes
- [ ] Generates actionable diff reports
- [ ] Audits for security issues
- [ ] Detects orphaned grants
- [ ] Provides best practice recommendations

---

## Security Considerations

### Permission Requirements

All write operations require **Administer Jira** global permission. This is one of the highest permission levels in JIRA.

**Risk Mitigation:**
1. Document permission requirements clearly in `--help` output
2. Provide clear error messages when permissions are insufficient
3. Recommend creating service accounts with minimal required permissions
4. Implement audit logging for all write operations

### Audit Logging

Log all modification operations to help with compliance and troubleshooting:

```python
import logging

logger = logging.getLogger('jira-admin.permissions')

def create_permission_scheme(name, description, grants):
    logger.info(f"Creating permission scheme: {name}")
    logger.debug(f"Grants: {len(grants)}")
    # ... implementation
    logger.info(f"Created permission scheme: {name} (ID: {scheme_id})")
```

### Validation Best Practices

1. **Validate before API calls:**
   - Check permission keys exist
   - Check holder groups/roles exist
   - Check projects exist before assignment

2. **Warn on dangerous operations:**
   - Assigning admin permissions to "anyone"
   - Deleting schemes used by many projects
   - Replacing all grants (data loss risk)

3. **Require explicit confirmation:**
   - Use `--confirm` flag for destructive operations
   - Display what will change before executing
   - Implement `--dry-run` for testing

### Holder Parameter Security

When granting permissions to users or groups:

1. **Validate group existence:**
   ```python
   def validate_group_exists(group_name):
       response = jira_client.get(f'/rest/api/3/group?groupname={group_name}')
       if response.status_code == 404:
           raise ValidationError(f"Group not found: {group_name}")
   ```

2. **Validate user existence:**
   ```python
   def validate_user_exists(account_id):
       response = jira_client.get(f'/rest/api/3/user?accountId={account_id}')
       if response.status_code == 404:
           raise ValidationError(f"User not found: {account_id}")
   ```

3. **Validate project role existence:**
   ```python
   def validate_project_role_exists(role_name):
       response = jira_client.get('/rest/api/3/role')
       roles = response.json()
       if role_name not in [r['name'] for r in roles]:
           raise ValidationError(f"Project role not found: {role_name}")
   ```

---

## Example CLI Usage Scenarios

### Scenario 1: Clone and Customize Existing Scheme

**Goal:** Create a new scheme based on the default, but with stricter permissions.

```bash
# 1. View the default scheme
python get_permission_scheme.py "Default Software Scheme" --show-grants

# 2. Clone it with a new name
python create_permission_scheme.py \
  --name "Restricted Development Scheme" \
  --clone "Default Software Scheme"

# 3. Remove overly permissive grants
python update_permission_scheme.py \
  "Restricted Development Scheme" \
  --remove-grant "DELETE_ISSUES:anyone" \
  --remove-grant "ADMINISTER_PROJECTS:group:jira-developers"

# 4. Add more restrictive grants
python update_permission_scheme.py \
  "Restricted Development Scheme" \
  --add-grant "DELETE_ISSUES:group:jira-administrators" \
  --add-grant "ADMINISTER_PROJECTS:projectRole:Administrators"

# 5. Audit the new scheme
python audit_permission_scheme.py "Restricted Development Scheme"
```

---

### Scenario 2: Standardize Permissions Across Projects

**Goal:** Apply consistent permission scheme to all development projects.

```bash
# 1. List current schemes and their usage
python list_permission_schemes.py --show-projects

# 2. Compare schemes to identify differences
python compare_permission_schemes.py \
  "Dev Team Scheme" \
  "QA Team Scheme" \
  --diff-only

# 3. Create standardized scheme
python create_permission_scheme.py \
  --name "Standard Development Scheme" \
  --template standard_dev_template.json

# 4. Assign to all DEV projects (with confirmation)
python assign_permission_scheme.py \
  --project-pattern "DEV-*" \
  --scheme "Standard Development Scheme" \
  --confirm

# 5. Verify assignment
python list_permission_schemes.py --show-projects | grep "Standard Development"
```

---

### Scenario 3: Audit and Fix Security Issues

**Goal:** Find and fix security issues across all permission schemes.

```bash
# 1. Audit all schemes
python audit_permission_scheme.py --all --output report --export audit_report.txt

# 2. Review findings (manually inspect audit_report.txt)
cat audit_report.txt

# 3. Fix high-severity issues in specific scheme
python update_permission_scheme.py 10000 \
  --remove-grant "DELETE_ISSUES:anyone" \
  --add-grant "DELETE_ISSUES:group:jira-administrators" \
  --confirm

# 4. Re-audit to verify fixes
python audit_permission_scheme.py 10000
```

---

### Scenario 4: Set Up New Project with Custom Permissions

**Goal:** Create project-specific permission scheme and assign it.

```bash
# 1. Create the permission scheme
python create_permission_scheme.py \
  --name "SecretProject Permissions" \
  --grant "BROWSE_PROJECTS:group:secretproject-team" \
  --grant "CREATE_ISSUES:group:secretproject-team" \
  --grant "EDIT_ISSUES:group:secretproject-team" \
  --grant "ADMINISTER_PROJECTS:group:secretproject-admins"

# 2. Assign to project
python assign_permission_scheme.py \
  --project SECRET \
  --scheme "SecretProject Permissions"

# 3. Verify assignment
python get_permission_scheme.py "SecretProject Permissions" --show-projects
```

---

### Scenario 5: Migrate Permission Scheme (Export/Import)

**Goal:** Export scheme from one JIRA instance and import to another.

```bash
# On source JIRA instance:
python get_permission_scheme.py "Production Scheme" \
  --export-template prod_scheme.json

# Copy prod_scheme.json to destination instance

# On destination JIRA instance:
python create_permission_scheme.py \
  --name "Production Scheme" \
  --template prod_scheme.json

# Verify import
python get_permission_scheme.py "Production Scheme"
```

---

## Integration with Existing Skills

### 1. Integration with jira-issue skill

When creating issues, check project permissions:

```bash
# Check if user can create issues in project
python list_permissions.py --check CREATE_ISSUES --project PROJ --user current

# Example: jira-issue create_issue.py could check permissions before attempting
```

### 2. Integration with Project Management scripts

When creating projects, assign appropriate permission scheme:

```bash
# Create project with specific permission scheme
python create_project.py --key PROJ --name "New Project" \
  --permission-scheme "Standard Development Scheme"
```

### 3. Integration with User Management scripts

When adding users to groups, show permission impact:

```bash
# Show what permissions a user will gain
python add_user_to_group.py john@example.com --group jira-developers \
  --show-permissions

# Would display: "This user will gain permissions from 3 permission schemes:
# - Default Software Scheme (PROJ1, PROJ2)
# - Development Scheme (DEV1, DEV2, DEV3)
```

---

## Common Troubleshooting Scenarios

### Issue 1: "You do not have permission to view permission schemes"

**Error:**
```
JiraError: 403 Forbidden - You do not have permission to view permission schemes.
```

**Cause:** User lacks "Administer Jira" global permission or "Administer project" permission.

**Solution:**
```bash
# Check your current permissions
python list_permissions.py --check ADMINISTER --user current

# Contact JIRA administrator to grant permissions
```

**Troubleshooting Steps:**
1. Verify API token has not expired
2. Check if user account is active
3. Confirm user has "Administer Jira" global permission
4. Try with a service account that has admin permissions

---

### Issue 2: "Cannot delete permission scheme: in use by projects"

**Error:**
```
JiraError: 400 Bad Request - The permission scheme cannot be deleted because it is used by one or more projects.
```

**Cause:** Scheme is assigned to active projects.

**Solution:**
```bash
# Find which projects use the scheme
python get_permission_scheme.py 10050 --show-projects

# Reassign projects to different scheme
python assign_permission_scheme.py --projects PROJ1,PROJ2 --scheme 10000 --confirm

# Now delete the scheme
python delete_permission_scheme.py 10050 --confirm

# Or use force delete (reassigns to default automatically)
python delete_permission_scheme.py 10050 --force --confirm
```

---

### Issue 3: "Group not found" when creating grant

**Error:**
```
ValidationError: Group not found: jira-developers
```

**Cause:** Group name is misspelled or group doesn't exist.

**Solution:**
```bash
# List all groups to find correct name
python list_groups.py | grep -i developer

# Use exact group name
python create_permission_scheme.py --name "New Scheme" \
  --grant "CREATE_ISSUES:group:jira-software-users"
```

---

### Issue 4: Permission scheme changes not taking effect

**Symptom:** Updated permission scheme but users still can't access project.

**Causes:**
1. Wrong project using the scheme
2. Issue security scheme overriding
3. Browser cache

**Solution:**
```bash
# 1. Verify correct scheme is assigned
python assign_permission_scheme.py --project PROJ --show-current

# 2. Check permission grants
python get_permission_scheme.py "Scheme Name" --show-grants

# 3. Verify user is in the granted group
python get_group_members.py "jira-developers" | grep user@example.com

# 4. Check if issue security is restricting access
# (Note: Issue security schemes are separate from permission schemes)
```

---

## Template Examples

### Template 1: Basic Development Scheme

**File:** `templates/basic_dev_scheme.json`

```json
{
  "name": "Basic Development Scheme",
  "description": "Standard permissions for development projects",
  "permissions": [
    {
      "holder": {"type": "anyone"},
      "permission": "BROWSE_PROJECTS"
    },
    {
      "holder": {"type": "group", "parameter": "jira-software-users"},
      "permission": "CREATE_ISSUES"
    },
    {
      "holder": {"type": "group", "parameter": "jira-software-users"},
      "permission": "EDIT_ISSUES"
    },
    {
      "holder": {"type": "group", "parameter": "jira-software-users"},
      "permission": "ADD_COMMENTS"
    },
    {
      "holder": {"type": "group", "parameter": "jira-software-users"},
      "permission": "CREATE_ATTACHMENTS"
    },
    {
      "holder": {"type": "projectRole", "parameter": "Developers"},
      "permission": "RESOLVE_ISSUES"
    },
    {
      "holder": {"type": "projectRole", "parameter": "Developers"},
      "permission": "CLOSE_ISSUES"
    },
    {
      "holder": {"type": "projectRole", "parameter": "Administrators"},
      "permission": "ADMINISTER_PROJECTS"
    },
    {
      "holder": {"type": "projectRole", "parameter": "Administrators"},
      "permission": "DELETE_ISSUES"
    },
    {
      "holder": {"type": "projectRole", "parameter": "Developers"},
      "permission": "MANAGE_SPRINTS"
    }
  ]
}
```

---

### Template 2: Restricted Internal Scheme

**File:** `templates/restricted_internal_scheme.json`

```json
{
  "name": "Restricted Internal Scheme",
  "description": "Highly restricted permissions for sensitive internal projects",
  "permissions": [
    {
      "holder": {"type": "group", "parameter": "internal-employees"},
      "permission": "BROWSE_PROJECTS"
    },
    {
      "holder": {"type": "group", "parameter": "project-contributors"},
      "permission": "CREATE_ISSUES"
    },
    {
      "holder": {"type": "group", "parameter": "project-contributors"},
      "permission": "EDIT_ISSUES"
    },
    {
      "holder": {"type": "projectLead"},
      "permission": "DELETE_ISSUES"
    },
    {
      "holder": {"type": "group", "parameter": "jira-administrators"},
      "permission": "ADMINISTER_PROJECTS"
    },
    {
      "holder": {"type": "projectLead"},
      "permission": "ADMINISTER_PROJECTS"
    }
  ]
}
```

---

### Template 3: Public Open Source Scheme

**File:** `templates/public_opensource_scheme.json`

```json
{
  "name": "Public Open Source Scheme",
  "description": "Permissive scheme for public open source projects",
  "permissions": [
    {
      "holder": {"type": "anyone"},
      "permission": "BROWSE_PROJECTS"
    },
    {
      "holder": {"type": "anyone"},
      "permission": "CREATE_ISSUES"
    },
    {
      "holder": {"type": "anyone"},
      "permission": "ADD_COMMENTS"
    },
    {
      "holder": {"type": "reporter"},
      "permission": "EDIT_OWN_COMMENTS"
    },
    {
      "holder": {"type": "group", "parameter": "contributors"},
      "permission": "EDIT_ISSUES"
    },
    {
      "holder": {"type": "group", "parameter": "contributors"},
      "permission": "RESOLVE_ISSUES"
    },
    {
      "holder": {"type": "group", "parameter": "maintainers"},
      "permission": "CLOSE_ISSUES"
    },
    {
      "holder": {"type": "group", "parameter": "maintainers"},
      "permission": "DELETE_ISSUES"
    },
    {
      "holder": {"type": "projectRole", "parameter": "Administrators"},
      "permission": "ADMINISTER_PROJECTS"
    }
  ]
}
```

---

## Documentation Requirements

### 1. Update SKILL.md

Add permission schemes section to `.claude/skills/jira-admin/SKILL.md`:

```markdown
### Permission Schemes

Manage JIRA permission schemes to control who can perform actions in projects.

**Scripts:**
- `list_permission_schemes.py` - List all permission schemes
- `get_permission_scheme.py` - Get detailed scheme information
- `create_permission_scheme.py` - Create new permission scheme
- `update_permission_scheme.py` - Modify existing scheme
- `delete_permission_scheme.py` - Delete permission scheme
- `assign_permission_scheme.py` - Assign scheme to projects
- `list_permissions.py` - List all available permissions
- `compare_permission_schemes.py` - Compare two schemes
- `audit_permission_scheme.py` - Audit scheme for issues

**Common Tasks:**

Clone and customize scheme:
```bash
python create_permission_scheme.py --name "New Scheme" --clone "Default Scheme"
python update_permission_scheme.py "New Scheme" --add-grant "EDIT_ISSUES:group:developers"
```

Assign to project:
```bash
python assign_permission_scheme.py --project PROJ --scheme "New Scheme"
```

Audit security:
```bash
python audit_permission_scheme.py "New Scheme"
```
```

---

### 2. Update CLAUDE.md

Add permission schemes patterns to project root `CLAUDE.md`:

```markdown
**Permission Scheme Management**: Use the Permission Scheme APIs for security configuration:
- Scheme CRUD: `/rest/api/3/permissionscheme` for create, read, update, delete
- Grant management: `/rest/api/3/permissionscheme/{id}/permission` for adding/removing grants
- Project assignment: `/rest/api/3/project/{key}/permissionscheme` for assigning schemes
- Holder types: user, group, projectRole, projectLead, reporter, currentAssignee, anyone
- Grant format: `{permission: "CREATE_ISSUES", holder: {type: "group", parameter: "developers"}}`
- Integration: `create_project.py --permission-scheme`, `assign_permission_scheme.py`, `audit_permission_scheme.py`
```

---

### 3. Create User Guide

**File:** `.claude/skills/jira-admin/docs/permission_schemes_guide.md`

Include:
- Overview of permission schemes
- How permissions work in JIRA
- Common permission patterns
- Security best practices
- Troubleshooting guide
- Template library
- Integration examples

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 75+ unit tests passing
- [ ] Coverage ≥ 85%
- [ ] All edge cases covered

**Scripts:**
- [ ] 9 scripts implemented
- [ ] All scripts have `--help`
- [ ] All scripts support `--profile`
- [ ] All write operations have `--dry-run`
- [ ] All destructive operations require `--confirm`

**Documentation:**
- [ ] SKILL.md updated with permission schemes section
- [ ] CLAUDE.md updated with patterns
- [ ] User guide created
- [ ] Template library provided
- [ ] Troubleshooting guide complete

**Integration:**
- [ ] Integrated with project creation scripts
- [ ] Integrated with user management scripts
- [ ] Audit logging implemented
- [ ] Error handling comprehensive

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Permission denied errors | High | High | Clear error messages, permission checker script |
| Schemes in use can't be deleted | Medium | Low | Check usage before delete, provide force option |
| Invalid holder references | Medium | Medium | Validate groups/roles exist before creating grants |
| Overly permissive defaults | Low | High | Audit script detects and warns about security issues |
| API rate limits | Low | Medium | Implement retry with backoff (already in shared lib) |
| Breaking changes in scheme API | Low | High | Version pin API, monitor Atlassian changelog |

---

## Summary Metrics

| Category | Count |
|----------|-------|
| Scripts | 9 |
| Unit Tests | 75 |
| API Endpoints | 11 |
| Holder Types | 8 |
| Permission Types | 34+ |
| Templates | 3 |
| Effort (hours) | 64-80 |
| Duration (weeks) | 4 |

---

**Document Version:** 1.0
**Created:** 2025-12-26
**Status:** Ready for Implementation

---

## Sources

This implementation plan was researched using the following official Atlassian documentation:

- [The Jira Cloud platform REST API - Permission Schemes](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-permission-schemes/)
- [The Jira Cloud platform REST API - Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-permissions/)
- [What are permission schemes in Jira? | Atlassian Support](https://support.atlassian.com/jira-cloud-administration/docs/manage-project-permissions/)
- [Types of permissions in Jira | Atlassian Support](https://support.atlassian.com/jira-service-management-cloud/docs/overview-of-jira-cloud-permissions/)
- [Find groups used in Jira Cloud permission schemes with REST API and Python | Atlassian Support](https://support.atlassian.com/jira/kb/how-to-find-group-usage-in-permission-schemes-for-jira-cloud-via-rest-api-and-python/)
