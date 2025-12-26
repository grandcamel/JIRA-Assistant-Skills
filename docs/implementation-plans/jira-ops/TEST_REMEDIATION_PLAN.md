# Test Remediation Plan: jira-ops Skill

**Created:** 2025-12-26
**Status:** Draft
**Test Files Reviewed:** 8
**Total Issues Identified:** ~65

---

## Executive Summary

This plan addresses test quality issues discovered during a comprehensive review of the `jira-ops` skill test suite. The jira-ops skill focuses on cache management, request batching, and operational utilities. Issues are organized by priority and grouped into actionable phases.

**Test File Breakdown:**
- Unit Tests: 4 files (`conftest.py`, `test_cache.py`, `test_cache_scripts.py`, `test_request_batcher.py`)
- Live Integration Tests: 3 files (`conftest.py`, `__init__.py`, `test_cache_operations.py`)

**Estimated Effort:**
- Phase 1 (Critical): 2-3 hours
- Phase 2 (High Priority): 3-4 hours
- Phase 3 (Medium Priority): 2-3 hours
- Phase 4 (Low Priority): 1-2 hours

---

## Phase 1: Critical Issues (Must Fix)

### 1.1 Missing pytest Markers on Test Classes

**Impact:** Inconsistent test categorization, unable to run tests by category
**Files Affected:** All test files (6 files with test classes)

| File | Line | Classes Missing Markers |
|------|------|------------------------|
| `tests/test_cache.py` | 30, 57, 78, 118, 158, 180, 210, 227, 244, 274, 298, 328, 415, 458 | All 14 classes |
| `tests/test_cache_scripts.py` | 30, 77, 161 | All 3 classes |
| `tests/test_request_batcher.py` | 27, 88, 126, 163, 229, 274, 312 | All 7 classes |
| `tests/live_integration/test_cache_operations.py` | 22, 53, 87, 105, 123, 205, 253 | All 7 classes |

**Remediation:**

Add markers to `tests/conftest.py`:

```python
# Add at top of conftest.py
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "ops: mark test as ops skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "asyncio: mark test as async test")
```

Add to each test class in unit tests:

```python
@pytest.mark.ops
@pytest.mark.unit
class TestCacheGetHit:
    """Test cache hit returns cached value."""
```

Add to each test class in live integration tests:

```python
@pytest.mark.ops
@pytest.mark.integration
class TestCacheWarmProjects:
    """Tests for project cache warming."""
```

---

### 1.2 Missing pytest-asyncio Configuration

**Impact:** Async tests may not be properly discovered or may cause warnings
**File:** `tests/conftest.py`

**Current Issue:** `test_request_batcher.py` uses `@pytest.mark.asyncio` but pytest-asyncio mode is not configured.

**Remediation - Add to `tests/conftest.py`:**

```python
# Add pytest-asyncio configuration
def pytest_configure(config):
    """Register custom markers and configure pytest-asyncio."""
    config.addinivalue_line("markers", "ops: mark test as ops skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "asyncio: mark test as async test")


# Configure pytest-asyncio mode
pytest_plugins = ['pytest_asyncio']
```

**Alternative - Add `pytest.ini` or `pyproject.toml`:**

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
```

---

### 1.3 Weak Assertions That Always Pass

**Impact:** Tests pass even when functionality is broken
**Files Affected:** 4 files

| File | Line | Current Assertion | Fix |
|------|------|-------------------|-----|
| `test_cache.py` | 427 | `assert stats.entry_count >= 3` | `assert stats.entry_count == 3` |
| `test_cache.py` | 439 | `assert stats.by_category["issue"]["count"] >= 2` | `assert stats.by_category["issue"]["count"] == 2` |
| `test_cache_operations.py` | 224 | `assert cached_issues >= 0` | `assert cached_issues >= 0 or len(result.get('issues', [])) == 0` with comment |
| `test_request_batcher.py` | 249 | `assert len(progress_calls) > 0` | `assert len(progress_calls) >= 5` (should be at least as many as requests) |

**Remediation Examples:**

```python
# Before (test_cache.py:427 - weak):
def test_cache_stats_entry_count(self, temp_cache_dir):
    cache = JiraCache(cache_dir=temp_cache_dir)
    cache.set("key1", {"value": 1}, category="issue")
    cache.set("key2", {"value": 2}, category="issue")
    cache.set("key3", {"value": 3}, category="project")

    stats = cache.get_stats()

    assert stats.entry_count >= 3  # Always true if anything cached

# After (strong):
def test_cache_stats_entry_count(self, temp_cache_dir):
    cache = JiraCache(cache_dir=temp_cache_dir)
    cache.set("key1", {"value": 1}, category="issue")
    cache.set("key2", {"value": 2}, category="issue")
    cache.set("key3", {"value": 3}, category="project")

    stats = cache.get_stats()

    assert stats.entry_count == 3
    assert "issue" in stats.by_category
    assert "project" in stats.by_category
```

---

### 1.4 Fixture Mutation Issues

**Impact:** Potential test pollution between tests
**Files Affected:** 2 files

| File | Line | Issue |
|------|------|-------|
| `tests/conftest.py` | 47-61 | `sample_issue_data` fixture returns mutable dict |
| `tests/conftest.py` | 64-72 | `sample_project_data` fixture returns mutable dict |
| `tests/conftest.py` | 75-83 | `sample_user_data` fixture returns mutable dict |
| `tests/conftest.py` | 86-94 | `sample_field_data` fixture returns mutable dict |

**Remediation:**

```python
# Before (mutation risk):
@pytest.fixture
def sample_issue_data():
    """Sample JIRA issue data for cache testing."""
    return {
        "id": "10100",
        "key": "PROJ-123",
        # ... rest of data
    }

# After (safe - use deepcopy):
import copy

@pytest.fixture
def sample_issue_data():
    """Sample JIRA issue data for cache testing."""
    data = {
        "id": "10100",
        "key": "PROJ-123",
        "self": "https://test.atlassian.net/rest/api/3/issue/10100",
        "fields": {
            "summary": "Test Issue",
            "description": None,
            "issuetype": {"name": "Task"},
            "project": {"key": "PROJ"},
            "status": {"name": "To Do"},
            "priority": {"name": "Medium"}
        }
    }
    return copy.deepcopy(data)
```

---

## Phase 2: High Priority Issues

### 2.1 Missing Error Handling Tests

**Impact:** Error scenarios untested, poor user experience on failures
**Coverage Gap:** All test files missing tests for:
- `AuthenticationError` (401)
- `PermissionError` (403)
- `NotFoundError` (404)
- Rate limiting (429)
- Server errors (500, 502, 503, 504)
- Network timeout/connection errors

**Files to Update:**

| File | Missing Tests |
|------|---------------|
| `test_cache.py` | SQLite errors, corrupted cache file |
| `test_cache_scripts.py` | Invalid cache directory, permission errors |
| `test_request_batcher.py` | 401, 403, 404, 429, 500 error handling |

**Remediation Template for `test_request_batcher.py`:**

```python
class TestBatchErrorCodes:
    """Test handling of specific HTTP error codes."""

    @pytest.mark.asyncio
    async def test_batch_handles_401_unauthorized(self, mock_jira_client):
        """Test handling of 401 authentication error."""
        from error_handler import AuthenticationError

        mock_jira_client.get.side_effect = AuthenticationError("Invalid token")
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        results = await batcher.execute()

        assert results[request_id].success is False
        assert "authentication" in results[request_id].error.lower() or \
               "401" in results[request_id].error

    @pytest.mark.asyncio
    async def test_batch_handles_403_forbidden(self, mock_jira_client):
        """Test handling of 403 permission denied error."""
        from error_handler import JiraError

        mock_jira_client.get.side_effect = JiraError("Permission denied", status_code=403)
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        results = await batcher.execute()

        assert results[request_id].success is False
        assert results[request_id].error is not None

    @pytest.mark.asyncio
    async def test_batch_handles_404_not_found(self, mock_jira_client):
        """Test handling of 404 not found error."""
        from error_handler import JiraError

        mock_jira_client.get.side_effect = JiraError("Issue not found", status_code=404)
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("GET", "/rest/api/3/issue/NONEXISTENT-1")
        results = await batcher.execute()

        assert results[request_id].success is False
        assert "not found" in results[request_id].error.lower() or \
               "404" in results[request_id].error

    @pytest.mark.asyncio
    async def test_batch_handles_429_rate_limit(self, mock_jira_client):
        """Test handling of 429 rate limit error."""
        from error_handler import JiraError

        mock_jira_client.get.side_effect = JiraError("Rate limit exceeded", status_code=429)
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        results = await batcher.execute()

        assert results[request_id].success is False
        assert "rate" in results[request_id].error.lower() or \
               "429" in results[request_id].error

    @pytest.mark.asyncio
    async def test_batch_handles_500_server_error(self, mock_jira_client):
        """Test handling of 500 internal server error."""
        from error_handler import JiraError

        mock_jira_client.get.side_effect = JiraError("Internal server error", status_code=500)
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        results = await batcher.execute()

        assert results[request_id].success is False
        assert results[request_id].error is not None
```

**Remediation Template for `test_cache.py`:**

```python
class TestCacheErrorHandling:
    """Test cache error handling scenarios."""

    def test_cache_handles_corrupted_db(self, temp_cache_dir):
        """Test handling of corrupted database file."""
        # Create cache and add data
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("key1", {"value": 1}, category="issue")
        cache.close()

        # Corrupt the database file
        db_path = Path(temp_cache_dir) / "cache.db"
        with open(db_path, 'wb') as f:
            f.write(b"corrupted data")

        # Should handle gracefully (may recreate or raise specific error)
        try:
            cache2 = JiraCache(cache_dir=temp_cache_dir)
            # If it succeeds, cache should be empty/fresh
            stats = cache2.get_stats()
            assert stats.entry_count == 0
        except Exception as e:
            # Should be a specific, catchable error
            assert "database" in str(e).lower() or "corrupt" in str(e).lower()

    def test_cache_handles_readonly_directory(self, temp_cache_dir):
        """Test handling of read-only cache directory."""
        import os
        import stat

        # Make directory read-only (skip on Windows)
        if os.name != 'nt':
            os.chmod(temp_cache_dir, stat.S_IRUSR | stat.S_IXUSR)
            try:
                cache = JiraCache(cache_dir=temp_cache_dir + "/subdir")
                # Should raise permission error
                pytest.fail("Expected permission error")
            except PermissionError:
                pass  # Expected
            finally:
                os.chmod(temp_cache_dir, stat.S_IRWXU)
```

---

### 2.2 Cache API Mismatches Between Tests and Implementation

**Impact:** Tests may pass but actual usage fails, or tests may fail incorrectly
**Files Affected:** 2 files

| File | Line | Issue | API Expectation vs. Reality |
|------|------|-------|----------------------------|
| `test_cache_operations.py` | 33 | `stats['total_entries']` | Implementation uses `stats.entry_count` (CacheStats dataclass) |
| `test_cache_operations.py` | 50 | `stats['categories']` | Implementation uses `stats.by_category` |
| `test_cache_operations.py` | 64 | `stats['categories']` | Implementation uses `stats.by_category` |
| `test_cache_operations.py` | 132 | `cache.get(key)` without category | Implementation requires `category` parameter |
| `test_cache_operations.py` | 148 | `cache.set(..., ttl=1)` | TTL should be `timedelta(seconds=1)` not int |
| `test_cache_operations.py` | 164 | `cache.invalidate(key)` | Implementation signature: `invalidate(key=None, pattern=None, category=None)` |
| `test_cache_operations.py` | 175 | `stats['total_entries']` | Should be `stats.entry_count` |
| `test_cache_operations.py` | 195 | `cache.clear(category="issue")` | Implementation: `clear()` returns count, `invalidate(category="...")` for category clear |
| `test_cache_operations.py` | 272 | `stats['hit_rate']` or `stats['hits']` | Implementation uses `stats.hit_rate` (float property) |

**Remediation for `test_cache_operations.py`:**

```python
# Before (line 33 - incorrect API):
def test_warm_projects_success(self, jira_client, test_cache):
    count = warm_projects(jira_client, test_cache, verbose=False)
    assert count > 0
    stats = test_cache.get_stats()
    assert stats['total_entries'] > 0  # Wrong - dict access

# After (correct API):
def test_warm_projects_success(self, jira_client, test_cache):
    count = warm_projects(jira_client, test_cache, verbose=False)
    assert count > 0
    stats = test_cache.get_stats()
    assert stats.entry_count > 0  # Correct - attribute access

# Before (line 132 - missing category):
def test_cache_set_and_get(self, test_cache):
    key = "test_key_123"
    value = {"data": "test_value", "count": 42}
    test_cache.set(key, value, category="test")
    retrieved = test_cache.get(key)  # Missing category!
    assert retrieved is not None

# After (with category):
def test_cache_set_and_get(self, test_cache):
    key = "test_key_123"
    value = {"data": "test_value", "count": 42}
    test_cache.set(key, value, category="test")
    retrieved = test_cache.get(key, category="test")  # Include category
    assert retrieved is not None
    assert retrieved == value

# Before (line 148 - wrong ttl type):
def test_cache_expiry(self, test_cache):
    test_cache.set(key, value, category="test", ttl=1)  # int instead of timedelta

# After (correct ttl type):
from datetime import timedelta

def test_cache_expiry(self, test_cache):
    test_cache.set(key, value, category="test", ttl=timedelta(seconds=1))

# Before (line 195 - wrong clear API):
def test_cache_clear_category(self, test_cache):
    test_cache.clear(category="issue")  # clear() doesn't take category

# After (correct API):
def test_cache_clear_category(self, test_cache):
    test_cache.invalidate(category="issue")  # Use invalidate for category clear
```

---

### 2.3 Incomplete Test Assertions in Script Tests

**Impact:** Tests may pass without verifying actual behavior
**File:** `tests/test_cache_scripts.py`

| Line | Issue |
|------|-------|
| 47-51 | `test_cache_status_shows_stats` - No actual assertion, just "doesn't crash" |
| 66-74 | `test_cache_status_json_output` - Only tests if output can be parsed, not content validity |
| 184-186 | `test_cache_warm_projects` - No assertion that cache was actually populated |

**Remediation:**

```python
# Before (line 47-51 - no real assertion):
def test_cache_status_shows_stats(self, temp_cache_dir):
    cache = JiraCache(cache_dir=temp_cache_dir)
    cache.set("issue1", {"key": "PROJ-1"}, category="issue")
    cache.close()

    import cache_status
    with patch('sys.argv', ['cache_status.py', '--cache-dir', temp_cache_dir]):
        with patch('sys.stdout') as mock_stdout:
            try:
                cache_status.main()
            except SystemExit:
                pass  # No assertion!

# After (with actual assertions):
def test_cache_status_shows_stats(self, temp_cache_dir, capsys):
    """Test showing cache statistics with actual output verification."""
    cache = JiraCache(cache_dir=temp_cache_dir)
    cache.set("issue1", {"key": "PROJ-1"}, category="issue")
    cache.set("issue2", {"key": "PROJ-2"}, category="issue")
    cache.close()

    import cache_status

    with patch('sys.argv', ['cache_status.py', '--cache-dir', temp_cache_dir]):
        try:
            cache_status.main()
        except SystemExit as e:
            assert e.code is None or e.code == 0  # Success exit

    captured = capsys.readouterr()
    # Verify expected output elements
    assert "Cache Statistics" in captured.out
    assert "Entries:" in captured.out
    assert "issue" in captured.out.lower()

# Before (line 184-186 - incomplete):
def test_cache_warm_projects(self, temp_cache_dir, mock_jira_client):
    # ... setup ...
    # Verify projects were cached
    cache = JiraCache(cache_dir=temp_cache_dir)
    stats = cache.get_stats()
    # At least attempted to cache something <-- No assertion!

# After (with proper verification):
def test_cache_warm_projects(self, temp_cache_dir, mock_jira_client):
    mock_jira_client.get.return_value = [
        {"key": "PROJ1", "name": "Project 1"},
        {"key": "PROJ2", "name": "Project 2"}
    ]

    import cache_warm

    with patch('cache_warm.get_jira_client', return_value=mock_jira_client):
        with patch('cache_warm.HAS_CONFIG_MANAGER', True):
            with patch('sys.argv', ['cache_warm.py', '--projects', '--cache-dir', temp_cache_dir, '-v']):
                try:
                    cache_warm.main()
                except SystemExit:
                    pass

    # Verify projects were actually cached
    cache = JiraCache(cache_dir=temp_cache_dir)
    stats = cache.get_stats()
    assert stats.entry_count >= 2
    assert "project" in stats.by_category
    assert stats.by_category["project"]["count"] >= 2
```

---

### 2.4 Missing LRU Eviction Test Completion

**Impact:** LRU behavior not verified
**File:** `test_cache.py`, lines 277-296

**Current (incomplete):**

```python
def test_cache_lru_eviction_removes_least_recently_used(self, temp_cache_dir):
    """Test that LRU eviction removes least recently used entries."""
    cache = JiraCache(cache_dir=temp_cache_dir, max_size_mb=0.001)

    cache.set("old1", {"data": "x" * 50}, category="issue")
    cache.set("old2", {"data": "x" * 50}, category="issue")

    # Access old1 to make it more recently used
    cache.get("old1", category="issue")

    # Add more entries to trigger eviction
    for i in range(50):
        cache.set(f"new{i}", {"data": "x" * 50}, category="issue")

    # old2 should be evicted first (least recently used)
    # old1 might still exist since we accessed it
    # This is a best-effort test - exact behavior depends on implementation
    # <-- NO ASSERTIONS!
```

**Remediation:**

```python
def test_cache_lru_eviction_removes_least_recently_used(self, temp_cache_dir):
    """Test that LRU eviction removes least recently used entries."""
    cache = JiraCache(cache_dir=temp_cache_dir, max_size_mb=0.001)

    # Add initial entries
    cache.set("old1", {"data": "x" * 50}, category="issue")
    cache.set("old2", {"data": "x" * 50}, category="issue")

    # Access old1 to make it more recently used
    result = cache.get("old1", category="issue")
    assert result is not None  # Verify old1 exists

    # Add more entries to trigger eviction
    for i in range(50):
        cache.set(f"new{i}", {"data": "x" * 50}, category="issue")

    # old2 should be evicted first (least recently used)
    old2_result = cache.get("old2", category="issue")
    assert old2_result is None, "old2 should have been evicted (LRU)"

    # old1 might still exist if cache is large enough, or be evicted
    # At minimum verify the cache is respecting size limits
    stats = cache.get_stats()
    assert stats.total_size_bytes <= cache.max_size
```

---

## Phase 3: Medium Priority Issues

### 3.1 Unused Imports

**Impact:** Code hygiene, slight memory overhead
**Files Affected:** 3 files

| File | Line | Unused Import |
|------|------|---------------|
| `tests/conftest.py` | 14 | `MagicMock` (only `Mock` used) |
| `tests/test_cache_scripts.py` | 15 | `subprocess` (not used in tests) |
| `tests/test_request_batcher.py` | 16 | `AsyncMock` (not used, mock_jira_client uses `Mock`) |
| `tests/live_integration/test_cache_operations.py` | 12 | `Dict, Any` from typing (not used in tests) |

**Remediation:**

```python
# tests/conftest.py - line 14
# Before:
from unittest.mock import Mock, MagicMock
# After:
from unittest.mock import Mock

# tests/test_cache_scripts.py - line 15
# Before:
import subprocess
# After:
# (remove line entirely)

# tests/test_request_batcher.py - line 16
# Before:
from unittest.mock import Mock, MagicMock, AsyncMock, patch
# After:
from unittest.mock import Mock, MagicMock, patch
```

---

### 3.2 Missing Edge Case Tests

**Impact:** Boundary conditions and edge cases untested
**Priority order by impact:**

| Category | Test File | Missing Edge Case |
|----------|-----------|-------------------|
| Empty batch | `test_request_batcher.py` | Test with 0 requests (already exists, but verify sync version) |
| Boundary | `test_cache.py` | Max key length (200+ chars triggers hash) |
| Boundary | `test_cache.py` | Max value size (very large JSON objects) |
| Concurrency | `test_request_batcher.py` | More requests than max_concurrent |
| Invalid input | `test_cache_scripts.py` | Invalid cache directory path |
| Invalid input | `test_request_batcher.py` | Unsupported HTTP method (e.g., PATCH) |

**Remediation Templates:**

```python
# test_cache.py - Add to TestCacheKeyGeneration
def test_generate_key_long_key_uses_hash(self, temp_cache_dir):
    """Test that long keys are hashed for storage."""
    cache = JiraCache(cache_dir=temp_cache_dir)

    # Create a key that would be > 200 chars
    long_jql = "project = PROJ AND " + " AND ".join([f"label{i} = 'value{i}'" for i in range(50)])
    key = cache.generate_key("search", jql=long_jql)

    assert len(key) <= 200
    assert "search:" in key  # Should still have category prefix
    # Hash should be consistent
    key2 = cache.generate_key("search", jql=long_jql)
    assert key == key2


def test_cache_large_value(self, temp_cache_dir):
    """Test caching very large values."""
    cache = JiraCache(cache_dir=temp_cache_dir)

    # Create a large value (1MB+)
    large_value = {
        "data": "x" * (1024 * 1024),
        "issues": [{"key": f"PROJ-{i}"} for i in range(1000)]
    }

    cache.set("large_key", large_value, category="search")
    result = cache.get("large_key", category="search")

    assert result is not None
    assert result["data"] == large_value["data"]
    assert len(result["issues"]) == 1000


# test_request_batcher.py - Add to TestBatchMethods
@pytest.mark.asyncio
async def test_batch_unsupported_method(self, mock_jira_client):
    """Test handling of unsupported HTTP method."""
    batcher = RequestBatcher(mock_jira_client)

    request_id = batcher.add("PATCH", "/rest/api/3/issue/PROJ-1", data={})
    results = await batcher.execute()

    assert results[request_id].success is False
    assert "unsupported" in results[request_id].error.lower() or \
           "method" in results[request_id].error.lower()


@pytest.mark.asyncio
async def test_batch_exceeds_max_concurrent(self, mock_jira_client):
    """Test batch with more requests than max_concurrent."""
    mock_jira_client.get.return_value = {"key": "test"}
    batcher = RequestBatcher(mock_jira_client, max_concurrent=2)

    # Add 10 requests with max_concurrent=2
    request_ids = []
    for i in range(10):
        request_ids.append(batcher.add("GET", f"/rest/api/3/issue/PROJ-{i}"))

    results = await batcher.execute()

    # All 10 should complete successfully
    assert len(results) == 10
    for request_id in request_ids:
        assert results[request_id].success is True
```

---

### 3.3 Missing DELETE Method Test

**Impact:** DELETE operations untested in request batcher
**File:** `test_request_batcher.py`

**Remediation:**

```python
# Add to TestBatchMethods class
@pytest.mark.asyncio
async def test_batch_delete_method(self, mock_jira_client):
    """Test DELETE method in batch."""
    mock_jira_client.delete.return_value = None  # DELETE typically returns empty
    batcher = RequestBatcher(mock_jira_client)

    request_id = batcher.add("DELETE", "/rest/api/3/issue/PROJ-1")
    results = await batcher.execute()

    mock_jira_client.delete.assert_called()
    assert results[request_id].success is True
```

---

### 3.4 Inconsistent Path Setup Between Files

**Impact:** Maintenance burden, potential import issues
**Files Affected:** 2 files with different path patterns

| File | Current Pattern |
|------|-----------------|
| `tests/conftest.py` | Uses `resolve()` for absolute paths |
| `tests/live_integration/conftest.py` | Does not use `resolve()` |

**Remediation for `tests/live_integration/conftest.py`:**

```python
# Before (line 18):
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib'))

# After (with resolve for absolute paths):
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / 'shared' / 'scripts' / 'lib'))
```

---

## Phase 4: Low Priority Issues

### 4.1 Test Documentation Improvements

**Impact:** Code maintainability and onboarding
**Files Affected:** All test files

**Improvements:**

1. Add module-level docstrings explaining test scope
2. Add class-level docstrings explaining test categories
3. Ensure all test methods have descriptive docstrings

```python
# Example for test_cache.py header
"""
Test suite for JiraCache caching layer.

Tests cover:
- Cache hit/miss behavior
- TTL expiration
- Key invalidation (single, pattern, category)
- Size limits and LRU eviction
- Persistence across sessions
- Thread-safe concurrent access
- Cache statistics

Usage:
    pytest tests/test_cache.py -v
    pytest tests/test_cache.py -v -m unit
"""
```

---

### 4.2 Add Test Count Verification

**Impact:** Catch accidental test deletion
**File:** New file `tests/test_coverage_check.py`

```python
"""Verify minimum test count to prevent accidental test deletion."""
import pytest
from pathlib import Path


def test_minimum_test_count():
    """Ensure test count doesn't regress."""
    test_dir = Path(__file__).parent
    test_files = list(test_dir.rglob('test_*.py'))

    # Count test functions
    test_count = 0
    for f in test_files:
        if f.name == 'test_coverage_check.py':
            continue
        content = f.read_text()
        test_count += content.count('def test_')

    # Minimum expected tests
    # Unit: ~60 tests, Integration: ~21 tests
    MIN_TESTS = 75
    assert test_count >= MIN_TESTS, f"Expected {MIN_TESTS}+ tests, found {test_count}"
```

---

### 4.3 Add Fixtures for Common Error Responses

**Impact:** Test consistency and reusability
**File:** `tests/conftest.py`

```python
@pytest.fixture
def auth_error():
    """Authentication error for testing."""
    from error_handler import AuthenticationError
    return AuthenticationError("Invalid or expired API token")


@pytest.fixture
def rate_limit_error():
    """Rate limit error for testing."""
    from error_handler import JiraError
    return JiraError("Rate limit exceeded. Retry after 30 seconds.", status_code=429)


@pytest.fixture
def not_found_error():
    """Not found error for testing."""
    from error_handler import JiraError
    return JiraError("Issue not found", status_code=404)


@pytest.fixture
def server_error():
    """Server error for testing."""
    from error_handler import JiraError
    return JiraError("Internal server error", status_code=500)
```

---

## Implementation Checklist

### Phase 1 Checklist (Critical)

- [ ] Add `pytest_configure` to `tests/conftest.py` with marker registration
- [ ] Add pytest markers to all 14 classes in `test_cache.py`
- [ ] Add pytest markers to all 3 classes in `test_cache_scripts.py`
- [ ] Add pytest markers to all 7 classes in `test_request_batcher.py`
- [ ] Add pytest markers to all 7 classes in `test_cache_operations.py`
- [ ] Configure pytest-asyncio mode
- [ ] Fix 4 weak assertions
- [ ] Add `copy.deepcopy` to all fixture returns in `conftest.py`

### Phase 2 Checklist (High Priority)

- [ ] Add error handling tests for 401, 403, 404, 429, 500 to `test_request_batcher.py`
- [ ] Add cache error handling tests (corrupted DB, readonly dir)
- [ ] Fix all Cache API mismatches in `test_cache_operations.py`:
  - [ ] `stats['total_entries']` -> `stats.entry_count`
  - [ ] `stats['categories']` -> `stats.by_category`
  - [ ] Add `category` parameter to all `cache.get()` calls
  - [ ] Change `ttl=1` to `ttl=timedelta(seconds=1)`
  - [ ] Change `cache.clear(category=...)` to `cache.invalidate(category=...)`
- [ ] Complete assertions in `test_cache_scripts.py`
- [ ] Complete LRU eviction test assertions

### Phase 3 Checklist (Medium Priority)

- [ ] Remove unused imports from 4 files
- [ ] Add long key hash test
- [ ] Add large value cache test
- [ ] Add unsupported HTTP method test
- [ ] Add exceeds max_concurrent test
- [ ] Add DELETE method test
- [ ] Standardize path setup with `resolve()`

### Phase 4 Checklist (Low Priority)

- [ ] Add module-level docstrings to all test files
- [ ] Add test count verification
- [ ] Add common error response fixtures

---

## Verification Commands

```bash
# Run all jira-ops unit tests
pytest .claude/skills/jira-ops/tests/ -v --ignore=.claude/skills/jira-ops/tests/live_integration

# Run only unit tests with marker
pytest .claude/skills/jira-ops/tests/ -v -m unit --ignore=.claude/skills/jira-ops/tests/live_integration

# Run async tests
pytest .claude/skills/jira-ops/tests/ -v -m asyncio --ignore=.claude/skills/jira-ops/tests/live_integration

# Run live integration tests (requires JIRA connection)
pytest .claude/skills/jira-ops/tests/live_integration/ --profile development -v

# Check for test count
pytest .claude/skills/jira-ops/tests/ --collect-only 2>/dev/null | grep "test session starts" -A 5

# Check for unused imports (requires pylint)
pylint .claude/skills/jira-ops/tests/ --disable=all --enable=unused-import

# Check weak assertions
grep -rn "assert.*>= 0" .claude/skills/jira-ops/tests/
grep -rn "assert.*>= 3" .claude/skills/jira-ops/tests/
grep -rn "or len.*== 0" .claude/skills/jira-ops/tests/

# Verify API usage
grep -rn "stats\[" .claude/skills/jira-ops/tests/
grep -rn "\.get_stats()" .claude/skills/jira-ops/tests/
```

---

## Success Criteria

1. **All tests pass:** `pytest` exits with code 0
2. **No weak assertions:** grep commands return no false-positive patterns
3. **Consistent markers:** All test classes have `@pytest.mark.ops` and `@pytest.mark.unit`/`@pytest.mark.integration`
4. **No pytest warnings:** About unknown markers or async configuration
5. **Coverage maintained:** Test count >= 75 (current baseline)
6. **No unused imports:** pylint reports clean
7. **API consistency:** All Cache API calls match implementation

---

## Notes

- Prioritize Phase 1 before merging to main
- Phase 2 should be completed before next release
- Phases 3-4 can be addressed incrementally
- The Cache API mismatches in live integration tests are critical - they will cause test failures
- Consider adding pre-commit hooks to prevent regression
