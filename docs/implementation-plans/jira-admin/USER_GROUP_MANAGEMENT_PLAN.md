# JIRA Administration Phase 2: User & Group Management - TDD Implementation Plan

## Implementation Status

**Status:** READY FOR IMPLEMENTATION
**Created Date:** 2025-12-26

### Summary
- Phase 2.1: User Search & Retrieval (2/2 scripts planned)
- Phase 2.2: Group CRUD Operations (4/4 scripts planned)
- Phase 2.3: Group Membership Management (2/2 scripts planned)
- Total: 8/8 scripts planned

## Overview

**Objective:** Implement comprehensive user and group management for JIRA Cloud using Test-Driven Development (TDD)

**Context:** This is Phase 2 of the jira-admin skill implementation. User and group management enables automation of team onboarding, permission management, and organizational structure maintenance.

**Important:** This implementation focuses exclusively on JIRA Cloud APIs. Cloud and Server have significantly different user management architectures.

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
1. **Phase 2.1: User Search & Retrieval** (Search and get user information)
2. **Phase 2.2: Group CRUD Operations** (Create, list, get, delete groups)
3. **Phase 2.3: Group Membership Management** (Add/remove users from groups)

**Dependencies:**
- Shared JiraClient library (must support user/group APIs)
- GDPR-compliant accountId-based user identification
- Phase 1 (Project Management) - Recommended but not required

---

## JIRA API Reference

### API Version
**Base URL:** `/rest/api/3` (JIRA Cloud Platform REST API v3)

### User Management Endpoints

| Method | Endpoint | Description | Required Permission |
|--------|----------|-------------|---------------------|
| GET | `/user/search` | Search users by query string | Browse users and groups |
| GET | `/user` | Get user details by accountId or email | Browse users and groups |
| GET | `/users/search` | Get all users (paginated) | Browse users and groups |
| GET | `/user/assignable/search` | Find assignable users for project | Browse Projects (per project) |
| GET | `/user/groups` | Get groups user belongs to | Browse users and groups |
| GET | `/myself` | Get current user information | None (authenticated) |
| GET | `/user/bulk` | Get multiple users by accountId | Browse users and groups |

**Note:** User creation and deactivation are NOT available through the Jira Platform API in Cloud. These operations require:
- User creation: Handled through Atlassian Cloud Admin (admin.atlassian.com)
- User deactivation: Cloud Admin API (`/users/{accountId}/manage/lifecycle/disable`)

### Group Management Endpoints

| Method | Endpoint | Description | Required Permission |
|--------|----------|-------------|---------------------|
| GET | `/groups/picker` | Find groups by name (picker UI) | Browse users and groups |
| GET | `/group/bulk` | Get multiple groups | Browse users and groups |
| GET | `/group` | Get single group details | Browse users and groups |
| POST | `/group` | Create new group | Site administration |
| DELETE | `/group` | Delete group | Site administration |
| GET | `/group/member` | Get group members (paginated) | Browse users and groups |
| POST | `/group/user` | Add user to group | Site administration |
| DELETE | `/group/user` | Remove user from group | Site administration |

### GDPR & Privacy Considerations

**Critical:** JIRA Cloud has implemented GDPR-compliant user privacy controls:

1. **Account ID Required:** Username and userkey were removed from APIs in April 2019. All user references must use `accountId`.

2. **Privacy Controls:** Users can restrict visibility of personal data:
   - Email addresses may be hidden
   - Display names may be restricted
   - Time zone and locale may be hidden
   - Profile visibility settings are user-controlled

3. **Special Account IDs:**
   - `"unknown"`: May appear for deleted/anonymized users
   - Apps should NOT attempt to retrieve personal data for "unknown"

4. **Deleted Users:** When users exercise "right to be forgotten":
   - `displayName` shows indication of deletion
   - Other fields are blank or default values
   - Email will be blank

5. **Profile Visibility:** Response fields depend on:
   - User's own privacy settings
   - Calling user's permissions
   - Organizational admin settings

### Permission Requirements

**User Search Operations:**
- `GET /user/search` - Requires "Browse users and groups" global permission
- Anonymous calls return empty results
- Privacy controls filter response data

**Group Operations:**
- List/Read groups - "Browse users and groups" global permission
- Create/Delete groups - "Site administration" (site-admin group membership)
- Add/Remove members - "Site administration"

**Connect Apps:** Most user/group endpoints are NOT accessible to Connect apps. This skill is designed for API token authentication.

### Data Structures

#### User Object (GET /user)
```json
{
  "accountId": "5b10ac8d82e05b22cc7d4ef5",
  "accountType": "atlassian",
  "displayName": "John Doe",
  "emailAddress": "john.doe@example.com",
  "active": true,
  "timeZone": "America/New_York",
  "locale": "en-US",
  "groups": {
    "size": 3,
    "items": []
  },
  "applicationRoles": {
    "size": 1,
    "items": []
  },
  "avatarUrls": {
    "48x48": "https://avatar-url.com/48x48",
    "24x24": "https://avatar-url.com/24x24",
    "16x16": "https://avatar-url.com/16x16",
    "32x32": "https://avatar-url.com/32x32"
  }
}
```

**Note:** Some fields may be absent due to privacy controls.

#### User Search Results (GET /user/search)
```json
[
  {
    "accountId": "5b10ac8d82e05b22cc7d4ef5",
    "displayName": "John Doe",
    "emailAddress": "john.doe@example.com",
    "active": true
  }
]
```

#### Group Object (GET /group)
```json
{
  "name": "jira-developers",
  "groupId": "276f955c-63d7-42c8-9520-92d01dca0625",
  "self": "https://your-domain.atlassian.net/rest/api/3/group?groupId=276f955c-63d7-42c8-9520-92d01dca0625"
}
```

#### Create Group Payload (POST /group)
```json
{
  "name": "jira-developers"
}
```

#### Add User to Group Payload (POST /group/user)
```json
{
  "accountId": "5b10ac8d82e05b22cc7d4ef5"
}
```

Query Parameters:
- `groupname` or `groupId` - Specify target group

#### Group Members Response (GET /group/member)
```json
{
  "self": "https://your-domain.atlassian.net/rest/api/3/group/member",
  "maxResults": 50,
  "startAt": 0,
  "total": 2,
  "isLast": true,
  "values": [
    {
      "accountId": "5b10ac8d82e05b22cc7d4ef5",
      "displayName": "John Doe",
      "emailAddress": "john.doe@example.com",
      "active": true
    }
  ]
}
```

---

## Cloud vs Server API Differences

### User Management Architecture

**JIRA Cloud:**
- Centralized user management via admin.atlassian.com
- Users managed at organization level, not product level
- Single Atlassian account across all cloud products
- User creation requires Cloud Admin API (not Jira Platform API)
- User deactivation via Cloud Admin API lifecycle endpoint

**JIRA Server/Data Center:**
- Embedded Crowd for user management
- Users managed per instance
- User creation via Jira API
- Deactivation via PUT /user with `"active": false`

### API Endpoint Differences

| Operation | Cloud | Server |
|-----------|-------|--------|
| Create User | Cloud Admin API only | POST /rest/api/2/user |
| Deactivate User | Cloud Admin lifecycle API | PUT /rest/api/2/user (active: false) |
| User Identification | accountId only | username, userkey, accountId |
| Group Creation | POST /rest/api/3/group | POST /rest/api/2/group |

### Migration Implications

**This implementation targets JIRA Cloud exclusively:**
- Uses accountId for all user references
- Does NOT support username/userkey (deprecated in Cloud)
- Group operations use both groupname and groupId
- Privacy controls are Cloud-specific features

**If Server support is needed:** Create separate scripts or add `--cloud/--server` flag to handle API differences.

---

## Test Infrastructure Setup

### Initial Setup Tasks

- [ ] **Setup 2.1:** Create test infrastructure for Phase 2
  - [ ] Create `tests/test_user_search.py` skeleton
  - [ ] Create `tests/test_user_retrieval.py` skeleton
  - [ ] Create `tests/test_group_operations.py` skeleton
  - [ ] Create `tests/test_group_membership.py` skeleton
  - [ ] Add user/group fixtures to `tests/conftest.py`
  - **Commit:** `test(jira-admin): add Phase 2 test infrastructure`

- [ ] **Setup 2.2:** Add JiraClient methods for user operations
  - [ ] `search_users(query, start=0, max_results=50, active_only=True)` - Search users
  - [ ] `get_user(account_id=None, email=None, expand=None)` - Get user details
  - [ ] `get_current_user()` - Get current authenticated user
  - [ ] `get_user_groups(account_id)` - Get user's group memberships
  - [ ] `find_assignable_users(query, project_key, start=0, max_results=50)` - Assignable users
  - [ ] `get_all_users(start=0, max_results=50)` - Get all users (admin only)
  - **Commit:** `feat(shared): add user management methods to JiraClient`

- [ ] **Setup 2.3:** Add JiraClient methods for group operations
  - [ ] `find_groups(query, start=0, max_results=50)` - Find groups (picker API)
  - [ ] `get_group(group_name=None, group_id=None)` - Get group details
  - [ ] `create_group(name)` - Create new group
  - [ ] `delete_group(group_name=None, group_id=None)` - Delete group
  - [ ] `get_group_members(group_name=None, group_id=None, start=0, max_results=50)` - List members
  - [ ] `add_user_to_group(account_id, group_name=None, group_id=None)` - Add member
  - [ ] `remove_user_from_group(account_id, group_name=None, group_id=None)` - Remove member
  - **Commit:** `feat(shared): add group management methods to JiraClient`

### Error Handling Requirements

Add to `error_handler.py`:
- Map 403 to PermissionError with hint: "User/group operations require 'Browse users and groups' or 'Site administration' permissions"
- Map 404 with context: User not found vs Group not found
- Handle GDPR "unknown" accountId gracefully
- Provide clear messages for privacy-restricted fields

---

## Phase 2.1: User Search & Retrieval

### Feature 2.1.1: Search Users

**Script:** `search_users.py`

**JIRA API:**
- `GET /rest/api/3/user/search` - Search users by query
- `GET /rest/api/3/user/assignable/search` - Find assignable users

**Test File:** `tests/test_search_users.py`

**Test Cases:**
```python
def test_search_users_by_name():
    """Test searching users by display name."""
    # Should return users matching query in displayName

def test_search_users_by_email():
    """Test searching users by email address."""
    # Should return users matching query in email

def test_search_users_active_only():
    """Test filtering to active users only."""
    # Should exclude inactive users when flag set

def test_search_users_include_inactive():
    """Test including inactive users in results."""
    # Should include all users when flag not set

def test_search_users_assignable_for_project():
    """Test finding assignable users for specific project."""
    # Should use assignable/search endpoint with project filter

def test_search_users_pagination():
    """Test pagination with start and max_results."""
    # Should handle paginated results correctly

def test_search_users_empty_results():
    """Test handling no matching users."""
    # Should show clear "no users found" message

def test_search_users_text_format():
    """Test formatted table output."""
    # Should show table with accountId, name, email, status

def test_search_users_json_output():
    """Test JSON output format."""
    # Should return array of user objects

def test_search_users_csv_output():
    """Test CSV export format."""
    # Should generate CSV with headers

def test_search_users_privacy_controls():
    """Test handling privacy-restricted fields."""
    # Should gracefully handle missing email/timezone

def test_search_users_permission_error():
    """Test handling insufficient permissions."""
    # Should explain 'Browse users and groups' requirement

def test_search_users_with_groups():
    """Test including group membership in output."""
    # Should show groups each user belongs to

def test_search_users_empty_query():
    """Test behavior with empty query string."""
    # Should return first N users or require query
```

**CLI Interface:**
```bash
# Basic search
python search_users.py "john"
python search_users.py "john.doe@example.com"

# Active users only (default)
python search_users.py "john" --active-only

# Include inactive users
python search_users.py "john" --all

# Find assignable users for project
python search_users.py "john" --project PROJ --assignable

# Pagination
python search_users.py "john" --start 0 --max-results 10

# Include group membership
python search_users.py "john" --include-groups

# Output formats
python search_users.py "john" --output table  # Default
python search_users.py "john" --output json
python search_users.py "john" --output csv > users.csv

# With profile
python search_users.py "john" --profile development
```

**Output Example (table format):**
```
Found 3 users matching "john"

Account ID                     Display Name     Email                    Status   Groups
5b10ac8d82e05b22cc7d4ef5       John Doe         john.doe@example.com     Active   jira-users, developers
a1b2c3d4e5f6g7h8i9j0k1l2       John Smith       [hidden]                 Active   jira-users
9z8y7x6w5v4u3t2s1r0q9p8o       Johnny Bravo     johnny@example.com       Inactive jira-users
```

**Output Example (JSON format):**
```json
[
  {
    "accountId": "5b10ac8d82e05b22cc7d4ef5",
    "displayName": "John Doe",
    "emailAddress": "john.doe@example.com",
    "active": true,
    "accountType": "atlassian",
    "groups": ["jira-users", "developers"]
  }
]
```

**Acceptance Criteria:**
- [ ] All 14 tests pass
- [ ] Supports name and email search
- [ ] Active-only filtering
- [ ] Project-specific assignable user search
- [ ] Pagination support
- [ ] Handles privacy-restricted fields gracefully
- [ ] Multiple output formats (table, JSON, CSV)
- [ ] Clear permission error messages

**Implementation Notes:**
- Default to active users only for cleaner results
- Handle privacy controls - show "[hidden]" for restricted fields
- Use tabulate for table formatting (consistent with other scripts)
- Assignable search requires project context
- Document "Browse users and groups" permission requirement

**Commits:**
1. `test(jira-admin): add failing tests for search_users`
2. `feat(jira-admin): implement search_users.py (14/14 tests passing)`

---

### Feature 2.1.2: Get User Details

**Script:** `get_user.py`

**JIRA API:**
- `GET /rest/api/3/user` - Get user by accountId or email
- `GET /rest/api/3/myself` - Get current user
- `GET /rest/api/3/user/groups` - Get user's groups

**Test File:** `tests/test_get_user.py`

**Test Cases:**
```python
def test_get_user_by_account_id():
    """Test getting user details by accountId."""
    # Should return full user object

def test_get_user_by_email():
    """Test getting user by email address."""
    # Should lookup by email and return user

def test_get_current_user():
    """Test getting current authenticated user."""
    # Should call /myself endpoint

def test_get_user_with_groups():
    """Test including group membership."""
    # Should fetch and display user's groups

def test_get_user_with_application_roles():
    """Test including application roles."""
    # Should show Jira access level

def test_get_user_text_format():
    """Test formatted user details output."""
    # Should show readable user profile

def test_get_user_json_output():
    """Test JSON output format."""
    # Should return complete user object

def test_get_user_not_found():
    """Test handling user not found error."""
    # Should show clear error message

def test_get_user_privacy_restricted():
    """Test handling privacy-restricted profile."""
    # Should show available fields, mark others as [hidden]

def test_get_user_inactive():
    """Test displaying inactive user."""
    # Should clearly indicate inactive status

def test_get_user_unknown_account():
    """Test handling 'unknown' special accountId."""
    # Should explain this represents deleted/anonymized user

def test_get_user_permission_error():
    """Test handling insufficient permissions."""
    # Should explain permission requirements
```

**CLI Interface:**
```bash
# Get by accountId
python get_user.py --account-id 5b10ac8d82e05b22cc7d4ef5

# Get by email
python get_user.py --email john.doe@example.com

# Get current user
python get_user.py --me

# Include groups
python get_user.py --email john@example.com --include-groups

# Include application roles
python get_user.py --email john@example.com --include-roles

# Output formats
python get_user.py --email john@example.com --output text  # Default
python get_user.py --email john@example.com --output json

# With profile
python get_user.py --email john@example.com --profile development
```

**Output Example (text format):**
```
User Details
============

Account ID:      5b10ac8d82e05b22cc7d4ef5
Display Name:    John Doe
Email Address:   john.doe@example.com
Account Type:    atlassian
Status:          Active
Time Zone:       America/New_York
Locale:          en-US

Groups:
  - jira-users
  - jira-developers
  - jira-administrators

Application Roles:
  - Jira Software (Licensed)
```

**Output Example (privacy-restricted):**
```
User Details
============

Account ID:      a1b2c3d4e5f6g7h8i9j0k1l2
Display Name:    Jane Smith
Email Address:   [hidden - privacy settings]
Account Type:    atlassian
Status:          Active
Time Zone:       [hidden - privacy settings]
Locale:          [hidden - privacy settings]

Note: Some fields are hidden due to user privacy settings.
```

**Acceptance Criteria:**
- [ ] All 12 tests pass
- [ ] Supports lookup by accountId or email
- [ ] Get current user functionality
- [ ] Includes group membership when requested
- [ ] Handles privacy-restricted fields gracefully
- [ ] Clear display of inactive status
- [ ] Explains "unknown" accountId
- [ ] Multiple output formats

**Implementation Notes:**
- Require either --account-id, --email, or --me
- Show "[hidden - privacy settings]" for restricted fields
- Highlight inactive status prominently
- Document that email lookup may fail if email is privacy-restricted
- Use expand parameter for groups/applicationRoles

**Commits:**
1. `test(jira-admin): add failing tests for get_user`
2. `feat(jira-admin): implement get_user.py (12/12 tests passing)`

---

## Phase 2.2: Group CRUD Operations

### Feature 2.2.1: List Groups

**Script:** `list_groups.py`

**JIRA API:**
- `GET /rest/api/3/groups/picker` - Find groups by query

**Test File:** `tests/test_list_groups.py`

**Test Cases:**
```python
def test_list_all_groups():
    """Test listing all groups."""
    # Should return paginated list of groups

def test_list_groups_by_query():
    """Test searching groups by name."""
    # Should filter groups matching query

def test_list_groups_pagination():
    """Test pagination with start and max_results."""
    # Should handle large group lists

def test_list_groups_empty_results():
    """Test handling no matching groups."""
    # Should show "no groups found" message

def test_list_groups_text_format():
    """Test formatted table output."""
    # Should show table with name, groupId

def test_list_groups_json_output():
    """Test JSON output format."""
    # Should return array of group objects

def test_list_groups_with_member_count():
    """Test including member count for each group."""
    # Should fetch and display member counts (requires additional API calls)

def test_list_groups_permission_error():
    """Test handling insufficient permissions."""
    # Should explain 'Browse users and groups' requirement
```

**CLI Interface:**
```bash
# List all groups
python list_groups.py

# Search groups
python list_groups.py --query "jira"
python list_groups.py --query "developers"

# Pagination
python list_groups.py --start 0 --max-results 20

# Include member counts (slower - makes additional API calls)
python list_groups.py --include-members

# Output formats
python list_groups.py --output table  # Default
python list_groups.py --output json

# With profile
python list_groups.py --profile development
```

**Output Example (table format):**
```
Found 5 groups

Group Name              Group ID                              Members
jira-administrators     276f955c-63d7-42c8-9520-92d01dca0625  3
jira-developers         a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5o6  12
jira-users              9z8y7x6w-5v4u-43t2-s1r0-q9p8o7n6m5l4  45
project-admins          f1e2d3c4-b5a6-4978-8899-aabbccddeeff  5
external-contractors    11223344-5566-4778-8990-0aabbccddeef  8
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Lists all groups with pagination
- [ ] Supports query filtering
- [ ] Optional member count (with performance warning)
- [ ] Multiple output formats
- [ ] Clear permission error messages

**Implementation Notes:**
- Use /groups/picker endpoint (supports query parameter)
- Member count requires separate API call per group (can be slow)
- Add warning if --include-members used with large result set
- Default max_results to 50

**Commits:**
1. `test(jira-admin): add failing tests for list_groups`
2. `feat(jira-admin): implement list_groups.py (8/8 tests passing)`

---

### Feature 2.2.2: Get Group Details & Members

**Script:** `get_group_members.py`

**JIRA API:**
- `GET /rest/api/3/group` - Get group details
- `GET /rest/api/3/group/member` - Get group members (paginated)

**Test File:** `tests/test_get_group_members.py`

**Test Cases:**
```python
def test_get_group_members_by_name():
    """Test getting members by group name."""
    # Should return paginated list of users

def test_get_group_members_by_id():
    """Test getting members by groupId."""
    # Should work with groupId parameter

def test_get_group_members_pagination():
    """Test pagination for large groups."""
    # Should handle groups with many members

def test_get_group_members_empty_group():
    """Test handling group with no members."""
    # Should show "no members" message

def test_get_group_members_include_inactive():
    """Test including inactive users in results."""
    # Should show inactive members when requested

def test_get_group_members_text_format():
    """Test formatted table output."""
    # Should show table with member details

def test_get_group_members_json_output():
    """Test JSON output format."""
    # Should return array of user objects

def test_get_group_members_csv_export():
    """Test CSV export for bulk processing."""
    # Should generate CSV with member details

def test_get_group_not_found():
    """Test handling non-existent group."""
    # Should show clear error message

def test_get_group_members_permission_error():
    """Test handling insufficient permissions."""
    # Should explain permission requirements
```

**CLI Interface:**
```bash
# Get members by group name
python get_group_members.py "jira-developers"

# Get members by group ID
python get_group_members.py --group-id 276f955c-63d7-42c8-9520-92d01dca0625

# Pagination
python get_group_members.py "jira-developers" --start 0 --max-results 50

# Include inactive members
python get_group_members.py "jira-developers" --include-inactive

# Output formats
python get_group_members.py "jira-developers" --output table  # Default
python get_group_members.py "jira-developers" --output json
python get_group_members.py "jira-developers" --output csv > members.csv

# With profile
python get_group_members.py "jira-developers" --profile development
```

**Output Example (table format):**
```
Group: jira-developers
Total Members: 12

Account ID                     Display Name     Email                    Status
5b10ac8d82e05b22cc7d4ef5       John Doe         john.doe@example.com     Active
a1b2c3d4e5f6g7h8i9j0k1l2       Jane Smith       [hidden]                 Active
9z8y7x6w5v4u3t2s1r0q9p8o       Bob Johnson      bob.j@example.com        Active
...
```

**Acceptance Criteria:**
- [ ] All 10 tests pass
- [ ] Supports lookup by group name or groupId
- [ ] Pagination support
- [ ] Optional inclusion of inactive members
- [ ] Handles privacy-restricted user fields
- [ ] Multiple output formats including CSV
- [ ] Clear error for non-existent group

**Implementation Notes:**
- Support both --group-name and --group-id
- Default to active members only
- Use same privacy handling as search_users
- CSV export useful for auditing/reporting

**Commits:**
1. `test(jira-admin): add failing tests for get_group_members`
2. `feat(jira-admin): implement get_group_members.py (10/10 tests passing)`

---

### Feature 2.2.3: Create Group

**Script:** `create_group.py`

**JIRA API:**
- `POST /rest/api/3/group` - Create group

**Required Permission:** Site administration (site-admin group membership)

**Test File:** `tests/test_create_group.py`

**Test Cases:**
```python
def test_create_group_basic():
    """Test creating group with valid name."""
    # Should create group and return details

def test_create_group_name_validation():
    """Test group name validation."""
    # Should reject invalid names (empty, special chars, etc.)

def test_create_group_duplicate_name():
    """Test handling duplicate group name error."""
    # Should provide clear error message

def test_create_group_text_output():
    """Test formatted success output."""
    # Should show created group name and ID

def test_create_group_json_output():
    """Test JSON output format."""
    # Should return group object

def test_create_group_dry_run():
    """Test dry-run mode without creating."""
    # Should validate but not create group

def test_create_group_permission_error():
    """Test handling insufficient permissions."""
    # Should explain 'Site administration' requirement

def test_create_group_naming_conventions():
    """Test various naming patterns."""
    # Should support kebab-case, lowercase, numbers
```

**CLI Interface:**
```bash
# Create group
python create_group.py "new-team"
python create_group.py "project-external-reviewers"

# Dry-run (validation only)
python create_group.py "test-group" --dry-run

# Output formats
python create_group.py "new-team" --output text  # Default
python create_group.py "new-team" --output json

# With profile
python create_group.py "new-team" --profile development
```

**Output Example:**
```
Group created successfully!

Group Name:  new-team
Group ID:    276f955c-63d7-42c8-9520-92d01dca0625
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Name validation before API call
- [ ] Clear error for duplicate names
- [ ] Dry-run mode
- [ ] Multiple output formats
- [ ] Clear permission error messages

**Implementation Notes:**
- Validate group name: non-empty, reasonable length, allowed characters
- JIRA Cloud allows: lowercase, numbers, hyphens, underscores
- Document site-admin permission requirement clearly
- Suggest using lowercase and hyphens for consistency

**Commits:**
1. `test(jira-admin): add failing tests for create_group`
2. `feat(jira-admin): implement create_group.py (8/8 tests passing)`

---

### Feature 2.2.4: Delete Group

**Script:** `delete_group.py`

**JIRA API:**
- `DELETE /rest/api/3/group` - Delete group

**Required Permission:** Site administration

**Test File:** `tests/test_delete_group.py`

**Test Cases:**
```python
def test_delete_group_with_confirmation():
    """Test deleting group with --confirm flag."""
    # Should delete group when confirmed

def test_delete_group_requires_confirmation():
    """Test confirmation is required by default."""
    # Should error without --confirm flag

def test_delete_group_by_name():
    """Test deleting by group name."""
    # Should use groupname parameter

def test_delete_group_by_id():
    """Test deleting by groupId."""
    # Should use groupId parameter

def test_delete_group_not_found():
    """Test handling non-existent group."""
    # Should show clear error message

def test_delete_group_permission_error():
    """Test handling insufficient permissions."""
    # Should explain 'Site administration' requirement

def test_delete_group_dry_run():
    """Test dry-run mode without deleting."""
    # Should validate but not delete

def test_delete_group_with_members_warning():
    """Test warning when deleting group with members."""
    # Should warn about member count before deletion

def test_delete_system_group_protection():
    """Test preventing deletion of system groups."""
    # Should block deletion of jira-administrators, jira-users, etc.
```

**CLI Interface:**
```bash
# Delete group (requires confirmation)
python delete_group.py "old-team" --confirm

# Delete by group ID
python delete_group.py --group-id 276f955c-63d7-42c8-9520-92d01dca0625 --confirm

# Dry-run (validation only)
python delete_group.py "test-group" --dry-run

# With profile
python delete_group.py "old-team" --confirm --profile development
```

**Output Example:**
```
WARNING: You are about to delete group "old-team"
This group has 8 members. They will lose group-based permissions.

Group Name:  old-team
Group ID:    276f955c-63d7-42c8-9520-92d01dca0625

Proceeding with deletion...
Group deleted successfully!
```

**Acceptance Criteria:**
- [ ] All 9 tests pass
- [ ] Requires --confirm flag for safety
- [ ] Supports deletion by name or ID
- [ ] Warns about member count
- [ ] Protects system groups (jira-administrators, etc.)
- [ ] Dry-run mode
- [ ] Clear permission error messages

**Implementation Notes:**
- Fetch group details first to show member count
- Protect system groups: jira-administrators, jira-users, jira-software-users, site-admins
- Make confirmation requirement very clear in help text
- Consider adding --force flag to skip warnings (but still require --confirm)

**Commits:**
1. `test(jira-admin): add failing tests for delete_group`
2. `feat(jira-admin): implement delete_group.py (9/9 tests passing)`

---

## Phase 2.3: Group Membership Management

### Feature 2.3.1: Add User to Group

**Script:** `add_user_to_group.py`

**JIRA API:**
- `POST /rest/api/3/group/user` - Add user to group

**Required Permission:** Site administration

**Test File:** `tests/test_add_user_to_group.py`

**Test Cases:**
```python
def test_add_user_to_group_by_account_id():
    """Test adding user by accountId."""
    # Should add user successfully

def test_add_user_to_group_by_email():
    """Test adding user by email (lookup accountId first)."""
    # Should lookup accountId and add user

def test_add_user_by_group_name():
    """Test specifying group by name."""
    # Should use groupname parameter

def test_add_user_by_group_id():
    """Test specifying group by groupId."""
    # Should use groupId parameter

def test_add_user_already_member():
    """Test handling user already in group."""
    # Should show informative message (idempotent)

def test_add_user_not_found():
    """Test handling non-existent user."""
    # Should show clear error message

def test_add_group_not_found():
    """Test handling non-existent group."""
    # Should show clear error message

def test_add_user_dry_run():
    """Test dry-run mode without adding."""
    # Should validate but not modify group

def test_add_user_permission_error():
    """Test handling insufficient permissions."""
    # Should explain 'Site administration' requirement

def test_add_inactive_user():
    """Test adding inactive user to group."""
    # Should allow but warn about inactive status
```

**CLI Interface:**
```bash
# Add user by email
python add_user_to_group.py john.doe@example.com --group "jira-developers"

# Add user by accountId
python add_user_to_group.py --account-id 5b10ac8d82e05b22cc7d4ef5 --group "jira-developers"

# Specify group by ID
python add_user_to_group.py john@example.com --group-id 276f955c-63d7-42c8-9520-92d01dca0625

# Dry-run
python add_user_to_group.py john@example.com --group "jira-developers" --dry-run

# With profile
python add_user_to_group.py john@example.com --group "jira-developers" --profile development
```

**Output Example:**
```
User added to group successfully!

User:        John Doe (john.doe@example.com)
Account ID:  5b10ac8d82e05b22cc7d4ef5
Group:       jira-developers
```

**Acceptance Criteria:**
- [ ] All 10 tests pass
- [ ] Supports user lookup by email or accountId
- [ ] Supports group lookup by name or ID
- [ ] Idempotent (handles already-member gracefully)
- [ ] Dry-run mode
- [ ] Clear error messages for not found cases
- [ ] Warns about inactive users

**Implementation Notes:**
- If email provided, lookup accountId first via GET /user
- Support both --group (name) and --group-id
- Operation is idempotent - no error if already member
- Fetch and display user details for confirmation

**Commits:**
1. `test(jira-admin): add failing tests for add_user_to_group`
2. `feat(jira-admin): implement add_user_to_group.py (10/10 tests passing)`

---

### Feature 2.3.2: Remove User from Group

**Script:** `remove_user_from_group.py`

**JIRA API:**
- `DELETE /rest/api/3/group/user` - Remove user from group

**Required Permission:** Site administration

**Test File:** `tests/test_remove_user_from_group.py`

**Test Cases:**
```python
def test_remove_user_from_group_by_account_id():
    """Test removing user by accountId."""
    # Should remove user successfully

def test_remove_user_from_group_by_email():
    """Test removing user by email (lookup accountId first)."""
    # Should lookup accountId and remove user

def test_remove_user_by_group_name():
    """Test specifying group by name."""
    # Should use groupname parameter

def test_remove_user_by_group_id():
    """Test specifying group by groupId."""
    # Should use groupId parameter

def test_remove_user_not_member():
    """Test handling user not in group."""
    # Should show informative message (idempotent)

def test_remove_user_not_found():
    """Test handling non-existent user."""
    # Should show clear error message

def test_remove_group_not_found():
    """Test handling non-existent group."""
    # Should show clear error message

def test_remove_user_dry_run():
    """Test dry-run mode without removing."""
    # Should validate but not modify group

def test_remove_user_permission_error():
    """Test handling insufficient permissions."""
    # Should explain 'Site administration' requirement

def test_remove_from_system_group_warning():
    """Test warning when removing from critical groups."""
    # Should warn about removing from jira-administrators
```

**CLI Interface:**
```bash
# Remove user by email
python remove_user_from_group.py john.doe@example.com --group "jira-developers"

# Remove user by accountId
python remove_user_from_group.py --account-id 5b10ac8d82e05b22cc7d4ef5 --group "jira-developers"

# Specify group by ID
python remove_user_from_group.py john@example.com --group-id 276f955c-63d7-42c8-9520-92d01dca0625

# Dry-run
python remove_user_from_group.py john@example.com --group "jira-developers" --dry-run

# With profile
python remove_user_from_group.py john@example.com --group "jira-developers" --profile development
```

**Output Example:**
```
User removed from group successfully!

User:        John Doe (john.doe@example.com)
Account ID:  5b10ac8d82e05b22cc7d4ef5
Group:       jira-developers
```

**Acceptance Criteria:**
- [ ] All 10 tests pass
- [ ] Supports user lookup by email or accountId
- [ ] Supports group lookup by name or ID
- [ ] Idempotent (handles not-member gracefully)
- [ ] Dry-run mode
- [ ] Warns when removing from critical groups
- [ ] Clear error messages

**Implementation Notes:**
- Mirror add_user_to_group functionality
- Warn when removing from jira-administrators or site-admins
- Operation is idempotent - no error if not a member
- Consider requiring --confirm for system groups

**Commits:**
1. `test(jira-admin): add failing tests for remove_user_from_group`
2. `feat(jira-admin): implement remove_user_from_group.py (10/10 tests passing)`

---

## Phase 2 Completion Summary

### Scripts Implemented
- [ ] `search_users.py` - Search users by name/email (14 tests)
- [ ] `get_user.py` - Get user details (12 tests)
- [ ] `list_groups.py` - List/search groups (8 tests)
- [ ] `get_group_members.py` - Get group members (10 tests)
- [ ] `create_group.py` - Create new group (8 tests)
- [ ] `delete_group.py` - Delete group (9 tests)
- [ ] `add_user_to_group.py` - Add user to group (10 tests)
- [ ] `remove_user_from_group.py` - Remove user from group (10 tests)

**Total:** 8 scripts, 81 tests

### Shared Library Updates
- [ ] User management methods in JiraClient (6 methods)
- [ ] Group management methods in JiraClient (7 methods)
- [ ] Enhanced error handling for user/group operations
- [ ] Privacy control handling utilities

### Final Phase 2 Commit
- [ ] **Commit:** `docs(jira-admin): complete Phase 2 - User & Group Management (8 scripts, 81 tests passing)`

---

## Integration & Documentation

### Integration with Other Skills

**jira-issue (Assignee Management):**
- `create_issue.py --assignee` can use email lookup from get_user
- Validate assignable users with search_users --assignable

**jira-search (User-based JQL):**
- Generate JQL with accountId from user email lookups
- Validate user references in saved filters

**jira-admin Phase 3 (Permission Schemes):**
- Permission grants reference groups created here
- Validate groups exist before assigning permissions

### Documentation Updates

- [ ] **Update SKILL.md for jira-admin:**
  - Add Phase 2 scripts to "Available Scripts" section
  - Include usage examples
  - Document permission requirements
  - Add GDPR/privacy considerations section

- [ ] **Update CLAUDE.md:**
  - Add user/group management patterns
  - Document accountId requirement
  - Add privacy control handling examples

- [ ] **Create PRIVACY_GUIDE.md:**
  - Explain GDPR compliance
  - Document privacy control handling
  - Provide examples of privacy-restricted responses
  - Explain "unknown" accountId

### Example Use Cases

**Onboarding New Team:**
```bash
# 1. Create team group
python create_group.py "mobile-team"

# 2. Add team members
python add_user_to_group.py alice@example.com --group "mobile-team"
python add_user_to_group.py bob@example.com --group "mobile-team"

# 3. Verify membership
python get_group_members.py "mobile-team"
```

**Team Transition:**
```bash
# 1. Find user
python search_users.py "john.doe@example.com"

# 2. Remove from old team
python remove_user_from_group.py john.doe@example.com --group "backend-team"

# 3. Add to new team
python add_user_to_group.py john.doe@example.com --group "frontend-team"

# 4. Verify groups
python get_user.py --email john.doe@example.com --include-groups
```

**Audit Team Membership:**
```bash
# 1. Export all groups
python list_groups.py --output json > groups.json

# 2. Export members for each team
python get_group_members.py "jira-administrators" --output csv > admin-members.csv
python get_group_members.py "jira-developers" --output csv > dev-members.csv

# 3. Find assignable users for project
python search_users.py "" --project PROJ --assignable --output csv > assignable.csv
```

---

## GDPR & Privacy Compliance

### Privacy Controls Implementation

**Field Visibility:**
- Email address - May be hidden
- Time zone - May be hidden
- Locale - May be hidden
- Display name - Usually visible (minimal profile info)

**Handling Strategy:**
```python
def format_user_field(field_value, field_name):
    """Format user field with privacy controls."""
    if field_value is None or field_value == "":
        return f"[hidden - privacy settings]"
    return field_value

# Example output
user = get_user(account_id)
print(f"Email: {format_user_field(user.get('emailAddress'), 'email')}")
```

### Special Account IDs

**"unknown" Account:**
- Represents deleted or anonymized users
- Don't attempt to fetch personal data
- Display as "Deleted User" or "Unknown User"
- Don't include in personal data reports

**Deleted Users (Right to be Forgotten):**
- displayName shows deletion indicator
- Other fields blank or default
- accountId still present for referential integrity

### Best Practices

1. **Don't Cache Personal Data:** Always fetch fresh from API to respect current privacy settings

2. **Graceful Degradation:** Applications should work even if email/name hidden

3. **Clear User Communication:** Explain when fields are hidden and why

4. **Audit Logging:** Log group membership changes with accountId only

5. **Email Lookup Limitations:** Searching by email may fail if user hides email

### Compliance Notes

- This implementation respects GDPR privacy controls
- No local caching of personal data
- All lookups use current API data
- Privacy restrictions clearly communicated to user
- "Unknown" accounts handled appropriately

---

## Testing Strategy

### Unit Tests (pytest)

**Coverage Target:** 85%+

**Test Categories:**
1. **Happy Path:** Normal operations with valid data
2. **Validation:** Input validation before API calls
3. **Error Handling:** API errors, not found, permission denied
4. **Privacy Controls:** Handling hidden/restricted fields
5. **Edge Cases:** Empty results, special characters, inactive users
6. **Output Formats:** Table, JSON, CSV formatting
7. **Dry-run:** Validation without mutation

### Mock Strategy

**Mock External API Calls:**
```python
@pytest.fixture
def mock_jira_client(mocker):
    """Mock JiraClient for testing."""
    client = mocker.Mock()
    client.search_users.return_value = [
        {
            "accountId": "123",
            "displayName": "John Doe",
            "emailAddress": "john@example.com",
            "active": True
        }
    ]
    return client
```

**Use responses library for HTTP:**
```python
import responses

@responses.activate
def test_search_users_api():
    """Test actual HTTP request/response."""
    responses.add(
        responses.GET,
        "https://site.atlassian.net/rest/api/3/user/search",
        json=[{"accountId": "123", "displayName": "John"}],
        status=200
    )
    # Test code
```

### Live Integration Tests

**Optional Live Tests:**
- Create test group "integration-test-group"
- Add/remove test users
- Clean up after tests
- Require --live flag to run
- Document in tests/live_integration/README.md

### Test Fixtures

**Common Fixtures (conftest.py):**
```python
@pytest.fixture
def sample_user():
    """Sample user object for testing."""
    return {
        "accountId": "5b10ac8d82e05b22cc7d4ef5",
        "displayName": "John Doe",
        "emailAddress": "john.doe@example.com",
        "active": True,
        "timeZone": "America/New_York",
        "locale": "en-US"
    }

@pytest.fixture
def sample_group():
    """Sample group object for testing."""
    return {
        "name": "jira-developers",
        "groupId": "276f955c-63d7-42c8-9520-92d01dca0625"
    }

@pytest.fixture
def privacy_restricted_user():
    """User with privacy controls enabled."""
    return {
        "accountId": "a1b2c3d4e5f6g7h8i9j0k1l2",
        "displayName": "Jane Smith",
        "active": True
        # Note: email, timeZone, locale are missing
    }
```

---

## Permission Requirements

### Global Permissions

**Browse Users and Groups:**
- Required for: All user/group read operations
- Allows: Searching users, listing groups, viewing members
- Does NOT allow: Creating/deleting groups, modifying membership

**Site Administration:**
- Required for: All group write operations
- Allows: Create/delete groups, add/remove members
- Members: Users in site-admins group
- Critical: Most powerful permission in JIRA Cloud

### Permission Validation

**Pre-flight Checks:**
Scripts should provide clear permission error messages:

```
Error: Insufficient Permissions

This operation requires 'Site administration' permission.

You need to be a member of one of these groups:
  - site-admins

Current permissions: Browse users and groups

Please contact your JIRA administrator to request access.
```

### Permission Hierarchy

```
Site Administration (site-admins)
  └─ Can do everything below PLUS:
     - Create/delete groups
     - Add/remove group members
     - Modify user attributes (limited)

Browse Users and Groups
  └─ Can:
     - Search and view users
     - List groups
     - View group members
     - Get user/group details

Authenticated User (no special permissions)
  └─ Can:
     - View own profile (/myself)
     - Limited user search (may be restricted)
```

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Privacy controls hide critical fields | High | Medium | Graceful degradation, clear messaging |
| Email lookup fails due to privacy | Medium | Low | Support accountId as primary identifier |
| Permission denied errors | Medium | Medium | Clear permission requirement docs |
| Rate limiting on bulk operations | Low | Low | Implement pagination, respect rate limits |
| GDPR compliance complexity | Medium | High | Follow Atlassian guidelines, test thoroughly |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Accidental group deletion | Medium | High | Require --confirm, protect system groups |
| Removing admin from admin group | Low | High | Warn on system group modifications |
| Privacy violation through logging | Low | High | Log accountId only, not personal data |
| Mass membership changes | Low | Medium | Dry-run mode, clear confirmation messages |

### Security Considerations

**API Token Security:**
- Never log API tokens
- Use environment variables only
- Document secure credential management

**Audit Trail:**
- Log all group modifications (using accountId)
- Include timestamp and operator accountId
- Don't log personal data (names, emails)

**Least Privilege:**
- Document minimum required permissions
- Recommend dedicated service accounts for automation
- Avoid using admin accounts for routine operations

---

## Future Enhancements

### Phase 2.5 Potential Features

**Bulk Operations:**
- `bulk_add_users.py` - Add multiple users to group from CSV
- `bulk_remove_users.py` - Remove multiple users
- `sync_group_membership.py` - Sync members from external source

**Advanced Queries:**
- `find_users_without_groups.py` - Users not in any group
- `find_orphaned_groups.py` - Empty groups
- `compare_groups.py` - Compare membership between groups

**Reporting:**
- `generate_user_report.py` - User access audit report
- `generate_group_report.py` - Group membership report
- `export_org_structure.py` - Full org structure export

**Integration:**
- `sync_ldap_groups.py` - Sync with LDAP/AD
- `validate_access.py` - Validate user access across projects

### Not Implemented (Cloud Limitations)

**User Creation/Deactivation:**
- Requires Cloud Admin API (different auth)
- Requires organization-level admin access
- Out of scope for jira-admin skill
- Document as limitation

**Advanced User Management:**
- Password reset - Not available via API
- Account settings - Limited API access
- Product access - Requires Cloud Admin API
- License management - Requires Cloud Admin API

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 81 unit tests passing
- [ ] Coverage ≥ 85%
- [ ] All edge cases covered
- [ ] Privacy controls tested

**Scripts:**
- [ ] 8 scripts fully implemented
- [ ] All scripts have --help
- [ ] All scripts support --profile
- [ ] All mutation scripts have --dry-run
- [ ] All scripts have multiple output formats

**Code Quality:**
- [ ] Follows existing patterns from other skills
- [ ] Consistent error handling
- [ ] Clear, descriptive help text
- [ ] Privacy-aware output formatting

**Documentation:**
- [ ] SKILL.md updated with Phase 2 scripts
- [ ] CLAUDE.md updated with user/group patterns
- [ ] PRIVACY_GUIDE.md created
- [ ] Permission requirements documented
- [ ] Example use cases provided

**Performance:**
- [ ] Pagination implemented for large results
- [ ] Efficient API usage (minimal calls)
- [ ] Handles rate limits gracefully
- [ ] Warns about slow operations (member counts)

---

## Implementation Timeline

### Estimated Effort

| Phase | Scripts | Tests | Estimated Hours |
|-------|---------|-------|-----------------|
| Setup (JiraClient + fixtures) | 0 | 0 | 4h |
| 2.1: User Search & Retrieval | 2 | 26 | 8h |
| 2.2: Group CRUD Operations | 4 | 35 | 12h |
| 2.3: Group Membership | 2 | 20 | 6h |
| Documentation | 0 | 0 | 4h |
| **Total** | **8** | **81** | **34h** |

### Recommended Approach

**Week 1: Foundation**
- Day 1-2: Setup JiraClient methods, test infrastructure
- Day 3-4: Implement user search & retrieval
- Day 5: Testing and refinement

**Week 2: Group Operations**
- Day 1-2: List and get group operations
- Day 3-4: Create and delete group operations
- Day 5: Testing and refinement

**Week 3: Membership & Polish**
- Day 1-2: Add/remove membership operations
- Day 3: Integration testing
- Day 4: Documentation
- Day 5: Final review and commit

---

## Appendix: API Examples

### Search Users Example

**Request:**
```bash
GET /rest/api/3/user/search?query=john&maxResults=10
Authorization: Basic <base64(email:token)>
```

**Response:**
```json
[
  {
    "accountId": "5b10ac8d82e05b22cc7d4ef5",
    "accountType": "atlassian",
    "displayName": "John Doe",
    "emailAddress": "john.doe@example.com",
    "active": true,
    "timeZone": "America/New_York",
    "avatarUrls": {
      "48x48": "https://avatar.url/48x48",
      "24x24": "https://avatar.url/24x24"
    }
  }
]
```

### Get User Example

**Request:**
```bash
GET /rest/api/3/user?accountId=5b10ac8d82e05b22cc7d4ef5&expand=groups
Authorization: Basic <base64(email:token)>
```

**Response:**
```json
{
  "accountId": "5b10ac8d82e05b22cc7d4ef5",
  "accountType": "atlassian",
  "displayName": "John Doe",
  "emailAddress": "john.doe@example.com",
  "active": true,
  "timeZone": "America/New_York",
  "locale": "en-US",
  "groups": {
    "size": 3,
    "items": [
      {
        "name": "jira-users",
        "groupId": "group-id-1"
      },
      {
        "name": "jira-developers",
        "groupId": "group-id-2"
      }
    ]
  }
}
```

### Create Group Example

**Request:**
```bash
POST /rest/api/3/group
Content-Type: application/json
Authorization: Basic <base64(email:token)>

{
  "name": "jira-mobile-team"
}
```

**Response:**
```json
{
  "name": "jira-mobile-team",
  "groupId": "276f955c-63d7-42c8-9520-92d01dca0625",
  "self": "https://site.atlassian.net/rest/api/3/group?groupId=276f955c-63d7-42c8-9520-92d01dca0625"
}
```

### Add User to Group Example

**Request:**
```bash
POST /rest/api/3/group/user?groupname=jira-developers
Content-Type: application/json
Authorization: Basic <base64(email:token)>

{
  "accountId": "5b10ac8d82e05b22cc7d4ef5"
}
```

**Response:**
```json
{
  "name": "jira-developers",
  "groupId": "276f955c-63d7-42c8-9520-92d01dca0625",
  "self": "https://site.atlassian.net/rest/api/3/group?groupId=276f955c-63d7-42c8-9520-92d01dca0625"
}
```

### Get Group Members Example

**Request:**
```bash
GET /rest/api/3/group/member?groupname=jira-developers&startAt=0&maxResults=50
Authorization: Basic <base64(email:token)>
```

**Response:**
```json
{
  "self": "https://site.atlassian.net/rest/api/3/group/member",
  "maxResults": 50,
  "startAt": 0,
  "total": 3,
  "isLast": true,
  "values": [
    {
      "accountId": "5b10ac8d82e05b22cc7d4ef5",
      "displayName": "John Doe",
      "emailAddress": "john.doe@example.com",
      "active": true
    },
    {
      "accountId": "a1b2c3d4e5f6g7h8i9j0k1l2",
      "displayName": "Jane Smith",
      "active": true
      // Note: emailAddress missing due to privacy controls
    }
  ]
}
```

---

## References

### Official Documentation

- [Jira Cloud REST API v3 - Users](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-users/)
- [Jira Cloud REST API v3 - Groups](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-groups/)
- [User Privacy Developer Guide](https://developer.atlassian.com/cloud/jira/platform/user-privacy-developer-guide/)
- [GDPR Migration Guide](https://developer.atlassian.com/cloud/jira/platform/deprecation-notice-user-privacy-api-migration-guide/)
- [User Management Differences (Cloud vs Server)](https://support.atlassian.com/migration/docs/user-management-differences-in-cloud-and-server/)

### Internal Documentation

- `.claude/skills/shared/scripts/lib/jira_client.py` - HTTP client implementation
- `.claude/skills/shared/scripts/lib/error_handler.py` - Error handling patterns
- `CLAUDE.md` - Project patterns and conventions
- `docs/implementation-plans/ADMINISTRATION_IMPLEMENTATION_PLAN.md` - Master admin plan

---

**Document Version:** 1.0
**Created:** 2025-12-26
**Status:** Ready for Implementation
**Author:** Claude (Strategic Planning Agent)
