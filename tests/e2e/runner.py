#!/usr/bin/env python3
"""
Help-only sufficiency arm runner.

Drives Claude Code non-interactively with ONLY the shipped plugin (the
manifest plus skills/jira/SKILL.md, the Entry-Point Hint), the Bash tool,
and the Skill tool needed to load that hint in the first place. A
`jira-as` binary is on PATH, forced into its `simulation` transport, with
no Jira credentials in the environment -- so nothing the model runs can
reach a live site.

Confinement, refined against authorized live-CLI probes:
  - `--tools Bash,Skill` restricts the available tool set to exactly
    those two (per https://code.claude.com/docs/en/cli-reference's
    `--tools` entry: "Tools available to Claude in this session... Omit
    a tool to remove it from Claude's context"; this differs from
    `--allowedTools`, which only pre-approves permissions for tools that
    are otherwise still available). `Skill` is included, and is the ONLY
    other tool besides `Bash`, because a plugin's SKILL.md reaches the
    model through the built-in `Skill` tool
    (https://code.claude.com/docs/en/tools-reference): with `--tools
    Bash` alone the model could never load the Entry-Point Hint at all.
  - A probe also found that `--tools` alone is not enough: under
    `--permission-mode dontAsk`, the Skill tool call was itself DENIED
    ("Permission to use Skill has been denied because Claude Code is
    running in don't ask mode"). `--allowedTools "Bash,Skill"` is passed
    alongside `--tools` so both tools are pre-approved to run without a
    permission prompt.
  - `--strict-mcp-config --mcp-config <empty-mcp.json>` (absolute path)
    keeps the operator's own configured MCP servers -- which a probe
    found still load and expose tools otherwise -- out of the session
    entirely.
  - Each trial runs with `cwd` set to a fresh, empty temporary directory,
    so Claude Code does not load this repository's own CLAUDE.md or any
    other file as project context; the plugin is still loaded via an
    absolute `--plugin-dir` path, which does not depend on the process's
    working directory. The subprocess environment is built by
    tests/harness_env.py's build_harness_env(), an allowlist shared with
    the routing check (skills/jira/tests/test_routing.py).
  - One known, unavoidable gap (see tests/e2e/README.md): user-level
    skills installed on the host (not shipped with this plugin) remain
    visible to the model regardless of the flags above; `--bare` would
    remove them but requires an API key this harness does not use. A
    trial FAILS if it loaded any skill other than `jira` (see
    extract_skill_invocations / run_trial); loading `jira` is recorded
    as evidence the hint worked, but is not itself required, since the
    model can complete a task by running jira-as directly once it knows
    to.

For each task, this:
  1. Appends a fixed trailer to the task's prompt (see PROMPT_TRAILER)
     instructing the model to act now, not ask a clarifying question,
     and use the DEMO project / DEMO-1 issue the simulation transport's
     empty store expects.
  2. Sends the combined prompt to Claude Code from an empty temp
     directory and captures its full tool-use transcript
     (--output-format stream-json --verbose).
  3. Extracts EVERY `jira-as ...` command the model ran as a Bash tool
     call, from each tool_use block's `input.command` field -- never
     from answer text -- strips any shell redirection before replay (run
     1 of the arm found the model writing `2>&1`/`> file` etc., which the
     harness's no-shell subprocess replay must not see as literal
     arguments), and finds every one that matches the task's `accept`
     list (see command_matches_accept).
  4. Re-runs EVERY matching command in the harness, under the same
     simulation transport, and classifies each well-formed or not per
     classify_replay's live-probe-derived rules -- not simply "exit 0",
     since the simulation transport's empty store makes a well-formed
     call to a real operation exit 5 (contract verbs) or 1 (api
     call/describe), not 0. The trial passes if ANY matching invocation
     replays well-formed; scoring on any match, not just the first or
     last command, closes a gaming path where a trailing `jira-as help`
     would otherwise pass or fail a trial on its own.

There is no assertion on business content: only whether the shape of the
call the model produced is one jira-as accepts as a real, known
operation.
"""

import json
import re
import shlex
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

# Fixed instruction appended to every task prompt. Without it, a live
# probe found the model would ask a clarifying question (e.g. "what JQL
# would you like?") instead of acting -- which the harness cannot
# meaningfully score. Also names the DEMO project / DEMO-1 issue the
# simulation transport's empty store expects, and tells the model a
# not-found response is fine, so it does not treat that as a reason to
# retry or ask further questions.
PROMPT_TRAILER = (
    "Do this now with the jira-as CLI in this shell. Do not ask me "
    "questions. The CLI is in simulation mode: use project DEMO and "
    "issue DEMO-1 where a key is needed; a not-found response is "
    "expected and fine. When finished, reply with the exact command you "
    "ran."
)

# Absolute path to an MCP config declaring no servers at all, so the
# operator's own configured MCP servers (found by a live probe to still
# load and expose tools otherwise) never enter the session.
EMPTY_MCP_CONFIG = (Path(__file__).parent / "empty-mcp.json").resolve()


@dataclass
class ReplayOutcome:
    """Result of replaying ONE matching jira-as invocation."""

    command: str
    exit_code: int | None
    ok: bool
    reason: str = ""


@dataclass
class TrialResult:
    """
    Result of one cold trial for one task.

    `command` and `exit_code` name the ONE matching invocation that
    passed (None if none did). `commands` holds every jira-as invocation
    the model ran, matching or not, for visibility when a trial fails.
    `replay_outcomes` holds the replay outcome of every invocation that
    matched the task's accept list (a strict subset of `commands`).
    """

    task_id: str
    command: str | None
    exit_code: int | None
    well_formed: bool
    duration: float
    transcript_error: str = ""
    commands: list[str] = field(default_factory=list)
    replay_outcomes: list[ReplayOutcome] = field(default_factory=list)


# Captures a jira-as invocation from the `jira-as` token up to the next
# command separator (`;`, `&`, `|`) or newline -- never merely
# "mentioned" elsewhere in a larger command string. Anchored so it only
# matches jira-as as its own command (start of string, after a
# separator, or after a `time` prefix), not a substring of another word.
# Unlike earlier versions, this does NOT stop at `>`: run 1 of the arm
# found the model writing commands like `jira-as api describe getIssue
# --examples 2>&1`, and stopping at the bare `>` left a stray `2` as the
# last captured token (`... --examples 2`), which then failed replay
# with "Got unexpected extra argument (2)". Redirections are captured
# here and removed by strip_redirections() before replay instead.
JIRA_AS_COMMAND_RE = re.compile(r"(?:^|[;&|]\s*|\btime\s+)(jira-as\b[^;&|\n]*)")

# A backslash immediately followed by a newline: a shell line continuation.
# The extraction regex above stops at the first newline, so a continued
# command would otherwise be silently truncated to its first line -- that
# is a different, shorter command than the one the model actually ran, so
# it must be rejected rather than tested as if it were complete.
LINE_CONTINUATION_RE = re.compile(r"\\\s*\r?\n")

# A redirection operator, optionally with its target attached in the same
# token (no separating space): `2>&1`, `>&2`, `>file`, `>>file`,
# `2>file`, `2>/dev/null`, `<file`.
_OUTPUT_REDIRECTION_RE = re.compile(r"^\d*>>?&?\S*$")
_INPUT_REDIRECTION_RE = re.compile(r"^<\S*$")
# The same operator with NO target attached -- its target is therefore a
# separate following token (`2>` `/dev/null`, `>` `out.txt`) that must
# also be dropped.
_BARE_OUTPUT_REDIRECTION_RE = re.compile(r"^\d*>>?&?$")


def strip_redirections(command: str) -> str:
    """
    Remove shell redirection operators and their targets from an
    already-extracted `jira-as ...` command, so replaying it via
    subprocess (no shell involved) never sees a literal `>`/`<` token or
    its target file/fd as a stray CLI argument. Handles `2>&1`, `>&2`,
    `>file`, `>>file`, `2>file`, `2>/dev/null`, `<file`, with or without
    a space between the operator and its target.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return command

    kept: list[str] = []
    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            continue

        if _BARE_OUTPUT_REDIRECTION_RE.match(token) or token == "<":
            # Operator with no attached target: the target is the next,
            # separate token, so drop that too.
            skip_next = True
            continue

        if _OUTPUT_REDIRECTION_RE.match(token) or _INPUT_REDIRECTION_RE.match(token):
            # Target is attached to this same token.
            continue

        kept.append(token)

    return shlex.join(kept)


def extract_jira_as_invocation(raw_command: str) -> tuple[str | None, str | None]:
    """
    Extract a single jira-as invocation from one raw Bash `input.command`
    string. Returns `(command, None)` when one is found, `(None, None)`
    when the string has no jira-as invocation at all, or `(None, reason)`
    when the one found uses a backslash line continuation and is
    therefore rejected rather than silently truncated.
    """
    match = JIRA_AS_COMMAND_RE.search(raw_command)
    if not match:
        return None, None

    if LINE_CONTINUATION_RE.search(raw_command):
        return None, (
            "a jira-as command uses a backslash line continuation; "
            f"rejected rather than silently truncated: {raw_command!r}"
        )

    return match.group(1).strip(), None


def extract_all_jira_as_invocations(
    transcript_lines: list[str],
) -> tuple[list[str], list[str]]:
    """
    Parse a `--output-format stream-json --verbose` transcript (one JSON
    object per line) and return `(commands, rejections)`: every
    well-formed jira-as invocation found across all Bash tool_use blocks,
    in transcript order, and the reasons any commands were rejected
    outright (e.g. a backslash line continuation).
    """
    commands: list[str] = []
    rejections: list[str] = []

    for line in transcript_lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") != "assistant":
            continue

        message = event.get("message", {})
        for block in message.get("content", []) or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            if block.get("name") != "Bash":
                continue

            raw_command = (block.get("input") or {}).get("command", "")
            command, rejection = extract_jira_as_invocation(raw_command)
            if command:
                commands.append(command)
            elif rejection:
                rejections.append(rejection)

    return commands, rejections


def _normalize_operation_id(operation_id: str) -> str:
    """
    Normalize an operationId for comparison: lowercase, with `-` and `_`
    removed. The supervisor verified on the pinned CLI that
    `jira-as api call get-issue --issue-id-or-key DEMO-1` resolves to the
    same operation (`getIssue`) as `api call getIssue --issueIdOrKey
    DEMO-1` -- kebab-case is an accepted alias for the camelCase
    operationId, not a different operation -- so accept-list matching
    must not be case- or separator-sensitive.
    """
    return operation_id.lower().replace("-", "").replace("_", "")


def command_matches_accept(command: str, accept: list[str]) -> bool:
    """
    Check whether one already-extracted `jira-as ...` command matches a
    task's accept list. Three entry shapes:
      - `"describe:OPERATIONID"` -- matches ONLY `jira-as api describe
        OPERATIONID` (used when the task asks the model to find and
        describe an operation, not call it). A bare `api call
        OPERATIONID` of the same operation does NOT match.
      - A bare operationId (no colon, no space) -- matches ONLY
        `jira-as api call OPERATIONID`. An `api describe` of the same
        operation does NOT match: run 1 of the arm showed the model
        running `api describe X` as a discovery step for an action task,
        which must not be scored as the action having been performed.
      - A "verb pair" containing a space (e.g. `"issue get"`) -- matches
        a contract-verb invocation whose first tokens after `jira-as` are
        exactly those words, e.g. `jira-as issue get DEMO-1`.

    OperationId comparisons (both the bare and `describe:` shapes) are
    normalized per _normalize_operation_id, so `get-issue`, `getIssue`
    and `get_issue` are all treated as the same operation.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    if not tokens or tokens[0] != "jira-as":
        return False
    rest = tokens[1:]

    for entry in accept:
        if entry.startswith("describe:"):
            operation_id = entry.split(":", 1)[1]
            if (
                len(rest) >= 3
                and rest[0] == "api"
                and rest[1] == "describe"
                and _normalize_operation_id(rest[2])
                == _normalize_operation_id(operation_id)
            ):
                return True
        elif " " in entry:
            verb_tokens = entry.split(" ")
            if rest[: len(verb_tokens)] == verb_tokens:
                return True
        else:
            if (
                len(rest) >= 3
                and rest[0] == "api"
                and rest[1] == "call"
                and _normalize_operation_id(rest[2]) == _normalize_operation_id(entry)
            ):
                return True

    return False


def find_matching_commands(commands: list[str], accept: list[str]) -> list[str]:
    """Return every command (in transcript order) that matches the
    task's accept list."""
    return [c for c in commands if command_matches_accept(c, accept)]


def extract_skill_invocations(transcript_lines: list[str]) -> list[str]:
    """
    Return every skill invoked via the Skill tool, in transcript order,
    normalized to the segment after the last colon. A live probe showed
    the tool_use input is `{"skill": "jira-assistant-skills:jira"}` --
    the plugin-namespaced skill name under the key `skill`, not `name`,
    `skill_name`, or `command`.
    """
    skills: list[str] = []

    for line in transcript_lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") != "assistant":
            continue

        message = event.get("message", {})
        for block in message.get("content", []) or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            if block.get("name") != "Skill":
                continue

            skill_value = (block.get("input") or {}).get("skill")
            if skill_value:
                skills.append(str(skill_value).rsplit(":", 1)[-1])

    return skills


def classify_replay(exit_code: int, stdout: str, stderr: str) -> tuple[bool, str]:
    """
    Classify a replayed jira-as invocation as well-formed or not, per
    live-probe ground truth against the simulation transport's EMPTY
    store (not "exit 0" -- a well-formed call to a real operation
    legitimately exits nonzero there):

      - exit 0: well-formed (e.g. a preview, or a search returning an
        empty page).
      - exit 5 with JSON stdout carrying `"status": 404` and no message
        starting with "Unknown operation": well-formed -- a valid `api
        call`/`api describe` naming a real operation, just not-found
        against the empty store.
      - exit 1 with `"(HTTP 404)"` in stderr: well-formed -- the
        equivalent not-found shape for a contract-verb invocation.
      - exit 5 whose message starts with "Unknown operation": NOT
        well-formed (the operation name itself does not exist).
      - exit 2: NOT well-formed (a CLI usage error, e.g. a bad flag or
        malformed body source).
      - anything else: NOT well-formed ("other").

    Returns `(ok, reason)`; `reason` is "" when `ok` is True.
    """
    if exit_code == 0:
        return True, ""

    if exit_code == 5:
        try:
            payload = json.loads(stdout)
        except (json.JSONDecodeError, TypeError):
            return False, f"exit 5 but stdout was not valid JSON: {stdout[:300]!r}"
        messages = payload.get("messages") or []
        if any(str(m).startswith("Unknown operation") for m in messages):
            return False, f"unknown operation: {messages}"
        if payload.get("status") == 404:
            return True, ""
        return False, f"exit 5 with unexpected payload: {payload}"

    if exit_code == 1:
        if "(HTTP 404)" in stderr:
            return True, ""
        return False, f"exit 1 without (HTTP 404) in stderr: {stderr[:300]}"

    if exit_code == 2:
        return False, f"exit 2 usage error: {(stderr or stdout)[:300]}"

    return False, f"other: exit {exit_code}; stderr={stderr[:300]}"


class SufficiencyRunner:
    """Runs the help-only sufficiency arm's trials."""

    def __init__(
        self,
        plugin_dir: Path,
        timeout: int = 120,
        model: str = "claude-sonnet-5",
        env: dict[str, str] | None = None,
    ):
        # Always absolute: --plugin-dir must resolve independently of the
        # empty temp cwd each trial runs from.
        self.plugin_dir = Path(plugin_dir).resolve()
        self.timeout = timeout
        self.model = model
        self.env = env or {}

    def _run_claude(self, prompt: str, cwd: str) -> tuple[list[str], str]:
        """
        Send one prompt to Claude Code, restricted to the shipped plugin,
        the Bash and Skill tools (both pre-approved via --allowedTools so
        neither is denied under --permission-mode dontAsk), and no MCP
        servers, running from `cwd` (a fresh empty directory, never this
        repository). Returns (transcript_lines, stderr).
        """
        cmd = [
            "claude",
            "--print",
            "--output-format",
            "stream-json",
            "--verbose",
            "--permission-mode",
            "dontAsk",
            "--tools",
            "Bash,Skill",
            "--allowedTools",
            "Bash,Skill",
            "--strict-mcp-config",
            "--mcp-config",
            str(EMPTY_MCP_CONFIG),
            "--plugin-dir",
            str(self.plugin_dir),
            "--model",
            self.model,
        ]

        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            env=self.env,
            cwd=cwd,
        )

        return result.stdout.splitlines(), result.stderr

    def run_trial(self, task_id: str, prompt: str, accept: list[str]) -> TrialResult:
        """Run one cold trial: one fresh `claude` invocation from an empty
        temp directory (prompt plus the fixed trailer), then a
        same-transport re-run of EVERY jira-as command that matches the
        task's accept list. The trial passes if any of those replays is
        well-formed."""
        start = time.time()
        full_prompt = f"{prompt}\n\n{PROMPT_TRAILER}"

        with tempfile.TemporaryDirectory(prefix="jas55-sufficiency-") as scratch_dir:
            try:
                transcript_lines, stderr = self._run_claude(
                    full_prompt, cwd=scratch_dir
                )
            except subprocess.TimeoutExpired:
                return TrialResult(
                    task_id=task_id,
                    command=None,
                    exit_code=None,
                    well_formed=False,
                    duration=time.time() - start,
                    transcript_error=f"claude timed out after {self.timeout}s",
                )

            # Fail outright if the model loaded any skill other than
            # jira. User-level skills on the host remain visible to the
            # model regardless of --tools/--plugin-dir (see README); the
            # only enforcement left is to fail on the evidence. Loading
            # jira itself is recorded but not required, since the model
            # can run jira-as directly once it knows to.
            loaded_skills = extract_skill_invocations(transcript_lines)
            non_jira = [s for s in loaded_skills if s != "jira"]
            if non_jira:
                return TrialResult(
                    task_id=task_id,
                    command=None,
                    exit_code=None,
                    well_formed=False,
                    duration=time.time() - start,
                    transcript_error=f"loaded skill(s) other than jira: {non_jira}",
                )

            commands, rejections = extract_all_jira_as_invocations(transcript_lines)
            matching_commands = find_matching_commands(commands, accept)
            if not matching_commands:
                if not commands and not rejections:
                    reason = "model never ran a jira-as command"
                else:
                    reason = (
                        "no jira-as invocation matched the task's accept "
                        f"list (ran: {commands}"
                        + (f"; rejected: {rejections}" if rejections else "")
                        + ")"
                    )
                return TrialResult(
                    task_id=task_id,
                    command=None,
                    exit_code=None,
                    well_formed=False,
                    duration=time.time() - start,
                    transcript_error=f"{reason}; stderr={stderr[:500]}",
                    commands=commands,
                )

        replay_outcomes: list[ReplayOutcome] = []
        passing: ReplayOutcome | None = None
        for candidate in matching_commands:
            exit_code, replay_stdout, replay_stderr = self._replay_command(candidate)
            ok, reason = classify_replay(exit_code, replay_stdout, replay_stderr)
            outcome = ReplayOutcome(
                command=candidate, exit_code=exit_code, ok=ok, reason=reason
            )
            replay_outcomes.append(outcome)
            if ok and passing is None:
                passing = outcome

        return TrialResult(
            task_id=task_id,
            command=passing.command if passing else None,
            exit_code=passing.exit_code if passing else None,
            well_formed=passing is not None,
            duration=time.time() - start,
            transcript_error=(
                ""
                if passing
                else "no matching invocation replayed well-formed: "
                + "; ".join(f"{o.command!r} -> {o.reason}" for o in replay_outcomes)
            ),
            commands=commands,
            replay_outcomes=replay_outcomes,
        )

    def _replay_command(self, command: str) -> tuple[int, str, str]:
        """Re-run the extracted jira-as command under the same simulation
        transport, in the harness (not inside the model's own turn),
        after stripping any shell redirection the model wrote (the
        subprocess replay has no shell to interpret it). Returns
        (exit_code, stdout, stderr) for classify_replay."""
        stripped = strip_redirections(command)
        try:
            result = subprocess.run(
                shlex.split(stripped),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=self.env,
                cwd=self.plugin_dir,
            )
            return result.returncode, result.stdout, result.stderr
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError) as exc:
            return -1, "", str(exc)

    def run_task(
        self, task_id: str, prompt: str, accept: list[str], trials: int
    ) -> list[TrialResult]:
        """Run `trials` independent cold trials for one task."""
        return [self.run_trial(task_id, prompt, accept) for _ in range(trials)]
