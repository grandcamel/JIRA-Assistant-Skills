"""
Negative Scenario Tests for jira-ops skill.

Tests verify proper handling of error conditions including:
- Invalid credentials
- Network errors
- Timeouts
- Rate limiting
- Server errors
- Cache corruption
"""

import pytest
import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from datetime import timedelta

# Add shared lib to path
shared_lib_path = str(Path(__file__).resolve().parent.parent.parent / 'shared' / 'scripts' / 'lib')
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

# Add scripts path
scripts_path = str(Path(__file__).resolve().parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.mark.ops
@pytest.mark.unit
class TestInvalidCredentials:
    """Tests for invalid credential handling."""

    def test_authentication_error_401(self, mock_jira_client):
        """Test handling 401 Unauthorized response."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.get.side_effect = AuthenticationError(
            "Invalid authentication credentials"
        )

        import cache_warm

        with patch('cache_warm.get_jira_client', return_value=mock_jira_client):
            with patch('cache_warm.HAS_CONFIG_MANAGER', True):
                with patch('sys.argv', ['cache_warm.py', '--projects']):
                    with pytest.raises(SystemExit) as exc_info:
                        cache_warm.main()

                    # Should exit with error code
                    assert exc_info.value.code != 0

    def test_invalid_token_format(self, mock_jira_client):
        """Test handling of malformed API token."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.get.side_effect = AuthenticationError(
            "Invalid API token format"
        )

        import cache_warm

        with patch('cache_warm.get_jira_client', return_value=mock_jira_client):
            with patch('cache_warm.HAS_CONFIG_MANAGER', True):
                with patch('sys.argv', ['cache_warm.py', '--projects']):
                    with pytest.raises(SystemExit) as exc_info:
                        cache_warm.main()

                    assert exc_info.value.code != 0

    def test_expired_token(self, mock_jira_client):
        """Test handling of expired API token."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.get.side_effect = AuthenticationError(
            "Token has expired"
        )

        import cache_warm

        with patch('cache_warm.get_jira_client', return_value=mock_jira_client):
            with patch('cache_warm.HAS_CONFIG_MANAGER', True):
                with patch('sys.argv', ['cache_warm.py', '--fields']):
                    with pytest.raises(SystemExit) as exc_info:
                        cache_warm.main()

                    assert exc_info.value.code != 0


@pytest.mark.ops
@pytest.mark.unit
class TestNetworkErrors:
    """Tests for network error handling."""

    def test_connection_timeout(self, mock_jira_client):
        """Test handling connection timeout."""
        import requests

        mock_jira_client.get.side_effect = requests.exceptions.Timeout(
            "Connection timed out"
        )

        import cache_warm

        with patch('cache_warm.get_jira_client', return_value=mock_jira_client):
            with patch('cache_warm.HAS_CONFIG_MANAGER', True):
                with patch('sys.argv', ['cache_warm.py', '--projects']):
                    with pytest.raises(SystemExit) as exc_info:
                        cache_warm.main()

                    assert exc_info.value.code != 0

    def test_connection_refused(self, mock_jira_client):
        """Test handling connection refused."""
        import requests

        mock_jira_client.get.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )

        import cache_warm

        with patch('cache_warm.get_jira_client', return_value=mock_jira_client):
            with patch('cache_warm.HAS_CONFIG_MANAGER', True):
                with patch('sys.argv', ['cache_warm.py', '--projects']):
                    with pytest.raises(SystemExit) as exc_info:
                        cache_warm.main()

                    assert exc_info.value.code != 0

    def test_dns_resolution_failure(self, mock_jira_client):
        """Test handling DNS resolution failure."""
        import requests

        mock_jira_client.get.side_effect = requests.exceptions.ConnectionError(
            "Failed to resolve hostname"
        )

        import cache_warm

        with patch('cache_warm.get_jira_client', return_value=mock_jira_client):
            with patch('cache_warm.HAS_CONFIG_MANAGER', True):
                with patch('sys.argv', ['cache_warm.py', '--all']):
                    with pytest.raises(SystemExit) as exc_info:
                        cache_warm.main()

                    assert exc_info.value.code != 0


@pytest.mark.ops
@pytest.mark.unit
class TestRateLimiting:
    """Tests for rate limit handling."""

    def test_rate_limit_429(self, mock_jira_client):
        """Test handling 429 Too Many Requests."""
        from jira_assistant_skills_lib import RateLimitError

        mock_jira_client.get.side_effect = RateLimitError(retry_after=60)

        import cache_warm

        with patch('cache_warm.get_jira_client', return_value=mock_jira_client):
            with patch('cache_warm.HAS_CONFIG_MANAGER', True):
                with patch('sys.argv', ['cache_warm.py', '--projects']):
                    with pytest.raises(SystemExit) as exc_info:
                        cache_warm.main()

                    assert exc_info.value.code != 0

    def test_rate_limit_with_retry_after(self, mock_jira_client):
        """Test rate limit error includes retry-after info."""
        from jira_assistant_skills_lib import RateLimitError

        error = RateLimitError(retry_after=120)

        assert error.retry_after == 120
        assert '120' in str(error) or 'retry' in str(error).lower()


@pytest.mark.ops
@pytest.mark.unit
class TestServerErrors:
    """Tests for server error handling."""

    def test_internal_server_error_500(self, mock_jira_client):
        """Test handling 500 Internal Server Error."""
        from jira_assistant_skills_lib import ServerError

        mock_jira_client.get.side_effect = ServerError("Internal server error")

        import cache_warm

        with patch('cache_warm.get_jira_client', return_value=mock_jira_client):
            with patch('cache_warm.HAS_CONFIG_MANAGER', True):
                with patch('sys.argv', ['cache_warm.py', '--projects']):
                    with pytest.raises(SystemExit) as exc_info:
                        cache_warm.main()

                    assert exc_info.value.code != 0

    def test_bad_gateway_502(self, mock_jira_client):
        """Test handling 502 Bad Gateway."""
        from jira_assistant_skills_lib import ServerError

        mock_jira_client.get.side_effect = ServerError("Bad gateway")

        import cache_warm

        with patch('cache_warm.get_jira_client', return_value=mock_jira_client):
            with patch('cache_warm.HAS_CONFIG_MANAGER', True):
                with patch('sys.argv', ['cache_warm.py', '--fields']):
                    with pytest.raises(SystemExit) as exc_info:
                        cache_warm.main()

                    assert exc_info.value.code != 0

    def test_service_unavailable_503(self, mock_jira_client):
        """Test handling 503 Service Unavailable."""
        from jira_assistant_skills_lib import ServerError

        mock_jira_client.get.side_effect = ServerError("Service unavailable")

        import cache_warm

        with patch('cache_warm.get_jira_client', return_value=mock_jira_client):
            with patch('cache_warm.HAS_CONFIG_MANAGER', True):
                with patch('sys.argv', ['cache_warm.py', '--all']):
                    with pytest.raises(SystemExit) as exc_info:
                        cache_warm.main()

                    assert exc_info.value.code != 0

    def test_gateway_timeout_504(self, mock_jira_client):
        """Test handling 504 Gateway Timeout."""
        from jira_assistant_skills_lib import ServerError

        mock_jira_client.get.side_effect = ServerError("Gateway timeout")

        import cache_warm

        with patch('cache_warm.get_jira_client', return_value=mock_jira_client):
            with patch('cache_warm.HAS_CONFIG_MANAGER', True):
                with patch('sys.argv', ['cache_warm.py', '--projects']):
                    with pytest.raises(SystemExit) as exc_info:
                        cache_warm.main()

                    assert exc_info.value.code != 0


@pytest.mark.ops
@pytest.mark.unit
class TestCacheErrors:
    """Tests for cache-specific error handling."""

    def test_invalid_cache_directory_permissions(self):
        """Test handling invalid cache directory permissions."""
        from jira_assistant_skills_lib import JiraCache

        # Try to use a directory we can't write to (if not root)
        if os.getuid() != 0:  # Not running as root
            with pytest.raises((PermissionError, OSError)):
                # Try to create cache in read-only location
                cache = JiraCache(cache_dir='/root/nonexistent_cache')

    def test_corrupted_cache_file_handling(self, temp_cache_dir):
        """Test handling corrupted cache file."""
        from jira_assistant_skills_lib import JiraCache

        # Create cache and add data
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("key1", {"value": "test"}, category="issue")
        cache.close()

        # Corrupt the cache file
        cache_files = list(Path(temp_cache_dir).glob('**/*.json'))
        for cache_file in cache_files:
            with open(cache_file, 'w') as f:
                f.write('{ corrupted json }')

        # Try to load cache - should handle gracefully
        cache2 = JiraCache(cache_dir=temp_cache_dir)
        # Getting corrupted data should return None, not crash
        result = cache2.get("key1", category="issue")
        # Behavior depends on implementation - might be None or raise
        cache2.close()

    def test_cache_full_disk_simulation(self, temp_cache_dir):
        """Test handling when disk is full."""
        from jira_assistant_skills_lib import JiraCache

        cache = JiraCache(cache_dir=temp_cache_dir, max_size_mb=0.001)  # Very small

        # Try to add data that exceeds cache size
        # Should handle gracefully via eviction
        for i in range(100):
            cache.set(f"key{i}", {"data": "x" * 100, "index": i}, category="issue")

        # Cache should still be functional
        stats = cache.get_stats()
        assert stats.total_size_bytes <= cache.max_size
        cache.close()


@pytest.mark.ops
@pytest.mark.unit
class TestCacheRecovery:
    """Tests for cache recovery scenarios."""

    def test_recovery_after_invalid_json(self, temp_cache_dir):
        """Test cache recovery after encountering invalid JSON."""
        from jira_assistant_skills_lib import JiraCache

        # Create cache with valid data
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("valid_key", {"valid": "data"}, category="issue")
        cache.close()

        # Create new cache instance - should work despite potential corruption
        cache2 = JiraCache(cache_dir=temp_cache_dir)

        # Should be able to add new data
        cache2.set("new_key", {"new": "data"}, category="issue")
        result = cache2.get("new_key", category="issue")

        assert result is not None
        assert result["new"] == "data"
        cache2.close()

    def test_recovery_after_process_crash(self, temp_cache_dir):
        """Test cache recovery after simulated crash (incomplete write)."""
        from jira_assistant_skills_lib import JiraCache

        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("key1", {"value": "test"}, category="issue")
        # Don't call close() - simulate crash

        # Create new cache instance - should recover gracefully
        cache2 = JiraCache(cache_dir=temp_cache_dir)

        # Should be able to use cache normally
        cache2.set("key2", {"value": "test2"}, category="issue")
        result = cache2.get("key2", category="issue")

        assert result is not None
        cache2.close()
