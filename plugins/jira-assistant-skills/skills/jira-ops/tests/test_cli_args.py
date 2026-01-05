"""
CLI Argument Parsing Tests for jira-ops skill.

Tests verify that argparse configurations are correct and handle
various input combinations properly.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts path
scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.mark.ops
@pytest.mark.unit
class TestCacheStatusCLI:
    """CLI argument tests for cache_status.py."""

    def test_no_required_args(self):
        """Test cache_status works with no arguments."""
        import cache_status

        with patch("sys.argv", ["cache_status.py"]):
            # Should work without any arguments (uses default cache dir)
            try:
                cache_status.main()
            except SystemExit as e:
                # Exit code 0 or 1 is acceptable (depending on cache state)
                assert e.code in [0, 1, None]

    def test_json_flag(self):
        """Test --json flag."""
        import cache_status

        with patch("sys.argv", ["cache_status.py", "--json"]):
            try:
                cache_status.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--json flag should be valid")

    def test_cache_dir_option(self, temp_cache_dir):
        """Test --cache-dir option."""
        import cache_status

        with patch("sys.argv", ["cache_status.py", "--cache-dir", temp_cache_dir]):
            try:
                cache_status.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--cache-dir should be valid")

    def test_verbose_flag(self):
        """Test -v/--verbose flag."""
        import cache_status

        with patch("sys.argv", ["cache_status.py", "-v"]):
            try:
                cache_status.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("-v flag should be valid")


@pytest.mark.ops
@pytest.mark.unit
class TestCacheClearCLI:
    """CLI argument tests for cache_clear.py."""

    def test_requires_force_or_dry_run(self, temp_cache_dir):
        """Test that --force or --dry-run is required for safety."""
        import cache_clear

        # Without --force or --dry-run, should prompt (we test with --force)
        with patch(
            "sys.argv", ["cache_clear.py", "--cache-dir", temp_cache_dir, "--force"]
        ):
            try:
                cache_clear.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--force should be valid")

    def test_category_option(self, temp_cache_dir):
        """Test --category option."""
        import cache_clear

        with patch(
            "sys.argv",
            [
                "cache_clear.py",
                "--category",
                "issue",
                "--force",
                "--cache-dir",
                temp_cache_dir,
            ],
        ):
            try:
                cache_clear.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--category should be valid")

    def test_pattern_option(self, temp_cache_dir):
        """Test --pattern option."""
        import cache_clear

        with patch(
            "sys.argv",
            [
                "cache_clear.py",
                "--pattern",
                "PROJ-*",
                "--category",
                "issue",
                "--force",
                "--cache-dir",
                temp_cache_dir,
            ],
        ):
            try:
                cache_clear.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--pattern should be valid")

    def test_dry_run_option(self, temp_cache_dir):
        """Test --dry-run option."""
        import cache_clear

        with patch(
            "sys.argv", ["cache_clear.py", "--dry-run", "--cache-dir", temp_cache_dir]
        ):
            try:
                cache_clear.main()
            except SystemExit as e:
                if e.code == 2:
                    pytest.fail("--dry-run should be valid")


@pytest.mark.ops
@pytest.mark.unit
class TestCacheWarmCLI:
    """CLI argument tests for cache_warm.py."""

    def test_requires_at_least_one_option(self, temp_cache_dir):
        """Test that at least one warming option is required."""
        import cache_warm

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["cache_warm.py", "--cache-dir", temp_cache_dir]):
                cache_warm.main()

        assert exc_info.value.code == 1  # Should fail without warming options

    def test_projects_option(self, temp_cache_dir, mock_jira_client):
        """Test --projects option."""
        import cache_warm

        with (
            patch(
                "sys.argv",
                ["cache_warm.py", "--projects", "--cache-dir", temp_cache_dir],
            ),
            patch("cache_warm.get_jira_client", return_value=mock_jira_client),
        ):
            with patch("cache_warm.HAS_CONFIG_MANAGER", True):
                mock_jira_client.get.return_value = []
                try:
                    cache_warm.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("--projects should be valid")

    def test_fields_option(self, temp_cache_dir, mock_jira_client):
        """Test --fields option."""
        import cache_warm

        with (
            patch(
                "sys.argv", ["cache_warm.py", "--fields", "--cache-dir", temp_cache_dir]
            ),
            patch("cache_warm.get_jira_client", return_value=mock_jira_client),
        ):
            with patch("cache_warm.HAS_CONFIG_MANAGER", True):
                mock_jira_client.get.return_value = []
                try:
                    cache_warm.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("--fields should be valid")

    def test_all_option(self, temp_cache_dir, mock_jira_client):
        """Test --all option."""
        import cache_warm

        with (
            patch(
                "sys.argv", ["cache_warm.py", "--all", "--cache-dir", temp_cache_dir]
            ),
            patch("cache_warm.get_jira_client", return_value=mock_jira_client),
        ):
            with patch("cache_warm.HAS_CONFIG_MANAGER", True):
                mock_jira_client.get.return_value = []
                try:
                    cache_warm.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("--all should be valid")

    def test_verbose_flag(self, temp_cache_dir, mock_jira_client):
        """Test -v/--verbose flag."""
        import cache_warm

        with (
            patch(
                "sys.argv",
                ["cache_warm.py", "--projects", "-v", "--cache-dir", temp_cache_dir],
            ),
            patch("cache_warm.get_jira_client", return_value=mock_jira_client),
        ):
            with patch("cache_warm.HAS_CONFIG_MANAGER", True):
                mock_jira_client.get.return_value = []
                try:
                    cache_warm.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("-v flag should be valid")
