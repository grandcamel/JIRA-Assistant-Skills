"""
Unit Test Configuration for jira-fields skill.

Provides mock JIRA API responses and client fixtures for testing
custom field management operations.

Note: Common markers (unit, integration, fields) are defined in the root pytest.ini.

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-fields/tests/unit/ -v
"""

import copy
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add paths to sys.path before any imports that depend on them
_this_dir = Path(__file__).parent
_tests_dir = _this_dir.parent
_jira_fields_dir = _tests_dir.parent
_scripts_dir = _jira_fields_dir / "scripts"
_shared_lib_dir = _jira_fields_dir.parent / "shared" / "scripts" / "lib"

# Insert at beginning to ensure our paths take precedence
for path in [str(_shared_lib_dir), str(_scripts_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)


# ========== Sample API Responses ==========

SAMPLE_FIELDS_RESPONSE = [
    {
        "id": "customfield_10001",
        "name": "Sprint",
        "custom": True,
        "searchable": True,
        "navigable": True,
        "schema": {"type": "array", "items": "string"},
    },
    {
        "id": "customfield_10002",
        "name": "Story Points",
        "custom": True,
        "searchable": True,
        "navigable": True,
        "schema": {"type": "number"},
    },
    {
        "id": "customfield_10003",
        "name": "Epic Link",
        "custom": True,
        "searchable": True,
        "navigable": True,
        "schema": {"type": "any"},
    },
    {
        "id": "customfield_10004",
        "name": "Epic Name",
        "custom": True,
        "searchable": True,
        "navigable": True,
        "schema": {"type": "string"},
    },
    {
        "id": "customfield_10005",
        "name": "Rank",
        "custom": True,
        "searchable": True,
        "navigable": True,
        "schema": {"type": "any"},
    },
    {
        "id": "summary",
        "name": "Summary",
        "custom": False,
        "searchable": True,
        "navigable": True,
        "schema": {"type": "string"},
    },
    {
        "id": "description",
        "name": "Description",
        "custom": False,
        "searchable": True,
        "navigable": True,
        "schema": {"type": "string"},
    },
]


SAMPLE_PROJECT_RESPONSE = {
    "id": "10001",
    "key": "TEST",
    "name": "Test Project",
    "style": "classic",
    "simplified": False,
    "projectTypeKey": "software",
}


SAMPLE_PROJECT_TEAM_MANAGED = {
    "id": "10002",
    "key": "TEAM",
    "name": "Team Managed Project",
    "style": "next-gen",
    "simplified": True,
    "projectTypeKey": "software",
}


SAMPLE_CREATE_META_RESPONSE = {
    "projects": [
        {
            "id": "10001",
            "key": "TEST",
            "issuetypes": [
                {
                    "id": "10001",
                    "name": "Task",
                    "fields": {
                        "summary": {"name": "Summary", "required": True},
                        "description": {"name": "Description", "required": False},
                        "customfield_10001": {"name": "Sprint", "required": False},
                        "customfield_10002": {
                            "name": "Story Points",
                            "required": False,
                        },
                    },
                },
                {
                    "id": "10002",
                    "name": "Story",
                    "fields": {
                        "summary": {"name": "Summary", "required": True},
                        "description": {"name": "Description", "required": False},
                        "customfield_10001": {"name": "Sprint", "required": False},
                        "customfield_10002": {
                            "name": "Story Points",
                            "required": False,
                        },
                        "customfield_10003": {"name": "Epic Link", "required": False},
                    },
                },
            ],
        }
    ]
}


SAMPLE_SCREEN_SCHEMES_RESPONSE = {
    "values": [
        {"issueTypeScreenScheme": {"id": "10001", "name": "Default Screen Scheme"}}
    ]
}


SAMPLE_SCREEN_SCHEME_MAPPING = {"values": [{"screenSchemeId": "10001"}]}


SAMPLE_SCREEN_SCHEME = {
    "id": "10001",
    "name": "Default Screen Scheme",
    "screens": {"default": 10001, "create": 10002, "edit": 10003},
}


SAMPLE_SCREEN = {"id": 10001, "name": "Default Screen"}


SAMPLE_SCREEN_TABS = [{"id": 10001, "name": "Field Tab"}]


SAMPLE_SCREEN_FIELDS = [{"id": "summary", "name": "Summary"}]


SAMPLE_CREATED_FIELD = {
    "id": "customfield_10100",
    "name": "Test Field",
    "schema": {"type": "number"},
    "custom": True,
}


SAMPLE_ALL_SCREENS = {
    "values": [
        {"id": 1, "name": "Default Screen"},
        {"id": 2, "name": "Bug Create Screen"},
    ]
}


# ========== Fixtures ==========


@pytest.fixture
def mock_jira_client():
    """Mock JiraClient for testing without API calls."""
    client = Mock()
    client.base_url = "https://test.atlassian.net"
    client.email = "test@example.com"
    client.close = Mock()
    return client


@pytest.fixture
def sample_fields_response():
    """Sample fields API response."""
    return copy.deepcopy(SAMPLE_FIELDS_RESPONSE)


@pytest.fixture
def sample_project_response():
    """Sample project API response."""
    return copy.deepcopy(SAMPLE_PROJECT_RESPONSE)


@pytest.fixture
def sample_project_team_managed():
    """Sample team-managed project response."""
    return copy.deepcopy(SAMPLE_PROJECT_TEAM_MANAGED)


@pytest.fixture
def sample_create_meta_response():
    """Sample create meta API response."""
    return copy.deepcopy(SAMPLE_CREATE_META_RESPONSE)


@pytest.fixture
def sample_screen_schemes_response():
    """Sample screen schemes response."""
    return copy.deepcopy(SAMPLE_SCREEN_SCHEMES_RESPONSE)


@pytest.fixture
def sample_screen_scheme_mapping():
    """Sample screen scheme mapping."""
    return copy.deepcopy(SAMPLE_SCREEN_SCHEME_MAPPING)


@pytest.fixture
def sample_screen_scheme():
    """Sample screen scheme."""
    return copy.deepcopy(SAMPLE_SCREEN_SCHEME)


@pytest.fixture
def sample_screen():
    """Sample screen."""
    return copy.deepcopy(SAMPLE_SCREEN)


@pytest.fixture
def sample_screen_tabs():
    """Sample screen tabs."""
    return copy.deepcopy(SAMPLE_SCREEN_TABS)


@pytest.fixture
def sample_screen_fields():
    """Sample screen fields."""
    return copy.deepcopy(SAMPLE_SCREEN_FIELDS)


@pytest.fixture
def sample_created_field():
    """Sample created field response."""
    return copy.deepcopy(SAMPLE_CREATED_FIELD)


@pytest.fixture
def sample_all_screens():
    """Sample all screens response."""
    return copy.deepcopy(SAMPLE_ALL_SCREENS)


