"""
Offline unit tests for tests/e2e/runner.py's pure functions: well-
formedness classification (classify_replay), redirection stripping
(strip_redirections), and accept-list matching (command_matches_accept,
extract_jira_as_invocation, extract_all_jira_as_invocations,
find_matching_commands). No subprocess and no `claude`/`jira-as` binary
is launched anywhere in this file -- every sample below is a literal,
hand-written stand-in for output an authorized live probe of the real
CLI actually produced (including, for this round, a real run of the
sufficiency arm itself).
"""

import json

from tests.e2e.runner import (
    classify_replay,
    command_matches_accept,
    extract_all_jira_as_invocations,
    extract_jira_as_invocation,
    find_matching_commands,
    strip_redirections,
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
# strip_redirections: run 1 of the sufficiency arm found the model
# writing shell redirections the no-shell subprocess replay must not see
# as literal arguments.
# ---------------------------------------------------------------------------


def test_strip_redirections_exact_run1_example():
    """The exact command from run 1's log: `2>&1` with no space, attached
    to the same token as the operator."""
    command = "jira-as api describe getIssue --examples 2>&1"
    assert strip_redirections(command) == "jira-as api describe getIssue --examples"


def test_strip_redirections_with_space_before_target():
    """A redirection with a space between the operator and its target is
    a separate token in shlex terms and must also be dropped."""
    command = "jira-as time log --help 2> /dev/null"
    assert strip_redirections(command) == "jira-as time log --help"


def test_strip_redirections_stderr_to_stdout():
    assert strip_redirections("jira-as help >&2") == "jira-as help"


def test_strip_redirections_bare_overwrite():
    assert strip_redirections("jira-as help >out.txt") == "jira-as help"
    assert strip_redirections("jira-as help > out.txt") == "jira-as help"


def test_strip_redirections_append():
    assert strip_redirections("jira-as help >>out.txt") == "jira-as help"
    assert strip_redirections("jira-as help >> out.txt") == "jira-as help"


def test_strip_redirections_stderr_to_file():
    assert strip_redirections("jira-as help 2>out.txt") == "jira-as help"
    assert strip_redirections("jira-as help 2> out.txt") == "jira-as help"


def test_strip_redirections_stderr_to_dev_null_attached():
    assert strip_redirections("jira-as help 2>/dev/null") == "jira-as help"


def test_strip_redirections_input_redirect():
    assert strip_redirections("jira-as help <input.txt") == "jira-as help"
    assert strip_redirections("jira-as help < input.txt") == "jira-as help"


def test_strip_redirections_preserves_normal_arguments():
    """A command with no redirection at all is returned unchanged
    (modulo shlex round-tripping)."""
    command = "jira-as api call getIssue --issueIdOrKey DEMO-1"
    assert strip_redirections(command) == command


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


def test_bare_operation_id_does_not_match_api_describe():
    """Run 1 found the model running `api describe X` as a discovery
    step for an action task; that must NOT count as the action having
    been performed -- a bare operationId entry matches ONLY `api call`."""
    command = "jira-as api describe getIssue"
    assert command_matches_accept(command, READ_ISSUE_ACCEPT) is False


def test_describe_prefixed_entry_requires_describe_verb():
    """A bare `api call getIssueWatchers` must NOT satisfy a
    "describe:getIssueWatchers" entry -- only `api describe` does."""
    call_command = "jira-as api call getIssueWatchers --issueIdOrKey DEMO-1"
    describe_command = "jira-as api describe getIssueWatchers"
    assert command_matches_accept(call_command, WATCHERS_ACCEPT) is False
    assert command_matches_accept(describe_command, WATCHERS_ACCEPT) is True


def test_kebab_case_operation_id_matches_camel_case_accept_entry():
    """The pinned CLI resolves `get-issue` to the same operation as
    `getIssue` (verified on the real CLI: both exit 5 not-found for
    DEMO-1, naming "operation": "getIssue") -- kebab-case is an accepted
    alias, not a different operation, so accept-list matching must
    normalize both sides (lowercase, `-`/`_` removed)."""
    command = "jira-as api call get-issue --issue-id-or-key DEMO-1"
    assert command_matches_accept(command, READ_ISSUE_ACCEPT) is True


def test_kebab_case_operation_id_matches_describe_entry():
    command = "jira-as api describe get-issue-watchers"
    assert command_matches_accept(command, WATCHERS_ACCEPT) is True


def test_unrelated_operation_id_does_not_match():
    """A different operation entirely (search-query) must not match an
    accept list scoped to a different operation (getIssue), kebab-case
    normalization notwithstanding."""
    command = "jira-as api call search-query --jql 'project = DEMO'"
    assert command_matches_accept(command, READ_ISSUE_ACCEPT) is False


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
    """A trial that runs a matching command FIRST and a trailing `jira-as
    help` LAST must still find and be able to replay the matching
    command, not fall through to "no match" because only the last
    command used to be considered."""
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
    matching = find_matching_commands(commands, READ_ISSUE_ACCEPT)
    assert matching == ["jira-as api call getIssue --issueIdOrKey DEMO-1"]


def test_a_lone_trailing_help_command_never_matches_on_its_own():
    """If the ONLY jira-as invocation is `jira-as help`, there is no
    match -- the gaming path the "last command" scoring was vulnerable
    to."""
    transcript = [_bash_tool_use_event("jira-as help")]
    commands, rejections = extract_all_jira_as_invocations(transcript)
    assert commands == ["jira-as help"]
    assert find_matching_commands(commands, READ_ISSUE_ACCEPT) == []


def test_multiple_matching_commands_are_all_returned():
    """A discovery step (api describe, which does NOT match a bare
    operationId entry) followed by two genuinely matching invocations
    yields both matches, in transcript order -- run_trial replays each
    and the trial passes if any one is well-formed."""
    transcript = [
        _bash_tool_use_event("jira-as api describe getIssueWatchers"),
        _bash_tool_use_event("jira-as api call getIssue --issueIdOrKey DEMO-1"),
        _bash_tool_use_event("jira-as issue get DEMO-1"),
    ]
    commands, _ = extract_all_jira_as_invocations(transcript)
    matching = find_matching_commands(commands, READ_ISSUE_ACCEPT)
    assert matching == [
        "jira-as api call getIssue --issueIdOrKey DEMO-1",
        "jira-as issue get DEMO-1",
    ]
