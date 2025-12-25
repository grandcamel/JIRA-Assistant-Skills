# JSM Phase 4: SLA & Queue Management - TDD Implementation Plan

## Overview

**Objective:** Implement SLA tracking, breach detection, compliance reporting, and queue management for Jira Service Management using Test-Driven Development (TDD)

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
1. **Phase 4.1: Get Request SLA** (Fetch all SLAs for a request)
2. **Phase 4.2: Check SLA Breach Status** (Detect breached/at-risk SLAs)
3. **Phase 4.3: SLA Compliance Report** (Generate reports with CSV/JSON export)
4. **Phase 4.4: List Queues** (List all queues for service desk)
5. **Phase 4.5: Get Queue Issues** (Retrieve issues in queue with pagination)

---

## JIRA API Reference

### SLA Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rest/servicedeskapi/request/{issueIdOrKey}/sla` | Get all SLAs for request |
| GET | `/rest/servicedeskapi/request/{issueIdOrKey}/sla/{slaMetricId}` | Get specific SLA metric |

### SLA Response Structure

```json
{
  "size": 2,
  "start": 0,
  "limit": 50,
  "isLastPage": true,
  "_links": {...},
  "values": [
    {
      "id": "1",
      "name": "Time to First Response",
      "_links": {...},
      "completedCycles": [],
      "ongoingCycle": {
        "startTime": {
          "iso8601": "2025-01-15T10:00:00Z",
          "jira": "2025-01-15T10:00:00.000+0000",
          "friendly": "15/Jan/25 10:00 AM",
          "epochMillis": 1705315200000
        },
        "breachTime": {
          "iso8601": "2025-01-15T14:00:00Z",
          "jira": "2025-01-15T14:00:00.000+0000",
          "friendly": "15/Jan/25 2:00 PM",
          "epochMillis": 1705329600000
        },
        "breached": false,
        "paused": false,
        "withinCalendarHours": true,
        "goalDuration": {
          "millis": 14400000,
          "friendly": "4h"
        },
        "elapsedTime": {
          "millis": 7200000,
          "friendly": "2h"
        },
        "remainingTime": {
          "millis": 7200000,
          "friendly": "2h"
        }
      }
    },
    {
      "id": "2",
      "name": "Time to Resolution",
      "_links": {...},
      "completedCycles": [],
      "ongoingCycle": {
        "startTime": {
          "iso8601": "2025-01-15T10:00:00Z",
          "jira": "2025-01-15T10:00:00.000+0000",
          "friendly": "15/Jan/25 10:00 AM",
          "epochMillis": 1705315200000
        },
        "breachTime": {
          "iso8601": "2025-01-17T10:00:00Z",
          "jira": "2025-01-17T10:00:00.000+0000",
          "friendly": "17/Jan/25 10:00 AM",
          "epochMillis": 1705488000000
        },
        "breached": false,
        "paused": false,
        "withinCalendarHours": true,
        "goalDuration": {
          "millis": 172800000,
          "friendly": "2d"
        },
        "elapsedTime": {
          "millis": 7200000,
          "friendly": "2h"
        },
        "remainingTime": {
          "millis": 165600000,
          "friendly": "1d 22h"
        }
      }
    }
  ]
}
```

### Completed SLA Cycle

```json
{
  "startTime": {
    "iso8601": "2025-01-15T10:00:00Z",
    "jira": "2025-01-15T10:00:00.000+0000",
    "friendly": "15/Jan/25 10:00 AM",
    "epochMillis": 1705315200000
  },
  "stopTime": {
    "iso8601": "2025-01-15T11:30:00Z",
    "jira": "2025-01-15T11:30:00.000+0000",
    "friendly": "15/Jan/25 11:30 AM",
    "epochMillis": 1705320600000
  },
  "breached": false,
  "goalDuration": {
    "millis": 14400000,
    "friendly": "4h"
  },
  "elapsedTime": {
    "millis": 5400000,
    "friendly": "1h 30m"
  },
  "remainingTime": {
    "millis": 9000000,
    "friendly": "2h 30m"
  }
}
```

### Queue Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rest/servicedeskapi/servicedesk/{serviceDeskId}/queue` | List all queues |
| GET | `/rest/servicedeskapi/servicedesk/{serviceDeskId}/queue/{queueId}` | Get queue details |
| GET | `/rest/servicedeskapi/servicedesk/{serviceDeskId}/queue/{queueId}/issue` | Get issues in queue |

### Queue List Response

```json
{
  "size": 3,
  "start": 0,
  "limit": 50,
  "isLastPage": true,
  "_links": {...},
  "values": [
    {
      "id": "1",
      "name": "Open Requests",
      "jql": "project = SD AND status = Open",
      "fields": ["issuekey", "summary", "status", "priority"],
      "_links": {...}
    },
    {
      "id": "2",
      "name": "Waiting for Customer",
      "jql": "project = SD AND status = 'Waiting for customer'",
      "fields": ["issuekey", "summary", "status", "priority", "reporter"],
      "_links": {...}
    },
    {
      "id": "3",
      "name": "Breached SLAs",
      "jql": "project = SD AND 'SLA Status' = Breached",
      "fields": ["issuekey", "summary", "status", "priority", "sla"],
      "_links": {...}
    }
  ]
}
```

### Queue Issues Response

```json
{
  "size": 25,
  "start": 0,
  "limit": 50,
  "isLastPage": false,
  "_links": {...},
  "values": [
    {
      "issueId": "10001",
      "issueKey": "SD-123",
      "fields": {
        "summary": "Login not working",
        "status": {
          "name": "Open"
        },
        "priority": {
          "name": "High"
        },
        "reporter": {
          "displayName": "John Customer",
          "emailAddress": "john@customer.com"
        }
      }
    }
  ]
}
```

---

## Test Infrastructure Setup

### Initial Setup Tasks

- [ ] **Setup 1.1:** Create SLA test fixtures
  - [ ] Create `.claude/skills/jira-jsm/tests/conftest.py` (enhance existing)
  - [ ] Add sample SLA response fixtures (ongoing/completed cycles)
  - [ ] Add breached SLA fixtures
  - [ ] Add paused SLA fixtures
  - **Commit:** `test(jira-jsm): add SLA test fixtures for Phase 4`

- [ ] **Setup 1.2:** Create queue test fixtures
  - [ ] Add sample queue list fixtures
  - [ ] Add queue details fixtures
  - [ ] Add queue issues fixtures (with pagination)
  - **Commit:** `test(jira-jsm): add queue test fixtures for Phase 4`

- [ ] **Setup 1.3:** Add JiraClient JSM methods for SLAs and Queues
  - [ ] `get_request_slas(issue_key)` - Get all SLAs for request
  - [ ] `get_request_sla(issue_key, sla_metric_id)` - Get specific SLA metric
  - [ ] `get_service_desk_queues(service_desk_id)` - List queues
  - [ ] `get_queue(service_desk_id, queue_id)` - Get queue details
  - [ ] `get_queue_issues(service_desk_id, queue_id, start, limit)` - Get issues in queue
  - **Commit:** `feat(shared): add JSM SLA and queue API methods`

---

## Phase 4.1: Get Request SLA

### Feature 4.1: Get Request SLA

**Script:** `get_sla.py`

**JIRA API:**
- `GET /rest/servicedeskapi/request/{issueIdOrKey}/sla`
- `GET /rest/servicedeskapi/request/{issueIdOrKey}/sla/{slaMetricId}`

**Test File:** `tests/test_get_sla.py`

**Test Cases:**
```python
def test_get_all_slas():
    """Test fetching all SLAs for a request."""
    # Should return list of SLA metrics

def test_get_specific_sla():
    """Test fetching specific SLA metric by ID."""
    # Should return single SLA metric details

def test_get_sla_ongoing_cycle():
    """Test SLA with ongoing cycle (not yet completed)."""
    # Should show elapsed, remaining, breach time

def test_get_sla_completed_cycles():
    """Test SLA with completed cycles."""
    # Should show historical performance

def test_get_sla_paused():
    """Test SLA in paused state."""
    # Should indicate paused=true

def test_get_sla_breached():
    """Test SLA that has breached."""
    # Should indicate breached=true

def test_format_text_output():
    """Test human-readable SLA status output."""
    # Should show friendly time formats

def test_format_json_output():
    """Test JSON output format."""
    # Should return complete SLA data
```

**CLI Interface:**
```bash
# Get all SLAs for request
python get_sla.py SD-123

# Get specific SLA metric
python get_sla.py SD-123 --sla-id 1

# JSON output
python get_sla.py SD-123 --output json
```

**Output Example:**
```
SLAs for SD-123:

┌─────────────────────────────┬──────────┬─────────────────────────────────┐
│ SLA Name                    │ Status   │ Details                         │
├─────────────────────────────┼──────────┼─────────────────────────────────┤
│ Time to First Response      │ ✓ Met    │ Completed in 1h 30m             │
│                             │          │ Goal: 4h, Remaining: 2h 30m     │
├─────────────────────────────┼──────────┼─────────────────────────────────┤
│ Time to Resolution          │ ⚠ Active │ Elapsed: 2h, Remaining: 1d 22h  │
│                             │          │ Breach at: 17/Jan/25 10:00 AM   │
│                             │          │ Goal: 2d                        │
└─────────────────────────────┴──────────┴─────────────────────────────────┘

All SLAs are within target.
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Shows all SLA metrics
- [ ] Displays ongoing and completed cycles
- [ ] Shows friendly time formats
- [ ] Indicates breach status clearly
- [ ] Text and JSON output

**Commits:**
1. `test(jira-jsm): add failing tests for get_sla`
2. `feat(jira-jsm): implement get_sla.py (8/8 tests passing)`

---

## Phase 4.2: Check SLA Breach Status

### Feature 4.2: Check SLA Breach

**Script:** `check_sla_breach.py`

**JIRA API:**
- `GET /rest/servicedeskapi/request/{issueIdOrKey}/sla`

**Test File:** `tests/test_check_sla_breach.py`

**Test Cases:**
```python
def test_check_no_breach():
    """Test request with all SLAs within target."""
    # Should report all clear

def test_check_breached_sla():
    """Test request with breached SLA."""
    # Should report breach with details

def test_check_at_risk():
    """Test SLA approaching breach (< 20% remaining)."""
    # Should warn about at-risk SLAs

def test_check_paused_sla():
    """Test handling of paused SLAs."""
    # Should indicate paused status

def test_check_multiple_breaches():
    """Test request with multiple breached SLAs."""
    # Should list all breaches

def test_exit_code_on_breach():
    """Test non-zero exit code when breach detected."""
    # Exit 1 if any SLA breached

def test_warning_threshold_configurable():
    """Test configurable at-risk threshold."""
    # --threshold flag (default 20%)

def test_filter_by_sla_name():
    """Test checking specific SLA only."""
    # --sla-name flag
```

**CLI Interface:**
```bash
# Check SLA status
python check_sla_breach.py SD-123

# Custom at-risk threshold (30%)
python check_sla_breach.py SD-123 --threshold 30

# Check specific SLA
python check_sla_breach.py SD-123 --sla-name "Time to First Response"

# Quiet mode (exit code only)
python check_sla_breach.py SD-123 --quiet

# JSON output for monitoring
python check_sla_breach.py SD-123 --output json
```

**Output Example:**
```
SLA Status for SD-123:

✓ Time to First Response: Met (completed 1h 30m ago)

⚠ Time to Resolution: At Risk
  Elapsed:    2h
  Remaining:  1h 15m (15% of goal)
  Breach at:  15/Jan/25 3:15 PM
  Warning:    Less than 20% time remaining

Overall Status: AT RISK

Exit code: 0 (use --fail-on-risk for non-zero exit)
```

**Breach Example:**
```
SLA Status for SD-456:

✗ Time to First Response: BREACHED
  Goal:       4h
  Elapsed:    6h 30m
  Breached:   2h 30m ago (15/Jan/25 2:00 PM)

✗ Time to Resolution: BREACHED
  Goal:       2d
  Elapsed:    2d 8h
  Breached:   8h ago (17/Jan/25 10:00 AM)

Overall Status: BREACHED (2 SLAs)

Exit code: 1
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Detects breached SLAs
- [ ] Warns about at-risk SLAs
- [ ] Configurable threshold
- [ ] Exit code for monitoring
- [ ] Filter by SLA name

**Commits:**
1. `test(jira-jsm): add failing tests for check_sla_breach`
2. `feat(jira-jsm): implement check_sla_breach.py (8/8 tests passing)`

---

## Phase 4.3: SLA Compliance Report

### Feature 4.3: SLA Report

**Script:** `sla_report.py`

**JIRA API:**
- `GET /rest/servicedeskapi/request/{issueIdOrKey}/sla` (bulk via jira-search integration)
- `POST /rest/api/3/search` (JQL to find requests)

**Test File:** `tests/test_sla_report.py`

**Test Cases:**
```python
def test_report_by_project():
    """Test SLA report for all requests in project."""
    # Should aggregate SLA metrics

def test_report_by_jql():
    """Test SLA report for JQL results."""
    # Custom query support

def test_report_by_service_desk():
    """Test SLA report for service desk."""
    # Filter to service desk

def test_report_breach_summary():
    """Test breach summary statistics."""
    # Count/percentage of breached SLAs

def test_report_by_sla_name():
    """Test filtering to specific SLA metric."""
    # e.g., only "Time to First Response"

def test_report_csv_export():
    """Test CSV export for spreadsheet import."""
    # Headers, proper quoting

def test_report_json_export():
    """Test JSON export for programmatic use."""
    # Complete data structure

def test_report_time_period():
    """Test filtering by time period."""
    # --since and --until flags

def test_report_pagination():
    """Test handling large result sets."""
    # Process issues in batches

def test_report_progress_indicator():
    """Test progress display for long reports."""
    # Show progress bar
```

**CLI Interface:**
```bash
# Report for all requests in project
python sla_report.py --project SD

# Report for service desk
python sla_report.py --service-desk 1

# Report by JQL
python sla_report.py --jql "project = SD AND created >= -7d"

# Report by time period
python sla_report.py --project SD --since 2025-01-01 --until 2025-01-31

# Report for specific SLA
python sla_report.py --project SD --sla-name "Time to First Response"

# CSV export
python sla_report.py --project SD --output csv > sla_report.csv

# JSON export
python sla_report.py --project SD --output json > sla_report.json

# Show only breached SLAs
python sla_report.py --project SD --breached-only
```

**Output Example (Text):**
```
SLA Compliance Report: Project SD
Period: 2025-01-01 to 2025-01-31
Generated: 2025-01-25 10:30 AM

Summary:
  Total Requests:           250
  Requests with SLAs:       250
  Total SLA Metrics:        500 (2 per request)

SLA: Time to First Response
  Met:                      230 (92%)
  Breached:                 20 (8%)
  Average Response Time:    2h 15m
  Goal:                     4h

SLA: Time to Resolution
  Met:                      210 (84%)
  Breached:                 40 (16%)
  Average Resolution Time:  1d 8h
  Goal:                     2d

Top 10 Breached Requests:
┌──────────┬────────────────────────────┬──────────────┬─────────────┐
│ Key      │ Summary                    │ SLA Breached │ Breach Time │
├──────────┼────────────────────────────┼──────────────┼─────────────┤
│ SD-456   │ Critical outage            │ Resolution   │ 12h         │
│ SD-789   │ Database performance       │ Resolution   │ 8h          │
│ SD-234   │ Login issues               │ First Reply  │ 6h          │
└──────────┴────────────────────────────┴──────────────┴─────────────┘

Export to CSV: python sla_report.py --project SD --output csv
```

**CSV Export Example:**
```csv
Request Key,Summary,Reporter,Created,Status,SLA Name,SLA Goal,Elapsed Time,Remaining Time,Breached,Breach Time
SD-123,Login not working,john@customer.com,2025-01-15T10:00:00Z,Open,Time to First Response,4h,1h 30m,2h 30m,false,
SD-123,Login not working,john@customer.com,2025-01-15T10:00:00Z,Open,Time to Resolution,2d,2h,1d 22h,false,
SD-456,Critical outage,jane@customer.com,2025-01-14T08:00:00Z,In Progress,Time to First Response,4h,30m,3h 30m,false,
SD-456,Critical outage,jane@customer.com,2025-01-14T08:00:00Z,In Progress,Time to Resolution,2d,2d 12h,-12h,true,2025-01-16T08:00:00Z
```

**Acceptance Criteria:**
- [ ] All 10 tests pass
- [ ] Aggregates SLA metrics across requests
- [ ] Calculates breach statistics
- [ ] Filters by project, service desk, JQL, time period
- [ ] CSV export with all fields
- [ ] JSON export for automation
- [ ] Progress indicator for large reports
- [ ] Top breached requests list

**Commits:**
1. `test(jira-jsm): add failing tests for sla_report`
2. `feat(jira-jsm): implement sla_report.py (10/10 tests passing)`

---

## Phase 4.4: List Queues

### Feature 4.4: List Queues

**Script:** `list_queues.py`

**JIRA API:**
- `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/queue`
- `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/queue/{queueId}`

**Test File:** `tests/test_list_queues.py`

**Test Cases:**
```python
def test_list_all_queues():
    """Test listing all queues for service desk."""
    # Should return queue names and IDs

def test_list_queues_with_jql():
    """Test showing queue JQL queries."""
    # Should display JQL for each queue

def test_get_queue_details():
    """Test getting specific queue by ID."""
    # Should show name, JQL, fields

def test_empty_queues():
    """Test service desk with no queues."""
    # Should handle gracefully

def test_format_text_output():
    """Test human-readable table output."""
    # Queue name, JQL preview

def test_format_json_output():
    """Test JSON output format."""
    # Complete queue data
```

**CLI Interface:**
```bash
# List all queues
python list_queues.py --service-desk 1

# Get specific queue
python list_queues.py --service-desk 1 --queue-id 5

# Show JQL queries
python list_queues.py --service-desk 1 --show-jql

# JSON output
python list_queues.py --service-desk 1 --output json
```

**Output Example:**
```
Queues for Service Desk: IT Support (ID: 1)

┌────┬────────────────────────────┬─────────────────────────────────────────┐
│ ID │ Queue Name                 │ JQL Query                               │
├────┼────────────────────────────┼─────────────────────────────────────────┤
│ 1  │ Open Requests              │ project = SD AND status = Open          │
│ 2  │ Waiting for Customer       │ project = SD AND status = 'Waiting ...' │
│ 3  │ Breached SLAs              │ project = SD AND 'SLA Status' = Brea... │
│ 4  │ My Active Requests         │ project = SD AND assignee = current...  │
│ 5  │ High Priority              │ project = SD AND priority = High        │
└────┴────────────────────────────┴─────────────────────────────────────────┘

Total: 5 queues

View issues in queue: python get_queue_issues.py --service-desk 1 --queue-id 1
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Lists all queues
- [ ] Shows queue JQL
- [ ] Gets single queue details
- [ ] Text and JSON output

**Commits:**
1. `test(jira-jsm): add failing tests for list_queues`
2. `feat(jira-jsm): implement list_queues.py (6/6 tests passing)`

---

## Phase 4.5: Get Queue Issues

### Feature 4.5: Get Queue Issues

**Script:** `get_queue_issues.py`

**JIRA API:**
- `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/queue/{queueId}/issue`

**Test File:** `tests/test_get_queue_issues.py`

**Test Cases:**
```python
def test_get_queue_issues():
    """Test fetching issues in queue."""
    # Should return issue list

def test_get_queue_issues_pagination():
    """Test paginated results."""
    # Handle start/limit parameters

def test_get_queue_issues_empty():
    """Test queue with no issues."""
    # Should handle gracefully

def test_get_queue_issues_with_fields():
    """Test showing custom fields."""
    # Display queue-configured fields

def test_format_text_output():
    """Test human-readable table output."""
    # Show key, summary, status, priority

def test_format_json_output():
    """Test JSON output format."""
    # Complete issue data

def test_limit_results():
    """Test limiting number of results."""
    # --limit flag

def test_all_pages():
    """Test fetching all pages automatically."""
    # --all flag
```

**CLI Interface:**
```bash
# Get issues in queue (first 50)
python get_queue_issues.py --service-desk 1 --queue-id 1

# Limit results
python get_queue_issues.py --service-desk 1 --queue-id 1 --limit 10

# Get all issues (all pages)
python get_queue_issues.py --service-desk 1 --queue-id 1 --all

# Pagination
python get_queue_issues.py --service-desk 1 --queue-id 1 --start 50 --limit 50

# JSON output
python get_queue_issues.py --service-desk 1 --queue-id 1 --output json
```

**Output Example:**
```
Queue: Open Requests (ID: 1)
Service Desk: IT Support (ID: 1)

Issues (showing 10 of 45):

┌──────────┬────────────────────────────┬──────────────┬──────────┐
│ Key      │ Summary                    │ Status       │ Priority │
├──────────┼────────────────────────────┼──────────────┼──────────┤
│ SD-123   │ Login not working          │ Open         │ High     │
│ SD-124   │ Email sync issue           │ Open         │ Medium   │
│ SD-125   │ VPN connection failed      │ Open         │ High     │
│ SD-126   │ Printer not responding     │ Open         │ Low      │
│ SD-127   │ Password reset             │ Open         │ Medium   │
│ SD-128   │ Software installation      │ Open         │ Low      │
│ SD-129   │ Network slow               │ Open         │ High     │
│ SD-130   │ File access denied         │ Open         │ Medium   │
│ SD-131   │ Screen flickering          │ Open         │ Low      │
│ SD-132   │ Keyboard malfunction       │ Open         │ Medium   │
└──────────┴────────────────────────────┴──────────────┴──────────┘

Showing 10 of 45 total issues.
Use --all to fetch all pages, or --limit to show more/less.
Next page: python get_queue_issues.py --service-desk 1 --queue-id 1 --start 10
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Shows issues in queue
- [ ] Pagination support
- [ ] Fetch all pages option
- [ ] Configurable limit
- [ ] Text and JSON output

**Commits:**
1. `test(jira-jsm): add failing tests for get_queue_issues`
2. `feat(jira-jsm): implement get_queue_issues.py (8/8 tests passing)`

---

## Integration with jira-search

### Integration Tasks

- [ ] **Integration 1:** Add SLA fields to jira-search output
  - [ ] Update `jql_search.py` to support `--show-sla` flag
  - [ ] Display SLA breach status in search results
  - [ ] Add SLA columns to table output
  - **Commit:** `feat(jira-search): add JSM SLA field support`

- [ ] **Integration 2:** Queue-aware search
  - [ ] Add `--queue` parameter to search within queue
  - [ ] Use queue JQL automatically
  - **Commit:** `feat(jira-search): add queue-based search support`

---

## Documentation Updates

- [ ] **Docs 1:** Create jira-jsm SKILL.md section for Phase 4
  - [ ] SLA management section
  - [ ] Queue management section
  - [ ] Example workflows
  - [ ] Monitoring integration examples
  - **Commit:** `docs(jira-jsm): add SLA and queue documentation`

- [ ] **Docs 2:** Update CLAUDE.md
  - [ ] Add JSM Phase 4 to project overview
  - [ ] Add SLA monitoring patterns
  - **Commit:** `docs: update CLAUDE.md with JSM Phase 4 features`

- [ ] **Docs 3:** Update GAP_ANALYSIS.md
  - [ ] Mark Phase 4 (Categories H & I) as completed
  - [ ] Update JSM coverage metrics
  - **Commit:** `docs: update GAP_ANALYSIS.md - JSM Phase 4 complete`

---

## Testing & Quality

- [ ] **Quality 1:** Live integration tests
  - [ ] `test_jsm_sla.py`: SLA retrieval, breach detection, reporting (8 tests)
  - [ ] `test_jsm_queues.py`: Queue listing, issue retrieval (6 tests)
  - [ ] Run against real JSM instance
  - **Commit:** `test(shared): add live integration tests for JSM SLA and queues`

- [ ] **Quality 2:** Coverage validation
  - [ ] Run `pytest --cov=.claude/skills/jira-jsm --cov-report=html`
  - [ ] Ensure coverage ≥ 85%
  - **Commit:** (if fixes needed) `test(jira-jsm): improve test coverage for Phase 4`

- [ ] **Quality 3:** Error handling review
  - [ ] Test JSM API errors (service desk not found, SLA disabled, etc.)
  - [ ] Test invalid queue IDs
  - [ ] Helpful error messages
  - **Commit:** (if improvements needed) `fix(jira-jsm): improve error handling for Phase 4`

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 40+ unit tests passing (8 + 8 + 10 + 6 + 8)
- [ ] 14+ live integration tests passing
- [ ] Coverage ≥ 85% for Phase 4 code

**Scripts:**
- [ ] 5 new scripts implemented
- [ ] All scripts have `--help`
- [ ] All scripts support `--profile`
- [ ] Reports support `--output csv/json`

**Documentation:**
- [ ] SKILL.md updated with Phase 4
- [ ] CLAUDE.md updated
- [ ] GAP_ANALYSIS.md updated
- [ ] All scripts have docstrings

**Integration:**
- [ ] 1 existing skill updated (jira-search)
- [ ] No breaking changes

### Progress Tracking

**Phase Status:**
- [ ] Phase 4.1: Get Request SLA (1 script, 8 tests)
- [ ] Phase 4.2: Check SLA Breach (1 script, 8 tests)
- [ ] Phase 4.3: SLA Compliance Report (1 script, 10 tests)
- [ ] Phase 4.4: List Queues (1 script, 6 tests)
- [ ] Phase 4.5: Get Queue Issues (1 script, 8 tests)
- [ ] Integration (1 update)
- [ ] Documentation (3 docs)
- [ ] Quality (3 checks, 14 live tests)

---

## Script Summary

| Script | Phase | Tests | Description |
|--------|-------|-------|-------------|
| `get_sla.py` | 4.1 | 8 | Get all SLAs for request |
| `check_sla_breach.py` | 4.2 | 8 | Check SLA breach status |
| `sla_report.py` | 4.3 | 10 | Generate SLA compliance report |
| `list_queues.py` | 4.4 | 6 | List service desk queues |
| `get_queue_issues.py` | 4.5 | 8 | Get issues in queue |
| **Total** | - | **40** | - |

---

## JiraClient Methods to Add

```python
# In shared/scripts/lib/jira_client.py

# ========== SLA Management ==========

def get_request_slas(self, issue_key: str, start: int = 0,
                     limit: int = 50) -> Dict[str, Any]:
    """
    Get all SLAs for a service request.

    Args:
        issue_key: Issue key (e.g., 'SD-123')
        start: Starting index for pagination
        limit: Maximum results per page

    Returns:
        SLA data with values array of SLA metrics
    """
    params = {'start': start, 'limit': limit}
    return self.get(f'/rest/servicedeskapi/request/{issue_key}/sla',
                   params=params,
                   operation=f"get SLAs for {issue_key}")

def get_request_sla(self, issue_key: str, sla_metric_id: str) -> Dict[str, Any]:
    """
    Get a specific SLA metric for a request.

    Args:
        issue_key: Issue key (e.g., 'SD-123')
        sla_metric_id: SLA metric ID

    Returns:
        SLA metric details
    """
    return self.get(f'/rest/servicedeskapi/request/{issue_key}/sla/{sla_metric_id}',
                   operation=f"get SLA {sla_metric_id} for {issue_key}")

# ========== Queue Management ==========

def get_service_desk_queues(self, service_desk_id: int,
                            include_count: bool = False,
                            start: int = 0,
                            limit: int = 50) -> Dict[str, Any]:
    """
    Get all queues for a service desk.

    Args:
        service_desk_id: Service desk ID
        include_count: Include issue counts for each queue
        start: Starting index for pagination
        limit: Maximum results per page

    Returns:
        Queue data with values array of queues
    """
    params = {
        'start': start,
        'limit': limit,
        'includeCount': str(include_count).lower()
    }
    return self.get(f'/rest/servicedeskapi/servicedesk/{service_desk_id}/queue',
                   params=params,
                   operation=f"get queues for service desk {service_desk_id}")

def get_queue(self, service_desk_id: int, queue_id: int,
              include_count: bool = False) -> Dict[str, Any]:
    """
    Get a specific queue by ID.

    Args:
        service_desk_id: Service desk ID
        queue_id: Queue ID
        include_count: Include issue count

    Returns:
        Queue details
    """
    params = {'includeCount': str(include_count).lower()}
    return self.get(f'/rest/servicedeskapi/servicedesk/{service_desk_id}/queue/{queue_id}',
                   params=params,
                   operation=f"get queue {queue_id}")

def get_queue_issues(self, service_desk_id: int, queue_id: int,
                     start: int = 0, limit: int = 50) -> Dict[str, Any]:
    """
    Get issues in a queue.

    Args:
        service_desk_id: Service desk ID
        queue_id: Queue ID
        start: Starting index for pagination
        limit: Maximum results per page

    Returns:
        Issue data with values array of issues
    """
    params = {'start': start, 'limit': limit}
    return self.get(f'/rest/servicedeskapi/servicedesk/{service_desk_id}/queue/{queue_id}/issue',
                   params=params,
                   operation=f"get issues in queue {queue_id}")
```

---

## Helper Functions

### SLA Time Formatting

```python
# In shared/scripts/lib/jsm_utils.py (new file)

from datetime import datetime, timedelta
from typing import Dict, Any, Optional

def format_sla_time(time_dict: Dict[str, Any]) -> str:
    """
    Format SLA time from API response.

    Args:
        time_dict: Time object with iso8601, jira, friendly, epochMillis

    Returns:
        Human-readable time string

    Examples:
        >>> format_sla_time({"friendly": "15/Jan/25 10:00 AM"})
        '15/Jan/25 10:00 AM'
    """
    if not time_dict:
        return "N/A"
    return time_dict.get('friendly', time_dict.get('iso8601', 'Unknown'))

def format_duration(duration_dict: Dict[str, Any]) -> str:
    """
    Format SLA duration from API response.

    Args:
        duration_dict: Duration with millis and friendly fields

    Returns:
        Human-readable duration string

    Examples:
        >>> format_duration({"friendly": "2h 30m"})
        '2h 30m'
    """
    if not duration_dict:
        return "N/A"
    return duration_dict.get('friendly', f"{duration_dict.get('millis', 0) // 1000}s")

def calculate_sla_percentage(elapsed_millis: int, goal_millis: int) -> float:
    """
    Calculate SLA completion percentage.

    Args:
        elapsed_millis: Elapsed time in milliseconds
        goal_millis: Goal duration in milliseconds

    Returns:
        Percentage (0-100+)

    Examples:
        >>> calculate_sla_percentage(7200000, 14400000)  # 2h of 4h
        50.0
    """
    if goal_millis == 0:
        return 0.0
    return (elapsed_millis / goal_millis) * 100

def is_sla_at_risk(remaining_millis: int, goal_millis: int,
                   threshold: float = 20.0) -> bool:
    """
    Check if SLA is at risk of breach.

    Args:
        remaining_millis: Remaining time in milliseconds
        goal_millis: Goal duration in milliseconds
        threshold: Warning threshold percentage (default 20%)

    Returns:
        True if remaining time is less than threshold% of goal

    Examples:
        >>> is_sla_at_risk(3600000, 14400000)  # 1h remaining of 4h goal
        True  # 25% remaining > 20% threshold = False
        >>> is_sla_at_risk(1800000, 14400000)  # 30m remaining of 4h goal
        True  # 12.5% remaining < 20% threshold = True
    """
    if goal_millis == 0:
        return False
    remaining_percentage = (remaining_millis / goal_millis) * 100
    return remaining_percentage < threshold

def get_sla_status_emoji(sla: Dict[str, Any]) -> str:
    """
    Get emoji for SLA status.

    Args:
        sla: SLA metric object

    Returns:
        Status emoji

    Examples:
        >>> get_sla_status_emoji({"ongoingCycle": {"breached": False}})
        '✓'
        >>> get_sla_status_emoji({"ongoingCycle": {"breached": True}})
        '✗'
    """
    ongoing = sla.get('ongoingCycle')
    completed = sla.get('completedCycles', [])

    if ongoing:
        if ongoing.get('breached'):
            return '✗'
        if ongoing.get('paused'):
            return '⏸'
        # Check if at risk
        remaining = ongoing.get('remainingTime', {}).get('millis', 0)
        goal = ongoing.get('goalDuration', {}).get('millis', 0)
        if is_sla_at_risk(remaining, goal):
            return '⚠'
        return '▶'  # Active

    if completed:
        last_cycle = completed[-1]
        if last_cycle.get('breached'):
            return '✗'
        return '✓'

    return '?'

def get_sla_status_text(sla: Dict[str, Any]) -> str:
    """
    Get human-readable SLA status.

    Args:
        sla: SLA metric object

    Returns:
        Status text
    """
    ongoing = sla.get('ongoingCycle')
    completed = sla.get('completedCycles', [])

    if ongoing:
        if ongoing.get('breached'):
            return 'BREACHED'
        if ongoing.get('paused'):
            return 'Paused'
        remaining = ongoing.get('remainingTime', {}).get('millis', 0)
        goal = ongoing.get('goalDuration', {}).get('millis', 0)
        if is_sla_at_risk(remaining, goal):
            return 'At Risk'
        return 'Active'

    if completed:
        last_cycle = completed[-1]
        if last_cycle.get('breached'):
            return 'Failed'
        return 'Met'

    return 'Unknown'
```

---

## Commit Strategy

### Commit Types

**test:** Adding or updating tests
- `test(jira-jsm): add failing tests for get_sla`

**feat:** Implementing features
- `feat(jira-jsm): implement get_sla.py (8/8 tests passing)`

**docs:** Documentation updates
- `docs(jira-jsm): add SLA and queue documentation`

**fix:** Bug fixes
- `fix(jira-jsm): handle missing SLA data gracefully`

---

## API Sources

- [Service Desk Request SLA API](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-request/#api-rest-servicedeskapi-request-issueidorkey-sla-get)
- [Service Desk Queue API](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-servicedesk/#api-rest-servicedeskapi-servicedesk-servicedeskid-queue-get)
- [JSM SLA Documentation](https://support.atlassian.com/jira-service-management-cloud/docs/set-up-slas/)
- [JSM Queue Documentation](https://support.atlassian.com/jira-service-management-cloud/docs/use-queues-to-group-issues/)

---

**Plan Version:** 1.0
**Created:** 2025-12-25
**Status:** READY FOR IMPLEMENTATION

### Estimated Scope

| Metric | Estimate |
|--------|----------|
| Unit Tests | 40 |
| Live Integration Tests | 14 |
| Scripts | 5 |
| JiraClient Methods | 5 |
| Helper Functions | 6 |
| Skills Affected | 2 (jira-jsm, jira-search) |
| Estimated Effort | ~20-25 hours |
