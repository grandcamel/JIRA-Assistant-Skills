# JIRA Agile Skill - TDD Implementation Plan

## Overview

**Objective:** Implement comprehensive Agile/Scrum functionality using Test-Driven Development (TDD)

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
- **Test Location:** `.claude/skills/jira-agile/tests/`

**Feature Priority:**
1. ✅ **Phase 1: Epics** (Foundation for hierarchies)
2. ✅ **Phase 2: Sprints** (Core Agile workflow)
3. ✅ **Phase 3: Backlog** (Sprint planning support)
4. ✅ **Phase 4: Story Points** (Estimation)

---

## Test Infrastructure Setup

### Initial Setup Tasks

- [x] **Setup 1.1:** Create test infrastructure
  - [x] Install pytest: `pip install pytest pytest-cov responses`
  - [x] Create `.claude/skills/jira-agile/tests/` directory
  - [x] Create `conftest.py` with shared fixtures
  - [x] Create `test_jira_client_agile.py` for new JiraClient methods
  - [x] Update requirements.txt with test dependencies
  - **Commit:** `test(jira-agile): add pytest infrastructure and fixtures` ✅

- [x] **Setup 1.2:** Create base test fixtures
  - [x] Mock JiraClient fixture
  - [x] Sample epic response fixture
  - [x] Sample sprint response fixture
  - [x] Sample board response fixture
  - **Commit:** `test(jira-agile): add base fixtures for mocking API responses` ✅

- [x] **Setup 1.3:** Configure pytest
  - [x] Create `pytest.ini` in project root
  - [x] Configure coverage reporting
  - [x] Add test command to documentation
  - **Commit:** `test: configure pytest and coverage reporting` ✅

---

## Phase 1: Epic Management

### Feature 1.1: Create Epic ✅ COMPLETED

**Script:** `create_epic.py`

**JIRA API:**
- `POST /rest/api/3/issue` with `issuetype: {name: "Epic"}`
- Epic Name field: `customfield_10011` (may vary per instance)
- Epic Color field: `customfield_10012` (may vary per instance)

**Test File:** `tests/test_create_epic.py`

**Test Cases (Write These First):**
```python
def test_create_epic_minimal():
    """Test creating epic with only required fields (project, summary)"""
    # Should POST with project, issuetype=Epic, summary

def test_create_epic_with_description():
    """Test creating epic with markdown description"""
    # Should convert markdown to ADF

def test_create_epic_with_epic_name():
    """Test setting Epic Name field"""
    # Should set customfield_10011

def test_create_epic_with_color():
    """Test setting epic color"""
    # Should set customfield_10012 with valid color

def test_create_epic_invalid_color():
    """Test validation of epic color"""
    # Should raise ValidationError for invalid color

def test_create_epic_missing_project():
    """Test error handling for missing required field"""
    # Should raise ValidationError

def test_create_epic_api_error():
    """Test handling of JIRA API errors"""
    # Should raise appropriate JiraError subclass
```

**Acceptance Criteria:**
- [x] All 7 tests pass
- [x] Coverage ≥ 85% for create_epic.py
- [x] Script executable from command line
- [x] Help text shows all options
- [x] Integrates with existing config system

**CLI Interface:**
```bash
python create_epic.py --project PROJ --summary "Epic summary" --epic-name "MVP"
python create_epic.py --project PROJ --summary "Epic" --description "Details" --color blue
python create_epic.py --project PROJ --summary "Epic" --assignee self --priority High
```

**Integration Points:**
- [ ] Update `create_issue.py` to add `--epic` flag for creating issues in epic
- [ ] Update SKILL.md with epic creation examples

**Commits:**
1. `test(jira-agile): add failing tests for create_epic`
2. `feat(jira-agile): implement create_epic.py (7/7 tests passing)`
3. `docs(jira-agile): add epic creation to SKILL.md`

---

### Feature 1.2: Add Issues to Epic ✅ COMPLETED

**Script:** `add_to_epic.py`

**JIRA API:**
- `POST /rest/api/3/epic/{epicIdOrKey}/issue` (newer API)
- OR `PUT /rest/api/3/issue/{issueIdOrKey}` with epic link field

**Test File:** `tests/test_add_to_epic.py`

**Test Cases:**
```python
def test_add_single_issue_to_epic():
    """Test adding one issue to epic"""

def test_add_multiple_issues_to_epic():
    """Test bulk adding issues to epic"""

def test_add_to_epic_with_dry_run():
    """Test dry-run mode shows preview without making changes"""

def test_add_to_epic_invalid_epic():
    """Test error when epic doesn't exist"""

def test_add_to_epic_invalid_issue():
    """Test error when issue doesn't exist"""

def test_add_to_epic_not_epic_type():
    """Test error when target is not an Epic issue type"""

def test_remove_from_epic():
    """Test removing issue from epic (set to None)"""
```

**CLI Interface:**
```bash
python add_to_epic.py --epic PROJ-100 --issues PROJ-101,PROJ-102,PROJ-103
python add_to_epic.py --epic PROJ-100 --issues PROJ-101 --dry-run
python add_to_epic.py --epic PROJ-100 --jql "project=PROJ AND status=Todo"
python add_to_epic.py --remove --issues PROJ-101  # Remove from epic
```

**Acceptance Criteria:**
- [x] All 7 tests pass
- [x] Supports single and bulk operations
- [x] Dry-run mode
- [x] Can add by issue keys or JQL query
- [x] Progress indicator for bulk ops

**Commits:**
1. `test(jira-agile): add failing tests for add_to_epic`
2. `feat(jira-agile): implement add_to_epic.py (7/7 tests passing)`

---

### Feature 1.3: Get Epic Details & Progress ✅ COMPLETED

**Script:** `get_epic.py`

**JIRA API:**
- `GET /rest/api/3/issue/{epicIdOrKey}`
- `GET /rest/api/3/search` with JQL `"Epic Link" = {epicKey}`

**Test File:** `tests/test_get_epic.py`

**Test Cases:**
```python
def test_get_epic_basic_info():
    """Test retrieving epic details"""

def test_get_epic_with_children():
    """Test fetching all issues in epic"""

def test_get_epic_progress_calculation():
    """Test calculating epic progress (done/total)"""

def test_get_epic_story_points_sum():
    """Test summing story points in epic"""

def test_get_epic_format_text():
    """Test text output format"""

def test_get_epic_format_json():
    """Test JSON output format"""

def test_get_epic_not_found():
    """Test error when epic doesn't exist"""
```

**CLI Interface:**
```bash
python get_epic.py PROJ-100
python get_epic.py PROJ-100 --with-children
python get_epic.py PROJ-100 --output json
```

**Output Example:**
```
Epic: PROJ-100
Name: Mobile App MVP
Status: In Progress
Progress: 12/20 issues (60%)
Story Points: 45/80 (56%)

Children:
  PROJ-101 [Done] - User authentication
  PROJ-102 [In Progress] - Dashboard layout
  ...
```

**Acceptance Criteria:**
- [x] All 7 tests pass
- [x] Shows epic metadata
- [x] Lists child issues
- [x] Calculates progress percentage
- [x] Sums story points if available

**Commits:**
1. `test(jira-agile): add failing tests for get_epic`
2. `feat(jira-agile): implement get_epic.py (7/7 tests passing)`

---

### Feature 1.4: Create Sub-task

**Script:** `create_subtask.py`

**JIRA API:**
- `POST /rest/api/3/issue` with `issuetype: {name: "Sub-task"}` and `parent: {key: ...}`

**Test File:** `tests/test_create_subtask.py`

**Test Cases:**
```python
def test_create_subtask_minimal():
    """Test creating subtask with parent and summary"""

def test_create_subtask_with_description():
    """Test subtask with markdown description"""

def test_create_subtask_inherits_project():
    """Test subtask inherits project from parent"""

def test_create_subtask_with_assignee():
    """Test assigning subtask (including 'self')"""

def test_create_subtask_with_estimate():
    """Test setting time estimate on subtask"""

def test_create_subtask_invalid_parent():
    """Test error when parent doesn't exist"""

def test_create_subtask_parent_not_story():
    """Test validation that some issue types can't have subtasks"""
```

**CLI Interface:**
```bash
python create_subtask.py --parent PROJ-101 --summary "Implement login API"
python create_subtask.py --parent PROJ-101 --summary "Task" --assignee self
python create_subtask.py --parent PROJ-101 --summary "Task" --estimate 4h
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Subtask linked to parent
- [ ] Inherits project from parent
- [ ] Supports all standard issue fields

**Integration Points:**
- [ ] Update `get_issue.py` to show subtasks

**Commits:**
1. `test(jira-agile): add failing tests for create_subtask`
2. `feat(jira-agile): implement create_subtask.py (7/7 tests passing)`
3. `feat(jira-issue): show subtasks in get_issue output`

---

### Phase 1 Completion

- [ ] **Phase 1 Summary:**
  - [ ] 4 scripts implemented (create_epic, add_to_epic, get_epic, create_subtask)
  - [ ] 28 tests passing
  - [ ] Coverage ≥ 85% for all epic-related code
  - [ ] SKILL.md updated with epic examples
  - **Commit:** `docs(jira-agile): complete Phase 1 - Epic Management`

---

## Phase 2: Sprint Management

### Feature 2.1: Create Sprint

**Script:** `create_sprint.py`

**JIRA API:**
- `POST /rest/agile/1.0/sprint` (Agile API, not standard API)

**Test File:** `tests/test_create_sprint.py`

**Test Cases:**
```python
def test_create_sprint_minimal():
    """Test creating sprint with board ID and name"""

def test_create_sprint_with_dates():
    """Test setting start and end dates"""

def test_create_sprint_with_goal():
    """Test setting sprint goal"""

def test_create_sprint_invalid_board():
    """Test error when board doesn't exist"""

def test_create_sprint_invalid_dates():
    """Test validation of date ranges (end > start)"""

def test_create_sprint_date_format():
    """Test various date input formats (ISO, relative)"""
```

**CLI Interface:**
```bash
python create_sprint.py --board 123 --name "Sprint 42"
python create_sprint.py --board 123 --name "Sprint 42" --start 2025-01-20 --end 2025-02-03
python create_sprint.py --board 123 --name "Sprint 42" --goal "Launch MVP"
python create_sprint.py --board 123 --name "Sprint 42" --start "+1 week" --duration 2w
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Sprint created in specified board
- [ ] Supports date ranges
- [ ] Sprint goal support

**Commits:**
1. `test(jira-agile): add failing tests for create_sprint`
2. `feat(jira-agile): implement create_sprint.py (6/6 tests passing)`

---

### Feature 2.2: Manage Sprint Lifecycle

**Script:** `manage_sprint.py`

**JIRA API:**
- `POST /rest/agile/1.0/sprint/{sprintId}/move` (move issues)
- `POST /rest/agile/1.0/sprint/{sprintId}` (update sprint state)

**Test File:** `tests/test_manage_sprint.py`

**Test Cases:**
```python
def test_start_sprint():
    """Test starting a sprint (moves from future to active)"""

def test_close_sprint():
    """Test closing active sprint"""

def test_close_sprint_with_incomplete_issues():
    """Test moving incomplete issues to next sprint"""

def test_update_sprint_dates():
    """Test extending sprint end date"""

def test_update_sprint_goal():
    """Test changing sprint goal mid-sprint"""

def test_get_active_sprint():
    """Test fetching current active sprint for board"""
```

**CLI Interface:**
```bash
python manage_sprint.py --sprint 456 --start
python manage_sprint.py --sprint 456 --close
python manage_sprint.py --sprint 456 --close --move-incomplete-to 457
python manage_sprint.py --sprint 456 --extend-by 3d
python manage_sprint.py --board 123 --get-active
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Can start/close sprints
- [ ] Handles incomplete issues
- [ ] Can update sprint metadata

**Commits:**
1. `test(jira-agile): add failing tests for manage_sprint`
2. `feat(jira-agile): implement manage_sprint.py (6/6 tests passing)`

---

### Feature 2.3: Move Issues to Sprint

**Script:** `move_to_sprint.py`

**JIRA API:**
- `POST /rest/agile/1.0/sprint/{sprintId}/issue`
- `POST /rest/agile/1.0/backlog/issue` (move to backlog)

**Test File:** `tests/test_move_to_sprint.py`

**Test Cases:**
```python
def test_move_single_issue_to_sprint():
    """Test moving one issue to sprint"""

def test_move_multiple_issues_to_sprint():
    """Test bulk moving issues"""

def test_move_to_sprint_by_jql():
    """Test moving all issues matching JQL query"""

def test_move_to_backlog():
    """Test removing issues from sprint (back to backlog)"""

def test_move_to_sprint_dry_run():
    """Test dry-run preview"""

def test_move_to_sprint_with_rank():
    """Test moving and setting rank position"""
```

**CLI Interface:**
```bash
python move_to_sprint.py --sprint 456 --issues PROJ-1,PROJ-2,PROJ-3
python move_to_sprint.py --sprint 456 --jql "project=PROJ AND status='To Do'"
python move_to_sprint.py --sprint 456 --issues PROJ-1 --rank top
python move_to_sprint.py --backlog --issues PROJ-5  # Remove from sprint
python move_to_sprint.py --sprint 456 --issues PROJ-1,PROJ-2 --dry-run
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Supports single and bulk moves
- [ ] JQL query support
- [ ] Dry-run mode
- [ ] Progress indicator for bulk ops

**Commits:**
1. `test(jira-agile): add failing tests for move_to_sprint`
2. `feat(jira-agile): implement move_to_sprint.py (6/6 tests passing)`

---

### Feature 2.4: Get Sprint Info & Report

**Script:** `get_sprint.py`

**JIRA API:**
- `GET /rest/agile/1.0/sprint/{sprintId}`
- `GET /rest/agile/1.0/sprint/{sprintId}/issue`

**Test File:** `tests/test_get_sprint.py`

**Test Cases:**
```python
def test_get_sprint_basic():
    """Test fetching sprint metadata"""

def test_get_sprint_with_issues():
    """Test listing all issues in sprint"""

def test_get_sprint_progress():
    """Test calculating sprint progress (burndown data)"""

def test_get_sprint_by_board_active():
    """Test finding active sprint for board"""

def test_get_sprint_format_text():
    """Test text output"""

def test_get_sprint_format_json():
    """Test JSON output"""
```

**CLI Interface:**
```bash
python get_sprint.py 456
python get_sprint.py 456 --with-issues
python get_sprint.py --board 123 --active
python get_sprint.py 456 --output json
```

**Output Example:**
```
Sprint: Sprint 42
Status: Active
Dates: 2025-01-20 → 2025-02-03 (8 days remaining)
Goal: Launch MVP
Progress: 15/25 issues (60%)
Story Points: 32/55 (58%)

Issues:
  [Done] PROJ-101 - User auth (5 pts)
  [In Progress] PROJ-102 - Dashboard (8 pts)
  [To Do] PROJ-103 - Settings (3 pts)
  ...
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Shows sprint metadata
- [ ] Lists issues in sprint
- [ ] Calculates progress

**Commits:**
1. `test(jira-agile): add failing tests for get_sprint`
2. `feat(jira-agile): implement get_sprint.py (6/6 tests passing)`

---

### Phase 2 Completion

- [ ] **Phase 2 Summary:**
  - [ ] 4 scripts implemented (create_sprint, manage_sprint, move_to_sprint, get_sprint)
  - [ ] 24 tests passing (52 total)
  - [ ] Coverage ≥ 85% for sprint-related code
  - [ ] SKILL.md updated with sprint examples
  - **Commit:** `docs(jira-agile): complete Phase 2 - Sprint Management`

---

## Phase 3: Backlog Management

### Feature 3.1: Rank Issues

**Script:** `rank_issue.py`

**JIRA API:**
- `PUT /rest/agile/1.0/issue/rank`

**Test File:** `tests/test_rank_issue.py`

**Test Cases:**
```python
def test_rank_issue_before():
    """Test ranking issue before another issue"""

def test_rank_issue_after():
    """Test ranking issue after another issue"""

def test_rank_issue_top():
    """Test moving issue to top of backlog"""

def test_rank_issue_bottom():
    """Test moving issue to bottom of backlog"""

def test_rank_multiple_issues():
    """Test bulk ranking"""

def test_rank_issue_invalid_position():
    """Test validation of rank position"""
```

**CLI Interface:**
```bash
python rank_issue.py PROJ-1 --before PROJ-2
python rank_issue.py PROJ-1 --after PROJ-3
python rank_issue.py PROJ-1 --top
python rank_issue.py PROJ-1 --bottom
python rank_issue.py PROJ-1,PROJ-2,PROJ-3 --before PROJ-10
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Supports before/after positioning
- [ ] Top/bottom shortcuts
- [ ] Bulk ranking

**Commits:**
1. `test(jira-agile): add failing tests for rank_issue`
2. `feat(jira-agile): implement rank_issue.py (6/6 tests passing)`

---

### Feature 3.2: Get Backlog

**Script:** `get_backlog.py`

**JIRA API:**
- `GET /rest/agile/1.0/board/{boardId}/backlog`

**Test File:** `tests/test_get_backlog.py`

**Test Cases:**
```python
def test_get_backlog_all():
    """Test fetching full backlog for board"""

def test_get_backlog_with_filter():
    """Test filtering backlog by JQL"""

def test_get_backlog_with_pagination():
    """Test paginated backlog retrieval"""

def test_get_backlog_sorted():
    """Test backlog in rank order"""

def test_get_backlog_with_epics():
    """Test grouping backlog by epic"""
```

**CLI Interface:**
```bash
python get_backlog.py --board 123
python get_backlog.py --board 123 --filter "priority=High"
python get_backlog.py --board 123 --group-by epic
python get_backlog.py --board 123 --max-results 50
```

**Acceptance Criteria:**
- [ ] All 5 tests pass
- [ ] Shows backlog in rank order
- [ ] Supports filtering
- [ ] Optional epic grouping

**Commits:**
1. `test(jira-agile): add failing tests for get_backlog`
2. `feat(jira-agile): implement get_backlog.py (5/5 tests passing)`

---

### Phase 3 Completion

- [ ] **Phase 3 Summary:**
  - [ ] 2 scripts implemented (rank_issue, get_backlog)
  - [ ] 11 tests passing (63 total)
  - [ ] Coverage ≥ 85% for backlog-related code
  - [ ] SKILL.md updated with backlog examples
  - **Commit:** `docs(jira-agile): complete Phase 3 - Backlog Management`

---

## Phase 4: Story Points & Estimation

### Feature 4.1: Set Story Points

**Script:** `estimate_issue.py`

**JIRA API:**
- `PUT /rest/api/3/issue/{issueIdOrKey}` with story point field

**Test File:** `tests/test_estimate_issue.py`

**Test Cases:**
```python
def test_set_story_points_single():
    """Test setting story points on one issue"""

def test_set_story_points_multiple():
    """Test bulk setting story points"""

def test_set_story_points_fibonacci():
    """Test validation of Fibonacci sequence (1,2,3,5,8,13...)"""

def test_set_story_points_custom_scale():
    """Test custom point scale (e.g., t-shirt sizes)"""

def test_clear_story_points():
    """Test removing story point estimate"""

def test_estimate_by_jql():
    """Test bulk estimating from JQL query"""
```

**CLI Interface:**
```bash
python estimate_issue.py PROJ-1 --points 5
python estimate_issue.py PROJ-1,PROJ-2,PROJ-3 --points 3
python estimate_issue.py PROJ-1 --points 0  # Clear estimate
python estimate_issue.py --jql "sprint=456 AND type=Story" --points 2
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Supports single and bulk updates
- [ ] Validates point scale
- [ ] JQL query support

**Commits:**
1. `test(jira-agile): add failing tests for estimate_issue`
2. `feat(jira-agile): implement estimate_issue.py (6/6 tests passing)`

---

### Feature 4.2: Get Estimation Summary

**Script:** `get_estimates.py`

**JIRA API:**
- `GET /rest/api/3/search` with story point aggregation

**Test File:** `tests/test_get_estimates.py`

**Test Cases:**
```python
def test_get_estimates_for_sprint():
    """Test summing story points in sprint"""

def test_get_estimates_for_epic():
    """Test summing story points in epic"""

def test_get_estimates_by_assignee():
    """Test grouping estimates by assignee"""

def test_get_estimates_by_status():
    """Test grouping estimates by status (done vs todo)"""
```

**CLI Interface:**
```bash
python get_estimates.py --sprint 456
python get_estimates.py --epic PROJ-100
python get_estimates.py --sprint 456 --group-by assignee
python get_estimates.py --sprint 456 --group-by status
```

**Output Example:**
```
Sprint 42 Estimates:
Total: 55 points
Done: 32 points (58%)
In Progress: 15 points (27%)
To Do: 8 points (15%)

By Assignee:
  Alice: 20 points (36%)
  Bob: 18 points (33%)
  Charlie: 17 points (31%)
```

**Acceptance Criteria:**
- [ ] All 4 tests pass
- [ ] Sums story points correctly
- [ ] Groups by various dimensions
- [ ] Shows percentages

**Commits:**
1. `test(jira-agile): add failing tests for get_estimates`
2. `feat(jira-agile): implement get_estimates.py (4/4 tests passing)`

---

### Phase 4 Completion

- [ ] **Phase 4 Summary:**
  - [ ] 2 scripts implemented (estimate_issue, get_estimates)
  - [ ] 10 tests passing (73 total)
  - [ ] Coverage ≥ 85% for estimation code
  - [ ] SKILL.md updated with estimation examples
  - **Commit:** `docs(jira-agile): complete Phase 4 - Story Points & Estimation`

---

## Integration & Polish

### Integration Tasks

- [ ] **Integration 1:** Update jira-issue scripts
  - [ ] `create_issue.py`: Add `--epic` flag to create issue in epic
  - [ ] `create_issue.py`: Add `--sprint` flag to create issue in sprint
  - [ ] `create_issue.py`: Add `--story-points` flag
  - [ ] `get_issue.py`: Show epic link, sprint, story points in output
  - [ ] `get_issue.py`: Show subtasks if issue is parent
  - **Commit:** `feat(jira-issue): integrate Agile fields (epic, sprint, story points)`

- [ ] **Integration 2:** Update jira-lifecycle scripts
  - [ ] `transition_issue.py`: Option to move to sprint on transition
  - **Commit:** `feat(jira-lifecycle): add sprint integration to transitions`

- [ ] **Integration 3:** Update jira-search scripts
  - [ ] Update search output to show sprint and epic columns
  - [ ] Add sprint and epic to default fields
  - **Commit:** `feat(jira-search): show Agile fields in search results`

### Documentation Updates

- [ ] **Docs 1:** Create comprehensive SKILL.md for jira-agile
  - [ ] "When to use this skill" section
  - [ ] "What this skill does" section
  - [ ] "Available scripts" with descriptions
  - [ ] "Examples" section with realistic workflows
  - [ ] Configuration notes
  - [ ] Related skills section
  - **Commit:** `docs(jira-agile): create comprehensive SKILL.md`

- [ ] **Docs 2:** Update CLAUDE.md
  - [ ] Add jira-agile to project overview
  - [ ] Add agile patterns to common patterns section
  - [ ] Document story point custom field configuration
  - **Commit:** `docs: update CLAUDE.md with jira-agile skill`

- [ ] **Docs 3:** Update GAP_ANALYSIS.md
  - [ ] Mark Agile/Scrum gap as completed
  - [ ] Update coverage metrics
  - [ ] Move to implemented features section
  - **Commit:** `docs: update GAP_ANALYSIS.md - Agile features complete`

### Testing & Quality

- [ ] **Quality 1:** Integration tests
  - [ ] End-to-end workflow test: Create epic → Add issues → Create sprint → Move to sprint
  - [ ] End-to-end workflow test: Create sprint → Add issues → Set estimates → Start → Close
  - **Commit:** `test(jira-agile): add end-to-end integration tests`

- [ ] **Quality 2:** Coverage validation
  - [ ] Run `pytest --cov=.claude/skills/jira-agile --cov-report=html`
  - [ ] Verify ≥85% coverage for all modules
  - [ ] Add coverage badge to README if applicable
  - **Commit:** `test(jira-agile): validate 85%+ test coverage`

- [ ] **Quality 3:** Error handling review
  - [ ] Ensure all API errors handled gracefully
  - [ ] Add troubleshooting hints to error messages
  - [ ] Test all error paths
  - **Commit:** `fix(jira-agile): improve error handling and messages`

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 73+ unit tests passing
- [ ] 2+ integration tests passing
- [ ] 85%+ code coverage

**Scripts:**
- [ ] 12 new scripts implemented
- [ ] All scripts have `--help`
- [ ] All scripts support `--profile`
- [ ] All mutation scripts have `--dry-run`

**Documentation:**
- [ ] SKILL.md complete with examples
- [ ] CLAUDE.md updated
- [ ] GAP_ANALYSIS.md updated
- [ ] All scripts have docstrings

**Integration:**
- [ ] 3 existing skills updated (jira-issue, jira-lifecycle, jira-search)
- [ ] No breaking changes to existing functionality

### Progress Tracking

**Test Status:** 0/73 passing (0%)

**Phase Status:**
- [ ] Phase 1: Epics (0/4 scripts, 0/28 tests)
- [ ] Phase 2: Sprints (0/4 scripts, 0/24 tests)
- [ ] Phase 3: Backlog (0/2 scripts, 0/11 tests)
- [ ] Phase 4: Story Points (0/2 scripts, 0/10 tests)
- [ ] Integration (0/3 updates)
- [ ] Documentation (0/3 docs)
- [ ] Quality (0/3 tasks)

---

## Commit Strategy

### Commit Types

**test:** Adding or updating tests
- `test(jira-agile): add failing tests for create_epic`

**feat:** Implementing features
- `feat(jira-agile): implement create_epic.py (7/7 tests passing)`

**docs:** Documentation updates
- `docs(jira-agile): add epic examples to SKILL.md`

**refactor:** Code improvements without changing behavior
- `refactor(jira-agile): extract epic field mapping to helper`

**fix:** Bug fixes
- `fix(jira-agile): handle missing story point field gracefully`

### Commit Cadence

**After each test suite passes:**
```bash
git add .
git commit -m "feat(jira-agile): implement create_epic.py (7/7 tests passing)"
```

**After documentation updates:**
```bash
git add .claude/skills/jira-agile/SKILL.md
git commit -m "docs(jira-agile): add epic creation examples"
```

**After phase completion:**
```bash
git add AGILE_IMPLEMENTATION_PLAN.md
git commit -m "docs(jira-agile): complete Phase 1 - Epic Management"
```

---

## Development Workflow

### For Each Feature

1. **Write tests first** (TDD red phase)
   ```bash
   # Create test file with failing tests
   pytest tests/test_create_epic.py  # All fail
   git add tests/test_create_epic.py
   git commit -m "test(jira-agile): add failing tests for create_epic"
   ```

2. **Implement minimum code** (TDD green phase)
   ```bash
   # Write script until tests pass
   pytest tests/test_create_epic.py  # 1/7 pass
   pytest tests/test_create_epic.py  # 3/7 pass
   pytest tests/test_create_epic.py  # 7/7 pass ✓
   git add .claude/skills/jira-agile/scripts/create_epic.py
   git commit -m "feat(jira-agile): implement create_epic.py (7/7 tests passing)"
   ```

3. **Refactor** (TDD refactor phase)
   ```bash
   # Improve code while keeping tests green
   pytest tests/test_create_epic.py  # 7/7 pass ✓
   git add .claude/skills/jira-agile/scripts/create_epic.py
   git commit -m "refactor(jira-agile): extract epic validation logic"
   ```

4. **Document**
   ```bash
   # Update SKILL.md
   git add .claude/skills/jira-agile/SKILL.md
   git commit -m "docs(jira-agile): add create_epic examples"
   ```

5. **Update plan**
   ```bash
   # Check off completed items in this plan
   git add AGILE_IMPLEMENTATION_PLAN.md
   git commit -m "docs: mark create_epic as complete in plan"
   ```

---

## Next Steps

1. **Start with setup:**
   ```bash
   cd .claude/skills
   mkdir -p jira-agile/tests jira-agile/scripts jira-agile/references
   pip install pytest pytest-cov responses
   ```

2. **Create initial structure:**
   - `jira-agile/SKILL.md` (template)
   - `jira-agile/tests/conftest.py` (fixtures)
   - `jira-agile/tests/__init__.py`

3. **Begin Phase 1:**
   - Start with `tests/test_create_epic.py`
   - Write 7 failing tests
   - Commit
   - Implement `scripts/create_epic.py`
   - Run tests until all pass
   - Commit

---

**Plan Version:** 1.0
**Created:** 2025-01-15
**Last Updated:** 2025-01-15
**Status:** Ready to begin
