"""
Live integration test infrastructure for JIRA Assistant Skills.

This package provides fixtures and utilities for testing against a real
JIRA instance (Cloud or Data Center).

Usage in skill tests:
    # In your skill's tests/live_integration/conftest.py
    pytest_plugins = ["fixtures"]

Environment Variables:
    JIRA_TEST_URL: JIRA instance URL
    JIRA_TEST_EMAIL: User email for authentication
    JIRA_TEST_TOKEN: API token for authentication
    JIRA_TEST_PROJECT: Test project key (default: SKILLSTEST)
"""

from .fixtures import (
    IssueHelper,
    SearchHelper,
    wait_for_indexing,
)
from .jira_container import (
    JiraConnection,
    JiraContainer,
    cleanup_connection,
    get_jira_connection,
)
from .test_utils import (
    IssueBuilder,
    assert_issue_has_field,
    assert_search_returns_empty,
    assert_search_returns_results,
    generate_unique_name,
    get_jira_version,
    is_cloud_instance,
    skip_if_version_below,
    wait_for_assignment,
    wait_for_transition,
)

__all__ = [
    # Connection
    "JiraConnection",
    "JiraContainer",
    "get_jira_connection",
    "cleanup_connection",
    # Fixtures
    "IssueHelper",
    "SearchHelper",
    "wait_for_indexing",
    # Test utilities
    "IssueBuilder",
    "assert_search_returns_results",
    "assert_search_returns_empty",
    "assert_issue_has_field",
    "get_jira_version",
    "skip_if_version_below",
    "is_cloud_instance",
    "wait_for_transition",
    "wait_for_assignment",
    "generate_unique_name",
]
