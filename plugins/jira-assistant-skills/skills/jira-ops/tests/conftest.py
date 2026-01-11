"""
Shared pytest fixtures for jira-ops skill tests.

Provides fixtures for testing caching, rate limiting, and other
robustness features without hitting real JIRA instance.

Note: Common markers (unit, integration, ops, asyncio) are defined in the root pytest.ini.
"""

import copy
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add shared lib to path so imports work in tests (use resolve for absolute paths)
shared_lib_path = str(
    Path(__file__).resolve().parent.parent.parent / "shared" / "scripts" / "lib"
)
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

# Add scripts to path for importing
scripts_path = str(Path(__file__).resolve().parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.fixture
def temp_cache_dir():
    """Create temporary directory for cache testing."""
    temp_dir = tempfile.mkdtemp(prefix="jira_cache_test_")
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


# mock_jira_client is provided by root conftest.py


@pytest.fixture
def sample_issue_data():
    """Sample JIRA issue data for cache testing."""
    data = {
        "id": "10100",
        "key": "PROJ-123",
        "self": "https://test.atlassian.net/rest/api/3/issue/10100",
        "fields": {
            "summary": "Test Issue",
            "description": None,
            "issuetype": {"name": "Task"},
            "project": {"key": "PROJ"},
            "status": {"name": "To Do"},
            "priority": {"name": "Medium"},
        },
    }
    return copy.deepcopy(data)


@pytest.fixture
def sample_project_data():
    """Sample JIRA project data for cache testing."""
    data = {
        "id": "10000",
        "key": "PROJ",
        "name": "Test Project",
        "projectTypeKey": "software",
    }
    return copy.deepcopy(data)
