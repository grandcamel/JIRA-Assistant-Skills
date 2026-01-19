"""
Test utilities for JIRA live integration tests.

Provides:
- IssueBuilder: Fluent API for creating test issues
- Assertion helpers for search results
- Version detection utilities
"""

import random
import string
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


class IssueBuilder:
    """
    Fluent API for building test issues.

    Example:
        issue = (IssueBuilder(client, "PROJ")
            .with_summary("Test issue")
            .with_type("Bug")
            .with_priority("High")
            .with_labels(["test", "urgent"])
            .build())
    """

    def __init__(self, client, project_key: str):
        """
        Initialize builder.

        Args:
            client: JiraClient instance
            project_key: Project key to create issues in
        """
        self._client = client
        self._project_key = project_key
        self._fields: Dict[str, Any] = {
            "project": {"key": project_key},
            "issuetype": {"name": "Task"},
            "labels": ["test", "automated"],
        }
        self._link_to: Optional[Tuple[str, str]] = None

    def with_summary(self, summary: str) -> "IssueBuilder":
        """Set issue summary."""
        self._fields["summary"] = summary
        return self

    def with_type(self, issue_type: str) -> "IssueBuilder":
        """Set issue type (Task, Bug, Story, Epic, etc.)."""
        self._fields["issuetype"] = {"name": issue_type}
        return self

    def with_priority(self, priority: str) -> "IssueBuilder":
        """Set priority (Highest, High, Medium, Low, Lowest)."""
        self._fields["priority"] = {"name": priority}
        return self

    def with_description(self, description: str) -> "IssueBuilder":
        """Set issue description (plain text, auto-converted to ADF)."""
        self._fields["description"] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}],
                }
            ],
        }
        return self

    def with_labels(self, labels: List[str]) -> "IssueBuilder":
        """Set labels (replaces defaults)."""
        self._fields["labels"] = labels
        return self

    def add_labels(self, labels: List[str]) -> "IssueBuilder":
        """Add labels to existing."""
        current = self._fields.get("labels", [])
        self._fields["labels"] = list(set(current + labels))
        return self

    def with_assignee(self, account_id: str) -> "IssueBuilder":
        """Set assignee by account ID."""
        self._fields["assignee"] = {"accountId": account_id}
        return self

    def with_components(self, component_names: List[str]) -> "IssueBuilder":
        """Set components by name."""
        self._fields["components"] = [{"name": name} for name in component_names]
        return self

    def with_epic(self, epic_key: str) -> "IssueBuilder":
        """Link to epic (for company-managed projects)."""
        # Epic Link field ID varies by instance
        # This is a common default
        self._fields["customfield_10014"] = epic_key
        return self

    def with_story_points(self, points: int) -> "IssueBuilder":
        """Set story points (for Scrum projects)."""
        # Story Points field ID varies by instance
        # This is a common default
        self._fields["customfield_10016"] = points
        return self

    def with_field(self, field_id: str, value: Any) -> "IssueBuilder":
        """Set arbitrary field value."""
        self._fields[field_id] = value
        return self

    def link_to(self, issue_key: str, link_type: str = "Relates") -> "IssueBuilder":
        """Create a link to another issue after creation."""
        self._link_to = (issue_key, link_type)
        return self

    def build(self) -> Dict[str, Any]:
        """
        Create the issue.

        Returns:
            Created issue data
        """
        # Generate summary if not set
        if "summary" not in self._fields:
            self._fields["summary"] = f"[Test] {self._fields['issuetype']['name']} - {_random_suffix()}"

        issue = self._client.post("/rest/api/3/issue", json={"fields": self._fields})

        # Create link if requested
        if self._link_to:
            target_key, link_type = self._link_to
            try:
                self._client.post(
                    "/rest/api/3/issueLink",
                    json={
                        "type": {"name": link_type},
                        "inwardIssue": {"key": issue["key"]},
                        "outwardIssue": {"key": target_key},
                    },
                )
            except Exception:
                pass  # Link creation is best-effort

        return issue


# =============================================================================
# Assertion Helpers
# =============================================================================


def assert_search_returns_results(
    client,
    jql: str,
    min_count: int = 1,
    timeout: int = 10,
) -> List[Dict[str, Any]]:
    """
    Assert that a JQL query returns results.

    Waits for indexing with exponential backoff.

    Args:
        client: JiraClient instance
        jql: JQL query
        min_count: Minimum expected results
        timeout: Maximum seconds to wait

    Returns:
        List of matching issues

    Raises:
        AssertionError: If count not reached
    """
    start = time.time()
    interval = 0.5
    last_count = 0

    while time.time() - start < timeout:
        response = client.post(
            "/rest/api/3/search",
            json={"jql": jql, "maxResults": 100},
        )
        issues = response.get("issues", [])
        last_count = len(issues)

        if last_count >= min_count:
            return issues

        time.sleep(interval)
        interval = min(interval * 1.5, 5.0)  # Exponential backoff, max 5s

    raise AssertionError(
        f"Expected at least {min_count} results for '{jql}', got {last_count}"
    )


def assert_search_returns_empty(
    client,
    jql: str,
    timeout: int = 5,
) -> None:
    """
    Assert that a JQL query returns no results.

    Args:
        client: JiraClient instance
        jql: JQL query
        timeout: Seconds to wait for indexing

    Raises:
        AssertionError: If any results found
    """
    # Wait a bit for indexing, then check
    time.sleep(min(timeout, 2))

    response = client.post(
        "/rest/api/3/search",
        json={"jql": jql, "maxResults": 1},
    )
    count = response.get("total", 0)

    if count > 0:
        raise AssertionError(f"Expected no results for '{jql}', got {count}")


def assert_issue_has_field(
    issue: Dict[str, Any],
    field_name: str,
    expected_value: Any = None,
) -> None:
    """
    Assert that an issue has a field with optional value check.

    Args:
        issue: Issue data dictionary
        field_name: Field to check
        expected_value: Optional expected value

    Raises:
        AssertionError: If field missing or value doesn't match
    """
    fields = issue.get("fields", {})
    if field_name not in fields:
        raise AssertionError(f"Issue {issue.get('key')} missing field '{field_name}'")

    if expected_value is not None:
        actual = fields[field_name]
        # Handle nested objects (e.g., status.name)
        if isinstance(expected_value, dict):
            for k, v in expected_value.items():
                if actual.get(k) != v:
                    raise AssertionError(
                        f"Issue {issue.get('key')} field '{field_name}.{k}' "
                        f"expected '{v}', got '{actual.get(k)}'"
                    )
        elif isinstance(actual, dict) and "name" in actual:
            if actual["name"] != expected_value:
                raise AssertionError(
                    f"Issue {issue.get('key')} field '{field_name}' "
                    f"expected '{expected_value}', got '{actual['name']}'"
                )
        elif actual != expected_value:
            raise AssertionError(
                f"Issue {issue.get('key')} field '{field_name}' "
                f"expected '{expected_value}', got '{actual}'"
            )


# =============================================================================
# Version Detection
# =============================================================================


def get_jira_version(client) -> Tuple[int, int, int]:
    """
    Get JIRA version as tuple.

    Args:
        client: JiraClient instance

    Returns:
        Version tuple (major, minor, patch)
    """
    try:
        info = client.get("/rest/api/3/serverInfo")
    except Exception:
        info = client.get("/rest/api/2/serverInfo")

    version_str = info.get("version", "0.0.0")
    parts = version_str.split(".")
    return (
        int(parts[0]) if len(parts) > 0 else 0,
        int(parts[1]) if len(parts) > 1 else 0,
        int(parts[2].split("-")[0]) if len(parts) > 2 else 0,
    )


def skip_if_version_below(
    client,
    min_version: Tuple[int, int, int],
    reason: str = "",
) -> None:
    """
    Skip test if JIRA version is below minimum.

    Args:
        client: JiraClient instance
        min_version: Minimum version tuple (major, minor, patch)
        reason: Skip reason message

    Raises:
        pytest.skip if version too low
    """
    import pytest

    current = get_jira_version(client)
    if current < min_version:
        min_str = ".".join(str(v) for v in min_version)
        cur_str = ".".join(str(v) for v in current)
        skip_reason = reason or f"Requires JIRA {min_str}+, found {cur_str}"
        pytest.skip(skip_reason)


def is_cloud_instance(client) -> bool:
    """
    Check if connected to JIRA Cloud.

    Returns:
        True if JIRA Cloud, False if DC/Server
    """
    try:
        info = client.get("/rest/api/3/serverInfo")
        return info.get("deploymentType") == "Cloud"
    except Exception:
        return False


# =============================================================================
# Wait Utilities
# =============================================================================


def wait_for_transition(
    client,
    issue_key: str,
    expected_status: str,
    timeout: int = 30,
) -> bool:
    """
    Wait for issue to reach expected status.

    Args:
        client: JiraClient instance
        issue_key: Issue to check
        expected_status: Expected status name
        timeout: Maximum seconds to wait

    Returns:
        True if status reached, False on timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        issue = client.get(f"/rest/api/3/issue/{issue_key}?fields=status")
        current = issue.get("fields", {}).get("status", {}).get("name")
        if current == expected_status:
            return True
        time.sleep(1)
    return False


def wait_for_assignment(
    client,
    issue_key: str,
    expected_assignee: Optional[str] = None,
    timeout: int = 10,
) -> bool:
    """
    Wait for issue to be assigned.

    Args:
        client: JiraClient instance
        issue_key: Issue to check
        expected_assignee: Expected account ID (None for unassigned)
        timeout: Maximum seconds to wait

    Returns:
        True if assignment matches, False on timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        issue = client.get(f"/rest/api/3/issue/{issue_key}?fields=assignee")
        assignee = issue.get("fields", {}).get("assignee")
        current_id = assignee.get("accountId") if assignee else None

        if current_id == expected_assignee:
            return True
        time.sleep(0.5)
    return False


# =============================================================================
# Utility Functions
# =============================================================================


def _random_suffix(length: int = 8) -> str:
    """Generate random suffix for unique names."""
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def generate_unique_name(prefix: str = "test") -> str:
    """Generate unique name with timestamp and random suffix."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = _random_suffix(4)
    return f"{prefix}_{ts}_{suffix}"
