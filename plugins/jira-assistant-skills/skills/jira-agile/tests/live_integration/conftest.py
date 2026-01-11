"""
Live Integration Test Configuration for jira-agile skill.

Provides fixtures for testing agile operations against a real JIRA instance.

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-agile/tests/live_integration/ --profile development -v
"""

import os
import sys
import uuid
import time
import pytest
from pathlib import Path
from typing import Generator, Dict, Any, List

# Add scripts to path
_this_dir = Path(__file__).parent
_scripts_path = _this_dir.parent.parent / 'scripts'
sys.path.insert(0, str(_scripts_path))

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraClient


def pytest_addoption(parser):
    """Add custom command line options."""
    try:
        parser.addoption(
            "--profile",
            action="store",
            default=os.environ.get("JIRA_PROFILE", "development"),
            help="JIRA profile to use (default: development)"
        )
    except ValueError:
        pass

    try:
        parser.addoption(
            "--keep-project",
            action="store_true",
            default=False,
            help="Keep the test project after tests complete (for debugging)"
        )
    except ValueError:
        pass

    try:
        parser.addoption(
            "--project-key",
            action="store",
            default=None,
            help="Use existing project instead of creating one (skips cleanup)"
        )
    except ValueError:
        pass


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
    Create a unique test project for the session with Scrum board.

    Yields:
        Project data with keys: 'id', 'key', 'name', 'board_id'
    """
    if existing_project_key:
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

    unique_suffix = uuid.uuid4().hex[:6].upper()
    project_key = f"AGL{unique_suffix}"
    project_name = f"Agile Test {project_key}"

    print(f"\n{'='*60}")
    print(f"Creating test project: {project_key}")
    print(f"{'='*60}")

    project = jira_client.create_project(
        key=project_key,
        name=project_name,
        project_type_key='software',
        template_key='com.pyxis.greenhopper.jira:gh-simplified-agility-scrum',
        description='Temporary project for jira-agile live integration tests'
    )

    time.sleep(2)

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

    if not keep_project and project_data.get('is_temporary', True):
        print(f"\n{'='*60}")
        print(f"Cleaning up test project: {project_key}")
        print(f"{'='*60}")
        _cleanup_project(jira_client, project_key)


def _cleanup_project(client: JiraClient, project_key: str) -> None:
    """Clean up all resources in a project before deletion."""
    try:
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

            subtasks = [i for i in issues if i['fields']['issuetype'].get('subtask', False)]
            parents = [i for i in issues if not i['fields']['issuetype'].get('subtask', False)]

            for issue in subtasks + parents:
                try:
                    client.delete_issue(issue['key'])
                    issues_deleted += 1
                except Exception as e:
                    print(f"    Warning: Could not delete {issue['key']}: {e}")

        print(f"  Deleted {issues_deleted} issues")

        # Delete future sprints
        boards = client.get_all_boards(project_key=project_key)
        for board in boards.get('values', []):
            try:
                sprints = client.get_board_sprints(board['id'], state='future')
                for sprint in sprints.get('values', []):
                    try:
                        client.delete_sprint(sprint['id'])
                    except Exception:
                        pass
            except Exception:
                pass

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

    Yields:
        Issue data with 'key', 'id', 'self'
    """
    issue = jira_client.create_issue({
        'project': {'key': test_project['key']},
        'summary': f'Test Issue {uuid.uuid4().hex[:8]}',
        'description': {
            'type': 'doc',
            'version': 1,
            'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Test issue for agile tests'}]}]
        },
        'issuetype': {'name': 'Task'}
    })

    yield issue

    try:
        jira_client.delete_issue(issue['key'])
    except Exception:
        pass


@pytest.fixture(scope="function")
def test_story(jira_client, test_project) -> Generator[Dict[str, Any], None, None]:
    """
    Create a test Story issue for individual tests.

    Yields:
        Issue data with 'key', 'id', 'self'
    """
    issue = jira_client.create_issue({
        'project': {'key': test_project['key']},
        'summary': f'Test Story {uuid.uuid4().hex[:8]}',
        'description': {
            'type': 'doc',
            'version': 1,
            'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Test story for agile tests'}]}]
        },
        'issuetype': {'name': 'Story'}
    })

    yield issue

    try:
        jira_client.delete_issue(issue['key'])
    except Exception:
        pass


@pytest.fixture(scope="function")
def test_sprint(jira_client, test_project) -> Generator[Dict[str, Any], None, None]:
    """
    Create a test sprint for individual tests.

    Yields:
        Sprint data with 'id', 'name', 'state'
    """
    if not test_project.get('board_id'):
        pytest.skip("No board available for sprint creation")

    sprint = jira_client.create_sprint(
        board_id=test_project['board_id'],
        name=f'Test Sprint {uuid.uuid4().hex[:8]}',
        goal='Integration test sprint'
    )

    yield sprint

    try:
        if sprint.get('state') == 'future':
            jira_client.delete_sprint(sprint['id'])
    except Exception:
        pass
