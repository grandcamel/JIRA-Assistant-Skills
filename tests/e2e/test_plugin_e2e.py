"""
Help-only sufficiency arm.

Is the Entry-Point Hint (skills/jira/SKILL.md) alone enough for a model to
complete representative jira-as tasks? The model gets the shipped plugin,
the Bash and Skill tools (Skill is required to load the hint at all), no
MCP servers, and a `jira-as` forced into simulation transport with no
credentials, so nothing it runs can reach a live site. Each task's prompt
gets a fixed trailer (runner.PROMPT_TRAILER) telling the model to act now
rather than ask a clarifying question. A trial passes when any jira-as
invocation in its transcript matches the task's `accept` list (see
test_cases.yaml and runner.command_matches_accept) and that invocation's
replay classifies well-formed (runner.classify_replay) -- and fails
outright if the model loaded any skill other than `jira` (see
runner.extract_skill_invocations and README.md's known-limitation note
about user-level skills on the host).

Thresholds (see README.md for provenance and the ruling date): five cold
trials per task; a task passes at four or more well-formed trials; the
arm passes only when all seven tasks pass. Model: claude-sonnet-5.

Run with: pytest tests/e2e/ -v
Not run in CI: this launches the `claude` binary. See
.github/workflows/ci.yml, which deselects this file.
"""

import pytest
import yaml

pytestmark = [pytest.mark.e2e, pytest.mark.slow]

TRIALS_PER_TASK = 5
MIN_PASSING_TRIALS = 4


def _load_tasks(test_cases_path):
    with open(test_cases_path) as f:
        data = yaml.safe_load(f)
    return data.get("tasks", [])


class TestSufficiencyArm:
    """One test per representative task; each runs its own cold trials."""

    @pytest.fixture(autouse=True)
    def _tasks(self, test_cases_path):
        self.tasks = {
            t["id"]: (t["prompt"], t["accept"]) for t in _load_tasks(test_cases_path)
        }

    def _run_task(self, sufficiency_runner, task_id):
        prompt, accept = self.tasks[task_id]
        results = sufficiency_runner.run_task(task_id, prompt, accept, TRIALS_PER_TASK)
        well_formed = sum(1 for r in results if r.well_formed)

        if well_formed < MIN_PASSING_TRIALS:
            trial_reports = []
            for i, r in enumerate(results, 1):
                if r.replay_outcomes:
                    outcomes = "; ".join(
                        f"{o.command!r} -> exit {o.exit_code}, "
                        + ("ok" if o.ok else f"FAIL ({o.reason})")
                        for o in r.replay_outcomes
                    )
                else:
                    outcomes = "(no matching invocation replayed)"
                trial_reports.append(
                    f"  trial {i}: well_formed={r.well_formed} passed={r.command!r}\n"
                    f"    all commands run: {r.commands}\n"
                    f"    matching-command replays: {outcomes}\n"
                    f"    transcript_error: {r.transcript_error}"
                )
            pytest.fail(
                f"[{task_id}] expected >= {MIN_PASSING_TRIALS}/{TRIALS_PER_TASK} "
                f"well-formed trials, got {well_formed}/{TRIALS_PER_TASK}\n"
                f"Prompt: {prompt}\nAccept: {accept}\n" + "\n".join(trial_reports)
            )

    def test_search_jql(self, sufficiency_runner):
        self._run_task(sufficiency_runner, "search-jql")

    def test_read_issue(self, sufficiency_runner):
        self._run_task(sufficiency_runner, "read-issue")

    def test_create_issue(self, sufficiency_runner):
        self._run_task(sufficiency_runner, "create-issue")

    def test_add_comment(self, sufficiency_runner):
        self._run_task(sufficiency_runner, "add-comment")

    def test_transition_issue(self, sufficiency_runner):
        self._run_task(sufficiency_runner, "transition-issue")

    def test_log_work(self, sufficiency_runner):
        self._run_task(sufficiency_runner, "log-work")

    def test_find_watchers_operation(self, sufficiency_runner):
        self._run_task(sufficiency_runner, "find-watchers-operation")
