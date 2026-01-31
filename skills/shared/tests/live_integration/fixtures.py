"""
Session-scoped fixtures for live JIRA integration tests.

These fixtures provide real JIRA connections and test data. Import them
into your skill's live_integration/conftest.py:

    pytest_plugins = ["fixtures"]

Fixtures provided:
- jira_connection: Session-scoped JIRA connection details
- jira_client: Session-scoped JiraClient instance
- jira_info: Server information dictionary
- test_project: Dedicated test project (auto-created if needed)
- test_project_key: Test project key string
- test_issue: Single test issue (function-scoped)
- fresh_test_issue: Isolated test issue per test
- issue_helper: Issue creation helper with auto-cleanup
- search_helper: Simplified search interface

Environment Variables:
- JIRA_TEST_URL: JIRA instance URL (required)
- JIRA_TEST_EMAIL: User email (or JIRA_EMAIL)
- JIRA_TEST_TOKEN: API token (or JIRA_API_TOKEN)
- JIRA_TEST_PROJECT: Test project key (default: SKILLS_TEST)
"""

import os
import random
import string
import time
from typing import Any, Dict, Generator, List, Optional

import pytest

from .jira_container import JiraConnection, cleanup_connection, get_jira_connection

# =============================================================================
# Connection Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def jira_connection() -> Generator[JiraConnection, None, None]:
    """
    Session-scoped JIRA connection.

    Yields the connection details for the test JIRA instance.
    Cleans up container (if used) at session end.
    """
    connection = get_jira_connection()
    yield connection
    cleanup_connection()


@pytest.fixture(scope="session")
def jira_client(jira_connection: JiraConnection):
    """
    Session-scoped JiraClient instance.

    Provides a configured client for API operations.
    """
    try:
        from jira_as import JiraClient
    except ImportError:
        from jira_as.jira_client import JiraClient

    client = JiraClient(
        base_url=jira_connection.base_url,
        email=jira_connection.email,
        api_token=jira_connection.api_token,
    )

    yield client

    # Cleanup
    if hasattr(client, "close"):
        client.close()


@pytest.fixture(scope="session")
def jira_info(jira_client) -> Dict[str, Any]:
    """
    Get JIRA server information.

    Returns a dictionary with server details like version, deployment type, etc.
    """
    try:
        info = jira_client.get("/rest/api/3/serverInfo")
        return info
    except Exception:
        # Fallback for v2 API
        return jira_client.get("/rest/api/2/serverInfo")


# =============================================================================
# Project Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def test_project_key() -> str:
    """
    Get the test project key from environment or use default.
    """
    return os.getenv("JIRA_TEST_PROJECT", "SKILLSTEST")


@pytest.fixture(scope="session")
def test_project(jira_client, test_project_key: str) -> Dict[str, Any]:
    """
    Get or create the test project.

    Returns the project data. Creates the project if it doesn't exist.
    """
    try:
        project = jira_client.get(f"/rest/api/3/project/{test_project_key}")
        return project
    except Exception:
        # Project doesn't exist, try to create it
        try:
            project = jira_client.post(
                "/rest/api/3/project",
                json={
                    "key": test_project_key,
                    "name": "JIRA Skills Test Project",
                    "projectTypeKey": "software",
                    "projectTemplateKey": "com.pyxis.greenhopper.jira:gh-kanban-template",
                    "leadAccountId": jira_client.get_current_user_id(),
                },
            )
            return project
        except Exception as e:
            pytest.skip(f"Cannot access or create test project {test_project_key}: {e}")


# =============================================================================
# Issue Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def test_issue(jira_client, test_project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Session-scoped test issue.

    Creates a single issue for tests that only read data.
    """
    issue = jira_client.post(
        "/rest/api/3/issue",
        json={
            "fields": {
                "project": {"key": test_project["key"]},
                "summary": f"[Test] Session test issue - {_random_suffix()}",
                "issuetype": {"name": "Task"},
                "labels": ["test", "automated"],
            }
        },
    )
    yield issue

    # Cleanup
    try:
        jira_client.delete(f"/rest/api/3/issue/{issue['key']}")
    except Exception:
        pass


@pytest.fixture
def fresh_test_issue(
    jira_client, test_project: Dict[str, Any]
) -> Generator[Dict[str, Any], None, None]:
    """
    Function-scoped isolated test issue.

    Creates a new issue for each test, automatically cleaned up after.
    Use this for tests that modify issue data.
    """
    issue = jira_client.post(
        "/rest/api/3/issue",
        json={
            "fields": {
                "project": {"key": test_project["key"]},
                "summary": f"[Test] Fresh issue - {_random_suffix()}",
                "issuetype": {"name": "Task"},
                "labels": ["test", "automated", "fresh"],
            }
        },
    )
    yield issue

    # Cleanup
    try:
        jira_client.delete(f"/rest/api/3/issue/{issue['key']}")
    except Exception:
        pass


# =============================================================================
# Helper Fixtures
# =============================================================================


class IssueHelper:
    """Helper for creating and managing test issues with auto-cleanup."""

    def __init__(self, client, project_key: str):
        self._client = client
        self._project_key = project_key
        self._created_issues: List[str] = []

    def create(
        self,
        summary: Optional[str] = None,
        issue_type: str = "Task",
        **fields,
    ) -> Dict[str, Any]:
        """
        Create a test issue.

        Args:
            summary: Issue summary (auto-generated if not provided)
            issue_type: Issue type name
            **fields: Additional fields to set

        Returns:
            Created issue data
        """
        issue_fields = {
            "project": {"key": self._project_key},
            "summary": summary or f"[Test] {issue_type} - {_random_suffix()}",
            "issuetype": {"name": issue_type},
            "labels": fields.pop("labels", []) + ["test", "automated"],
            **fields,
        }

        issue = self._client.post("/rest/api/3/issue", json={"fields": issue_fields})
        self._created_issues.append(issue["key"])
        return issue

    def create_batch(self, count: int, **fields) -> List[Dict[str, Any]]:
        """Create multiple test issues."""
        return [self.create(**fields) for _ in range(count)]

    def cleanup(self):
        """Delete all created issues."""
        for key in self._created_issues:
            try:
                self._client.delete(f"/rest/api/3/issue/{key}")
            except Exception:
                pass
        self._created_issues.clear()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()


@pytest.fixture
def issue_helper(
    jira_client, test_project: Dict[str, Any]
) -> Generator[IssueHelper, None, None]:
    """
    Issue creation helper with auto-cleanup.

    Creates issues that are automatically deleted after the test.
    """
    helper = IssueHelper(jira_client, test_project["key"])
    yield helper
    helper.cleanup()


class SearchHelper:
    """Simplified search interface for tests."""

    def __init__(self, client):
        self._client = client

    def query(
        self,
        jql: str,
        fields: Optional[List[str]] = None,
        max_results: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Execute a JQL query.

        Args:
            jql: JQL query string
            fields: Fields to return (default: key, summary, status)
            max_results: Maximum results to return

        Returns:
            List of matching issues
        """
        response = self._client.post(
            "/rest/api/3/search",
            json={
                "jql": jql,
                "fields": fields or ["key", "summary", "status"],
                "maxResults": max_results,
            },
        )
        return response.get("issues", [])

    def count(self, jql: str) -> int:
        """Get count of issues matching JQL."""
        response = self._client.post(
            "/rest/api/3/search",
            json={"jql": jql, "maxResults": 0},
        )
        return response.get("total", 0)

    def exists(self, jql: str) -> bool:
        """Check if any issues match JQL."""
        return self.count(jql) > 0


@pytest.fixture
def search_helper(jira_client) -> SearchHelper:
    """Simplified search interface."""
    return SearchHelper(jira_client)


# =============================================================================
# Skip Markers
# =============================================================================


@pytest.fixture(scope="session")
def skip_if_no_jira(jira_connection: JiraConnection):
    """Skip test if JIRA is not available."""
    if not jira_connection:
        pytest.skip("JIRA connection not available")


@pytest.fixture
def skip_if_container(jira_connection: JiraConnection):
    """Skip test if running against a container (vs cloud)."""
    if jira_connection.is_container:
        pytest.skip("Test not supported on container JIRA")


@pytest.fixture
def skip_if_cloud(jira_connection: JiraConnection):
    """Skip test if running against cloud (vs container/DC)."""
    if not jira_connection.is_container:
        pytest.skip("Test only supported on container/DC JIRA")


# =============================================================================
# Utility Functions
# =============================================================================


def _random_suffix(length: int = 8) -> str:
    """Generate a random suffix for unique names."""
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def wait_for_indexing(
    client,
    jql: str,
    min_count: int = 1,
    timeout: int = 30,
    interval: float = 1.0,
) -> bool:
    """
    Wait for issues to be indexed and searchable.

    Args:
        client: JiraClient instance
        jql: JQL to check
        min_count: Minimum expected count
        timeout: Maximum seconds to wait
        interval: Seconds between checks

    Returns:
        True if count reached, False if timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = client.post(
                "/rest/api/3/search",
                json={"jql": jql, "maxResults": 0},
            )
            if response.get("total", 0) >= min_count:
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False
