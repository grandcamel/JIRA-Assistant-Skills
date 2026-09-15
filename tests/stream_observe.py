"""
Incremental stream-json observation for a live subprocess.

The two-skill routing check (skills/jira/tests/test_routing.py) only
needs to know which skill, if any, the model invoked on its first turn --
it must never block waiting for the model to go on and finish an entire
task, or for its own overall timeout, once that signal has already
arrived. Run 1 of the routing check found the opposite (blocking) design
actively harmful: three of jira-01's five trials hit the then-60s
`subprocess.run` timeout while the model was still executing a real
search after the skill had already loaded, and `subprocess.run`'s
`TimeoutExpired` handling discards the entire captured stdout -- so the
Skill tool_use block seen seconds into the run was thrown away along with
everything else, turning an observed pass into a scored miss.

`run_and_observe` launches a subprocess, feeds it a fixed input on stdin,
and reads its stdout one line at a time, calling a caller-supplied
`detect_line` function on each line as it arrives. As soon as
`detect_line` returns a non-None value, the process is terminated
(SIGTERM, a grace period, then SIGKILL) and the observation is returned
immediately -- the rest of the model's turn, and however long the task
itself would otherwise take, is never read or waited on. If no line ever
satisfies `detect_line`, the subprocess is still bounded by an overall
timeout, and is read to completion (EOF) if it exits sooner.

This module knows nothing about Claude Code, `Skill` tool_use blocks, or
jira/confluence -- `detect_line`'s return value is entirely up to the
caller (see skills/jira/tests/test_routing.py's
`extract_skill_from_transcript_line`). Kept generic so the subprocess-
management and timeout logic can be unit-tested
(tests/test_stream_observe.py) against a small, deterministic stand-in
script instead of the real, expensive, non-deterministic `claude` binary.

Two simplifications, acceptable for this module's only caller:
- `input_text` is written to stdin and the pipe is closed before any
  reading begins, rather than writing and reading concurrently. This is
  safe only because every input this harness sends is a short, fixed
  prompt that fits well within a pipe's kernel buffer -- a large input
  could deadlock against a child that writes enough output before
  reading all of its stdin.
- The overall timeout is enforced between lines via `select.select` (POSIX
  only -- fine for this repo's macOS/Linux hosts and CI): once a line
  starts arriving, `readline()` itself has no timeout, so a child that
  writes a partial line and then stalls indefinitely mid-line could block
  past the deadline. Every producer this module reads from in practice
  (Claude Code's stream-json output, and this module's own test scripts)
  writes and flushes one complete line per event, so this case does not
  arise.
"""

import select
import subprocess
import time
from typing import Callable, NamedTuple


class ProcessObservation(NamedTuple):
    """Result of watching one subprocess's stdout for a signal.

    `result` is whatever `detect_line` returned (None if it never
    returned a non-None value). `lines` holds every line read, in
    order, regardless of outcome -- including when nothing was ever
    detected. `timed_out` is True only when the overall timeout fired
    with nothing observed yet: a timeout that happens after `result` is
    already set cannot occur, since the read loop returns as soon as
    `detect_line` succeeds, but is spelled out explicitly here so a
    caller never has to guess which condition to treat as an error.
    """

    result: object | None
    lines: list[str]
    timed_out: bool


def run_and_observe(
    cmd: list[str],
    input_text: str,
    detect_line: Callable[[str], object | None],
    on_line: Callable[[str], None] | None = None,
    timeout: float = 120,
    terminate_grace: float = 5,
    **popen_kwargs,
) -> ProcessObservation:
    """
    Launch `cmd`, write `input_text` to stdin and close it, then read
    stdout line by line (stderr is discarded -- this harness only ever
    parses stdout). Each line is passed to `on_line` (if given, e.g. to
    persist it to disk immediately) and then to `detect_line`.

    Stops and returns as soon as `detect_line` returns a non-None value,
    terminating the process first: SIGTERM, then up to `terminate_grace`
    seconds to exit on its own, then SIGKILL. If the process instead
    exits on its own (EOF on stdout) or `timeout` seconds elapse first
    without a detection, returns with `result=None`; `timed_out`
    distinguishes the two.

    `popen_kwargs` (e.g. `env`, `cwd`) are forwarded to `subprocess.Popen`.
    """
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
        **popen_kwargs,
    )
    # Popen's stdin/stdout are typed as optional because they are None
    # when the corresponding stream isn't piped; both are piped above, so
    # these are never None here. Bound to locals (rather than just
    # asserted inline) so the non-optional type holds throughout the
    # function, including inside the try/finally below.
    assert proc.stdin is not None
    assert proc.stdout is not None
    stdin = proc.stdin
    stdout = proc.stdout

    lines: list[str] = []
    result: object | None = None
    timed_out = False
    deadline = time.monotonic() + timeout

    try:
        try:
            stdin.write(input_text)
            stdin.close()
        except (BrokenPipeError, OSError):
            pass  # The child may have already exited; nothing to do.

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break

            ready, _, _ = select.select([stdout], [], [], remaining)
            if not ready:
                continue  # The deadline is re-checked at the top of the loop.

            raw_line = stdout.readline()
            if raw_line == "":
                break  # EOF: the process closed stdout on its own.

            line = raw_line.rstrip("\n")
            lines.append(line)
            if on_line is not None:
                on_line(line)

            result = detect_line(line)
            if result is not None:
                break
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=terminate_grace)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        else:
            proc.wait()

        stdout.close()

    return ProcessObservation(
        result=result, lines=lines, timed_out=timed_out and result is None
    )
