"""SBX live fixtures, runnable through jira-dev-host --suite only.

Credentials and project come exclusively from the wrapper environment.
Fixture names and helper APIs remain available to skill-specific consumers.
The standalone jira_container module retains its legacy connection API.
"""

import os
import random
import string
import time
from typing import Any, Dict, Generator, List, Optional

import pytest

from .jira_container import JiraConnection
from .sbx_profile import TrackedJiraClient, resolve_sbx_profile

# =============================================================================
# Connection Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def sbx_profile():
    """Fail before client construction when wrapper configuration is absent."""
    try:
        return resolve_sbx_profile(os.environ)
    except ValueError as exc:
        pytest.fail(str(exc), pytrace=False)


@pytest.fixture(scope="session")
def jira_connection(sbx_profile) -> Generator[JiraConnection, None, None]:
    connection = JiraConnection(
        base_url=sbx_profile.base_url,
        email=sbx_profile.email,
        api_token=sbx_profile.api_token,
    ).start()
    try:
        yield connection
    finally:
        connection.stop()


@pytest.fixture(scope="session")
def jira_client(jira_connection: JiraConnection, request):
    """Track all issue creates; verify session cleanup before closing HTTP."""
    client = TrackedJiraClient(
        base_url=jira_connection.base_url,
        email=jira_connection.email,
        api_token=jira_connection.api_token,
    )
    reporter = request.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is not None:
        reporter.write_line(f"SBX live run: run_label={client.run_label}")
    try:
        yield client
    finally:
        try:
            request.config._sbx_cleanup_summary = client.cleanup_created_issues()
        except Exception as exc:
            request.config._sbx_cleanup_summary = "SBX cleanup FAILED: " + str(exc)
            pytest.fail(request.config._sbx_cleanup_summary, pytrace=False)
        finally:
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
def test_project_key(sbx_profile) -> str:
    return sbx_profile.project_key


@pytest.fixture(scope="session")
def test_project(jira_client, test_project_key: str) -> Dict[str, Any]:
    """Require the existing Sandbox Project; never create a project."""
    project = jira_client.get(f"/rest/api/3/project/{test_project_key}")
    if project.get("key") != "SBX":
        pytest.fail(
            "SBX live profile refused: server returned a non-SBX project", pytrace=False
        )
    return project


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
        data={
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
        data={
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

        issue = self._client.post("/rest/api/3/issue", data={"fields": issue_fields})
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
            data={
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
            data={"jql": jql, "maxResults": 0},
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
                data={"jql": jql, "maxResults": 0},
            )
            if response.get("total", 0) >= min_count:
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False
