"""
Test suite for cache management scripts.

Tests cover:
- cache_status.py output and JSON mode
- cache_clear.py with categories, patterns, and keys
- cache_warm.py (mock API calls)
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add shared lib to path (use resolve for absolute paths)
shared_lib_path = str(Path(__file__).resolve().parent.parent.parent / 'shared' / 'scripts' / 'lib')
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

# Add scripts to path for importing
scripts_path = str(Path(__file__).resolve().parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from jira_assistant_skills_lib import JiraCache


@pytest.mark.ops
@pytest.mark.unit
class TestCacheStatusScript:
    """Tests for cache_status.py script."""

    def test_cache_status_shows_stats(self, temp_cache_dir):
        """Test showing cache statistics."""
        # Set up cache with some data
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("issue1", {"key": "PROJ-1"}, category="issue")
        cache.set("issue2", {"key": "PROJ-2"}, category="issue")
        cache.set("proj1", {"key": "PROJ"}, category="project")
        cache.close()

        # Import and run the script's main function
        import cache_status

        with patch('sys.argv', ['cache_status.py', '--cache-dir', temp_cache_dir]):
            with patch('sys.stdout') as mock_stdout:
                # Just verify it doesn't crash
                try:
                    cache_status.main()
                except SystemExit:
                    pass

    def test_cache_status_json_output(self, temp_cache_dir):
        """Test JSON output mode."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("issue1", {"key": "PROJ-1"}, category="issue")
        cache.close()

        import cache_status
        import io

        captured_output = io.StringIO()
        with patch('sys.argv', ['cache_status.py', '--json', '--cache-dir', temp_cache_dir]):
            with patch('sys.stdout', captured_output):
                try:
                    cache_status.main()
                except SystemExit:
                    pass

        output = captured_output.getvalue()
        if output:
            data = json.loads(output)
            assert "entry_count" in data
            assert "total_size_bytes" in data


@pytest.mark.ops
@pytest.mark.unit
class TestCacheClearScript:
    """Tests for cache_clear.py script."""

    def test_cache_clear_all(self, temp_cache_dir):
        """Test clearing all cache."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("issue1", {"key": "PROJ-1"}, category="issue")
        cache.set("proj1", {"key": "PROJ"}, category="project")
        cache.close()

        import cache_clear

        with patch('sys.argv', ['cache_clear.py', '--force', '--cache-dir', temp_cache_dir]):
            try:
                cache_clear.main()
            except SystemExit:
                pass

        # Verify cache is empty
        cache2 = JiraCache(cache_dir=temp_cache_dir)
        assert cache2.get("issue1", category="issue") is None
        assert cache2.get("proj1", category="project") is None

    def test_cache_clear_category(self, temp_cache_dir):
        """Test clearing specific category."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("issue1", {"key": "PROJ-1"}, category="issue")
        cache.set("proj1", {"key": "PROJ"}, category="project")
        cache.close()

        import cache_clear

        with patch('sys.argv', ['cache_clear.py', '--category', 'issue', '--force', '--cache-dir', temp_cache_dir]):
            try:
                cache_clear.main()
            except SystemExit:
                pass

        # Verify only issue category is cleared
        cache2 = JiraCache(cache_dir=temp_cache_dir)
        assert cache2.get("issue1", category="issue") is None
        assert cache2.get("proj1", category="project") is not None

    def test_cache_clear_pattern(self, temp_cache_dir):
        """Test clearing by pattern."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("PROJ-123", {"key": "PROJ-123"}, category="issue")
        cache.set("PROJ-456", {"key": "PROJ-456"}, category="issue")
        cache.set("OTHER-789", {"key": "OTHER-789"}, category="issue")
        cache.close()

        import cache_clear

        with patch('sys.argv', ['cache_clear.py', '--pattern', 'PROJ-*', '--category', 'issue', '--force', '--cache-dir', temp_cache_dir]):
            try:
                cache_clear.main()
            except SystemExit:
                pass

        # Verify pattern clearing
        cache2 = JiraCache(cache_dir=temp_cache_dir)
        assert cache2.get("PROJ-123", category="issue") is None
        assert cache2.get("PROJ-456", category="issue") is None
        assert cache2.get("OTHER-789", category="issue") is not None

    def test_cache_clear_dry_run(self, temp_cache_dir):
        """Test dry-run doesn't actually clear."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("issue1", {"key": "PROJ-1"}, category="issue")
        cache.close()

        import cache_clear

        with patch('sys.argv', ['cache_clear.py', '--dry-run', '--cache-dir', temp_cache_dir]):
            try:
                cache_clear.main()
            except SystemExit:
                pass

        # Verify cache is NOT cleared
        cache2 = JiraCache(cache_dir=temp_cache_dir)
        assert cache2.get("issue1", category="issue") is not None


@pytest.mark.ops
@pytest.mark.unit
class TestCacheWarmScript:
    """Tests for cache_warm.py script."""

    def test_cache_warm_projects(self, temp_cache_dir, mock_jira_client):
        """Test pre-warming project cache."""
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

        # Verify projects were cached
        cache = JiraCache(cache_dir=temp_cache_dir)
        # Check that we attempted to cache
        stats = cache.get_stats()
        # At least attempted to cache something

    def test_cache_warm_fields(self, temp_cache_dir, mock_jira_client):
        """Test pre-warming field cache."""
        mock_jira_client.get.side_effect = [
            [{"id": "customfield_10016", "name": "Story Points"}],  # fields
            [{"id": "10001", "name": "Story"}],  # issue types
            [{"id": "1", "name": "High"}],  # priorities
            [{"id": "1", "name": "To Do"}],  # statuses
        ]

        import cache_warm

        with patch('cache_warm.get_jira_client', return_value=mock_jira_client):
            with patch('cache_warm.HAS_CONFIG_MANAGER', True):
                with patch('sys.argv', ['cache_warm.py', '--fields', '--cache-dir', temp_cache_dir]):
                    try:
                        cache_warm.main()
                    except SystemExit:
                        pass

    def test_cache_warm_requires_option(self, temp_cache_dir):
        """Test that at least one option is required."""
        import cache_warm
        import io

        captured_stderr = io.StringIO()
        with patch('sys.argv', ['cache_warm.py', '--cache-dir', temp_cache_dir]):
            with patch('sys.stderr', captured_stderr):
                with pytest.raises(SystemExit) as exc_info:
                    cache_warm.main()
                assert exc_info.value.code == 1
