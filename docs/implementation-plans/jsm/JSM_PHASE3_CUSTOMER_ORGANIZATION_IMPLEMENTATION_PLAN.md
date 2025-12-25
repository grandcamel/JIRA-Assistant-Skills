# JIRA Service Management Phase 3: Customer & Organization Management - TDD Implementation Plan

## Overview

**Objective:** Implement comprehensive customer and organization management for JSM using Test-Driven Development (TDD)

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
- **Test Location:** `.claude/skills/jira-jsm/tests/`

**Feature Priority:**
1. **Phase 3.1: Customer CRUD** (Create, list, add/remove customers)
2. **Phase 3.2: Organization CRUD** (Create, list, get, delete organizations)
3. **Phase 3.3: Organization Membership** (Add/remove users from organizations)
4. **Phase 3.4: Request Participants** (Get, add, remove request participants)

**Dependencies:**
- Phase 1 (Service Desk & Request Types) - Must be completed first
- Phase 2 (Request Management) - Must be completed first
- Shared JiraClient library with JSM support

---

## JIRA API Reference

### Service Desk API Base
**Base URL:** `/rest/servicedeskapi`

### Customer Management Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/customer` | Create customer account |
| GET | `/servicedesk/{id}/customer` | List customers for service desk |
| POST | `/servicedesk/{id}/customer` | Add customer(s) to service desk |
| DELETE | `/servicedesk/{id}/customer` | Remove customer(s) from service desk |

### Organization Management Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/organization` | List all organizations |
| POST | `/organization` | Create organization |
| GET | `/organization/{id}` | Get organization details |
| DELETE | `/organization/{id}` | Delete organization |
| GET | `/organization/{id}/user` | List users in organization |
| POST | `/organization/{id}/user` | Add users to organization |
| DELETE | `/organization/{id}/user` | Remove users from organization |
| GET | `/servicedesk/{id}/organization` | Get organizations for service desk |
| POST | `/servicedesk/{id}/organization` | Add organization to service desk |
| DELETE | `/servicedesk/{id}/organization` | Remove organization from service desk |

### Request Participants Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/request/{key}/participant` | Get request participants |
| POST | `/request/{key}/participant` | Add participant(s) to request |
| DELETE | `/request/{key}/participant` | Remove participant(s) from request |

### Data Structures

#### Create Customer Payload
```json
{
  "email": "customer@example.com",
  "displayName": "John Customer"
}
```

#### Add Customer to Service Desk
```json
{
  "accountIds": [
    "5b10ac8d82e05b22cc7d4ef5",
    "5b109f2e9729b51b54dc274d"
  ]
}
```

#### Create Organization
```json
{
  "name": "Example Organization"
}
```

#### Add Users to Organization
```json
{
  "accountIds": [
    "5b10ac8d82e05b22cc7d4ef5"
  ]
}
```

#### Add Participants
```json
{
  "accountIds": [
    "5b10ac8d82e05b22cc7d4ef5"
  ],
  "usernames": []
}
```

---

## Test Infrastructure Setup

### Initial Setup Tasks

- [ ] **Setup 3.1:** Create test infrastructure for Phase 3
  - [ ] Create `tests/test_customers.py` skeleton
  - [ ] Create `tests/test_organizations.py` skeleton
  - [ ] Create `tests/test_participants.py` skeleton
  - [ ] Add customer fixtures to `tests/conftest.py`
  - [ ] Add organization fixtures to `tests/conftest.py`
  - **Commit:** `test(jira-jsm): add Phase 3 test infrastructure`

- [ ] **Setup 3.2:** Add JiraClient methods for customers
  - [ ] `create_customer(email, display_name)` - Create customer
  - [ ] `get_service_desk_customers(service_desk_id, query)` - List customers
  - [ ] `add_customers_to_service_desk(service_desk_id, account_ids)` - Add customers
  - [ ] `remove_customers_from_service_desk(service_desk_id, account_ids)` - Remove customers
  - **Commit:** `feat(shared): add customer management methods to JiraClient`

- [ ] **Setup 3.3:** Add JiraClient methods for organizations
  - [ ] `get_organizations(start, limit)` - List organizations
  - [ ] `create_organization(name)` - Create organization
  - [ ] `get_organization(organization_id)` - Get organization details
  - [ ] `delete_organization(organization_id)` - Delete organization
  - [ ] `get_organization_users(organization_id, start, limit)` - List users
  - [ ] `add_users_to_organization(organization_id, account_ids)` - Add users
  - [ ] `remove_users_from_organization(organization_id, account_ids)` - Remove users
  - [ ] `get_service_desk_organizations(service_desk_id, start, limit)` - List SD orgs
  - [ ] `add_organization_to_service_desk(service_desk_id, organization_id)` - Add org
  - [ ] `remove_organization_from_service_desk(service_desk_id, organization_id)` - Remove org
  - **Commit:** `feat(shared): add organization management methods to JiraClient`

- [ ] **Setup 3.4:** Add JiraClient methods for participants
  - [ ] `get_request_participants(issue_key, start, limit)` - Get participants
  - [ ] `add_request_participants(issue_key, account_ids, usernames)` - Add participants
  - [ ] `remove_request_participants(issue_key, account_ids, usernames)` - Remove participants
  - **Commit:** `feat(shared): add request participant methods to JiraClient`

---

## Phase 3.1: Customer CRUD Operations

### Feature 3.1.1: Create Customer

**Script:** `create_customer.py`

**JIRA API:**
- `POST /rest/servicedeskapi/customer`

**Test File:** `tests/test_create_customer.py`

**Test Cases:**
```python
def test_create_customer_basic():
    """Test creating customer with email and display name."""
    # Should create customer and return account ID

def test_create_customer_email_validation():
    """Test email format validation before API call."""
    # Should reject invalid email addresses

def test_create_customer_duplicate_email():
    """Test handling duplicate email error."""
    # Should provide clear error message

def test_create_customer_missing_display_name():
    """Test creating customer with email only (display name derived)."""
    # Should use email as display name if not provided

def test_create_customer_special_characters():
    """Test customer names with special characters."""
    # Should handle unicode, apostrophes, etc.

def test_create_customer_json_output():
    """Test JSON output format with account ID."""
    # Should return accountId, emailAddress, displayName

def test_create_customer_invalid_email():
    """Test error on invalid email format."""
    # Should validate email before API call

def test_create_customer_network_error():
    """Test handling network/API errors gracefully."""
    # Should provide user-friendly error message

def test_create_customer_permission_error():
    """Test handling insufficient permissions."""
    # Should explain permission requirements

def test_create_customer_verbose_output():
    """Test verbose mode showing full API response."""
    # Should show all returned fields in verbose mode
```

**CLI Interface:**
```bash
# Create customer
python create_customer.py --email customer@example.com --name "John Customer"
python create_customer.py --email jane@example.com  # Uses email as name

# Output formats
python create_customer.py --email user@example.com --output json
python create_customer.py --email user@example.com --verbose

# Dry-run
python create_customer.py --email test@example.com --dry-run
```

**Output Example:**
```
Customer created successfully!

Account ID:   5b10ac8d82e05b22cc7d4ef5
Email:        customer@example.com
Display Name: John Customer
```

**Acceptance Criteria:**
- [ ] All 10 tests pass
- [ ] Email validation before API call
- [ ] Clear error messages for common failures
- [ ] JSON output option
- [ ] Dry-run mode
- [ ] Verbose mode

**Commits:**
1. `test(jira-jsm): add failing tests for create_customer`
2. `feat(jira-jsm): implement create_customer.py (10/10 tests passing)`

---

### Feature 3.1.2: List Service Desk Customers

**Script:** `list_customers.py`

**JIRA API:**
- `GET /rest/servicedeskapi/servicedesk/{id}/customer`

**Test File:** `tests/test_list_customers.py`

**Test Cases:**
```python
def test_list_all_customers():
    """Test listing all customers for service desk."""
    # Should return list of customers with pagination

def test_list_customers_with_query():
    """Test filtering customers by email/name search."""
    # Should support query parameter

def test_list_customers_pagination():
    """Test pagination with start and limit."""
    # Should handle large customer lists

def test_list_customers_empty_service_desk():
    """Test output when no customers exist."""
    # Should show clear "no customers" message

def test_list_customers_text_format():
    """Test formatted table output."""
    # Should show table with email, name, active status

def test_list_customers_json_format():
    """Test JSON output with all fields."""
    # Should return full customer objects

def test_list_customers_service_desk_not_found():
    """Test error when service desk doesn't exist."""
    # Should provide clear error message

def test_list_customers_count_only():
    """Test getting customer count without details."""
    # Should support --count flag

def test_list_customers_export_csv():
    """Test exporting customer list to CSV."""
    # Should generate CSV with headers

def test_list_customers_filter_active():
    """Test filtering to show only active customers."""
    # Should support --active-only flag
```

**CLI Interface:**
```bash
# List all customers
python list_customers.py SERVICE-DESK-1
python list_customers.py SERVICE-DESK-1 --query "john"
python list_customers.py SERVICE-DESK-1 --query "example.com"

# Pagination
python list_customers.py SERVICE-DESK-1 --start 0 --limit 50
python list_customers.py SERVICE-DESK-1 --all  # Get all pages

# Output formats
python list_customers.py SERVICE-DESK-1 --output json
python list_customers.py SERVICE-DESK-1 --output csv > customers.csv
python list_customers.py SERVICE-DESK-1 --count

# Filtering
python list_customers.py SERVICE-DESK-1 --active-only
```

**Output Example:**
```
Customers for Service Desk: IT Help Desk (SERVICE-DESK-1)

Email                    Display Name          Active
─────────────────────────────────────────────────────────
john@example.com         John Customer         Yes
jane@example.com         Jane Smith            Yes
test@example.com         Test User             No

Total: 3 customers (2 active)
```

**Acceptance Criteria:**
- [ ] All 10 tests pass
- [ ] Pagination support
- [ ] Search/query filtering
- [ ] Multiple output formats (text, JSON, CSV)
- [ ] Customer count option
- [ ] Active status filtering

**Commits:**
1. `test(jira-jsm): add failing tests for list_customers`
2. `feat(jira-jsm): implement list_customers.py (10/10 tests passing)`

---

### Feature 3.1.3: Add Customer to Service Desk

**Script:** `add_customer.py`

**JIRA API:**
- `POST /rest/servicedeskapi/servicedesk/{id}/customer`

**Test File:** `tests/test_add_customer.py`

**Test Cases:**
```python
def test_add_single_customer():
    """Test adding single customer by account ID."""
    # Should add customer to service desk

def test_add_multiple_customers():
    """Test adding multiple customers at once."""
    # Should support comma-separated account IDs

def test_add_customer_by_email():
    """Test looking up account ID by email and adding."""
    # Should support --email flag with lookup

def test_add_customer_already_exists():
    """Test handling when customer already in service desk."""
    # Should skip or warn, not error

def test_add_customer_dry_run():
    """Test preview without making changes."""
    # Should show what would be added

def test_add_customer_invalid_account_id():
    """Test error on non-existent account ID."""
    # Should provide clear error message

def test_add_customer_service_desk_not_found():
    """Test error when service desk doesn't exist."""
    # Should validate service desk first

def test_add_customer_permission_error():
    """Test handling insufficient permissions."""
    # Should explain required permissions

def test_add_customer_bulk_from_file():
    """Test adding customers from file (one per line)."""
    # Should support --from-file option

def test_add_customer_progress_indicator():
    """Test progress indicator for bulk operations."""
    # Should show progress for multiple adds
```

**CLI Interface:**
```bash
# Add by account ID
python add_customer.py SERVICE-DESK-1 --account-id 5b10ac8d82e05b22cc7d4ef5
python add_customer.py SERVICE-DESK-1 --account-id "5b10ac8d,5b109f2e"

# Add by email (requires lookup)
python add_customer.py SERVICE-DESK-1 --email customer@example.com
python add_customer.py SERVICE-DESK-1 --email "john@example.com,jane@example.com"

# Bulk operations
python add_customer.py SERVICE-DESK-1 --from-file customers.txt
python add_customer.py SERVICE-DESK-1 --account-id "id1,id2,id3" --dry-run

# Options
python add_customer.py SERVICE-DESK-1 --email user@example.com --skip-existing
python add_customer.py SERVICE-DESK-1 --from-file customers.txt --progress
```

**Acceptance Criteria:**
- [ ] All 10 tests pass
- [ ] Single and bulk customer addition
- [ ] Email-based lookup
- [ ] File-based bulk import
- [ ] Dry-run mode
- [ ] Skip existing customers
- [ ] Progress indicator

**Commits:**
1. `test(jira-jsm): add failing tests for add_customer`
2. `feat(jira-jsm): implement add_customer.py (10/10 tests passing)`

---

### Feature 3.1.4: Remove Customer from Service Desk

**Script:** `remove_customer.py`

**JIRA API:**
- `DELETE /rest/servicedeskapi/servicedesk/{id}/customer`

**Test File:** `tests/test_remove_customer.py`

**Test Cases:**
```python
def test_remove_single_customer():
    """Test removing single customer by account ID."""
    # Should remove customer from service desk

def test_remove_multiple_customers():
    """Test removing multiple customers at once."""
    # Should support comma-separated account IDs

def test_remove_customer_by_email():
    """Test looking up account ID by email and removing."""
    # Should support --email flag with lookup

def test_remove_customer_not_in_service_desk():
    """Test handling when customer not in service desk."""
    # Should warn but not error

def test_remove_customer_confirmation():
    """Test confirmation prompt before removal."""
    # Should require --yes or interactive confirmation

def test_remove_customer_dry_run():
    """Test preview without making changes."""
    # Should show what would be removed

def test_remove_customer_with_active_requests():
    """Test warning when customer has active requests."""
    # Should warn but allow with confirmation

def test_remove_customer_bulk_from_file():
    """Test removing customers from file."""
    # Should support --from-file option
```

**CLI Interface:**
```bash
# Remove by account ID
python remove_customer.py SERVICE-DESK-1 --account-id 5b10ac8d82e05b22cc7d4ef5
python remove_customer.py SERVICE-DESK-1 --account-id "id1,id2" --yes

# Remove by email
python remove_customer.py SERVICE-DESK-1 --email customer@example.com
python remove_customer.py SERVICE-DESK-1 --email "user1@ex.com,user2@ex.com"

# Bulk operations
python remove_customer.py SERVICE-DESK-1 --from-file remove-list.txt --yes

# Safety options
python remove_customer.py SERVICE-DESK-1 --account-id 5b10ac8d --dry-run
python remove_customer.py SERVICE-DESK-1 --email user@ex.com --yes  # Skip confirmation
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Single and bulk customer removal
- [ ] Email-based lookup
- [ ] File-based bulk removal
- [ ] Confirmation prompts
- [ ] Dry-run mode
- [ ] Warning for active requests

**Commits:**
1. `test(jira-jsm): add failing tests for remove_customer`
2. `feat(jira-jsm): implement remove_customer.py (8/8 tests passing)`

---

### Phase 3.1 Completion

- [ ] **Phase 3.1 Summary:**
  - [ ] 4 scripts implemented (create_customer, list_customers, add_customer, remove_customer)
  - [ ] 38 tests passing (38 total)
  - [ ] All scripts have --dry-run mode
  - [ ] Email lookup support
  - [ ] Bulk operations support
  - **Commit:** `docs(jira-jsm): complete Phase 3.1 - Customer CRUD`

---

## Phase 3.2: Organization CRUD Operations

### Feature 3.2.1: List Organizations

**Script:** `list_organizations.py`

**JIRA API:**
- `GET /rest/servicedeskapi/organization`
- `GET /rest/servicedeskapi/servicedesk/{id}/organization`

**Test File:** `tests/test_list_organizations.py`

**Test Cases:**
```python
def test_list_all_organizations():
    """Test listing all organizations."""
    # Should return all organizations with pagination

def test_list_organizations_for_service_desk():
    """Test listing organizations for specific service desk."""
    # Should filter by service desk ID

def test_list_organizations_pagination():
    """Test pagination with start and limit."""
    # Should handle large organization lists

def test_list_organizations_empty():
    """Test output when no organizations exist."""
    # Should show clear "no organizations" message

def test_list_organizations_text_format():
    """Test formatted table output."""
    # Should show ID, name, user count

def test_list_organizations_json_format():
    """Test JSON output with all fields."""
    # Should return full organization objects

def test_list_organizations_count_only():
    """Test getting organization count."""
    # Should support --count flag

def test_list_organizations_with_user_counts():
    """Test showing user counts for each organization."""
    # Should fetch and display user counts

def test_list_organizations_export_csv():
    """Test exporting organization list to CSV."""
    # Should generate CSV output

def test_list_organizations_filter_by_name():
    """Test filtering organizations by name pattern."""
    # Should support name search/filter
```

**CLI Interface:**
```bash
# List all organizations
python list_organizations.py
python list_organizations.py --all  # All pages

# List for specific service desk
python list_organizations.py --service-desk SERVICE-DESK-1

# Pagination
python list_organizations.py --start 0 --limit 25

# Output formats
python list_organizations.py --output json
python list_organizations.py --output csv > orgs.csv
python list_organizations.py --count

# Filtering
python list_organizations.py --filter "Acme"
python list_organizations.py --with-user-counts
```

**Output Example:**
```
Organizations:

ID      Name                      Users    Service Desks
─────────────────────────────────────────────────────────
1       Acme Corporation          45       IT Support, HR
2       Beta Industries           12       IT Support
3       Gamma Enterprises         8        HR

Total: 3 organizations
```

**Acceptance Criteria:**
- [ ] All 10 tests pass
- [ ] List all or service desk-specific organizations
- [ ] Pagination support
- [ ] Multiple output formats
- [ ] User count display
- [ ] Name filtering

**Commits:**
1. `test(jira-jsm): add failing tests for list_organizations`
2. `feat(jira-jsm): implement list_organizations.py (10/10 tests passing)`

---

### Feature 3.2.2: Create Organization

**Script:** `create_organization.py`

**JIRA API:**
- `POST /rest/servicedeskapi/organization`

**Test File:** `tests/test_create_organization.py`

**Test Cases:**
```python
def test_create_organization_basic():
    """Test creating organization with name."""
    # Should create organization and return ID

def test_create_organization_duplicate_name():
    """Test handling duplicate organization name."""
    # Should allow (JSM allows duplicates)

def test_create_organization_name_validation():
    """Test name validation (length, characters)."""
    # Should validate name before API call

def test_create_organization_json_output():
    """Test JSON output with organization ID."""
    # Should return id, name, links

def test_create_organization_verbose_output():
    """Test verbose mode showing full response."""
    # Should show all returned fields

def test_create_organization_add_to_service_desk():
    """Test creating and immediately adding to service desk."""
    # Should support --add-to-service-desk flag

def test_create_organization_with_users():
    """Test creating organization and adding initial users."""
    # Should support --add-users flag

def test_create_organization_permission_error():
    """Test handling insufficient permissions."""
    # Should explain permission requirements

def test_create_organization_dry_run():
    """Test preview without creating."""
    # Should show what would be created

def test_create_organization_network_error():
    """Test handling API errors gracefully."""
    # Should provide user-friendly error message
```

**CLI Interface:**
```bash
# Create organization
python create_organization.py --name "Acme Corporation"

# Create and add to service desk
python create_organization.py --name "Beta Industries" --add-to-service-desk SERVICE-DESK-1

# Create with initial users
python create_organization.py --name "Gamma" --add-users "user1@ex.com,user2@ex.com"

# Output formats
python create_organization.py --name "Delta Corp" --output json
python create_organization.py --name "Test Org" --verbose

# Dry-run
python create_organization.py --name "Example" --dry-run
```

**Output Example:**
```
Organization created successfully!

ID:   12345
Name: Acme Corporation
```

**Acceptance Criteria:**
- [ ] All 10 tests pass
- [ ] Name validation
- [ ] JSON output option
- [ ] Add to service desk on creation
- [ ] Add initial users on creation
- [ ] Dry-run mode
- [ ] Verbose mode

**Commits:**
1. `test(jira-jsm): add failing tests for create_organization`
2. `feat(jira-jsm): implement create_organization.py (10/10 tests passing)`

---

### Feature 3.2.3: Get Organization Details

**Script:** `get_organization.py`

**JIRA API:**
- `GET /rest/servicedeskapi/organization/{id}`
- `GET /rest/servicedeskapi/organization/{id}/user`

**Test File:** `tests/test_get_organization.py`

**Test Cases:**
```python
def test_get_organization_basic():
    """Test getting organization details by ID."""
    # Should return organization info

def test_get_organization_with_users():
    """Test getting organization with user list."""
    # Should support --show-users flag

def test_get_organization_text_format():
    """Test formatted text output."""
    # Should show ID, name, user count

def test_get_organization_json_format():
    """Test JSON output with all fields."""
    # Should return full organization object

def test_get_organization_not_found():
    """Test error when organization doesn't exist."""
    # Should provide clear error message

def test_get_organization_users_pagination():
    """Test paginating through large user lists."""
    # Should handle organizations with many users

def test_get_organization_export_users():
    """Test exporting user list to CSV."""
    # Should support --export-users-csv flag

def test_get_organization_show_service_desks():
    """Test showing which service desks organization belongs to."""
    # Should support --show-service-desks flag
```

**CLI Interface:**
```bash
# Get organization details
python get_organization.py 12345
python get_organization.py 12345 --show-users
python get_organization.py 12345 --show-service-desks

# Output formats
python get_organization.py 12345 --output json
python get_organization.py 12345 --show-users --output csv > users.csv

# Export options
python get_organization.py 12345 --export-users-csv users.csv
```

**Output Example:**
```
Organization: Acme Corporation (ID: 12345)

Users: 45 members
─────────────────────────────────────────────
john@acme.com       John Smith
jane@acme.com       Jane Doe
...

Service Desks:
  - IT Support (SERVICE-DESK-1)
  - HR Portal (SERVICE-DESK-2)
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Show organization details
- [ ] Optional user list
- [ ] Optional service desk list
- [ ] Multiple output formats
- [ ] User export to CSV

**Commits:**
1. `test(jira-jsm): add failing tests for get_organization`
2. `feat(jira-jsm): implement get_organization.py (8/8 tests passing)`

---

### Feature 3.2.4: Delete Organization

**Script:** `delete_organization.py`

**JIRA API:**
- `DELETE /rest/servicedeskapi/organization/{id}`

**Test File:** `tests/test_delete_organization.py`

**Test Cases:**
```python
def test_delete_organization_basic():
    """Test deleting organization by ID."""
    # Should delete organization

def test_delete_organization_confirmation():
    """Test confirmation prompt before deletion."""
    # Should require --yes or interactive confirmation

def test_delete_organization_not_found():
    """Test error when organization doesn't exist."""
    # Should handle 404 gracefully

def test_delete_organization_with_users():
    """Test warning when deleting organization with users."""
    # Should show user count in confirmation

def test_delete_organization_dry_run():
    """Test preview without deleting."""
    # Should show what would be deleted

def test_delete_organization_force():
    """Test forcing deletion without confirmation."""
    # Should support --yes flag

def test_delete_organization_permission_error():
    """Test handling insufficient permissions."""
    # Should explain permission requirements
```

**CLI Interface:**
```bash
# Delete organization
python delete_organization.py 12345
python delete_organization.py 12345 --yes  # Skip confirmation

# Safety options
python delete_organization.py 12345 --dry-run
```

**Output Example:**
```
WARNING: This will delete organization "Acme Corporation" (45 users)
This action cannot be undone.

Continue? [y/N]: y

Organization deleted successfully.
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Confirmation prompt
- [ ] Warning about user impact
- [ ] Dry-run mode
- [ ] Force deletion option
- [ ] Clear error messages

**Commits:**
1. `test(jira-jsm): add failing tests for delete_organization`
2. `feat(jira-jsm): implement delete_organization.py (7/7 tests passing)`

---

### Phase 3.2 Completion

- [ ] **Phase 3.2 Summary:**
  - [ ] 4 scripts implemented (list_organizations, create_organization, get_organization, delete_organization)
  - [ ] 35 tests passing (73 total)
  - [ ] All mutation scripts have --dry-run mode
  - [ ] CSV export support
  - [ ] User and service desk relationship display
  - **Commit:** `docs(jira-jsm): complete Phase 3.2 - Organization CRUD`

---

## Phase 3.3: Organization Membership Management

### Feature 3.3.1: Add Users to Organization

**Script:** `add_to_organization.py`

**JIRA API:**
- `POST /rest/servicedeskapi/organization/{id}/user`

**Test File:** `tests/test_add_to_organization.py`

**Test Cases:**
```python
def test_add_single_user_to_organization():
    """Test adding single user by account ID."""
    # Should add user to organization

def test_add_multiple_users_to_organization():
    """Test adding multiple users at once."""
    # Should support comma-separated account IDs

def test_add_user_by_email():
    """Test looking up account ID by email and adding."""
    # Should support --email flag with lookup

def test_add_user_already_in_organization():
    """Test handling when user already in organization."""
    # Should skip or warn, not error

def test_add_users_bulk_from_file():
    """Test adding users from file."""
    # Should support --from-file option

def test_add_users_dry_run():
    """Test preview without making changes."""
    # Should show what would be added

def test_add_users_progress_indicator():
    """Test progress indicator for bulk operations."""
    # Should show progress for multiple adds

def test_add_users_permission_error():
    """Test handling insufficient permissions."""
    # Should explain required permissions
```

**CLI Interface:**
```bash
# Add by account ID
python add_to_organization.py 12345 --account-id 5b10ac8d82e05b22cc7d4ef5
python add_to_organization.py 12345 --account-id "id1,id2,id3"

# Add by email
python add_to_organization.py 12345 --email user@example.com
python add_to_organization.py 12345 --email "user1@ex.com,user2@ex.com"

# Bulk operations
python add_to_organization.py 12345 --from-file users.txt

# Options
python add_to_organization.py 12345 --account-id "id1,id2" --dry-run
python add_to_organization.py 12345 --from-file users.txt --progress
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Single and bulk user addition
- [ ] Email-based lookup
- [ ] File-based bulk import
- [ ] Dry-run mode
- [ ] Progress indicator
- [ ] Skip existing members

**Commits:**
1. `test(jira-jsm): add failing tests for add_to_organization`
2. `feat(jira-jsm): implement add_to_organization.py (8/8 tests passing)`

---

### Feature 3.3.2: Remove Users from Organization

**Script:** `remove_from_organization.py`

**JIRA API:**
- `DELETE /rest/servicedeskapi/organization/{id}/user`

**Test File:** `tests/test_remove_from_organization.py`

**Test Cases:**
```python
def test_remove_single_user_from_organization():
    """Test removing single user by account ID."""
    # Should remove user from organization

def test_remove_multiple_users_from_organization():
    """Test removing multiple users at once."""
    # Should support comma-separated account IDs

def test_remove_user_by_email():
    """Test looking up account ID by email and removing."""
    # Should support --email flag with lookup

def test_remove_user_not_in_organization():
    """Test handling when user not in organization."""
    # Should warn but not error

def test_remove_users_confirmation():
    """Test confirmation prompt before removal."""
    # Should require --yes or interactive confirmation

def test_remove_users_bulk_from_file():
    """Test removing users from file."""
    # Should support --from-file option

def test_remove_users_dry_run():
    """Test preview without making changes."""
    # Should show what would be removed
```

**CLI Interface:**
```bash
# Remove by account ID
python remove_from_organization.py 12345 --account-id 5b10ac8d82e05b22cc7d4ef5
python remove_from_organization.py 12345 --account-id "id1,id2" --yes

# Remove by email
python remove_from_organization.py 12345 --email user@example.com

# Bulk operations
python remove_from_organization.py 12345 --from-file remove-list.txt --yes

# Safety options
python remove_from_organization.py 12345 --account-id id1 --dry-run
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Single and bulk user removal
- [ ] Email-based lookup
- [ ] File-based bulk removal
- [ ] Confirmation prompts
- [ ] Dry-run mode

**Commits:**
1. `test(jira-jsm): add failing tests for remove_from_organization`
2. `feat(jira-jsm): implement remove_from_organization.py (7/7 tests passing)`

---

### Phase 3.3 Completion

- [ ] **Phase 3.3 Summary:**
  - [ ] 2 scripts implemented (add_to_organization, remove_from_organization)
  - [ ] 15 tests passing (88 total)
  - [ ] Bulk operations support
  - [ ] Email lookup integration
  - [ ] File-based import/export
  - **Commit:** `docs(jira-jsm): complete Phase 3.3 - Organization Membership`

---

## Phase 3.4: Request Participants Management

### Feature 3.4.1: Get Request Participants

**Script:** `get_participants.py`

**JIRA API:**
- `GET /rest/servicedeskapi/request/{key}/participant`

**Test File:** `tests/test_get_participants.py`

**Test Cases:**
```python
def test_get_participants_basic():
    """Test getting all participants for request."""
    # Should return list of participants

def test_get_participants_empty():
    """Test output when no participants exist."""
    # Should show clear "no participants" message

def test_get_participants_text_format():
    """Test formatted table output."""
    # Should show email, name, added date

def test_get_participants_json_format():
    """Test JSON output with all fields."""
    # Should return full participant objects

def test_get_participants_pagination():
    """Test pagination for requests with many participants."""
    # Should handle large participant lists

def test_get_participants_count_only():
    """Test getting participant count."""
    # Should support --count flag

def test_get_participants_export_csv():
    """Test exporting participant list to CSV."""
    # Should generate CSV output

def test_get_participants_request_not_found():
    """Test error when request doesn't exist."""
    # Should provide clear error message
```

**CLI Interface:**
```bash
# Get participants
python get_participants.py REQ-123
python get_participants.py REQ-123 --all  # All pages

# Output formats
python get_participants.py REQ-123 --output json
python get_participants.py REQ-123 --output csv > participants.csv
python get_participants.py REQ-123 --count

# Pagination
python get_participants.py REQ-123 --start 0 --limit 50
```

**Output Example:**
```
Participants for REQ-123:

Email                    Display Name          Added
─────────────────────────────────────────────────────────
john@example.com         John Smith            2025-12-20
jane@example.com         Jane Doe              2025-12-21
bob@example.com          Bob Johnson           2025-12-22

Total: 3 participants
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] List all participants
- [ ] Pagination support
- [ ] Multiple output formats
- [ ] Participant count option
- [ ] CSV export

**Commits:**
1. `test(jira-jsm): add failing tests for get_participants`
2. `feat(jira-jsm): implement get_participants.py (8/8 tests passing)`

---

### Feature 3.4.2: Add Request Participants

**Script:** `add_participant.py`

**JIRA API:**
- `POST /rest/servicedeskapi/request/{key}/participant`

**Test File:** `tests/test_add_participant.py`

**Test Cases:**
```python
def test_add_single_participant():
    """Test adding single participant by account ID."""
    # Should add participant to request

def test_add_multiple_participants():
    """Test adding multiple participants at once."""
    # Should support comma-separated account IDs

def test_add_participant_by_email():
    """Test looking up account ID by email and adding."""
    # Should support --email flag with lookup

def test_add_participant_already_exists():
    """Test handling when participant already added."""
    # Should skip or warn, not error

def test_add_participant_by_username():
    """Test adding participant by username (legacy)."""
    # Should support --username flag

def test_add_participants_bulk_from_file():
    """Test adding participants from file."""
    # Should support --from-file option

def test_add_participants_dry_run():
    """Test preview without making changes."""
    # Should show what would be added

def test_add_participants_notify():
    """Test notification option for participants."""
    # Should support --notify flag
```

**CLI Interface:**
```bash
# Add by account ID
python add_participant.py REQ-123 --account-id 5b10ac8d82e05b22cc7d4ef5
python add_participant.py REQ-123 --account-id "id1,id2,id3"

# Add by email
python add_participant.py REQ-123 --email user@example.com
python add_participant.py REQ-123 --email "user1@ex.com,user2@ex.com"

# Add by username (legacy)
python add_participant.py REQ-123 --username jsmith

# Bulk operations
python add_participant.py REQ-123 --from-file participants.txt

# Options
python add_participant.py REQ-123 --email user@ex.com --dry-run
python add_participant.py REQ-123 --email user@ex.com --notify
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Single and bulk participant addition
- [ ] Email-based lookup
- [ ] Username support (legacy)
- [ ] File-based bulk import
- [ ] Dry-run mode
- [ ] Notification option

**Commits:**
1. `test(jira-jsm): add failing tests for add_participant`
2. `feat(jira-jsm): implement add_participant.py (8/8 tests passing)`

---

### Feature 3.4.3: Remove Request Participants

**Script:** `remove_participant.py`

**JIRA API:**
- `DELETE /rest/servicedeskapi/request/{key}/participant`

**Test File:** `tests/test_remove_participant.py`

**Test Cases:**
```python
def test_remove_single_participant():
    """Test removing single participant by account ID."""
    # Should remove participant from request

def test_remove_multiple_participants():
    """Test removing multiple participants at once."""
    # Should support comma-separated account IDs

def test_remove_participant_by_email():
    """Test looking up account ID by email and removing."""
    # Should support --email flag with lookup

def test_remove_participant_not_in_request():
    """Test handling when participant not in request."""
    # Should warn but not error

def test_remove_participants_confirmation():
    """Test confirmation prompt before removal."""
    # Should require --yes or interactive confirmation

def test_remove_participants_dry_run():
    """Test preview without making changes."""
    # Should show what would be removed
```

**CLI Interface:**
```bash
# Remove by account ID
python remove_participant.py REQ-123 --account-id 5b10ac8d82e05b22cc7d4ef5
python remove_participant.py REQ-123 --account-id "id1,id2" --yes

# Remove by email
python remove_participant.py REQ-123 --email user@example.com

# Safety options
python remove_participant.py REQ-123 --account-id id1 --dry-run
python remove_participant.py REQ-123 --email user@ex.com --yes  # Skip confirmation
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Single and bulk participant removal
- [ ] Email-based lookup
- [ ] Confirmation prompts
- [ ] Dry-run mode

**Commits:**
1. `test(jira-jsm): add failing tests for remove_participant`
2. `feat(jira-jsm): implement remove_participant.py (6/6 tests passing)`

---

### Phase 3.4 Completion

- [ ] **Phase 3.4 Summary:**
  - [ ] 3 scripts implemented (get_participants, add_participant, remove_participant)
  - [ ] 22 tests passing (110 total)
  - [ ] Email and username lookup
  - [ ] Notification support
  - [ ] CSV export
  - **Commit:** `docs(jira-jsm): complete Phase 3.4 - Request Participants`

---

## Integration & Documentation

### Integration Tasks

- [ ] **Integration 1:** Update create_request.py
  - [ ] Add `--participants` flag to add participants on creation
  - [ ] Add `--organization` flag to associate request with organization
  - **Commit:** `feat(jira-jsm): add participant and organization support to create_request`

- [ ] **Integration 2:** Update get_request.py
  - [ ] Add `--show-participants` flag to display participants
  - [ ] Add `--show-organization` flag to display organization
  - **Commit:** `feat(jira-jsm): add participant and organization display to get_request`

- [ ] **Integration 3:** Create organization workflow helper
  - [ ] Create `manage_organization.py` - Interactive organization management
  - [ ] Support: create org → add users → add to service desk
  - **Commit:** `feat(jira-jsm): add interactive organization management workflow`

### Documentation Updates

- [ ] **Docs 1:** Update jira-jsm SKILL.md
  - [ ] Add "Customer Management" section
  - [ ] Add "Organization Management" section
  - [ ] Add "Request Participants" section
  - [ ] Add workflow examples (onboarding organization, bulk customer import)
  - **Commit:** `docs(jira-jsm): add Phase 3 documentation to SKILL.md`

- [ ] **Docs 2:** Create customer management guide
  - [ ] Create `references/customer_management_guide.md`
  - [ ] Document customer vs user differences
  - [ ] Document organization best practices
  - [ ] Add troubleshooting section
  - **Commit:** `docs(jira-jsm): add customer and organization management guide`

- [ ] **Docs 3:** Update JSM Gap Analysis
  - [ ] Mark Categories D, E, F as complete
  - [ ] Update implementation percentages
  - [ ] Update completion status
  - **Commit:** `docs(jira-jsm): update gap analysis - Phase 3 complete`

### Testing & Quality

- [ ] **Quality 1:** Integration tests
  - [ ] End-to-end: Create customer → Add to SD → Create request → Add participant
  - [ ] End-to-end: Create organization → Add users → Add to SD → Create request
  - [ ] Live integration tests in `shared/tests/live_integration/test_jsm_phase3.py`
  - **Commit:** `test(jira-jsm): add Phase 3 live integration tests`

- [ ] **Quality 2:** Coverage validation
  - [ ] Run `pytest --cov=.claude/skills/jira-jsm --cov-report=html`
  - [ ] Ensure ≥85% coverage for Phase 3 scripts
  - [ ] Document uncovered code (CLI main() functions acceptable)

- [ ] **Quality 3:** Error handling review
  - [ ] All scripts use try/except with JiraError
  - [ ] Validation before API calls
  - [ ] Helpful error messages with print_error()
  - [ ] Permission error handling documented

- [ ] **Quality 4:** Performance testing
  - [ ] Test bulk operations with 100+ customers
  - [ ] Test pagination with large organizations
  - [ ] Ensure reasonable performance for common operations

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 110+ unit tests passing
- [ ] 5+ integration tests passing
- [ ] Coverage ≥85% for Phase 3 code

**Scripts:**
- [ ] 13 new scripts implemented
- [ ] All scripts have `--help`
- [ ] All scripts support `--profile`
- [ ] Mutation scripts have `--dry-run`
- [ ] Mutation scripts have confirmation prompts

**Documentation:**
- [ ] SKILL.md updated with Phase 3 content
- [ ] Customer management guide created
- [ ] JSM Gap Analysis updated
- [ ] All scripts have comprehensive docstrings

**Integration:**
- [ ] create_request.py supports participants and organizations
- [ ] get_request.py displays participants and organizations
- [ ] Interactive workflow helper created

### Progress Tracking

**Test Status:** 0/110 unit tests passing (0%)

**Phase Status:**
- [ ] Phase 3.1: Customer CRUD (4 scripts, 38 tests)
- [ ] Phase 3.2: Organization CRUD (4 scripts, 35 tests)
- [ ] Phase 3.3: Organization Membership (2 scripts, 15 tests)
- [ ] Phase 3.4: Request Participants (3 scripts, 22 tests)
- [ ] Integration (3 updates)
- [ ] Documentation (3 docs)
- [ ] Quality (4 tasks)

---

## Script Summary

| Script | Phase | Tests | Description |
|--------|-------|-------|-------------|
| `create_customer.py` | 3.1 | 10 | Create customer account |
| `list_customers.py` | 3.1 | 10 | List service desk customers |
| `add_customer.py` | 3.1 | 10 | Add customers to service desk |
| `remove_customer.py` | 3.1 | 8 | Remove customers from service desk |
| `list_organizations.py` | 3.2 | 10 | List all organizations |
| `create_organization.py` | 3.2 | 10 | Create organization |
| `get_organization.py` | 3.2 | 8 | Get organization details |
| `delete_organization.py` | 3.2 | 7 | Delete organization |
| `add_to_organization.py` | 3.3 | 8 | Add users to organization |
| `remove_from_organization.py` | 3.3 | 7 | Remove users from organization |
| `get_participants.py` | 3.4 | 8 | Get request participants |
| `add_participant.py` | 3.4 | 8 | Add participants to request |
| `remove_participant.py` | 3.4 | 6 | Remove participants from request |
| **Total** | - | **110** | - |

---

## JiraClient Methods to Add

```python
# In shared/scripts/lib/jira_client.py

# ============================================================================
# Customer Management
# ============================================================================

def create_customer(self, email: str, display_name: str = None) -> dict:
    """Create a customer account."""
    payload = {'email': email}
    if display_name:
        payload['displayName'] = display_name
    return self.post('/rest/servicedeskapi/customer', json=payload)

def get_service_desk_customers(self, service_desk_id: str, query: str = None,
                                start: int = 0, limit: int = 50) -> dict:
    """List customers for a service desk."""
    params = {'start': start, 'limit': limit}
    if query:
        params['query'] = query
    return self.get(f'/rest/servicedeskapi/servicedesk/{service_desk_id}/customer',
                    params=params)

def add_customers_to_service_desk(self, service_desk_id: str,
                                   account_ids: List[str]) -> None:
    """Add customers to a service desk."""
    payload = {'accountIds': account_ids}
    self.post(f'/rest/servicedeskapi/servicedesk/{service_desk_id}/customer',
              json=payload)

def remove_customers_from_service_desk(self, service_desk_id: str,
                                       account_ids: List[str]) -> None:
    """Remove customers from a service desk."""
    payload = {'accountIds': account_ids}
    self.delete(f'/rest/servicedeskapi/servicedesk/{service_desk_id}/customer',
                json=payload)

# ============================================================================
# Organization Management
# ============================================================================

def get_organizations(self, start: int = 0, limit: int = 50) -> dict:
    """List all organizations."""
    params = {'start': start, 'limit': limit}
    return self.get('/rest/servicedeskapi/organization', params=params)

def create_organization(self, name: str) -> dict:
    """Create an organization."""
    payload = {'name': name}
    return self.post('/rest/servicedeskapi/organization', json=payload)

def get_organization(self, organization_id: str) -> dict:
    """Get organization details."""
    return self.get(f'/rest/servicedeskapi/organization/{organization_id}')

def delete_organization(self, organization_id: str) -> None:
    """Delete an organization."""
    self.delete(f'/rest/servicedeskapi/organization/{organization_id}')

def get_organization_users(self, organization_id: str,
                           start: int = 0, limit: int = 50) -> dict:
    """List users in an organization."""
    params = {'start': start, 'limit': limit}
    return self.get(f'/rest/servicedeskapi/organization/{organization_id}/user',
                    params=params)

def add_users_to_organization(self, organization_id: str,
                               account_ids: List[str]) -> None:
    """Add users to an organization."""
    payload = {'accountIds': account_ids}
    self.post(f'/rest/servicedeskapi/organization/{organization_id}/user',
              json=payload)

def remove_users_from_organization(self, organization_id: str,
                                   account_ids: List[str]) -> None:
    """Remove users from an organization."""
    payload = {'accountIds': account_ids}
    self.delete(f'/rest/servicedeskapi/organization/{organization_id}/user',
                json=payload)

def get_service_desk_organizations(self, service_desk_id: str,
                                    start: int = 0, limit: int = 50) -> dict:
    """List organizations for a service desk."""
    params = {'start': start, 'limit': limit}
    return self.get(f'/rest/servicedeskapi/servicedesk/{service_desk_id}/organization',
                    params=params)

def add_organization_to_service_desk(self, service_desk_id: str,
                                      organization_id: str) -> None:
    """Add organization to a service desk."""
    payload = {'organizationId': int(organization_id)}
    self.post(f'/rest/servicedeskapi/servicedesk/{service_desk_id}/organization',
              json=payload)

def remove_organization_from_service_desk(self, service_desk_id: str,
                                          organization_id: str) -> None:
    """Remove organization from a service desk."""
    payload = {'organizationId': int(organization_id)}
    self.delete(f'/rest/servicedeskapi/servicedesk/{service_desk_id}/organization',
                json=payload)

# ============================================================================
# Request Participants
# ============================================================================

def get_request_participants(self, issue_key: str,
                             start: int = 0, limit: int = 50) -> dict:
    """Get participants for a request."""
    params = {'start': start, 'limit': limit}
    return self.get(f'/rest/servicedeskapi/request/{issue_key}/participant',
                    params=params)

def add_request_participants(self, issue_key: str,
                             account_ids: List[str] = None,
                             usernames: List[str] = None) -> dict:
    """Add participants to a request."""
    payload = {
        'accountIds': account_ids or [],
        'usernames': usernames or []
    }
    return self.post(f'/rest/servicedeskapi/request/{issue_key}/participant',
                     json=payload)

def remove_request_participants(self, issue_key: str,
                                account_ids: List[str] = None,
                                usernames: List[str] = None) -> dict:
    """Remove participants from a request."""
    payload = {
        'accountIds': account_ids or [],
        'usernames': usernames or []
    }
    return self.delete(f'/rest/servicedeskapi/request/{issue_key}/participant',
                       json=payload)
```

---

## Commit Strategy

### Commit Types

**test:** Adding or updating tests
- `test(jira-jsm): add failing tests for create_customer`

**feat:** Implementing features
- `feat(jira-jsm): implement create_customer.py (10/10 tests passing)`

**docs:** Documentation updates
- `docs(jira-jsm): add customer management section to SKILL.md`

**fix:** Bug fixes
- `fix(jira-jsm): handle duplicate customer email gracefully`

---

## API Sources

- [Jira Service Management Cloud REST API](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-servicedesk/)
- [Customer API](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-customer/)
- [Organization API](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-organization/)
- [Request Participants API](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-request/#api-group-participant)
- [JSM Data Center REST API Reference](https://docs.atlassian.com/jira-servicedesk/REST/5.15.2/)

---

**Plan Version:** 1.0
**Created:** 2025-12-25
**Last Updated:** 2025-12-25
**Status:** NOT STARTED - Phase 3 Customer & Organization Management
**Prerequisites:** Phase 1 (Service Desk & Request Types), Phase 2 (Request Management)
