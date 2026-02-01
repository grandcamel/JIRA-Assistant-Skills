"""
Test utilities for JIRA live integration tests.

This module re-exports utilities from jira_as.testing for backwards compatibility.
New code should import directly from jira_as.testing instead.

Example:
    # Preferred (new code):
    from jira_as.testing import IssueBuilder, assert_search_returns_results

    # Legacy (backwards compatible):
    from test_utils import IssueBuilder, assert_search_returns_results
"""

from jira_as.testing import (
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
    "IssueBuilder",
    "assert_issue_has_field",
    "assert_search_returns_empty",
    "assert_search_returns_results",
    "generate_unique_name",
    "get_jira_version",
    "is_cloud_instance",
    "skip_if_version_below",
    "wait_for_assignment",
    "wait_for_transition",
]
