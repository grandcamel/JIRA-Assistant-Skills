"""
Help-only sufficiency arm.

Is the Entry-Point Hint (skills/jira/SKILL.md) alone enough for a model to
complete representative jira-as tasks? The model gets nothing else -- no
other skill, only the Bash tool, and a `jira-as` forced into simulation
transport with no credentials, so nothing it runs can reach a live site.

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
        self.tasks = {t["id"]: t["prompt"] for t in _load_tasks(test_cases_path)}

    def _run_task(self, sufficiency_runner, task_id):
        prompt = self.tasks[task_id]
        results = sufficiency_runner.run_task(task_id, prompt, TRIALS_PER_TASK)
        well_formed = sum(1 for r in results if r.well_formed)
        assert well_formed >= MIN_PASSING_TRIALS, (
            f"[{task_id}] expected >= {MIN_PASSING_TRIALS}/{TRIALS_PER_TASK} "
            f"well-formed trials, got {well_formed}/{TRIALS_PER_TASK}\n"
            f"Prompt: {prompt}\n"
            f"Trials: {[(r.command, r.exit_code, r.transcript_error) for r in results]}"
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
