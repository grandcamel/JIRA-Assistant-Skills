"""
Live Integration Test Configuration for jira-relationships skill.

Pytest fixtures for running relationship integration tests against a real JIRA instance.
Creates a temporary project, runs tests, and cleans up all resources.

Usage:
    pytest .claude/skills/jira-relationships/tests/live_integration/ --profile development -v

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
    config.addinivalue_line("markers", "relationships: mark test as relationships test")
    config.addinivalue_line("markers", "links: mark test as link test")
    config.addinivalue_line("markers", "blockers: mark test as blocker test")
    config.addinivalue_line("markers", "clone: mark test as clone test")


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

    The project key is generated as REL + 6 random hex chars (e.g., RELA1B2C3).
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
    project_key = f"REL{unique_suffix}"
    project_name = f"Relationships Test {project_key}"

    print(f"\n{'='*60}")
    print(f"Creating test project: {project_key}")
    print(f"{'='*60}")

    # Create the project with Scrum template
    project = jira_client.create_project(
        key=project_key,
        name=project_name,
        project_type_key='software',
        template_key='com.pyxis.greenhopper.jira:gh-simplified-agility-scrum',
        description='Temporary project for jira-relationships live integration tests'
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
    2. Delete the project (cascades to board)
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

        # Step 2: Delete the project
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
        'summary': f'Test Issue {uuid.uuid4().hex[:8]}',
        'description': {
            'type': 'doc',
            'version': 1,
            'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Test issue for relationship tests'}]}]
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
def linked_issues(jira_client, test_project) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Create a pair of linked issues for testing.

    Creates two issues with a 'Relates' link between them.

    Yields:
        List of two issue dicts
    """
    issue1 = jira_client.create_issue({
        'project': {'key': test_project['key']},
        'summary': f'Linked Issue 1 {uuid.uuid4().hex[:8]}',
        'issuetype': {'name': 'Task'}
    })
    issue2 = jira_client.create_issue({
        'project': {'key': test_project['key']},
        'summary': f'Linked Issue 2 {uuid.uuid4().hex[:8]}',
        'issuetype': {'name': 'Task'}
    })

    # Create link
    jira_client.create_link('Relates', issue2['key'], issue1['key'])

    yield [issue1, issue2]

    # Cleanup
    for issue in [issue1, issue2]:
        try:
            jira_client.delete_issue(issue['key'])
        except Exception:
            pass


@pytest.fixture(scope="function")
def blocker_chain(jira_client, test_project) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Create a chain of blocking issues for testing.

    Creates issues: A <- B <- C where A blocks B and B blocks C.

    Yields:
        List of three issue dicts [A, B, C]
    """
    issues = []
    for name in ['Blocker A', 'Blocked B', 'Blocked C']:
        issue = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'{name} {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'}
        })
        issues.append(issue)

    # Create blocking chain: A blocks B, B blocks C
    jira_client.create_link('Blocks', issues[1]['key'], issues[0]['key'])  # A blocks B
    jira_client.create_link('Blocks', issues[2]['key'], issues[1]['key'])  # B blocks C

    yield issues

    # Cleanup
    for issue in issues:
        try:
            jira_client.delete_issue(issue['key'])
        except Exception:
            pass


@pytest.fixture(scope="function")
def issue_with_subtasks(jira_client, test_project) -> Generator[Dict[str, Any], None, None]:
    """
    Create a parent issue with subtasks for cloning tests.

    Yields:
        Parent issue data with 'key', 'id', 'self', 'subtask_keys'
    """
    # Create parent
    parent = jira_client.create_issue({
        'project': {'key': test_project['key']},
        'summary': f'Parent Issue {uuid.uuid4().hex[:8]}',
        'description': {
            'type': 'doc',
            'version': 1,
            'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Parent for cloning test'}]}]
        },
        'issuetype': {'name': 'Task'}
    })

    # Create subtasks
    subtask_keys = []
    for i in range(2):
        subtask = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Subtask {i+1} {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Subtask'},
            'parent': {'key': parent['key']}
        })
        subtask_keys.append(subtask['key'])

    parent['subtask_keys'] = subtask_keys

    yield parent

    # Cleanup - subtasks are deleted with parent
    try:
        jira_client.delete_issue(parent['key'])
    except Exception:
        pass


@pytest.fixture(scope="session")
def link_types(jira_client) -> List[Dict[str, Any]]:
    """Get available link types for the JIRA instance."""
    return jira_client.get_link_types()
