#!/usr/bin/env python3
"""
Help-only sufficiency arm runner.

Drives Claude Code non-interactively with ONLY the shipped plugin (the
manifest plus skills/jira/SKILL.md, the Entry-Point Hint) and the Bash
tool. A `jira-as` binary is on PATH, forced into its `simulation`
transport, with no Jira credentials in the environment -- so nothing the
model runs can reach a live site.

For each task, this:
  1. Sends the plain-English prompt to Claude Code and captures its full
     tool-use transcript (--output-format stream-json).
  2. Extracts the LAST `jira-as ...` command the model ran as a Bash tool
     call.
  3. Re-runs that exact command in the harness, under the same simulation
     transport, and checks whether jira-as accepts it (exit 0, including a
     preview of a risk-tagged call).

A trial is "well-formed" only on that exit-0 re-run -- there is no
assertion on business content (spec L94's sufficiency test is about
whether the CLI accepts the shape of the call, not whether the result is
"right").
"""

import json
import re
import shlex
import subprocess
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


# Matches a `jira-as ...` invocation as its own command, or chained after
# `;`, `&&`, `|`, or a leading shell prompt -- not merely mentioned in prose.
JIRA_AS_COMMAND_RE = re.compile(r"(?:^|[;&|]|\btime\b)\s*jira-as\b.*", re.MULTILINE)


def extract_last_jira_as_command(transcript_lines: list[str]) -> str | None:
    """
    Parse a Claude Code `--output-format stream-json` transcript (one JSON
    object per line) and return the LAST `jira-as ...` Bash command the
    model ran, or None if it never ran one.
    """
    last_command: str | None = None

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

            command = (block.get("input") or {}).get("command", "")
            match = JIRA_AS_COMMAND_RE.search(command)
            if match:
                last_command = match.group(0).strip()

    return last_command


class SufficiencyRunner:
    """Runs the help-only sufficiency arm's trials."""

    def __init__(
        self,
        plugin_dir: Path,
        timeout: int = 120,
        model: str = "claude-sonnet-5",
        env: dict[str, str] | None = None,
    ):
        self.plugin_dir = plugin_dir
        self.timeout = timeout
        self.model = model
        self.env = env or {}

    def _run_claude(self, prompt: str) -> tuple[list[str], str]:
        """
        Send one prompt to Claude Code, restricted to the shipped plugin
        and the Bash tool. Returns (transcript_lines, stderr).
        """
        cmd = [
            "claude",
            "--print",
            "--output-format",
            "stream-json",
            "--verbose",
            "--permission-mode",
            "dontAsk",
            "--allowedTools",
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
            cwd=self.plugin_dir,
        )

        return result.stdout.splitlines(), result.stderr

    def run_trial(self, task_id: str, prompt: str) -> TrialResult:
        """Run one cold trial: one fresh `claude` invocation, then a
        same-transport re-run of the last jira-as command it produced."""
        start = time.time()

        try:
            transcript_lines, stderr = self._run_claude(prompt)
        except subprocess.TimeoutExpired:
            return TrialResult(
                task_id=task_id,
                command=None,
                exit_code=None,
                well_formed=False,
                duration=time.time() - start,
                transcript_error=f"claude timed out after {self.timeout}s",
            )

        command = extract_last_jira_as_command(transcript_lines)
        if not command:
            return TrialResult(
                task_id=task_id,
                command=None,
                exit_code=None,
                well_formed=False,
                duration=time.time() - start,
                transcript_error=f"model never ran a jira-as command; stderr={stderr[:500]}",
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
