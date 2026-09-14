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
- The Bash tool only, via **`--tools Bash`** -- not `--allowedTools`, which
  only pre-approves permission for tools that would otherwise still be
  available (Read/Glob/Grep/WebFetch would stay reachable under
  `--allowedTools` alone). `--tools` restricts the tool set itself.
- **No project context from this repository.** Each trial runs with `cwd`
  set to a fresh, empty temporary directory, so Claude Code does not load
  this repository's own `CLAUDE.md`, its files, or any other ambient
  project context -- only the plugin passed via `--plugin-dir` is present.
- A `jira-as` binary on `PATH`, forced into its `simulation` transport via
  `JIRA_AS_TRANSPORT=simulation`.
- **No Jira credentials in the environment at all** (`JIRA_SITE_URL`,
  `JIRA_EMAIL`, `JIRA_API_TOKEN`, and profile-specific token variables are
  stripped before the subprocess is launched). Nothing the model runs can
  reach a live Jira site.

## How a trial is judged

For each cold trial:

1. Send the task's plain-English prompt to Claude Code, from the fresh
   empty temp directory described above, and capture its full tool-use
   transcript (`--output-format stream-json --verbose`).
2. Extract the **last** `jira-as ...` command the model ran, read from the
   Bash tool_use block's `input.command` field -- never inferred from the
   model's answer text. The command is captured from the `jira-as` token
   up to the next command separator (`;`, `&`, `|`), redirect (`>`), or
   newline. A command that uses a backslash line continuation is
   **rejected as a failed trial** with that reason stated, rather than
   silently truncated to its first line (a truncated command is not the
   command the model actually ran).
3. Re-run that exact command in the harness, under the same simulation
   transport, and check whether `jira-as` accepts it: exit code 0,
   including a risk-tagged call that only previews (preview-by-default is
   an accept, not a failure).

There is **no assertion on business content** -- the arm does not check
that the created issue looks right or that the JQL returns the issue you
meant. It only checks that the shape of the call the model produced is
one jira-as accepts. Business-logic correctness is the CLI's own test
suite's job, not this harness's.

## The seven tasks

`test_cases.yaml` holds seven representative tasks, one line of plain
English each:

1. Search issues with a JQL query.
2. Read one issue.
3. Create an issue in a project (a preview is enough).
4. Add a comment to an issue.
5. Transition an issue to a named status.
6. Log two hours of work on an issue.
7. Find and describe the operation that lists an issue's watchers.

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

- Claude Code CLI installed and authenticated:
  ```bash
  export ANTHROPIC_API_KEY="sk-ant-..."
  # or: claude auth login
  ```
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
tests/e2e/
├── __init__.py
├── conftest.py          # Simulation-env + runner fixtures
├── runner.py            # SufficiencyRunner: run + replay + judge
├── test_cases.yaml      # The seven representative tasks
└── test_plugin_e2e.py   # One pytest test per task
```
