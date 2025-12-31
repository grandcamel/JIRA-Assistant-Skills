"""
Live Integration Test Configuration for jira-lifecycle skill.

Pytest fixtures for running lifecycle integration tests against a real JIRA instance.
Creates a temporary project, runs tests, and cleans up all resources.

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-lifecycle/tests/live_integration/ --profile development -v

Environment:
    Requires JIRA admin permissions to create/delete projects.
    Uses the profile specified via --profile flag or JIRA_PROFILE env var.
"""

import os
import sys
import uuid
import time
import pytest
from pathlib import Path
from typing import Generator, Dict, Any, List


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "lifecycle: mark test as lifecycle test")
    config.addinivalue_line("markers", "transition: mark test as transition test")
    config.addinivalue_line("markers", "version: mark test as version test")
    config.addinivalue_line("markers", "component: mark test as component test")


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraClient


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--profile",
        action="store",
        default=os.environ.get("JIRA_PROFILE", "development"),
        help="JIRA profile to use (default: development)"
    )
    parser.addoption(
        "--keep-project",
        action="store_true",
        default=False,
        help="Keep the test project after tests complete (for debugging)"
    )
    parser.addoption(
        "--project-key",
        action="store",
        default=None,
        help="Use existing project instead of creating one (skips cleanup)"
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
def test_project(jira_client, keep_project, existing_project_key) -> Generator[Dict[str, Any], None, None]:
    """
    Create a unique test project for the session.

    The project key is generated as LIF + 6 random hex chars (e.g., LIFA1B2C3).
    A Scrum board is automatically created with the project.

    Yields:
        Project data with keys: 'id', 'key', 'name', 'board_id'
    """
    if existing_project_key:
        # Use existing project - no cleanup
        project = jira_client.get_project(existing_project_key)
        boards = jira_client.get_all_boards(project_key=existing_project_key)
        board_id = boards['values'][0]['id'] if boards.get('values') else None
        yield {
            'id': project['id'],
            'key': project['key'],
            'name': project['name'],
            'board_id': board_id,
            'is_temporary': False
        }
        return

    # Generate unique project key
    unique_suffix = uuid.uuid4().hex[:6].upper()
    project_key = f"LIF{unique_suffix}"
    project_name = f"Lifecycle Test {project_key}"

    print(f"\n{'='*60}")
    print(f"Creating test project: {project_key}")
    print(f"{'='*60}")

    # Create the project with Scrum template
    project = jira_client.create_project(
        key=project_key,
        name=project_name,
        project_type_key='software',
        template_key='com.pyxis.greenhopper.jira:gh-simplified-agility-scrum',
        description='Temporary project for jira-lifecycle live integration tests'
    )

    # Wait a moment for the board to be created
    time.sleep(2)

    # Get the auto-created board
    boards = jira_client.get_all_boards(project_key=project_key)
    board_id = boards['values'][0]['id'] if boards.get('values') else None

    project_data = {
        'id': project['id'],
        'key': project_key,
        'name': project_name,
        'board_id': board_id,
        'is_temporary': True
    }

    print(f"Project created: {project_key} (Board ID: {board_id})")

    yield project_data

    # Cleanup
    if not keep_project and project_data.get('is_temporary', True):
        print(f"\n{'='*60}")
        print(f"Cleaning up test project: {project_key}")
        print(f"{'='*60}")
        cleanup_project(jira_client, project_key)


def cleanup_project(client: JiraClient, project_key: str) -> None:
    """
    Clean up all resources in a project before deletion.

    Order of cleanup:
    1. Delete all issues (handles subtasks and links automatically)
    2. Delete versions
    3. Delete components
    4. Delete the project (cascades to board)
    """
    try:
        # Step 1: Delete all issues
        print(f"  Deleting issues in {project_key}...")
        issues_deleted = 0

        while True:
            result = client.search_issues(
                f"project = {project_key} ORDER BY created DESC",
                fields=['key', 'issuetype'],
                max_results=50
            )
            issues = result.get('issues', [])
            if not issues:
                break

            # Delete subtasks first, then parent issues
            subtasks = [i for i in issues if i['fields']['issuetype'].get('subtask', False)]
            parents = [i for i in issues if not i['fields']['issuetype'].get('subtask', False)]

            for issue in subtasks + parents:
                try:
                    client.delete_issue(issue['key'])
                    issues_deleted += 1
                except Exception as e:
                    print(f"    Warning: Could not delete {issue['key']}: {e}")

        print(f"  Deleted {issues_deleted} issues")

        # Step 2: Delete versions
        try:
            versions = client.get_project_versions(project_key)
            for version in versions:
                if version.get('name', '').startswith('Test'):
                    try:
                        client.delete_version(version['id'])
                    except Exception:
                        pass
        except Exception:
            pass

        # Step 3: Delete components
        try:
            components = client.get_project_components(project_key)
            for component in components:
                if component.get('name', '').startswith('Test'):
                    try:
                        client.delete_component(component['id'])
                    except Exception:
                        pass
        except Exception:
            pass

        # Step 4: Delete the project
        print(f"  Deleting project {project_key}...")
        client.delete_project(project_key, enable_undo=True)
        print(f"  Project {project_key} deleted (in trash for 60 days)")

    except Exception as e:
        print(f"  Error during cleanup: {e}")
        raise


@pytest.fixture(scope="function")
def test_issue(jira_client, test_project) -> Generator[Dict[str, Any], None, None]:
    """
    Create a test issue for individual tests.

    Creates a Task issue and cleans it up after the test.

    Yields:
        Issue data with 'key', 'id', 'self'
    """
    issue = jira_client.create_issue({
        'project': {'key': test_project['key']},
        'summary': f'Lifecycle Test Issue {uuid.uuid4().hex[:8]}',
        'description': {
            'type': 'doc',
            'version': 1,
            'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Test issue for lifecycle tests'}]}]
        },
        'issuetype': {'name': 'Task'}
    })

    yield issue

    # Cleanup
    try:
        jira_client.delete_issue(issue['key'])
    except Exception:
        pass


@pytest.fixture(scope="function")
def test_version(jira_client, test_project) -> Generator[Dict[str, Any], None, None]:
    """
    Create a test version for individual tests.

    Yields:
        Version data with 'id', 'name', etc.
    """
    version_name = f'Test Version {uuid.uuid4().hex[:8]}'
    version = jira_client.create_version(
        project=test_project['key'],
        name=version_name,
        description='Test version for lifecycle tests'
    )

    yield version

    # Cleanup
    try:
        jira_client.delete_version(version['id'])
    except Exception:
        pass


@pytest.fixture(scope="function")
def test_component(jira_client, test_project) -> Generator[Dict[str, Any], None, None]:
    """
    Create a test component for individual tests.

    Yields:
        Component data with 'id', 'name', etc.
    """
    component_name = f'Test Component {uuid.uuid4().hex[:8]}'
    component = jira_client.create_component(
        project=test_project['key'],
        name=component_name,
        description='Test component for lifecycle tests'
    )

    yield component

    # Cleanup
    try:
        jira_client.delete_component(component['id'])
    except Exception:
        pass


@pytest.fixture(scope="session")
def current_user(jira_client) -> Dict[str, Any]:
    """Get the current authenticated user."""
    return jira_client.get('/rest/api/3/myself', operation='get myself')
