"""
Conftest for shared live integration tests.

Re-exports fixtures for use in skill-specific live tests.
"""

import pytest

from .fixtures import (
    fresh_test_issue,
    issue_helper,
    jira_client,
    jira_connection,
    jira_info,
    search_helper,
    skip_if_cloud,
    skip_if_container,
    skip_if_no_jira,
    test_issue,
    test_project,
    test_project_key,
)

# Re-export all fixtures for pytest discovery
__all__ = [
    "jira_connection",
    "jira_client",
    "jira_info",
    "test_project_key",
    "test_project",
    "test_issue",
    "fresh_test_issue",
    "issue_helper",
    "search_helper",
    "skip_if_no_jira",
    "skip_if_container",
    "skip_if_cloud",
]
