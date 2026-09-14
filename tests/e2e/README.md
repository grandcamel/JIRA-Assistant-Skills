# Help-Only Sufficiency Arm

The end-to-end harness for JIRA-Assistant-Skills is the **help-only
sufficiency arm**: a task-level test of whether the Entry-Point Hint
(`skills/jira/SKILL.md`) alone is enough for a model to complete
representative jira-as tasks, per the atlassian-tooling-v2 spec's user
story 32 ("a task-level sufficiency test where a model given only the
Entry-Point Hint completes representative tasks, so that the help is
proven enough").

This replaced the old plugin-installation / per-skill-discovery E2E suite
when the thirteen domain skills and the hub were retired: there is
nothing left to "discover" across skills, so the arm now asks a narrower
question -- is `jira-as help` (as pointed to by the one shipped skill)
sufficient on its own?

## What the model gets, and nothing else

- The shipped plugin only: the plugin manifest plus `skills/jira/SKILL.md`,
  installed via an **absolute** `--plugin-dir` path.
- Exactly two tools, via **`--tools Bash,Skill`** -- not `--allowedTools`
  alone, which only pre-approves permission for tools that would
  otherwise still be available (Read/Glob/Grep/WebFetch would stay
  reachable under `--allowedTools` alone; per the CLI reference, `--tools`
  "omit[s] a tool to remove it from Claude's context" instead). `Skill` is
  included, and is the only tool besides `Bash`, because a plugin's
  `SKILL.md` reaches the model only through the built-in `Skill` tool --
  with `--tools Bash` alone the model could never load the Entry-Point
  Hint at all, and the arm would measure "no hint," not "the hint alone."
  A live probe found `--tools` alone is not sufficient either: under
  `--permission-mode dontAsk`, the Skill tool call was itself **denied**
  ("Permission to use Skill has been denied because Claude Code is
  running in don't ask mode"), so **`--allowedTools "Bash,Skill"`** is
  passed too, pre-approving both tools so neither is denied. See
  [cli-reference](https://code.claude.com/docs/en/cli-reference) and
  [tools-reference](https://code.claude.com/docs/en/tools-reference).
- **No MCP servers.** `--strict-mcp-config --mcp-config
  tests/e2e/empty-mcp.json` (an absolute path to `{"mcpServers": {}}`)
  keeps the operator's own configured MCP servers out of the session --
  a live probe found they otherwise still load and expose tools even
  with `--tools`/`--allowedTools` restricted to `Bash,Skill`.
- **No project context from this repository.** Each trial runs with `cwd`
  set to a fresh, empty temporary directory, so Claude Code does not load
  this repository's own `CLAUDE.md`, its files, or any other ambient
  project context -- only the plugin passed via `--plugin-dir` is present.
- A `jira-as` binary on `PATH`, forced into its `simulation` transport via
  `JIRA_AS_TRANSPORT=simulation`.
- **An allowlisted subprocess environment, not a denylisted one.** Built by
  `tests/harness_env.py`'s `build_harness_env()` (shared with the routing
  check): only `PATH`, `HOME`, `USER`, `LOGNAME` (a live probe found the
  CLI's Keychain-backed login reports "Not logged in" without USER/
  LOGNAME, not just HOME), and `TERM`/`LANG` (if present) are ever copied
  from the operator's own environment, plus `JIRA_AS_TRANSPORT=simulation`.
  `JIRA_SITE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_DEFAULT_PROJECT`,
  `ANTHROPIC_API_KEY`, and any other variable starting with `JIRA_` or
  `ANTHROPIC_` never reach the subprocess. Nothing the model runs can
  reach a live Jira site.

### Known limitation: user-level skills and the operator's global CLAUDE.md

Two gaps a live probe confirmed are not closed by any flag:

- **User-level skills.** A probe found roughly 120 skills installed at
  the user level on the probing host, all still visible to the model
  regardless of `--tools`/`--plugin-dir`/`--strict-mcp-config`. `--bare`
  would remove them, but it requires an `ANTHROPIC_API_KEY` this harness
  deliberately does not use (see Prerequisites below), and an empty
  `CLAUDE_CONFIG_DIR` loses the OAuth login instead. The mitigation is
  detection, not prevention: `runner.extract_skill_invocations` records
  **every** `Skill` tool_use in a trial's transcript, and `run_trial`
  **fails the trial outright if any loaded skill is not `jira`**. Loading
  `jira` itself is recorded as evidence the hint worked, but is not
  required for a trial to pass -- the model can complete a task by
  running `jira-as` directly once it knows to, without re-invoking the
  Skill tool on every turn.
- **The operator's global CLAUDE.md.** `HOME` is preserved (needed for
  the OAuth login above), so the operator's **global** `~/.claude/
  CLAUDE.md`, if they have one, is still loaded as context -- the
  empty-cwd confinement only rules out a *project* `CLAUDE.md`. Run the
  arm on a host with no global `~/.claude/CLAUDE.md` (or one known to
  carry no Jira-specific guidance) if this matters for a given
  measurement.

## How a trial is judged

For each cold trial:

1. Append a **fixed trailer** (`runner.PROMPT_TRAILER`) to the task's
   prompt: "Do this now with the jira-as CLI in this shell. Do not ask
   me questions. The CLI is in simulation mode: use project DEMO and
   issue DEMO-1 where a key is needed; a not-found response is expected
   and fine. When finished, reply with the exact command you ran." A
   live probe found that without this, the model would ask a
   clarifying question (e.g. "what JQL would you like?") instead of
   acting on the first task, which the harness cannot meaningfully
   score.
2. Send the combined prompt to Claude Code, from the fresh empty temp
   directory described above, and capture its full tool-use transcript
   (`--output-format stream-json --verbose`).
3. Extract **every** Bash command the model ran, verbatim, read from
   each Bash tool_use block's `input.command` field -- never inferred
   from the model's answer text (see `runner.extract_bash_commands`). A
   command that uses a backslash line continuation is **rejected** with
   that reason stated: a newline-based splitter cannot reconstruct such
   a command's true shape, so it is never matched or replayed under a
   guess.
4. Split each command into segments on newlines, `;`, `&&`, `||` and `|`
   (a shell-aware, quote-safe tokenizer -- never a lone `&`, which is
   not one of these separators and is only ever produced fused into
   `>&`), and find every segment that -- after stripping any
   redirection and a leading environment-assignment/`time` prefix -- is
   a `jira-as` invocation matching the task's `accept` list in
   `test_cases.yaml` (`runner.command_matches_accept`): a bare
   operationId matches ONLY `api call OPERATIONID` (an `api describe` of
   the same operation is a discovery step, not the action being
   performed, and does not count); `"describe:OPERATIONID"` matches
   ONLY `api describe OPERATIONID`; a contract-verb pair like
   `"issue get"` matches a contract-verb invocation. A segment
   containing `--help`/`-h` never matches, however it is otherwise
   shaped. Matching against ANY invocation, not just the last command,
   closes a gaming path: a trial that runs the right command and then a
   trailing `jira-as help` must still be able to pass. Real runs of the
   arm found the model's actual commands prefixed with
   `JIRA_AS_TRANSPORT=simulation ` (invisible to a matcher that only
   recognized `jira-as` at the very start of a command) and calling
   `--help` on the correct operation (which must not count as doing the
   task) -- the segment-and-strip approach handles both.
5. Fail the trial outright if the model loaded any **Skill** other than
   `jira` (see the known-limitation note above) before reaching step 6.
6. Re-run **every matching command's ORIGINAL, verbatim string** (not a
   re-parsed or reassembled segment) through a **real shell**
   (`bash -o pipefail -c`), from a fresh empty temp directory, under the
   same simulation environment, and classify each well-formed or not
   with `runner.classify_replay` (see below) -- **not simply "exit 0"**:
   the simulation transport's store is empty, so a well-formed call to a
   real operation legitimately exits nonzero. Manual reproductions
   confirmed a full-shell replay is required, not optional: an
   environment-variable prefix, a pipeline feeding a request body over
   stdin (`echo '{...}' | jira-as ... --body -`), `| head -N`, and any
   redirection all need real shell semantics that a direct, shell-free
   argv exec cannot reproduce. The trial passes if ANY matching
   command's replay is well-formed; `TrialResult` records every command
   the model ran and the replay outcome of every matching one, naming
   whichever one passed.

### Well-formedness against an empty store

Live probes of the simulation transport with an empty store established:

| Exit code | Condition | Well-formed? |
|---|---|---|
| `0` | any (preview, or a real call that returns an empty page) | Yes |
| `5` | JSON output has `"status": 404` and no message starting with `"Unknown operation"` | Yes -- a real `api call`/`api describe` operation, just not found |
| `1` | output contains `"(HTTP 404)"` | Yes -- the equivalent not-found shape for a contract-verb invocation |
| `5` | a message starts with `"Unknown operation"` | No -- the operation name itself does not exist |
| `2` | (usage error, e.g. a bad flag, malformed body source, or an invalid flag combination) | No |
| anything else | | No |

`classify_replay` checks stdout and stderr **together** (concatenated):
a live probe found that on `api call`, the not-found JSON payload for
exit 5 is written to **stderr** with **empty stdout** (verified:
`jira-as api call doTransition --issue-id-or-key DEMO-1 --field
transition.name="Done" --confirm` prints nothing on stdout), so the two
streams cannot be treated as mutually exclusive.

One CLI quirk noted along the way, not a harness matter: `jira-as api
--transport simulation call ...` is genuinely invalid on the pinned CLI
(`--transport` accepts only `http` or `responder`; it does not accept
`simulation` as a flag value, even though `JIRA_AS_TRANSPORT=simulation`
as an environment variable is exactly how this harness forces the
transport) -- exit 2, correctly classified as a real failure. A product
follow-up, not something this harness works around.

There is **no assertion on business content** -- the arm does not check
that the created issue looks right or that the JQL returns the issue you
meant. It only checks that the shape of the call the model produced names
a real jira-as operation. Business-logic correctness is the CLI's own
test suite's job, not this harness's.

## Evidence

Every run writes a directory `${TMPDIR:-/tmp}/jas55-sufficiency-<UTC
timestamp>/` (one per pytest session). Per trial, it contains:

- `<task>-<n>.transcript.jsonl` -- the raw `--output-format stream-json`
  transcript, exactly as captured.
- `<task>-<n>.commands.json` -- every Bash command the model ran that
  trial, its segments, whether it matched the task's accept list, and
  (for matching commands) the replay's exit code, stdout, stderr, and
  classification.

and the directory also holds a `summary.json`, updated after every
trial, recording each trial's outcome across the whole session. The
directory path is printed for every task, in `pytest`'s output and in
the failure message when a task does not reach threshold, so a scoring
question about a specific run never requires re-running the (expensive,
non-deterministic) live arm to get an answer. The routing check
(`skills/jira/tests/test_routing.py`) does the same, in a sibling
`jas55-routing-<UTC timestamp>/` directory holding each trial's
transcript and the observed skill.

## The seven tasks

`test_cases.yaml` holds seven representative, concrete tasks, each with
an `accept` list of what counts as a matching invocation:

1. Search Jira for open issues in project DEMO ordered by creation date,
   newest first.
2. Read the details of the Jira issue DEMO-1.
3. Create a Jira Task in project DEMO with the summary "Harness probe"
   (a preview is enough).
4. Add the comment "Harness probe comment" to the Jira issue DEMO-1.
5. Transition the Jira issue DEMO-1 to the status "Done".
6. Log two hours of work on the Jira issue DEMO-1.
7. Find and describe the jira-as API operation that lists a Jira issue's
   watchers.

## Thresholds and provenance

The atlassian-tooling-v2 spec named "set the sufficiency-test thresholds"
as an implementation task without ticketing it. **This plugin's 5.0.0
implementation rules the thresholds below, 2026-09-14:**

- **Five cold trials per task** (five independent, fresh `claude`
  invocations -- no session reuse).
- **A task passes at four or more well-formed trials** out of five.
- **The arm passes only when all seven tasks pass.**
- **Model: `claude-sonnet-5`** (the only floor model this harness
  exercises directly; a second floor model, if ever added, is a separate
  host capability).

These mirror the floor-eval's own four-of-five cold-trial convention
(`tests/floor_eval/README.md`) rather than inventing a new one.

## Running it

This harness launches the `claude` binary directly and is **not run in
CI** (see `.github/workflows/ci.yml`, which deselects
`tests/e2e/test_plugin_e2e.py`). It is host-triggered, the same way the
routing check (`skills/jira/tests/test_routing.py`) and the floor eval
(`tests/floor_eval/`) are -- run on fleet-policy model changes and before
each plugin release, per `docs/TESTING.md`.

### Prerequisites

- Claude Code CLI installed and authenticated with **`claude auth login`**
  (OAuth credentials live under `~/.claude/`, reachable via the preserved
  `HOME`). An `ANTHROPIC_API_KEY` exported in your shell will NOT reach
  the trial subprocess -- the allowlisted environment described above
  never copies it -- so OAuth login is the supported way to authenticate
  for this arm.
- `jira-as>=2,<3` installed and its `simulation` transport available on
  `PATH`.
- `pytest` and `pyyaml`.

### Explicit opt-in: `E2E_SUFFICIENCY=1`

Because this arm launches the real `claude` binary and spends real
tokens, it never runs silently. Without `E2E_SUFFICIENCY=1` set, every
test in this directory is **skipped with a loud reason naming the
variable** -- not a quiet pass, and not inferred from whether
`ANTHROPIC_API_KEY` or OAuth credentials happen to be present (a macOS
`claude auth login` keeps credentials in the Keychain, which would
otherwise make the arm look "enabled" and silently skip with no visible
signal). With the variable set, collection itself probes `claude
--version`; if the binary is missing, the run **fails** at that probe
rather than skipping, because an operator who set the opt-in variable
asked for a real run.

### Quick start

```bash
# Explicit opt-in is required -- this arm never runs silently
export E2E_SUFFICIENCY=1

# Run the full sufficiency arm (five cold trials per task)
pytest tests/e2e/ -v

# Override the model or per-trial timeout
pytest tests/e2e/ -v --sufficiency-model claude-sonnet-5 --sufficiency-timeout 180
```

## Test structure

```
tests/
├── harness_env.py            # Shared allowlist env builder (also used
│                              # by skills/jira/tests/test_routing.py)
├── evidence.py                # Shared run-dir/transcript/summary writer
│                              # (also used by test_routing.py)
├── test_harness_env.py       # Offline unit tests for harness_env.py
├── test_e2e_matching.py      # Offline unit tests for classify_replay,
│                              # segment splitting, and accept-list
│                              # matching
└── e2e/
    ├── __init__.py
    ├── conftest.py          # Gate + runner fixtures (uses harness_env)
    ├── empty-mcp.json       # {"mcpServers": {}} -- passed with
    │                         # --strict-mcp-config
    ├── runner.py            # SufficiencyRunner: run + replay + judge
    ├── test_cases.yaml      # The seven tasks, each with an accept list
    └── test_plugin_e2e.py   # One pytest test per task
```
