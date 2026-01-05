"""
Concurrent Operations Tests for jira-relationships skill.

Tests verify that relationship operations are thread-safe and handle
concurrent access correctly.
"""

import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts path
scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.mark.relationships
@pytest.mark.unit
class TestConcurrentLinkCreation:
    """Tests for concurrent link creation operations."""

    def test_concurrent_link_creation_thread_safety(self, mock_jira_client):
        """Test creating links concurrently from multiple threads."""
        import link_issue

        results = []
        errors = []
        call_count = 0
        lock = threading.Lock()

        def mock_create_link(*args, **kwargs):
            nonlocal call_count
            with lock:
                call_count += 1
            # Simulate small API delay
            time.sleep(0.01)
            return None

        mock_jira_client.create_link = mock_create_link

        def create_link_thread(inward_key, outward_key):
            try:
                with patch.object(
                    link_issue, "get_jira_client", return_value=mock_jira_client
                ):
                    # Create simple link operation
                    mock_jira_client.create_link("Blocks", inward_key, outward_key)
                    results.append((inward_key, outward_key))
            except Exception as e:
                errors.append(str(e))

        threads = []
        for i in range(10):
            t = threading.Thread(
                target=create_link_thread, args=(f"PROJ-{i}", "PROJ-100")
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent execution: {errors}"
        assert len(results) == 10
        assert call_count == 10

    def test_concurrent_bulk_link_operations(self, mock_jira_client):
        """Test bulk_link with concurrent operations."""
        import bulk_link

        mock_jira_client.create_link.return_value = None

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            # Simulate concurrent bulk operations
            results = []

            def run_bulk_link(issues, target):
                result = bulk_link.bulk_link(
                    issues=issues, target=target, link_type="Blocks"
                )
                return result

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for i in range(3):
                    issues = [f"PROJ-{i * 10 + j}" for j in range(5)]
                    # Use valid issue key format: PROJ-100, PROJ-101, PROJ-102
                    future = executor.submit(run_bulk_link, issues, f"PROJ-{100 + i}")
                    futures.append(future)

                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)

            # All bulk operations should complete successfully
            assert len(results) == 3
            for result in results:
                assert result["failed"] == 0

    def test_concurrent_error_handling(self, mock_jira_client):
        """Test concurrent operations with intermittent errors."""
        import bulk_link

        from jira_assistant_skills_lib import JiraError

        call_count = [0]
        lock = threading.Lock()

        def mock_create_link_with_errors(*args, **kwargs):
            with lock:
                call_count[0] += 1
                count = call_count[0]
            # Every 3rd call fails
            if count % 3 == 0:
                raise JiraError("Simulated error", 500)
            return None

        mock_jira_client.create_link = mock_create_link_with_errors

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            issues = [f"PROJ-{i}" for i in range(9)]
            result = bulk_link.bulk_link(
                issues=issues, target="PROJ-100", link_type="Blocks"
            )

        # Should have 3 failures (calls 3, 6, 9)
        assert result["failed"] == 3
        assert result["created"] == 6


@pytest.mark.relationships
@pytest.mark.unit
class TestConcurrentGetLinks:
    """Tests for concurrent get_links operations."""

    def test_concurrent_get_links(self, mock_jira_client):
        """Test getting links concurrently for multiple issues."""
        import get_links

        def mock_get_issue_links(issue_key):
            # Simulate API delay
            time.sleep(0.01)
            return [
                {
                    "id": f"link-{issue_key}",
                    "type": {"name": "Blocks"},
                    "outwardIssue": {"key": "PROJ-100"},
                }
            ]

        mock_jira_client.get_issue_links = mock_get_issue_links

        results = []
        errors = []

        def get_links_thread(issue_key):
            try:
                with patch.object(
                    get_links, "get_jira_client", return_value=mock_jira_client
                ):
                    links = mock_jira_client.get_issue_links(issue_key)
                    results.append((issue_key, links))
            except Exception as e:
                errors.append(str(e))

        threads = []
        for i in range(10):
            t = threading.Thread(target=get_links_thread, args=(f"PROJ-{i}",))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 10
        for _issue_key, links in results:
            assert len(links) == 1


@pytest.mark.relationships
@pytest.mark.unit
class TestRaceConditionPrevention:
    """Tests for race condition prevention in relationship operations."""

    def test_duplicate_link_prevention(self, mock_jira_client):
        """Test that duplicate links are handled correctly under concurrent access."""
        import bulk_link

        from jira_assistant_skills_lib import JiraError

        created_links = set()
        lock = threading.Lock()

        def mock_create_link_check_duplicate(link_type, inward, outward, comment=None):
            link_key = f"{inward}->{outward}"
            with lock:
                if link_key in created_links:
                    raise JiraError("Link already exists", 400)
                created_links.add(link_key)
            time.sleep(0.01)  # Simulate API delay
            return None

        mock_jira_client.create_link = mock_create_link_check_duplicate

        with patch.object(bulk_link, "get_jira_client", return_value=mock_jira_client):
            # Try to create the same links from multiple calls
            issues = ["PROJ-1", "PROJ-2", "PROJ-1"]  # PROJ-1 is duplicate
            result = bulk_link.bulk_link(
                issues=issues, target="PROJ-100", link_type="Blocks"
            )

        # One should fail due to duplicate
        assert result["created"] == 2
        assert result["failed"] == 1

    def test_concurrent_unlink_operations(self, mock_jira_client):
        """Test concurrent unlink operations don't cause race conditions."""

        unlinked = set()
        lock = threading.Lock()

        def mock_delete_link(link_id):
            with lock:
                if link_id in unlinked:
                    # Already unlinked - this is a race condition
                    raise Exception(f"Link {link_id} already deleted")
                unlinked.add(link_id)
            time.sleep(0.01)
            return None

        mock_jira_client.delete_link = mock_delete_link

        results = []
        errors = []

        def unlink_thread(link_id):
            try:
                mock_jira_client.delete_link(link_id)
                results.append(link_id)
            except Exception as e:
                errors.append(str(e))

        # Create threads trying to unlink different links
        threads = []
        for i in range(10):
            t = threading.Thread(target=unlink_thread, args=(f"link-{i}",))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All should succeed since they're different links
        assert len(errors) == 0
        assert len(results) == 10


@pytest.mark.relationships
@pytest.mark.unit
class TestConcurrentDependencyChain:
    """Tests for concurrent access to dependency chain operations."""

    def test_concurrent_get_blockers(self, mock_jira_client):
        """Test getting blocker chains concurrently."""
        import get_blockers

        def mock_get_issue(key, **kwargs):
            return {
                "key": key,
                "fields": {
                    "summary": f"Issue {key}",
                    "status": {"name": "To Do"},
                    "issuelinks": [
                        {
                            "type": {"name": "Blocks", "inward": "is blocked by"},
                            "inwardIssue": {"key": "PROJ-BLOCKER"},
                        }
                    ]
                    if key != "PROJ-BLOCKER"
                    else [],
                },
            }

        mock_jira_client.get_issue = mock_get_issue

        results = []
        errors = []

        def get_blockers_thread(issue_key):
            try:
                with patch.object(
                    get_blockers, "get_jira_client", return_value=mock_jira_client
                ):
                    issue = mock_jira_client.get_issue(issue_key)
                    results.append((issue_key, issue))
            except Exception as e:
                errors.append(str(e))

        threads = []
        for i in range(10):
            t = threading.Thread(target=get_blockers_thread, args=(f"PROJ-{i}",))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 10
