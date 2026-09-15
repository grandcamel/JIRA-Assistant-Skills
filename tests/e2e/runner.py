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
  3. Extracts EVERY Bash command the model ran, verbatim (see
     extract_bash_commands). For MATCHING purposes only, any backslash
     line continuation is first joined into a single logical line (a
     continuation is ordinary shell syntax once replay runs the whole
     command through a real shell -- there is no reason left to reject
     one, only to see past it), then each command is split into segments
     on newlines, `;`, `&&`, `||` and `|` (never a lone `&`, which is not
     one of these separators and is only ever seen fused into `>&`), and
     checked for whether any segment -- after stripping redirections and
     a leading environment-assignment/`time` prefix -- is a `jira-as`
     invocation matching the task's `accept` list (see
     command_matches_accept). Run 2 of the arm found the model's real
     commands prefixed with `JIRA_AS_TRANSPORT=simulation ` (hiding the
     whole invocation from a matcher that only recognized `jira-as` at
     the very start of a segment) and calling `--help` on the right
     operation (which must not count as doing the task) -- both are
     handled here.
  4. Re-runs EVERY matching command's ORIGINAL, verbatim string -- not a
     re-parsed or re-assembled segment -- through a real shell
     (`bash -o pipefail -c`), from a fresh empty temp directory, under
     the same simulation environment. This is required for the harness
     to behave exactly as the model's own turn did: an environment-
     variable prefix, a pipeline feeding a body over stdin
     (`echo '...' | jira-as ... --body -`), `| head -N`, and any
     redirection all need real shell semantics that a direct,
     shell-free argv exec cannot reproduce. Classifies each replay
     well-formed or not with classify_replay's live-probe-derived rules
     -- not simply "exit 0" -- and the trial passes if ANY matching
     command's replay is well-formed.
  5. Persists the full transcript, every command's segments/match/replay
     outcome, and a run-wide summary to disk (see tests/evidence.py),
     so a defect in the harness's own scoring can be diagnosed from the
     record without re-running the (expensive, non-deterministic) live
     arm.

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

from tests.evidence import new_run_dir, write_json, write_transcript

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
    """Result of replaying ONE matching jira-as invocation (the ORIGINAL
    command string, via a real shell)."""

    command: str
    exit_code: int | None
    ok: bool
    reason: str = ""


@dataclass
class TrialResult:
    """
    Result of one cold trial for one task.

    `command` and `exit_code` name the ONE matching invocation that
    passed (None if none did). `commands` holds every RAW Bash command
    the model ran, matching or not, for visibility when a trial fails.
    `replay_outcomes` holds the replay outcome of every command that
    matched the task's accept list (a strict subset of `commands`).
    `skills_loaded` holds every Skill tool_use name observed, namespaced
    as the CLI reports it (e.g. `jira-assistant-skills:jira`) -- evidence
    of whether/how the model reached for the Entry-Point Hint, not a
    pass/fail signal on its own (see extract_skill_invocations). `evidence_dir`
    names where the full transcript and per-command detail for this run
    were written (see tests/evidence.py).
    """

    task_id: str
    command: str | None
    exit_code: int | None
    well_formed: bool
    duration: float
    transcript_error: str = ""
    commands: list[str] = field(default_factory=list)
    replay_outcomes: list[ReplayOutcome] = field(default_factory=list)
    skills_loaded: list[str] = field(default_factory=list)
    evidence_dir: str = ""


# A backslash immediately followed by a newline: a shell line continuation.
# For MATCHING purposes only, this is joined into a single line before
# segment splitting (a real shell -- what actually replays the command --
# treats it as ordinary syntax, so run 3 found the earlier "reject a
# continued command outright" behavior was wrong: it was rejecting
# well-formed commands, not protecting against a truncated one). A
# genuinely dangling backslash (no following newline at all) is simply
# left as a literal token for the tokenizer below to deal with -- it
# never raises, and such a token essentially never satisfies an accept
# list's structural checks.
_LINE_CONTINUATION_JOIN_RE = re.compile(r"\\\s*\r?\n")

# Command separators that start a new segment for MATCHING purposes. A
# lone `&` (background execution) is deliberately excluded: it is not
# one of the separators named for this harness, and would in any case
# only ever be produced as `>&` by the tokenizer below when it is part of
# a redirection, never as a bare separator token on its own.
_SEGMENT_SEPARATORS = {";", "&&", "||", "|"}

# Redirection operator tokens the shlex tokenizer below produces (with
# `punctuation_chars` enabled, an operator is always its own token,
# whether or not the model wrote a space before its target).
_REDIRECT_OPERATORS = {">", ">>", "<", "<<", ">&", "<&", "&>", "&>>"}

_ENV_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def _tokenize_shell_like(line: str) -> list[str]:
    """
    Tokenize one line into words plus separator/redirection tokens,
    quote-aware, using shlex's `punctuation_chars` mode so that `;`,
    `&&`, `||`, `|`, `>`, `>>`, `<` and `>&` are always their own tokens
    (whether or not the model put whitespace around them) without
    breaking a quoted argument that happens to contain one of these
    characters. Used only to find and classify jira-as segments for
    MATCHING -- the actual replay always uses the original, verbatim
    command string via a real shell (see SufficiencyRunner._replay_command).
    """
    lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        # Unbalanced quotes or a trailing escape: fall back to naive
        # whitespace splitting rather than raising out of a matcher.
        return line.split()


def join_line_continuations(raw_command: str) -> str:
    """
    Join backslash-newline shell line continuations into a single line,
    for MATCHING purposes only. Replay always uses the ORIGINAL,
    unmodified command via a real shell, where a continuation is
    ordinary, correctly-interpreted syntax; this function exists only so
    the matcher's newline-based segment splitter can see a continued
    command as the one logical line it actually is.
    """
    return _LINE_CONTINUATION_JOIN_RE.sub(" ", raw_command)


def split_into_segments(raw_command: str) -> list[list[str]]:
    """
    Split a raw Bash command into segments (lists of tokens), on
    newlines, `;`, `&&`, `||` and `|`, after first joining any backslash
    line continuation (see join_line_continuations) so a continued
    command is not misread as two separate, broken lines. Each segment
    is one candidate "simple command" to check for a jira-as invocation.
    """
    segments: list[list[str]] = []
    for line in join_line_continuations(raw_command).split("\n"):
        if not line.strip():
            continue
        tokens = _tokenize_shell_like(line)
        current: list[str] = []
        for token in tokens:
            if token in _SEGMENT_SEPARATORS:
                if current:
                    segments.append(current)
                current = []
            else:
                current.append(token)
        if current:
            segments.append(current)
    return segments


def strip_redirection_tokens(tokens: list[str]) -> list[str]:
    """
    Remove redirection operator tokens and their targets from a
    shlex-tokenized (punctuation_chars=True) token list, wherever they
    appear. A leading numeric fd (e.g. the "2" in "2>&1" / "2> file") is
    part of the redirection and is removed too.
    """
    cleaned: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]

        if (
            token.isdigit()
            and i + 1 < len(tokens)
            and tokens[i + 1] in _REDIRECT_OPERATORS
        ):
            # The fd prefix of an operator at i + 1; skip both, and the
            # operator's target (if any) below on the next loop pass.
            i += 1
            continue

        if token in _REDIRECT_OPERATORS:
            i += 1
            if i < len(tokens) and tokens[i] not in _REDIRECT_OPERATORS:
                i += 1  # the operator's target
            continue

        cleaned.append(token)
        i += 1

    return cleaned


def strip_leading_env_and_time(tokens: list[str]) -> list[str]:
    """Remove leading `NAME=value` environment assignments (quoted
    values allowed -- shlex has already resolved the quoting into a
    single token) and a leading `time`, e.g. `JIRA_AS_TRANSPORT=simulation
    jira-as help` -> `jira-as help`."""
    i = 0
    while i < len(tokens) and (
        tokens[i] == "time" or _ENV_ASSIGNMENT_RE.match(tokens[i])
    ):
        i += 1
    return tokens[i:]


def clean_segment(tokens: list[str]) -> list[str]:
    """Strip redirections and a leading env/time prefix from one
    segment's tokens, leaving what should be the bare command and its
    arguments if this segment is a jira-as invocation."""
    return strip_leading_env_and_time(strip_redirection_tokens(tokens))


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


def _rest_matches_accept(rest: list[str], accept: list[str]) -> bool:
    """Check whether `rest` (a cleaned segment's tokens after `jira-as`)
    matches a task's accept list. See command_matches_accept for the
    three entry shapes."""
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


def segment_matches_accept(tokens: list[str], accept: list[str]) -> bool:
    """
    Check whether one segment's raw tokens are a jira-as invocation that
    matches the task's accept list, after cleaning (stripping
    redirections and a leading env/time prefix). A segment whose cleaned
    tokens include `--help` or `-h` never matches: run 2 of the arm found
    `jira-as api call getIssue --help` and `jira-as lifecycle transition
    --help` counted as doing the task, when they are only discovery. A
    bare `\\` token also never matches: it only appears when the
    tokenizer's quote-aware pass failed (an unterminated escape, e.g. a
    dangling backslash with no following newline to continue) and fell
    back to a naive whitespace split -- a signal the command may be
    truncated or malformed, not something to guess a match for.
    """
    cleaned = clean_segment(tokens)
    if not cleaned or cleaned[0] != "jira-as":
        return False
    if "--help" in cleaned or "-h" in cleaned or "\\" in cleaned:
        return False
    return _rest_matches_accept(cleaned[1:], accept)


def command_matches_accept(raw_command: str, accept: list[str]) -> bool:
    """
    Check whether a RAW Bash command (as the model wrote it -- possibly
    env-prefixed, piped, chained, or redirected) contains ANY segment
    that is a jira-as invocation matching the task's accept list. Three
    entry shapes:
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
    return any(
        segment_matches_accept(segment, accept)
        for segment in split_into_segments(raw_command)
    )


def find_matching_commands(commands: list[str], accept: list[str]) -> list[str]:
    """Return every RAW command (in transcript order) that has at least
    one segment matching the task's accept list."""
    return [c for c in commands if command_matches_accept(c, accept)]


def extract_bash_commands(transcript_lines: list[str]) -> list[str]:
    """
    Parse a `--output-format stream-json --verbose` transcript (one JSON
    object per line) and return the exact, verbatim `input.command`
    string of every Bash tool_use block, in transcript order -- this is
    what gets matched (via command_matches_accept) and, if matching,
    replayed in full via a real shell. Nothing is rejected here: a
    command with a backslash line continuation is ordinary shell syntax
    once replay runs it through a real shell (see join_line_continuations
    for how MATCHING sees past one).
    """
    raw_commands: list[str] = []

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
            if not raw_command.strip():
                continue

            raw_commands.append(raw_command)

    return raw_commands


def extract_skill_invocations(transcript_lines: list[str]) -> list[str]:
    """
    Return every skill invoked via the Skill tool, in transcript order,
    namespaced exactly as the CLI reports it (e.g.
    `jira-assistant-skills:jira`) -- this is what gets persisted as
    evidence (TrialResult.skills_loaded). A live probe showed the
    tool_use input is `{"skill": "jira-assistant-skills:jira"}` -- the
    plugin-namespaced skill name under the key `skill`, not `name`,
    `skill_name`, or `command`. Callers checking WHICH skill loaded
    should compare the segment after the last colon (see run_trial).
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
                skills.append(str(skill_value))

    return skills


def classify_replay(exit_code: int, stdout: str, stderr: str) -> tuple[bool, str]:
    """
    Classify a replayed jira-as invocation as well-formed or not, per
    live-probe ground truth against the simulation transport's EMPTY
    store (not "exit 0" -- a well-formed call to a real operation
    legitimately exits nonzero there). `stdout` and `stderr` are checked
    TOGETHER (concatenated): a live probe found `api call`'s not-found
    JSON payload is written to stderr with exit 5 (not stdout, as
    earlier assumed), so the two streams can no longer be treated as
    mutually exclusive for either the JSON or the "(HTTP 404)" check.

      - exit 0: well-formed (e.g. a preview, or a search returning an
        empty page).
      - exit 5 with JSON output carrying `"status": 404` and no message
        starting with "Unknown operation": well-formed -- a valid `api
        call`/`api describe` naming a real operation, just not-found
        against the empty store.
      - exit 1 with `"(HTTP 404)"` in the output: well-formed -- the
        equivalent not-found shape for a contract-verb invocation.
      - exit 5 whose message starts with "Unknown operation": NOT
        well-formed (the operation name itself does not exist).
      - exit 2: NOT well-formed (a CLI usage error, e.g. a bad flag or
        malformed body source, or a genuinely invalid flag such as
        `api --transport simulation call ...`, which the CLI rejects
        with exit 2 -- a real failure, not a harness defect).
      - anything else: NOT well-formed ("other").

    Returns `(ok, reason)`; `reason` is "" when `ok` is True.
    """
    if exit_code == 0:
        return True, ""

    combined = stdout + stderr

    if exit_code == 5:
        try:
            payload = json.loads(combined.strip())
        except (json.JSONDecodeError, TypeError):
            return (
                False,
                f"exit 5 but stdout+stderr was not valid JSON: {combined[:300]!r}",
            )
        messages = payload.get("messages") or []
        if any(str(m).startswith("Unknown operation") for m in messages):
            return False, f"unknown operation: {messages}"
        if payload.get("status") == 404:
            return True, ""
        return False, f"exit 5 with unexpected payload: {payload}"

    if exit_code == 1:
        if "(HTTP 404)" in combined:
            return True, ""
        return False, f"exit 1 without (HTTP 404) in output: {combined[:300]}"

    if exit_code == 2:
        return False, f"exit 2 usage error: {combined[:300]}"

    return False, f"other: exit {exit_code}; output={combined[:300]}"


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

        # One evidence directory per runner (i.e. per pytest session,
        # since sufficiency_runner is a session-scoped fixture): every
        # trial's transcript and command detail lands here, plus a
        # running summary, so a scoring defect can be diagnosed from the
        # record without re-running the live arm.
        self.run_dir = new_run_dir("jas55-sufficiency")
        self._trial_counters: dict[str, int] = {}
        self._summary: dict = {
            "run_dir": str(self.run_dir),
            "model": model,
            "tasks": {},
        }

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
        temp directory (prompt plus the fixed trailer), then a real-shell
        replay of EVERY original Bash command that matches the task's
        accept list. The trial passes if any of those replays is
        well-formed. Every trial's transcript and command detail is
        persisted to self.run_dir."""
        start = time.time()
        full_prompt = f"{prompt}\n\n{PROMPT_TRAILER}"
        trial_number = self._next_trial_number(task_id)

        with tempfile.TemporaryDirectory(prefix="jas55-sufficiency-") as scratch_dir:
            try:
                transcript_lines, _claude_stderr = self._run_claude(
                    full_prompt, cwd=scratch_dir
                )
            except subprocess.TimeoutExpired:
                result = TrialResult(
                    task_id=task_id,
                    command=None,
                    exit_code=None,
                    well_formed=False,
                    duration=time.time() - start,
                    transcript_error=f"claude timed out after {self.timeout}s",
                    evidence_dir=str(self.run_dir),
                )
                self._persist_trial(task_id, trial_number, [], [], result)
                return result

        loaded_skills = extract_skill_invocations(transcript_lines)
        non_jira = [s for s in loaded_skills if s.rsplit(":", 1)[-1] != "jira"]
        if non_jira:
            result = TrialResult(
                task_id=task_id,
                command=None,
                exit_code=None,
                well_formed=False,
                duration=time.time() - start,
                transcript_error=f"loaded skill(s) other than jira: {non_jira}",
                skills_loaded=loaded_skills,
                evidence_dir=str(self.run_dir),
            )
            self._persist_trial(task_id, trial_number, transcript_lines, [], result)
            return result

        raw_commands = extract_bash_commands(transcript_lines)

        commands_record: list[dict] = []
        replay_outcomes: list[ReplayOutcome] = []
        passing: ReplayOutcome | None = None

        for raw_command in raw_commands:
            matched = command_matches_accept(raw_command, accept)
            entry: dict = {
                "raw_command": raw_command,
                "segments": split_into_segments(raw_command),
                "matched": matched,
                "replayed": False,
            }
            if matched:
                exit_code, stdout, stderr = self._replay_command(raw_command)
                ok, reason = classify_replay(exit_code, stdout, stderr)
                entry.update(
                    replayed=True,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    well_formed=ok,
                    reason=reason,
                )
                outcome = ReplayOutcome(
                    command=raw_command, exit_code=exit_code, ok=ok, reason=reason
                )
                replay_outcomes.append(outcome)
                if ok and passing is None:
                    passing = outcome
            commands_record.append(entry)

        if not raw_commands:
            transcript_error = "model never ran a Bash command"
        elif not replay_outcomes:
            transcript_error = (
                "no jira-as invocation matched the task's accept list "
                f"(ran: {raw_commands})"
            )
        elif passing is None:
            transcript_error = (
                "no matching invocation replayed well-formed: "
                + "; ".join(f"{o.command!r} -> {o.reason}" for o in replay_outcomes)
            )
        else:
            transcript_error = ""

        result = TrialResult(
            task_id=task_id,
            command=passing.command if passing else None,
            exit_code=passing.exit_code if passing else None,
            well_formed=passing is not None,
            duration=time.time() - start,
            transcript_error=transcript_error,
            commands=raw_commands,
            replay_outcomes=replay_outcomes,
            skills_loaded=loaded_skills,
            evidence_dir=str(self.run_dir),
        )
        self._persist_trial(
            task_id, trial_number, transcript_lines, commands_record, result
        )
        return result

    def _replay_command(self, raw_command: str) -> tuple[int, str, str]:
        """
        Replay the model's ORIGINAL Bash command string through a real
        shell (`bash -o pipefail -c`), from a fresh empty temp directory,
        under the same simulation environment -- not a re-parsed or
        re-executed segment. Required for env-prefixed invocations
        (`VAR=value jira-as ...`), pipelines with a stdin-fed body
        (`echo '...' | jira-as ... --body -`), `| head -N`, and any
        redirection: none of these behave correctly under a direct argv
        exec with no shell. Returns (exit_code, stdout, stderr) for
        classify_replay.
        """
        try:
            with tempfile.TemporaryDirectory(prefix="jas55-replay-") as scratch_dir:
                result = subprocess.run(
                    ["bash", "-o", "pipefail", "-c", raw_command],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    env=self.env,
                    cwd=scratch_dir,
                )
                return result.returncode, result.stdout, result.stderr
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError) as exc:
            return -1, "", str(exc)

    def _next_trial_number(self, task_id: str) -> int:
        self._trial_counters[task_id] = self._trial_counters.get(task_id, 0) + 1
        return self._trial_counters[task_id]

    def _persist_trial(
        self,
        task_id: str,
        trial_number: int,
        transcript_lines: list[str],
        commands_record: list[dict],
        result: TrialResult,
    ) -> None:
        """Write this trial's transcript and command detail, and update
        the run-wide summary.json, so the evidence is on disk even if a
        later trial or the process itself is interrupted."""
        base_name = f"{task_id}-{trial_number}"
        write_transcript(
            self.run_dir / f"{base_name}.transcript.jsonl", transcript_lines
        )
        write_json(
            self.run_dir / f"{base_name}.commands.json",
            {
                "task_id": task_id,
                "trial": trial_number,
                "commands": commands_record,
                "skills_loaded": result.skills_loaded,
                "passing_command": result.command,
                "well_formed": result.well_formed,
                "transcript_error": result.transcript_error,
            },
        )
        self._summary["tasks"].setdefault(task_id, []).append(
            {
                "trial": trial_number,
                "well_formed": result.well_formed,
                "command": result.command,
                "exit_code": result.exit_code,
                "skills_loaded": result.skills_loaded,
                "transcript_error": result.transcript_error,
            }
        )
        write_json(self.run_dir / "summary.json", self._summary)

    def run_task(
        self, task_id: str, prompt: str, accept: list[str], trials: int
    ) -> list[TrialResult]:
        """Run `trials` independent cold trials for one task."""
        return [self.run_trial(task_id, prompt, accept) for _ in range(trials)]
