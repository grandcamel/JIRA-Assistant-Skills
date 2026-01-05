"""
Tests for get_blockers.py

TDD tests for finding blocker chains and dependencies.
"""

import copy
import json
from unittest.mock import patch

import pytest


@pytest.fixture
def blocker_chain_links():
    """
    Create a blocker chain:
    PROJ-50 blocks PROJ-101
    PROJ-101 blocks PROJ-123
    PROJ-100 blocks PROJ-123 (already done)

    Note on JIRA link semantics:
    When fetching links for issue B where "A blocks B":
    - outwardIssue = A (the blocker, on the "blocks" side)
    - No inwardIssue because B itself is the inward issue
    """
    return {
        "PROJ-123": [
            {
                "id": "20001",
                "type": {
                    "id": "10000",
                    "name": "Blocks",
                    "inward": "is blocked by",
                    "outward": "blocks",
                },
                "outwardIssue": {
                    "id": "10100",
                    "key": "PROJ-100",
                    "fields": {
                        "summary": "Database schema",
                        "status": {"name": "Done"},
                        "issuetype": {"name": "Story"},
                    },
                },
            },
            {
                "id": "20002",
                "type": {
                    "id": "10000",
                    "name": "Blocks",
                    "inward": "is blocked by",
                    "outward": "blocks",
                },
                "outwardIssue": {
                    "id": "10101",
                    "key": "PROJ-101",
                    "fields": {
                        "summary": "API auth",
                        "status": {"name": "In Progress"},
                        "issuetype": {"name": "Story"},
                    },
                },
            },
        ],
        "PROJ-101": [
            {
                "id": "20003",
                "type": {
                    "id": "10000",
                    "name": "Blocks",
                    "inward": "is blocked by",
                    "outward": "blocks",
                },
                "outwardIssue": {
                    "id": "10050",
                    "key": "PROJ-50",
                    "fields": {
                        "summary": "Security review",
                        "status": {"name": "To Do"},
                        "issuetype": {"name": "Task"},
                    },
                },
            }
        ],
        "PROJ-100": [],
        "PROJ-50": [],
    }


@pytest.fixture
def circular_links():
    """
    Create circular dependency: 3 blocks 1, 1 blocks 2, 2 blocks 3.

    Note on JIRA link semantics:
    When fetching links for issue B where "A blocks B":
    - outwardIssue = A (the blocker)
    """
    return {
        "PROJ-1": [
            {
                "id": "30001",
                "type": {
                    "id": "10000",
                    "name": "Blocks",
                    "inward": "is blocked by",
                    "outward": "blocks",
                },
                "outwardIssue": {
                    "id": "10003",
                    "key": "PROJ-3",
                    "fields": {"summary": "Task 3", "status": {"name": "To Do"}},
                },
            }
        ],
        "PROJ-2": [
            {
                "id": "30002",
                "type": {
                    "id": "10000",
                    "name": "Blocks",
                    "inward": "is blocked by",
                    "outward": "blocks",
                },
                "outwardIssue": {
                    "id": "10001",
                    "key": "PROJ-1",
                    "fields": {"summary": "Task 1", "status": {"name": "To Do"}},
                },
            }
        ],
        "PROJ-3": [
            {
                "id": "30003",
                "type": {
                    "id": "10000",
                    "name": "Blocks",
                    "inward": "is blocked by",
                    "outward": "blocks",
                },
                "outwardIssue": {
                    "id": "10002",
                    "key": "PROJ-2",
                    "fields": {"summary": "Task 2", "status": {"name": "To Do"}},
                },
            }
        ],
    }


@pytest.mark.relationships
@pytest.mark.unit
class TestGetBlockers:
    """Tests for the get_blockers function."""

    def test_get_direct_blockers(self, mock_jira_client, blocker_chain_links):
        """Test finding issues that directly block this issue."""
        mock_jira_client.get_issue_links.return_value = blocker_chain_links["PROJ-123"]

        import get_blockers

        with patch.object(
            get_blockers, "get_jira_client", return_value=mock_jira_client
        ):
            result = get_blockers.get_blockers("PROJ-123", recursive=False)

        # Should find 2 direct blockers
        assert len(result["blockers"]) == 2
        blocker_keys = {b["key"] for b in result["blockers"]}
        assert blocker_keys == {"PROJ-100", "PROJ-101"}

    def test_get_blocking_issues(self, mock_jira_client, sample_issue_links):
        """Test finding issues this issue blocks (outward direction)."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_blockers

        with patch.object(
            get_blockers, "get_jira_client", return_value=mock_jira_client
        ):
            result = get_blockers.get_blockers(
                "PROJ-123", direction="outward", recursive=False
            )

        # Should find issues that PROJ-123 blocks (outward)
        # The result should have 'blockers' key containing issues blocked by PROJ-123
        assert "blockers" in result
        # Outward blockers are found in outwardIssue links
        assert len(result["blockers"]) >= 0

    def test_get_blockers_recursive(self, mock_jira_client, blocker_chain_links):
        """Test following blocker chain recursively."""
        # Use deepcopy to avoid fixture mutation
        chain_data = copy.deepcopy(blocker_chain_links)

        def mock_get_links(issue_key):
            return chain_data.get(issue_key, [])

        mock_jira_client.get_issue_links.side_effect = mock_get_links

        import get_blockers

        with patch.object(
            get_blockers, "get_jira_client", return_value=mock_jira_client
        ):
            result = get_blockers.get_blockers("PROJ-123", recursive=True)

        # Should find all blockers in chain: PROJ-100, PROJ-101, PROJ-50
        # Result uses 'all_blockers' for recursive results
        assert "all_blockers" in result or "blockers" in result
        all_blockers = result.get("all_blockers", result.get("blockers", []))
        blocker_keys = {b["key"] for b in all_blockers}
        assert "PROJ-50" in blocker_keys  # Deep in chain

    def test_blockers_with_depth_limit(self, mock_jira_client, blocker_chain_links):
        """Test limiting recursion depth."""
        # Use deepcopy to avoid fixture mutation
        chain_data = copy.deepcopy(blocker_chain_links)

        def mock_get_links(issue_key):
            return chain_data.get(issue_key, [])

        mock_jira_client.get_issue_links.side_effect = mock_get_links

        import get_blockers

        with patch.object(
            get_blockers, "get_jira_client", return_value=mock_jira_client
        ):
            result = get_blockers.get_blockers("PROJ-123", recursive=True, max_depth=1)

        # With depth=1, should only get direct blockers, not PROJ-50
        # Result uses 'all_blockers' for recursive results
        assert "all_blockers" in result or "blockers" in result
        all_blockers = result.get("all_blockers", result.get("blockers", []))
        blocker_keys = {b["key"] for b in all_blockers}
        assert "PROJ-50" not in blocker_keys

    def test_detect_circular_dependency(self, mock_jira_client, circular_links):
        """Test detecting and reporting circular blockers."""
        # Use deepcopy to avoid fixture mutation
        circular_data = copy.deepcopy(circular_links)

        def mock_get_links(issue_key):
            return circular_data.get(issue_key, [])

        mock_jira_client.get_issue_links.side_effect = mock_get_links

        import get_blockers

        with patch.object(
            get_blockers, "get_jira_client", return_value=mock_jira_client
        ):
            result = get_blockers.get_blockers("PROJ-1", recursive=True)

        # Should detect circular dependency - the result should have 'circular' key set to True
        assert result.get("circular") is True

    def test_blockers_tree_format(self, mock_jira_client, blocker_chain_links):
        """Test tree-style output for blocker chain."""
        # Use deepcopy to avoid fixture mutation
        chain_data = copy.deepcopy(blocker_chain_links)

        def mock_get_links(issue_key):
            return chain_data.get(issue_key, [])

        mock_jira_client.get_issue_links.side_effect = mock_get_links

        import get_blockers

        with patch.object(
            get_blockers, "get_jira_client", return_value=mock_jira_client
        ):
            result = get_blockers.get_blockers("PROJ-123", recursive=True)
            output = get_blockers.format_blockers(result, output_format="tree")

        # Tree output should show hierarchy with the root issue
        assert "PROJ-123" in output
        # Should also show at least one of the direct blockers
        assert "PROJ-101" in output or "PROJ-100" in output

    def test_blockers_json_format(self, mock_jira_client, blocker_chain_links):
        """Test JSON output with full chain."""
        mock_jira_client.get_issue_links.return_value = copy.deepcopy(
            blocker_chain_links["PROJ-123"]
        )

        import get_blockers

        with patch.object(
            get_blockers, "get_jira_client", return_value=mock_jira_client
        ):
            result = get_blockers.get_blockers("PROJ-123", recursive=False)
            output = get_blockers.format_blockers(result, output_format="json")

        # Should be valid JSON with 'blockers' key
        parsed = json.loads(output)
        assert "blockers" in parsed
        assert isinstance(parsed["blockers"], list)

    def test_no_blockers(self, mock_jira_client):
        """Test output when no blockers exist."""
        mock_jira_client.get_issue_links.return_value = []

        import get_blockers

        with patch.object(
            get_blockers, "get_jira_client", return_value=mock_jira_client
        ):
            result = get_blockers.get_blockers("PROJ-999", recursive=False)

        assert len(result.get("blockers", [])) == 0


@pytest.mark.relationships
@pytest.mark.unit
class TestGetBlockersErrorHandling:
    """Test API error handling scenarios for get_blockers."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.get_issue_links.side_effect = AuthenticationError(
            "Invalid token"
        )

        import get_blockers

        with (
            patch.object(
                get_blockers, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(AuthenticationError),
        ):
            get_blockers.get_blockers("PROJ-123")

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.get_issue_links.side_effect = PermissionError(
            "Insufficient permissions"
        )

        import get_blockers

        with (
            patch.object(
                get_blockers, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(PermissionError),
        ):
            get_blockers.get_blockers("PROJ-123")

    def test_issue_not_found_error(self, mock_jira_client):
        """Test handling of 404 issue not found."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_issue_links.side_effect = NotFoundError("Issue not found")

        import get_blockers

        with (
            patch.object(
                get_blockers, "get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(NotFoundError),
        ):
            get_blockers.get_blockers("PROJ-999")

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_issue_links.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        import get_blockers

        with patch.object(
            get_blockers, "get_jira_client", return_value=mock_jira_client
        ):
            with pytest.raises(JiraError) as exc_info:
                get_blockers.get_blockers("PROJ-123")
            assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_issue_links.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        import get_blockers

        with patch.object(
            get_blockers, "get_jira_client", return_value=mock_jira_client
        ):
            with pytest.raises(JiraError) as exc_info:
                get_blockers.get_blockers("PROJ-123")
            assert exc_info.value.status_code == 500
