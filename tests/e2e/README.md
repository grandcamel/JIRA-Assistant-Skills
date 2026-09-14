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
  installed via `--plugin-dir`.
- The Bash tool only (`--allowedTools Bash`).
- A `jira-as` binary on `PATH`, forced into its `simulation` transport via
  `JIRA_AS_TRANSPORT=simulation`.
- **No Jira credentials in the environment at all** (`JIRA_SITE_URL`,
  `JIRA_EMAIL`, `JIRA_API_TOKEN`, and profile-specific token variables are
  stripped before the subprocess is launched). Nothing the model runs can
  reach a live Jira site.

## How a trial is judged

For each cold trial:

1. Send the task's plain-English prompt to Claude Code and capture its
   full tool-use transcript (`--output-format stream-json`).
2. Extract the **last** `jira-as ...` command the model ran as a Bash
   tool call.
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

### Quick start

```bash
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
