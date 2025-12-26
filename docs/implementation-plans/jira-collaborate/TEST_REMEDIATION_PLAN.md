# Test Remediation Plan: jira-collaborate Skill

**Created:** 2025-12-26
**Status:** Draft
**Test Files Reviewed:** 7
**Total Issues Identified:** ~45+

---

## Executive Summary

This plan addresses test quality issues discovered during a comprehensive review of the `jira-collaborate` skill test suite. The jira-collaborate skill has moderate test coverage but significant gaps in error handling, missing tests for 4 scripts, and no pytest markers on any test classes.

### Issue Summary

| Category | Count | Priority |
|----------|-------|----------|
| Missing pytest markers | 6 classes | Critical |
| Scripts with no tests | 4 scripts | Critical |
| Missing error handling tests | 6 files | High |
| Fixture mutations | 1 file | Medium |
| Unused imports | 6 files | Low |
| Missing CLI tests | 6+ files | Medium |

**Estimated Effort:**
- Phase 1 (Critical): 3-4 hours
- Phase 2 (High Priority): 4-6 hours
- Phase 3 (Medium Priority): 3-4 hours
- Phase 4 (Low Priority): 1-2 hours

---

## Phase 1: Critical Issues (Must Fix)

### 1.1 Missing pytest Marker Registration

**Impact:** pytest warnings, inconsistent test selection
**File:** `tests/conftest.py`

**Current state (lines 1-14):**
```python
"""
Pytest fixtures for jira-collaborate comment, notification, and activity tests.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_jira_client():
    """Create a mock JIRA client."""
    client = MagicMock()
    client.base_url = 'https://test.atlassian.net'
    return client
```

**Add at top of conftest.py (after imports):**

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "collaborate: mark test as collaborate skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
```

---

### 1.2 Missing pytest Markers on Test Classes

**Impact:** Inconsistent test categorization, cannot run tests by marker
**Files Affected:** 6 test files, 6 test classes

| File | Line | Class Name |
|------|------|------------|
| `tests/test_get_comments.py` | 14 | `TestGetComments` |
| `tests/test_update_comment.py` | 14 | `TestUpdateComment` |
| `tests/test_delete_comment.py` | 14 | `TestDeleteComment` |
| `tests/test_comment_visibility.py` | 14 | `TestCommentVisibility` |
| `tests/test_send_notification.py` | 14 | `TestSendNotification` |
| `tests/test_get_activity.py` | 14 | `TestGetActivity` |

**Remediation - Add to each test class:**

```python
# Before:
class TestGetComments:
    """Tests for getting comments on issues."""

# After:
@pytest.mark.collaborate
@pytest.mark.unit
class TestGetComments:
    """Tests for getting comments on issues."""
```

**Files requiring this change:**

| File | Lines to Add Before |
|------|---------------------|
| `test_get_comments.py` | Line 14 |
| `test_update_comment.py` | Line 14 |
| `test_delete_comment.py` | Line 14 |
| `test_comment_visibility.py` | Line 14 |
| `test_send_notification.py` | Line 14 |
| `test_get_activity.py` | Line 14 |

---

### 1.3 Scripts With No Tests (Critical Coverage Gap)

**Impact:** 4 out of 9 scripts have ZERO test coverage
**Scripts Affected:** 4

| Script | Functions | Estimated Tests Needed |
|--------|-----------|----------------------|
| `scripts/add_comment.py` | `add_comment()`, `add_comment_with_visibility()`, `main()` | 8-10 tests |
| `scripts/upload_attachment.py` | `upload_attachment()`, `main()` | 6-8 tests |
| `scripts/manage_watchers.py` | `list_watchers()`, `add_watcher()`, `remove_watcher()`, `main()` | 10-12 tests |
| `scripts/update_custom_fields.py` | `update_custom_fields()`, `main()` | 6-8 tests |

**Note:** `test_comment_visibility.py` tests `add_comment_with_visibility` but not the base `add_comment` function directly.

**Remediation - Create new test files:**

#### 1.3.1 Create `tests/test_add_comment.py`

```python
"""
Tests for add_comment.py - Add comments to issues.
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.collaborate
@pytest.mark.unit
class TestAddComment:
    """Tests for adding comments to issues."""

    @patch('add_comment.get_jira_client')
    def test_add_comment_text_format(self, mock_get_client, mock_jira_client, sample_comment):
        """Test adding comment with text format."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.add_comment.return_value = sample_comment

        from add_comment import add_comment

        result = add_comment('PROJ-123', 'Test comment', format_type='text', profile=None)

        assert result['id'] == '10001'
        mock_jira_client.add_comment.assert_called_once()
        call_args = mock_jira_client.add_comment.call_args
        assert call_args[0][0] == 'PROJ-123'
        # Should be ADF format
        assert call_args[0][1]['type'] == 'doc'

    @patch('add_comment.get_jira_client')
    def test_add_comment_markdown_format(self, mock_get_client, mock_jira_client, sample_comment):
        """Test adding comment with markdown format."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.add_comment.return_value = sample_comment

        from add_comment import add_comment

        result = add_comment('PROJ-123', '**bold** text', format_type='markdown', profile=None)

        assert result['id'] == '10001'
        call_args = mock_jira_client.add_comment.call_args
        assert call_args[0][1]['type'] == 'doc'

    @patch('add_comment.get_jira_client')
    def test_add_comment_adf_format(self, mock_get_client, mock_jira_client, sample_comment):
        """Test adding comment with raw ADF format."""
        import json
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.add_comment.return_value = sample_comment

        from add_comment import add_comment

        adf_body = json.dumps({
            'type': 'doc',
            'version': 1,
            'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Test'}]}]
        })

        result = add_comment('PROJ-123', adf_body, format_type='adf', profile=None)

        assert result['id'] == '10001'

    @patch('add_comment.get_jira_client')
    def test_add_comment_invalid_issue_key(self, mock_get_client, mock_jira_client):
        """Test error for invalid issue key."""
        from error_handler import ValidationError

        from add_comment import add_comment

        with pytest.raises(ValidationError):
            add_comment('invalid', 'Test comment', profile=None)

    @patch('add_comment.get_jira_client')
    def test_add_comment_issue_not_found(self, mock_get_client, mock_jira_client):
        """Test error when issue doesn't exist."""
        from error_handler import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.add_comment.side_effect = NotFoundError("Issue PROJ-999 not found")

        from add_comment import add_comment

        with pytest.raises(NotFoundError):
            add_comment('PROJ-999', 'Test comment', profile=None)
```

#### 1.3.2 Create `tests/test_upload_attachment.py`

```python
"""
Tests for upload_attachment.py - Upload attachments to issues.
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.collaborate
@pytest.mark.unit
class TestUploadAttachment:
    """Tests for uploading attachments."""

    @patch('upload_attachment.get_jira_client')
    def test_upload_attachment_success(self, mock_get_client, mock_jira_client, tmp_path):
        """Test successful attachment upload."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.upload_file.return_value = [
            {'id': '10001', 'filename': 'test.txt', 'size': 100}
        ]

        # Create temp file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        from upload_attachment import upload_attachment

        result = upload_attachment('PROJ-123', str(test_file), profile=None)

        assert result[0]['filename'] == 'test.txt'
        mock_jira_client.upload_file.assert_called_once()

    @patch('upload_attachment.get_jira_client')
    def test_upload_attachment_custom_name(self, mock_get_client, mock_jira_client, tmp_path):
        """Test upload with custom filename."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.upload_file.return_value = [
            {'id': '10001', 'filename': 'custom_name.txt', 'size': 100}
        ]

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        from upload_attachment import upload_attachment

        result = upload_attachment('PROJ-123', str(test_file), file_name='custom_name.txt', profile=None)

        call_args = mock_jira_client.upload_file.call_args
        assert call_args[1]['file_name'] == 'custom_name.txt'

    def test_upload_attachment_file_not_found(self):
        """Test error when file doesn't exist."""
        from error_handler import ValidationError

        from upload_attachment import upload_attachment

        with pytest.raises(ValidationError):
            upload_attachment('PROJ-123', '/nonexistent/file.txt', profile=None)

    @patch('upload_attachment.get_jira_client')
    def test_upload_attachment_permission_denied(self, mock_get_client, mock_jira_client, tmp_path):
        """Test error when no permission to attach."""
        from error_handler import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.upload_file.side_effect = PermissionError("No permission to add attachments")

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        from upload_attachment import upload_attachment

        with pytest.raises(PermissionError):
            upload_attachment('PROJ-123', str(test_file), profile=None)
```

#### 1.3.3 Create `tests/test_manage_watchers.py`

```python
"""
Tests for manage_watchers.py - Manage issue watchers.
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.fixture
def sample_watchers():
    """Sample watchers list."""
    return [
        {'accountId': '5b10a2844c20165700ede21g', 'displayName': 'Alice Smith', 'emailAddress': 'alice@company.com'},
        {'accountId': '5b10a2844c20165700ede22h', 'displayName': 'Bob Jones', 'emailAddress': 'bob@company.com'}
    ]


@pytest.mark.collaborate
@pytest.mark.unit
class TestListWatchers:
    """Tests for listing watchers."""

    @patch('manage_watchers.get_jira_client')
    def test_list_watchers_success(self, mock_get_client, mock_jira_client, sample_watchers):
        """Test listing watchers."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get.return_value = {'watchers': sample_watchers}

        from manage_watchers import list_watchers

        result = list_watchers('PROJ-123', profile=None)

        assert len(result) == 2
        assert result[0]['displayName'] == 'Alice Smith'

    @patch('manage_watchers.get_jira_client')
    def test_list_watchers_empty(self, mock_get_client, mock_jira_client):
        """Test listing when no watchers."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get.return_value = {'watchers': []}

        from manage_watchers import list_watchers

        result = list_watchers('PROJ-123', profile=None)

        assert len(result) == 0


@pytest.mark.collaborate
@pytest.mark.unit
class TestAddWatcher:
    """Tests for adding watchers."""

    @patch('manage_watchers.get_jira_client')
    def test_add_watcher_by_account_id(self, mock_get_client, mock_jira_client):
        """Test adding watcher by account ID."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.post.return_value = None

        from manage_watchers import add_watcher

        add_watcher('PROJ-123', '5b10a2844c20165700ede21g', profile=None)

        mock_jira_client.post.assert_called_once()

    @patch('manage_watchers.get_jira_client')
    def test_add_watcher_by_email(self, mock_get_client, mock_jira_client):
        """Test adding watcher by email (lookup required)."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get.return_value = [{'accountId': '5b10a2844c20165700ede21g'}]
        mock_jira_client.post.return_value = None

        from manage_watchers import add_watcher

        add_watcher('PROJ-123', 'alice@company.com', profile=None)

        mock_jira_client.get.assert_called_once()
        mock_jira_client.post.assert_called_once()

    @patch('manage_watchers.get_jira_client')
    def test_add_watcher_user_not_found(self, mock_get_client, mock_jira_client):
        """Test error when user not found."""
        from error_handler import ValidationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get.return_value = []

        from manage_watchers import add_watcher

        with pytest.raises(ValidationError):
            add_watcher('PROJ-123', 'nonexistent@company.com', profile=None)


@pytest.mark.collaborate
@pytest.mark.unit
class TestRemoveWatcher:
    """Tests for removing watchers."""

    @patch('manage_watchers.get_jira_client')
    def test_remove_watcher_by_account_id(self, mock_get_client, mock_jira_client):
        """Test removing watcher by account ID."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete.return_value = None

        from manage_watchers import remove_watcher

        remove_watcher('PROJ-123', '5b10a2844c20165700ede21g', profile=None)

        mock_jira_client.delete.assert_called_once()

    @patch('manage_watchers.get_jira_client')
    def test_remove_watcher_by_email(self, mock_get_client, mock_jira_client):
        """Test removing watcher by email (lookup required)."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get.return_value = [{'accountId': '5b10a2844c20165700ede21g'}]
        mock_jira_client.delete.return_value = None

        from manage_watchers import remove_watcher

        remove_watcher('PROJ-123', 'alice@company.com', profile=None)

        mock_jira_client.get.assert_called_once()
        mock_jira_client.delete.assert_called_once()
```

#### 1.3.4 Create `tests/test_update_custom_fields.py`

```python
"""
Tests for update_custom_fields.py - Update custom fields on issues.
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.collaborate
@pytest.mark.unit
class TestUpdateCustomFields:
    """Tests for updating custom fields."""

    @patch('update_custom_fields.get_jira_client')
    def test_update_single_field(self, mock_get_client, mock_jira_client):
        """Test updating a single custom field."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.return_value = None

        from update_custom_fields import update_custom_fields

        update_custom_fields('PROJ-123', field='customfield_10001', value='Production', profile=None)

        mock_jira_client.update_issue.assert_called_once()
        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][0] == 'PROJ-123'
        assert call_args[0][1] == {'customfield_10001': 'Production'}

    @patch('update_custom_fields.get_jira_client')
    def test_update_multiple_fields_json(self, mock_get_client, mock_jira_client):
        """Test updating multiple fields via JSON."""
        import json
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.return_value = None

        from update_custom_fields import update_custom_fields

        fields_json = json.dumps({
            'customfield_10001': 'Production',
            'customfield_10002': 'High'
        })

        update_custom_fields('PROJ-123', fields_json=fields_json, profile=None)

        call_args = mock_jira_client.update_issue.call_args
        assert 'customfield_10001' in call_args[0][1]
        assert 'customfield_10002' in call_args[0][1]

    @patch('update_custom_fields.get_jira_client')
    def test_update_field_json_value(self, mock_get_client, mock_jira_client):
        """Test updating field with JSON value (e.g., select field)."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.return_value = None

        from update_custom_fields import update_custom_fields

        # JSON value for select field
        update_custom_fields('PROJ-123', field='customfield_10001', value='{"value": "Option A"}', profile=None)

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]['customfield_10001'] == {'value': 'Option A'}

    def test_update_no_fields_specified(self):
        """Test error when no fields specified."""
        from error_handler import ValidationError

        from update_custom_fields import update_custom_fields

        with pytest.raises(ValidationError):
            update_custom_fields('PROJ-123', profile=None)

    @patch('update_custom_fields.get_jira_client')
    def test_update_field_not_found(self, mock_get_client, mock_jira_client):
        """Test error when field doesn't exist."""
        from error_handler import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.side_effect = JiraError("Field 'customfield_99999' does not exist", status_code=400)

        from update_custom_fields import update_custom_fields

        with pytest.raises(JiraError):
            update_custom_fields('PROJ-123', field='customfield_99999', value='test', profile=None)
```

---

## Phase 2: High Priority Issues

### 2.1 Missing API Error Handling Tests

**Impact:** Error scenarios untested, poor user experience on failures
**Coverage Gap:** All 6 existing test files missing tests for:
- `AuthenticationError` (401)
- `PermissionError` (403)
- Rate limiting (429)
- Server errors (500)
- Network timeout/connection errors

**Files to Update:**

| File | Lines | Missing Error Tests |
|------|-------|---------------------|
| `test_get_comments.py` | After 119 | 401, 403, 429, 500 |
| `test_update_comment.py` | After 96 | 401, 429, 500 |
| `test_delete_comment.py` | After 89 | 401, 429, 500 |
| `test_comment_visibility.py` | After 140 | 401, 403, 429, 500 |
| `test_send_notification.py` | After 157 | 401, 403, 429, 500 |
| `test_get_activity.py` | After 143 | 401, 403, 429, 500 |

**Remediation Template - Add to each test file:**

```python
@pytest.mark.collaborate
@pytest.mark.unit
class TestApiErrorHandling:
    """Test API error handling scenarios."""

    @patch('get_comments.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.side_effect = AuthenticationError("Invalid API token")

        from get_comments import get_comments

        with pytest.raises(AuthenticationError):
            get_comments('PROJ-123', profile=None)

    @patch('get_comments.get_jira_client')
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.side_effect = PermissionError("No permission to view comments")

        from get_comments import get_comments

        with pytest.raises(PermissionError):
            get_comments('PROJ-123', profile=None)

    @patch('get_comments.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.side_effect = JiraError("Rate limit exceeded", status_code=429)

        from get_comments import get_comments

        with pytest.raises(JiraError) as exc_info:
            get_comments('PROJ-123', profile=None)
        assert exc_info.value.status_code == 429

    @patch('get_comments.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comments.side_effect = JiraError("Internal server error", status_code=500)

        from get_comments import get_comments

        with pytest.raises(JiraError) as exc_info:
            get_comments('PROJ-123', profile=None)
        assert exc_info.value.status_code == 500
```

---

### 2.2 Missing Edge Case Tests

**Priority order by impact:**

| Category | Test File | Missing Edge Case |
|----------|-----------|-------------------|
| Empty results | `test_get_activity.py` | Empty changelog (no history) |
| Pagination boundary | `test_get_comments.py` | Offset exceeds total |
| Invalid input | `test_send_notification.py` | No recipients specified |
| Invalid input | `test_update_comment.py` | Empty body |
| Large content | `test_get_comments.py` | Very long comment body |
| Concurrent | All files | Concurrent modification handling |

**Remediation Template:**

```python
@patch('get_activity.get_jira_client')
def test_empty_changelog(self, mock_get_client, mock_jira_client):
    """Test handling issue with no history."""
    mock_get_client.return_value = mock_jira_client
    mock_jira_client.get_changelog.return_value = {
        'startAt': 0,
        'maxResults': 100,
        'total': 0,
        'isLast': True,
        'values': []
    }

    from get_activity import get_activity, parse_changelog

    result = get_activity('PROJ-123', profile=None)
    parsed = parse_changelog(result)

    assert result['total'] == 0
    assert len(parsed) == 0


@patch('send_notification.get_jira_client')
def test_notify_no_recipients(self, mock_get_client, mock_jira_client):
    """Test error when no recipients specified."""
    from error_handler import ValidationError

    mock_get_client.return_value = mock_jira_client

    from send_notification import send_notification

    with pytest.raises(ValidationError):
        send_notification(
            'PROJ-123',
            subject='Test',
            body='Body',
            # No recipients: watchers=False, assignee=False, etc.
            profile=None
        )
```

---

## Phase 3: Medium Priority Issues

### 3.1 Fixture Mutation Issue

**Impact:** Potential test pollution between tests
**File:** `test_update_comment.py` (line 21)

**Current (mutation risk):**

```python
def test_update_comment_body(self, mock_get_client, mock_jira_client, sample_comment):
    """Test updating comment body."""
    mock_get_client.return_value = mock_jira_client
    updated_comment = sample_comment.copy()  # Shallow copy - nested dicts shared!
    updated_comment['body']['content'][0]['content'][0]['text'] = 'Updated text'  # Mutates original!
```

**Remediation (safe):**

```python
def test_update_comment_body(self, mock_get_client, mock_jira_client, sample_comment):
    """Test updating comment body."""
    import copy
    mock_get_client.return_value = mock_jira_client
    updated_comment = copy.deepcopy(sample_comment)  # Deep copy - safe
    updated_comment['body']['content'][0]['content'][0]['text'] = 'Updated text'
```

---

### 3.2 Missing CLI Tests

**Impact:** CLI entry points not tested
**Files Affected:** All 9 scripts have `main()` functions that are not tested

| Script | CLI Features to Test |
|--------|---------------------|
| `add_comment.py` | `--body`, `--format`, `--visibility-role`, `--visibility-group` |
| `get_comments.py` | Order options, pagination, output formats |
| `update_comment.py` | `--format` options |
| `delete_comment.py` | Confirmation prompt handling |
| `send_notification.py` | `--watchers`, `--assignee`, `--users`, `--groups` |
| `get_activity.py` | Filtering, output formats |
| `upload_attachment.py` | `--file`, `--name` |
| `manage_watchers.py` | `--add`, `--remove`, `--list` |
| `update_custom_fields.py` | `--field`, `--value`, `--fields` |

**Remediation Template:**

```python
@pytest.mark.collaborate
@pytest.mark.unit
class TestCli:
    """Tests for CLI entry point."""

    @patch('add_comment.get_jira_client')
    def test_cli_basic_comment(self, mock_get_client, mock_jira_client, sample_comment, capsys):
        """Test CLI with basic arguments."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.add_comment.return_value = sample_comment

        import sys
        from unittest.mock import patch as mock_patch

        with mock_patch.object(sys, 'argv', ['add_comment.py', 'PROJ-123', '--body', 'Test comment']):
            from add_comment import main
            main()

        captured = capsys.readouterr()
        assert 'Added comment' in captured.out

    @patch('add_comment.get_jira_client')
    def test_cli_with_visibility(self, mock_get_client, mock_jira_client, sample_comment_with_visibility, capsys):
        """Test CLI with visibility argument."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.add_comment_with_visibility.return_value = sample_comment_with_visibility

        import sys
        from unittest.mock import patch as mock_patch

        with mock_patch.object(sys, 'argv', [
            'add_comment.py', 'PROJ-123',
            '--body', 'Internal note',
            '--visibility-role', 'Administrators'
        ]):
            from add_comment import main
            main()

        captured = capsys.readouterr()
        assert 'Visibility' in captured.out
```

---

### 3.3 Missing Output Format Tests

**Impact:** Output formatting not tested, could break CLI usability
**Files Affected:** 2

| File | Missing Test |
|------|--------------|
| `test_send_notification.py` | JSON output format test |
| `test_delete_comment.py` | Formatted output after deletion |

**Remediation:**

```python
@patch('send_notification.get_jira_client')
def test_format_notification_output(self, mock_get_client, mock_jira_client):
    """Test JSON output format for notifications."""
    import json

    from send_notification import notify_dry_run

    result = notify_dry_run(
        'PROJ-123',
        subject='Test',
        body='Body',
        watchers=True,
        profile=None
    )

    # Should be JSON serializable
    json_str = json.dumps(result)
    parsed = json.loads(json_str)

    assert parsed['issue_key'] == 'PROJ-123'
    assert 'recipients' in parsed
```

---

## Phase 4: Low Priority Issues

### 4.1 Remove Unused Imports

**Impact:** Code hygiene
**Files Affected:** 6 files

All test files import `MagicMock` directly but only use `patch` from the mock module. The `MagicMock` is provided by conftest.py fixture.

```bash
# Files with potentially unused MagicMock import:
tests/test_get_comments.py:6
tests/test_update_comment.py:6
tests/test_delete_comment.py:6
tests/test_comment_visibility.py:6
tests/test_send_notification.py:6
tests/test_get_activity.py:6
```

**Remediation:**

```python
# Before:
from unittest.mock import MagicMock, patch

# After (if MagicMock not used in file):
from unittest.mock import patch
```

**Note:** Review each file to confirm MagicMock is not used before removing.

---

### 4.2 Inconsistent Docstrings

**Impact:** Documentation quality
**Pattern to standardize:**

```python
# Before (minimal):
def test_get_all_comments(self, mock_get_client, mock_jira_client, sample_comments_list):
    """Test fetching all comments on an issue."""

# After (comprehensive):
def test_get_all_comments(self, mock_get_client, mock_jira_client, sample_comments_list):
    """Test fetching all comments on an issue.

    Verifies:
        - All comments are returned
        - Comment author information is preserved
        - Correct API call is made with default parameters
    """
```

---

### 4.3 Add Test Count Verification

**Impact:** Catch accidental test deletion
**Add to CI/CD or pre-commit:**

```python
# tests/test_coverage_check.py
import pytest
from pathlib import Path

def test_minimum_test_count():
    """Ensure test count doesn't regress."""
    test_dir = Path(__file__).parent
    test_files = list(test_dir.glob('test_*.py'))

    # Count test functions
    test_count = 0
    for f in test_files:
        content = f.read_text()
        test_count += content.count('def test_')

    # Current: 37 tests, target after remediation: 80+
    MIN_TESTS = 37
    assert test_count >= MIN_TESTS, f"Expected {MIN_TESTS}+ tests, found {test_count}"
```

---

## Implementation Checklist

### Phase 1 Checklist (Critical)

- [ ] Add `pytest_configure` to conftest.py
- [ ] Add pytest markers to 6 test classes
- [ ] Create `test_add_comment.py` with 5+ tests
- [ ] Create `test_upload_attachment.py` with 4+ tests
- [ ] Create `test_manage_watchers.py` with 8+ tests
- [ ] Create `test_update_custom_fields.py` with 5+ tests

### Phase 2 Checklist (High Priority)

- [ ] Add error handling tests to `test_get_comments.py` (4 tests)
- [ ] Add error handling tests to `test_update_comment.py` (4 tests)
- [ ] Add error handling tests to `test_delete_comment.py` (4 tests)
- [ ] Add error handling tests to `test_comment_visibility.py` (4 tests)
- [ ] Add error handling tests to `test_send_notification.py` (4 tests)
- [ ] Add error handling tests to `test_get_activity.py` (4 tests)
- [ ] Add edge case tests (empty results, invalid input, boundaries)

### Phase 3 Checklist (Medium Priority)

- [ ] Fix fixture mutation in `test_update_comment.py` (use deepcopy)
- [ ] Add CLI tests for all 9 scripts
- [ ] Add output format tests to `test_send_notification.py`
- [ ] Add output format tests to `test_delete_comment.py`

### Phase 4 Checklist (Low Priority)

- [ ] Remove unused `MagicMock` imports from 6 files
- [ ] Standardize docstrings
- [ ] Add test count verification

---

## Verification Commands

```bash
# Run all collaborate tests
pytest .claude/skills/jira-collaborate/tests/ -v

# Run only unit tests (after adding markers)
pytest .claude/skills/jira-collaborate/tests/ -v -m unit

# Run only collaborate skill tests (after adding markers)
pytest .claude/skills/jira-collaborate/tests/ -v -m collaborate

# Check for test count
pytest .claude/skills/jira-collaborate/tests/ --collect-only | grep "test session starts" -A 5

# Verify no unused imports (requires pylint)
pylint .claude/skills/jira-collaborate/tests/ --disable=all --enable=unused-import

# Check for shallow copy usage (potential mutation)
grep -rn "\.copy()" .claude/skills/jira-collaborate/tests/
```

---

## Success Criteria

1. **All tests pass:** `pytest` exits with code 0
2. **No fixture mutations:** All uses `.copy()` replaced with `deepcopy`
3. **Consistent markers:** All test classes have `@pytest.mark.collaborate` and `@pytest.mark.unit`
4. **No pytest warnings:** About unknown markers
5. **Coverage maintained:** Test count >= 80 (up from current 37)
6. **100% script coverage:** All 9 scripts have corresponding test files
7. **Error handling tested:** 401, 403, 429, 500 covered for all scripts

---

## Current vs Target Test Count

| Metric | Current | Target |
|--------|---------|--------|
| Test files | 6 | 10 |
| Test classes | 6 | 15+ |
| Test functions | 37 | 80+ |
| Scripts with tests | 5/9 (56%) | 9/9 (100%) |
| Error handling tests | 3 | 36+ |

---

## Notes

- Prioritize Phase 1 before merging to main
- Phase 2 should be completed before next release
- Phases 3-4 can be addressed incrementally
- Consider adding pre-commit hooks to prevent regression
- The `add_comment.py` script has partial coverage through `test_comment_visibility.py` but needs dedicated tests
