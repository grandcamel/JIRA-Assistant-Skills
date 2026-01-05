"""
Shared pytest fixtures for all skill tests.

Provides common fixtures used across multiple skill tests.
Skill-specific fixtures remain in their respective conftest.py files.

This file is placed at the project root to be automatically discovered
by pytest and shared across all test directories.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

# =============================================================================
# TEMPORARY DIRECTORY FIXTURES
# =============================================================================


@pytest.fixture
def temp_path():
    """Create a temporary directory as Path object.

    Preferred fixture for new tests. Automatically cleaned up.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_dir(temp_path):
    """Create a temporary directory as string.

    Legacy compatibility. Prefer temp_path for new tests.
    """
    return str(temp_path)


# =============================================================================
# COMMON MOCK FIXTURES
# =============================================================================


@pytest.fixture
def base_mock_jira_client():
    """Base mock JiraClient with minimal setup.

    Skill-specific conftest files should provide their own mock_jira_client
    fixtures with additional mocking as needed. This fixture provides
    a baseline for simple tests.
    """
    client = MagicMock()
    client.base_url = "https://test.atlassian.net"
    client.email = "test@example.com"
    client.close = Mock()
    client.__enter__ = Mock(return_value=client)
    client.__exit__ = Mock(return_value=False)
    return client


# =============================================================================
# PROJECT STRUCTURE FIXTURES
# =============================================================================


@pytest.fixture
def claude_project_structure(temp_path):
    """Create a standard .claude project structure."""
    project = temp_path / "Test-Project"
    project.mkdir()

    claude_dir = project / ".claude"
    skills_dir = claude_dir / "skills"
    shared_lib = skills_dir / "shared" / "scripts" / "lib"
    shared_lib.mkdir(parents=True)

    settings = claude_dir / "settings.json"
    settings.write_text("{}")

    return {
        "root": project,
        "claude_dir": claude_dir,
        "skills_dir": skills_dir,
        "shared_lib": shared_lib,
        "settings": settings,
    }


@pytest.fixture
def sample_skill_md():
    """Return sample SKILL.md content."""
    return """---
name: sample-skill
description: A sample skill for testing.
---

# Sample Skill

## Quick Start

```bash
echo "Hello"
```
"""


# =============================================================================
# SAMPLE DATA FIXTURES (shared across skills)
# =============================================================================


@pytest.fixture
def sample_jira_project():
    """Sample JIRA project data."""
    return {
        "id": "10000",
        "key": "PROJ",
        "name": "Test Project",
        "projectTypeKey": "software",
    }


@pytest.fixture
def sample_user():
    """Sample JIRA user data."""
    return {
        "accountId": "557058:test-user-id",
        "displayName": "Test User",
        "emailAddress": "test@example.com",
        "active": True,
    }
