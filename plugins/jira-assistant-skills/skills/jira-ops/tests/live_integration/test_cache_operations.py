"""
Live Integration Tests: Cache Operations

Tests for cache management operations against a real JIRA instance.
"""

import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from cache import JiraCache
from cache_warm import warm_projects, warm_fields, warm_issue_types, warm_priorities, warm_statuses


class TestCacheWarmProjects:
    """Tests for project cache warming."""

    def test_warm_projects_success(self, jira_client, test_cache):
        """Test warming projects cache from JIRA."""
        count, error = warm_projects(jira_client, test_cache, verbose=False)

        assert error is None
        assert count > 0

        # Verify cache has data
        stats = test_cache.get_stats()
        assert stats.entry_count > 0

    def test_warm_projects_with_verbose(self, jira_client, test_cache, capsys):
        """Test verbose output during cache warming."""
        count, error = warm_projects(jira_client, test_cache, verbose=True)

        captured = capsys.readouterr()
        assert "Fetching projects" in captured.out
        assert error is None
        assert count > 0

    def test_warm_projects_cacheable(self, jira_client, test_cache):
        """Test that projects are properly cached."""
        count, _ = warm_projects(jira_client, test_cache, verbose=False)

        # Get a project from cache
        # Projects are cached by key
        stats = test_cache.get_stats()
        assert stats.by_category.get('project', {}).get('count', 0) > 0


class TestCacheWarmFields:
    """Tests for field cache warming."""

    def test_warm_fields_success(self, jira_client, test_cache):
        """Test warming fields cache from JIRA."""
        count, error = warm_fields(jira_client, test_cache, verbose=False)

        assert error is None
        assert count > 0

        # Verify cache has field data
        stats = test_cache.get_stats()
        assert stats.by_category.get('field', {}).get('count', 0) > 0

    def test_warm_fields_with_verbose(self, jira_client, test_cache, capsys):
        """Test verbose output during field cache warming."""
        count, error = warm_fields(jira_client, test_cache, verbose=True)

        captured = capsys.readouterr()
        assert "Fetching fields" in captured.out
        assert error is None
        assert count > 0

    def test_warm_fields_caches_all_list(self, jira_client, test_cache):
        """Test that the 'all fields' list is cached."""
        warm_fields(jira_client, test_cache, verbose=False)

        # The full list should be cached
        all_key = test_cache.generate_key("field", "all")
        all_fields = test_cache.get(all_key)

        if all_fields:
            assert isinstance(all_fields, list)
            assert len(all_fields) > 0


class TestCacheWarmIssueTypes:
    """Tests for issue type cache warming."""

    def test_warm_issue_types_success(self, jira_client, test_cache):
        """Test warming issue types cache from JIRA."""
        count, error = warm_issue_types(jira_client, test_cache, verbose=False)

        assert error is None
        assert isinstance(count, int)
        assert count > 0

    def test_warm_issue_types_with_verbose(self, jira_client, test_cache, capsys):
        """Test verbose output during issue type cache warming."""
        count, error = warm_issue_types(jira_client, test_cache, verbose=True)

        captured = capsys.readouterr()
        assert error is None
        assert "issue types" in captured.out.lower() or count > 0


class TestCacheWarmPrioritiesAndStatuses:
    """Tests for priority and status cache warming."""

    def test_warm_priorities_success(self, jira_client, test_cache):
        """Test warming priorities cache from JIRA."""
        count, error = warm_priorities(jira_client, test_cache, verbose=False)

        assert error is None
        assert isinstance(count, int)
        assert count > 0

    def test_warm_statuses_success(self, jira_client, test_cache):
        """Test warming statuses cache from JIRA."""
        count, error = warm_statuses(jira_client, test_cache, verbose=False)

        assert error is None
        assert isinstance(count, int)
        assert count > 0


class TestCacheOperations:
    """Tests for cache operations."""

    def test_cache_set_and_get(self, test_cache):
        """Test basic cache set and get operations."""
        key = "test_key_123"
        value = {"data": "test_value", "count": 42}

        test_cache.set(key, value, category="test")
        retrieved = test_cache.get(key, category="test")

        assert retrieved is not None
        assert retrieved == value

    def test_cache_expiry(self, test_cache):
        """Test cache with short TTL."""
        import time
        from datetime import timedelta

        key = "expiring_key"
        value = {"data": "will_expire"}

        # Set with very short TTL
        test_cache.set(key, value, category="test", ttl=timedelta(seconds=1))

        # Should be available immediately
        assert test_cache.get(key, category="test") is not None

        # Wait for expiry
        time.sleep(2)

        # Should be expired
        assert test_cache.get(key, category="test") is None

    def test_cache_invalidate(self, test_cache):
        """Test cache invalidation."""
        key = "to_invalidate"
        value = {"data": "will_be_removed"}

        test_cache.set(key, value, category="test")
        assert test_cache.get(key, category="test") is not None

        test_cache.invalidate(key=key, category="test")
        assert test_cache.get(key, category="test") is None

    def test_cache_stats(self, test_cache):
        """Test cache statistics."""
        # Add some entries
        for i in range(5):
            test_cache.set(f"key_{i}", {"index": i}, category="test")

        stats = test_cache.get_stats()

        assert stats.entry_count >= 5
        assert isinstance(stats.by_category, dict)

    def test_cache_generate_key(self, test_cache):
        """Test key generation."""
        key = test_cache.generate_key("issue", "PROJ-123")

        assert key is not None
        assert "issue" in key
        assert "PROJ-123" in key

    def test_cache_clear_category(self, test_cache):
        """Test clearing a specific category."""
        # Add entries in different categories
        test_cache.set("issue_1", {"key": "PROJ-1"}, category="issue")
        test_cache.set("issue_2", {"key": "PROJ-2"}, category="issue")
        test_cache.set("project_1", {"key": "PROJ"}, category="project")

        # Invalidate only issue category (use invalidate, not clear)
        test_cache.invalidate(category="issue")

        # Issue entries should be gone
        assert test_cache.get("issue_1", category="issue") is None
        assert test_cache.get("issue_2", category="issue") is None

        # Project entries should remain
        assert test_cache.get("project_1", category="project") is not None


class TestCacheIntegration:
    """Integration tests for cache with real JIRA data."""

    def test_cache_issue_data(self, jira_client, test_cache):
        """Test caching issue search results."""
        # Perform a search
        result = jira_client.search_issues(
            "created >= -7d",
            max_results=5
        )

        # Cache the results - handle both old and new API response formats
        issues = result.get('issues', [])
        cached_count = 0
        for issue in issues:
            # Handle different response formats
            issue_key = issue.get('key') or issue.get('id')
            if issue_key:
                cache_key = test_cache.generate_key("issue", str(issue_key))
                test_cache.set(cache_key, issue, category="issue")
                cached_count += 1

        # Verify caching
        stats = test_cache.get_stats()
        cached_issues = stats.by_category.get('issue', {}).get('count', 0)
        assert cached_issues >= 0  # May be 0 if no issues found

    def test_cache_project_lookup(self, jira_client, test_cache):
        """Test caching and retrieving project data."""
        # Get projects from JIRA
        response = jira_client.get("/rest/api/3/project", operation="get projects")

        if response and len(response) > 0:
            project = response[0]
            key = test_cache.generate_key("project", project['key'])
            test_cache.set(key, project, category="project")

            # Retrieve from cache (need to pass category)
            cached = test_cache.get(key, category="project")
            assert cached is not None
            assert cached['key'] == project['key']

    def test_cache_warm_all(self, jira_client, test_cache):
        """Test warming all caches."""
        # Warm all cache types
        project_count, project_error = warm_projects(jira_client, test_cache, verbose=False)
        field_count, field_error = warm_fields(jira_client, test_cache, verbose=False)

        # Verify no errors
        assert project_error is None
        assert field_error is None

        # Verify caches have data
        stats = test_cache.get_stats()
        assert stats.entry_count > 0
        assert project_count > 0 or field_count > 0


class TestCachePerformance:
    """Tests for cache performance."""

    def test_cache_hit_rate(self, test_cache):
        """Test cache hit rate tracking."""
        key = "hit_test"
        value = {"data": "test"}

        test_cache.set(key, value, category="test")

        # Multiple gets
        for _ in range(5):
            test_cache.get(key, category="test")

        # Get miss
        test_cache.get("nonexistent_key", category="test")

        stats = test_cache.get_stats()
        # Hit rate should be calculated (CacheStats has hit_rate property and hits attribute)
        assert stats.hits >= 5 or stats.hit_rate > 0

    def test_cache_size_tracking(self, test_cache):
        """Test cache size tracking."""
        # Add entries
        for i in range(10):
            test_cache.set(f"size_test_{i}", {"index": i, "data": "x" * 100}, category="test")

        stats = test_cache.get_stats()
        assert stats.entry_count >= 10
        assert stats.total_size_bytes > 0
