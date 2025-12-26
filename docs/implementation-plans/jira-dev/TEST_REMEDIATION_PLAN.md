# Test Remediation Plan: jira-dev Skill

**Created:** 2025-12-26
**Status:** Draft
**Test Files Reviewed:** 7
**Total Issues Identified:** ~65

---

## Executive Summary

This plan addresses test quality issues discovered during a comprehensive review of the `jira-dev` skill test suite. The jira-dev skill provides developer workflow integration (Git branch names, commit parsing, PR descriptions) and has both unit tests and live integration tests.

**Issue Counts by Category:**

| Category | Count |
|----------|-------|
| Missing pytest markers | 11 classes |
| Missing pytest marker registration | 1 (conftest.py) |
| Weak assertions | 6 instances |
| Fixture mutations (need deepcopy) | 2 fixtures |
| Missing error handling tests | 20+ tests needed |
| API signature mismatches | 8 instances |
| Unused imports | 4 instances |
| Missing CLI tests | 6 scripts |

**Estimated Effort:**
- Phase 1 (Critical): 2-3 hours
- Phase 2 (High Priority): 3-4 hours
- Phase 3 (Medium Priority): 4-6 hours
- Phase 4 (Low Priority): 1-2 hours

---

## Phase 1: Critical Issues (Must Fix)

### 1.1 Missing pytest Marker Registration

**Impact:** pytest warnings, inconsistent test selection
**File:** `tests/conftest.py`
**Line:** Missing entirely

The conftest.py does not register custom markers, which causes pytest warnings and prevents proper test filtering.

**Current (missing):**
```python
# No pytest_configure function
```

**Add at top of conftest.py (after imports, line 8):**

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "dev: mark test as jira-dev skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
```

---

### 1.2 Missing pytest Markers on Test Classes

**Impact:** Inconsistent test categorization, cannot filter by skill
**Files Affected:** 2 unit test files, 1 live integration file

| File | Class | Line |
|------|-------|------|
| `tests/test_git_integration.py` | `TestCreateBranchName` | 25 |
| `tests/test_git_integration.py` | `TestParseCommitIssues` | 174 |
| `tests/test_git_integration.py` | `TestLinkCommit` | 259 |
| `tests/test_git_integration.py` | `TestGetIssueCommits` | 350 |
| `tests/test_pr_management.py` | `TestLinkPR` | 23 |
| `tests/test_pr_management.py` | `TestCreatePRDescription` | 124 |
| `tests/live_integration/test_dev_workflow.py` | `TestCreateBranchName` | 22 |
| `tests/live_integration/test_dev_workflow.py` | `TestLinkCommit` | 95 |
| `tests/live_integration/test_dev_workflow.py` | `TestLinkPR` | 149 |
| `tests/live_integration/test_dev_workflow.py` | `TestCreatePRDescription` | 211 |
| `tests/live_integration/test_dev_workflow.py` | `TestSanitizeForBranch` | 277 |
| `tests/live_integration/test_dev_workflow.py` | `TestExtractAcceptanceCriteria` | 297 |

**Remediation for unit tests:**

```python
# tests/test_git_integration.py, line 25
@pytest.mark.dev
@pytest.mark.unit
class TestCreateBranchName:
    """Tests for create_branch_name functionality."""
```

**Remediation for live integration tests:**

```python
# tests/live_integration/test_dev_workflow.py, line 22
@pytest.mark.dev
@pytest.mark.integration
class TestCreateBranchName:
    """Tests for branch name generation from JIRA issues."""
```

---

### 1.3 API Signature Mismatches Between Unit and Live Tests

**Impact:** Tests may pass but not accurately reflect actual API behavior
**Severity:** High - tests may be testing non-existent parameters

#### 1.3.1 create_branch_name.py

**Actual function signature (scripts/create_branch_name.py:111-116):**
```python
def create_branch_name(
    issue_key: str,
    prefix: Optional[str] = None,
    auto_prefix: bool = False,
    profile: Optional[str] = None
) -> str:  # Returns string, not dict
```

**Unit test usage (test_git_integration.py:34-35):**
```python
with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
    result = create_branch_name('PROJ-123')
# Expects: string return value
assert result.startswith('feature/')  # CORRECT - string
```

**Live integration test usage (test_dev_workflow.py:27-29):**
```python
result = create_branch_name(
    issue_key=test_issue['key'],
    client=jira_client  # PROBLEM: 'client' parameter doesn't exist!
)
# Expects: dict return value
assert result is not None
assert 'branch_name' in result  # WRONG - function returns string, not dict
```

**Issues identified:**
- Live tests pass `client=jira_client` but function has no `client` parameter
- Live tests expect dict with `branch_name` key but function returns plain string
- Live tests expect `issue_key`, `issue_type` keys that don't exist in return

**Remediation:**

Option A: Update live tests to match actual API:
```python
# test_dev_workflow.py TestCreateBranchName
def test_create_branch_name_task(self, jira_client, test_project, test_issue, jira_profile):
    """Test creating branch name from a task."""
    result = create_branch_name(
        issue_key=test_issue['key'],
        profile=jira_profile  # Use profile, not client
    )

    assert result is not None
    assert isinstance(result, str)  # Returns string
    assert test_issue['key'].lower() in result.lower()
```

Option B: Update script to accept `client` parameter for testing (preferred for testability):
```python
# scripts/create_branch_name.py - update function signature
def create_branch_name(
    issue_key: str,
    prefix: Optional[str] = None,
    auto_prefix: bool = False,
    profile: Optional[str] = None,
    client: Optional[Any] = None  # Add for testing
) -> Dict[str, Any]:  # Change return type
```

---

#### 1.3.2 link_commit.py

**Actual function signature (scripts/link_commit.py:142-150):**
```python
def link_commit(
    issue_key: str,
    commit_sha: str,  # Parameter is 'commit_sha'
    message: Optional[str] = None,
    repo_url: Optional[str] = None,  # Parameter is 'repo_url'
    author: Optional[str] = None,
    branch: Optional[str] = None,
    profile: Optional[str] = None
) -> Dict[str, Any]:
```

**Unit test usage (test_git_integration.py:268-273):**
```python
with patch('link_commit.get_jira_client', return_value=mock_jira_client):
    result = link_commit(
        issue_key='PROJ-123',
        commit_sha='abc123def456',  # CORRECT
        message='Fix login bug'
    )
```

**Live integration test usage (test_dev_workflow.py:103-109):**
```python
result = link_commit(
    issue_key=test_issue['key'],
    commit=commit_sha,  # WRONG: should be 'commit_sha'
    repo=repo_url,      # WRONG: should be 'repo_url'
    message='Test commit message',
    client=jira_client  # WRONG: no 'client' parameter
)
```

**Remediation (test_dev_workflow.py:103-109):**
```python
result = link_commit(
    issue_key=test_issue['key'],
    commit_sha=commit_sha,  # Fixed: use correct parameter name
    repo_url=repo_url,      # Fixed: use correct parameter name
    message='Test commit message',
    profile=jira_profile    # Fixed: use profile instead of client
)
```

---

#### 1.3.3 link_pr.py

**Actual function signature (scripts/link_pr.py:145-152):**
```python
def link_pr(
    issue_key: str,
    pr_url: str,
    title: Optional[str] = None,
    status: Optional[str] = None,
    author: Optional[str] = None,
    profile: Optional[str] = None
) -> Dict[str, Any]:
```

**Live integration test usage (test_dev_workflow.py:156-160):**
```python
result = link_pr(
    issue_key=test_issue['key'],
    pr_url=pr_url,
    client=jira_client  # WRONG: no 'client' parameter
)
```

**Remediation:**
```python
result = link_pr(
    issue_key=test_issue['key'],
    pr_url=pr_url,
    profile=jira_profile  # Fixed: use profile
)
```

---

#### 1.3.4 create_pr_description.py

**Actual function signature (scripts/create_pr_description.py:98-104):**
```python
def create_pr_description(
    issue_key: str,
    include_checklist: bool = False,
    include_labels: bool = False,
    include_components: bool = False,
    profile: Optional[str] = None
) -> str:  # Returns string, not dict
```

**Live integration test usage (test_dev_workflow.py:216-220):**
```python
result = create_pr_description(
    issue_key=test_issue['key'],
    client=jira_client,    # WRONG: no 'client' parameter
    profile=jira_profile   # OK: profile exists
)
# Test expects dict:
assert 'markdown' in result  # WRONG: returns string
```

**Remediation:**
```python
def test_create_pr_description_basic(self, jira_client, test_project, test_issue, jira_profile):
    """Test basic PR description generation."""
    result = create_pr_description(
        issue_key=test_issue['key'],
        profile=jira_profile  # Remove client parameter
    )

    assert result is not None
    assert isinstance(result, str)  # Returns markdown string
    assert test_issue['key'] in result  # Issue key should be in markdown
```

---

### 1.4 Weak Assertions That Always Pass

**Impact:** Tests pass even when functionality is broken
**Files Affected:** 2

| File | Line | Current Assertion | Issue | Fix |
|------|------|-------------------|-------|-----|
| `test_git_integration.py` | 362 | `assert len(result) >= 1` | Could pass with 0 if `>=` used | `assert len(result) > 0` |
| `test_git_integration.py` | 363 | `assert 'id' in result[0] or 'sha' in result[0]` | Always True if either | Test for specific key |
| `test_git_integration.py` | 389 | `assert len(result) >= 1` | Could hide failures | `assert len(result) > 0` |
| `test_pr_management.py` | 163-164 | `'- [ ]' in result or '- []' in result` | Too permissive | Use exact format |
| `test_pr_management.py` | 175-176 | `'##' in result or '#' in result` | Too permissive | Verify specific header |
| `test_pr_management.py` | 187-188 | `'mobile' in result.lower() or 'ui' in result.lower()` | Only needs one | Verify both or specific |

**Remediation Examples:**

```python
# test_git_integration.py line 362-363
# Before (weak):
assert len(result) >= 1
assert 'id' in result[0] or 'sha' in result[0]

# After (strong):
assert len(result) > 0, "Expected at least one commit"
assert 'id' in result[0], "Commit should have 'id' field"
# or if sha is the canonical field:
assert 'sha' in result[0], "Commit should have 'sha' field"


# test_pr_management.py line 163-164
# Before (weak):
assert '- [ ]' in result or '- []' in result

# After (strong):
assert '- [ ]' in result, "Checklist should use '- [ ]' format"


# test_pr_management.py line 175-176
# Before (weak):
assert '##' in result or '#' in result

# After (strong):
assert '## Summary' in result, "PR description should have Summary header"
assert '## JIRA Issue' in result, "PR description should have JIRA Issue header"
```

---

## Phase 2: High Priority Issues

### 2.1 Missing Error Handling Tests

**Impact:** Error scenarios untested, poor user experience on failures
**Scripts Affected:** 6
**Tests Needed:** ~20

All scripts handle errors but unit tests don't verify error handling behavior.

#### 2.1.1 Authentication Error Tests Needed

| Script | Test File | Missing Test |
|--------|-----------|--------------|
| `create_branch_name.py` | `test_git_integration.py` | `test_create_branch_name_auth_error` |
| `link_commit.py` | `test_git_integration.py` | `test_link_commit_auth_error` |
| `get_issue_commits.py` | `test_git_integration.py` | `test_get_commits_auth_error` |
| `link_pr.py` | `test_pr_management.py` | `test_link_pr_auth_error` |
| `create_pr_description.py` | `test_pr_management.py` | `test_create_pr_description_auth_error` |

**Remediation Template:**

```python
# Add to test_git_integration.py TestCreateBranchName class
def test_create_branch_name_auth_error(self, mock_jira_client):
    """Test handling of 401 unauthorized."""
    from error_handler import AuthenticationError

    mock_jira_client.get_issue.side_effect = AuthenticationError("Invalid token")

    with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
        with pytest.raises(AuthenticationError):
            create_branch_name('PROJ-123')
```

---

#### 2.1.2 Rate Limit (429) Tests Needed

| Script | Test File | Missing Test |
|--------|-----------|--------------|
| `create_branch_name.py` | `test_git_integration.py` | `test_create_branch_name_rate_limit` |
| `link_commit.py` | `test_git_integration.py` | `test_link_commit_rate_limit` |
| `get_issue_commits.py` | `test_git_integration.py` | `test_get_commits_rate_limit` |
| `link_pr.py` | `test_pr_management.py` | `test_link_pr_rate_limit` |

**Remediation Template:**

```python
def test_link_commit_rate_limit(self, mock_jira_client):
    """Test handling of 429 rate limit."""
    from error_handler import JiraError

    mock_jira_client.post.side_effect = JiraError(
        "Rate limit exceeded", status_code=429
    )

    with patch('link_commit.get_jira_client', return_value=mock_jira_client):
        with pytest.raises(JiraError) as exc_info:
            link_commit(
                issue_key='PROJ-123',
                commit_sha='abc123',
                message='Test'
            )
        assert exc_info.value.status_code == 429
```

---

#### 2.1.3 Not Found (404) Tests Needed

| Script | Test File | Missing Test |
|--------|-----------|--------------|
| `create_branch_name.py` | `test_git_integration.py` | `test_create_branch_name_issue_not_found` |
| `link_commit.py` | `test_git_integration.py` | `test_link_commit_issue_not_found` |
| `create_pr_description.py` | `test_pr_management.py` | `test_create_pr_description_issue_not_found` |

**Remediation Template:**

```python
def test_create_branch_name_issue_not_found(self, mock_jira_client):
    """Test handling of issue not found."""
    from error_handler import NotFoundError

    mock_jira_client.get_issue.side_effect = NotFoundError("Issue", "PROJ-999")

    with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
        with pytest.raises(NotFoundError):
            create_branch_name('PROJ-999')
```

---

#### 2.1.4 Permission Denied (403) Tests Needed

| Script | Test File | Missing Test |
|--------|-----------|--------------|
| `link_commit.py` | `test_git_integration.py` | `test_link_commit_permission_denied` |
| `link_pr.py` | `test_pr_management.py` | `test_link_pr_permission_denied` |

---

#### 2.1.5 Server Error (500) Tests Needed

| Script | Test File | Missing Test |
|--------|-----------|--------------|
| All scripts | Both test files | `test_*_server_error` |

**Remediation Template:**

```python
def test_link_commit_server_error(self, mock_jira_client):
    """Test handling of 500 server error."""
    from error_handler import JiraError

    mock_jira_client.post.side_effect = JiraError(
        "Internal server error", status_code=500
    )

    with patch('link_commit.get_jira_client', return_value=mock_jira_client):
        with pytest.raises(JiraError) as exc_info:
            link_commit(
                issue_key='PROJ-123',
                commit_sha='abc123'
            )
        assert exc_info.value.status_code == 500
```

---

### 2.2 Missing Validation Tests

**Impact:** Invalid input not properly rejected

| Script | Test File | Missing Test | Input to Test |
|--------|-----------|--------------|---------------|
| `link_pr.py` | `test_pr_management.py` | `test_parse_invalid_pr_url` | Malformed URLs |
| `link_pr.py` | `test_pr_management.py` | `test_link_pr_empty_url` | Empty string |
| `create_branch_name.py` | `test_git_integration.py` | `test_invalid_issue_key` | Invalid format |
| `parse_commit_issues.py` | `test_git_integration.py` | `test_parse_null_message` | None input |

**Remediation Template:**

```python
def test_parse_invalid_pr_url(self):
    """Test parsing invalid PR URL raises ValidationError."""
    from link_pr import parse_pr_url
    from error_handler import ValidationError

    with pytest.raises(ValidationError):
        parse_pr_url('not-a-valid-url')

    with pytest.raises(ValidationError):
        parse_pr_url('https://unknown-host.com/repo/pull/123')


def test_link_pr_empty_url(self, mock_jira_client):
    """Test empty PR URL raises ValidationError."""
    from link_pr import link_pr
    from error_handler import ValidationError

    with pytest.raises(ValidationError):
        link_pr(issue_key='PROJ-123', pr_url='')
```

---

## Phase 3: Medium Priority Issues

### 3.1 Fixture Mutation Issues

**Impact:** Potential test pollution between tests
**Files Affected:** 1 (`tests/conftest.py`)

| Fixture | Line | Issue |
|---------|------|-------|
| `sample_issue` | 28-78 | Returns dict that could be mutated by tests |
| `sample_dev_info` | 124-161 | Complex nested structure easily mutated |

**Remediation:**

```python
# conftest.py - Update fixture to use deepcopy

import copy

@pytest.fixture
def sample_issue():
    """Sample JIRA issue data."""
    _sample_issue = {
        'key': 'PROJ-123',
        'id': '10001',
        # ... rest of fixture data
    }
    return copy.deepcopy(_sample_issue)


@pytest.fixture
def sample_dev_info():
    """Sample development information from JIRA."""
    _sample_dev_info = {
        'detail': [
            # ... rest of fixture data
        ]
    }
    return copy.deepcopy(_sample_dev_info)
```

---

### 3.2 Missing CLI Tests

**Impact:** CLI interface untested, argument parsing could break unnoticed
**Scripts Affected:** 6

| Script | Functions to Test |
|--------|-------------------|
| `create_branch_name.py` | `main()` with various args |
| `link_commit.py` | `main()` with --commit, --repo, --from-message |
| `link_pr.py` | `main()` with --pr, --status |
| `create_pr_description.py` | `main()` with --include-checklist, --output |
| `get_issue_commits.py` | `main()` with --detailed, --repo |
| `parse_commit_issues.py` | `main()` with --from-stdin, --project |

**Remediation Template:**

```python
# Add new test class to test_git_integration.py

class TestCreateBranchNameCLI:
    """Tests for create_branch_name CLI interface."""

    def test_cli_basic(self, mock_jira_client, sample_issue, capsys):
        """Test CLI with issue key argument."""
        mock_jira_client.get_issue.return_value = sample_issue

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['create_branch_name.py', 'PROJ-123']):
                from create_branch_name import main
                try:
                    main()
                except SystemExit:
                    pass

        captured = capsys.readouterr()
        assert 'feature/' in captured.out
        assert 'proj-123' in captured.out.lower()

    def test_cli_auto_prefix(self, mock_jira_client, sample_issue, capsys):
        """Test CLI with --auto-prefix."""
        mock_jira_client.get_issue.return_value = sample_issue

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['create_branch_name.py', 'PROJ-123', '--auto-prefix']):
                from create_branch_name import main
                try:
                    main()
                except SystemExit:
                    pass

        captured = capsys.readouterr()
        assert 'bugfix/' in captured.out  # sample_issue is Bug type

    def test_cli_json_output(self, mock_jira_client, sample_issue, capsys):
        """Test CLI with --output json."""
        mock_jira_client.get_issue.return_value = sample_issue

        with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
            with patch('sys.argv', ['create_branch_name.py', 'PROJ-123', '--output', 'json']):
                from create_branch_name import main
                try:
                    main()
                except SystemExit:
                    pass

        captured = capsys.readouterr()
        import json
        data = json.loads(captured.out)
        assert 'branch_name' in data
        assert 'issue_key' in data
```

---

### 3.3 Missing Edge Case Tests

| Category | Test File | Missing Test | Edge Case |
|----------|-----------|--------------|-----------|
| Empty input | `test_git_integration.py` | `test_sanitize_empty_string` | `sanitize_for_branch("")` |
| Unicode | `test_git_integration.py` | `test_sanitize_unicode` | `sanitize_for_branch("Fix: add feature")` |
| Very long | `test_git_integration.py` | `test_branch_name_very_long_summary` | 500+ char summary |
| Special project | `test_git_integration.py` | `test_parse_numeric_project` | `A1-123` |
| Multiple PRs | `test_pr_management.py` | `test_link_multiple_prs` | Link 3+ PRs |
| Empty description | `test_pr_management.py` | `test_pr_description_no_description` | Issue with null description |

**Remediation Examples:**

```python
# test_git_integration.py TestParseCommitIssues
def test_parse_unicode_message(self):
    """Test handling unicode characters in commit message."""
    from parse_commit_issues import parse_issue_keys

    # Unicode in message but issue key still valid
    result = parse_issue_keys("PROJ-123: Fix bug with special chars")
    assert result == ["PROJ-123"]


# test_git_integration.py TestCreateBranchName
def test_sanitize_unicode(self):
    """Test sanitizing unicode characters."""
    from create_branch_name import sanitize_for_branch

    result = sanitize_for_branch("Add feature")  # em-dash
    assert result == "add-feature"  # Should collapse to hyphen


def test_branch_name_very_long_summary(self, mock_jira_client):
    """Test branch name truncation for very long summaries."""
    from create_branch_name import create_branch_name, MAX_BRANCH_LENGTH

    very_long_summary = "This is an extremely long summary " * 20
    mock_jira_client.get_issue.return_value = {
        'key': 'PROJ-123',
        'fields': {
            'summary': very_long_summary,
            'issuetype': {'name': 'Story'}
        }
    }

    with patch('create_branch_name.get_jira_client', return_value=mock_jira_client):
        result = create_branch_name('PROJ-123')

    assert len(result) <= MAX_BRANCH_LENGTH
    assert not result.endswith('-')  # Should not end with hyphen
```

---

### 3.4 Live Integration Test conftest.py Improvements

**File:** `tests/live_integration/conftest.py`
**Issues:**

1. **Line 23-42:** No marker registration for integration tests
2. **Line 71:** test_project fixture could leak if cleanup fails

**Remediation:**

```python
# Add after imports (line 21)
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "dev: mark test as jira-dev skill test")
    config.addinivalue_line("markers", "integration: mark test as live integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# Update cleanup to be more robust (line 116-120)
if not keep_project and project_data.get('is_temporary', True):
    print(f"\n{'='*60}")
    print(f"Cleaning up test project: {project_key}")
    print(f"{'='*60}")
    try:
        cleanup_project(jira_client, project_key)
    except Exception as e:
        print(f"Warning: Cleanup failed for {project_key}: {e}")
        # Don't raise - test results are more important than cleanup
```

---

## Phase 4: Low Priority Issues

### 4.1 Remove Unused Imports

**Impact:** Code hygiene
**Files Affected:** 3

| File | Line | Unused Import |
|------|------|---------------|
| `tests/conftest.py` | 7 | `MagicMock` (imported but fixtures use `Mock`) |
| `tests/test_git_integration.py` | 14 | `MagicMock` (not used) |
| `tests/test_pr_management.py` | 12 | `MagicMock` (not used) |
| `tests/live_integration/conftest.py` | 12 | `Dict, Any` from typing (used) - OK |

**Remediation:**

```python
# tests/conftest.py line 7
# Before:
from unittest.mock import Mock, patch, MagicMock

# After:
from unittest.mock import Mock, patch


# tests/test_git_integration.py line 14
# Before:
from unittest.mock import Mock, patch, MagicMock

# After:
from unittest.mock import Mock, patch


# tests/test_pr_management.py line 12
# Before:
from unittest.mock import Mock, patch, MagicMock

# After:
from unittest.mock import Mock, patch
```

---

### 4.2 Redundant Patches in Tests

**Impact:** Unnecessary complexity
**Files Affected:** Multiple tests

Several tests patch `get_jira_client` but then pass `mock_jira_client` directly to functions. This is redundant.

**Example (test_git_integration.py:268-276):**

```python
# Before (redundant):
def test_link_commit_basic(self, mock_jira_client):
    mock_jira_client.post.return_value = {'id': '10001'}

    with patch('link_commit.get_jira_client', return_value=mock_jira_client):
        result = link_commit(
            issue_key='PROJ-123',
            commit_sha='abc123def456',
            message='Fix login bug'
        )
    # The patch is needed since link_commit calls get_jira_client internally
```

This pattern is actually correct because `link_commit()` internally calls `get_jira_client()`. Keep the patches.

---

### 4.3 Inconsistent Test Naming

**Impact:** Code readability
**Pattern to standardize:**

```python
# Inconsistent:
def test_create_branch_name_basic(...)       # uses 'basic'
def test_link_commit_github(...)              # uses provider name
def test_create_pr_description_basic(...)     # uses 'basic'

# Standardize to use descriptive names:
def test_create_branch_name_default_prefix(...)
def test_create_branch_name_with_custom_prefix(...)
def test_create_branch_name_auto_prefix_bug(...)
```

---

### 4.4 Add Test Count Verification

**Impact:** Catch accidental test deletion

**Add to tests/__init__.py:**

```python
# tests/__init__.py
"""
jira-dev tests package.

Expected test counts:
- test_git_integration.py: 21 tests
- test_pr_management.py: 12 tests
- live_integration/test_dev_workflow.py: 25 tests

Total: 58 tests
"""
```

---

## Implementation Checklist

### Phase 1 Checklist (Critical)

- [ ] Add `pytest_configure` to `tests/conftest.py` (line 8)
- [ ] Add `@pytest.mark.dev` and `@pytest.mark.unit` to 6 classes in unit tests
- [ ] Add `@pytest.mark.dev` and `@pytest.mark.integration` to 6 classes in live tests
- [ ] Fix API signature mismatch in `test_dev_workflow.py` `create_branch_name` tests
- [ ] Fix API signature mismatch in `test_dev_workflow.py` `link_commit` tests
- [ ] Fix API signature mismatch in `test_dev_workflow.py` `link_pr` tests
- [ ] Fix API signature mismatch in `test_dev_workflow.py` `create_pr_description` tests
- [ ] Fix 6 weak assertions (use specific checks)

### Phase 2 Checklist (High Priority)

- [ ] Add authentication error tests (5 tests)
- [ ] Add rate limit (429) tests (4 tests)
- [ ] Add not found (404) tests (3 tests)
- [ ] Add permission denied (403) tests (2 tests)
- [ ] Add server error (500) tests (6 tests)
- [ ] Add validation tests for invalid inputs (4 tests)

### Phase 3 Checklist (Medium Priority)

- [ ] Add deepcopy to `sample_issue` fixture
- [ ] Add deepcopy to `sample_dev_info` fixture
- [ ] Add CLI tests for `create_branch_name.py` (3+ tests)
- [ ] Add CLI tests for `link_commit.py` (3+ tests)
- [ ] Add CLI tests for `link_pr.py` (2+ tests)
- [ ] Add CLI tests for `create_pr_description.py` (3+ tests)
- [ ] Add CLI tests for `get_issue_commits.py` (2+ tests)
- [ ] Add CLI tests for `parse_commit_issues.py` (3+ tests)
- [ ] Add edge case tests (6+ tests)
- [ ] Add `pytest_configure` to `tests/live_integration/conftest.py`
- [ ] Improve cleanup error handling in live integration

### Phase 4 Checklist (Low Priority)

- [ ] Remove unused `MagicMock` import from `tests/conftest.py`
- [ ] Remove unused `MagicMock` import from `tests/test_git_integration.py`
- [ ] Remove unused `MagicMock` import from `tests/test_pr_management.py`
- [ ] Standardize test naming conventions
- [ ] Add test count verification

---

## Verification Commands

```bash
# Run all jira-dev tests
pytest .claude/skills/jira-dev/tests/ -v

# Run only unit tests
pytest .claude/skills/jira-dev/tests/ -v -m "unit and dev"

# Run only integration tests (requires live JIRA)
pytest .claude/skills/jira-dev/tests/live_integration/ --profile development -v -m "integration and dev"

# Check for test count
pytest .claude/skills/jira-dev/tests/ --collect-only | grep "test session starts" -A 5

# Verify no unused imports (requires pylint)
pylint .claude/skills/jira-dev/tests/ --disable=all --enable=unused-import

# Check assertion quality (manual review)
grep -rn "assert.*>= 0" .claude/skills/jira-dev/tests/
grep -rn "or len.*>= 0" .claude/skills/jira-dev/tests/
grep -rn "is not None or.*is None" .claude/skills/jira-dev/tests/

# Verify marker registration
pytest .claude/skills/jira-dev/tests/ --markers | grep -E "(dev|unit|integration)"
```

---

## Success Criteria

1. **All tests pass:** `pytest` exits with code 0
2. **No weak assertions:** grep commands return no results
3. **Consistent markers:** All test classes have `@pytest.mark.dev` and appropriate `unit`/`integration` marker
4. **No pytest warnings:** About unknown markers
5. **API signatures match:** Live integration tests use correct parameter names
6. **Error handling tested:** Each script has tests for 401, 404, 429, 500 errors
7. **CLI tested:** Each script's main() function has basic CLI tests
8. **Coverage maintained:** Test count >= 58

---

## Notes

- The most critical issues are the API signature mismatches in live integration tests (Phase 1.3) - these tests may not be testing what they claim to test
- Phase 1 should be completed before merging any changes
- Phase 2 error handling tests provide important coverage for production stability
- Phases 3-4 can be addressed incrementally
- Consider updating scripts to accept `client` parameter for better testability
