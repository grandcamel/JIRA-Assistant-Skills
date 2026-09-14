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
     from answer text -- and picks the FIRST one that matches the task's
     `accept` list (see command_matches_accept). Scoring on any matching
     invocation, not just the last command, closes a gaming path where a
     trailing `jira-as help` would otherwise pass trivially.
  4. Re-runs that matched command in the harness, under the same
     simulation transport, and classifies it well-formed or not per
     classify_replay's live-probe-derived rules -- not simply "exit 0",
     since the simulation transport's empty store makes a well-formed
     call to a real operation exit 5 (contract verbs) or 1 (api
     call/describe), not 0.

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
from dataclasses import dataclass
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
class TrialResult:
    """Result of one cold trial for one task."""

    task_id: str
    command: str | None
    exit_code: int | None
    well_formed: bool
    duration: float
    transcript_error: str = ""


# Captures a jira-as invocation from the `jira-as` token up to the next
# command separator (`;`, `&`, `|`), redirect (`>`), or newline -- never
# merely "mentioned" elsewhere in a larger command string. Anchored so it
# only matches jira-as as its own command (start of string, after a
# separator, or after a `time` prefix), not a substring of another word.
JIRA_AS_COMMAND_RE = re.compile(r"(?:^|[;&|]\s*|\btime\s+)(jira-as\b[^;&|>\n]*)")

# A backslash immediately followed by a newline: a shell line continuation.
# The extraction regex above stops at the first newline, so a continued
# command would otherwise be silently truncated to its first line -- that
# is a different, shorter command than the one the model actually ran, so
# it must be rejected rather than tested as if it were complete.
LINE_CONTINUATION_RE = re.compile(r"\\\s*\r?\n")


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


def command_matches_accept(command: str, accept: list[str]) -> bool:
    """
    Check whether one already-extracted `jira-as ...` command matches a
    task's accept list. Three entry shapes:
      - `"describe:OPERATIONID"` -- matches ONLY `jira-as api describe
        OPERATIONID` (used when the task asks the model to find and
        describe an operation, not call it).
      - A bare operationId (no colon, no space) -- matches `jira-as api
        call OPERATIONID` or `jira-as api describe OPERATIONID`.
      - A "verb pair" containing a space (e.g. `"issue get"`) -- matches
        a contract-verb invocation whose first tokens after `jira-as` are
        exactly those words, e.g. `jira-as issue get DEMO-1`.
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
                and rest[2] == operation_id
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
                and rest[1] in ("call", "describe")
                and rest[2] == entry
            ):
                return True

    return False


def find_matching_command(commands: list[str], accept: list[str]) -> str | None:
    """Return the FIRST command (in transcript order) that matches the
    task's accept list, or None if none do."""
    for command in commands:
        if command_matches_accept(command, accept):
            return command
    return None


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
        same-transport re-run of the first jira-as command that matches
        the task's accept list."""
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
            matched_command = find_matching_command(commands, accept)
            if not matched_command:
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
                )

        exit_code, replay_stdout, replay_stderr = self._replay_command(matched_command)
        ok, reason = classify_replay(exit_code, replay_stdout, replay_stderr)

        return TrialResult(
            task_id=task_id,
            command=matched_command,
            exit_code=exit_code,
            well_formed=ok,
            duration=time.time() - start,
            transcript_error="" if ok else reason,
        )

    def _replay_command(self, command: str) -> tuple[int, str, str]:
        """Re-run the extracted jira-as command under the same simulation
        transport, in the harness (not inside the model's own turn).
        Returns (exit_code, stdout, stderr) for classify_replay."""
        try:
            result = subprocess.run(
                shlex.split(command),
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
