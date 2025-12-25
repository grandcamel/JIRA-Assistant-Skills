# JSM Phase 1: Service Desk Core Operations - TDD Implementation Plan

## Overview

**Objective:** Implement foundational Jira Service Management (JSM) service desk discovery and request type management using Test-Driven Development (TDD)

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
1. **Phase 1.1: List Service Desks** (Foundation - discover available service desks)
2. **Phase 1.2: Get Service Desk Details** (Service desk information with capabilities)
3. **Phase 1.3: List Request Types** (Discover available request types per service desk)
4. **Phase 1.4: Get Request Type Details** (Request type information and configuration)
5. **Phase 1.5: Get Request Type Fields** (Field requirements for creating requests)

---

## JIRA API Reference

### Endpoints

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| GET | `/rest/servicedeskapi/servicedesk` | List all service desks | **Critical** |
| GET | `/rest/servicedeskapi/servicedesk/{id}` | Get service desk details | High |
| GET | `/rest/servicedeskapi/info` | Get JSM installation info | Low |
| GET | `/rest/servicedeskapi/servicedesk/{id}/requesttype` | List request types for service desk | **Critical** |
| GET | `/rest/servicedeskapi/servicedesk/{id}/requesttype/{id}` | Get request type details | High |
| GET | `/rest/servicedeskapi/servicedesk/{id}/requesttype/{id}/field` | Get fields for request type | **Critical** |

### Service Desk Structure

```json
{
  "id": "1",
  "projectId": "10000",
  "projectName": "IT Service Desk",
  "projectKey": "ITS",
  "_links": {
    "self": "https://site.atlassian.net/rest/servicedeskapi/servicedesk/1"
  }
}
```

### Request Type Structure

```json
{
  "id": "25",
  "name": "Get IT help",
  "description": "Request help from your IT team",
  "helpText": "Please provide detailed information about your issue",
  "issueTypeId": "10001",
  "serviceDeskId": "1",
  "groupIds": ["1"],
  "icon": {
    "id": "10000",
    "_links": {}
  },
  "_links": {
    "self": "https://site.atlassian.net/rest/servicedeskapi/servicedesk/1/requesttype/25"
  }
}
```

### Request Type Fields

```json
{
  "requestTypeFields": [
    {
      "fieldId": "summary",
      "name": "Summary",
      "description": "Brief description of the issue",
      "required": true,
      "jiraSchema": {
        "type": "string",
        "system": "summary"
      },
      "validValues": [],
      "defaultValues": [],
      "presets": []
    },
    {
      "fieldId": "customfield_10050",
      "name": "Category",
      "description": "Issue category",
      "required": true,
      "jiraSchema": {
        "type": "option",
        "custom": "com.atlassian.jira.plugin.system.customfieldtypes:select",
        "customId": 10050
      },
      "validValues": [
        {"value": "Hardware", "label": "Hardware"},
        {"value": "Software", "label": "Software"}
      ],
      "defaultValues": [],
      "presets": []
    }
  ],
  "canRaiseOnBehalfOf": false,
  "canAddRequestParticipants": true
}
```

### List Service Desks Response

```json
{
  "size": 3,
  "start": 0,
  "limit": 50,
  "isLastPage": true,
  "_links": {},
  "values": [
    {
      "id": "1",
      "projectId": "10000",
      "projectName": "IT Service Desk",
      "projectKey": "ITS"
    },
    {
      "id": "2",
      "projectId": "10001",
      "projectName": "HR Service Desk",
      "projectKey": "HR"
    },
    {
      "id": "3",
      "projectId": "10002",
      "projectName": "Facilities",
      "projectKey": "FAC"
    }
  ]
}
```

---

## Test Infrastructure Setup

### Initial Setup Tasks

- [ ] **Setup 1.1:** Create skill structure
  - [ ] Create `.claude/skills/jira-jsm/` directory
  - [ ] Create `scripts/` subdirectory
  - [ ] Create `tests/` subdirectory
  - [ ] Create `references/` subdirectory
  - [ ] Create `SKILL.md` skeleton
  - **Commit:** `feat(jira-jsm): create skill structure`

- [ ] **Setup 1.2:** Create test infrastructure
  - [ ] Create `tests/conftest.py` with shared fixtures
  - [ ] Mock JiraClient fixture for JSM endpoints
  - [ ] Sample service desk fixture
  - [ ] Sample request types fixture
  - [ ] Sample request type fields fixture
  - **Commit:** `test(jira-jsm): add pytest fixtures`

- [ ] **Setup 1.3:** Add JiraClient methods for JSM
  - [ ] `get_service_desks()` - List all service desks
  - [ ] `get_service_desk(id)` - Get service desk details
  - [ ] `get_jsm_info()` - Get JSM installation info
  - [ ] `get_request_types(service_desk_id)` - List request types
  - [ ] `get_request_type(service_desk_id, request_type_id)` - Get request type details
  - [ ] `get_request_type_fields(service_desk_id, request_type_id)` - Get fields
  - **Commit:** `feat(shared): add JSM service desk API methods to JiraClient`

---

## Phase 1.1: List Service Desks

### Feature 1.1.1: List All Service Desks

**Script:** `list_service_desks.py`

**JIRA API:**
- `GET /rest/servicedeskapi/servicedesk`

**Test File:** `tests/test_list_service_desks.py`

**Test Cases:**
```python
def test_list_all_service_desks():
    """Test fetching all available service desks."""
    # Should return list of service desk objects

def test_service_desk_has_required_fields():
    """Test that each service desk has id, projectId, projectName, projectKey."""

def test_format_text_output():
    """Test human-readable table output."""

def test_format_json_output():
    """Test JSON output format."""

def test_filter_by_project_key():
    """Test filtering service desks by project key pattern."""

def test_empty_service_desks():
    """Test output when no service desks exist."""

def test_pagination_handling():
    """Test handling paginated results (limit/start)."""
```

**CLI Interface:**
```bash
python list_service_desks.py
python list_service_desks.py --output json
python list_service_desks.py --filter "IT"
python list_service_desks.py --project-key ITS
```

**Output Example:**
```
Available Service Desks:

ID  Project Key  Project Name           Project ID
──  ───────────  ─────────────────────  ──────────
1   ITS          IT Service Desk        10000
2   HR           HR Service Desk        10001
3   FAC          Facilities             10002

Total: 3 service desks
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Shows all available service desks
- [ ] Supports text and JSON output
- [ ] Optional project key filtering
- [ ] Handles pagination correctly
- [ ] Shows helpful error if JSM not enabled

**Commits:**
1. `test(jira-jsm): add failing tests for list_service_desks`
2. `feat(jira-jsm): implement list_service_desks.py (7/7 tests passing)`

---

### Feature 1.1.2: Get JSM Installation Info

**Script:** `get_jsm_info.py`

**JIRA API:**
- `GET /rest/servicedeskapi/info`

**Test File:** `tests/test_get_jsm_info.py`

**Test Cases:**
```python
def test_get_jsm_info():
    """Test fetching JSM installation information."""

def test_jsm_info_version():
    """Test that version information is present."""

def test_format_text_output():
    """Test human-readable output."""

def test_format_json_output():
    """Test JSON output format."""

def test_jsm_not_enabled():
    """Test error when JSM is not enabled."""
```

**CLI Interface:**
```bash
python get_jsm_info.py
python get_jsm_info.py --output json
```

**Acceptance Criteria:**
- [ ] All 5 tests pass
- [ ] Shows JSM version and capabilities
- [ ] Detects if JSM is not enabled

**Commits:**
1. `test(jira-jsm): add failing tests for get_jsm_info`
2. `feat(jira-jsm): implement get_jsm_info.py (5/5 tests passing)`

---

### Phase 1.1 Completion

- [ ] **Phase 1.1 Summary:**
  - [ ] 2 scripts implemented (list_service_desks, get_jsm_info)
  - [ ] 12 tests passing
  - [ ] JiraClient methods added (3 methods)
  - **Commit:** `docs(jira-jsm): complete Phase 1.1 - Service Desk Discovery`

---

## Phase 1.2: Get Service Desk Details

### Feature 1.2.1: Get Service Desk by ID

**Script:** `get_service_desk.py`

**JIRA API:**
- `GET /rest/servicedeskapi/servicedesk/{id}`

**Test File:** `tests/test_get_service_desk.py`

**Test Cases:**
```python
def test_get_service_desk_by_id():
    """Test fetching service desk by ID."""

def test_get_service_desk_by_project_key():
    """Test fetching service desk by project key (lookup)."""

def test_service_desk_details():
    """Test that all detail fields are present."""

def test_format_text_output():
    """Test human-readable output with full details."""

def test_format_json_output():
    """Test JSON output format."""

def test_service_desk_not_found():
    """Test error when service desk ID doesn't exist."""

def test_show_request_type_count():
    """Test showing number of request types available."""
```

**CLI Interface:**
```bash
python get_service_desk.py 1
python get_service_desk.py --project-key ITS
python get_service_desk.py 1 --output json
python get_service_desk.py 1 --show-request-types
```

**Output Example:**
```
Service Desk Details:

ID:           1
Project ID:   10000
Project Key:  ITS
Project Name: IT Service Desk

Capabilities:
  - Request Management
  - SLA Tracking
  - Customer Portal

Request Types: 5 available
Use: python list_request_types.py 1
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Fetches service desk by ID or project key
- [ ] Shows comprehensive service desk details
- [ ] Supports text and JSON output
- [ ] Shows request type count
- [ ] Helpful error for invalid IDs

**Commits:**
1. `test(jira-jsm): add failing tests for get_service_desk`
2. `feat(jira-jsm): implement get_service_desk.py (7/7 tests passing)`

---

### Phase 1.2 Completion

- [ ] **Phase 1.2 Summary:**
  - [ ] 1 script implemented (get_service_desk)
  - [ ] 7 tests passing (19 total)
  - [ ] Service desk lookup by ID or project key
  - **Commit:** `docs(jira-jsm): complete Phase 1.2 - Service Desk Details`

---

## Phase 1.3: List Request Types

### Feature 1.3.1: List Request Types for Service Desk

**Script:** `list_request_types.py`

**JIRA API:**
- `GET /rest/servicedeskapi/servicedesk/{id}/requesttype`

**Test File:** `tests/test_list_request_types.py`

**Test Cases:**
```python
def test_list_request_types():
    """Test fetching all request types for a service desk."""

def test_request_type_required_fields():
    """Test that each request type has id, name, description, issueTypeId."""

def test_format_text_output():
    """Test human-readable table output."""

def test_format_json_output():
    """Test JSON output format."""

def test_filter_by_name():
    """Test filtering request types by name pattern."""

def test_show_issue_type_mapping():
    """Test showing underlying JIRA issue type."""

def test_service_desk_not_found():
    """Test error when service desk doesn't exist."""

def test_empty_request_types():
    """Test output when service desk has no request types."""
```

**CLI Interface:**
```bash
python list_request_types.py 1
python list_request_types.py --project-key ITS
python list_request_types.py 1 --output json
python list_request_types.py 1 --filter "incident"
python list_request_types.py 1 --show-issue-types
```

**Output Example:**
```
Request Types for IT Service Desk (ITS):

ID  Name                    Description                          Issue Type
──  ──────────────────────  ───────────────────────────────────  ──────────
25  Get IT help             Request help from your IT team       Service Request
26  Report a system problem Report an incident with IT systems   Incident
27  Request new software    Request new software installation    Service Request
28  Hardware issue          Report hardware problems             Incident
29  Access request          Request access to systems            Service Request

Total: 5 request types
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Shows all request types for service desk
- [ ] Supports text and JSON output
- [ ] Optional name filtering
- [ ] Shows issue type mapping
- [ ] Handles service desk lookup by project key

**Commits:**
1. `test(jira-jsm): add failing tests for list_request_types`
2. `feat(jira-jsm): implement list_request_types.py (8/8 tests passing)`

---

### Phase 1.3 Completion

- [ ] **Phase 1.3 Summary:**
  - [ ] 1 script implemented (list_request_types)
  - [ ] 8 tests passing (27 total)
  - [ ] Request type discovery functionality
  - **Commit:** `docs(jira-jsm): complete Phase 1.3 - List Request Types`

---

## Phase 1.4: Get Request Type Details

### Feature 1.4.1: Get Request Type by ID

**Script:** `get_request_type.py`

**JIRA API:**
- `GET /rest/servicedeskapi/servicedesk/{id}/requesttype/{id}`

**Test File:** `tests/test_get_request_type.py`

**Test Cases:**
```python
def test_get_request_type():
    """Test fetching request type details."""

def test_request_type_details():
    """Test that all detail fields are present."""

def test_format_text_output():
    """Test human-readable output with full details."""

def test_format_json_output():
    """Test JSON output format."""

def test_request_type_not_found():
    """Test error when request type doesn't exist."""

def test_show_help_text():
    """Test showing request type help text for customers."""

def test_show_icon_info():
    """Test showing request type icon information."""
```

**CLI Interface:**
```bash
python get_request_type.py 1 25
python get_request_type.py --project-key ITS --request-type-name "Get IT help"
python get_request_type.py 1 25 --output json
python get_request_type.py 1 25 --show-fields
```

**Output Example:**
```
Request Type Details:

ID:             25
Name:           Get IT help
Description:    Request help from your IT team
Help Text:      Please provide detailed information about your issue

Service Desk:   IT Service Desk (ITS)
Issue Type ID:  10001
Groups:         1

Portal Configuration:
  Icon ID:      10000
  Visibility:   All customers

To see required fields:
  python get_request_type_fields.py 1 25
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Shows comprehensive request type details
- [ ] Lookup by ID or name
- [ ] Shows portal configuration
- [ ] Helpful error messages

**Commits:**
1. `test(jira-jsm): add failing tests for get_request_type`
2. `feat(jira-jsm): implement get_request_type.py (7/7 tests passing)`

---

### Phase 1.4 Completion

- [ ] **Phase 1.4 Summary:**
  - [ ] 1 script implemented (get_request_type)
  - [ ] 7 tests passing (34 total)
  - [ ] Request type detail retrieval
  - **Commit:** `docs(jira-jsm): complete Phase 1.4 - Request Type Details`

---

## Phase 1.5: Get Request Type Fields

### Feature 1.5.1: Get Fields for Request Type

**Script:** `get_request_type_fields.py`

**JIRA API:**
- `GET /rest/servicedeskapi/servicedesk/{id}/requesttype/{id}/field`

**Test File:** `tests/test_get_request_type_fields.py`

**Test Cases:**
```python
def test_get_request_type_fields():
    """Test fetching fields for a request type."""

def test_required_fields_marked():
    """Test that required fields are clearly marked."""

def test_field_types():
    """Test that field types are correctly identified."""

def test_valid_values():
    """Test showing valid values for select/option fields."""

def test_default_values():
    """Test showing default values when present."""

def test_format_text_output():
    """Test human-readable table output with field details."""

def test_format_json_output():
    """Test JSON output format."""

def test_filter_required_only():
    """Test showing only required fields."""

def test_show_field_ids():
    """Test showing field IDs for API usage."""
```

**CLI Interface:**
```bash
python get_request_type_fields.py 1 25
python get_request_type_fields.py --project-key ITS --request-type-name "Get IT help"
python get_request_type_fields.py 1 25 --output json
python get_request_type_fields.py 1 25 --required-only
python get_request_type_fields.py 1 25 --show-field-ids
python get_request_type_fields.py 1 25 --show-valid-values
```

**Output Example:**
```
Request Type Fields: Get IT help (IT Service Desk)

Required Fields:
──────────────────────────────────────────────────────────────────
Field ID          Name           Type      Valid Values
────────────────  ─────────────  ────────  ──────────────────────
summary           Summary        string    (any text)
description       Description    string    (any text)
customfield_10050 Category       option    Hardware, Software, Network
customfield_10051 Priority       option    Low, Medium, High, Critical

Optional Fields:
──────────────────────────────────────────────────────────────────
Field ID          Name           Type      Valid Values
────────────────  ─────────────  ────────  ──────────────────────
customfield_10052 Affected Users number    (any number)
attachment        Attachment     array     (file uploads)

Configuration:
  Can raise on behalf of: No
  Can add participants:   Yes

Total: 4 required fields, 2 optional fields
```

**Acceptance Criteria:**
- [ ] All 9 tests pass
- [ ] Shows all fields with types and requirements
- [ ] Clearly marks required vs optional fields
- [ ] Shows valid values for constrained fields
- [ ] Shows default values when present
- [ ] Filter to show only required fields
- [ ] Supports text and JSON output

**Commits:**
1. `test(jira-jsm): add failing tests for get_request_type_fields`
2. `feat(jira-jsm): implement get_request_type_fields.py (9/9 tests passing)`

---

### Phase 1.5 Completion

- [ ] **Phase 1.5 Summary:**
  - [ ] 1 script implemented (get_request_type_fields)
  - [ ] 9 tests passing (43 total)
  - [ ] Field discovery for request creation
  - **Commit:** `docs(jira-jsm): complete Phase 1.5 - Request Type Fields`

---

## Integration & Documentation Updates

### Integration Tasks

- [ ] **Integration 1:** Update shared library
  - [ ] Add JSM API base URL constant (`JSM_API_BASE = '/rest/servicedeskapi'`)
  - [ ] Add JSM-specific error handling
  - [ ] Add helper methods for service desk ID lookup
  - [ ] **Commit:** `feat(shared): add JSM API support to JiraClient`

- [ ] **Integration 2:** Create JSM utilities
  - [ ] Add `jsm_utils.py` with helper functions
  - [ ] Service desk ID to project key mapping
  - [ ] Request type name to ID lookup
  - [ ] Field validation helpers
  - [ ] **Commit:** `feat(jira-jsm): add JSM utility functions`

- [ ] **Integration 3:** Profile configuration
  - [ ] Document `use_service_management` flag usage
  - [ ] Add example JSM profile configuration
  - [ ] **Commit:** `docs(shared): add JSM profile configuration examples`

### Documentation Updates

- [ ] **Docs 1:** Create comprehensive SKILL.md
  - [ ] "When to use this skill" section
  - [ ] "What this skill does" section
  - [ ] "Available scripts" with descriptions
  - [ ] "Examples" with realistic workflows
  - [ ] Configuration notes
  - [ ] Related skills section
  - [ ] JSM vs JIRA differences
  - [ ] **Commit:** `docs(jira-jsm): create comprehensive SKILL.md`

- [ ] **Docs 2:** Create API reference
  - [ ] Create `references/jsm_api_reference.md`
  - [ ] Document all Phase 1 endpoints
  - [ ] Sample request/response payloads
  - [ ] Error codes and handling
  - [ ] **Commit:** `docs(jira-jsm): add JSM API reference documentation`

- [ ] **Docs 3:** Update root CLAUDE.md
  - [ ] Add jira-jsm to project overview
  - [ ] Add JSM usage patterns section
  - [ ] **Commit:** `docs: update CLAUDE.md with jira-jsm skill`

- [ ] **Docs 4:** Update GAP_ANALYSIS.md
  - [ ] Mark Phase 1 items as completed
  - [ ] Update coverage metrics for Categories A and C
  - [ ] **Commit:** `docs: update GAP_ANALYSIS.md - JSM Phase 1 complete`

### Testing & Quality

- [ ] **Quality 1:** Integration tests
  - [ ] End-to-end: List service desks → Get details → List request types → Get fields
  - [ ] Live integration test framework in `tests/live_integration/test_service_desk_core.py`
  - [ ] Minimum 5 integration tests covering happy paths
  - [ ] **Commit:** `test(jira-jsm): add live integration tests for Phase 1`

- [ ] **Quality 2:** Coverage validation
  - [ ] Run `pytest --cov=.claude/skills/jira-jsm --cov-report=html`
  - [ ] Verify ≥85% coverage target
  - [ ] Document uncovered code with justification
  - [ ] **Commit:** `test(jira-jsm): verify 85%+ test coverage`

- [ ] **Quality 3:** Error handling review
  - [ ] All scripts use try/except with JiraError
  - [ ] Validation before API calls
  - [ ] Helpful error messages with suggestions
  - [ ] JSM-not-enabled detection
  - [ ] **Commit:** `fix(jira-jsm): improve error handling and validation`

- [ ] **Quality 4:** CLI consistency check
  - [ ] All scripts have `--help`
  - [ ] All scripts support `--profile`
  - [ ] All scripts support `--output json`
  - [ ] Consistent argument naming conventions
  - [ ] **Commit:** `refactor(jira-jsm): ensure CLI consistency`

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 43+ unit tests passing
- [ ] 5+ integration tests passing
- [ ] Coverage ≥ 85%
- [ ] All tests use proper mocking

**Scripts:**
- [ ] 6 new scripts implemented
- [ ] All scripts have `--help`
- [ ] All scripts support `--profile`
- [ ] All scripts support `--output json`
- [ ] All scripts have proper error handling

**Documentation:**
- [ ] SKILL.md complete with examples
- [ ] API reference documentation
- [ ] CLAUDE.md updated
- [ ] GAP_ANALYSIS.md updated
- [ ] All scripts have docstrings

**Integration:**
- [ ] JiraClient extended with 6+ JSM methods
- [ ] JSM utilities module created
- [ ] No breaking changes to existing skills

### Progress Tracking

**Test Status:** 0/43 unit tests passing (0%) + 0 integration tests

**Phase Status:**
- [ ] Phase 1.1: Service Desk Discovery (2 scripts, 12 tests)
- [ ] Phase 1.2: Service Desk Details (1 script, 7 tests)
- [ ] Phase 1.3: List Request Types (1 script, 8 tests)
- [ ] Phase 1.4: Request Type Details (1 script, 7 tests)
- [ ] Phase 1.5: Request Type Fields (1 script, 9 tests)
- [ ] Integration (3 updates)
- [ ] Documentation (4 docs)
- [ ] Quality (4 tasks)

---

## Script Summary

| Script | Phase | Tests | Description |
|--------|-------|-------|-------------|
| `list_service_desks.py` | 1.1 | 7 | List all JSM service desks |
| `get_jsm_info.py` | 1.1 | 5 | Get JSM installation information |
| `get_service_desk.py` | 1.2 | 7 | Get service desk details by ID or key |
| `list_request_types.py` | 1.3 | 8 | List request types for service desk |
| `get_request_type.py` | 1.4 | 7 | Get request type details |
| `get_request_type_fields.py` | 1.5 | 9 | Get fields for request type |
| **Total** | - | **43** | - |

---

## JiraClient Methods to Add

```python
# In shared/scripts/lib/jira_client.py

# JSM API base URL
JSM_API_BASE = '/rest/servicedeskapi'

def get_service_desks(self, start: int = 0, limit: int = 50) -> dict:
    """Get all JSM service desks with pagination."""
    params = {'start': start, 'limit': limit}
    return self.get(f'{JSM_API_BASE}/servicedesk', params=params)

def get_service_desk(self, service_desk_id: str) -> dict:
    """Get a specific service desk by ID."""
    return self.get(f'{JSM_API_BASE}/servicedesk/{service_desk_id}')

def get_jsm_info(self) -> dict:
    """Get JSM installation information."""
    return self.get(f'{JSM_API_BASE}/info')

def get_request_types(self, service_desk_id: str,
                      start: int = 0, limit: int = 50) -> dict:
    """Get request types for a service desk."""
    params = {'start': start, 'limit': limit}
    return self.get(
        f'{JSM_API_BASE}/servicedesk/{service_desk_id}/requesttype',
        params=params
    )

def get_request_type(self, service_desk_id: str,
                     request_type_id: str) -> dict:
    """Get a specific request type."""
    return self.get(
        f'{JSM_API_BASE}/servicedesk/{service_desk_id}/requesttype/{request_type_id}'
    )

def get_request_type_fields(self, service_desk_id: str,
                            request_type_id: str) -> dict:
    """Get fields for a request type."""
    return self.get(
        f'{JSM_API_BASE}/servicedesk/{service_desk_id}/requesttype/{request_type_id}/field'
    )

def lookup_service_desk_by_project_key(self, project_key: str) -> dict:
    """Lookup service desk ID by project key."""
    service_desks = self.get_service_desks()
    for sd in service_desks.get('values', []):
        if sd.get('projectKey') == project_key:
            return sd
    raise JiraError(f"No service desk found for project key: {project_key}")
```

---

## Commit Strategy

### Commit Types

**test:** Adding or updating tests
- `test(jira-jsm): add failing tests for list_service_desks`

**feat:** Implementing features
- `feat(jira-jsm): implement list_service_desks.py (7/7 tests passing)`

**docs:** Documentation updates
- `docs(jira-jsm): add service desk examples to SKILL.md`

**fix:** Bug fixes
- `fix(jira-jsm): handle pagination edge cases`

**refactor:** Code improvements without changing behavior
- `refactor(jira-jsm): extract service desk lookup to utility function`

---

## API Sources

- [Jira Service Management Cloud REST API](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-servicedesk/)
- [Service Desk API Reference](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-servicedesk/#api-rest-servicedeskapi-servicedesk-get)
- [Request Type API Reference](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-requesttype/)
- [JSM Data Center REST API Reference](https://docs.atlassian.com/jira-servicedesk/REST/5.15.2/)
- [JSM API Changelog](https://developer.atlassian.com/cloud/jira/service-desk/changelog/)

---

## Related Phases

### Future Phases (Not in Scope)

**Phase 2: Request Management** - Creating and managing service requests
- `create_request.py` - Create requests using request types
- `get_request.py` - Get request details with SLA info
- `transition_request.py` - Transition requests with SLA awareness

**Phase 3: SLA Management** - SLA tracking and reporting
- `get_sla.py` - Get SLA status for requests
- `check_sla_breach.py` - Check SLA breach status
- `sla_report.py` - Generate SLA compliance reports

**Phase 4: Comments & Customer Communication** - Public/internal comments
- `add_request_comment.py` - Add comments with visibility control
- `get_request_comments.py` - Get comments with visibility info

**Phase 5: Queues & Workflows** - Agent work queues
- `list_queues.py` - List agent work queues
- `get_queue_issues.py` - Get issues in queue

---

## Notes

### JSM vs JIRA Differences

**Key Considerations:**
1. **API Base:** JSM uses `/rest/servicedeskapi/` not `/rest/api/3/`
2. **Request Types:** Required for creating requests via JSM API
3. **Hidden Fields:** Request types can hide/show fields dynamically
4. **Customer Portal:** Different permissions and visibility model
5. **SLA Tracking:** Automatic SLA calculation (not in Phase 1)
6. **Public/Internal Comments:** Different comment visibility model (not in Phase 1)

### Testing Strategy

**Unit Tests:**
- Mock all JIRA API responses
- Test error conditions thoroughly
- Test output formatting
- Test CLI argument parsing

**Integration Tests:**
- Require live JSM instance
- Use `@pytest.mark.integration` decorator
- Skip if credentials not configured
- Test happy path workflows

### Configuration Requirements

**Profile Setup:**
```json
{
  "name": "JSM Test",
  "jira_url": "https://yoursite.atlassian.net",
  "email": "test@example.com",
  "api_token": "your-api-token",
  "use_service_management": true
}
```

---

**Plan Version:** 1.0
**Created:** 2025-12-25
**Last Updated:** 2025-12-25
**Status:** NOT STARTED - Ready for Phase 1.1 implementation
**Estimated Effort:** 25-30 hours over 2-3 weeks
