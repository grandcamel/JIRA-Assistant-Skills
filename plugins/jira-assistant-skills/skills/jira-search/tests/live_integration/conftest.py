"""
Live Integration Test Configuration for jira-search skill.

Provides fixtures for testing search and filter operations against a real JIRA instance.

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-search/tests/live_integration/ --profile development -v
"""

import os
import sys
import uuid
import time
import pytest
from pathlib import Path
from typing import Generator, Dict, Any, List

# Add shared lib to path
_this_dir = Path(__file__).parent
sys.path.insert(0, str(_this_dir.parent.parent / 'scripts'))

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
    Create a unique test project for the session.

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
    project_key = f"SRC{unique_suffix}"
    project_name = f"Search Test {project_key}"

    print(f"\n{'='*60}")
    print(f"Creating test project: {project_key}")
    print(f"{'='*60}")

    project = jira_client.create_project(
        key=project_key,
        name=project_name,
        project_type_key='software',
        template_key='com.pyxis.greenhopper.jira:gh-simplified-agility-scrum',
        description='Temporary project for jira-search live integration tests'
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

        print(f"  Deleting project {project_key}...")
        client.delete_project(project_key, enable_undo=True)
        print(f"  Project {project_key} deleted (in trash for 60 days)")

    except Exception as e:
        print(f"  Error during cleanup: {e}")
        raise


@pytest.fixture(scope="session")
def test_issues(jira_client, test_project) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Create multiple test issues for search testing.

    Creates 5 issues with different types, priorities, and labels for testing
    various search scenarios.

    Yields:
        List of created issue data
    """
    issues = []
    issue_configs = [
        {'type': 'Bug', 'priority': 'High', 'labels': ['critical', 'backend']},
        {'type': 'Bug', 'priority': 'Low', 'labels': ['minor']},
        {'type': 'Task', 'priority': 'Medium', 'labels': ['backend']},
        {'type': 'Story', 'priority': 'High', 'labels': ['frontend']},
        {'type': 'Task', 'priority': 'Low', 'labels': ['documentation']},
    ]

    for i, config in enumerate(issue_configs):
        issue = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f"Search Test Issue {i+1} {uuid.uuid4().hex[:8]}",
            'description': {
                'type': 'doc',
                'version': 1,
                'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': f'Test issue for search integration tests - {config["type"]}'}]}]
            },
            'issuetype': {'name': config['type']},
            'priority': {'name': config['priority']},
            'labels': config['labels']
        })
        issues.append({**issue, 'config': config})

    # Wait for indexing
    time.sleep(1)

    yield issues

    # Cleanup handled by project cleanup


@pytest.fixture(scope="function")
def test_filter(jira_client, test_project) -> Generator[Dict[str, Any], None, None]:
    """
    Create a test filter for individual tests.

    Yields:
        Filter data with 'id', 'name', 'jql'
    """
    filter_name = f"Test Filter {uuid.uuid4().hex[:8]}"
    jql = f"project = {test_project['key']}"

    created = jira_client.create_filter(
        name=filter_name,
        jql=jql,
        description="Test filter for integration tests"
    )

    yield created

    # Cleanup
    try:
        jira_client.delete_filter(created['id'])
    except Exception:
        pass
