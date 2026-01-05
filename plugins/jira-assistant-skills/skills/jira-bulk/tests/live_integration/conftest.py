"""
Live Integration Test Configuration for jira-bulk skill.

Reuses fixtures from shared live integration tests.

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-bulk/tests/live_integration/ --profile development -v
"""

import os
import sys
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

import contextlib

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

    The project key is generated as BLK + 6 random hex chars (e.g., BLKA1B2C3).
    """
    if existing_project_key:
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
    project_key = f"BLK{unique_suffix}"
    project_name = f"Bulk Test {project_key}"

    print(f"\n{'=' * 60}")
    print(f"Creating test project: {project_key}")
    print(f"{'=' * 60}")

    # Create the project with Scrum template
    project = jira_client.create_project(
        key=project_key,
        name=project_name,
        project_type_key="software",
        template_key="com.pyxis.greenhopper.jira:gh-simplified-agility-scrum",
        description="Temporary project for bulk operation live integration tests",
    )

    import time

    time.sleep(2)

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
    """Clean up all resources in a project before deletion."""
    try:
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

        boards = client.get_all_boards(project_key=project_key)
        sprints_deleted = 0

        for board in boards.get("values", []):
            try:
                sprints = client.get_board_sprints(board["id"], state="future")
                for sprint in sprints.get("values", []):
                    try:
                        client.delete_sprint(sprint["id"])
                        sprints_deleted += 1
                    except Exception:
                        pass
            except Exception:
                pass

        if sprints_deleted > 0:
            print(f"  Deleted {sprints_deleted} sprints")

        print(f"  Deleting project {project_key}...")
        client.delete_project(project_key, enable_undo=True)
        print(f"  Project {project_key} deleted (in trash for 60 days)")

    except Exception as e:
        print(f"  Error during cleanup: {e}")
        raise


@pytest.fixture(scope="function")
def bulk_issues(
    jira_client, test_project
) -> Generator[list[dict[str, Any]], None, None]:
    """
    Create multiple test issues for bulk operations.

    Creates 5 issues for bulk operation testing.

    Yields:
        List of issue data dicts with 'key', 'id'
    """
    issues = []
    for i in range(5):
        issue = jira_client.create_issue(
            {
                "project": {"key": test_project["key"]},
                "summary": f"Bulk Test Issue {i + 1} - {uuid.uuid4().hex[:8]}",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Test issue {i + 1} for bulk operations",
                                }
                            ],
                        }
                    ],
                },
                "issuetype": {"name": "Task"},
            }
        )
        issues.append(issue)

    yield issues

    # Cleanup
    for issue in issues:
        with contextlib.suppress(Exception):
            jira_client.delete_issue(issue["key"])


@pytest.fixture(scope="function")
def single_issue(jira_client, test_project) -> Generator[dict[str, Any], None, None]:
    """Create a single test issue."""
    issue = jira_client.create_issue(
        {
            "project": {"key": test_project["key"]},
            "summary": f"Single Test Issue {uuid.uuid4().hex[:8]}",
            "issuetype": {"name": "Task"},
        }
    )

    yield issue

    with contextlib.suppress(Exception):
        jira_client.delete_issue(issue["key"])
