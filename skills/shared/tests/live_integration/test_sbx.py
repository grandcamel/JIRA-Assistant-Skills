"""Host-only acceptance probes; the session fixture verifies final deletion."""

import pytest

pytestmark = [pytest.mark.live, pytest.mark.destructive]


def test_session_issue_is_in_sbx(jira_client, test_issue):
    issue = jira_client.get(f"/rest/api/3/issue/{test_issue['key']}")
    assert issue["fields"]["project"]["key"] == "SBX"


def test_helper_and_direct_creation(jira_client, issue_helper):
    helper_issue = issue_helper.create(summary="[Test] SBX helper acceptance")
    direct_issue = jira_client.create_issue(
        {
            "project": {"key": "SBX"},
            "summary": "[Test] SBX direct-client acceptance",
            "issuetype": {"name": "Task"},
        }
    )
    for created in (helper_issue, direct_issue):
        issue = jira_client.get(f"/rest/api/3/issue/{created['key']}")
        assert issue["fields"]["project"]["key"] == "SBX"
    # Deliberately leave direct_issue for the session cleanup assertion.
