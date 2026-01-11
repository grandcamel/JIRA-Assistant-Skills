"""
Live Integration Test Configuration for jira-fields skill.

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-fields/tests/live_integration/ -v
"""

import sys
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from jira_assistant_skills_lib import JiraClient, get_jira_client


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
    )
    parser.addoption(
        "--keep-project",
        action="store_true",
        default=False,
        help="Keep the test project after tests complete",
    )
    parser.addoption(
        "--project-key",
        default=None,
        help="Use existing project instead of creating one",
    )


@pytest.fixture(scope="session")


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
    """Create a unique test project for the session."""
    if existing_project_key:
        project = jira_client.get_project(existing_project_key)
        yield {
            "id": project["id"],
            "key": project["key"],
            "name": project["name"],
            "is_temporary": False,
        }
        return

    # Generate unique project key
    unique_suffix = uuid.uuid4().hex[:6].upper()
    project_key = f"FLD{unique_suffix}"
    project_name = f"Fields Test {project_key}"

    print(f"\n{'=' * 60}")
    print(f"Creating test project: {project_key}")
    print(f"{'=' * 60}")

    project = jira_client.create_project(
        key=project_key,
        name=project_name,
        project_type_key="software",
        template_key="com.pyxis.greenhopper.jira:gh-simplified-agility-scrum",
        description="Temporary project for field management live integration tests",
    )

    import time

    time.sleep(2)

    project_data = {
        "id": project["id"],
        "key": project_key,
        "name": project_name,
        "is_temporary": True,
    }

    print(f"Project created: {project_key}")

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

        print(f"  Deleting project {project_key}...")
        client.delete_project(project_key, enable_undo=True)
        print(f"  Project {project_key} deleted")

    except Exception as e:
        print(f"  Error during cleanup: {e}")
        raise
