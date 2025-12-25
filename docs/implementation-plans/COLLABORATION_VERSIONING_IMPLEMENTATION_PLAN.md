# JIRA Collaboration & Versioning Skill - TDD Implementation Plan

## Overview

**Objective:** Implement comment enhancements, notification management, activity stream parsing, version management, and component CRUD using Test-Driven Development (TDD)

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
- **Test Locations:**
  - `.claude/skills/jira-collaborate/tests/`
  - `.claude/skills/jira-lifecycle/tests/`

**Feature Priority:**
1. **Phase 1: Comment Enhancements** (Edit/delete, internal vs external, get comments)
2. **Phase 2: Notifications & Activity** (Send notifications, parse activity stream)
3. **Phase 3: Version Management** (Create, release, archive versions)
4. **Phase 4: Component CRUD** (Create, read, update, delete components)

---

## Current State Analysis

### Existing Infrastructure

**jira-collaborate skill (4 scripts):**
- `add_comment.py` - Add comment to issue (implemented)
- `upload_attachment.py` - Upload file to issue (implemented)
- `manage_watchers.py` - Add/remove watchers (implemented)
- `update_custom_fields.py` - Update custom fields (implemented)

**SKILL.md mentions but NOT implemented:**
- `update_comment.py` - Update existing comment
- `delete_comment.py` - Delete comment
- `download_attachment.py` - Download attachment

**JiraClient methods already exist:**
- `add_comment()` - Add comment to issue ✅
- `get_comments()` - Get all comments on issue ✅
- `get_comment()` - Get specific comment ✅
- `update_comment()` - Update comment ✅
- `delete_comment()` - Delete comment ✅

**Missing capabilities:**
- Comment visibility (internal vs external)
- Notification sending
- Activity stream/changelog parsing
- Version management
- Component CRUD

---

## JIRA API Reference

### Comment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rest/api/3/issue/{key}/comment` | Get all comments on issue |
| GET | `/rest/api/3/issue/{key}/comment/{id}` | Get specific comment |
| POST | `/rest/api/3/issue/{key}/comment` | Add comment (with optional visibility) |
| PUT | `/rest/api/3/issue/{key}/comment/{id}` | Update comment |
| DELETE | `/rest/api/3/issue/{key}/comment/{id}` | Delete comment |

### Comment with Visibility Request

```json
{
  "body": {
    "type": "doc",
    "version": 1,
    "content": [
      {
        "type": "paragraph",
        "content": [{"type": "text", "text": "Internal note"}]
      }
    ]
  },
  "visibility": {
    "type": "role",
    "value": "Administrators",
    "identifier": "Administrators"
  }
}
```

### Visibility Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `role` | Visible to project role | `value`: Role name (e.g., "Administrators") |
| `group` | Visible to group | `value`: Group name (e.g., "jira-developers") |

**Note:** Internal comments require JIRA Service Management for full "Customers" vs "Internal" distinction. Standard JIRA uses role-based visibility.

### Notification Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rest/api/3/issue/{key}/notify` | Send notification about issue |

### Notify Request

```json
{
  "subject": "Issue update notification",
  "textBody": "Please review this issue.",
  "htmlBody": "<p>Please review this issue.</p>",
  "to": {
    "reporter": true,
    "assignee": true,
    "watchers": true,
    "voters": false,
    "users": [{"accountId": "5b10a2844c20165700ede21g"}],
    "groups": [{"name": "developers"}]
  },
  "restrict": {
    "permissions": [{"key": "BROWSE"}],
    "groups": [{"name": "developers"}]
  }
}
```

### Changelog/Activity Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rest/api/3/issue/{key}/changelog` | Get issue changelog (paginated) |
| GET | `/rest/api/3/issue/{key}?expand=changelog` | Get issue with changelog |

### Changelog Response

```json
{
  "startAt": 0,
  "maxResults": 100,
  "total": 15,
  "isLast": true,
  "values": [
    {
      "id": "10001",
      "author": {
        "accountId": "5b10a2844c20165700ede21g",
        "displayName": "John Smith"
      },
      "created": "2025-01-15T10:30:00.000+0000",
      "items": [
        {
          "field": "status",
          "fieldtype": "jira",
          "fieldId": "status",
          "from": "10000",
          "fromString": "Open",
          "to": "10001",
          "toString": "In Progress"
        }
      ]
    }
  ]
}
```

### Version Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rest/api/3/version` | Create version |
| GET | `/rest/api/3/version/{id}` | Get version |
| PUT | `/rest/api/3/version/{id}` | Update version |
| DELETE | `/rest/api/3/version/{id}` | Delete version |
| GET | `/rest/api/3/project/{key}/versions` | Get project versions |
| POST | `/rest/api/3/version/{id}/move` | Reorder version |
| PUT | `/rest/api/3/version/{id}/mergeto/{targetId}` | Merge version |
| GET | `/rest/api/3/version/{id}/relatedIssueCounts` | Get issue counts |
| GET | `/rest/api/3/version/{id}/unresolvedIssueCount` | Get unresolved count |

### Create Version Request

```json
{
  "name": "v1.0.0",
  "description": "First release",
  "projectId": 10000,
  "startDate": "2025-01-01",
  "releaseDate": "2025-03-01",
  "released": false,
  "archived": false
}
```

### Version Response

```json
{
  "id": "10000",
  "name": "v1.0.0",
  "description": "First release",
  "projectId": 10000,
  "startDate": "2025-01-01",
  "releaseDate": "2025-03-01",
  "released": false,
  "archived": false,
  "self": "https://site.atlassian.net/rest/api/3/version/10000"
}
```

### Component Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rest/api/3/component` | Create component |
| GET | `/rest/api/3/component/{id}` | Get component |
| PUT | `/rest/api/3/component/{id}` | Update component |
| DELETE | `/rest/api/3/component/{id}` | Delete component |
| GET | `/rest/api/3/project/{key}/components` | Get project components |
| GET | `/rest/api/3/component/{id}/relatedIssueCounts` | Get issue counts |

### Create Component Request

```json
{
  "name": "Backend API",
  "description": "Server-side API components",
  "project": "PROJ",
  "leadAccountId": "5b10a2844c20165700ede21g",
  "assigneeType": "COMPONENT_LEAD"
}
```

### Assignee Types

| Value | Description |
|-------|-------------|
| `PROJECT_DEFAULT` | Use project default assignee |
| `COMPONENT_LEAD` | Assign to component lead |
| `PROJECT_LEAD` | Assign to project lead |
| `UNASSIGNED` | Leave unassigned |

---

## Test Infrastructure Setup

### Initial Setup Tasks

- [ ] **Setup 1.1:** Create test fixtures for comments
  - [ ] Create `.claude/skills/jira-collaborate/tests/conftest.py` (if not exists)
  - [ ] Add sample comment fixtures (with/without visibility)
  - [ ] Add sample changelog fixtures
  - [ ] Add notification request fixtures
  - **Commit:** `test(jira-collaborate): add comment and activity test fixtures`

- [ ] **Setup 1.2:** Create test fixtures for versions and components
  - [ ] Create `.claude/skills/jira-lifecycle/tests/conftest.py` (if not exists)
  - [ ] Add sample version fixtures
  - [ ] Add sample component fixtures
  - [ ] Add project fixtures for version/component context
  - **Commit:** `test(jira-lifecycle): add version and component test fixtures`

- [ ] **Setup 1.3:** Add JiraClient methods for new APIs
  - [ ] `add_comment_with_visibility()` - Add comment with role/group visibility
  - [ ] `get_changelog()` - Get issue changelog
  - [ ] `notify_issue()` - Send notification about issue
  - [ ] `create_version()` - Create project version
  - [ ] `get_version()` - Get version details
  - [ ] `update_version()` - Update version
  - [ ] `delete_version()` - Delete version
  - [ ] `get_project_versions()` - List project versions
  - [ ] `release_version()` - Mark version as released
  - [ ] `archive_version()` - Archive version
  - [ ] `create_component()` - Create component
  - [ ] `get_component()` - Get component details
  - [ ] `update_component()` - Update component
  - [ ] `delete_component()` - Delete component
  - [ ] `get_project_components()` - List project components
  - **Commit:** `feat(shared): add version, component, notification, and changelog API methods`

---

## Phase 1: Comment Enhancements

### Feature 1.1: Get Comments

**Script:** `get_comments.py`

**JIRA API:**
- `GET /rest/api/3/issue/{key}/comment`

**Test File:** `tests/test_get_comments.py`

**Test Cases:**
```python
def test_get_all_comments():
    """Test fetching all comments on an issue."""
    # Should return list of comments with author, body, created

def test_get_comments_with_pagination():
    """Test paginated comment retrieval."""
    # Should handle startAt and maxResults

def test_get_comments_order_by_created():
    """Test ordering comments by creation date."""
    # Default: newest first (-created)

def test_get_comments_empty():
    """Test handling issue with no comments."""
    # Should return empty list gracefully

def test_get_single_comment():
    """Test fetching a specific comment by ID."""
    # Should return single comment details

def test_format_text_output():
    """Test human-readable table output."""
    # Should show author, date, body preview

def test_format_json_output():
    """Test JSON output format."""
```

**CLI Interface:**
```bash
python get_comments.py PROJ-123
python get_comments.py PROJ-123 --id 10001
python get_comments.py PROJ-123 --limit 10
python get_comments.py PROJ-123 --order asc
python get_comments.py PROJ-123 --output json
```

**Output Example:**
```
Comments on PROJ-123 (3 total):

ID       Author            Date                  Body
───────  ────────────────  ────────────────────  ──────────────────────────────
10003    Alice Smith       2025-01-15 10:30 AM   Fixed the issue by updating...
10002    Bob Jones         2025-01-14 03:15 PM   I'll take a look at this...
10001    Alice Smith       2025-01-14 09:00 AM   Started investigating...
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Shows all comments with author/date/body
- [ ] Supports pagination
- [ ] Supports single comment fetch
- [ ] Text and JSON output

**Commits:**
1. `test(jira-collaborate): add failing tests for get_comments`
2. `feat(jira-collaborate): implement get_comments.py (7/7 tests passing)`

---

### Feature 1.2: Update Comment

**Script:** `update_comment.py`

**JIRA API:**
- `PUT /rest/api/3/issue/{key}/comment/{id}`

**Test File:** `tests/test_update_comment.py`

**Test Cases:**
```python
def test_update_comment_body():
    """Test updating comment body."""
    # Should update body, preserve other fields

def test_update_comment_with_markdown():
    """Test updating with markdown format."""
    # Should convert markdown to ADF

def test_update_comment_not_author():
    """Test error when not comment author."""
    # Should raise PermissionError

def test_update_comment_not_found():
    """Test error when comment doesn't exist."""
    # Should raise NotFoundError

def test_update_preserves_visibility():
    """Test that visibility is preserved on update."""
    # Internal comments stay internal
```

**CLI Interface:**
```bash
python update_comment.py PROJ-123 --id 10001 --body "Updated comment text"
python update_comment.py PROJ-123 --id 10001 --body "## New heading" --format markdown
```

**Output Example:**
```
Comment 10001 updated on PROJ-123.

Updated body:
  Updated comment text

Author: Alice Smith
Last modified: 2025-01-15 11:30 AM
```

**Acceptance Criteria:**
- [ ] All 5 tests pass
- [ ] Updates comment body
- [ ] Supports markdown format
- [ ] Preserves visibility
- [ ] Proper error handling

**Commits:**
1. `test(jira-collaborate): add failing tests for update_comment`
2. `feat(jira-collaborate): implement update_comment.py (5/5 tests passing)`

---

### Feature 1.3: Delete Comment

**Script:** `delete_comment.py`

**JIRA API:**
- `DELETE /rest/api/3/issue/{key}/comment/{id}`

**Test File:** `tests/test_delete_comment.py`

**Test Cases:**
```python
def test_delete_comment():
    """Test deleting a comment."""
    # Should delete successfully

def test_delete_comment_not_author():
    """Test error when not comment author."""
    # Should raise PermissionError

def test_delete_comment_not_found():
    """Test error when comment doesn't exist."""
    # Should raise NotFoundError

def test_delete_with_confirmation():
    """Test confirmation prompt."""
    # Should prompt before deletion

def test_delete_dry_run():
    """Test dry-run mode."""
    # Should show what would be deleted
```

**CLI Interface:**
```bash
python delete_comment.py PROJ-123 --id 10001
python delete_comment.py PROJ-123 --id 10001 --yes  # Skip confirmation
python delete_comment.py PROJ-123 --id 10001 --dry-run
```

**Output Example:**
```
Delete comment 10001 from PROJ-123?

Comment preview:
  Author: Alice Smith
  Date: 2025-01-14 09:00 AM
  Body: Started investigating the issue...

Type 'yes' to confirm: yes

Comment 10001 deleted from PROJ-123.
```

**Acceptance Criteria:**
- [ ] All 5 tests pass
- [ ] Deletes comment
- [ ] Confirmation prompt
- [ ] Dry-run mode
- [ ] Proper error handling

**Commits:**
1. `test(jira-collaborate): add failing tests for delete_comment`
2. `feat(jira-collaborate): implement delete_comment.py (5/5 tests passing)`

---

### Feature 1.4: Internal Comments (Visibility)

**Enhancement to:** `add_comment.py`

**JIRA API:**
- `POST /rest/api/3/issue/{key}/comment` with visibility field

**Test File:** `tests/test_comment_visibility.py`

**Test Cases:**
```python
def test_add_internal_comment_role():
    """Test adding comment visible only to a role."""
    # Should set visibility.type = "role"

def test_add_internal_comment_group():
    """Test adding comment visible only to a group."""
    # Should set visibility.type = "group"

def test_add_public_comment():
    """Test adding comment visible to all (default)."""
    # Should not include visibility field

def test_update_comment_preserve_visibility():
    """Test that updating preserves visibility."""
    # Internal comments stay internal

def test_get_comment_shows_visibility():
    """Test that visibility is shown in output."""
    # Should indicate if comment is restricted

def test_invalid_visibility_role():
    """Test error for invalid role name."""
    # Should raise ValidationError
```

**CLI Interface:**
```bash
# Add public comment (default)
python add_comment.py PROJ-123 --body "Public note"

# Add comment visible only to Administrators role
python add_comment.py PROJ-123 --body "Admin note" --visibility-role "Administrators"

# Add comment visible only to developers group
python add_comment.py PROJ-123 --body "Dev note" --visibility-group "jira-developers"
```

**Output Example:**
```
Added comment to PROJ-123 (ID: 10005)

Visibility: Administrators (role)

Note: This comment is only visible to users with the Administrators role.
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Add comments with role visibility
- [ ] Add comments with group visibility
- [ ] Show visibility in output
- [ ] Preserve visibility on update

**Commits:**
1. `test(jira-collaborate): add failing tests for comment visibility`
2. `feat(jira-collaborate): add visibility support to add_comment.py (6/6 tests passing)`

---

### Phase 1 Completion

- [ ] **Phase 1 Summary:**
  - [ ] 4 scripts (get_comments, update_comment, delete_comment, add_comment enhanced)
  - [ ] 23 tests passing
  - [ ] JiraClient methods verified/enhanced
  - **Commit:** `docs(jira-collaborate): complete Phase 1 - Comment Enhancements`

---

## Phase 2: Notifications & Activity

### Feature 2.1: Send Notification

**Script:** `send_notification.py`

**JIRA API:**
- `POST /rest/api/3/issue/{key}/notify`

**Test File:** `tests/test_send_notification.py`

**Test Cases:**
```python
def test_notify_watchers():
    """Test notifying all watchers."""
    # to.watchers = true

def test_notify_assignee():
    """Test notifying assignee."""
    # to.assignee = true

def test_notify_reporter():
    """Test notifying reporter."""
    # to.reporter = true

def test_notify_specific_users():
    """Test notifying specific users by account ID."""
    # to.users = [{accountId: ...}]

def test_notify_group():
    """Test notifying a group."""
    # to.groups = [{name: ...}]

def test_custom_subject_body():
    """Test custom notification subject and body."""
    # Should include subject and textBody/htmlBody

def test_notify_dry_run():
    """Test dry-run mode shows recipients."""
    # Should show who would be notified
```

**CLI Interface:**
```bash
# Notify watchers
python send_notification.py PROJ-123 --watchers

# Notify specific recipients
python send_notification.py PROJ-123 --assignee --reporter

# Notify with custom message
python send_notification.py PROJ-123 --watchers \
  --subject "Action Required" \
  --body "Please review this issue"

# Notify specific users
python send_notification.py PROJ-123 --user 5b10a2844c20165700ede21g

# Notify a group
python send_notification.py PROJ-123 --group developers

# Dry run
python send_notification.py PROJ-123 --watchers --dry-run
```

**Output Example:**
```
Notification sent for PROJ-123:

Subject: Action Required
Body: Please review this issue

Recipients:
  - Watchers: 3 users
  - Assignee: Alice Smith
  - Reporter: Bob Jones

Total notified: 5 users
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Notify watchers/assignee/reporter
- [ ] Notify specific users/groups
- [ ] Custom subject and body
- [ ] Dry-run mode

**Commits:**
1. `test(jira-collaborate): add failing tests for send_notification`
2. `feat(jira-collaborate): implement send_notification.py (7/7 tests passing)`

---

### Feature 2.2: Get Activity Stream (Changelog)

**Script:** `get_activity.py`

**JIRA API:**
- `GET /rest/api/3/issue/{key}/changelog`

**Test File:** `tests/test_get_activity.py`

**Test Cases:**
```python
def test_get_all_activity():
    """Test fetching all changelog entries."""
    # Should return list of changes

def test_get_activity_with_pagination():
    """Test paginated changelog retrieval."""
    # Should handle startAt and maxResults

def test_filter_by_field():
    """Test filtering changes by field name."""
    # e.g., --field status

def test_filter_by_user():
    """Test filtering changes by author."""
    # e.g., --user alice@example.com

def test_filter_by_date_range():
    """Test filtering by date range."""
    # e.g., --since 2025-01-01 --until 2025-01-15

def test_format_text_output():
    """Test human-readable timeline output."""
    # Should show who changed what when

def test_format_json_output():
    """Test JSON output format."""

def test_empty_changelog():
    """Test handling issue with no changes."""
    # Should return empty list gracefully
```

**CLI Interface:**
```bash
python get_activity.py PROJ-123
python get_activity.py PROJ-123 --field status
python get_activity.py PROJ-123 --user alice@example.com
python get_activity.py PROJ-123 --since 2025-01-01
python get_activity.py PROJ-123 --limit 20
python get_activity.py PROJ-123 --output json
```

**Output Example:**
```
Activity for PROJ-123 (15 changes):

Date                  Author          Field        From              To
────────────────────  ──────────────  ───────────  ────────────────  ────────────────
2025-01-15 10:30 AM   Alice Smith     status       In Progress       Done
2025-01-15 10:30 AM   Alice Smith     resolution   None              Fixed
2025-01-14 03:15 PM   Bob Jones       assignee     Unassigned        Alice Smith
2025-01-14 09:00 AM   Alice Smith     status       Open              In Progress
2025-01-14 09:00 AM   Alice Smith     Sprint       None              Sprint 42

Showing 5 of 15 changes. Use --limit to see more.
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Shows all changelog entries
- [ ] Filter by field, user, date
- [ ] Pagination support
- [ ] Text and JSON output

**Commits:**
1. `test(jira-collaborate): add failing tests for get_activity`
2. `feat(jira-collaborate): implement get_activity.py (8/8 tests passing)`

---

### Phase 2 Completion

- [ ] **Phase 2 Summary:**
  - [ ] 2 scripts (send_notification, get_activity)
  - [ ] 15 tests passing (38 total)
  - [ ] JiraClient methods added (2 methods)
  - **Commit:** `docs(jira-collaborate): complete Phase 2 - Notifications & Activity`

---

## Phase 3: Version Management

### Feature 3.1: Create Version

**Script:** `create_version.py`

**JIRA API:**
- `POST /rest/api/3/version`

**Test File:** `tests/test_create_version.py`

**Test Cases:**
```python
def test_create_version_minimal():
    """Test creating version with name only."""
    # Should use project from --project

def test_create_version_with_dates():
    """Test creating version with start/release dates."""
    # Should set startDate and releaseDate

def test_create_version_with_description():
    """Test creating version with description."""
    # Should set description

def test_create_version_duplicate_name():
    """Test error for duplicate version name in project."""
    # Should raise ValidationError

def test_create_version_invalid_project():
    """Test error for invalid project."""
    # Should raise NotFoundError

def test_create_version_output():
    """Test output shows created version details."""
    # Should show ID, name, dates
```

**CLI Interface:**
```bash
python create_version.py --project PROJ --name "v1.0.0"
python create_version.py --project PROJ --name "v1.0.0" \
  --description "First release" \
  --start-date 2025-01-01 \
  --release-date 2025-03-01
```

**Output Example:**
```
Version created successfully:

  ID:           10000
  Name:         v1.0.0
  Project:      PROJ
  Description:  First release
  Start Date:   2025-01-01
  Release Date: 2025-03-01
  Released:     No
  Archived:     No

To add issues to this version:
  python update_issue.py PROJ-123 --fix-version "v1.0.0"
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Creates version with all options
- [ ] Validates project exists
- [ ] Shows created version details

**Commits:**
1. `test(jira-lifecycle): add failing tests for create_version`
2. `feat(jira-lifecycle): implement create_version.py (6/6 tests passing)`

---

### Feature 3.2: Get Versions

**Script:** `get_versions.py`

**JIRA API:**
- `GET /rest/api/3/project/{key}/versions`
- `GET /rest/api/3/version/{id}`

**Test File:** `tests/test_get_versions.py`

**Test Cases:**
```python
def test_get_project_versions():
    """Test listing all versions in a project."""
    # Should return list of versions

def test_get_version_by_id():
    """Test getting specific version by ID."""
    # Should return version details

def test_filter_released():
    """Test filtering to released versions only."""
    # --released flag

def test_filter_unreleased():
    """Test filtering to unreleased versions only."""
    # --unreleased flag

def test_filter_archived():
    """Test filtering to archived versions."""
    # --archived flag

def test_get_version_with_issue_counts():
    """Test including issue counts in output."""
    # Should show fixed/affected issue counts

def test_format_text_output():
    """Test table output with version details."""

def test_format_json_output():
    """Test JSON output format."""
```

**CLI Interface:**
```bash
python get_versions.py --project PROJ
python get_versions.py --id 10000
python get_versions.py --project PROJ --released
python get_versions.py --project PROJ --unreleased
python get_versions.py --project PROJ --with-counts
python get_versions.py --project PROJ --output json
```

**Output Example:**
```
Versions in PROJ (5 total):

ID       Name       Status      Start Date    Release Date   Issues
───────  ─────────  ──────────  ────────────  ─────────────  ────────
10004    v1.2.0     Unreleased  2025-03-01    2025-06-01     12 fixed
10003    v1.1.0     Released    2025-01-15    2025-02-15     45 fixed
10002    v1.0.1     Released    2025-01-01    2025-01-10     8 fixed
10001    v1.0.0     Released    2024-10-01    2025-01-01     120 fixed
10000    v0.9.0     Archived    2024-07-01    2024-09-30     85 fixed
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Lists project versions
- [ ] Gets single version
- [ ] Filter by status
- [ ] Show issue counts

**Commits:**
1. `test(jira-lifecycle): add failing tests for get_versions`
2. `feat(jira-lifecycle): implement get_versions.py (8/8 tests passing)`

---

### Feature 3.3: Release Version

**Script:** `release_version.py`

**JIRA API:**
- `PUT /rest/api/3/version/{id}` with `released: true`

**Test File:** `tests/test_release_version.py`

**Test Cases:**
```python
def test_release_version():
    """Test marking version as released."""
    # Should set released = true

def test_release_with_date():
    """Test setting release date on release."""
    # Should update releaseDate

def test_release_already_released():
    """Test error when version already released."""
    # Should warn or skip

def test_release_with_unresolved_issues():
    """Test warning when unresolved issues exist."""
    # Should warn but allow

def test_unrelease_version():
    """Test un-releasing a version."""
    # Should set released = false

def test_release_dry_run():
    """Test dry-run mode."""
    # Should show what would change
```

**CLI Interface:**
```bash
python release_version.py --id 10000
python release_version.py --id 10000 --date 2025-01-15
python release_version.py --project PROJ --name "v1.0.0"
python release_version.py --id 10000 --unrelease
python release_version.py --id 10000 --dry-run
```

**Output Example:**
```
Releasing version v1.0.0...

Warning: 3 unresolved issues in this version:
  - PROJ-45: Fix login bug (In Progress)
  - PROJ-67: Update documentation (Open)
  - PROJ-89: Add tests (Open)

Continue anyway? [y/N]: y

Version v1.0.0 released!

  Release Date: 2025-01-15
  Fixed Issues: 45
  Unresolved:   3

Generate release notes: python generate_release_notes.py --version 10000
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Releases version
- [ ] Warns about unresolved issues
- [ ] Supports un-release
- [ ] Dry-run mode

**Commits:**
1. `test(jira-lifecycle): add failing tests for release_version`
2. `feat(jira-lifecycle): implement release_version.py (6/6 tests passing)`

---

### Feature 3.4: Archive Version

**Script:** `archive_version.py`

**JIRA API:**
- `PUT /rest/api/3/version/{id}` with `archived: true`

**Test File:** `tests/test_archive_version.py`

**Test Cases:**
```python
def test_archive_version():
    """Test archiving a version."""
    # Should set archived = true

def test_unarchive_version():
    """Test un-archiving a version."""
    # Should set archived = false

def test_archive_unreleased():
    """Test warning when archiving unreleased version."""
    # Should warn but allow

def test_archive_dry_run():
    """Test dry-run mode."""
    # Should show what would change
```

**CLI Interface:**
```bash
python archive_version.py --id 10000
python archive_version.py --project PROJ --name "v0.9.0"
python archive_version.py --id 10000 --unarchive
python archive_version.py --id 10000 --dry-run
```

**Output Example:**
```
Version v0.9.0 archived.

This version is now hidden from the version picker.
To unarchive: python archive_version.py --id 10000 --unarchive
```

**Acceptance Criteria:**
- [ ] All 4 tests pass
- [ ] Archives version
- [ ] Supports un-archive
- [ ] Dry-run mode

**Commits:**
1. `test(jira-lifecycle): add failing tests for archive_version`
2. `feat(jira-lifecycle): implement archive_version.py (4/4 tests passing)`

---

### Feature 3.5: Move Issues Between Versions

**Script:** `move_issues_version.py`

**JIRA API:**
- Bulk update issues' `fixVersion` field
- `PUT /rest/api/3/issue/{key}` with fields.fixVersions

**Test File:** `tests/test_move_issues_version.py`

**Test Cases:**
```python
def test_move_issues_to_version():
    """Test moving issues to a new version."""
    # Should update fixVersion on all issues

def test_move_from_version():
    """Test moving all issues from one version to another."""
    # Should find issues by JQL and update

def test_move_specific_issues():
    """Test moving specific issue keys."""
    # Should update only specified issues

def test_replace_version():
    """Test replacing version (remove old, add new)."""
    # Default behavior

def test_add_version():
    """Test adding version without removing existing."""
    # --add flag

def test_dry_run():
    """Test dry-run shows affected issues."""
    # Should list issues without modifying
```

**CLI Interface:**
```bash
# Move specific issues
python move_issues_version.py --issues PROJ-1,PROJ-2,PROJ-3 --to-version "v1.1.0"

# Move all issues from one version to another
python move_issues_version.py --from-version "v1.0.0" --to-version "v1.1.0"

# Move by JQL
python move_issues_version.py --jql "project = PROJ AND status = Open" --to-version "v1.1.0"

# Add version (keep existing)
python move_issues_version.py --issues PROJ-1 --to-version "v1.1.0" --add

# Dry run
python move_issues_version.py --from-version "v1.0.0" --to-version "v1.1.0" --dry-run
```

**Output Example:**
```
Moving issues from v1.0.0 to v1.1.0...

Issues to move (12):
  PROJ-45: Fix login bug
  PROJ-67: Update documentation
  ...

Proceed? [y/N]: y

Moved 12 issues to v1.1.0.
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Moves specific issues
- [ ] Moves issues by JQL
- [ ] Replace or add version
- [ ] Dry-run mode

**Commits:**
1. `test(jira-lifecycle): add failing tests for move_issues_version`
2. `feat(jira-lifecycle): implement move_issues_version.py (6/6 tests passing)`

---

### Phase 3 Completion

- [ ] **Phase 3 Summary:**
  - [ ] 5 scripts (create_version, get_versions, release_version, archive_version, move_issues_version)
  - [ ] 30 tests passing (68 total)
  - [ ] JiraClient methods added (8 methods)
  - **Commit:** `docs(jira-lifecycle): complete Phase 3 - Version Management`

---

## Phase 4: Component CRUD

### Feature 4.1: Create Component

**Script:** `create_component.py`

**JIRA API:**
- `POST /rest/api/3/component`

**Test File:** `tests/test_create_component.py`

**Test Cases:**
```python
def test_create_component_minimal():
    """Test creating component with name only."""
    # Should use project from --project

def test_create_component_with_lead():
    """Test creating component with lead."""
    # Should set leadAccountId

def test_create_component_with_description():
    """Test creating component with description."""
    # Should set description

def test_create_component_with_assignee_type():
    """Test setting component assignee type."""
    # COMPONENT_LEAD, PROJECT_LEAD, etc.

def test_create_component_duplicate_name():
    """Test error for duplicate component name."""
    # Should raise ValidationError

def test_create_component_output():
    """Test output shows created component details."""
```

**CLI Interface:**
```bash
python create_component.py --project PROJ --name "Backend API"
python create_component.py --project PROJ --name "Backend API" \
  --description "Server-side API components" \
  --lead alice@example.com \
  --assignee-type COMPONENT_LEAD
```

**Output Example:**
```
Component created successfully:

  ID:            10000
  Name:          Backend API
  Project:       PROJ
  Description:   Server-side API components
  Lead:          Alice Smith
  Assignee Type: COMPONENT_LEAD

To add issues to this component:
  python update_issue.py PROJ-123 --components "Backend API"
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Creates component with all options
- [ ] Sets lead and assignee type
- [ ] Shows created component details

**Commits:**
1. `test(jira-lifecycle): add failing tests for create_component`
2. `feat(jira-lifecycle): implement create_component.py (6/6 tests passing)`

---

### Feature 4.2: Get Components

**Script:** `get_components.py`

**JIRA API:**
- `GET /rest/api/3/project/{key}/components`
- `GET /rest/api/3/component/{id}`

**Test File:** `tests/test_get_components.py`

**Test Cases:**
```python
def test_get_project_components():
    """Test listing all components in a project."""
    # Should return list of components

def test_get_component_by_id():
    """Test getting specific component by ID."""
    # Should return component details

def test_get_component_with_issue_counts():
    """Test including issue counts in output."""
    # Should show issues using this component

def test_empty_components():
    """Test handling project with no components."""
    # Should return empty list

def test_format_text_output():
    """Test table output with component details."""

def test_format_json_output():
    """Test JSON output format."""
```

**CLI Interface:**
```bash
python get_components.py --project PROJ
python get_components.py --id 10000
python get_components.py --project PROJ --with-counts
python get_components.py --project PROJ --output json
```

**Output Example:**
```
Components in PROJ (4 total):

ID       Name          Lead            Assignee Type    Issues
───────  ────────────  ──────────────  ───────────────  ────────
10003    UI/Frontend   Carol Lee       COMPONENT_LEAD   45
10002    Backend API   Alice Smith     COMPONENT_LEAD   78
10001    Database      Bob Jones       PROJECT_DEFAULT  23
10000    Infra         Unassigned      UNASSIGNED       12
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Lists project components
- [ ] Gets single component
- [ ] Show issue counts

**Commits:**
1. `test(jira-lifecycle): add failing tests for get_components`
2. `feat(jira-lifecycle): implement get_components.py (6/6 tests passing)`

---

### Feature 4.3: Update Component

**Script:** `update_component.py`

**JIRA API:**
- `PUT /rest/api/3/component/{id}`

**Test File:** `tests/test_update_component.py`

**Test Cases:**
```python
def test_update_component_name():
    """Test updating component name."""

def test_update_component_lead():
    """Test updating component lead."""

def test_update_component_description():
    """Test updating component description."""

def test_update_component_assignee_type():
    """Test updating assignee type."""

def test_update_component_not_found():
    """Test error when component doesn't exist."""

def test_update_multiple_fields():
    """Test updating multiple fields at once."""
```

**CLI Interface:**
```bash
python update_component.py --id 10000 --name "New Name"
python update_component.py --id 10000 --lead bob@example.com
python update_component.py --id 10000 --description "Updated description"
python update_component.py --id 10000 --assignee-type PROJECT_LEAD
```

**Output Example:**
```
Component updated successfully:

  ID:            10000
  Name:          New Name (was: Backend API)
  Lead:          Bob Jones (was: Alice Smith)

Changes: name, lead
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Updates individual fields
- [ ] Updates multiple fields
- [ ] Shows what changed

**Commits:**
1. `test(jira-lifecycle): add failing tests for update_component`
2. `feat(jira-lifecycle): implement update_component.py (6/6 tests passing)`

---

### Feature 4.4: Delete Component

**Script:** `delete_component.py`

**JIRA API:**
- `DELETE /rest/api/3/component/{id}`

**Test File:** `tests/test_delete_component.py`

**Test Cases:**
```python
def test_delete_component():
    """Test deleting a component."""

def test_delete_component_with_issues():
    """Test warning when component has issues."""
    # Should warn but allow (issues will have component removed)

def test_delete_component_not_found():
    """Test error when component doesn't exist."""

def test_delete_with_move_issues():
    """Test moving issues to another component on delete."""
    # --move-issues-to flag

def test_delete_with_confirmation():
    """Test confirmation prompt."""

def test_delete_dry_run():
    """Test dry-run mode."""
```

**CLI Interface:**
```bash
python delete_component.py --id 10000
python delete_component.py --id 10000 --yes  # Skip confirmation
python delete_component.py --id 10000 --move-issues-to 10001
python delete_component.py --id 10000 --dry-run
```

**Output Example:**
```
Delete component "Backend API"?

Warning: 78 issues use this component.
Issues will have this component removed after deletion.

To move issues to another component:
  python delete_component.py --id 10000 --move-issues-to 10001

Type 'yes' to confirm: yes

Component "Backend API" deleted.
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Deletes component
- [ ] Warns about issues
- [ ] Option to move issues
- [ ] Confirmation and dry-run

**Commits:**
1. `test(jira-lifecycle): add failing tests for delete_component`
2. `feat(jira-lifecycle): implement delete_component.py (6/6 tests passing)`

---

### Phase 4 Completion

- [ ] **Phase 4 Summary:**
  - [ ] 4 scripts (create_component, get_components, update_component, delete_component)
  - [ ] 24 tests passing (92 total)
  - [ ] JiraClient methods added (5 methods)
  - **Commit:** `docs(jira-lifecycle): complete Phase 4 - Component CRUD`

---

## Integration & Documentation

### Integration Tasks

- [ ] **Integration 1:** Update jira-collaborate SKILL.md
  - [ ] Add get_comments, update_comment, delete_comment
  - [ ] Add visibility (internal comments) documentation
  - [ ] Add send_notification examples
  - [ ] Add get_activity examples
  - **Commit:** `docs(jira-collaborate): update SKILL.md with new features`

- [ ] **Integration 2:** Update jira-lifecycle SKILL.md
  - [ ] Add version management section
  - [ ] Add component CRUD section
  - [ ] Add examples for all new scripts
  - **Commit:** `docs(jira-lifecycle): update SKILL.md with version and component features`

- [ ] **Integration 3:** Update CLAUDE.md
  - [ ] Add collaboration enhancements to overview
  - [ ] Add version/component patterns
  - **Commit:** `docs: update CLAUDE.md with collaboration and versioning features`

- [ ] **Integration 4:** Update GAP_ANALYSIS.md
  - [ ] Mark Collaboration Enhancements as completed (80%+)
  - [ ] Mark Versions & Releases as completed (100%)
  - [ ] Mark Components as completed (100%)
  - **Commit:** `docs: update GAP_ANALYSIS.md - Collaboration & Versioning complete`

### Live Integration Tests

- [ ] **Quality 1:** Add live integration tests
  - [ ] `test_comments.py`: CRUD, visibility
  - [ ] `test_notifications.py`: Send notifications
  - [ ] `test_activity.py`: Get changelog
  - [ ] `test_versions.py`: CRUD, release, archive
  - [ ] `test_components.py`: CRUD
  - **Commit:** `test(shared): add live integration tests for collaboration and versioning`

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 92+ unit tests passing
- [ ] Live integration tests for all features
- [ ] Coverage ≥ 85% for new code

**Scripts:**
- [ ] 15 new scripts implemented
- [ ] All scripts have `--help`
- [ ] All scripts support `--profile`
- [ ] Mutation scripts have `--dry-run`

**Documentation:**
- [ ] SKILL.md files updated
- [ ] CLAUDE.md updated
- [ ] GAP_ANALYSIS.md updated
- [ ] All scripts have docstrings

### Progress Tracking

**Phase Status:**
- [ ] Phase 1: Comment Enhancements (4 scripts, 23 tests)
- [ ] Phase 2: Notifications & Activity (2 scripts, 15 tests)
- [ ] Phase 3: Version Management (5 scripts, 30 tests)
- [ ] Phase 4: Component CRUD (4 scripts, 24 tests)
- [ ] Integration & Documentation

---

## Script Summary

| Script | Skill | Phase | Tests | Description |
|--------|-------|-------|-------|-------------|
| `get_comments.py` | jira-collaborate | 1 | 7 | List/view comments |
| `update_comment.py` | jira-collaborate | 1 | 5 | Update existing comment |
| `delete_comment.py` | jira-collaborate | 1 | 5 | Delete comment |
| `add_comment.py` | jira-collaborate | 1 | 6 | Enhanced with visibility |
| `send_notification.py` | jira-collaborate | 2 | 7 | Send issue notification |
| `get_activity.py` | jira-collaborate | 2 | 8 | View issue changelog |
| `create_version.py` | jira-lifecycle | 3 | 6 | Create project version |
| `get_versions.py` | jira-lifecycle | 3 | 8 | List/view versions |
| `release_version.py` | jira-lifecycle | 3 | 6 | Release/unrelease version |
| `archive_version.py` | jira-lifecycle | 3 | 4 | Archive/unarchive version |
| `move_issues_version.py` | jira-lifecycle | 3 | 6 | Move issues between versions |
| `create_component.py` | jira-lifecycle | 4 | 6 | Create component |
| `get_components.py` | jira-lifecycle | 4 | 6 | List/view components |
| `update_component.py` | jira-lifecycle | 4 | 6 | Update component |
| `delete_component.py` | jira-lifecycle | 4 | 6 | Delete component |
| **Total** | - | - | **92** | - |

---

## JiraClient Methods to Add

```python
# In shared/scripts/lib/jira_client.py

# ========== Comment Visibility ==========

def add_comment_with_visibility(self, issue_key: str, body: Dict[str, Any],
                                visibility_type: str = None,
                                visibility_value: str = None) -> Dict[str, Any]:
    """
    Add a comment with visibility restrictions.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        body: Comment body in ADF format
        visibility_type: 'role' or 'group' (None for public)
        visibility_value: Role or group name

    Returns:
        Created comment object
    """
    data = {'body': body}
    if visibility_type and visibility_value:
        data['visibility'] = {
            'type': visibility_type,
            'value': visibility_value,
            'identifier': visibility_value
        }
    return self.post(f'/rest/api/3/issue/{issue_key}/comment',
                    data=data, operation=f"add comment to {issue_key}")

# ========== Changelog ==========

def get_changelog(self, issue_key: str, start_at: int = 0,
                  max_results: int = 100) -> Dict[str, Any]:
    """
    Get issue changelog (activity history).

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        start_at: Starting index for pagination
        max_results: Maximum results per page

    Returns:
        Changelog with values array of change entries
    """
    params = {'startAt': start_at, 'maxResults': max_results}
    return self.get(f'/rest/api/3/issue/{issue_key}/changelog',
                   params=params,
                   operation=f"get changelog for {issue_key}")

# ========== Notifications ==========

def notify_issue(self, issue_key: str, subject: str = None,
                 text_body: str = None, html_body: str = None,
                 to: Dict[str, Any] = None,
                 restrict: Dict[str, Any] = None) -> None:
    """
    Send notification about an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        subject: Notification subject
        text_body: Plain text body
        html_body: HTML body
        to: Recipients dict (reporter, assignee, watchers, voters, users, groups)
        restrict: Restriction dict (permissions, groups)
    """
    data = {}
    if subject:
        data['subject'] = subject
    if text_body:
        data['textBody'] = text_body
    if html_body:
        data['htmlBody'] = html_body
    if to:
        data['to'] = to
    if restrict:
        data['restrict'] = restrict

    self.post(f'/rest/api/3/issue/{issue_key}/notify',
             data=data, operation=f"notify about {issue_key}")

# ========== Version Management ==========

def create_version(self, project_id: int, name: str,
                   description: str = None,
                   start_date: str = None,
                   release_date: str = None,
                   released: bool = False,
                   archived: bool = False) -> Dict[str, Any]:
    """
    Create a new project version.

    Args:
        project_id: Project ID (numeric)
        name: Version name (e.g., 'v1.0.0')
        description: Version description
        start_date: Start date (YYYY-MM-DD)
        release_date: Release date (YYYY-MM-DD)
        released: Whether version is released
        archived: Whether version is archived

    Returns:
        Created version object
    """
    data = {
        'projectId': project_id,
        'name': name,
        'released': released,
        'archived': archived
    }
    if description:
        data['description'] = description
    if start_date:
        data['startDate'] = start_date
    if release_date:
        data['releaseDate'] = release_date

    return self.post('/rest/api/3/version', data=data,
                    operation=f"create version '{name}'")

def get_version(self, version_id: str, expand: str = None) -> Dict[str, Any]:
    """
    Get a version by ID.

    Args:
        version_id: Version ID
        expand: Optional expansions (e.g., 'issueStatusCounts')

    Returns:
        Version object
    """
    params = {}
    if expand:
        params['expand'] = expand
    return self.get(f'/rest/api/3/version/{version_id}',
                   params=params if params else None,
                   operation=f"get version {version_id}")

def update_version(self, version_id: str, **kwargs) -> Dict[str, Any]:
    """
    Update a version.

    Args:
        version_id: Version ID
        **kwargs: Fields to update (name, description, released, archived,
                  startDate, releaseDate)

    Returns:
        Updated version object
    """
    data = {}
    field_mapping = {
        'name': 'name',
        'description': 'description',
        'released': 'released',
        'archived': 'archived',
        'start_date': 'startDate',
        'release_date': 'releaseDate'
    }
    for key, api_key in field_mapping.items():
        if key in kwargs and kwargs[key] is not None:
            data[api_key] = kwargs[key]

    return self.put(f'/rest/api/3/version/{version_id}',
                   data=data,
                   operation=f"update version {version_id}")

def delete_version(self, version_id: str,
                   move_fixed_to: str = None,
                   move_affected_to: str = None) -> None:
    """
    Delete a version.

    Args:
        version_id: Version ID
        move_fixed_to: Version ID to move fixVersion issues to
        move_affected_to: Version ID to move affectedVersion issues to
    """
    params = {}
    if move_fixed_to:
        params['moveFixIssuesTo'] = move_fixed_to
    if move_affected_to:
        params['moveAffectedIssuesTo'] = move_affected_to

    endpoint = f'/rest/api/3/version/{version_id}'
    url = f"{self.base_url}{endpoint}"
    response = self.session.delete(url, params=params if params else None,
                                  timeout=self.timeout)
    handle_jira_error(response, f"delete version {version_id}")

def get_project_versions(self, project_key: str,
                         expand: str = None) -> list:
    """
    Get all versions for a project.

    Args:
        project_key: Project key (e.g., 'PROJ')
        expand: Optional expansions

    Returns:
        List of version objects
    """
    params = {}
    if expand:
        params['expand'] = expand
    return self.get(f'/rest/api/3/project/{project_key}/versions',
                   params=params if params else None,
                   operation=f"get versions for project {project_key}")

def get_version_issue_counts(self, version_id: str) -> Dict[str, Any]:
    """
    Get issue counts for a version.

    Args:
        version_id: Version ID

    Returns:
        Issue counts (issuesFixedCount, issuesAffectedCount)
    """
    return self.get(f'/rest/api/3/version/{version_id}/relatedIssueCounts',
                   operation=f"get issue counts for version {version_id}")

def get_version_unresolved_count(self, version_id: str) -> Dict[str, Any]:
    """
    Get unresolved issue count for a version.

    Args:
        version_id: Version ID

    Returns:
        Unresolved count data
    """
    return self.get(f'/rest/api/3/version/{version_id}/unresolvedIssueCount',
                   operation=f"get unresolved count for version {version_id}")

# ========== Component Management ==========

def create_component(self, project: str, name: str,
                     description: str = None,
                     lead_account_id: str = None,
                     assignee_type: str = 'PROJECT_DEFAULT') -> Dict[str, Any]:
    """
    Create a new component.

    Args:
        project: Project key (e.g., 'PROJ')
        name: Component name
        description: Component description
        lead_account_id: Account ID of component lead
        assignee_type: 'PROJECT_DEFAULT', 'COMPONENT_LEAD', 'PROJECT_LEAD', 'UNASSIGNED'

    Returns:
        Created component object
    """
    data = {
        'project': project,
        'name': name,
        'assigneeType': assignee_type
    }
    if description:
        data['description'] = description
    if lead_account_id:
        data['leadAccountId'] = lead_account_id

    return self.post('/rest/api/3/component', data=data,
                    operation=f"create component '{name}'")

def get_component(self, component_id: str) -> Dict[str, Any]:
    """
    Get a component by ID.

    Args:
        component_id: Component ID

    Returns:
        Component object
    """
    return self.get(f'/rest/api/3/component/{component_id}',
                   operation=f"get component {component_id}")

def update_component(self, component_id: str, **kwargs) -> Dict[str, Any]:
    """
    Update a component.

    Args:
        component_id: Component ID
        **kwargs: Fields to update (name, description, leadAccountId, assigneeType)

    Returns:
        Updated component object
    """
    data = {}
    field_mapping = {
        'name': 'name',
        'description': 'description',
        'lead_account_id': 'leadAccountId',
        'assignee_type': 'assigneeType'
    }
    for key, api_key in field_mapping.items():
        if key in kwargs and kwargs[key] is not None:
            data[api_key] = kwargs[key]

    return self.put(f'/rest/api/3/component/{component_id}',
                   data=data,
                   operation=f"update component {component_id}")

def delete_component(self, component_id: str,
                     move_issues_to: str = None) -> None:
    """
    Delete a component.

    Args:
        component_id: Component ID
        move_issues_to: Component ID to move issues to
    """
    params = {}
    if move_issues_to:
        params['moveIssuesTo'] = move_issues_to

    endpoint = f'/rest/api/3/component/{component_id}'
    url = f"{self.base_url}{endpoint}"
    response = self.session.delete(url, params=params if params else None,
                                  timeout=self.timeout)
    handle_jira_error(response, f"delete component {component_id}")

def get_project_components(self, project_key: str) -> list:
    """
    Get all components for a project.

    Args:
        project_key: Project key (e.g., 'PROJ')

    Returns:
        List of component objects
    """
    return self.get(f'/rest/api/3/project/{project_key}/components',
                   operation=f"get components for project {project_key}")

def get_component_issue_counts(self, component_id: str) -> Dict[str, Any]:
    """
    Get issue counts for a component.

    Args:
        component_id: Component ID

    Returns:
        Issue count data
    """
    return self.get(f'/rest/api/3/component/{component_id}/relatedIssueCounts',
                   operation=f"get issue counts for component {component_id}")
```

---

## Known Limitations

### Internal Comments
- Full internal vs external comment distinction requires JIRA Service Management
- Standard JIRA Cloud uses role/group visibility instead
- Visibility cannot be changed after comment creation

### Notifications
- Rate limits may apply to notification API
- User notification preferences may override API calls
- HTML body rendering depends on email client

### Version Management
- Versions are project-specific
- Deleting versions with issues may affect reporting
- Archived versions are hidden but not deleted

### Component Management
- Components are project-specific
- Deleting components removes them from issues
- Component lead changes don't auto-reassign issues

---

## API Sources

- [Issue Comments API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/)
- [Issue Changelog API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-changelog-get)
- [Issue Notification API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-notify-post)
- [Project Versions API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-project-versions/)
- [Project Components API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-project-components/)

---

**Plan Version:** 1.0
**Created:** 2025-12-25
**Status:** READY FOR IMPLEMENTATION

### Estimated Scope

| Metric | Estimate |
|--------|----------|
| Unit Tests | 92 |
| Scripts | 15 |
| JiraClient Methods | ~20 |
| Skills Affected | 2 (jira-collaborate, jira-lifecycle) |
