# JSM Phase 2: Request Management - TDD Implementation Plan

## Overview

**Objective:** Implement comprehensive JSM request lifecycle management using Test-Driven Development (TDD)

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
1. **Phase 2.1: Create Request** (Foundation - create service requests with request types)
2. **Phase 2.2: Get Request Details** (View requests with SLA info)
3. **Phase 2.3: Transition Request** (Change request status with SLA awareness)
4. **Phase 2.4: List Requests** (Query requests by filters)
5. **Phase 2.5: Get Request Status History** (Status change timeline)

---

## JIRA API Reference

### JSM Request Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rest/servicedeskapi/request` | Create service request |
| GET | `/rest/servicedeskapi/request/{issueIdOrKey}` | Get request details |
| GET | `/rest/servicedeskapi/request/{issueIdOrKey}/status` | Get request status history |
| GET | `/rest/servicedeskapi/request/{issueIdOrKey}/transition` | Get available transitions |
| POST | `/rest/servicedeskapi/request/{issueIdOrKey}/transition` | Transition request |
| GET | `/rest/servicedeskapi/request` | Search/list requests (limited) |
| GET | `/rest/servicedeskapi/servicedesk/{serviceDeskId}/queue/{queueId}/issue` | Get requests in queue |

### Create Request Payload

```json
{
  "serviceDeskId": "1",
  "requestTypeId": "10",
  "requestFieldValues": {
    "summary": "Request title",
    "description": "Request description in ADF or text",
    "customfield_10050": "High",
    "components": [{"name": "IT Support"}]
  },
  "raiseOnBehalfOf": "user@example.com",
  "requestParticipants": ["participant1@example.com", "participant2@example.com"]
}
```

### Get Request Response

```json
{
  "issueId": "10010",
  "issueKey": "SD-101",
  "requestTypeId": "10",
  "requestType": {
    "id": "10",
    "name": "Incident",
    "description": "Report an incident",
    "helpText": "Use this for urgent issues"
  },
  "serviceDeskId": "1",
  "createdDate": {
    "iso8601": "2025-01-15T10:30:00+0000",
    "jira": "2025-01-15T10:30:00.000+0000",
    "friendly": "Today 10:30 AM",
    "epochMillis": 1736936400000
  },
  "reporter": {
    "accountId": "557058:abc123",
    "displayName": "Alice Reporter",
    "emailAddress": "alice@example.com"
  },
  "requestFieldValues": [
    {
      "fieldId": "summary",
      "label": "Summary",
      "value": "Request title"
    },
    {
      "fieldId": "description",
      "label": "Description",
      "value": "Request description",
      "renderedValue": {
        "html": "<p>Request description</p>"
      }
    }
  ],
  "currentStatus": {
    "status": "Waiting for support",
    "statusCategory": "NEW",
    "statusDate": {
      "iso8601": "2025-01-15T10:30:00+0000",
      "jira": "2025-01-15T10:30:00.000+0000",
      "friendly": "Today 10:30 AM",
      "epochMillis": 1736936400000
    }
  },
  "_expands": ["participant", "status", "sla", "requestType", "serviceDesk"],
  "_links": {
    "self": "https://site.atlassian.net/rest/servicedeskapi/request/SD-101",
    "jiraIssue": "https://site.atlassian.net/rest/api/3/issue/10010",
    "agent": "https://site.atlassian.net/browse/SD-101",
    "web": "https://site.atlassian.net/servicedesk/customer/portal/1/SD-101"
  }
}
```

### Get Status History Response

```json
{
  "values": [
    {
      "status": "Open",
      "statusCategory": "NEW",
      "statusDate": {
        "iso8601": "2025-01-15T10:30:00+0000",
        "jira": "2025-01-15T10:30:00.000+0000",
        "friendly": "Today 10:30 AM",
        "epochMillis": 1736936400000
      }
    },
    {
      "status": "In Progress",
      "statusCategory": "IN_PROGRESS",
      "statusDate": {
        "iso8601": "2025-01-15T11:00:00+0000",
        "jira": "2025-01-15T11:00:00.000+0000",
        "friendly": "Today 11:00 AM",
        "epochMillis": 1736938200000
      }
    },
    {
      "status": "Resolved",
      "statusCategory": "DONE",
      "statusDate": {
        "iso8601": "2025-01-15T14:30:00+0000",
        "jira": "2025-01-15T14:30:00.000+0000",
        "friendly": "Today 2:30 PM",
        "epochMillis": 1736950800000
      }
    }
  ]
}
```

### Transition Request Payload

```json
{
  "id": "11",
  "additionalComment": {
    "body": "Moving to In Progress",
    "public": true
  }
}
```

### Important JSM vs JIRA Differences

| Feature | JIRA API (`/rest/api/3/`) | JSM API (`/rest/servicedeskapi/`) |
|---------|---------------------------|----------------------------------|
| **Creating** | Uses issue types | Uses **request types** (configured per service desk) |
| **Field Structure** | `fields` object | `requestFieldValues` object |
| **Visibility** | Not applicable | Requests visible in **customer portal** |
| **SLA** | Not tracked | **Automatic SLA tracking** |
| **Participants** | Only assignee/reporter | **Multiple participants** supported |
| **Comments** | All internal | **Public vs internal** distinction |

---

## Test Infrastructure Setup

### Initial Setup Tasks

- [ ] **Setup 2.1:** Create jira-jsm skill structure
  - [ ] Create `.claude/skills/jira-jsm/` directory
  - [ ] Create `scripts/` subdirectory
  - [ ] Create `tests/` subdirectory
  - [ ] Create `SKILL.md` skeleton
  - **Commit:** `feat(jira-jsm): create skill structure for JSM Phase 2`

- [ ] **Setup 2.2:** Create test infrastructure
  - [ ] Create `tests/conftest.py` with shared fixtures
  - [ ] Mock JiraClient fixture with JSM endpoints
  - [ ] Sample service desk response fixture
  - [ ] Sample request type response fixture
  - [ ] Sample request creation response fixture
  - [ ] Sample request with SLA fixture
  - [ ] Sample transition response fixture
  - **Commit:** `test(jira-jsm): add pytest fixtures for request management`

- [ ] **Setup 2.3:** Add JiraClient methods for JSM requests
  - [ ] `create_request(service_desk_id, request_type_id, fields, participants)` - Create request
  - [ ] `get_request(issue_key)` - Get request details
  - [ ] `get_request_status(issue_key)` - Get status history
  - [ ] `get_request_transitions(issue_key)` - Get available transitions
  - [ ] `transition_request(issue_key, transition_id, comment, public)` - Transition request
  - [ ] `list_requests(service_desk_id, params)` - List/search requests
  - **Commit:** `feat(shared): add JSM request API methods to JiraClient`

---

## Phase 2.1: Create Request

### Feature 2.1.1: Create Service Request

**Script:** `create_request.py`

**JIRA API:**
- `POST /rest/servicedeskapi/request`

**Test File:** `tests/test_create_request.py`

**Test Cases:**
```python
def test_create_request_basic():
    """Test creating request with summary and description."""
    # Should POST with serviceDeskId, requestTypeId, requestFieldValues

def test_create_request_with_request_type():
    """Test creating request with specific request type."""
    # Should include requestTypeId in payload

def test_create_request_with_custom_fields():
    """Test creating request with JSM custom fields."""
    # Should include custom fields in requestFieldValues

def test_create_request_with_participants():
    """Test adding participants when creating request."""
    # Should include requestParticipants array

def test_create_request_on_behalf_of():
    """Test creating request on behalf of another user."""
    # Should include raiseOnBehalfOf field

def test_create_request_validate_required_fields():
    """Test validation of required fields for request type."""
    # Should validate fields match request type requirements

def test_create_request_with_priority():
    """Test setting priority during creation."""
    # Should include priority in requestFieldValues

def test_create_request_invalid_request_type():
    """Test error when request type doesn't exist."""
    # Should raise ValidationError

def test_create_request_service_desk_not_found():
    """Test error when service desk doesn't exist."""
    # Should raise NotFoundError

def test_create_request_field_validation_error():
    """Test error when required fields missing."""
    # Should raise ValidationError with field details
```

**CLI Interface:**
```bash
# Basic usage
python create_request.py --service-desk 1 --request-type 10 \
  --summary "Email not working" \
  --description "Cannot send emails since this morning"

# With request type name (auto-lookup)
python create_request.py --service-desk "IT Support" --request-type "Incident" \
  --summary "Server down" \
  --description "Production server not responding"

# With custom fields
python create_request.py --service-desk 1 --request-type 10 \
  --summary "New laptop request" \
  --field priority="High" \
  --field category="Hardware" \
  --field impact="Multiple Users"

# With participants
python create_request.py --service-desk 1 --request-type 10 \
  --summary "Team access request" \
  --participants "alice@example.com,bob@example.com"

# On behalf of customer
python create_request.py --service-desk 1 --request-type 10 \
  --summary "Password reset" \
  --on-behalf-of "customer@example.com"

# With template
python create_request.py --service-desk 1 --request-type 10 \
  --template incident_template.json
```

**Output Example:**
```
Service request created successfully!

Request Key: SD-101
Request Type: Incident
Service Desk: IT Support
Status: Waiting for support

Summary: Email not working
Description: Cannot send emails since this morning
Priority: High
Reporter: alice@example.com
Created: Today 10:30 AM

Customer Portal: https://site.atlassian.net/servicedesk/customer/portal/1/SD-101
Agent View: https://site.atlassian.net/browse/SD-101
```

**Acceptance Criteria:**
- [ ] All 10 tests pass
- [ ] Supports request type by ID or name
- [ ] Custom field support
- [ ] Participant management
- [ ] On-behalf-of creation
- [ ] Field validation before API call
- [ ] Returns request key and portal link

**Commits:**
1. `test(jira-jsm): add failing tests for create_request`
2. `feat(jira-jsm): implement create_request.py (10/10 tests passing)`

---

## Phase 2.2: Get Request Details

### Feature 2.2.1: View Request Information

**Script:** `get_request.py`

**JIRA API:**
- `GET /rest/servicedeskapi/request/{issueIdOrKey}`

**Test File:** `tests/test_get_request.py`

**Test Cases:**
```python
def test_get_request_basic():
    """Test fetching request with all details."""
    # Should GET request with default expands

def test_get_request_with_sla():
    """Test fetching request with SLA information."""
    # Should expand=sla and show SLA metrics

def test_get_request_with_participants():
    """Test fetching request with participant list."""
    # Should expand=participant

def test_get_request_format_text():
    """Test human-readable output."""
    # Should show formatted request details

def test_get_request_format_json():
    """Test JSON output format."""
    # Should return valid JSON

def test_get_request_show_field_values():
    """Test displaying all request field values."""
    # Should show requestFieldValues in readable format

def test_get_request_show_portal_link():
    """Test displaying customer portal link."""
    # Should show _links.web URL

def test_get_request_not_found():
    """Test error when request doesn't exist."""
    # Should raise NotFoundError
```

**CLI Interface:**
```bash
# Basic usage
python get_request.py SD-101

# With SLA information
python get_request.py SD-101 --show-sla

# With participants
python get_request.py SD-101 --show-participants

# All details
python get_request.py SD-101 --full

# JSON output
python get_request.py SD-101 --output json
```

**Output Example:**
```
Request: SD-101
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Request Type: Incident
Service Desk: IT Support
Status: In Progress (IN_PROGRESS)

Summary: Email not working
Description: Cannot send emails since this morning

Reporter: alice@example.com
Participants: alice@example.com, bob@example.com
Created: Today 10:30 AM
Last Updated: Today 11:00 AM

SLA Information:
  Time to First Response:
    ✓ Met (responded in 15m of 1h goal)

  Time to Resolution:
    ⏱ In Progress (3h 30m remaining of 4h goal)
    Breach Time: Today 2:30 PM

Custom Fields:
  Priority: High
  Impact: Multiple Users
  Category: Email

Links:
  Customer Portal: https://site.atlassian.net/servicedesk/customer/portal/1/SD-101
  Agent View: https://site.atlassian.net/browse/SD-101
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Shows complete request details
- [ ] SLA information display
- [ ] Participant list
- [ ] Portal and agent links
- [ ] Request field values formatted
- [ ] Status category shown

**Commits:**
1. `test(jira-jsm): add failing tests for get_request`
2. `feat(jira-jsm): implement get_request.py (8/8 tests passing)`

---

## Phase 2.3: Transition Request

### Feature 2.3.1: Change Request Status

**Script:** `transition_request.py`

**JIRA API:**
- `GET /rest/servicedeskapi/request/{issueIdOrKey}/transition` (get available)
- `POST /rest/servicedeskapi/request/{issueIdOrKey}/transition` (perform)

**Test File:** `tests/test_transition_request.py`

**Test Cases:**
```python
def test_transition_request_by_id():
    """Test transitioning request using transition ID."""
    # Should POST transition with id

def test_transition_request_by_name():
    """Test transitioning request using transition name."""
    # Should lookup transition ID from name

def test_transition_with_comment():
    """Test adding comment during transition."""
    # Should include additionalComment in payload

def test_transition_with_public_comment():
    """Test adding public (customer-visible) comment."""
    # Should set public: true in comment

def test_transition_with_internal_comment():
    """Test adding internal (agent-only) comment."""
    # Should set public: false in comment

def test_transition_show_sla_impact():
    """Test showing SLA impact of transition."""
    # Should warn if transition will affect SLA

def test_transition_invalid_transition():
    """Test error when transition not available."""
    # Should raise ValidationError

def test_transition_request_not_found():
    """Test error when request doesn't exist."""
    # Should raise NotFoundError
```

**CLI Interface:**
```bash
# By transition name
python transition_request.py SD-101 --to "In Progress"
python transition_request.py SD-101 --to "Resolved"

# By transition ID
python transition_request.py SD-101 --transition-id 11

# With comment
python transition_request.py SD-101 --to "Resolved" \
  --comment "Issue fixed by restarting mail server"

# Public vs internal comment
python transition_request.py SD-101 --to "Waiting for customer" \
  --comment "Please provide more details" \
  --public

python transition_request.py SD-101 --to "In Progress" \
  --comment "Escalating to L2 support" \
  --internal

# Show available transitions
python transition_request.py SD-101 --show-transitions
```

**Output Example:**
```
Transitioning request SD-101...

From: Waiting for support
To: In Progress

⚠ SLA Warning:
  Time to First Response: Will start (1h goal)
  Consider responding to customer first

Comment added: Starting investigation
Visibility: Internal (agent-only)

✓ Request transitioned successfully

Current Status: In Progress
Updated: Today 11:00 AM
```

**Output Example (Show Transitions):**
```
Available transitions for SD-101 (current status: Waiting for support):

ID   Name                    To Status           SLA Impact
───  ──────────────────────  ──────────────────  ─────────────────────
11   Start Progress          In Progress         Starts "First Response" SLA
21   Waiting for Customer    Waiting for customer Pauses all SLAs
31   Resolve                 Resolved            Stops all SLAs
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Transition by name or ID
- [ ] Public/internal comment support
- [ ] SLA impact warnings
- [ ] Show available transitions
- [ ] Validates transition availability

**Commits:**
1. `test(jira-jsm): add failing tests for transition_request`
2. `feat(jira-jsm): implement transition_request.py (8/8 tests passing)`

---

## Phase 2.4: List Requests

### Feature 2.4.1: Query Service Requests

**Script:** `list_requests.py`

**JIRA API:**
- `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/queue/{queueId}/issue` (recommended)
- `GET /rest/api/3/search` with JQL (fallback for complex queries)

**Test File:** `tests/test_list_requests.py`

**Test Cases:**
```python
def test_list_requests_by_service_desk():
    """Test listing all requests for service desk."""
    # Should use queue API or JQL: project=SD

def test_list_requests_by_queue():
    """Test listing requests in specific queue."""
    # Should GET /queue/{id}/issue

def test_list_requests_by_status():
    """Test filtering by status."""
    # Should use JQL: status="In Progress"

def test_list_requests_by_request_type():
    """Test filtering by request type."""
    # Should use appropriate filter

def test_list_requests_format_table():
    """Test table output with key columns."""
    # Should show key, summary, status, reporter, SLA

def test_list_requests_format_json():
    """Test JSON output."""
    # Should return valid JSON

def test_list_requests_pagination():
    """Test handling large result sets."""
    # Should support --max-results and pagination
```

**CLI Interface:**
```bash
# List all requests
python list_requests.py --service-desk "IT Support"
python list_requests.py --service-desk 1

# By queue
python list_requests.py --service-desk 1 --queue "My Open Requests"
python list_requests.py --service-desk 1 --queue-id 10

# By status
python list_requests.py --service-desk 1 --status "In Progress"
python list_requests.py --service-desk 1 --status "Waiting for support,In Progress"

# By request type
python list_requests.py --service-desk 1 --request-type "Incident"

# With SLA breach filter
python list_requests.py --service-desk 1 --sla-breached
python list_requests.py --service-desk 1 --sla-approaching-breach

# Pagination
python list_requests.py --service-desk 1 --max-results 50
python list_requests.py --service-desk 1 --start-at 50

# Output format
python list_requests.py --service-desk 1 --output json
```

**Output Example:**
```
Requests in IT Support (Service Desk):

Key      Summary                  Status              Reporter          SLA Status
───────  ───────────────────────  ──────────────────  ────────────────  ─────────────────
SD-101   Email not working        In Progress         alice@example.com ⏱ 3h 30m remaining
SD-102   Laptop request           Waiting for support bob@example.com   ✓ On track
SD-103   Password reset           Resolved            carol@example.com ✓ Met SLA
SD-104   Server outage            In Progress         dave@example.com  ⚠ Breach in 30m

Total: 4 requests (2 in progress, 1 waiting, 1 resolved)
SLA: 3 on track, 1 approaching breach
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] List by service desk
- [ ] Filter by queue, status, request type
- [ ] SLA status in results
- [ ] Pagination support
- [ ] Table and JSON formats

**Commits:**
1. `test(jira-jsm): add failing tests for list_requests`
2. `feat(jira-jsm): implement list_requests.py (7/7 tests passing)`

---

## Phase 2.5: Get Request Status History

### Feature 2.5.1: View Status Timeline

**Script:** `get_request_status.py`

**JIRA API:**
- `GET /rest/servicedeskapi/request/{issueIdOrKey}/status`

**Test File:** `tests/test_get_request_status.py`

**Test Cases:**
```python
def test_get_status_history():
    """Test fetching complete status history."""
    # Should GET /request/{key}/status

def test_status_history_with_durations():
    """Test calculating time in each status."""
    # Should compute duration between status changes

def test_status_history_format_timeline():
    """Test timeline output format."""
    # Should show chronological status changes

def test_status_history_format_json():
    """Test JSON output."""
    # Should return valid JSON

def test_status_history_empty():
    """Test when only creation status exists."""
    # Should show single status entry

def test_status_history_request_not_found():
    """Test error when request doesn't exist."""
    # Should raise NotFoundError
```

**CLI Interface:**
```bash
# Basic usage
python get_request_status.py SD-101

# With durations
python get_request_status.py SD-101 --show-durations

# JSON output
python get_request_status.py SD-101 --output json
```

**Output Example:**
```
Status History for SD-101:

Status                  Category      Changed              Duration
──────────────────────  ────────────  ───────────────────  ─────────
Open                    NEW           Today 10:30 AM       30m
Waiting for support     NEW           Today 11:00 AM       3h 30m
In Progress             IN_PROGRESS   Today 2:30 PM        1h 15m
Resolved                DONE          Today 3:45 PM        (current)

Total Time: 5h 15m
Time to First Response: 30m
Time to Resolution: 5h 15m
Status Changes: 4
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Shows complete status history
- [ ] Calculates time in each status
- [ ] Timeline format
- [ ] Metrics (time to first response, resolution)

**Commits:**
1. `test(jira-jsm): add failing tests for get_request_status`
2. `feat(jira-jsm): implement get_request_status.py (6/6 tests passing)`

---

## Integration with jira-issue Skill

### Bridging JSM and JIRA APIs

**Goal:** Ensure jira-issue scripts work gracefully with JSM requests

### Integration Tasks

- [ ] **Integration 1:** Update get_issue.py for JSM detection
  - [ ] Detect if issue is a JSM request (check serviceDeskId)
  - [ ] Show "This is a service request" banner
  - [ ] Display JSM-specific fields (request type, service desk)
  - [ ] Show customer portal link
  - [ ] Add `--as-request` flag to force JSM API usage
  - **Commit:** `feat(jira-issue): add JSM request detection to get_issue`

- [ ] **Integration 2:** Update create_issue.py with JSM awareness
  - [ ] Add `--service-desk` and `--request-type` flags
  - [ ] Detect if project is JSM project
  - [ ] Suggest using create_request.py for JSM projects
  - [ ] Document JSM limitations in help text
  - **Commit:** `feat(jira-issue): add JSM awareness to create_issue`

- [ ] **Integration 3:** Update transition_issue.py
  - [ ] Detect JSM requests
  - [ ] Show warning about using transition_request.py for SLA tracking
  - [ ] Still allow transitions via JIRA API (for backwards compatibility)
  - **Commit:** `feat(jira-issue): add JSM detection to transition_issue`

- [ ] **Integration 4:** Update add_comment.py
  - [ ] Add `--public` and `--internal` flags
  - [ ] Detect JSM requests and use JSM comment API if needed
  - [ ] Show warning about comment visibility
  - **Commit:** `feat(jira-issue): add public/internal comment support`

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 39+ unit tests passing (10 + 8 + 8 + 7 + 6)
- [ ] 5+ integration tests passing
- [ ] Coverage: 85%+

**Scripts:**
- [ ] 5 new scripts implemented
- [ ] All scripts have `--help`
- [ ] All scripts support `--profile`
- [ ] Mutation scripts have `--dry-run`

**Documentation:**
- [ ] SKILL.md complete with examples
- [ ] CLAUDE.md updated
- [ ] GAP_ANALYSIS.md updated
- [ ] All scripts have docstrings

**Integration:**
- [ ] 4 jira-issue scripts updated
- [ ] No breaking changes
- [ ] Graceful fallback to JIRA API

### Progress Tracking

**Test Status:** 0/39 tests passing

**Phase Status:**
- [ ] Setup (3 setup tasks)
- [ ] Phase 2.1: Create Request (1 script, 10 tests)
- [ ] Phase 2.2: Get Request (1 script, 8 tests)
- [ ] Phase 2.3: Transition Request (1 script, 8 tests)
- [ ] Phase 2.4: List Requests (1 script, 7 tests)
- [ ] Phase 2.5: Status History (1 script, 6 tests)
- [ ] Integration (4 updates)
- [ ] Documentation (3 docs)
- [ ] Quality (3 tasks)

---

## Script Summary

| Script | Phase | Tests | Status | Description |
|--------|-------|-------|--------|-------------|
| `create_request.py` | 2.1 | 10 | [ ] | Create service request with request type |
| `get_request.py` | 2.2 | 8 | [ ] | View request with SLA info |
| `transition_request.py` | 2.3 | 8 | [ ] | Change request status with SLA tracking |
| `list_requests.py` | 2.4 | 7 | [ ] | Query/filter service requests |
| `get_request_status.py` | 2.5 | 6 | [ ] | View status change timeline |
| **Total** | - | **39** | 0/39 | - |

---

## JiraClient Methods to Add

```python
# In shared/scripts/lib/jira_client.py

JSM_API_BASE = '/rest/servicedeskapi'

def create_request(self, service_desk_id: str, request_type_id: str,
                   fields: dict, participants: list = None,
                   on_behalf_of: str = None) -> dict:
    """Create a service request via JSM API.

    Args:
        service_desk_id: Service desk ID or key
        request_type_id: Request type ID
        fields: Dictionary of field values (summary, description, custom fields)
        participants: List of participant email addresses (optional)
        on_behalf_of: Create request on behalf of user (optional)

    Returns:
        Created request object with issueKey, issueId, requestType, etc.
    """
    payload = {
        'serviceDeskId': service_desk_id,
        'requestTypeId': request_type_id,
        'requestFieldValues': fields
    }

    if participants:
        payload['requestParticipants'] = participants

    if on_behalf_of:
        payload['raiseOnBehalfOf'] = on_behalf_of

    return self.post(f'{self.JSM_API_BASE}/request', data=payload)

def get_request(self, issue_key: str, expand: list = None) -> dict:
    """Get request details via JSM API.

    Args:
        issue_key: Request key (e.g., 'SD-101')
        expand: List of fields to expand (sla, participant, status, etc.)

    Returns:
        Request object with JSM-specific fields
    """
    params = {}
    if expand:
        params['expand'] = ','.join(expand)

    return self.get(f'{self.JSM_API_BASE}/request/{issue_key}', params=params)

def get_request_status(self, issue_key: str) -> dict:
    """Get request status history.

    Args:
        issue_key: Request key

    Returns:
        Status history with timestamps
    """
    return self.get(f'{self.JSM_API_BASE}/request/{issue_key}/status')

def get_request_transitions(self, issue_key: str) -> list:
    """Get available transitions for request.

    Args:
        issue_key: Request key

    Returns:
        List of available transition objects
    """
    result = self.get(f'{self.JSM_API_BASE}/request/{issue_key}/transition')
    return result.get('values', [])

def transition_request(self, issue_key: str, transition_id: str,
                       comment: str = None, public: bool = True) -> None:
    """Transition a service request.

    Args:
        issue_key: Request key
        transition_id: Transition ID
        comment: Optional comment to add
        public: Whether comment is public (customer-visible)
    """
    payload = {'id': transition_id}

    if comment:
        payload['additionalComment'] = {
            'body': comment,
            'public': public
        }

    self.post(f'{self.JSM_API_BASE}/request/{issue_key}/transition', data=payload)

def list_requests(self, service_desk_id: str, queue_id: str = None,
                  params: dict = None) -> list:
    """List requests for service desk or queue.

    Args:
        service_desk_id: Service desk ID
        queue_id: Optional queue ID to filter
        params: Additional query parameters (requestStatus, searchTerm, etc.)

    Returns:
        List of request objects
    """
    if queue_id:
        # Use queue API (recommended)
        url = f'{self.JSM_API_BASE}/servicedesk/{service_desk_id}/queue/{queue_id}/issue'
    else:
        # Use JQL fallback
        return self.search_issues(f'project=SD-{service_desk_id}', params=params)

    result = self.get(url, params=params or {})
    return result.get('values', [])
```

---

## Helper Functions

### JSM Field Conversion

```python
# In shared/scripts/lib/jsm_utils.py (new file)

from typing import Dict, Any
from .adf_utils import text_to_adf

def convert_fields_to_jsm_format(fields: dict) -> dict:
    """Convert standard field dict to JSM requestFieldValues format.

    Args:
        fields: Standard fields dict with summary, description, etc.

    Returns:
        JSM-formatted requestFieldValues dict
    """
    jsm_fields = {}

    for key, value in fields.items():
        if key == 'description' and isinstance(value, str):
            # Convert plain text to ADF
            jsm_fields[key] = text_to_adf(value)
        else:
            jsm_fields[key] = value

    return jsm_fields

def is_jsm_request(issue: dict) -> bool:
    """Check if an issue is a JSM request.

    Args:
        issue: Issue object from API

    Returns:
        True if issue is a JSM request
    """
    # Check for serviceDeskId in fields
    fields = issue.get('fields', {})
    return 'serviceDeskId' in fields or 'requestType' in fields

def format_sla_time(sla_metric: dict) -> str:
    """Format SLA time remaining/elapsed.

    Args:
        sla_metric: SLA metric object

    Returns:
        Human-readable time string
    """
    ongoing = sla_metric.get('ongoingCycle', {})

    if ongoing.get('breached'):
        return '⚠ BREACHED'

    remaining = ongoing.get('remainingTime', {})
    if remaining:
        millis = remaining.get('millis', 0)
        hours = millis // 3600000
        minutes = (millis % 3600000) // 60000

        if hours > 0:
            return f'⏱ {hours}h {minutes}m remaining'
        else:
            return f'⏱ {minutes}m remaining'

    return '✓ Met'

def calculate_status_duration(status_history: list) -> dict:
    """Calculate time spent in each status.

    Args:
        status_history: List of status change objects

    Returns:
        Dict mapping status names to duration in milliseconds
    """
    durations = {}

    for i, status in enumerate(status_history):
        status_name = status['status']
        start_time = status['statusDate']['epochMillis']

        if i + 1 < len(status_history):
            end_time = status_history[i + 1]['statusDate']['epochMillis']
        else:
            # Current status - use now
            import time
            end_time = int(time.time() * 1000)

        duration = end_time - start_time
        durations[status_name] = duration

    return durations
```

---

## Commit Strategy

### Commit Types

**test:** Adding or updating tests
- `test(jira-jsm): add failing tests for create_request`

**feat:** Implementing features
- `feat(jira-jsm): implement create_request.py (10/10 tests passing)`

**docs:** Documentation updates
- `docs(jira-jsm): add request management examples to SKILL.md`

**fix:** Bug fixes
- `fix(jira-jsm): handle missing requestType field gracefully`

---

## API Sources

- [JSM Request API](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-request/)
- [Create Request Endpoint](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-request/#api-rest-servicedeskapi-request-post)
- [Request Transitions](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-request/#api-rest-servicedeskapi-request-issueIdOrKey-transition-post)
- [JSM vs JIRA API Differences](https://support.atlassian.com/jira/kb/how-to-set-request-type-when-creating-an-issue-via-rest-api-using-rest-api-2-issue-endpoint/)
- [JSM Customer Portal](https://developer.atlassian.com/cloud/jira/service-desk/customer-portal/)

---

**Plan Version:** 1.0
**Created:** 2025-12-25
**Last Updated:** 2025-12-25
**Status:** PLANNED - Ready for TDD implementation (Phase 2 of JSM support)
