"""SBX live integration fixtures and compatible legacy test utilities.

Run this suite only through jira-dev-host --suite. The default SBX profile
reads JIRA_SITE_URL, JIRA_EMAIL, JIRA_API_TOKEN and JIRA_DEFAULT_PROJECT
from the wrapper environment. Standalone legacy container helpers remain
exported for compatibility; the SBX fixtures never call them.
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
