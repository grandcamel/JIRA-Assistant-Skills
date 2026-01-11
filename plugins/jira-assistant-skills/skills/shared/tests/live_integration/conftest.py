"""
Live Integration Test Configuration

Pytest fixtures for running integration tests against a real JIRA instance.
Creates a temporary project, runs tests, and cleans up all resources.

Note: Common markers (integration, shared, slow, api) are defined in the root pytest.ini.

Usage:
    pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/ -v

Environment:
    Requires JIRA admin permissions to create/delete projects.
"""

import os
import sys
import time
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "lib"))

import contextlib

from jira_assistant_skills_lib import JiraClient, get_jira_client


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--keep-project",
        action="store_true",
        default=False,
        help="Keep the test project after tests complete (for debugging)",
    )
    parser.addoption(
        "--project-key",
        default=None,
        help="Use existing project instead of creating one (skips cleanup)",
    )


@pytest.fixture(scope="session")
def keep_project(request) -> bool:
    """Check if project should be kept after tests."""
    return request.config.getoption("--keep-project")


@pytest.fixture(scope="session")
def existing_project_key(request) -> str:
    """Get existing project key if specified."""
    return request.config.getoption("--project-key")


@pytest.fixture(scope="session")
def jira_client() -> Generator[JiraClient, None, None]:
    """Create a JIRA client for the test session."""
    client = get_jira_client()
    yield client
    client.close()


@pytest.fixture(scope="session")
def test_project(
    jira_client, keep_project, existing_project_key
) -> Generator[dict[str, Any], None, None]:
    """
    Create a unique test project for the session.

    The project key is generated as INT + 6 random hex chars (e.g., INTA1B2C3).
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
    project_key = f"INT{unique_suffix}"
    project_name = f"Integration Test {project_key}"

    print(f"\n{'=' * 60}")
    print(f"Creating test project: {project_key}")
    print(f"{'=' * 60}")

    # Create the project with Scrum template
    project = jira_client.create_project(
        key=project_key,
        name=project_name,
        project_type_key="software",
        template_key="com.pyxis.greenhopper.jira:gh-simplified-agility-scrum",
        description="Temporary project for live integration tests",
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
    2. Delete all future sprints (active/closed cannot be deleted)
    3. Delete the project (cascades to board)
    """
    try:
        # Step 1: Delete all issues
        print(f"  Deleting issues in {project_key}...")
        issues_deleted = 0

        # Get all issues including subtasks
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

        # Step 2: Delete future sprints
        boards = client.get_all_boards(project_key=project_key)
        sprints_deleted = 0

        for board in boards.get("values", []):
            try:
                sprints = client.get_board_sprints(board["id"], state="future")
                for sprint in sprints.get("values", []):
                    try:
                        client.delete_sprint(sprint["id"])
                        sprints_deleted += 1
                    except Exception as e:
                        print(
                            f"    Warning: Could not delete sprint {sprint['id']}: {e}"
                        )
            except Exception as e:
                print(
                    f"    Warning: Could not get sprints for board {board['id']}: {e}"
                )

        if sprints_deleted > 0:
            print(f"  Deleted {sprints_deleted} sprints")

        # Step 3: Delete the project
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
            "summary": f"Test Issue {uuid.uuid4().hex[:8]}",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "Test issue for integration tests"}
                        ],
                    }
                ],
            },
            "issuetype": {"name": "Task"},
        }
    )

    yield issue

    # Cleanup
    try:
        jira_client.delete_issue(issue["key"])
    except Exception:
        pass  # Issue may have been deleted by test


@pytest.fixture(scope="function")
def test_epic(jira_client, test_project) -> Generator[dict[str, Any], None, None]:
    """
    Create a test epic for individual tests.

    Note: Simplified project templates don't require Epic Name field
    (customfield_10011). Just use summary and issuetype.

    Yields:
        Epic issue data with 'key', 'id', 'self'
    """
    issue = jira_client.create_issue(
        {
            "project": {"key": test_project["key"]},
            "summary": f"Test Epic {uuid.uuid4().hex[:8]}",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "Test epic for integration tests"}
                        ],
                    }
                ],
            },
            "issuetype": {"name": "Epic"},
        }
    )

    yield issue

    # Cleanup
    with contextlib.suppress(Exception):
        jira_client.delete_issue(issue["key"])


@pytest.fixture(scope="function")
def test_sprint(jira_client, test_project) -> Generator[dict[str, Any], None, None]:
    """
    Create a test sprint for individual tests.

    Yields:
        Sprint data with 'id', 'name', 'state'
    """
    if not test_project.get("board_id"):
        pytest.skip("No board available for sprint creation")

    sprint = jira_client.create_sprint(
        board_id=test_project["board_id"],
        name=f"Test Sprint {uuid.uuid4().hex[:8]}",
        goal="Integration test sprint",
    )

    yield sprint

    # Cleanup - only future sprints can be deleted
    try:
        if sprint.get("state") == "future":
            jira_client.delete_sprint(sprint["id"])
    except Exception:
        pass


@pytest.fixture(scope="session")
def agile_field_ids():
    """
    Return Agile custom field IDs for the current JIRA instance.

    These can be overridden via environment variables for different instances.
    """
    return {
        "sprint": os.environ.get("JIRA_SPRINT_FIELD_ID", "customfield_10020"),
        "story_points": os.environ.get(
            "JIRA_STORY_POINTS_FIELD_ID", "customfield_10016"
        ),
        "epic_link": os.environ.get("JIRA_EPIC_LINK_FIELD_ID", "customfield_10014"),
        "epic_name": os.environ.get("JIRA_EPIC_NAME_FIELD_ID", "customfield_10011"),
    }
