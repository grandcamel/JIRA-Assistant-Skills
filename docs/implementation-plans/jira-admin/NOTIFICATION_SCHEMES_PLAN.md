# Notification Schemes - TDD Implementation Plan

## Implementation Status

**Overall Status:** NOT STARTED

**Planned Scripts:** 6 core scripts
**Test Coverage Target:** 85%+
**Estimated Effort:** 20-25 hours over 2 weeks

---

## Overview

**Objective:** Implement comprehensive JIRA notification scheme management functionality using Test-Driven Development (TDD) for the jira-admin skill.

**What are Notification Schemes?**
Notification schemes define who receives email notifications when specific events occur on JIRA issues. They map events (issue created, assigned, commented, etc.) to recipients (assignees, reporters, watchers, groups, etc.).

**Key Concepts:**
- **Events:** System-defined or custom triggers (e.g., "Issue Created", "Issue Assigned")
- **Recipients:** Notification targets (current assignee, reporter, watchers, groups, project roles, users)
- **Scheme:** Collection of event-to-recipient mappings
- **Project Association:** Each project uses one notification scheme

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
1. **Phase 1: List Notification Schemes** (Discovery)
2. **Phase 2: Get Notification Scheme Details** (Inspect events and recipients)
3. **Phase 3: Create Notification Scheme** (New scheme creation)
4. **Phase 4: Update Notification Scheme** (Modify existing schemes)
5. **Phase 5: Add Notification to Scheme** (Add event-recipient mappings)
6. **Phase 6: Delete Operations** (Remove notifications and schemes)

---

## JIRA API Reference

### Endpoints

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| GET | `/rest/api/3/notificationscheme` | List all notification schemes | **Critical** |
| GET | `/rest/api/3/notificationscheme/{id}` | Get notification scheme details | **Critical** |
| GET | `/rest/api/3/notificationscheme/project` | Get project-to-scheme mappings | High |
| POST | `/rest/api/3/notificationscheme` | Create notification scheme | High |
| PUT | `/rest/api/3/notificationscheme/{id}` | Update notification scheme | High |
| PUT | `/rest/api/3/notificationscheme/{id}/notification` | Add notifications to scheme | High |
| DELETE | `/rest/api/3/notificationscheme/{schemeId}` | Delete notification scheme | Medium |
| DELETE | `/rest/api/3/notificationscheme/{schemeId}/notification/{notificationId}` | Remove notification from scheme | Medium |

### Notification Scheme Structure

```json
{
  "id": "10000",
  "self": "https://site.atlassian.net/rest/api/3/notificationscheme/10000",
  "name": "Default Notification Scheme",
  "description": "Standard notification setup for most projects",
  "notificationSchemeEvents": [
    {
      "event": {
        "id": "1",
        "name": "Issue created",
        "description": "This event is fired when an issue is created"
      },
      "notifications": [
        {
          "id": "10",
          "notificationType": "CurrentAssignee",
          "parameter": null
        },
        {
          "id": "11",
          "notificationType": "Reporter",
          "parameter": null
        },
        {
          "id": "12",
          "notificationType": "Group",
          "parameter": "jira-administrators"
        }
      ]
    },
    {
      "event": {
        "id": "2",
        "name": "Issue updated",
        "description": "This event is fired when an issue is updated"
      },
      "notifications": [
        {
          "id": "13",
          "notificationType": "CurrentAssignee",
          "parameter": null
        },
        {
          "id": "14",
          "notificationType": "AllWatchers",
          "parameter": null
        }
      ]
    }
  ]
}
```

### Create Notification Scheme Request

```json
{
  "name": "New Project Notification Scheme",
  "description": "Custom notifications for development team",
  "notificationSchemeEvents": [
    {
      "event": {
        "id": "1"
      },
      "notifications": [
        {
          "notificationType": "Group",
          "parameter": "developers"
        },
        {
          "notificationType": "CurrentAssignee"
        },
        {
          "notificationType": "Reporter"
        }
      ]
    }
  ]
}
```

### Update Notification Scheme Request (Add Notifications)

```json
{
  "notificationSchemeEvents": [
    {
      "event": {
        "id": "1"
      },
      "notifications": [
        {
          "notificationType": "Group",
          "parameter": "jira-administrators"
        }
      ]
    }
  ]
}
```

### Project-to-Scheme Mapping Response

```json
{
  "values": [
    {
      "projectId": "10000",
      "notificationSchemeId": "10000"
    },
    {
      "projectId": "10001",
      "notificationSchemeId": "10001"
    }
  ]
}
```

---

## Notification Event Types Reference

### Core System Events

| Event ID | Event Name | Description |
|----------|------------|-------------|
| 1 | Issue created | A work item has been entered into the system |
| 2 | Issue updated | A work item has had its details changed |
| 3 | Issue assigned | A work item has been assigned to a new user |
| 4 | Issue resolved | A work item has been resolved |
| 5 | Issue closed | A work item has been closed |
| 6 | Issue commented | A work item has had a comment added to it |
| 7 | Issue reopened | A work item has been re-opened |
| 8 | Issue deleted | A work item has been deleted |
| 9 | Issue moved | A work item has been moved to a different project |
| 10 | Work logged | Hours logged against a work item |
| 11 | Work started | The assignee has started working on a work item |
| 12 | Work stopped | The assignee has stopped working on a work item |
| 13 | Generic event | Generic event type |
| 14 | Issue comment edited | A work item's comment has been modified |
| 15 | Issue worklog updated | An entry in a work item's worklog has been modified |
| 16 | Issue worklog deleted | An entry in a work item's worklog has been deleted |

**Note:** Event IDs may vary by JIRA instance. Use event names for reliability.

### Event Type Categories

**System Events:**
- Predefined by JIRA
- Cannot be deleted
- Can be made inactive
- Used throughout JIRA internally

**Custom Events:**
- Created by administrators
- Used for workflow-specific notifications
- Fired from workflow transition post-functions

---

## Notification Recipient Types

| Type | Parameter | Description |
|------|-----------|-------------|
| `CurrentAssignee` | null | Person currently assigned to the issue |
| `Reporter` | null | Person who created the issue |
| `CurrentUser` | null | Person performing the action |
| `ProjectLead` | null | Project lead |
| `ComponentLead` | null | Lead of the affected component |
| `User` | User account ID | Specific user |
| `Group` | Group name | All members of a group |
| `ProjectRole` | Project role ID | All users with a specific project role |
| `EmailAddress` | Email address | Specific email address (deprecated) |
| `AllWatchers` | null | All users watching the issue |
| `UserCustomField` | Custom field ID | User from a custom field |
| `GroupCustomField` | Custom field ID | Group from a custom field |

**Examples:**
```json
// Current assignee (no parameter)
{"notificationType": "CurrentAssignee"}

// Specific group
{"notificationType": "Group", "parameter": "jira-administrators"}

// Specific user
{"notificationType": "User", "parameter": "5b10ac8d82e05b22cc7d4ef5"}

// Project role
{"notificationType": "ProjectRole", "parameter": "10002"}

// All watchers
{"notificationType": "AllWatchers"}
```

---

## Test Infrastructure Setup

### Initial Setup Tasks

- [ ] **Setup 1.1:** Create skill structure
  - [ ] Create `.claude/skills/jira-admin/` directory
  - [ ] Create `scripts/` subdirectory
  - [ ] Create `tests/` subdirectory
  - [ ] Create `references/` subdirectory
  - [ ] Create `SKILL.md` skeleton
  - **Commit:** `feat(jira-admin): create skill structure`

- [ ] **Setup 1.2:** Create test infrastructure
  - [ ] Create `tests/conftest.py` with shared fixtures
  - [ ] Mock JiraClient fixture for notification scheme endpoints
  - [ ] Sample notification scheme fixture
  - [ ] Sample event types fixture
  - [ ] Sample recipient types fixture
  - **Commit:** `test(jira-admin): add pytest fixtures for notification schemes`

- [ ] **Setup 1.3:** Add JiraClient methods for notification schemes
  - [ ] `get_notification_schemes()` - List all schemes
  - [ ] `get_notification_scheme(scheme_id)` - Get scheme details
  - [ ] `get_notification_scheme_projects()` - Get project mappings
  - [ ] `create_notification_scheme(data)` - Create new scheme
  - [ ] `update_notification_scheme(scheme_id, data)` - Update scheme
  - [ ] `add_notification_to_scheme(scheme_id, event_data)` - Add notification
  - [ ] `delete_notification_scheme(scheme_id)` - Delete scheme
  - [ ] `delete_notification_from_scheme(scheme_id, notification_id)` - Remove notification
  - **Commit:** `feat(shared): add notification scheme API methods to JiraClient`

---

## Phase 1: List Notification Schemes

### Feature 1.1: List All Notification Schemes

**Script:** `list_notification_schemes.py`

**JIRA API:**
- `GET /rest/api/3/notificationscheme`
- Optional params: `startAt`, `maxResults`, `expand`

**Test File:** `tests/test_list_notification_schemes.py`

**Test Cases:**
```python
def test_list_all_notification_schemes():
    """Test fetching all available notification schemes."""
    # Should return list of notification scheme objects

def test_scheme_has_required_fields():
    """Test that each scheme has id, name, description."""

def test_format_text_output():
    """Test human-readable table output."""

def test_format_json_output():
    """Test JSON output format."""

def test_filter_by_name():
    """Test filtering schemes by name pattern."""

def test_show_event_count():
    """Test showing number of configured events per scheme."""

def test_empty_notification_schemes():
    """Test output when no schemes exist."""

def test_pagination_handling():
    """Test handling paginated results (startAt/maxResults)."""
```

**CLI Interface:**
```bash
python list_notification_schemes.py
python list_notification_schemes.py --output json
python list_notification_schemes.py --filter "default"
python list_notification_schemes.py --show-events
python list_notification_schemes.py --profile production
```

**Output Example:**
```
Available Notification Schemes:

ID     Name                              Description                           Events
─────  ────────────────────────────────  ────────────────────────────────────  ──────
10000  Default Notification Scheme       Standard notification setup           8
10001  Development Team Notifications    Custom notifications for dev team     12
10002  Customer Support Notifications    Support team notification rules       10

Total: 3 notification schemes
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Shows all available notification schemes
- [ ] Supports text and JSON output
- [ ] Optional name filtering
- [ ] Handles pagination correctly
- [ ] Shows helpful message if no schemes exist

**Commits:**
1. `test(jira-admin): add failing tests for list_notification_schemes`
2. `feat(jira-admin): implement list_notification_schemes.py (8/8 tests passing)`

---

## Phase 2: Get Notification Scheme Details

### Feature 2.1: Get Notification Scheme by ID

**Script:** `get_notification_scheme.py`

**JIRA API:**
- `GET /rest/api/3/notificationscheme/{id}`
- Optional params: `expand=all,user,field,group,projectRole,notificationSchemeEvents`

**Test File:** `tests/test_get_notification_scheme.py`

**Test Cases:**
```python
def test_get_notification_scheme_by_id():
    """Test fetching notification scheme by ID."""

def test_scheme_details():
    """Test that all detail fields are present."""

def test_show_event_configurations():
    """Test showing event-to-recipient mappings."""

def test_format_text_output():
    """Test human-readable output with full details."""

def test_format_json_output():
    """Test JSON output format."""

def test_scheme_not_found():
    """Test error when scheme ID doesn't exist."""

def test_show_projects_using_scheme():
    """Test showing which projects use this scheme."""

def test_group_by_event_type():
    """Test grouping notifications by event type."""

def test_show_recipient_details():
    """Test expanding recipient details (group names, user names)."""
```

**CLI Interface:**
```bash
python get_notification_scheme.py 10000
python get_notification_scheme.py 10000 --output json
python get_notification_scheme.py 10000 --show-projects
python get_notification_scheme.py 10000 --expand-recipients
python get_notification_scheme.py --name "Default Notification Scheme"
```

**Output Example:**
```
Notification Scheme Details:

ID:           10000
Name:         Default Notification Scheme
Description:  Standard notification setup for most projects

Event Configurations:
──────────────────────────────────────────────────────────────────────────────
Event: Issue created (ID: 1)
  Recipients:
    - Current Assignee
    - Reporter
    - Group: jira-administrators

Event: Issue assigned (ID: 3)
  Recipients:
    - Current Assignee
    - Reporter
    - All Watchers

Event: Issue commented (ID: 6)
  Recipients:
    - Current Assignee
    - All Watchers
    - Group: developers

Event: Issue resolved (ID: 4)
  Recipients:
    - Current Assignee
    - Reporter
    - Project Lead

Total: 4 events configured
Projects using this scheme: 5

Use: python list_notification_schemes.py --show-projects 10000
```

**Acceptance Criteria:**
- [ ] All 9 tests pass
- [ ] Fetches scheme by ID or name
- [ ] Shows comprehensive scheme details
- [ ] Shows all event-to-recipient mappings
- [ ] Groups notifications by event type
- [ ] Supports text and JSON output
- [ ] Optional project usage display
- [ ] Helpful error for invalid IDs

**Commits:**
1. `test(jira-admin): add failing tests for get_notification_scheme`
2. `feat(jira-admin): implement get_notification_scheme.py (9/9 tests passing)`

---

## Phase 3: Create Notification Scheme

### Feature 3.1: Create New Notification Scheme

**Script:** `create_notification_scheme.py`

**JIRA API:**
- `POST /rest/api/3/notificationscheme`

**Test File:** `tests/test_create_notification_scheme.py`

**Test Cases:**
```python
def test_create_minimal_scheme():
    """Test creating scheme with minimal required fields."""

def test_create_scheme_with_events():
    """Test creating scheme with event configurations."""

def test_validate_required_fields():
    """Test validation of required fields (name)."""

def test_validate_event_ids():
    """Test validation of event IDs."""

def test_validate_recipient_types():
    """Test validation of notification types."""

def test_format_text_output():
    """Test human-readable success output."""

def test_format_json_output():
    """Test JSON output with created scheme details."""

def test_template_file_support():
    """Test creating from JSON template file."""

def test_dry_run_mode():
    """Test dry-run shows what would be created without creating."""

def test_duplicate_name_error():
    """Test error when scheme name already exists."""
```

**CLI Interface:**
```bash
# Create minimal scheme
python create_notification_scheme.py --name "New Scheme" --description "Description"

# Create with event configurations
python create_notification_scheme.py \
  --name "Dev Team Notifications" \
  --description "Notifications for development team" \
  --event "Issue created" \
  --notify CurrentAssignee \
  --notify Reporter \
  --notify Group:developers

# Create from template
python create_notification_scheme.py --template notification_scheme.json

# Dry run
python create_notification_scheme.py --template scheme.json --dry-run
```

**Output Example:**
```
Creating notification scheme...

Notification Scheme Created:
─────────────────────────────────────────
ID:           10100
Name:         Dev Team Notifications
Description:  Notifications for development team

Event Configurations:
  Issue created (ID: 1):
    - Current Assignee
    - Reporter
    - Group: developers

Success! Notification scheme created with ID: 10100

To assign to a project:
  python assign_notification_scheme.py PROJECT_KEY 10100
```

**Template File Example:**
```json
{
  "name": "Development Team Notifications",
  "description": "Custom notification setup for development projects",
  "notificationSchemeEvents": [
    {
      "event": {"id": "1"},
      "notifications": [
        {"notificationType": "CurrentAssignee"},
        {"notificationType": "Reporter"},
        {"notificationType": "Group", "parameter": "developers"}
      ]
    },
    {
      "event": {"id": "3"},
      "notifications": [
        {"notificationType": "CurrentAssignee"},
        {"notificationType": "AllWatchers"}
      ]
    }
  ]
}
```

**Acceptance Criteria:**
- [ ] All 10 tests pass
- [ ] Creates scheme with name and description
- [ ] Supports adding event configurations on creation
- [ ] Validates all input fields
- [ ] Supports template file input
- [ ] Dry-run mode for validation
- [ ] Returns created scheme ID
- [ ] Helpful error messages

**Commits:**
1. `test(jira-admin): add failing tests for create_notification_scheme`
2. `feat(jira-admin): implement create_notification_scheme.py (10/10 tests passing)`

---

## Phase 4: Update Notification Scheme

### Feature 4.1: Update Notification Scheme Metadata

**Script:** `update_notification_scheme.py`

**JIRA API:**
- `PUT /rest/api/3/notificationscheme/{id}`

**Test File:** `tests/test_update_notification_scheme.py`

**Test Cases:**
```python
def test_update_scheme_name():
    """Test updating scheme name."""

def test_update_scheme_description():
    """Test updating scheme description."""

def test_update_both_fields():
    """Test updating both name and description."""

def test_validate_scheme_exists():
    """Test error when scheme doesn't exist."""

def test_format_text_output():
    """Test human-readable success output."""

def test_format_json_output():
    """Test JSON output with updated scheme details."""

def test_dry_run_mode():
    """Test dry-run shows changes without applying."""

def test_no_changes_error():
    """Test error when no changes provided."""
```

**CLI Interface:**
```bash
# Update name
python update_notification_scheme.py 10000 --name "Updated Scheme Name"

# Update description
python update_notification_scheme.py 10000 --description "New description"

# Update both
python update_notification_scheme.py 10000 \
  --name "Renamed Scheme" \
  --description "Updated description"

# Dry run
python update_notification_scheme.py 10000 --name "Test" --dry-run
```

**Output Example:**
```
Updating notification scheme 10000...

Changes:
  Name:        "Default Notification Scheme" → "Production Notifications"
  Description: "Standard notification setup" → "Notifications for production projects"

Notification Scheme Updated:
─────────────────────────────────────────
ID:           10000
Name:         Production Notifications
Description:  Notifications for production projects

Success! Notification scheme 10000 updated.
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Updates scheme name
- [ ] Updates scheme description
- [ ] Validates scheme exists
- [ ] Shows before/after changes
- [ ] Dry-run mode
- [ ] Helpful error messages

**Commits:**
1. `test(jira-admin): add failing tests for update_notification_scheme`
2. `feat(jira-admin): implement update_notification_scheme.py (8/8 tests passing)`

---

## Phase 5: Add Notification to Scheme

### Feature 5.1: Add Event-Recipient Mapping

**Script:** `add_notification.py`

**JIRA API:**
- `PUT /rest/api/3/notificationscheme/{id}/notification`

**Test File:** `tests/test_add_notification.py`

**Test Cases:**
```python
def test_add_notification_current_assignee():
    """Test adding CurrentAssignee notification to event."""

def test_add_notification_group():
    """Test adding Group notification with parameter."""

def test_add_notification_project_role():
    """Test adding ProjectRole notification with role ID."""

def test_add_notification_user():
    """Test adding User notification with user account ID."""

def test_add_notification_all_watchers():
    """Test adding AllWatchers notification."""

def test_add_multiple_notifications():
    """Test adding multiple notifications to same event."""

def test_validate_event_id():
    """Test validation of event ID."""

def test_validate_recipient_type():
    """Test validation of notification type."""

def test_validate_required_parameters():
    """Test validation of required parameters (group name, role ID, etc.)."""

def test_format_text_output():
    """Test human-readable success output."""

def test_format_json_output():
    """Test JSON output."""

def test_dry_run_mode():
    """Test dry-run shows what would be added."""
```

**CLI Interface:**
```bash
# Add current assignee notification
python add_notification.py 10000 \
  --event "Issue created" \
  --notify CurrentAssignee

# Add group notification
python add_notification.py 10000 \
  --event "Issue created" \
  --notify Group:developers

# Add project role notification
python add_notification.py 10000 \
  --event "Issue assigned" \
  --notify ProjectRole:10002

# Add multiple notifications
python add_notification.py 10000 \
  --event "Issue resolved" \
  --notify CurrentAssignee \
  --notify Reporter \
  --notify AllWatchers

# Using event ID
python add_notification.py 10000 --event-id 1 --notify Group:jira-admins

# Dry run
python add_notification.py 10000 --event "Issue created" --notify Reporter --dry-run
```

**Output Example:**
```
Adding notification to scheme 10000...

Event: Issue created (ID: 1)
Adding recipients:
  - Current Assignee
  - Reporter
  - Group: developers

Notification Added:
─────────────────────────────────────────
Scheme:       Default Notification Scheme (10000)
Event:        Issue created
New Recipients:
  - Current Assignee
  - Reporter
  - Group: developers

Success! Notifications added to event "Issue created"

Current configuration for this event:
  - Current Assignee
  - Reporter
  - Group: jira-administrators
  - Group: developers
```

**Acceptance Criteria:**
- [ ] All 12 tests pass
- [ ] Adds notifications by event name or ID
- [ ] Supports all recipient types
- [ ] Validates event and recipient parameters
- [ ] Shows current and new configuration
- [ ] Dry-run mode
- [ ] Helpful error messages

**Commits:**
1. `test(jira-admin): add failing tests for add_notification`
2. `feat(jira-admin): implement add_notification.py (12/12 tests passing)`

---

## Phase 6: Delete Operations

### Feature 6.1: Delete Notification Scheme

**Script:** `delete_notification_scheme.py`

**JIRA API:**
- `DELETE /rest/api/3/notificationscheme/{notificationSchemeId}`

**Test File:** `tests/test_delete_notification_scheme.py`

**Test Cases:**
```python
def test_delete_scheme():
    """Test deleting notification scheme."""

def test_confirm_before_delete():
    """Test confirmation prompt before deletion."""

def test_force_delete_no_confirm():
    """Test --force flag bypasses confirmation."""

def test_validate_scheme_exists():
    """Test error when scheme doesn't exist."""

def test_prevent_delete_in_use():
    """Test preventing deletion of schemes in use by projects."""

def test_format_text_output():
    """Test human-readable success output."""

def test_dry_run_mode():
    """Test dry-run shows what would be deleted."""
```

**CLI Interface:**
```bash
# Delete with confirmation
python delete_notification_scheme.py 10000

# Force delete without confirmation
python delete_notification_scheme.py 10000 --force

# Dry run
python delete_notification_scheme.py 10000 --dry-run
```

**Output Example:**
```
Notification Scheme: Default Notification Scheme (10000)
Description: Standard notification setup

Projects using this scheme: 0

WARNING: This will permanently delete the notification scheme.
Are you sure you want to delete this scheme? (yes/no): yes

Deleting notification scheme 10000...

Success! Notification scheme "Default Notification Scheme" (10000) deleted.
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Deletes notification scheme by ID
- [ ] Confirmation prompt (unless --force)
- [ ] Prevents deletion if in use by projects
- [ ] Dry-run mode
- [ ] Helpful error messages

**Commits:**
1. `test(jira-admin): add failing tests for delete_notification_scheme`
2. `feat(jira-admin): implement delete_notification_scheme.py (7/7 tests passing)`

---

### Feature 6.2: Remove Notification from Scheme

**Script:** `remove_notification.py`

**JIRA API:**
- `DELETE /rest/api/3/notificationscheme/{schemeId}/notification/{notificationId}`

**Test File:** `tests/test_remove_notification.py`

**Test Cases:**
```python
def test_remove_notification_by_id():
    """Test removing notification by ID."""

def test_remove_by_event_and_recipient():
    """Test removing by event name and recipient type."""

def test_validate_notification_exists():
    """Test error when notification doesn't exist."""

def test_confirm_before_remove():
    """Test confirmation prompt before removal."""

def test_force_remove_no_confirm():
    """Test --force flag bypasses confirmation."""

def test_format_text_output():
    """Test human-readable success output."""

def test_dry_run_mode():
    """Test dry-run shows what would be removed."""
```

**CLI Interface:**
```bash
# Remove by notification ID
python remove_notification.py 10000 --notification-id 12

# Remove by event and recipient
python remove_notification.py 10000 \
  --event "Issue created" \
  --recipient Group:developers

# Force remove
python remove_notification.py 10000 --notification-id 12 --force

# Dry run
python remove_notification.py 10000 --notification-id 12 --dry-run
```

**Output Example:**
```
Notification Scheme: Default Notification Scheme (10000)
Event: Issue created
Recipient: Group: developers

WARNING: This will remove the notification from the scheme.
Are you sure? (yes/no): yes

Removing notification...

Success! Notification removed from scheme.

Remaining recipients for "Issue created":
  - Current Assignee
  - Reporter
  - Group: jira-administrators
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Removes notification by ID
- [ ] Removes by event and recipient matching
- [ ] Confirmation prompt (unless --force)
- [ ] Shows remaining configuration
- [ ] Dry-run mode
- [ ] Helpful error messages

**Commits:**
1. `test(jira-admin): add failing tests for remove_notification`
2. `feat(jira-admin): implement remove_notification.py (7/7 tests passing)`

---

## Integration & Documentation Updates

### Integration Tasks

- [ ] **Integration 1:** Update shared library
  - [ ] Add notification scheme API base URL constants
  - [ ] Add notification scheme-specific error handling
  - [ ] Add helper methods for scheme lookup by name
  - [ ] **Commit:** `feat(shared): add notification scheme API support to JiraClient`

- [ ] **Integration 2:** Create notification scheme utilities
  - [ ] Add `notification_utils.py` with helper functions
  - [ ] Event ID to name mapping
  - [ ] Event name to ID lookup
  - [ ] Recipient type validation
  - [ ] Scheme name to ID lookup
  - [ ] **Commit:** `feat(jira-admin): add notification scheme utility functions`

- [ ] **Integration 3:** Create template files
  - [ ] Add `assets/templates/notification_scheme_basic.json`
  - [ ] Add `assets/templates/notification_scheme_comprehensive.json`
  - [ ] Add `assets/templates/notification_scheme_minimal.json`
  - [ ] **Commit:** `feat(jira-admin): add notification scheme templates`

### Documentation Updates

- [ ] **Docs 1:** Create comprehensive SKILL.md
  - [ ] "When to use this skill" section
  - [ ] "What this skill does" section
  - [ ] "Available scripts" with descriptions
  - [ ] "Examples" with realistic workflows
  - [ ] Configuration notes
  - [ ] Related skills section
  - [ ] **Commit:** `docs(jira-admin): create comprehensive SKILL.md`

- [ ] **Docs 2:** Create API reference
  - [ ] Create `references/notification_api_reference.md`
  - [ ] Document all notification scheme endpoints
  - [ ] Sample request/response payloads
  - [ ] Error codes and handling
  - [ ] **Commit:** `docs(jira-admin): add notification scheme API reference`

- [ ] **Docs 3:** Update root CLAUDE.md
  - [ ] Add jira-admin to project overview
  - [ ] Add notification scheme usage patterns section
  - [ ] **Commit:** `docs: update CLAUDE.md with jira-admin skill`

- [ ] **Docs 4:** Create user guide
  - [ ] Create `references/notification_schemes_guide.md`
  - [ ] Common notification scheme patterns
  - [ ] Best practices
  - [ ] Troubleshooting
  - [ ] **Commit:** `docs(jira-admin): add notification schemes user guide`

### Testing & Quality

- [ ] **Quality 1:** Integration tests
  - [ ] End-to-end: Create scheme → Add notifications → Update → Delete
  - [ ] Live integration test framework
  - [ ] Minimum 5 integration tests covering happy paths
  - [ ] **Commit:** `test(jira-admin): add live integration tests for notification schemes`

- [ ] **Quality 2:** Coverage validation
  - [ ] Run `pytest --cov=.claude/skills/jira-admin --cov-report=html`
  - [ ] Verify ≥85% coverage target
  - [ ] Document uncovered code with justification
  - [ ] **Commit:** `test(jira-admin): verify 85%+ test coverage`

- [ ] **Quality 3:** Error handling review
  - [ ] All scripts use try/except with JiraError
  - [ ] Validation before API calls
  - [ ] Helpful error messages with suggestions
  - [ ] Permission error detection
  - [ ] **Commit:** `fix(jira-admin): improve error handling and validation`

- [ ] **Quality 4:** CLI consistency check
  - [ ] All scripts have `--help`
  - [ ] All scripts support `--profile`
  - [ ] All scripts support `--output json`
  - [ ] Consistent argument naming conventions
  - [ ] **Commit:** `refactor(jira-admin): ensure CLI consistency`

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 60+ unit tests passing (8+8+10+8+12+7+7)
- [ ] 5+ integration tests passing
- [ ] Coverage ≥ 85%
- [ ] All tests use proper mocking

**Scripts:**
- [ ] 6 scripts implemented
- [ ] All scripts have `--help`
- [ ] All scripts support `--profile`
- [ ] All scripts support `--output json`
- [ ] All scripts have proper error handling

**Documentation:**
- [ ] SKILL.md complete with examples
- [ ] API reference documentation
- [ ] User guide with best practices
- [ ] CLAUDE.md updated
- [ ] All scripts have docstrings

**Integration:**
- [ ] JiraClient extended with 8 notification scheme methods
- [ ] Notification utilities module created
- [ ] Template files created
- [ ] No breaking changes to existing skills

### Progress Tracking

**Test Status:** 0/60+ unit tests passing (0%)

**Phase Status:**
- [ ] Phase 1: List Notification Schemes (1 script, 8 tests)
- [ ] Phase 2: Get Notification Scheme Details (1 script, 9 tests)
- [ ] Phase 3: Create Notification Scheme (1 script, 10 tests)
- [ ] Phase 4: Update Notification Scheme (1 script, 8 tests)
- [ ] Phase 5: Add Notification to Scheme (1 script, 12 tests)
- [ ] Phase 6: Delete Operations (2 scripts, 14 tests)
- [ ] Integration (3 updates)
- [ ] Documentation (4 docs)
- [ ] Quality (4 tasks)

---

## Script Summary

| Script | Phase | Tests | Status | Description |
|--------|-------|-------|--------|-------------|
| `list_notification_schemes.py` | 1 | 8 | NOT STARTED | List all notification schemes |
| `get_notification_scheme.py` | 2 | 9 | NOT STARTED | Get scheme details with event mappings |
| `create_notification_scheme.py` | 3 | 10 | NOT STARTED | Create new notification scheme |
| `update_notification_scheme.py` | 4 | 8 | NOT STARTED | Update scheme metadata |
| `add_notification.py` | 5 | 12 | NOT STARTED | Add event-recipient mapping |
| `delete_notification_scheme.py` | 6.1 | 7 | NOT STARTED | Delete notification scheme |
| `remove_notification.py` | 6.2 | 7 | NOT STARTED | Remove notification from scheme |
| **Total** | - | **61** | **0/6** | - |

---

## JiraClient Methods to Add

```python
# In shared/scripts/lib/jira_client.py

def get_notification_schemes(self, start_at: int = 0, max_results: int = 50,
                             expand: str = None) -> dict:
    """Get all notification schemes with pagination."""
    params = {'startAt': start_at, 'maxResults': max_results}
    if expand:
        params['expand'] = expand
    return self.get('/rest/api/3/notificationscheme', params=params)

def get_notification_scheme(self, scheme_id: str, expand: str = None) -> dict:
    """Get a specific notification scheme by ID."""
    params = {}
    if expand:
        params['expand'] = expand
    return self.get(f'/rest/api/3/notificationscheme/{scheme_id}', params=params)

def get_notification_scheme_projects(self, start_at: int = 0,
                                     max_results: int = 50,
                                     notification_scheme_id: list = None) -> dict:
    """Get project-to-notification scheme mappings."""
    params = {'startAt': start_at, 'maxResults': max_results}
    if notification_scheme_id:
        params['notificationSchemeId'] = notification_scheme_id
    return self.get('/rest/api/3/notificationscheme/project', params=params)

def create_notification_scheme(self, data: dict) -> dict:
    """Create a new notification scheme.

    Args:
        data: Dictionary with 'name', 'description', 'notificationSchemeEvents'

    Returns:
        Created notification scheme object
    """
    return self.post('/rest/api/3/notificationscheme', json=data)

def update_notification_scheme(self, scheme_id: str, data: dict) -> dict:
    """Update notification scheme metadata (name, description).

    Args:
        scheme_id: Notification scheme ID
        data: Dictionary with 'name' and/or 'description'

    Returns:
        Updated notification scheme object
    """
    return self.put(f'/rest/api/3/notificationscheme/{scheme_id}', json=data)

def add_notification_to_scheme(self, scheme_id: str, event_data: dict) -> dict:
    """Add notifications to a notification scheme.

    Args:
        scheme_id: Notification scheme ID
        event_data: Dictionary with 'notificationSchemeEvents'

    Returns:
        Updated notification scheme object
    """
    return self.put(
        f'/rest/api/3/notificationscheme/{scheme_id}/notification',
        json=event_data
    )

def delete_notification_scheme(self, scheme_id: str) -> None:
    """Delete a notification scheme.

    Args:
        scheme_id: Notification scheme ID
    """
    return self.delete(f'/rest/api/3/notificationscheme/{scheme_id}')

def delete_notification_from_scheme(self, scheme_id: str,
                                    notification_id: str) -> dict:
    """Remove a notification from a notification scheme.

    Args:
        scheme_id: Notification scheme ID
        notification_id: Notification ID to remove

    Returns:
        Updated notification scheme object
    """
    return self.delete(
        f'/rest/api/3/notificationscheme/{scheme_id}/notification/{notification_id}'
    )

def lookup_notification_scheme_by_name(self, name: str) -> dict:
    """Lookup notification scheme ID by name.

    Args:
        name: Notification scheme name (case-sensitive)

    Returns:
        Notification scheme object

    Raises:
        JiraError: If scheme not found
    """
    schemes = self.get_notification_schemes()
    for scheme in schemes.get('values', []):
        if scheme.get('name') == name:
            return scheme
    raise JiraError(f"No notification scheme found with name: {name}")
```

---

## Commit Strategy

### Commit Types

**test:** Adding or updating tests
- `test(jira-admin): add failing tests for list_notification_schemes`

**feat:** Implementing features
- `feat(jira-admin): implement list_notification_schemes.py (8/8 tests passing)`

**docs:** Documentation updates
- `docs(jira-admin): add notification scheme examples to SKILL.md`

**fix:** Bug fixes
- `fix(jira-admin): handle pagination edge cases`

**refactor:** Code improvements without changing behavior
- `refactor(jira-admin): extract scheme lookup to utility function`

---

## Example Workflows

### Workflow 1: Create Comprehensive Notification Scheme

```bash
# 1. Create base scheme
python create_notification_scheme.py \
  --name "Production Notifications" \
  --description "Notification setup for production projects"

# Output: Created scheme with ID 10100

# 2. Add "Issue Created" notifications
python add_notification.py 10100 \
  --event "Issue created" \
  --notify CurrentAssignee \
  --notify Reporter \
  --notify Group:jira-administrators

# 3. Add "Issue Assigned" notifications
python add_notification.py 10100 \
  --event "Issue assigned" \
  --notify CurrentAssignee \
  --notify Reporter \
  --notify AllWatchers

# 4. Add "Issue Resolved" notifications
python add_notification.py 10100 \
  --event "Issue resolved" \
  --notify CurrentAssignee \
  --notify Reporter \
  --notify ProjectLead

# 5. Verify configuration
python get_notification_scheme.py 10100

# 6. Assign to project (future script)
python assign_notification_scheme.py PROJ 10100
```

### Workflow 2: Audit and Update Existing Schemes

```bash
# 1. List all schemes
python list_notification_schemes.py --show-events

# 2. Get details of scheme in use
python get_notification_scheme.py 10000 --show-projects

# 3. Add missing notification
python add_notification.py 10000 \
  --event "Issue commented" \
  --notify AllWatchers

# 4. Verify changes
python get_notification_scheme.py 10000
```

### Workflow 3: Clone and Customize Scheme

```bash
# 1. Export existing scheme
python get_notification_scheme.py 10000 --output json > scheme_backup.json

# 2. Edit JSON file to customize (change name, modify events)
# ... edit scheme_backup.json ...

# 3. Create new scheme from template
python create_notification_scheme.py --template scheme_backup.json

# 4. Verify new scheme
python list_notification_schemes.py --filter "Custom"
```

### Workflow 4: Clean Up Unused Schemes

```bash
# 1. List all schemes with project usage
python list_notification_schemes.py --show-projects

# 2. Identify unused scheme (0 projects)
# Scheme ID 10050: "Old Dev Scheme" - 0 projects

# 3. Get details to confirm
python get_notification_scheme.py 10050 --show-projects

# 4. Delete unused scheme
python delete_notification_scheme.py 10050

# 5. Verify deletion
python list_notification_schemes.py
```

---

## API Sources

- [Jira Cloud REST API - Notification Schemes](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-notification-schemes/)
- [Configure Notification Schemes - Atlassian Support](https://support.atlassian.com/jira-cloud-administration/docs/configure-notification-schemes/)
- [Add a Custom Event - Atlassian Support](https://support.atlassian.com/jira-cloud-administration/docs/add-a-custom-event/)
- [New REST APIs for Notification Schemes Announcement](https://community.developer.atlassian.com/t/new-rest-apis-for-event-and-notifications-scheme-are-released-in-jira-cloud/64012)
- [Jira Events Reference](https://developer.atlassian.com/platform/forge/events-reference/jira/)

---

## Related Future Features

### Additional Scripts (Not in Scope)

**Project Assignment:**
- `assign_notification_scheme.py` - Assign scheme to project
- `get_project_notification_scheme.py` - Get scheme for project
- `bulk_assign_notification_scheme.py` - Assign to multiple projects

**Event Management:**
- `list_notification_events.py` - List all available events
- `create_custom_event.py` - Create custom event
- `delete_custom_event.py` - Delete custom event

**Reporting:**
- `notification_scheme_report.py` - Generate scheme usage report
- `notification_coverage_report.py` - Check which events have notifications

---

## Notes

### Important Considerations

**Permissions:**
- Requires "Administer Jira" global permission
- Only schemes for projects the user can administer are returned

**Project Types:**
- Only company-managed (classic) projects support notification schemes
- Team-managed projects have their own notification model

**Event IDs:**
- Event IDs may vary by JIRA instance
- Use event names for portability when possible
- System events cannot be deleted (only deactivated)

**Recipient Parameters:**
- `Group`: Requires group name as parameter
- `User`: Requires user account ID (not username)
- `ProjectRole`: Requires project role ID
- `CurrentAssignee`, `Reporter`, `AllWatchers`: No parameter needed

**Testing Strategy:**
- Mock all JIRA API responses
- Test error conditions thoroughly
- Test output formatting
- Test CLI argument parsing
- Integration tests require "Administer Jira" permission

**Common Pitfalls:**
- Deleting scheme in use by projects (should be prevented)
- Using incorrect event IDs (validate against available events)
- Missing required parameters for recipient types (Group, User, ProjectRole)
- Case sensitivity in scheme/group names

---

**Plan Version:** 1.0
**Created:** 2025-12-26
**Last Updated:** 2025-12-26
**Status:** NOT STARTED
**Estimated Effort:** 20-25 hours over 2 weeks

**Summary:**
- 6 core scripts planned (list, get, create, update, add notification, delete)
- 61+ unit tests to implement
- 5+ integration tests to implement
- Coverage target: 85%+
- Full TDD approach with test-first development
- Comprehensive documentation and user guide
