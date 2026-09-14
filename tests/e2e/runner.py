#!/usr/bin/env python3
"""
Help-only sufficiency arm runner.

Drives Claude Code non-interactively with ONLY the shipped plugin (the
manifest plus skills/jira/SKILL.md, the Entry-Point Hint) and the Bash
tool. A `jira-as` binary is on PATH, forced into its `simulation`
transport, with no Jira credentials in the environment -- so nothing the
model runs can reach a live site.

Confinement (review fix): `--tools Bash` restricts the available tool set
(unlike `--allowedTools`, which only pre-approves permissions for tools
that are otherwise still available -- Read/Glob/Grep/WebFetch would stay
reachable under `--allowedTools` alone). Each trial also runs with `cwd`
set to a fresh, empty temporary directory, so Claude Code does not load
this repository's own CLAUDE.md or any other file as project context;
the plugin is still loaded via an absolute `--plugin-dir` path, which
does not depend on the process's working directory.

For each task, this:
  1. Sends the plain-English prompt to Claude Code from an empty temp
     directory and captures its full tool-use transcript
     (--output-format stream-json --verbose).
  2. Extracts the LAST `jira-as ...` command the model ran as a Bash tool
     call, from that tool_use block's `input.command` field -- never from
     answer text.
  3. Re-runs that exact command in the harness, under the same simulation
     transport, and checks whether jira-as accepts it (exit 0, including a
     preview of a risk-tagged call).

A trial is "well-formed" only on that exit-0 re-run -- there is no
assertion on business content (the sufficiency test is about whether the
CLI accepts the shape of the call, not whether the result is "right").
"""

import json
import re
import shlex
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


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


def extract_last_jira_as_command(
    transcript_lines: list[str],
) -> tuple[str | None, str | None]:
    """
    Parse a Claude Code `--output-format stream-json --verbose` transcript
    (one JSON object per line) and return `(command, error)` for the LAST
    `jira-as ...` command the model ran as a Bash tool call.

    `command` is None when no jira-as command was ever run, or when the
    last Bash command containing one uses a backslash line continuation
    (rejected, not truncated). `error` names the reason in either case;
    it is None only when `command` is not None.
    """
    last_command: str | None = None
    last_error: str | None = "model never ran a jira-as command"

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
            match = JIRA_AS_COMMAND_RE.search(raw_command)
            if not match:
                continue

            if LINE_CONTINUATION_RE.search(raw_command):
                last_command = None
                last_error = (
                    "the model's last jira-as command uses a backslash line "
                    "continuation; rejected rather than silently truncated "
                    f"at the newline: {raw_command!r}"
                )
                continue

            last_command = match.group(1).strip()
            last_error = None

    return last_command, last_error


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
        Send one prompt to Claude Code, restricted to the shipped plugin
        and the Bash tool, running from `cwd` (a fresh empty directory,
        never this repository). Returns (transcript_lines, stderr).
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
            "Bash",
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

    def run_trial(self, task_id: str, prompt: str) -> TrialResult:
        """Run one cold trial: one fresh `claude` invocation from an empty
        temp directory, then a same-transport re-run of the last jira-as
        command it produced."""
        start = time.time()

        with tempfile.TemporaryDirectory(prefix="jas55-sufficiency-") as scratch_dir:
            try:
                transcript_lines, stderr = self._run_claude(prompt, cwd=scratch_dir)
            except subprocess.TimeoutExpired:
                return TrialResult(
                    task_id=task_id,
                    command=None,
                    exit_code=None,
                    well_formed=False,
                    duration=time.time() - start,
                    transcript_error=f"claude timed out after {self.timeout}s",
                )

            command, error = extract_last_jira_as_command(transcript_lines)
            if not command:
                reason = error or "model never ran a jira-as command"
                return TrialResult(
                    task_id=task_id,
                    command=None,
                    exit_code=None,
                    well_formed=False,
                    duration=time.time() - start,
                    transcript_error=f"{reason}; stderr={stderr[:500]}",
                )

        exit_code = self._replay_command(command)

        return TrialResult(
            task_id=task_id,
            command=command,
            exit_code=exit_code,
            well_formed=exit_code == 0,
            duration=time.time() - start,
        )

    def _replay_command(self, command: str) -> int:
        """Re-run the extracted jira-as command under the same simulation
        transport, in the harness (not inside the model's own turn)."""
        try:
            result = subprocess.run(
                shlex.split(command),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=self.env,
                cwd=self.plugin_dir,
            )
            return result.returncode
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            return -1

    def run_task(self, task_id: str, prompt: str, trials: int) -> list[TrialResult]:
        """Run `trials` independent cold trials for one task."""
        return [self.run_trial(task_id, prompt) for _ in range(trials)]
