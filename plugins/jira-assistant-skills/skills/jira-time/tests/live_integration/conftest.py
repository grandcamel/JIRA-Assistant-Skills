"""
Live Integration Test Configuration for jira-time skill.

Pytest fixtures for running time tracking integration tests against a real JIRA instance.
Creates a temporary project, runs tests, and cleans up all resources.

Note: Common markers (integration, time, worklog, estimate, bulk) are defined in the root pytest.ini.

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-time/tests/live_integration/ --profile development -v

Environment:
    Requires JIRA admin permissions to create/delete projects.
    Uses the profile specified via --profile flag or JIRA_PROFILE env var.
"""

import contextlib
import os
import time
import uuid
from collections.abc import Generator
from typing import Any

import pytest

from jira_assistant_skills_lib import JiraClient, get_jira_client


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--profile",
        action="store",
        default=os.environ.get("JIRA_PROFILE", "development"),
        help="JIRA profile to use (default: development)",
    )
    parser.addoption(
        "--keep-project",
        action="store_true",
        default=False,
        help="Keep the test project after tests complete (for debugging)",
    )
    parser.addoption(
        "--project-key",
        action="store",
        default=None,
        help="Use existing project instead of creating one (skips cleanup)",
    )


@pytest.fixture(scope="session")
def jira_profile(request) -> str:
    """Get the JIRA profile from command line."""
    return request.config.getoption("--profile")


@pytest.fixture(scope="session")
def keep_project(request) -> bool:
    """Check if project should be kept after tests."""
    return request.config.getoption("--keep-project")


@pytest.fixture(scope="session")
def existing_project_key(request) -> str:
    """Get existing project key if specified."""
    return request.config.getoption("--project-key")


@pytest.fixture(scope="session")
def jira_client(jira_profile) -> Generator[JiraClient, None, None]:
    """Create a JIRA client for the test session."""
    client = get_jira_client(jira_profile)
    yield client
    client.close()


@pytest.fixture(scope="session")
def test_project(
    jira_client, keep_project, existing_project_key
) -> Generator[dict[str, Any], None, None]:
    """
    Create a unique test project for the session.

    The project key is generated as TIM + 6 random hex chars (e.g., TIMA1B2C3).
    A Scrum board is automatically created with the project.

    Yields:
        Project data with keys: 'id', 'key', 'name', 'board_id'
    """
    if existing_project_key:
        # Use existing project - no cleanup
        project = jira_client.get_project(existing_project_key)
        boards = jira_client.get_all_boards(project_key=existing_project_key)
        board_id = boards["values"][0]["id"] if boards.get("values") else None
        yield {
            "id": project["id"],
            "key": project["key"],
            "name": project["name"],
            "board_id": board_id,
            "is_temporary": False,
        }
        return

    # Generate unique project key
    unique_suffix = uuid.uuid4().hex[:6].upper()
    project_key = f"TIM{unique_suffix}"
    project_name = f"Time Tracking Test {project_key}"

    print(f"\n{'=' * 60}")
    print(f"Creating test project: {project_key}")
    print(f"{'=' * 60}")

    # Create the project with Scrum template
    project = jira_client.create_project(
        key=project_key,
        name=project_name,
        project_type_key="software",
        template_key="com.pyxis.greenhopper.jira:gh-simplified-agility-scrum",
        description="Temporary project for jira-time live integration tests",
    )

    # Wait a moment for the board to be created
    time.sleep(2)

    # Get the auto-created board
    boards = jira_client.get_all_boards(project_key=project_key)
    board_id = boards["values"][0]["id"] if boards.get("values") else None

    project_data = {
        "id": project["id"],
        "key": project_key,
        "name": project_name,
        "board_id": board_id,
        "is_temporary": True,
    }

    print(f"Project created: {project_key} (Board ID: {board_id})")

    yield project_data

    # Cleanup
    if not keep_project and project_data.get("is_temporary", True):
        print(f"\n{'=' * 60}")
        print(f"Cleaning up test project: {project_key}")
        print(f"{'=' * 60}")
        cleanup_project(jira_client, project_key)


def cleanup_project(client: JiraClient, project_key: str) -> None:
    """
    Clean up all resources in a project before deletion.

    Order of cleanup:
    1. Delete all issues (handles subtasks and links automatically)
    2. Delete the project (cascades to board)
    """
    try:
        # Step 1: Delete all issues
        print(f"  Deleting issues in {project_key}...")
        issues_deleted = 0

        while True:
            result = client.search_issues(
                f"project = {project_key} ORDER BY created DESC",
                fields=["key", "issuetype"],
                max_results=50,
            )
            issues = result.get("issues", [])
            if not issues:
                break

            # Delete subtasks first, then parent issues
            subtasks = [
                i for i in issues if i["fields"]["issuetype"].get("subtask", False)
            ]
            parents = [
                i for i in issues if not i["fields"]["issuetype"].get("subtask", False)
            ]

            for issue in subtasks + parents:
                try:
                    client.delete_issue(issue["key"])
                    issues_deleted += 1
                except Exception as e:
                    print(f"    Warning: Could not delete {issue['key']}: {e}")

        print(f"  Deleted {issues_deleted} issues")

        # Step 2: Delete the project
        print(f"  Deleting project {project_key}...")
        client.delete_project(project_key, enable_undo=True)
        print(f"  Project {project_key} deleted (in trash for 60 days)")

    except Exception as e:
        print(f"  Error during cleanup: {e}")
        raise


@pytest.fixture(scope="function")
def test_issue(jira_client, test_project) -> Generator[dict[str, Any], None, None]:
    """
    Create a test issue for individual tests.

    Creates a Task issue and cleans it up after the test.

    Yields:
        Issue data with 'key', 'id', 'self'
    """
    issue = jira_client.create_issue(
        {
            "project": {"key": test_project["key"]},
            "summary": f"Time Test Issue {uuid.uuid4().hex[:8]}",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "Test issue for time tracking tests",
                            }
                        ],
                    }
                ],
            },
            "issuetype": {"name": "Task"},
        }
    )

    yield issue

    # Cleanup
    with contextlib.suppress(Exception):
        jira_client.delete_issue(issue["key"])


@pytest.fixture(scope="function")
def issue_with_estimate(
    jira_client, test_project
) -> Generator[dict[str, Any], None, None]:
    """
    Create a test issue with time estimate set.

    Yields:
        Issue data with 'key', 'id', 'self'
    """
    issue = jira_client.create_issue(
        {
            "project": {"key": test_project["key"]},
            "summary": f"Estimated Issue {uuid.uuid4().hex[:8]}",
            "issuetype": {"name": "Task"},
        }
    )

    # Set time estimate
    jira_client.set_time_tracking(issue["key"], original_estimate="4h")

    yield issue

    with contextlib.suppress(Exception):
        jira_client.delete_issue(issue["key"])


@pytest.fixture(scope="function")
def issue_with_worklog(
    jira_client, test_project
) -> Generator[dict[str, Any], None, None]:
    """
    Create a test issue with existing worklog.

    Yields:
        Issue data with 'key', 'id', 'worklog_id'
    """
    issue = jira_client.create_issue(
        {
            "project": {"key": test_project["key"]},
            "summary": f"Worklog Issue {uuid.uuid4().hex[:8]}",
            "issuetype": {"name": "Task"},
        }
    )

    # Add worklog
    worklog = jira_client.add_worklog(issue["key"], time_spent="1h")
    issue["worklog_id"] = worklog["id"]

    yield issue

    with contextlib.suppress(Exception):
        jira_client.delete_issue(issue["key"])


@pytest.fixture(scope="function")
def multiple_issues(
    jira_client, test_project
) -> Generator[list[dict[str, Any]], None, None]:
    """
    Create multiple test issues for bulk operations.

    Yields:
        List of issue dicts
    """
    issues = []
    for i in range(3):
        issue = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Bulk Time Issue {i + 1} {uuid.uuid4().hex[:8]}",
                "issuetype": {"name": "Task"},
            }
        )
        issues.append(issue)

    yield issues

    for issue in issues:
        with contextlib.suppress(Exception):
            jira_client.delete_issue(issue["key"])


def make_adf_comment(text: str) -> dict:
    """Create an ADF-formatted comment."""
    return {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }
