#!/usr/bin/env python3
"""State tracker for test remediation progress persistence."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class TestStatus(str, Enum):
    """Status of a test in the remediation process."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    FAILED = "failed"
    UNFIXABLE = "unfixable"


@dataclass
class TestState:
    """State for a single test."""
    status: TestStatus = TestStatus.PENDING
    attempts: int = 0
    conflict_attempts: int = 0
    last_error: str = ""
    last_fix_proposal: dict | None = None
    fixed_at: str | None = None
    commit_sha: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "attempts": self.attempts,
            "conflict_attempts": self.conflict_attempts,
            "last_error": self.last_error,
            "last_fix_proposal": self.last_fix_proposal,
            "fixed_at": self.fixed_at,
            "commit_sha": self.commit_sha,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TestState":
        """Create from dictionary."""
        return cls(
            status=TestStatus(data.get("status", "pending")),
            attempts=data.get("attempts", 0),
            conflict_attempts=data.get("conflict_attempts", 0),
            last_error=data.get("last_error", ""),
            last_fix_proposal=data.get("last_fix_proposal"),
            fixed_at=data.get("fixed_at"),
            commit_sha=data.get("commit_sha"),
        )


@dataclass
class RemediationState:
    """Overall state of the remediation process."""
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    iteration: int = 1
    max_attempts: int = 5
    tests: dict[str, TestState] = field(default_factory=dict)
    baseline_passing: list[str] = field(default_factory=list)
    initial_failures: list[str] = field(default_factory=list)
    current_failures: list[str] = field(default_factory=list)
    completed: bool = False
    completed_at: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "iteration": self.iteration,
            "max_attempts": self.max_attempts,
            "tests": {k: v.to_dict() for k, v in self.tests.items()},
            "baseline_passing": self.baseline_passing,
            "initial_failures": self.initial_failures,
            "current_failures": self.current_failures,
            "completed": self.completed,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RemediationState":
        """Create from dictionary."""
        state = cls(
            run_id=data.get("run_id", str(uuid.uuid4())),
            started_at=data.get("started_at", datetime.now().isoformat()),
            iteration=data.get("iteration", 1),
            max_attempts=data.get("max_attempts", 5),
            baseline_passing=data.get("baseline_passing", []),
            initial_failures=data.get("initial_failures", []),
            current_failures=data.get("current_failures", []),
            completed=data.get("completed", False),
            completed_at=data.get("completed_at"),
        )
        for test_id, test_data in data.get("tests", {}).items():
            state.tests[test_id] = TestState.from_dict(test_data)
        return state


class StateTracker:
    """Manages persistence of remediation state."""

    DEFAULT_STATE_FILE = ".remediation_state.json"

    def __init__(self, state_file: str | Path | None = None):
        """Initialize state tracker.

        Args:
            state_file: Path to state file. If None, uses default in current directory.
        """
        if state_file is None:
            self.state_file = Path(__file__).parent / self.DEFAULT_STATE_FILE
        else:
            self.state_file = Path(state_file)

        self.state: RemediationState | None = None

    def load(self) -> RemediationState:
        """Load state from file, or create new state if file doesn't exist."""
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                data = json.load(f)
            self.state = RemediationState.from_dict(data)
        else:
            self.state = RemediationState()
        return self.state

    def save(self) -> None:
        """Save current state to file."""
        if self.state is None:
            raise ValueError("No state to save. Call load() first.")

        with open(self.state_file, "w") as f:
            json.dump(self.state.to_dict(), f, indent=2)

    def reset(self, max_attempts: int = 5) -> RemediationState:
        """Create a fresh state, discarding any existing state."""
        self.state = RemediationState(max_attempts=max_attempts)
        self.save()
        return self.state

    def get_test_state(self, test_id: str) -> TestState:
        """Get state for a specific test, creating if needed."""
        if self.state is None:
            self.load()

        if test_id not in self.state.tests:
            self.state.tests[test_id] = TestState()

        return self.state.tests[test_id]

    def update_test(
        self,
        test_id: str,
        status: TestStatus | None = None,
        increment_attempts: bool = False,
        increment_conflict_attempts: bool = False,
        last_error: str | None = None,
        last_fix_proposal: dict | None = None,
        commit_sha: str | None = None,
    ) -> TestState:
        """Update state for a specific test."""
        test_state = self.get_test_state(test_id)

        if status is not None:
            test_state.status = status
            if status == TestStatus.FIXED:
                test_state.fixed_at = datetime.now().isoformat()

        if increment_attempts:
            test_state.attempts += 1

        if increment_conflict_attempts:
            test_state.conflict_attempts += 1

        if last_error is not None:
            test_state.last_error = last_error

        if last_fix_proposal is not None:
            test_state.last_fix_proposal = last_fix_proposal

        if commit_sha is not None:
            test_state.commit_sha = commit_sha

        self.save()
        return test_state

    def set_baseline(self, passing: list[str], failing: list[str]) -> None:
        """Set the baseline test results."""
        if self.state is None:
            self.load()

        self.state.baseline_passing = passing
        self.state.initial_failures = failing
        self.state.current_failures = failing.copy()

        # Initialize test states for all failing tests
        for test_id in failing:
            if test_id not in self.state.tests:
                self.state.tests[test_id] = TestState(status=TestStatus.PENDING)

        self.save()

    def update_current_failures(self, failures: list[str]) -> None:
        """Update the current list of failing tests."""
        if self.state is None:
            self.load()

        self.state.current_failures = failures
        self.save()

    def increment_iteration(self) -> int:
        """Increment the iteration counter."""
        if self.state is None:
            self.load()

        self.state.iteration += 1
        self.save()
        return self.state.iteration

    def mark_completed(self) -> None:
        """Mark the remediation as completed."""
        if self.state is None:
            self.load()

        self.state.completed = True
        self.state.completed_at = datetime.now().isoformat()
        self.save()

    def get_pending_tests(self) -> list[str]:
        """Get list of tests that still need remediation."""
        if self.state is None:
            self.load()

        return [
            test_id
            for test_id in self.state.current_failures
            if self.state.tests.get(test_id, TestState()).status
            in (TestStatus.PENDING, TestStatus.IN_PROGRESS, TestStatus.FAILED)
            and self.state.tests.get(test_id, TestState()).attempts < self.state.max_attempts
        ]

    def get_unfixable_tests(self) -> list[str]:
        """Get list of tests that exceeded max attempts."""
        if self.state is None:
            self.load()

        return [
            test_id
            for test_id, test_state in self.state.tests.items()
            if test_state.status == TestStatus.UNFIXABLE
            or test_state.attempts >= self.state.max_attempts
        ]

    def get_fixed_tests(self) -> list[str]:
        """Get list of successfully fixed tests."""
        if self.state is None:
            self.load()

        return [
            test_id
            for test_id, test_state in self.state.tests.items()
            if test_state.status == TestStatus.FIXED
        ]

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the current state."""
        if self.state is None:
            self.load()

        return {
            "run_id": self.state.run_id,
            "iteration": self.state.iteration,
            "total_initial_failures": len(self.state.initial_failures),
            "current_failures": len(self.state.current_failures),
            "fixed": len(self.get_fixed_tests()),
            "unfixable": len(self.get_unfixable_tests()),
            "pending": len(self.get_pending_tests()),
            "completed": self.state.completed,
        }
