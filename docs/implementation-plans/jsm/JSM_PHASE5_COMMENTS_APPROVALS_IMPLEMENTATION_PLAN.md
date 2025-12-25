# JSM Phase 5: Comments & Approvals - TDD Implementation Plan

## Overview

**Objective:** Implement JSM-specific comment management (public/internal distinction) and approval workflows using Test-Driven Development (TDD)

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
1. **Phase 5.1: Add Request Comment** (JSM public/internal comments)
2. **Phase 5.2: Get Request Comments** (Comments with visibility info)
3. **Phase 5.3: Get Pending Approvals** (List approval requests)
4. **Phase 5.4: Approve Request** (Approve approval requests)
5. **Phase 5.5: Decline Request** (Decline approval requests)
6. **Phase 5.6: List All Pending Approvals** (Agent queue view)

---

## Current State Analysis

### Existing Infrastructure

**jira-collaborate skill (4 scripts):**
- `add_comment.py` - Uses `/rest/api/3/issue/{key}/comment` (JIRA API)
- Does NOT support JSM public/internal distinction properly

**Gap:** Standard JIRA comments don't map to JSM's customer portal visibility model.

**JSM Difference:**
- **JIRA API** (`/rest/api/3/`): Uses role/group visibility
- **JSM API** (`/rest/servicedeskapi/`): Uses `public: true/false` flag
  - `public: true` → Visible in customer portal
  - `public: false` → Internal (agent-only)

### New Skill: jira-jsm

This implementation plan creates the foundation for the `jira-jsm` skill, which will eventually include:
- Service desk management
- Request types
- Customer management
- Organizations
- **Phase 5: Comments & Approvals** (this plan)
- SLA management
- Queues
- Knowledge base

---

## JIRA API Reference

### JSM Comment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rest/servicedeskapi/request/{key}/comment` | Get comments with public/internal visibility |
| POST | `/rest/servicedeskapi/request/{key}/comment` | Add comment (public or internal) |
| GET | `/rest/servicedeskapi/request/{key}/comment/{id}` | Get specific comment details |

### Add Request Comment (JSM)

**Request Body:**
```json
{
  "body": "Your issue has been resolved. Please verify the fix.",
  "public": true
}
```

**Key Differences from JIRA API:**
- Uses `public: boolean` instead of `visibility` object
- `public: true` → Customer can see in portal
- `public: false` → Internal (agents only)
- Simpler model than role/group visibility

**Response:**
```json
{
  "id": "10001",
  "body": "Your issue has been resolved.",
  "public": true,
  "author": {
    "accountId": "5b10a2844c20165700ede21g",
    "displayName": "Alice Smith"
  },
  "created": "2025-01-17T10:30:00.000+0000"
}
```

### Get Request Comments

**Endpoint:** `GET /rest/servicedeskapi/request/{key}/comment`

**Query Parameters:**
| Parameter | Description |
|-----------|-------------|
| `public` | Filter by visibility: `true`, `false`, or omit for all |
| `internal` | Deprecated - use `public` instead |
| `expand` | Additional fields: `renderedBody`, `request` |
| `start` | Pagination start index |
| `limit` | Results per page (max 100) |

**Response:**
```json
{
  "values": [
    {
      "id": "10001",
      "body": "Customer-visible update",
      "public": true,
      "author": {...},
      "created": "2025-01-17T10:30:00.000+0000"
    },
    {
      "id": "10002",
      "body": "Internal note: escalate to Tier 2",
      "public": false,
      "author": {...},
      "created": "2025-01-17T11:00:00.000+0000"
    }
  ],
  "start": 0,
  "limit": 100,
  "isLastPage": true
}
```

### Approval Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rest/servicedeskapi/request/{key}/approval` | Get pending approvals for request |
| GET | `/rest/servicedeskapi/request/{key}/approval/{approvalId}` | Get specific approval details |
| POST | `/rest/servicedeskapi/request/{key}/approval/{approvalId}` | Approve or decline approval |

### Get Approvals Response

```json
{
  "values": [
    {
      "id": "10050",
      "name": "Change Approval",
      "finalDecision": "pending",
      "canAnswerApproval": true,
      "approvers": [
        {
          "accountId": "5b10a2844c20165700ede21g",
          "displayName": "Manager Alice"
        }
      ],
      "createdDate": "2025-01-17T09:00:00.000+0000",
      "completedDate": null
    }
  ]
}
```

### Approval Decision Request

**Endpoint:** `POST /rest/servicedeskapi/request/{key}/approval/{approvalId}`

**Request Body:**
```json
{
  "decision": "approve"
}
```

**Valid Decisions:**
- `approve` - Approve the approval request
- `decline` - Decline the approval request

**Response:**
```json
{
  "id": "10050",
  "name": "Change Approval",
  "finalDecision": "approve",
  "canAnswerApproval": false,
  "approvers": [...],
  "createdDate": "2025-01-17T09:00:00.000+0000",
  "completedDate": "2025-01-17T14:30:00.000+0000"
}
```

---

## Test Infrastructure Setup

### Initial Setup Tasks

- [ ] **Setup 1.1:** Create skill structure
  - [ ] Create `.claude/skills/jira-jsm/` directory
  - [ ] Create `scripts/` subdirectory
  - [ ] Create `tests/` subdirectory
  - [ ] Create `SKILL.md` skeleton
  - **Commit:** `feat(jira-jsm): create skill structure for JSM support`

- [ ] **Setup 1.2:** Create test fixtures
  - [ ] Create `tests/conftest.py` with shared fixtures
  - [ ] Mock JiraClient fixture for JSM endpoints
  - [ ] Sample JSM comment response fixtures (public/internal)
  - [ ] Sample approval response fixtures (pending/approved/declined)
  - [ ] Sample request fixtures with JSM-specific fields
  - **Commit:** `test(jira-jsm): add test fixtures for comments and approvals`

- [ ] **Setup 1.3:** Add JiraClient methods for JSM APIs
  - [ ] `add_request_comment(issue_key, body, public)` - Add JSM comment
  - [ ] `get_request_comments(issue_key, public, start, limit)` - Get JSM comments
  - [ ] `get_request_comment(issue_key, comment_id)` - Get specific comment
  - [ ] `get_request_approvals(issue_key)` - Get pending approvals
  - [ ] `get_request_approval(issue_key, approval_id)` - Get approval details
  - [ ] `approve_request(issue_key, approval_id)` - Approve approval
  - [ ] `decline_request(issue_key, approval_id)` - Decline approval
  - **Commit:** `feat(shared): add JSM comment and approval API methods`

---

## Phase 5.1: Add Request Comment

### Feature 5.1: Add JSM Comment with Public/Internal Flag

**Script:** `add_request_comment.py`

**JIRA API:**
- `POST /rest/servicedeskapi/request/{key}/comment`

**Test File:** `tests/test_add_request_comment.py`

**Test Cases:**
```python
def test_add_public_comment():
    """Test adding public (customer-visible) comment."""
    # Should POST with public: true

def test_add_internal_comment():
    """Test adding internal (agent-only) comment."""
    # Should POST with public: false

def test_add_comment_default_public():
    """Test default behavior when --internal not specified."""
    # Should default to public: true (customer-visible)

def test_add_comment_with_body():
    """Test comment body handling."""
    # Should send plain text body (JSM API doesn't require ADF)

def test_add_comment_multiline():
    """Test multiline comment text."""
    # Should preserve line breaks

def test_add_comment_issue_not_found():
    """Test error when request doesn't exist."""
    # Should raise NotFoundError

def test_add_comment_not_service_desk():
    """Test error when issue is not a JSM request."""
    # Should raise JiraError with helpful message

def test_add_comment_output_format():
    """Test output shows visibility clearly."""
    # Should indicate if comment is public or internal

def test_add_comment_from_stdin():
    """Test reading comment body from stdin."""
    # Support for piping comment text

def test_add_comment_from_file():
    """Test reading comment from file."""
    # --body-file option
```

**CLI Interface:**
```bash
# Add public (customer-visible) comment (default)
python add_request_comment.py REQ-123 --body "Your issue has been resolved."

# Add internal (agent-only) comment
python add_request_comment.py REQ-123 --body "Escalating to Tier 2" --internal

# Multiline comment
python add_request_comment.py REQ-123 --body "Issue resolved.

Root cause: Database connection timeout.
Fix: Increased timeout to 30s."

# From stdin
echo "Waiting for vendor response" | python add_request_comment.py REQ-123 --internal

# From file
python add_request_comment.py REQ-123 --body-file update.txt
```

**Output Example:**
```
Added comment to REQ-123 (ID: 10001)

Visibility: Public (Customer Portal)
Body:
  Your issue has been resolved. Please verify the fix.

Note: This comment is visible to customers in the service portal.
```

**Output Example (Internal):**
```
Added comment to REQ-123 (ID: 10002)

Visibility: Internal (Agents Only)
Body:
  Escalating to Tier 2 - requires database access review.

Note: This comment is NOT visible to customers.
```

**Acceptance Criteria:**
- [ ] All 10 tests pass
- [ ] Adds public comments (customer-visible)
- [ ] Adds internal comments (agent-only)
- [ ] Clear visibility indication in output
- [ ] Supports multiline text
- [ ] Supports stdin and file input

**Commits:**
1. `test(jira-jsm): add failing tests for add_request_comment`
2. `feat(jira-jsm): implement add_request_comment.py (10/10 tests passing)`

---

## Phase 5.2: Get Request Comments

### Feature 5.2: Get Comments with Visibility Info

**Script:** `get_request_comments.py`

**JIRA API:**
- `GET /rest/servicedeskapi/request/{key}/comment`

**Test File:** `tests/test_get_request_comments.py`

**Test Cases:**
```python
def test_get_all_comments():
    """Test fetching all comments (public and internal)."""
    # Should return both public and internal comments

def test_get_public_comments_only():
    """Test filtering to public comments only."""
    # --public-only flag

def test_get_internal_comments_only():
    """Test filtering to internal comments only."""
    # --internal-only flag

def test_get_comments_with_pagination():
    """Test handling paginated results."""
    # Should fetch all pages automatically

def test_get_comments_empty():
    """Test handling request with no comments."""
    # Should show helpful message

def test_get_comment_by_id():
    """Test fetching specific comment by ID."""
    # --id option

def test_format_text_output():
    """Test human-readable table output."""
    # Should show visibility clearly

def test_format_json_output():
    """Test JSON output format."""
    # Should include public field
```

**CLI Interface:**
```bash
# All comments
python get_request_comments.py REQ-123

# Public comments only
python get_request_comments.py REQ-123 --public-only

# Internal comments only
python get_request_comments.py REQ-123 --internal-only

# Specific comment
python get_request_comments.py REQ-123 --id 10001

# JSON output
python get_request_comments.py REQ-123 --output json
```

**Output Example:**
```
Comments on REQ-123 (5 total: 3 public, 2 internal):

ID       Author            Date                  Visibility   Body
───────  ────────────────  ────────────────────  ───────────  ──────────────────────────────
10005    Alice Smith       2025-01-17 02:30 PM   PUBLIC       Issue resolved. Please verify...
10004    Bob Jones         2025-01-17 01:45 PM   INTERNAL     Escalated to database team
10003    Alice Smith       2025-01-17 10:30 AM   PUBLIC       Working on this now...
10002    Carol Lee         2025-01-17 09:15 AM   INTERNAL     Need manager approval
10001    Alice Smith       2025-01-17 09:00 AM   PUBLIC       Thank you for reporting this...

Legend:
  PUBLIC    - Visible in customer portal
  INTERNAL  - Agent-only, not visible to customers
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Shows all comments with visibility
- [ ] Filter by public/internal
- [ ] Pagination support
- [ ] Clear visual distinction
- [ ] JSON output includes public field

**Commits:**
1. `test(jira-jsm): add failing tests for get_request_comments`
2. `feat(jira-jsm): implement get_request_comments.py (8/8 tests passing)`

---

## Phase 5.3: Get Pending Approvals

### Feature 5.3: Get Approval Requests

**Script:** `get_approvals.py`

**JIRA API:**
- `GET /rest/servicedeskapi/request/{key}/approval`
- `GET /rest/servicedeskapi/request/{key}/approval/{approvalId}`

**Test File:** `tests/test_get_approvals.py`

**Test Cases:**
```python
def test_get_all_approvals():
    """Test fetching all approvals for request."""
    # Should return list of approval objects

def test_get_approval_by_id():
    """Test fetching specific approval by ID."""
    # --id option

def test_get_approvals_filter_pending():
    """Test filtering to pending approvals only."""
    # --pending flag (default)

def test_get_approvals_all_statuses():
    """Test showing all approvals (pending, approved, declined)."""
    # --all flag

def test_get_approvals_empty():
    """Test handling request with no approvals."""
    # Should show helpful message

def test_format_text_output():
    """Test human-readable table output."""
    # Should show approval status and approvers
```

**CLI Interface:**
```bash
# Pending approvals (default)
python get_approvals.py REQ-123

# All approvals (including completed)
python get_approvals.py REQ-123 --all

# Specific approval
python get_approvals.py REQ-123 --id 10050

# JSON output
python get_approvals.py REQ-123 --output json
```

**Output Example:**
```
Approvals for REQ-123 (2 pending, 1 completed):

ID       Name              Status     Approvers           Created              Completed
───────  ────────────────  ─────────  ──────────────────  ───────────────────  ─────────────────
10052    Change Approval   PENDING    Manager Alice       2025-01-17 09:00 AM  -
10051    Security Review   PENDING    Security Team (3)   2025-01-17 09:00 AM  -
10050    Budget Approval   APPROVED   Finance Manager     2025-01-17 09:00 AM  2025-01-17 10:30 AM

To approve/decline:
  python approve_request.py REQ-123 --approval-id 10052
  python decline_request.py REQ-123 --approval-id 10052
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Shows all approval details
- [ ] Filter by status
- [ ] Clear status indication
- [ ] Shows approvers
- [ ] Helpful next-step hints

**Commits:**
1. `test(jira-jsm): add failing tests for get_approvals`
2. `feat(jira-jsm): implement get_approvals.py (6/6 tests passing)`

---

## Phase 5.4: Approve Request

### Feature 5.4: Approve Approval Request

**Script:** `approve_request.py`

**JIRA API:**
- `POST /rest/servicedeskapi/request/{key}/approval/{approvalId}` with `decision: "approve"`

**Test File:** `tests/test_approve_request.py`

**Test Cases:**
```python
def test_approve_request():
    """Test approving an approval request."""
    # Should POST with decision: approve

def test_approve_request_not_pending():
    """Test error when approval already completed."""
    # Should raise JiraError

def test_approve_request_not_approver():
    """Test error when user is not an approver."""
    # Should raise PermissionError

def test_approve_request_not_found():
    """Test error when approval doesn't exist."""
    # Should raise NotFoundError

def test_approve_request_with_confirmation():
    """Test confirmation prompt."""
    # Should confirm before approving

def test_approve_request_dry_run():
    """Test dry-run mode."""
    # Should show what would be approved

def test_approve_request_output():
    """Test output shows approval result."""
    # Should show approval status and timestamp

def test_approve_request_multiple():
    """Test approving multiple approvals at once."""
    # --approval-id can be specified multiple times
```

**CLI Interface:**
```bash
# Approve single approval
python approve_request.py REQ-123 --approval-id 10050

# Approve multiple approvals
python approve_request.py REQ-123 --approval-id 10050 --approval-id 10051

# Skip confirmation
python approve_request.py REQ-123 --approval-id 10050 --yes

# Dry run
python approve_request.py REQ-123 --approval-id 10050 --dry-run
```

**Output Example:**
```
Approve approval for REQ-123?

Approval ID:   10050
Name:          Change Approval
Approvers:     Manager Alice, Bob Jones
Created:       2025-01-17 09:00 AM

Type 'yes' to confirm: yes

Approval 10050 APPROVED for REQ-123.

Status: approve
Completed: 2025-01-17 02:30 PM
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Approves approval request
- [ ] Confirmation prompt
- [ ] Dry-run mode
- [ ] Validates user permissions
- [ ] Supports multiple approvals
- [ ] Clear success message

**Commits:**
1. `test(jira-jsm): add failing tests for approve_request`
2. `feat(jira-jsm): implement approve_request.py (8/8 tests passing)`

---

## Phase 5.5: Decline Request

### Feature 5.5: Decline Approval Request

**Script:** `decline_request.py`

**JIRA API:**
- `POST /rest/servicedeskapi/request/{key}/approval/{approvalId}` with `decision: "decline"`

**Test File:** `tests/test_decline_request.py`

**Test Cases:**
```python
def test_decline_request():
    """Test declining an approval request."""
    # Should POST with decision: decline

def test_decline_request_not_pending():
    """Test error when approval already completed."""
    # Should raise JiraError

def test_decline_request_not_approver():
    """Test error when user is not an approver."""
    # Should raise PermissionError

def test_decline_with_confirmation():
    """Test confirmation prompt."""
    # Should confirm before declining

def test_decline_dry_run():
    """Test dry-run mode."""
    # Should show what would be declined

def test_decline_request_output():
    """Test output shows decline result."""
    # Should show decline status and timestamp
```

**CLI Interface:**
```bash
# Decline single approval
python decline_request.py REQ-123 --approval-id 10050

# Decline multiple approvals
python decline_request.py REQ-123 --approval-id 10050 --approval-id 10051

# Skip confirmation
python decline_request.py REQ-123 --approval-id 10050 --yes

# Dry run
python decline_request.py REQ-123 --approval-id 10050 --dry-run
```

**Output Example:**
```
Decline approval for REQ-123?

Approval ID:   10050
Name:          Change Approval
Approvers:     Manager Alice, Bob Jones
Created:       2025-01-17 09:00 AM

Warning: Declining this approval may prevent the change from proceeding.

Type 'yes' to confirm: yes

Approval 10050 DECLINED for REQ-123.

Status: decline
Completed: 2025-01-17 02:30 PM
Reason: Change request declined by approver
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Declines approval request
- [ ] Confirmation prompt with warning
- [ ] Dry-run mode
- [ ] Validates user permissions
- [ ] Clear success message

**Commits:**
1. `test(jira-jsm): add failing tests for decline_request`
2. `feat(jira-jsm): implement decline_request.py (6/6 tests passing)`

---

## Phase 5.6: List All Pending Approvals

### Feature 5.6: List Pending Approvals Across Requests

**Script:** `list_pending_approvals.py`

**JIRA API:**
- `GET /rest/api/3/search` with JQL for requests with pending approvals
- `GET /rest/servicedeskapi/request/{key}/approval` for each request

**Test File:** `tests/test_list_pending_approvals.py`

**Test Cases:**
```python
def test_list_all_pending_approvals():
    """Test listing all pending approvals for current user."""
    # Should query for requests where user is approver

def test_list_approvals_by_project():
    """Test filtering by service desk project."""
    # --project option

def test_list_approvals_by_user():
    """Test listing approvals for specific user."""
    # --user option (requires admin permissions)

def test_list_approvals_empty():
    """Test handling no pending approvals."""
    # Should show helpful message

def test_format_text_output():
    """Test human-readable table output."""
    # Should show request, approval, and approvers

def test_format_json_output():
    """Test JSON output format."""
    # Should include all approval details
```

**CLI Interface:**
```bash
# All pending approvals for current user
python list_pending_approvals.py

# Filter by project
python list_pending_approvals.py --project SD

# For specific user (admin only)
python list_pending_approvals.py --user alice@company.com

# JSON output
python list_pending_approvals.py --output json
```

**Output Example:**
```
Pending Approvals for alice@company.com (5 total):

Request    Summary                     Approval ID   Approval Name      Created              Action
─────────  ──────────────────────────  ────────────  ─────────────────  ───────────────────  ──────────────────
SD-789     Database schema change      10055         Change Approval    2025-01-17 09:00 AM  Approve | Decline
SD-678     New server deployment       10054         Budget Approval    2025-01-17 08:30 AM  Approve | Decline
SD-567     API endpoint modification   10053         Security Review    2025-01-16 04:00 PM  Approve | Decline
SD-456     Network firewall rule       10052         Security Review    2025-01-16 02:30 PM  Approve | Decline
SD-345     Software license renewal    10051         Budget Approval    2025-01-15 10:00 AM  Approve | Decline

To approve/decline:
  python approve_request.py <REQUEST-KEY> --approval-id <APPROVAL-ID>
  python decline_request.py <REQUEST-KEY> --approval-id <APPROVAL-ID>
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Lists all pending approvals
- [ ] Filter by project and user
- [ ] Shows request context
- [ ] Clear action hints
- [ ] Efficient (batches API calls)

**Commits:**
1. `test(jira-jsm): add failing tests for list_pending_approvals`
2. `feat(jira-jsm): implement list_pending_approvals.py (6/6 tests passing)`

---

## Phase 5 Completion

- [ ] **Phase 5 Summary:**
  - [ ] 6 scripts (add_request_comment, get_request_comments, get_approvals, approve_request, decline_request, list_pending_approvals)
  - [ ] 44 tests passing (10 + 8 + 6 + 8 + 6 + 6)
  - [ ] JiraClient methods added (7 methods)
  - **Commit:** `docs(jira-jsm): complete Phase 5 - Comments & Approvals`

---

## Integration with jira-collaborate

### Integration Tasks

- [ ] **Integration 1:** Update jira-collaborate SKILL.md
  - [ ] Add note about JSM vs JIRA comment differences
  - [ ] Reference jira-jsm skill for JSM requests
  - [ ] Document when to use each API
  - **Commit:** `docs(jira-collaborate): document JSM comment differences`

- [ ] **Integration 2:** Enhance add_comment.py JSM detection
  - [ ] Detect if issue is JSM request (check `fields.project.projectTypeKey === "service_desk"`)
  - [ ] Suggest using `add_request_comment.py` for JSM requests
  - [ ] Keep existing functionality for standard JIRA
  - **Commit:** `feat(jira-collaborate): detect JSM requests and suggest jira-jsm skill`

- [ ] **Integration 3:** Create jira-jsm SKILL.md
  - [ ] "When to use this skill" section
  - [ ] "What this skill does" section
  - [ ] "Available scripts" with descriptions
  - [ ] "Examples" with realistic workflows
  - [ ] JSM vs JIRA API differences
  - [ ] Configuration notes
  - **Commit:** `docs(jira-jsm): create comprehensive SKILL.md`

### Documentation Updates

- [ ] **Docs 1:** Update CLAUDE.md
  - [ ] Add jira-jsm to project overview
  - [ ] Add JSM patterns section
  - [ ] Document service desk workflows
  - **Commit:** `docs: update CLAUDE.md with jira-jsm skill`

- [ ] **Docs 2:** Update GAP_ANALYSIS.md
  - [ ] Mark Category G (JSM Comments) as completed
  - [ ] Mark Category J (Approvals) as completed
  - [ ] Update JSM coverage metrics
  - [ ] Update recommendation priorities
  - **Commit:** `docs: update GAP_ANALYSIS.md - JSM Phase 5 complete`

### Live Integration Tests

- [ ] **Quality 1:** Add live integration tests
  - [ ] `test_jsm_comments.py`: Add/get public and internal comments
  - [ ] `test_jsm_approvals.py`: Get/approve/decline approvals
  - [ ] `test_jsm_workflows.py`: Full approval workflow scenarios
  - **Commit:** `test(shared): add live integration tests for JSM comments and approvals`

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 44+ unit tests passing
- [ ] Live integration tests for all features
- [ ] Coverage ≥ 85% for new code

**Scripts:**
- [ ] 6 new scripts implemented
- [ ] All scripts have `--help`
- [ ] All scripts support `--profile`
- [ ] Mutation scripts have `--dry-run` and `--yes`

**Documentation:**
- [ ] SKILL.md created with examples
- [ ] CLAUDE.md updated
- [ ] GAP_ANALYSIS.md updated
- [ ] All scripts have docstrings

**Integration:**
- [ ] jira-collaborate updated with JSM detection
- [ ] No breaking changes to existing scripts

### Progress Tracking

**Phase Status:**
- [ ] Phase 5.1: Add Request Comment (10 tests)
- [ ] Phase 5.2: Get Request Comments (8 tests)
- [ ] Phase 5.3: Get Pending Approvals (6 tests)
- [ ] Phase 5.4: Approve Request (8 tests)
- [ ] Phase 5.5: Decline Request (6 tests)
- [ ] Phase 5.6: List All Pending Approvals (6 tests)
- [ ] Integration & Documentation

---

## Script Summary

| Script | Phase | Tests | Description |
|--------|-------|-------|-------------|
| `add_request_comment.py` | 5.1 | 10 | Add JSM comment (public/internal) |
| `get_request_comments.py` | 5.2 | 8 | List comments with visibility |
| `get_approvals.py` | 5.3 | 6 | Get approval requests |
| `approve_request.py` | 5.4 | 8 | Approve approval request |
| `decline_request.py` | 5.5 | 6 | Decline approval request |
| `list_pending_approvals.py` | 5.6 | 6 | List all pending approvals |
| **Total** | - | **44** | - |

---

## JiraClient Methods to Add

```python
# In shared/scripts/lib/jira_client.py

# ========== JSM Comment Management ==========

def add_request_comment(self, issue_key: str, body: str, public: bool = True) -> Dict[str, Any]:
    """
    Add a comment to a JSM request with public/internal visibility.

    Args:
        issue_key: Request key (e.g., REQ-123)
        body: Comment body (plain text)
        public: True for customer-visible, False for internal (default: True)

    Returns:
        Created comment object

    Note:
        Uses JSM API (/rest/servicedeskapi/) which differs from standard JIRA API.
        Public comments are visible in the customer portal.
    """
    data = {
        'body': body,
        'public': public
    }
    return self.post(f'/rest/servicedeskapi/request/{issue_key}/comment',
                    data=data, operation=f"add JSM comment to {issue_key}")

def get_request_comments(self, issue_key: str, public: bool = None,
                         start: int = 0, limit: int = 100) -> Dict[str, Any]:
    """
    Get comments for a JSM request with visibility information.

    Args:
        issue_key: Request key (e.g., REQ-123)
        public: Filter by visibility (True=public, False=internal, None=all)
        start: Starting index for pagination
        limit: Maximum results per page (max 100)

    Returns:
        Comments response with values array and pagination info
    """
    params = {'start': start, 'limit': limit}
    if public is not None:
        params['public'] = str(public).lower()

    return self.get(f'/rest/servicedeskapi/request/{issue_key}/comment',
                   params=params,
                   operation=f"get JSM comments for {issue_key}")

def get_request_comment(self, issue_key: str, comment_id: str,
                        expand: str = None) -> Dict[str, Any]:
    """
    Get a specific JSM comment by ID.

    Args:
        issue_key: Request key (e.g., REQ-123)
        comment_id: Comment ID
        expand: Optional expansions (e.g., 'renderedBody')

    Returns:
        Comment object
    """
    params = {}
    if expand:
        params['expand'] = expand

    return self.get(f'/rest/servicedeskapi/request/{issue_key}/comment/{comment_id}',
                   params=params if params else None,
                   operation=f"get JSM comment {comment_id}")

# ========== JSM Approval Management ==========

def get_request_approvals(self, issue_key: str, start: int = 0,
                          limit: int = 100) -> Dict[str, Any]:
    """
    Get approvals for a JSM request.

    Args:
        issue_key: Request key (e.g., REQ-123)
        start: Starting index for pagination
        limit: Maximum results per page

    Returns:
        Approvals response with values array and pagination info
    """
    params = {'start': start, 'limit': limit}
    return self.get(f'/rest/servicedeskapi/request/{issue_key}/approval',
                   params=params,
                   operation=f"get approvals for {issue_key}")

def get_request_approval(self, issue_key: str, approval_id: str) -> Dict[str, Any]:
    """
    Get a specific approval by ID.

    Args:
        issue_key: Request key (e.g., REQ-123)
        approval_id: Approval ID

    Returns:
        Approval object
    """
    return self.get(f'/rest/servicedeskapi/request/{issue_key}/approval/{approval_id}',
                   operation=f"get approval {approval_id}")

def approve_request(self, issue_key: str, approval_id: str) -> Dict[str, Any]:
    """
    Approve an approval request.

    Args:
        issue_key: Request key (e.g., REQ-123)
        approval_id: Approval ID to approve

    Returns:
        Updated approval object with decision: approve
    """
    data = {'decision': 'approve'}
    return self.post(f'/rest/servicedeskapi/request/{issue_key}/approval/{approval_id}',
                    data=data,
                    operation=f"approve approval {approval_id} for {issue_key}")

def decline_request(self, issue_key: str, approval_id: str) -> Dict[str, Any]:
    """
    Decline an approval request.

    Args:
        issue_key: Request key (e.g., REQ-123)
        approval_id: Approval ID to decline

    Returns:
        Updated approval object with decision: decline
    """
    data = {'decision': 'decline'}
    return self.post(f'/rest/servicedeskapi/request/{issue_key}/approval/{approval_id}',
                    data=data,
                    operation=f"decline approval {approval_id} for {issue_key}")
```

---

## Helper Functions

### JSM Detection

```python
# In shared/scripts/lib/jsm_utils.py (new file)

def is_jsm_request(issue: Dict[str, Any]) -> bool:
    """
    Check if an issue is a JSM request.

    Args:
        issue: Issue object from JIRA API

    Returns:
        True if issue is a JSM request, False otherwise
    """
    project = issue.get('fields', {}).get('project', {})
    return project.get('projectTypeKey') == 'service_desk'

def get_service_desk_id(issue: Dict[str, Any]) -> Optional[int]:
    """
    Get service desk ID from issue.

    Args:
        issue: Issue object from JIRA API

    Returns:
        Service desk ID or None if not a JSM request
    """
    if not is_jsm_request(issue):
        return None

    # Service desk ID is typically in customfield_10001 (may vary)
    # Or can be retrieved from project configuration
    project = issue.get('fields', {}).get('project', {})
    return project.get('id')
```

---

## Known Limitations

### JSM Comment Visibility

- **Public/Internal Model:** JSM uses simple boolean flag, not role-based visibility
- **Portal vs Email:** Public comments appear in both portal and email notifications
- **Internal Visibility:** Internal comments are hidden from customer portal but visible to all agents
- **No Granular Control:** Cannot restrict internal comments to specific agent groups using JSM API

### Approval Workflows

- **Approval Configuration:** Approval steps configured in JSM project settings, not via API
- **Multi-Approver Logic:** "Any" vs "All" approval logic configured in project, not controllable per-approval
- **Delegation:** Approver delegation not supported via API
- **Approval History:** Historical approvals retained but cannot be modified after completion

### API Differences

| Feature | JIRA API | JSM API |
|---------|----------|---------|
| **Comment Visibility** | Role/group based | Public boolean |
| **API Base** | `/rest/api/3/` | `/rest/servicedeskapi/` |
| **Comment Body** | ADF format | Plain text |
| **Approvals** | No built-in support | Full approval workflow |

---

## Commit Strategy

### Commit Types

**test:** Adding or updating tests
- `test(jira-jsm): add failing tests for add_request_comment`

**feat:** Implementing features
- `feat(jira-jsm): implement add_request_comment.py (10/10 tests passing)`

**docs:** Documentation updates
- `docs(jira-jsm): add JSM comment examples to SKILL.md`

**fix:** Bug fixes
- `fix(jira-jsm): handle non-JSM requests gracefully`

---

## API Sources

- [JSM Cloud REST API - Request Comments](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-request/#api-rest-servicedeskapi-request-issueidorkey-comment-post)
- [JSM Cloud REST API - Approvals](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-request/#api-rest-servicedeskapi-request-issueidorkey-approval-get)
- [JSM Data Center REST API Reference](https://docs.atlassian.com/jira-servicedesk/REST/5.15.2/)
- [JSM API Changelog](https://developer.atlassian.com/cloud/jira/service-desk/changelog/)
- [Public vs Internal Comments in JSM](https://support.atlassian.com/jira-service-management-cloud/docs/add-comments-to-a-request/)

---

**Plan Version:** 1.0
**Created:** 2025-12-25
**Status:** READY FOR IMPLEMENTATION

### Estimated Scope

| Metric | Estimate |
|--------|----------|
| Unit Tests | 44 |
| Scripts | 6 |
| JiraClient Methods | 7 |
| Skills Affected | 2 (jira-jsm new, jira-collaborate enhanced) |
| Estimated Effort | ~18 hours (3 hours per script + integration/docs) |

---

## Workflow Examples

### Customer Support Workflow

```bash
# Agent receives new request
python get_issue.py REQ-123

# Add internal note about investigation
python add_request_comment.py REQ-123 --body "Investigating database connection issue" --internal

# Update customer with public comment
python add_request_comment.py REQ-123 --body "We are working on your issue and will update you within 2 hours."

# View all comments (public and internal)
python get_request_comments.py REQ-123

# View only internal notes
python get_request_comments.py REQ-123 --internal-only
```

### Change Management Workflow

```bash
# List pending approvals for current user
python list_pending_approvals.py

# Get details of specific request's approvals
python get_approvals.py CHG-456

# Approve change request
python approve_request.py CHG-456 --approval-id 10050

# Add public comment after approval
python add_request_comment.py CHG-456 --body "Change approved. Implementation scheduled for next maintenance window."

# Decline another change
python decline_request.py CHG-789 --approval-id 10051
```

### Bulk Approval Processing

```bash
# Get all pending approvals
python list_pending_approvals.py --output json > pending_approvals.json

# Approve multiple approvals in one request
python approve_request.py CHG-100 --approval-id 10055 --approval-id 10056 --approval-id 10057 --yes

# Review change history
python get_request_comments.py CHG-100 --internal-only
```

---

## Next Steps After Phase 5

**Phase 6: Service Desk & Request Types** (from JSM Gap Analysis Categories A, B, C)
- `list_service_desks.py` - List all JSM projects
- `get_service_desk.py` - Get service desk details
- `list_request_types.py` - List available request types
- `get_request_type_fields.py` - Get fields for request type
- `create_request.py` - Create request via JSM API (vs generic issue API)

**Phase 7: SLA Management** (from JSM Gap Analysis Category H)
- `get_sla.py` - Get SLA metrics for request
- `check_sla_breach.py` - Check if SLA breached
- `sla_report.py` - Generate SLA compliance report

**Phase 8: Customer & Organization Management** (from JSM Gap Analysis Categories D, E, F)
- Customer CRUD operations
- Organization management
- Request participant management
