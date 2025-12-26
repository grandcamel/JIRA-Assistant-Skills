# JIRA Admin Skill - Project Management Implementation Plan

## Overview

**Objective:** Implement comprehensive project creation, configuration, and management functionality for JIRA administration using Test-Driven Development (TDD)

**Scope:** This plan covers project CRUD operations, project categories, project types/templates, and basic project configuration management.

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
1. **Phase 1: Project CRUD** (Create, read, update, delete, list projects)
2. **Phase 2: Project Categories** (Create, list, assign categories)
3. **Phase 3: Project Configuration** (Avatars, leads, permissions schemes)
4. **Phase 4: Archive/Restore Operations** (Archive, restore, trash management)

---

## JIRA Cloud REST API Reference

### Project Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|---------------------|
| GET | `/rest/api/3/project` | Get all projects (paginated) | Browse Projects |
| POST | `/rest/api/3/project` | Create a new project | Administer Jira (global) |
| GET | `/rest/api/3/project/{projectIdOrKey}` | Get project details | Browse Projects or Administer Projects |
| PUT | `/rest/api/3/project/{projectIdOrKey}` | Update project | Administer Projects or Administer Jira (for schemes/key) |
| DELETE | `/rest/api/3/project/{projectIdOrKey}` | Delete project (sync, moved to trash) | Administer Jira (global) |
| POST | `/rest/api/3/project/{projectIdOrKey}/delete` | Delete project asynchronously | Administer Jira (global) |
| POST | `/rest/api/3/project/{projectIdOrKey}/archive` | Archive a project | Administer Jira (global) |
| POST | `/rest/api/3/project/{projectIdOrKey}/restore` | Restore archived/trashed project | Administer Jira (global) |

### Project Type Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rest/api/3/project/type` | Get all project types |
| GET | `/rest/api/3/project/type/{projectTypeKey}` | Get project type by key |
| GET | `/rest/api/3/project/type/{projectTypeKey}/accessible` | Get accessible project type |

### Project Category Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|---------------------|
| GET | `/rest/api/3/projectCategory` | Get all project categories | Any authenticated user |
| POST | `/rest/api/3/projectCategory` | Create project category | Administer Jira (global) |
| GET | `/rest/api/3/projectCategory/{id}` | Get project category by ID | Any authenticated user |
| PUT | `/rest/api/3/projectCategory/{id}` | Update project category | Administer Jira (global) |
| DELETE | `/rest/api/3/projectCategory/{id}` | Delete project category | Administer Jira (global) |

### Project Avatar Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rest/api/3/project/{projectIdOrKey}/avatar2` | Load project avatar |
| GET | `/rest/api/3/project/{projectIdOrKey}/avatars` | Get all project avatars |
| DELETE | `/rest/api/3/project/{projectIdOrKey}/avatar/{id}` | Delete project avatar |

---

## API Request/Response Examples

### Create Project Request

```json
POST /rest/api/3/project
{
  "key": "PROJ",
  "name": "My Project",
  "description": "Project description in plain text",
  "projectTypeKey": "software",
  "projectTemplateKey": "com.pyxis.greenhopper.jira:gh-scrum-template",
  "lead": "charlie@example.com",
  "url": "https://example.com/project",
  "assigneeType": "PROJECT_LEAD",
  "categoryId": 10000,
  "notificationScheme": 10000,
  "permissionScheme": 10000,
  "issueSecurityScheme": 10000
}
```

**Response (201 Created):**
```json
{
  "self": "https://your-domain.atlassian.net/rest/api/3/project/10000",
  "id": "10000",
  "key": "PROJ",
  "name": "My Project",
  "avatarUrls": {
    "48x48": "https://your-domain.atlassian.net/secure/projectavatar?avatarId=10324",
    "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&avatarId=10324",
    "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&avatarId=10324",
    "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&avatarId=10324"
  },
  "projectTypeKey": "software",
  "simplified": false,
  "style": "classic",
  "isPrivate": false
}
```

### Get Project Response

```json
GET /rest/api/3/project/PROJ
{
  "expand": "description,lead,issueTypes,url,projectKeys,permissions,insight",
  "self": "https://your-domain.atlassian.net/rest/api/3/project/10000",
  "id": "10000",
  "key": "PROJ",
  "name": "My Project",
  "description": "Project description",
  "lead": {
    "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g",
    "accountId": "5b10a2844c20165700ede21g",
    "displayName": "Charlie Brown",
    "active": true
  },
  "components": [],
  "issueTypes": [...],
  "assigneeType": "PROJECT_LEAD",
  "versions": [],
  "roles": {...},
  "avatarUrls": {...},
  "projectTypeKey": "software",
  "simplified": false,
  "style": "classic",
  "isPrivate": false,
  "projectCategory": {
    "self": "https://your-domain.atlassian.net/rest/api/3/projectCategory/10000",
    "id": "10000",
    "name": "Development",
    "description": "Development projects"
  },
  "url": "https://example.com/project"
}
```

### Update Project Request

```json
PUT /rest/api/3/project/PROJ
{
  "name": "Updated Project Name",
  "description": "Updated description",
  "lead": "alice@example.com",
  "url": "https://example.com/updated",
  "assigneeType": "UNASSIGNED",
  "categoryId": 10001
}
```

### Create Project Category Request

```json
POST /rest/api/3/projectCategory
{
  "name": "Development",
  "description": "All development projects"
}
```

**Response (201 Created):**
```json
{
  "self": "https://your-domain.atlassian.net/rest/api/3/projectCategory/10000",
  "id": "10000",
  "name": "Development",
  "description": "All development projects"
}
```

---

## Project Types and Templates

### Project Type Keys

- **software**: Jira Software projects (requires Jira Software license)
- **business**: Jira Core/Work Management projects
- **service_desk**: Jira Service Management projects (requires JSM license)

### Common Project Template Keys

#### Software Project Templates
- `com.pyxis.greenhopper.jira:gh-scrum-template` - Scrum board
- `com.pyxis.greenhopper.jira:gh-kanban-template` - Kanban board
- `com.pyxis.greenhopper.jira:basic-software-development-template` - Basic software
- `com.pyxis.greenhopper.jira:gh-simplified-agility-scrum` - Simplified Scrum
- `com.pyxis.greenhopper.jira:gh-simplified-agility-kanban` - Simplified Kanban
- `com.pyxis.greenhopper.jira:gh-simplified-basic` - Simplified Basic

#### Business Project Templates
- `com.atlassian.jira-core-project-templates:jira-core-project-management` - Project Management
- `com.atlassian.jira-core-project-templates:jira-core-task-management` - Task Management
- `com.atlassian.jira-core-project-templates:jira-core-process-management` - Process Management

#### Service Desk Templates
- `com.atlassian.servicedesk:simplified-it-service-desk` - IT Service Desk
- `com.atlassian.servicedesk:simplified-general-service-desk` - General Service Desk
- `com.atlassian.servicedesk:simplified-internal-service-desk` - Internal Service Desk

**Note:** Templates are only used during project creation and don't persist after the project is created.

---

## Phase 1: Project CRUD Operations

### Feature 1.1: Create Project

**Script:** `create_project.py`

**JIRA API:**
- `POST /rest/api/3/project`
- `GET /rest/api/3/project/type` (to list available types)

**Test File:** `tests/test_create_project.py`

**Test Cases:**
```python
def test_create_project_minimal():
    """Test creating project with only required fields (key, name, type)"""
    # Should POST with key, name, projectTypeKey

def test_create_project_with_template():
    """Test creating project with specific template"""
    # Should set projectTemplateKey for scrum/kanban/etc

def test_create_project_with_lead():
    """Test setting project lead"""
    # Should set lead field with account ID or email

def test_create_project_with_description():
    """Test creating project with description"""
    # Should set description field

def test_create_project_with_category():
    """Test assigning project to category"""
    # Should set categoryId

def test_create_project_invalid_key():
    """Test validation of project key (uppercase, starts with letter)"""
    # Should raise ValidationError for invalid keys

def test_create_project_duplicate_key():
    """Test error when key already exists"""
    # Should raise ConflictError

def test_create_project_invalid_type():
    """Test error for invalid project type"""
    # Should raise ValidationError

def test_create_project_no_permission():
    """Test error when user lacks admin permission"""
    # Should raise PermissionError
```

**CLI Interface:**
```bash
# Minimal - create software project
python create_project.py --key PROJ --name "My Project" --type software

# With template
python create_project.py --key SCRUM --name "Scrum Project" --type software --template scrum
python create_project.py --key KANBAN --name "Kanban Board" --type software --template kanban

# With all options
python create_project.py --key PROJ --name "Full Project" \
  --type software --template scrum \
  --lead charlie@example.com \
  --description "A comprehensive project" \
  --category 10000 \
  --url https://example.com/project

# Interactive template selection
python create_project.py --key PROJ --name "My Project" --type software --interactive
```

**Output Example:**
```
Creating project...
Project created successfully!

Key: PROJ
Name: My Project
ID: 10000
Type: software
Template: Scrum
Lead: Charlie Brown (charlie@example.com)
URL: https://your-domain.atlassian.net/browse/PROJ

Board created: PROJ board (ID: 123)
```

**Acceptance Criteria:**
- All 9 tests pass
- Validates project key format (uppercase, starts with letter, 2-10 chars)
- Supports all three project types (software, business, service_desk)
- Template shortcuts (scrum, kanban, basic) map to full template keys
- Clear error messages for permission/validation issues

**Commits:**
1. `test(jira-admin): add failing tests for create_project`
2. `feat(jira-admin): implement create_project.py (9/9 tests passing)`

---

### Feature 1.2: Get Project

**Script:** `get_project.py`

**JIRA API:**
- `GET /rest/api/3/project/{projectIdOrKey}`

**Test File:** `tests/test_get_project.py`

**Test Cases:**
```python
def test_get_project_by_key():
    """Test fetching project by key"""

def test_get_project_by_id():
    """Test fetching project by ID"""

def test_get_project_with_expand():
    """Test expanding additional fields (lead, issueTypes, etc)"""

def test_get_project_format_text():
    """Test human-readable output"""

def test_get_project_format_json():
    """Test JSON output"""

def test_get_project_not_found():
    """Test error when project doesn't exist"""

def test_get_project_show_components():
    """Test showing project components"""

def test_get_project_show_versions():
    """Test showing project versions"""
```

**CLI Interface:**
```bash
python get_project.py PROJ
python get_project.py 10000
python get_project.py PROJ --output json
python get_project.py PROJ --show-components --show-versions
```

**Output Example:**
```
Project: PROJ - My Project
ID: 10000
Type: software (Scrum)
Lead: Charlie Brown (charlie@example.com)
Category: Development
URL: https://example.com/project

Description:
  A comprehensive development project for the team

Statistics:
  Issue Types: 10 (Story, Bug, Task, Epic, Sub-task, ...)
  Components: 3 (Backend, Frontend, Mobile)
  Versions: 5 (1.0, 1.1, 2.0, ...)

Created: 2025-01-15
Style: Company-managed (classic)
```

**Acceptance Criteria:**
- All 8 tests pass
- Shows complete project metadata
- Optional expansion of related data
- Both text and JSON output formats

**Commits:**
1. `test(jira-admin): add failing tests for get_project`
2. `feat(jira-admin): implement get_project.py (8/8 tests passing)`

---

### Feature 1.3: List Projects

**Script:** `list_projects.py`

**JIRA API:**
- `GET /rest/api/3/project/search` (paginated)

**Test File:** `tests/test_list_projects.py`

**Test Cases:**
```python
def test_list_all_projects():
    """Test fetching all projects"""

def test_list_projects_pagination():
    """Test handling paginated results"""

def test_list_projects_filter_by_type():
    """Test filtering by project type"""

def test_list_projects_filter_by_category():
    """Test filtering by category"""

def test_list_projects_search_by_name():
    """Test searching by project name"""

def test_list_projects_format_table():
    """Test table output"""

def test_list_projects_format_json():
    """Test JSON output"""

def test_list_projects_archived():
    """Test listing archived projects"""
```

**CLI Interface:**
```bash
# List all projects
python list_projects.py

# Filter by type
python list_projects.py --type software
python list_projects.py --type business

# Filter by category
python list_projects.py --category "Development"

# Search
python list_projects.py --search "mobile"

# Include archived
python list_projects.py --include-archived

# Output formats
python list_projects.py --output json
python list_projects.py --output csv > projects.csv
```

**Output Example:**
```
Projects (showing 12 of 45):

Key       Name                    Type        Lead              Category      Issues
────────  ──────────────────────  ──────────  ────────────────  ────────────  ──────
PROJ      My Project              software    Charlie Brown     Development   156
KANBAN    Kanban Board            software    Alice Smith       Development   89
MOBILE    Mobile App              software    Bob Jones         Development   234
WEBSITE   Website Redesign        business    Diana Prince      Marketing     45
...

Use --max-results to show more projects.
```

**Acceptance Criteria:**
- All 8 tests pass
- Handles pagination automatically
- Multiple filtering options
- Table, JSON, and CSV output formats
- Shows key statistics per project

**Commits:**
1. `test(jira-admin): add failing tests for list_projects`
2. `feat(jira-admin): implement list_projects.py (8/8 tests passing)`

---

### Feature 1.4: Update Project

**Script:** `update_project.py`

**JIRA API:**
- `PUT /rest/api/3/project/{projectIdOrKey}`

**Test File:** `tests/test_update_project.py`

**Test Cases:**
```python
def test_update_project_name():
    """Test updating project name"""

def test_update_project_description():
    """Test updating description"""

def test_update_project_lead():
    """Test changing project lead"""

def test_update_project_category():
    """Test changing project category"""

def test_update_project_url():
    """Test updating project URL"""

def test_update_project_assignee_type():
    """Test changing default assignee"""

def test_update_project_key():
    """Test updating project key (requires admin)"""

def test_update_project_not_found():
    """Test error when project doesn't exist"""

def test_update_project_no_permission():
    """Test error when lacking permission"""
```

**CLI Interface:**
```bash
# Update individual fields
python update_project.py PROJ --name "Updated Project Name"
python update_project.py PROJ --description "New description"
python update_project.py PROJ --lead alice@example.com
python update_project.py PROJ --category 10001

# Update multiple fields
python update_project.py PROJ \
  --name "Updated Name" \
  --description "Updated description" \
  --url https://example.com/updated

# Update project key (dangerous!)
python update_project.py PROJ --new-key NEWKEY --confirm
```

**Output Example:**
```
Updating project PROJ...

Changes:
  Name: "My Project" → "Updated Project Name"
  Description: Updated
  Lead: charlie@example.com → alice@example.com

Project updated successfully!
```

**Acceptance Criteria:**
- All 9 tests pass
- Can update any field individually
- Project key changes require confirmation flag
- Shows diff of changes before applying
- Clear permission error messages

**Commits:**
1. `test(jira-admin): add failing tests for update_project`
2. `feat(jira-admin): implement update_project.py (9/9 tests passing)`

---

### Feature 1.5: Delete Project

**Script:** `delete_project.py`

**JIRA API:**
- `DELETE /rest/api/3/project/{projectIdOrKey}` (synchronous, moves to trash)
- `POST /rest/api/3/project/{projectIdOrKey}/delete` (asynchronous)
- `GET /rest/api/3/task/{taskId}` (for async status)

**Test File:** `tests/test_delete_project.py`

**Test Cases:**
```python
def test_delete_project_sync():
    """Test synchronous project deletion"""

def test_delete_project_async():
    """Test asynchronous project deletion"""

def test_delete_project_poll_status():
    """Test polling task status for async delete"""

def test_delete_project_with_confirmation():
    """Test confirmation prompt"""

def test_delete_project_dry_run():
    """Test dry-run preview"""

def test_delete_project_not_found():
    """Test error when project doesn't exist"""

def test_delete_archived_project():
    """Test deleting archived project (requires restore first)"""
```

**CLI Interface:**
```bash
# Delete with confirmation prompt
python delete_project.py PROJ

# Skip confirmation
python delete_project.py PROJ --yes

# Asynchronous delete (for large projects)
python delete_project.py PROJ --async

# Dry run
python delete_project.py PROJ --dry-run
```

**Output Example:**
```
WARNING: You are about to delete project PROJ (My Project)
This will move the project to trash. It can be restored within 60 days.

Project details:
  Key: PROJ
  Name: My Project
  Issues: 156
  Lead: Charlie Brown

Are you sure you want to delete this project? (yes/no): yes

Deleting project...
Project PROJ moved to trash.

The project can be restored within 60 days using:
  python restore_project.py PROJ
```

**Acceptance Criteria:**
- All 7 tests pass
- Confirmation prompt (skippable with --yes)
- Shows project details before delete
- Supports both sync and async delete
- Polls task status for async operations
- Dry-run mode

**Commits:**
1. `test(jira-admin): add failing tests for delete_project`
2. `feat(jira-admin): implement delete_project.py (7/7 tests passing)`

---

### Phase 1 Completion

- **Phase 1 Summary:**
  - 5 scripts implemented (create_project, get_project, list_projects, update_project, delete_project)
  - 41 tests passing (9 + 8 + 8 + 9 + 7)
  - JiraClient methods added (5+ methods)
  - **Commit:** `docs(jira-admin): complete Phase 1 - Project CRUD`

---

## Phase 2: Project Categories

### Feature 2.1: Create Project Category

**Script:** `create_category.py`

**JIRA API:**
- `POST /rest/api/3/projectCategory`

**Test File:** `tests/test_create_category.py`

**Test Cases:**
```python
def test_create_category_minimal():
    """Test creating category with name only"""

def test_create_category_with_description():
    """Test creating category with description"""

def test_create_category_duplicate_name():
    """Test error when name already exists"""

def test_create_category_no_permission():
    """Test error when lacking admin permission"""
```

**CLI Interface:**
```bash
python create_category.py --name "Development"
python create_category.py --name "Development" --description "All dev projects"
```

**Acceptance Criteria:**
- All 4 tests pass
- Creates category with name and optional description
- Handles duplicate names gracefully

**Commits:**
1. `test(jira-admin): add failing tests for project categories`
2. `feat(jira-admin): implement project category management (12/12 tests passing)`

---

### Feature 2.2: List Project Categories

**Script:** `list_categories.py`

**JIRA API:**
- `GET /rest/api/3/projectCategory`

**Test File:** `tests/test_list_categories.py`

**Test Cases:**
```python
def test_list_all_categories():
    """Test fetching all categories"""

def test_list_categories_format_table():
    """Test table output"""

def test_list_categories_format_json():
    """Test JSON output"""
```

**CLI Interface:**
```bash
python list_categories.py
python list_categories.py --output json
```

**Acceptance Criteria:**
- All 3 tests pass
- Shows all categories with descriptions
- Table and JSON output

**Commits:**
1. Same as Feature 2.1

---

### Feature 2.3: Assign Category to Project

**Script:** `assign_category.py`

**JIRA API:**
- `PUT /rest/api/3/project/{projectIdOrKey}` with `categoryId`

**Test File:** `tests/test_assign_category.py`

**Test Cases:**
```python
def test_assign_category_by_id():
    """Test assigning category by ID"""

def test_assign_category_by_name():
    """Test assigning category by name (lookup)"""

def test_remove_category():
    """Test removing category from project"""

def test_assign_category_invalid_id():
    """Test error for invalid category ID"""

def test_assign_category_no_permission():
    """Test error when lacking permission"""
```

**CLI Interface:**
```bash
# Assign by category ID
python assign_category.py PROJ --category-id 10000

# Assign by category name
python assign_category.py PROJ --category "Development"

# Remove category
python assign_category.py PROJ --remove
```

**Acceptance Criteria:**
- All 5 tests pass
- Supports category ID or name lookup
- Can remove category assignment

**Commits:**
1. Same as Feature 2.1

---

### Phase 2 Completion

- **Phase 2 Summary:**
  - 3 scripts implemented (create_category, list_categories, assign_category)
  - 12 tests passing (53 total)
  - **Commit:** `docs(jira-admin): complete Phase 2 - Project Categories`

---

## Phase 3: Project Configuration

### Feature 3.1: Set Project Avatar

**Script:** `set_avatar.py`

**JIRA API:**
- `POST /rest/api/3/project/{projectIdOrKey}/avatar2`
- `GET /rest/api/3/project/{projectIdOrKey}/avatars`

**Test File:** `tests/test_set_avatar.py`

**Test Cases:**
```python
def test_upload_avatar_from_file():
    """Test uploading avatar from local file"""

def test_upload_avatar_from_url():
    """Test uploading avatar from URL"""

def test_list_available_avatars():
    """Test listing system avatars"""

def test_select_system_avatar():
    """Test selecting from system avatars"""

def test_invalid_file_format():
    """Test error for unsupported file format"""

def test_file_too_large():
    """Test error when file exceeds size limit"""
```

**CLI Interface:**
```bash
# Upload from file
python set_avatar.py PROJ --file /path/to/avatar.png

# Upload from URL
python set_avatar.py PROJ --url https://example.com/avatar.png

# List and select system avatar
python set_avatar.py PROJ --list
python set_avatar.py PROJ --avatar-id 10200
```

**Acceptance Criteria:**
- All 6 tests pass
- Supports PNG, JPEG, GIF formats
- Max file size validation (10MB)
- Can list and select system avatars

**Commits:**
1. `test(jira-admin): add failing tests for project configuration`
2. `feat(jira-admin): implement project configuration scripts (15/15 tests passing)`

---

### Feature 3.2: Update Project Lead

**Script:** `set_project_lead.py`

**JIRA API:**
- `PUT /rest/api/3/project/{projectIdOrKey}` with `lead` field

**Test File:** `tests/test_set_project_lead.py`

**Test Cases:**
```python
def test_set_lead_by_email():
    """Test setting lead by email address"""

def test_set_lead_by_account_id():
    """Test setting lead by account ID"""

def test_set_lead_user_not_found():
    """Test error when user doesn't exist"""

def test_set_lead_user_no_access():
    """Test error when user lacks project access"""
```

**CLI Interface:**
```bash
python set_project_lead.py PROJ --lead alice@example.com
python set_project_lead.py PROJ --account-id 5b10a2844c20165700ede21g
```

**Acceptance Criteria:**
- All 4 tests pass
- Supports email and account ID
- Validates user exists and has access

**Commits:**
1. Same as Feature 3.1

---

### Feature 3.3: Configure Default Assignee

**Script:** `set_default_assignee.py`

**JIRA API:**
- `PUT /rest/api/3/project/{projectIdOrKey}` with `assigneeType` field

**Test File:** `tests/test_set_default_assignee.py`

**Test Cases:**
```python
def test_set_assignee_type_project_lead():
    """Test setting default to project lead"""

def test_set_assignee_type_unassigned():
    """Test setting default to unassigned"""

def test_set_assignee_type_component_lead():
    """Test setting default to component lead"""

def test_invalid_assignee_type():
    """Test error for invalid assignee type"""
```

**CLI Interface:**
```bash
python set_default_assignee.py PROJ --type PROJECT_LEAD
python set_default_assignee.py PROJ --type UNASSIGNED
python set_default_assignee.py PROJ --type COMPONENT_LEAD
```

**Acceptance Criteria:**
- All 4 tests pass
- Supports all assignee types
- Validates assignee type

**Commits:**
1. Same as Feature 3.1

---

### Feature 3.4: Get Project Configuration

**Script:** `get_config.py`

**JIRA API:**
- `GET /rest/api/3/project/{projectIdOrKey}` with full expansion

**Test File:** `tests/test_get_config.py`

**Test Cases:**
```python
def test_get_full_configuration():
    """Test fetching complete project configuration"""

def test_show_permission_scheme():
    """Test showing permission scheme details"""

def test_show_notification_scheme():
    """Test showing notification scheme"""

def test_format_text():
    """Test human-readable output"""

def test_format_json():
    """Test JSON output"""
```

**CLI Interface:**
```bash
python get_config.py PROJ
python get_config.py PROJ --show-schemes
python get_config.py PROJ --output json
```

**Output Example:**
```
Project Configuration: PROJ - My Project

Basic Settings:
  Key: PROJ
  Type: software (Scrum)
  Lead: Charlie Brown
  Default Assignee: Project Lead
  Category: Development

Schemes:
  Permission Scheme: Default Software Permission Scheme (10000)
  Notification Scheme: Default Notification Scheme (10000)
  Issue Security Scheme: None
  Workflow Scheme: Software Simplified Workflow (10001)
  Issue Type Scheme: Default Issue Type Scheme (10000)

Settings:
  Issue Type: Bug, Story, Task, Epic, Sub-task
  Components: 3 components
  Versions: 5 versions
  Style: Company-managed (classic)
```

**Acceptance Criteria:**
- All 5 tests pass
- Shows complete configuration
- Optional scheme details
- Text and JSON output

**Commits:**
1. Same as Feature 3.1

---

### Phase 3 Completion

- **Phase 3 Summary:**
  - 4 scripts implemented (set_avatar, set_project_lead, set_default_assignee, get_config)
  - 19 tests passing (72 total)
  - **Commit:** `docs(jira-admin): complete Phase 3 - Project Configuration`

---

## Phase 4: Archive/Restore Operations

### Feature 4.1: Archive Project

**Script:** `archive_project.py`

**JIRA API:**
- `POST /rest/api/3/project/{projectIdOrKey}/archive`

**Test File:** `tests/test_archive_project.py`

**Test Cases:**
```python
def test_archive_project():
    """Test archiving a project"""

def test_archive_with_confirmation():
    """Test confirmation prompt"""

def test_archive_dry_run():
    """Test dry-run preview"""

def test_archive_already_archived():
    """Test error when already archived"""

def test_archive_no_permission():
    """Test error when lacking permission"""
```

**CLI Interface:**
```bash
python archive_project.py PROJ
python archive_project.py PROJ --yes
python archive_project.py PROJ --dry-run
```

**Output Example:**
```
Archiving project PROJ (My Project)...

Archived projects:
  - Cannot have issues created or edited
  - Can be browsed in read-only mode
  - Can be restored later

Project PROJ archived successfully.

To restore: python restore_project.py PROJ
```

**Acceptance Criteria:**
- All 5 tests pass
- Confirmation prompt
- Dry-run mode
- Explains archive implications

**Commits:**
1. `test(jira-admin): add failing tests for archive/restore operations`
2. `feat(jira-admin): implement archive/restore operations (11/11 tests passing)`

---

### Feature 4.2: Restore Project

**Script:** `restore_project.py`

**JIRA API:**
- `POST /rest/api/3/project/{projectIdOrKey}/restore`

**Test File:** `tests/test_restore_project.py`

**Test Cases:**
```python
def test_restore_archived_project():
    """Test restoring archived project"""

def test_restore_trashed_project():
    """Test restoring deleted project from trash"""

def test_restore_active_project():
    """Test error when project is not archived/trashed"""

def test_restore_no_permission():
    """Test error when lacking permission"""
```

**CLI Interface:**
```bash
python restore_project.py PROJ
python restore_project.py PROJ --yes
```

**Output Example:**
```
Restoring project PROJ...

Project PROJ restored successfully.
The project is now active and editable.

URL: https://your-domain.atlassian.net/browse/PROJ
```

**Acceptance Criteria:**
- All 4 tests pass
- Restores archived projects
- Restores trashed projects
- Clear status messages

**Commits:**
1. Same as Feature 4.1

---

### Feature 4.3: List Trashed Projects

**Script:** `list_trash.py`

**JIRA API:**
- `GET /rest/api/3/project/search` with status filter

**Test File:** `tests/test_list_trash.py`

**Test Cases:**
```python
def test_list_trashed_projects():
    """Test listing deleted projects in trash"""

def test_list_trash_format_table():
    """Test table output"""

def test_list_trash_with_expiry():
    """Test showing expiry dates"""
```

**CLI Interface:**
```bash
python list_trash.py
python list_trash.py --output json
```

**Output Example:**
```
Trashed Projects (recoverable for 60 days):

Key       Name            Deleted     Expires     Issues
────────  ──────────────  ──────────  ──────────  ──────
OLD       Old Project     2025-01-10  2025-03-11  234
TEMP      Temp Project    2025-01-15  2025-03-16  12

To restore a project: python restore_project.py <KEY>
```

**Acceptance Criteria:**
- All 3 tests pass
- Shows expiry countdown
- Table and JSON output

**Commits:**
1. Same as Feature 4.1

---

### Phase 4 Completion

- **Phase 4 Summary:**
  - 3 scripts implemented (archive_project, restore_project, list_trash)
  - 12 tests passing (84 total)
  - **Commit:** `docs(jira-admin): complete Phase 4 - Archive/Restore Operations`

---

## Integration & Polish

### Integration Tasks

- **Integration 1:** Add JiraClient methods
  - `create_project()` - Create project
  - `get_project()` - Get project details
  - `list_projects()` - List/search projects
  - `update_project()` - Update project
  - `delete_project()` - Delete project (sync/async)
  - `archive_project()` - Archive project
  - `restore_project()` - Restore project
  - `create_project_category()` - Create category
  - `list_project_categories()` - List categories
  - `upload_project_avatar()` - Upload avatar
  - **Commit:** `feat(shared): add project management methods to JiraClient`

- **Integration 2:** Add validators
  - `validate_project_key()` - Validate key format (uppercase, 2-10 chars, starts with letter)
  - `validate_project_type()` - Validate project type
  - `validate_assignee_type()` - Validate assignee type
  - **Commit:** `feat(shared): add project validation functions`

### Documentation Updates

- **Docs 1:** Create comprehensive SKILL.md
  - "When to use this skill" section
  - "What this skill does" section
  - "Available scripts" with descriptions
  - "Examples" with workflows
  - Permission requirements
  - **Commit:** `docs(jira-admin): create comprehensive SKILL.md`

- **Docs 2:** Update CLAUDE.md
  - Add jira-admin to project overview
  - Add project management patterns
  - Document permission requirements
  - **Commit:** `docs: update CLAUDE.md with jira-admin skill`

- **Docs 3:** Update GAP_ANALYSIS.md
  - Mark project management as completed
  - Update coverage metrics
  - **Commit:** `docs: update GAP_ANALYSIS.md - project management complete`

### Testing & Quality

- **Quality 1:** Live integration tests
  - Create/read/update/delete project workflow
  - Category assignment workflow
  - Archive/restore workflow
  - Permission validation
  - **Commit:** `test(jira-admin): add live integration tests for project management`

- **Quality 2:** Coverage validation
  - Run pytest with coverage
  - Ensure 85%+ coverage target
  - **Commit:** `test(jira-admin): achieve 85%+ test coverage`

- **Quality 3:** Error handling review
  - All scripts use try/except with JiraError
  - Helpful error messages
  - Permission error detection
  - **Commit:** (no separate commit, part of implementation)

---

## Success Metrics

### Completion Criteria

**Tests:**
- 84+ unit tests passing
- 10+ live integration tests
- Coverage ≥ 85%

**Scripts:**
- 15 new scripts implemented
- All scripts have `--help`
- All scripts support `--profile`
- Mutation scripts have `--dry-run` and confirmation

**Documentation:**
- SKILL.md complete
- CLAUDE.md updated
- GAP_ANALYSIS.md updated
- All scripts have docstrings

**Integration:**
- 10+ JiraClient methods added
- 3+ validators added
- No breaking changes

### Progress Tracking

**Phase Status:**
- Phase 1: Project CRUD (5 scripts, 41 tests)
- Phase 2: Project Categories (3 scripts, 12 tests)
- Phase 3: Project Configuration (4 scripts, 19 tests)
- Phase 4: Archive/Restore (3 scripts, 12 tests)
- Integration (3 tasks)
- Documentation (3 docs)
- Quality (3 tasks)

---

## Error Handling Considerations

### Common Errors and Handling

1. **Permission Errors (403)**
   - Message: "You don't have permission to administer projects. This requires Administer Jira global permission or Administer Projects project permission."
   - Suggestion: "Contact your Jira administrator to request permissions."

2. **Project Not Found (404)**
   - Message: "Project 'PROJ' not found."
   - Suggestion: "Check the project key and ensure the project exists. Use 'list_projects.py' to see available projects."

3. **Duplicate Project Key (400/409)**
   - Message: "A project with key 'PROJ' already exists."
   - Suggestion: "Choose a different project key."

4. **Invalid Project Key Format (400)**
   - Message: "Invalid project key 'proj'. Keys must be uppercase, 2-10 characters, and start with a letter."
   - Suggestion: "Example valid keys: PROJ, DEV, MOBILE"

5. **Invalid Project Type (400)**
   - Message: "Invalid project type 'invalid'. Valid types: software, business, service_desk"
   - Suggestion: "Use --type software (default), --type business, or --type service_desk"

6. **License Required (400)**
   - Message: "Cannot create 'software' project. Your Jira instance doesn't have a Jira Software license."
   - Suggestion: "Use --type business or contact your administrator to add a Jira Software license."

7. **Archived Project Delete (400)**
   - Message: "Cannot delete archived project 'PROJ'. Archived projects must be restored before deletion."
   - Suggestion: "First restore the project: python restore_project.py PROJ"

8. **Async Task Failure**
   - Message: "Project deletion task failed. Check Jira audit log for details."
   - Suggestion: "The project may have dependencies. Contact your Jira administrator."

---

## Example CLI Usage Workflows

### Workflow 1: Create a New Scrum Project

```bash
# Create project with Scrum template
python create_project.py \
  --key MOBILE \
  --name "Mobile App Development" \
  --type software \
  --template scrum \
  --lead alice@example.com \
  --description "iOS and Android mobile applications"

# Assign to category
python assign_category.py MOBILE --category "Development"

# Set project avatar
python set_avatar.py MOBILE --file /path/to/mobile-icon.png

# Verify configuration
python get_config.py MOBILE
```

### Workflow 2: Project Reorganization

```bash
# List all projects by category
python list_projects.py

# Create new categories
python create_category.py --name "Mobile" --description "Mobile applications"
python create_category.py --name "Web" --description "Web applications"

# Re-categorize projects
python assign_category.py MOBILE --category "Mobile"
python assign_category.py WEBAPP --category "Web"

# List categories
python list_categories.py
```

### Workflow 3: Project Cleanup

```bash
# Archive old projects
python archive_project.py OLDPROJ --yes

# List archived projects
python list_projects.py --include-archived

# Check trash
python list_trash.py

# Restore if needed
python restore_project.py OLDPROJ

# Permanent delete (must restore first if archived)
python delete_project.py OLDPROJ --yes
```

### Workflow 4: Bulk Project Updates

```bash
# List projects needing lead change
python list_projects.py --lead bob@example.com

# Update leads (script this in bash loop)
for project in PROJ1 PROJ2 PROJ3; do
  python set_project_lead.py $project --lead alice@example.com
done

# Verify changes
python list_projects.py --lead alice@example.com
```

---

## Important Limitations and Gotchas

### Team-Managed vs Company-Managed Projects

**Team-Managed (Next-Gen/Simplified) Projects:**
- Limited API support for configuration
- Cannot change some schemes via API
- `simplified: true` in API responses
- More restricted permissions model

**Company-Managed (Classic) Projects:**
- Full API configuration support
- Can modify all schemes
- `simplified: false` in API responses
- Traditional Jira permission model

**Impact:** Some scripts may have reduced functionality with team-managed projects. Always check the `simplified` field.

### Project Type Changes Not Supported

Atlassian has deprecated the ability to change project type via API. Once created, a project's type (software/business/service_desk) cannot be changed.

**Workaround:** Create a new project with the desired type and bulk move issues.

### Template Keys Are Not Standardized

Project template keys can vary between Jira instances. The template keys listed in this plan are common defaults, but custom templates may have different keys.

**Solution:** Provide `--list-templates` flag to discover available templates on the instance.

### Async Delete Task Tracking

Asynchronous project deletion returns a task ID. You must poll the task status endpoint to determine completion.

**Implementation:** Scripts should poll every 2-5 seconds with timeout (default 5 minutes).

### 60-Day Trash Retention

Deleted projects remain in trash for 60 days before permanent deletion. This is a Jira Cloud policy and cannot be changed via API.

### Permission Requirements

Most project administration requires **Administer Jira** global permission. Some operations (like updating project details without changing schemes) only require **Administer Projects** project permission.

**Best Practice:** Always show clear permission error messages with instructions.

---

## API Documentation Sources

- [Jira Cloud REST API - Projects](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-projects/)
- [Jira Cloud REST API - Project Types](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-project-types/)
- [Jira Cloud REST API - Project Categories](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-project-categories/)
- [Creating Projects via REST API](https://support.atlassian.com/jira/kb/creating-projects-via-rest-api-in-jira-server-and-data-center/)
- [Archive and Restore Projects](https://support.atlassian.com/jira-cloud-administration/docs/archive-a-project/)
- [Trash and Delete Projects](https://support.atlassian.com/jira-service-management-cloud/docs/trash-archive-restore-and-delete-service-projects/)
- [Project Type Deprecation Notice](https://developer.atlassian.com/cloud/jira/platform/deprecation-notice-change-project-type-via-api/)

---

**Plan Version:** 1.0
**Created:** 2025-12-26
**Status:** READY FOR IMPLEMENTATION
