"""
Offline unit tests for tests/e2e/runner.py's pure functions: well-
formedness classification (classify_replay) and accept-list matching
(command_matches_accept, extract_jira_as_invocation,
extract_all_jira_as_invocations, find_matching_command). No subprocess
and no `claude`/`jira-as` binary is launched anywhere in this file --
every sample below is a literal, hand-written stand-in for output an
authorized live probe of the real CLI actually produced.
"""

import json

from tests.e2e.runner import (
    classify_replay,
    command_matches_accept,
    extract_all_jira_as_invocations,
    extract_jira_as_invocation,
    find_matching_command,
)

# ---------------------------------------------------------------------------
# classify_replay: well-formedness against the simulation transport's
# EMPTY store, per exact live-probe outputs.
# ---------------------------------------------------------------------------


def test_exit_0_is_well_formed():
    """`api call searchAndReconsileIssuesUsingJql ...` exits 0 with an
    empty page."""
    stdout = json.dumps({"issues": [], "total": 0})
    ok, reason = classify_replay(0, stdout, "")
    assert ok is True
    assert reason == ""


def test_exit_0_describe_is_well_formed():
    """`api describe getIssueWatchers` exits 0."""
    ok, reason = classify_replay(0, "operationId: getIssueWatchers\n...", "")
    assert ok is True
    assert reason == ""


def test_exit_5_not_found_is_well_formed():
    """`api call getIssue --issueIdOrKey DEMO-1` exits 5 with a 404 JSON
    payload against the empty simulation store -- a well-formed call to a
    real operation, just not found."""
    stdout = json.dumps(
        {"status": 404, "messages": ["Issue not found"], "errorMessages": []}
    )
    ok, reason = classify_replay(5, stdout, "")
    assert ok is True
    assert reason == ""


def test_exit_1_http_404_is_well_formed():
    """`issue get DEMO-1` (contract verb) exits 1 with the CLI's own
    error-formatted not-found message."""
    stderr = "[ERROR] Jira Error: Issue not found for key 'DEMO-1' (HTTP 404)"
    ok, reason = classify_replay(1, "", stderr)
    assert ok is True
    assert reason == ""


def test_exit_5_unknown_operation_is_not_well_formed():
    """An unknown operation ALSO exits 5, but its message starts with
    "Unknown operation" -- this is the operation name being wrong, not a
    not-found result, so it must NOT be classified well-formed."""
    stdout = json.dumps({"status": 404, "messages": ["Unknown operation: bogusOp"]})
    ok, reason = classify_replay(5, stdout, "")
    assert ok is False
    assert "unknown operation" in reason.lower()


def test_exit_2_usage_error_is_not_well_formed():
    """`api call addComment ... --body '{...}'` exits 2 with a usage
    error ("body source must be @file or -")."""
    stderr = "Error: body source must be @file or -"
    ok, reason = classify_replay(2, "", stderr)
    assert ok is False
    assert "usage" in reason.lower()


def test_exit_1_without_http_404_is_not_well_formed():
    """A contract-verb exit 1 without the (HTTP 404) marker is some other
    failure, not the recognized not-found shape."""
    ok, reason = classify_replay(1, "", "[ERROR] Something else went wrong")
    assert ok is False
    assert "HTTP 404" in reason


def test_other_exit_code_is_not_well_formed():
    ok, reason = classify_replay(17, "", "")
    assert ok is False
    assert "17" in reason


# ---------------------------------------------------------------------------
# command_matches_accept / extraction: accept-list matching for the
# read-issue and find-watchers-operation tasks' exact accept lists.
# ---------------------------------------------------------------------------

READ_ISSUE_ACCEPT = ["getIssue", "issue get"]
WATCHERS_ACCEPT = ["describe:getIssueWatchers"]


def test_api_call_matches_bare_operation_id():
    command = "jira-as api call getIssue --issueIdOrKey DEMO-1"
    assert command_matches_accept(command, READ_ISSUE_ACCEPT) is True


def test_contract_verb_matches_verb_pair():
    command = "jira-as issue get DEMO-1"
    assert command_matches_accept(command, READ_ISSUE_ACCEPT) is True


def test_describe_prefixed_entry_requires_describe_verb():
    """A bare `api call getIssueWatchers` must NOT satisfy a
    "describe:getIssueWatchers" entry -- only `api describe` does."""
    call_command = "jira-as api call getIssueWatchers --issueIdOrKey DEMO-1"
    describe_command = "jira-as api describe getIssueWatchers"
    assert command_matches_accept(call_command, WATCHERS_ACCEPT) is False
    assert command_matches_accept(describe_command, WATCHERS_ACCEPT) is True


def test_messy_command_extracts_and_then_matches():
    """`cd /tmp && jira-as api describe getIssueWatchers | head -20`: the
    extraction regex isolates the jira-as portion (dropping the `cd`
    prefix and the `| head -20` pipeline tail) before matching runs."""
    raw = "cd /tmp && jira-as api describe getIssueWatchers | head -20"
    extracted, rejection = extract_jira_as_invocation(raw)
    assert rejection is None
    assert extracted == "jira-as api describe getIssueWatchers"
    assert command_matches_accept(extracted, WATCHERS_ACCEPT) is True


def test_help_command_does_not_match_any_accept_list():
    command = "jira-as help"
    assert command_matches_accept(command, READ_ISSUE_ACCEPT) is False
    assert command_matches_accept(command, WATCHERS_ACCEPT) is False


def _bash_tool_use_event(command: str) -> str:
    """Build one stream-json transcript line for a Bash tool_use block,
    matching the shape a real `claude --output-format stream-json
    --verbose` transcript carries."""
    return json.dumps(
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "name": "Bash", "input": {"command": command}}
                ]
            },
        }
    )


def test_a_trailing_help_command_cannot_game_a_real_match():
    """The scoring fix this round closes: a trial that runs a matching
    command FIRST and a trailing `jira-as help` LAST must still find and
    replay the matching command, not fall through to "no match" because
    only the last command used to be considered."""
    transcript = [
        _bash_tool_use_event("jira-as api call getIssue --issueIdOrKey DEMO-1"),
        _bash_tool_use_event("jira-as help"),
    ]
    commands, rejections = extract_all_jira_as_invocations(transcript)
    assert commands == [
        "jira-as api call getIssue --issueIdOrKey DEMO-1",
        "jira-as help",
    ]
    assert rejections == []
    matched = find_matching_command(commands, READ_ISSUE_ACCEPT)
    assert matched == "jira-as api call getIssue --issueIdOrKey DEMO-1"


def test_a_lone_trailing_help_command_never_matches_on_its_own():
    """The inverse: if the ONLY jira-as invocation is `jira-as help`,
    there is no match -- the gaming path the old "last command" scoring
    was vulnerable to."""
    transcript = [_bash_tool_use_event("jira-as help")]
    commands, rejections = extract_all_jira_as_invocations(transcript)
    assert commands == ["jira-as help"]
    assert find_matching_command(commands, READ_ISSUE_ACCEPT) is None
