# JIRA Time Tracking Skill - TDD Implementation Plan

## Overview

**Objective:** Implement comprehensive time tracking and worklog management using Test-Driven Development (TDD)

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
- **Test Location:** `.claude/skills/jira-time/tests/`

**Feature Priority:**
1. **Phase 1: Worklog CRUD** (Foundation - add/view/edit/delete time entries)
2. **Phase 2: Time Estimates** (Original and remaining estimates)
3. **Phase 3: Time Reports** (Aggregation and reporting)
4. **Phase 4: Bulk Operations** (Multi-issue time logging)

---

## JIRA API Reference

### Worklog Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rest/api/3/issue/{issueIdOrKey}/worklog` | Add worklog to issue |
| GET | `/rest/api/3/issue/{issueIdOrKey}/worklog` | Get all worklogs for issue |
| GET | `/rest/api/3/issue/{issueIdOrKey}/worklog/{id}` | Get specific worklog |
| PUT | `/rest/api/3/issue/{issueIdOrKey}/worklog/{id}` | Update worklog |
| DELETE | `/rest/api/3/issue/{issueIdOrKey}/worklog/{id}` | Delete worklog |
| GET | `/rest/api/3/worklog/updated` | Get worklogs updated since timestamp |
| POST | `/rest/api/3/worklog/list` | Get worklogs by IDs (bulk) |

### Add Worklog Request Body

```json
{
  "timeSpentSeconds": 12000,
  "started": "2025-01-17T12:34:00.000+0000",
  "comment": {
    "type": "doc",
    "version": 1,
    "content": [
      {
        "type": "paragraph",
        "content": [
          {"type": "text", "text": "Debugging authentication issue"}
        ]
      }
    ]
  },
  "visibility": {
    "type": "group",
    "identifier": "jira-developers"
  }
}
```

### Query Parameters for Add Worklog

| Parameter | Description |
|-----------|-------------|
| `adjustEstimate` | How to adjust remaining estimate: `new`, `leave`, `manual`, `auto` |
| `newEstimate` | New remaining estimate (when `adjustEstimate=new`) |
| `reduceBy` | Amount to reduce estimate by (when `adjustEstimate=manual`) |
| `expand` | Fields to expand (e.g., `renderedFields`) |
| `notifyUsers` | Whether to notify watchers (default: true) |

### Time Tracking Fields (on Issue)

```json
{
  "fields": {
    "timetracking": {
      "originalEstimate": "2d",
      "originalEstimateSeconds": 57600,
      "remainingEstimate": "1d 4h",
      "remainingEstimateSeconds": 43200,
      "timeSpent": "4h",
      "timeSpentSeconds": 14400
    }
  }
}
```

### Update Estimates (PUT Issue)

```json
{
  "fields": {
    "timetracking": {
      "originalEstimate": "2d",
      "remainingEstimate": "1d"
    }
  }
}
```

**Important:** Always set both `originalEstimate` and `remainingEstimate` together due to [known bug JRACLOUD-67539](https://jira.atlassian.com/browse/JRACLOUD-67539) where updating only `remainingEstimate` may overwrite `originalEstimate`.

### Time Format Strings

JIRA accepts human-readable time formats:
- `30m` - 30 minutes
- `2h` - 2 hours
- `1d` - 1 day (8 hours by default)
- `1w` - 1 week (5 days by default)
- `2d 4h 30m` - Combined format

---

## Test Infrastructure Setup

### Initial Setup Tasks

- [x] **Setup 1.1:** Create skill structure ✅
  - [x] Create `.claude/skills/jira-time/` directory
  - [x] Create `scripts/` subdirectory
  - [x] Create `tests/` subdirectory
  - [x] Create `SKILL.md` skeleton
  - **Commit:** `feat(jira-time): create skill structure and add time tracking infrastructure`

- [x] **Setup 1.2:** Create test infrastructure ✅
  - [x] Create `tests/conftest.py` with shared fixtures
  - [x] Mock JiraClient fixture
  - [x] Sample worklog response fixture
  - [x] Sample time tracking response fixture
  - **Commit:** `feat(jira-time): create skill structure and add time tracking infrastructure`

- [x] **Setup 1.3:** Add JiraClient methods for time tracking ✅
  - [x] `add_worklog(issue_key, time_spent, started, comment, adjust_estimate)` - Add worklog
  - [x] `get_worklogs(issue_key)` - Get all worklogs for issue
  - [x] `get_worklog(issue_key, worklog_id)` - Get specific worklog
  - [x] `update_worklog(issue_key, worklog_id, time_spent, started, comment)` - Update worklog
  - [x] `delete_worklog(issue_key, worklog_id)` - Delete worklog
  - [x] `get_time_tracking(issue_key)` - Get time tracking summary
  - [x] `set_time_tracking(issue_key, original, remaining)` - Set estimates
  - **Commit:** `feat(jira-time): create skill structure and add time tracking infrastructure`

---

## Phase 1: Worklog CRUD Operations

### Feature 1.1: Add Worklog

**Script:** `add_worklog.py`

**JIRA API:**
- `POST /rest/api/3/issue/{issueIdOrKey}/worklog`

**Test File:** `tests/test_add_worklog.py`

**Test Cases:**
```python
def test_add_worklog_time_spent():
    """Test adding worklog with time spent (e.g., '2h')."""
    # Should POST with timeSpentSeconds calculated

def test_add_worklog_with_started_datetime():
    """Test specifying when work was started."""
    # Should set started field in ISO format

def test_add_worklog_with_comment():
    """Test adding worklog with ADF comment."""
    # Should convert text to ADF format

def test_add_worklog_adjust_estimate_auto():
    """Test automatic estimate adjustment."""
    # Should use adjustEstimate=auto (default)

def test_add_worklog_adjust_estimate_leave():
    """Test leaving estimate unchanged."""
    # Should use adjustEstimate=leave

def test_add_worklog_adjust_estimate_new():
    """Test setting new remaining estimate."""
    # Should use adjustEstimate=new with newEstimate

def test_add_worklog_invalid_time_format():
    """Test validation of time format."""
    # Should raise ValidationError for invalid formats

def test_add_worklog_issue_not_found():
    """Test error when issue doesn't exist."""
    # Should raise NotFoundError

def test_add_worklog_time_tracking_disabled():
    """Test error when time tracking is disabled."""
    # Should raise JiraError with helpful message
```

**CLI Interface:**
```bash
# Basic usage
python add_worklog.py PROJ-123 --time 2h
python add_worklog.py PROJ-123 --time "1d 4h" --comment "Debugging auth issue"

# With start time
python add_worklog.py PROJ-123 --time 2h --started "2025-01-15 09:00"
python add_worklog.py PROJ-123 --time 2h --started yesterday

# Estimate adjustment
python add_worklog.py PROJ-123 --time 2h --adjust-estimate leave
python add_worklog.py PROJ-123 --time 2h --adjust-estimate new --new-estimate "1d"
```

**Output Example:**
```
Worklog added to PROJ-123:
  Time logged: 2h (7200 seconds)
  Started: 2025-01-15 09:00:00
  Comment: Debugging auth issue
  Remaining estimate: 6h (was 8h)

Worklog ID: 10045
```

**Acceptance Criteria:**
- [x] All 12 tests pass ✅
- [x] Supports human-readable time formats (2h, 1d, etc.) ✅
- [x] Optional comment support with ADF conversion ✅
- [x] Estimate adjustment options ✅
- [x] Validates time format before API call ✅

**Commits:**
1. `feat(jira-time): implement Phase 1 - Worklog CRUD (32 tests)` ✅

---

### Feature 1.2: Get Worklogs

**Script:** `get_worklogs.py`

**JIRA API:**
- `GET /rest/api/3/issue/{issueIdOrKey}/worklog`

**Test File:** `tests/test_get_worklogs.py`

**Test Cases:**
```python
def test_get_all_worklogs():
    """Test fetching all worklogs for an issue."""
    # Should return list of worklog objects

def test_get_worklogs_with_pagination():
    """Test handling paginated results."""
    # Should fetch all pages

def test_get_worklogs_filter_by_author():
    """Test filtering worklogs by author."""
    # Should show only specified author's worklogs

def test_get_worklogs_filter_by_date_range():
    """Test filtering by date range."""
    # Should filter by started date

def test_get_worklogs_format_text():
    """Test human-readable output."""
    # Should show formatted table

def test_get_worklogs_format_json():
    """Test JSON output."""
    # Should return valid JSON

def test_get_worklogs_empty():
    """Test output when no worklogs exist."""
    # Should show helpful message

def test_get_worklogs_issue_not_found():
    """Test error when issue doesn't exist."""
```

**CLI Interface:**
```bash
python get_worklogs.py PROJ-123
python get_worklogs.py PROJ-123 --author currentUser()
python get_worklogs.py PROJ-123 --since 2025-01-01 --until 2025-01-31
python get_worklogs.py PROJ-123 --output json
```

**Output Example:**
```
Worklogs for PROJ-123:

ID       Author        Started              Time     Comment
───────  ────────────  ───────────────────  ───────  ─────────────────────
10045    alice@co.com  2025-01-15 09:00     2h       Debugging auth issue
10046    bob@co.com    2025-01-15 14:30     1h 30m   Code review
10047    alice@co.com  2025-01-16 10:00     4h       Implemented fix

Total: 7h 30m (3 entries)
```

**Acceptance Criteria:**
- [x] All 9 tests pass ✅
- [x] Shows all worklogs with details ✅
- [x] Supports filtering by author and date ✅
- [x] Calculates total time ✅
- [x] Pagination handling ✅

**Commits:**
1. `feat(jira-time): implement Phase 1 - Worklog CRUD (32 tests)` ✅

---

### Feature 1.3: Update Worklog

**Script:** `update_worklog.py`

**JIRA API:**
- `PUT /rest/api/3/issue/{issueIdOrKey}/worklog/{id}`

**Test File:** `tests/test_update_worklog.py`

**Test Cases:**
```python
def test_update_worklog_time():
    """Test updating time spent."""

def test_update_worklog_started():
    """Test updating start time."""

def test_update_worklog_comment():
    """Test updating comment."""

def test_update_worklog_multiple_fields():
    """Test updating multiple fields at once."""

def test_update_worklog_not_found():
    """Test error when worklog doesn't exist."""

def test_update_worklog_not_author():
    """Test error when not the worklog author."""
```

**CLI Interface:**
```bash
python update_worklog.py PROJ-123 --worklog-id 10045 --time 3h
python update_worklog.py PROJ-123 --worklog-id 10045 --comment "Updated description"
python update_worklog.py PROJ-123 --worklog-id 10045 --started "2025-01-15 10:00"
```

**Acceptance Criteria:**
- [x] All 6 tests pass ✅
- [x] Can update time, started, and comment ✅
- [x] Validates worklog ownership ✅

**Commits:**
1. `feat(jira-time): implement Phase 1 - Worklog CRUD (32 tests)` ✅

---

### Feature 1.4: Delete Worklog

**Script:** `delete_worklog.py`

**JIRA API:**
- `DELETE /rest/api/3/issue/{issueIdOrKey}/worklog/{id}`

**Test File:** `tests/test_delete_worklog.py`

**Test Cases:**
```python
def test_delete_worklog():
    """Test deleting a worklog."""

def test_delete_worklog_adjust_estimate():
    """Test estimate adjustment on delete."""

def test_delete_worklog_not_found():
    """Test error when worklog doesn't exist."""

def test_delete_worklog_with_confirmation():
    """Test confirmation prompt."""

def test_delete_worklog_dry_run():
    """Test dry-run mode."""
```

**CLI Interface:**
```bash
python delete_worklog.py PROJ-123 --worklog-id 10045
python delete_worklog.py PROJ-123 --worklog-id 10045 --adjust-estimate new --new-estimate "2d"
python delete_worklog.py PROJ-123 --worklog-id 10045 --dry-run
python delete_worklog.py PROJ-123 --worklog-id 10045 --yes  # Skip confirmation
```

**Acceptance Criteria:**
- [x] All 5 tests pass ✅
- [x] Confirmation before delete ✅
- [x] Dry-run mode ✅
- [x] Estimate adjustment options ✅

**Commits:**
1. `feat(jira-time): implement Phase 1 - Worklog CRUD (32 tests)` ✅

---

### Phase 1 Completion ✅

- [x] **Phase 1 Summary:**
  - [x] 4 scripts implemented (add_worklog, get_worklogs, update_worklog, delete_worklog) ✅
  - [x] 32 tests passing (12 + 9 + 6 + 5) ✅
  - [x] JiraClient methods added (7 methods) ✅
  - [x] time_utils.py helper module added ✅
  - **Commit:** `feat(jira-time): implement Phase 1 - Worklog CRUD (32 tests)` ✅

---

## Phase 2: Time Estimates

### Feature 2.1: Set Time Estimates

**Script:** `set_estimate.py`

**JIRA API:**
- `PUT /rest/api/3/issue/{issueIdOrKey}` with `timetracking` field

**Test File:** `tests/test_set_estimate.py`

**Test Cases:**
```python
def test_set_original_estimate():
    """Test setting original estimate."""

def test_set_remaining_estimate():
    """Test setting remaining estimate."""

def test_set_both_estimates():
    """Test setting both estimates together."""

def test_set_estimate_clears_value():
    """Test clearing estimate (set to None)."""

def test_set_estimate_invalid_format():
    """Test validation of time format."""

def test_set_estimate_field_not_on_screen():
    """Test error when field not available."""
```

**CLI Interface:**
```bash
python set_estimate.py PROJ-123 --original "2d"
python set_estimate.py PROJ-123 --remaining "1d 4h"
python set_estimate.py PROJ-123 --original "2d" --remaining "1d 4h"
python set_estimate.py PROJ-123 --clear-original
```

**Output Example:**
```
Time estimates updated for PROJ-123:
  Original estimate: 2d (was unset)
  Remaining estimate: 1d 4h (was unset)
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Sets both estimates together (bug workaround)
- [ ] Validates time format
- [ ] Can clear estimates

**Commits:**
1. `test(jira-time): add failing tests for set_estimate`
2. `feat(jira-time): implement set_estimate.py (6/6 tests passing)`

---

### Feature 2.2: Get Time Tracking Summary

**Script:** `get_time_tracking.py`

**JIRA API:**
- `GET /rest/api/3/issue/{issueIdOrKey}` with `fields=timetracking`

**Test File:** `tests/test_get_time_tracking.py`

**Test Cases:**
```python
def test_get_time_tracking_full():
    """Test fetching complete time tracking info."""

def test_get_time_tracking_no_work_logged():
    """Test when no work has been logged."""

def test_get_time_tracking_no_estimates():
    """Test when estimates not set."""

def test_get_time_tracking_calculate_progress():
    """Test calculating completion percentage."""

def test_get_time_tracking_format_text():
    """Test human-readable output."""

def test_get_time_tracking_format_json():
    """Test JSON output."""
```

**CLI Interface:**
```bash
python get_time_tracking.py PROJ-123
python get_time_tracking.py PROJ-123 --output json
```

**Output Example:**
```
Time Tracking for PROJ-123:

Original Estimate:    2d (16h)
Remaining Estimate:   1d 4h (12h)
Time Spent:           4h

Progress: ████████░░ 25% complete
          4h logged of 16h estimated
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Shows all time tracking fields
- [ ] Calculates progress percentage
- [ ] Visual progress bar in text mode

**Commits:**
1. `test(jira-time): add failing tests for get_time_tracking`
2. `feat(jira-time): implement get_time_tracking.py (6/6 tests passing)`

---

### Phase 2 Completion

- [ ] **Phase 2 Summary:**
  - [ ] 2 scripts implemented (set_estimate, get_time_tracking)
  - [ ] 12 tests passing (40 total)
  - **Commit:** `docs(jira-time): complete Phase 2 - Time Estimates`

---

## Phase 3: Time Reports

### Feature 3.1: Time Report

**Script:** `time_report.py`

**JIRA API:**
- `GET /rest/api/3/worklog/updated` - Get updated worklogs
- `POST /rest/api/3/worklog/list` - Bulk fetch worklogs
- `GET /rest/api/3/search` - Find issues with worklogs

**Test File:** `tests/test_time_report.py`

**Test Cases:**
```python
def test_report_by_user():
    """Test time report for specific user."""

def test_report_by_project():
    """Test time report for project."""

def test_report_by_date_range():
    """Test time report for date range."""

def test_report_group_by_issue():
    """Test grouping by issue."""

def test_report_group_by_day():
    """Test grouping by day."""

def test_report_group_by_user():
    """Test grouping by user."""

def test_report_format_table():
    """Test table output."""

def test_report_format_csv():
    """Test CSV output for export."""

def test_report_format_json():
    """Test JSON output."""

def test_report_calculate_totals():
    """Test total calculations."""
```

**CLI Interface:**
```bash
# By user
python time_report.py --user currentUser() --period last-week
python time_report.py --user alice@company.com --since 2025-01-01 --until 2025-01-31

# By project
python time_report.py --project PROJ --period this-month
python time_report.py --project PROJ --since 2025-01-01

# Grouping
python time_report.py --user currentUser() --group-by issue
python time_report.py --project PROJ --group-by day
python time_report.py --project PROJ --group-by user

# Export
python time_report.py --project PROJ --period last-month --output csv > timesheet.csv
```

**Output Example (by user, grouped by issue):**
```
Time Report: alice@company.com
Period: 2025-01-13 to 2025-01-19

Issue        Summary                     Time Logged
───────────  ──────────────────────────  ───────────
PROJ-123     Authentication refactor     12h 30m
PROJ-124     API documentation           4h
PROJ-125     Bug fix: login redirect     2h 15m

Total: 18h 45m

By Day:
  Mon 2025-01-13:  6h
  Tue 2025-01-14:  4h 30m
  Wed 2025-01-15:  3h
  Thu 2025-01-16:  5h 15m
  Fri 2025-01-17:  0h
```

**Acceptance Criteria:**
- [ ] All 10 tests pass
- [ ] Supports user and project filtering
- [ ] Multiple grouping options
- [ ] CSV export for billing/invoicing
- [ ] Period shortcuts (last-week, this-month, etc.)

**Commits:**
1. `test(jira-time): add failing tests for time_report`
2. `feat(jira-time): implement time_report.py (10/10 tests passing)`

---

### Feature 3.2: Export Timesheets

**Script:** `export_timesheets.py`

**JIRA API:**
- Uses same APIs as time_report.py

**Test File:** `tests/test_export_timesheets.py`

**Test Cases:**
```python
def test_export_csv_format():
    """Test CSV export with proper headers."""

def test_export_json_format():
    """Test JSON export structure."""

def test_export_with_billable_hours():
    """Test marking billable vs non-billable time."""

def test_export_includes_all_fields():
    """Test all required fields are included."""

def test_export_to_file():
    """Test writing to output file."""
```

**CLI Interface:**
```bash
python export_timesheets.py --project PROJ --period 2025-01 --output timesheets.csv
python export_timesheets.py --project PROJ --period 2025-01 --format json --output timesheets.json
python export_timesheets.py --user currentUser() --period last-month --include-billable
```

**CSV Output Example:**
```csv
Issue Key,Issue Summary,Author,Date,Time Spent,Time Seconds,Comment
PROJ-123,Authentication refactor,alice@company.com,2025-01-15,2h,7200,Debugging auth issue
PROJ-123,Authentication refactor,alice@company.com,2025-01-16,4h,14400,Implemented fix
PROJ-124,API documentation,alice@company.com,2025-01-16,2h,7200,Updated endpoints
```

**Acceptance Criteria:**
- [ ] All 5 tests pass
- [ ] CSV format for spreadsheet import
- [ ] JSON format for programmatic use
- [ ] All relevant fields included

**Commits:**
1. `test(jira-time): add failing tests for export_timesheets`
2. `feat(jira-time): implement export_timesheets.py (5/5 tests passing)`

---

### Phase 3 Completion

- [ ] **Phase 3 Summary:**
  - [ ] 2 scripts implemented (time_report, export_timesheets)
  - [ ] 15 tests passing (55 total)
  - **Commit:** `docs(jira-time): complete Phase 3 - Time Reports`

---

## Phase 4: Bulk Operations

### Feature 4.1: Bulk Log Time

**Script:** `bulk_log_time.py`

**JIRA API:**
- `POST /rest/api/3/issue/{issueIdOrKey}/worklog` (multiple calls)

**Test File:** `tests/test_bulk_log_time.py`

**Test Cases:**
```python
def test_bulk_log_same_time():
    """Test logging same time to multiple issues."""

def test_bulk_log_from_jql():
    """Test logging time to JQL results."""

def test_bulk_log_dry_run():
    """Test preview without logging."""

def test_bulk_log_progress():
    """Test progress indicator."""

def test_bulk_log_partial_failure():
    """Test handling when some logs fail."""

def test_bulk_log_with_comment():
    """Test adding same comment to all."""
```

**CLI Interface:**
```bash
# Same time to multiple issues
python bulk_log_time.py --issues PROJ-1,PROJ-2,PROJ-3 --time 30m --comment "Sprint planning"

# From JQL query
python bulk_log_time.py --jql "project=PROJ AND sprint=456" --time 15m --comment "Daily standup"

# Dry run
python bulk_log_time.py --issues PROJ-1,PROJ-2 --time 1h --dry-run
```

**Output Example:**
```
Bulk Time Logging Preview (dry-run):
  PROJ-1: +30m (Authentication task)
  PROJ-2: +30m (Database migration)
  PROJ-3: +30m (API endpoint)

Would log 1h 30m total to 3 issues.
Run without --dry-run to apply.
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Log same time to multiple issues
- [ ] JQL query support
- [ ] Progress indicator
- [ ] Dry-run mode

**Commits:**
1. `test(jira-time): add failing tests for bulk_log_time`
2. `feat(jira-time): implement bulk_log_time.py (6/6 tests passing)`

---

### Phase 4 Completion

- [ ] **Phase 4 Summary:**
  - [ ] 1 script implemented (bulk_log_time)
  - [ ] 6 tests passing (61 total)
  - **Commit:** `docs(jira-time): complete Phase 4 - Bulk Operations`

---

## Integration & Polish

### Integration Tasks

- [ ] **Integration 1:** Update jira-issue scripts
  - [ ] `create_issue.py`: Add `--estimate` flag for original estimate
  - [ ] `get_issue.py`: Show time tracking summary with `--show-time`
  - **Commit:** `feat(jira-issue): add time tracking support to create/get`

- [ ] **Integration 2:** Update jira-search scripts
  - [ ] `jql_search.py`: Add `--show-time` option for time tracking fields
  - [ ] Add time spent/estimate columns to search output
  - **Commit:** `feat(jira-search): show time tracking in search results`

### Documentation Updates

- [ ] **Docs 1:** Create comprehensive SKILL.md
  - [ ] "When to use this skill" section
  - [ ] "What this skill does" section
  - [ ] "Available scripts" with descriptions
  - [ ] "Examples" with realistic workflows
  - [ ] Billing/invoicing workflow examples
  - [ ] Configuration notes
  - **Commit:** `docs(jira-time): create comprehensive SKILL.md`

- [ ] **Docs 2:** Update CLAUDE.md
  - [ ] Add jira-time to project overview
  - [ ] Add time tracking patterns section
  - **Commit:** `docs: update CLAUDE.md with jira-time skill`

- [ ] **Docs 3:** Update GAP_ANALYSIS.md
  - [ ] Mark Time Tracking gap as completed
  - [ ] Update coverage metrics
  - **Commit:** `docs: update GAP_ANALYSIS.md - Time Tracking complete`

### Testing & Quality

- [ ] **Quality 1:** Integration tests
  - [ ] End-to-end: Create issue → Set estimate → Log time → Get report
  - [ ] Live integration tests
  - **Commit:** `test(jira-time): add end-to-end integration tests`

- [ ] **Quality 2:** Coverage validation
  - [ ] Run `pytest --cov=.claude/skills/jira-time --cov-report=html`
  - [ ] Target: 85%+ coverage

- [ ] **Quality 3:** Error handling review
  - [ ] All scripts use try/except with JiraError
  - [ ] Time tracking disabled detection
  - [ ] Helpful error messages

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 65+ unit tests passing (32/65 complete)
- [ ] 2+ integration tests passing
- [ ] Coverage ≥ 85%

**Scripts:**
- [ ] 9 new scripts implemented
- [ ] All scripts have `--help`
- [ ] All scripts support `--profile`
- [ ] Mutation scripts have `--dry-run`

**Documentation:**
- [ ] SKILL.md complete with examples
- [ ] CLAUDE.md updated
- [ ] GAP_ANALYSIS.md updated
- [ ] All scripts have docstrings

**Integration:**
- [ ] 2 existing skills updated (jira-issue, jira-search)
- [ ] No breaking changes

### Progress Tracking

**Test Status:** 32/65 tests passing ✅

**Phase Status:**
- [x] Phase 1: Worklog CRUD (4 scripts, 32 tests) ✅
- [ ] Phase 2: Time Estimates (2 scripts, 12 tests)
- [ ] Phase 3: Time Reports (2 scripts, 15 tests)
- [ ] Phase 4: Bulk Operations (1 script, 6 tests)
- [ ] Integration (2 updates)
- [ ] Documentation (3 docs)
- [ ] Quality (3 tasks)

---

## Script Summary

| Script | Phase | Tests | Status | Description |
|--------|-------|-------|--------|-------------|
| `add_worklog.py` | 1 | 12 | ✅ | Add time entry to issue |
| `get_worklogs.py` | 1 | 9 | ✅ | List worklogs for issue |
| `update_worklog.py` | 1 | 6 | ✅ | Modify existing worklog |
| `delete_worklog.py` | 1 | 5 | ✅ | Remove worklog |
| `set_estimate.py` | 2 | 6 | ⏳ | Set original/remaining estimates |
| `get_time_tracking.py` | 2 | 6 | ⏳ | View time tracking summary |
| `time_report.py` | 3 | 10 | ⏳ | Generate time reports |
| `export_timesheets.py` | 3 | 5 | ⏳ | Export to CSV/JSON |
| `bulk_log_time.py` | 4 | 6 | ⏳ | Bulk time logging |
| **Total** | - | **65** | 32 ✅ | - |

---

## JiraClient Methods to Add

```python
# In shared/scripts/lib/jira_client.py

def add_worklog(self, issue_key: str, time_spent: str, started: str = None,
                comment: str = None, adjust_estimate: str = 'auto',
                new_estimate: str = None) -> dict:
    """Add a worklog to an issue.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        time_spent: Time spent in JIRA format (e.g., '2h', '1d 4h')
        started: When work started (ISO format or relative like 'yesterday')
        comment: Optional comment text
        adjust_estimate: How to adjust remaining estimate ('auto', 'leave', 'new', 'manual')
        new_estimate: New remaining estimate (when adjust_estimate='new')

    Returns:
        Created worklog object
    """
    payload = {
        'timeSpent': time_spent
    }
    if started:
        payload['started'] = self._format_datetime(started)
    if comment:
        payload['comment'] = text_to_adf(comment)

    params = {'adjustEstimate': adjust_estimate}
    if new_estimate:
        params['newEstimate'] = new_estimate

    return self.post(f'/rest/api/3/issue/{issue_key}/worklog',
                     data=payload, params=params)

def get_worklogs(self, issue_key: str) -> list:
    """Get all worklogs for an issue."""
    result = self.get(f'/rest/api/3/issue/{issue_key}/worklog')
    return result.get('worklogs', [])

def get_worklog(self, issue_key: str, worklog_id: str) -> dict:
    """Get a specific worklog."""
    return self.get(f'/rest/api/3/issue/{issue_key}/worklog/{worklog_id}')

def update_worklog(self, issue_key: str, worklog_id: str,
                   time_spent: str = None, started: str = None,
                   comment: str = None) -> dict:
    """Update an existing worklog."""
    payload = {}
    if time_spent:
        payload['timeSpent'] = time_spent
    if started:
        payload['started'] = self._format_datetime(started)
    if comment:
        payload['comment'] = text_to_adf(comment)

    return self.put(f'/rest/api/3/issue/{issue_key}/worklog/{worklog_id}',
                    data=payload)

def delete_worklog(self, issue_key: str, worklog_id: str,
                   adjust_estimate: str = 'auto') -> None:
    """Delete a worklog."""
    params = {'adjustEstimate': adjust_estimate}
    self.delete(f'/rest/api/3/issue/{issue_key}/worklog/{worklog_id}',
                params=params)

def get_time_tracking(self, issue_key: str) -> dict:
    """Get time tracking info for an issue."""
    issue = self.get(f'/rest/api/3/issue/{issue_key}',
                     params={'fields': 'timetracking'})
    return issue.get('fields', {}).get('timetracking', {})

def set_time_tracking(self, issue_key: str, original_estimate: str = None,
                      remaining_estimate: str = None) -> None:
    """Set time tracking estimates.

    Note: Always set both estimates together due to JIRA bug JRACLOUD-67539.
    """
    timetracking = {}
    if original_estimate:
        timetracking['originalEstimate'] = original_estimate
    if remaining_estimate:
        timetracking['remainingEstimate'] = remaining_estimate

    self.put(f'/rest/api/3/issue/{issue_key}',
             data={'fields': {'timetracking': timetracking}})
```

---

## Helper Functions

### Time Parsing

```python
# In shared/scripts/lib/time_utils.py (new file)

import re
from datetime import datetime, timedelta
from typing import Union

def parse_time_string(time_str: str) -> int:
    """Parse JIRA time format to seconds.

    Args:
        time_str: Time string like '2h', '1d 4h 30m', '3w 2d'

    Returns:
        Time in seconds

    Examples:
        >>> parse_time_string('2h')
        7200
        >>> parse_time_string('1d 4h')
        43200
    """
    patterns = {
        'w': 5 * 8 * 3600,  # 1 week = 5 days
        'd': 8 * 3600,       # 1 day = 8 hours
        'h': 3600,           # 1 hour
        'm': 60              # 1 minute
    }

    total_seconds = 0
    for match in re.finditer(r'(\d+)\s*([wdhm])', time_str.lower()):
        value, unit = match.groups()
        total_seconds += int(value) * patterns[unit]

    if total_seconds == 0:
        raise ValueError(f"Invalid time format: {time_str}")

    return total_seconds

def format_seconds(seconds: int) -> str:
    """Format seconds to human-readable time.

    Args:
        seconds: Time in seconds

    Returns:
        Human-readable string like '1d 4h 30m'

    Examples:
        >>> format_seconds(7200)
        '2h'
        >>> format_seconds(43200)
        '1d 4h'
    """
    if seconds == 0:
        return '0m'

    parts = []
    hours_per_day = 8
    days_per_week = 5

    weeks = seconds // (days_per_week * hours_per_day * 3600)
    seconds %= (days_per_week * hours_per_day * 3600)

    days = seconds // (hours_per_day * 3600)
    seconds %= (hours_per_day * 3600)

    hours = seconds // 3600
    seconds %= 3600

    minutes = seconds // 60

    if weeks:
        parts.append(f'{weeks}w')
    if days:
        parts.append(f'{days}d')
    if hours:
        parts.append(f'{hours}h')
    if minutes:
        parts.append(f'{minutes}m')

    return ' '.join(parts)

def parse_relative_date(date_str: str) -> datetime:
    """Parse relative date strings.

    Args:
        date_str: Date string like 'yesterday', 'last-week', '2025-01-15'

    Returns:
        datetime object
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    relative_dates = {
        'today': today,
        'yesterday': today - timedelta(days=1),
        'last-week': today - timedelta(weeks=1),
        'this-week': today - timedelta(days=today.weekday()),
        'last-month': (today.replace(day=1) - timedelta(days=1)).replace(day=1),
        'this-month': today.replace(day=1),
    }

    if date_str.lower() in relative_dates:
        return relative_dates[date_str.lower()]

    # Try ISO format
    return datetime.fromisoformat(date_str)
```

---

## Commit Strategy

### Commit Types

**test:** Adding or updating tests
- `test(jira-time): add failing tests for add_worklog`

**feat:** Implementing features
- `feat(jira-time): implement add_worklog.py (9/9 tests passing)`

**docs:** Documentation updates
- `docs(jira-time): add worklog examples to SKILL.md`

**fix:** Bug fixes
- `fix(jira-time): handle time tracking disabled gracefully`

---

## API Sources

- [Issue Worklogs API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-worklogs/)
- [Update Issue (timetracking field)](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-put)
- [JRACLOUD-67539 Bug](https://jira.atlassian.com/browse/JRACLOUD-67539) - remainingEstimate overwrites originalEstimate
- [Configuring Time Tracking](https://support.atlassian.com/jira-cloud-administration/docs/configure-time-tracking/)

---

**Plan Version:** 1.1
**Created:** 2025-12-25
**Last Updated:** 2025-12-25
**Status:** IN PROGRESS - Phase 1 complete (32/65 tests passing)
