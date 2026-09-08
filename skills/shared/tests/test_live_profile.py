"""Offline contract tests for the wrapped SBX live-test profile."""

from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from skills.shared.tests.live_integration import fixtures as live_fixtures
from skills.shared.tests.live_integration.sbx_profile import (
    TrackedJiraClient,
    resolve_sbx_profile,
)


def _environment(**updates):
    values = {
        "JIRA_DEFAULT_PROJECT": "SBX",
        "JIRA_SITE_URL": "https://example.invalid",
        "JIRA_EMAIL": "tester@example.invalid",
        "JIRA_API_TOKEN": "secret",  # nosec B105
    }
    values.update(updates)
    return values


def _client(monkeypatch, responses=()):
    calls = []
    deleted = []
    queue = iter(responses)

    def post(
        self,
        endpoint,
        data=None,
        operation="create resource",
        headers=None,
        params=None,
    ):
        calls.append((endpoint, deepcopy(data), operation))
        return next(queue)

    def delete(self, endpoint):
        deleted.append(endpoint)

    class NotFound(Exception):
        status_code = 404

    def get(self, endpoint, *args, **kwargs):
        raise NotFound()

    monkeypatch.setattr("jira_as.JiraClient.post", post)
    monkeypatch.setattr("jira_as.JiraClient.delete", delete)
    monkeypatch.setattr("jira_as.JiraClient.get", get)
    return (
        TrackedJiraClient("https://example.invalid", "a", "b", run_label="run-label"),
        calls,
        deleted,
    )


@pytest.mark.parametrize("project", [None, "", "GC", "JAS", "sbx", " SBX"])
def test_profile_requires_sbx_before_credentials(project):
    with pytest.raises(ValueError, match="JIRA_DEFAULT_PROJECT must be SBX"):
        resolve_sbx_profile(_environment(JIRA_DEFAULT_PROJECT=project))


@pytest.mark.parametrize(
    "credential", ["JIRA_SITE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"]
)
@pytest.mark.parametrize("value", [None, ""])
def test_profile_requires_named_credentials_and_redacts_them(credential, value):
    environment = _environment(**{credential: value})
    with pytest.raises(ValueError, match=credential):
        resolve_sbx_profile(environment)
    assert "secret" not in repr(resolve_sbx_profile(_environment()))


def test_profile_uses_only_the_supplied_mapping(monkeypatch):
    monkeypatch.setattr("os.getenv", lambda *_: pytest.fail("environment consulted"))
    monkeypatch.setattr(
        "builtins.open", lambda *_a, **_k: pytest.fail("settings consulted")
    )
    assert resolve_sbx_profile(_environment()).project_key == "SBX"


def test_create_paths_are_guarded_labeled_and_tracked(monkeypatch):
    client, calls, _ = _client(
        monkeypatch,
        [{"key": "SBX-1", "id": "1"}, {"issues": [{"key": "SBX-2", "id": "2"}]}],
    )
    direct = {"fields": {"project": {"key": "SBX"}, "labels": ["test"]}}
    bulk = {"issueUpdates": [{"fields": {"project": "SBX", "labels": []}}]}
    client.post("/rest/api/3/issue", json=direct)
    client.post("/rest/api/3/issue/bulk", bulk)
    assert direct["fields"]["labels"] == ["test"]
    assert calls[0][1]["fields"]["labels"] == ["test", "run-label"]
    assert calls[1][1]["issueUpdates"][0]["fields"]["labels"] == ["run-label"]
    assert client.created_keys == {"SBX-1", "SBX-2"}
    assert client.created_ids == {"1", "2"}


def test_high_level_create_issue_routes_through_tracking(monkeypatch):
    client, _, _ = _client(monkeypatch, [{"key": "SBX-3", "id": "3"}])
    client.create_issue({"project": {"key": "SBX"}, "summary": "x"})
    assert client.created_keys == {"SBX-3"}


def test_non_sbx_payload_never_reaches_network(monkeypatch):
    client, calls, _ = _client(monkeypatch)
    with pytest.raises(ValueError, match="project must be SBX"):
        client.post("/rest/api/2/issue", {"fields": {"project": {"key": "GC"}}})
    assert calls == []


def test_cleanup_recovers_lost_response_and_preserves_ledger(monkeypatch):
    client, calls, deleted = _client(
        monkeypatch,
        [
            {"issues": [{"key": "SBX-9", "id": "9"}]},
            {"issues": []},
        ],
    )
    assert "remaining=0" in client.cleanup_created_issues()
    assert deleted == ["/rest/api/3/issue/SBX-9"]
    assert client.created_keys == {"SBX-9"}
    assert calls[0][0] == "/rest/api/3/search/jql"


def test_cleanup_attempts_all_keys_and_accepts_404(monkeypatch):
    client, _, deleted = _client(monkeypatch, [{"issues": []}, {"issues": []}])
    client._created_keys.update({"SBX-1", "SBX-2"})

    class NotFound(Exception):
        status_code = 404

    def delete(self, endpoint):
        deleted.append(endpoint)
        if endpoint.endswith("SBX-1"):
            raise NotFound()

    monkeypatch.setattr("jira_as.JiraClient.delete", delete)
    client.cleanup_created_issues()
    assert deleted == ["/rest/api/3/issue/SBX-1", "/rest/api/3/issue/SBX-2"]


def test_cleanup_attempts_all_keys_before_reporting_delete_error(monkeypatch):
    client, _, deleted = _client(monkeypatch, [{"issues": []}, {"issues": []}])
    client._created_keys.update({"SBX-1", "SBX-2"})

    def delete(self, endpoint):
        deleted.append(endpoint)
        if endpoint.endswith("SBX-1"):
            raise RuntimeError("private response details")

    monkeypatch.setattr("jira_as.JiraClient.delete", delete)
    with pytest.raises(RuntimeError, match="deletion errors for SBX-1") as error:
        client.cleanup_created_issues()
    assert "private response details" not in str(error.value)
    assert deleted == ["/rest/api/3/issue/SBX-1", "/rest/api/3/issue/SBX-2"]


def test_cleanup_fails_for_survivor_or_malformed_search(monkeypatch):
    client, _, _ = _client(monkeypatch, [{"issues": [{"key": "SBX-1"}]}] * 11)
    monkeypatch.setattr(client, "_CLEANUP_DELAY_SECONDS", 0)
    with pytest.raises(RuntimeError, match="issues remain"):
        client.cleanup_created_issues()
    client, _, _ = _client(monkeypatch, [{"unexpected": []}])
    with pytest.raises(RuntimeError, match="malformed"):
        client.cleanup_created_issues()


@pytest.mark.parametrize("response", [None, {}, {"key": "GC-1"}])
def test_malformed_creation_response_cannot_claim_success(monkeypatch, response):
    client, _, deleted = _client(
        monkeypatch, [response, {"issues": []}, {"issues": []}]
    )
    with pytest.raises(RuntimeError, match="malformed issue creation"):
        client.create_issue({"project": {"key": "SBX"}})
    with pytest.raises(RuntimeError, match="invalid SBX issue key"):
        client.cleanup_created_issues()
    assert deleted == []


def test_removed_label_cannot_hide_tracked_survivor(monkeypatch):
    client, _, _ = _client(monkeypatch, [{"issues": []}, {"issues": []}])
    client._created_keys.add("SBX-1")
    monkeypatch.setattr("jira_as.JiraClient.get", lambda *_a, **_k: {})
    with pytest.raises(RuntimeError, match="issues remain"):
        client.cleanup_created_issues()


def test_unavailable_search_fails_without_response_details(monkeypatch):
    client, _, _ = _client(monkeypatch)

    def unavailable(*args, **kwargs):
        raise RuntimeError("private response details")

    monkeypatch.setattr("jira_as.JiraClient.post", unavailable)
    with pytest.raises(RuntimeError, match="label search unavailable") as error:
        client.cleanup_created_issues()
    assert "private response details" not in str(error.value)
    assert "run_label=run-label" in str(error.value)


def test_search_never_authorizes_non_sbx_deletion(monkeypatch):
    client, _, deleted = _client(monkeypatch, [{"issues": [{"key": "GC-1"}]}])
    with pytest.raises(RuntimeError, match="malformed issues"):
        client.cleanup_created_issues()
    assert deleted == []


def test_invalid_bulk_payload_rejected_before_network(monkeypatch):
    client, calls, _ = _client(monkeypatch)
    with pytest.raises(ValueError, match="bulk issueUpdates"):
        client.post("/rest/api/3/issue/bulk", {"issueUpdates": [None]})
    assert calls == []


def test_project_lookup_failure_never_creates_project():
    client = Mock()
    client.get.side_effect = RuntimeError("missing project")
    with pytest.raises(RuntimeError, match="missing project"):
        live_fixtures.test_project.__wrapped__(client, "SBX")
    client.post.assert_not_called()


def test_fixture_guard_has_no_docker_fallback(monkeypatch):
    monkeypatch.setattr(live_fixtures, "os", SimpleNamespace(environ={}))
    with pytest.raises(pytest.fail.Exception, match="JIRA_DEFAULT_PROJECT must be SBX"):
        live_fixtures.sbx_profile.__wrapped__()


@pytest.mark.parametrize("cleanup_error", [False, True])
def test_client_fixture_finalizes_on_test_error_and_closes(monkeypatch, cleanup_error):
    client = Mock()
    client.cleanup_created_issues.return_value = "SBX cleanup verified: remaining=0"
    if cleanup_error:
        client.cleanup_created_issues.side_effect = RuntimeError(
            "SBX cleanup failed: survivor"
        )
    monkeypatch.setattr(live_fixtures, "TrackedJiraClient", lambda **_k: client)
    config = SimpleNamespace(pluginmanager=Mock())
    config.pluginmanager.get_plugin.return_value = None
    connection = SimpleNamespace(
        base_url="https://example.invalid",
        email="a",
        api_token="b",  # nosec B106
    )
    fixture = live_fixtures.jira_client.__wrapped__(
        connection, SimpleNamespace(config=config)
    )
    assert next(fixture) is client
    # Pytest finalizes a yielded fixture even when the test body raises.
    if cleanup_error:
        with pytest.raises(pytest.fail.Exception, match="SBX cleanup FAILED"):
            fixture.close()
    else:
        fixture.close()
        assert "remaining=0" in config._sbx_cleanup_summary
    client.cleanup_created_issues.assert_called_once()
    client.close.assert_called_once()


def test_helper_and_fresh_fixture_share_session_ledger(monkeypatch):
    client, _, _ = _client(monkeypatch, [{"key": "SBX-1"}, {"key": "SBX-2"}])
    helper = live_fixtures.IssueHelper(client, "SBX")
    helper.create(summary="offline helper")
    fresh = live_fixtures.fresh_test_issue.__wrapped__(client, {"key": "SBX"})
    assert next(fresh)["key"] == "SBX-2"
    fresh.close()
    helper.cleanup()
    assert client.created_keys == {"SBX-1", "SBX-2"}
