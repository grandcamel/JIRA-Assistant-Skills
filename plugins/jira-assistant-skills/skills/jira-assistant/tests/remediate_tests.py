#!/usr/bin/env python3
"""Automated test remediation system for routing tests.

This script iteratively fixes failing routing tests by:
1. Running the test suite to identify failures
2. Using Claude to analyze failures and propose fixes
3. Applying fixes to SKILL.md files
4. Validating fixes with fast (haiku) then production (opus) tests
5. Handling conflicts and regressions
6. Committing successful fixes incrementally
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

from claude_analyzer import ClaudeAnalyzer, FixProposal, TestCase
from skill_editor import SkillEditor
from state_tracker import StateTracker, TestStatus
from test_runner import TestRunner, TestSuiteResult


# Configure logging
def setup_logging(
    log_file: Path | None = None, verbose: bool = False
) -> logging.Logger:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )

    return logging.getLogger(__name__)


# OpenTelemetry integration
def setup_otel() -> bool:
    """Set up OpenTelemetry if endpoint is available."""
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return False

    try:
        from opentelemetry import metrics, trace
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            {
                "service.name": "routing-test-remediation",
                "service.version": "1.0.0",
            }
        )

        # Traces
        trace_provider = TracerProvider(resource=resource)
        trace_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces"))
        )
        trace.set_tracer_provider(trace_provider)

        # Metrics
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics"),
            export_interval_millis=10000,
        )
        metrics.set_meter_provider(
            MeterProvider(resource=resource, metric_readers=[metric_reader])
        )

        logging.info(f"OpenTelemetry configured with endpoint: {endpoint}")
        return True

    except ImportError:
        logging.warning("OpenTelemetry packages not installed")
        return False
    except Exception as e:
        logging.warning(f"Failed to setup OpenTelemetry: {e}")
        return False


class RemediationEngine:
    """Main orchestrator for test remediation."""

    def __init__(
        self,
        max_attempts: int = 5,
        fast_model: str = "haiku",
        production_model: str = "sonnet",
        parallel: int = 4,
        suite_timeout: int = 2400,
        log_file: Path | None = None,
        verbose: bool = False,
    ):
        """Initialize remediation engine.

        Args:
            max_attempts: Maximum fix attempts per test
            fast_model: Model for fast iteration tests
            production_model: Model for production validation
            parallel: Number of parallel test workers
            suite_timeout: Timeout in seconds for full test suite
            log_file: Path to log file
            verbose: Enable verbose logging
        """
        self.max_attempts = max_attempts
        self.fast_model = fast_model
        self.production_model = production_model
        self.parallel = parallel
        self.suite_timeout = suite_timeout

        self.logger = setup_logging(log_file, verbose)
        self.otel_enabled = setup_otel()

        self.state_tracker = StateTracker()
        self.skill_editor = SkillEditor()
        self.claude_analyzer = ClaudeAnalyzer(
            skill_editor=self.skill_editor,
            model=fast_model,
        )
        self.test_runner = TestRunner()

        # Track fix attempts for alternative proposals
        self.fix_attempts: dict[str, list[FixProposal]] = {}

        # OTel instruments
        if self.otel_enabled:
            from opentelemetry import metrics, trace

            self.tracer = trace.get_tracer(__name__)
            meter = metrics.get_meter(__name__)
            self.tests_fixed_counter = meter.create_counter(
                "tests_fixed", description="Number of tests fixed"
            )
            self.tests_failed_counter = meter.create_counter(
                "tests_failed", description="Number of tests that couldn't be fixed"
            )
            self.fix_attempts_histogram = meter.create_histogram(
                "fix_attempts", description="Number of attempts to fix a test"
            )

    def run(self, resume: bool = False) -> bool:
        """Run the full remediation process.

        Args:
            resume: Whether to resume from a previous run

        Returns:
            True if all tests pass, False otherwise
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Automated Test Remediation")
        self.logger.info("=" * 60)

        # Load or create state
        if resume and self.state_tracker.state_file.exists():
            state = self.state_tracker.load()
            self.logger.info(
                f"Resuming run {state.run_id}, iteration {state.iteration}"
            )
        else:
            state = self.state_tracker.reset(max_attempts=self.max_attempts)
            self.logger.info(f"Starting new run {state.run_id}")

        iteration = 0
        max_iterations = 10  # Safety limit

        while iteration < max_iterations:
            iteration += 1
            self.state_tracker.state.iteration = iteration
            self.state_tracker.save()

            self.logger.info(f"\n{'=' * 60}")
            self.logger.info(f"ITERATION {iteration}")
            self.logger.info(f"{'=' * 60}")

            # Run initial/current test suite
            self.logger.info("Running full test suite (fast mode)...")
            suite_result = self.test_runner.run_full_suite(
                model=self.fast_model,
                parallel=self.parallel,
                timeout=self.suite_timeout,
            )

            if suite_result.error:
                self.logger.error(f"Test suite error: {suite_result.error}")
                return False

            # Update baseline on first iteration
            if iteration == 1:
                passing_ids = [r.test_id for r in suite_result.passed]
                failing_ids = [r.test_id for r in suite_result.failed]
                self.state_tracker.set_baseline(passing_ids, failing_ids)
                self.logger.info(
                    f"Baseline: {len(passing_ids)} passing, {len(failing_ids)} failing"
                )

            # Check if all tests pass
            if suite_result.all_passed:
                self.logger.info("\n" + "=" * 60)
                self.logger.info("ALL TESTS PASSING!")
                self.logger.info("=" * 60)
                self.state_tracker.mark_completed()
                return True

            # Update current failures
            failing_ids = [r.test_id for r in suite_result.failed]
            self.state_tracker.update_current_failures(failing_ids)

            # Get pending tests
            pending = self.state_tracker.get_pending_tests()
            if not pending:
                self.logger.info("No more tests to remediate")
                break

            self.logger.info(f"\nTests to remediate: {len(pending)}")

            # Remediate each failing test
            for test_id in pending:
                if not self._remediate_test(test_id):
                    self.logger.warning(f"Could not fix {test_id}")

            # Check if any progress was made
            if iteration > 1:
                prev_failures = len(self.state_tracker.state.initial_failures)
                curr_failures = len(failing_ids)
                if curr_failures >= prev_failures:
                    self.logger.warning("No progress made this iteration")

        # Final production validation
        self.logger.info("\nRunning final production validation...")
        final_result = self.test_runner.run_full_suite(
            model=self.production_model,
            parallel=self.parallel,
            timeout=self.suite_timeout,
        )

        self._print_summary(final_result)

        return final_result.all_passed

    def _remediate_test(self, test_id: str) -> bool:
        """Attempt to remediate a single failing test.

        Args:
            test_id: The test ID to remediate

        Returns:
            True if test was fixed, False otherwise
        """
        self.logger.info(f"\n--- Remediating {test_id} ---")

        # Get test info
        test_info = self.test_runner.get_test_info(test_id)
        if not test_info:
            self.logger.error(f"Could not find test info for {test_id}")
            return False

        test_state = self.state_tracker.get_test_state(test_id)

        if test_state.attempts >= self.max_attempts:
            self.logger.warning(f"{test_id}: Max attempts reached, marking unfixable")
            self.state_tracker.update_test(test_id, status=TestStatus.UNFIXABLE)
            return False

        # Update status
        self.state_tracker.update_test(test_id, status=TestStatus.IN_PROGRESS)

        # Create test case for analysis
        test_case = TestCase(
            test_id=test_id,
            input_text=test_info.get("input", ""),
            expected_skill=test_info.get("expected_skill", ""),
            category=test_info.get("category", ""),
        )

        # Run initial test to get actual skill
        initial_result = self.test_runner.run_single_test(
            test_id, model=self.fast_model
        )
        if initial_result.passed:
            self.logger.info(f"{test_id}: Already passing!")
            self.state_tracker.update_test(test_id, status=TestStatus.FIXED)
            return True

        test_case.actual_skill = initial_result.actual_skill
        test_case.response_text = initial_result.response_text

        # Get or generate fix proposal
        if test_id not in self.fix_attempts:
            self.fix_attempts[test_id] = []

        if self.fix_attempts[test_id]:
            # Generate alternative fix
            self.logger.info(
                f"{test_id}: Generating alternative fix (attempt {test_state.attempts + 1})"
            )
            fix = self.claude_analyzer.generate_alternative_fix(
                test_case, self.fix_attempts[test_id]
            )
        else:
            # Initial analysis
            self.logger.info(f"{test_id}: Analyzing failure...")
            fix = self.claude_analyzer.analyze_failure(test_case)

        self.fix_attempts[test_id].append(fix)
        self.logger.info(f"{test_id}: Analysis: {fix.analysis}")

        if not fix.changes:
            self.logger.warning(f"{test_id}: No changes proposed")
            self.state_tracker.update_test(
                test_id,
                increment_attempts=True,
                last_error="No changes proposed",
            )
            return False

        # Apply fix
        self.logger.info(f"{test_id}: Applying {len(fix.changes)} change(s)...")
        try:
            self.skill_editor.apply_changes(fix.changes, backup=True)
        except Exception as e:
            self.logger.error(f"{test_id}: Failed to apply changes: {e}")
            self.state_tracker.update_test(
                test_id,
                increment_attempts=True,
                last_error=str(e),
            )
            return False

        # Test with fast model
        self.logger.info(f"{test_id}: Testing with {self.fast_model}...")
        fast_result = self.test_runner.run_single_test(test_id, model=self.fast_model)

        if not fast_result.passed:
            self.logger.warning(f"{test_id}: Fast test failed, rolling back")
            self.skill_editor.restore_all()
            self.state_tracker.update_test(
                test_id,
                increment_attempts=True,
                last_error=fast_result.error_message,
                last_fix_proposal={"analysis": fix.analysis, "changes": fix.changes},
            )
            return False

        # Test with production model
        self.logger.info(f"{test_id}: Testing with {self.production_model}...")
        prod_result = self.test_runner.run_single_test(
            test_id, model=self.production_model
        )

        if not prod_result.passed:
            self.logger.warning(f"{test_id}: Production test failed, rolling back")
            self.skill_editor.restore_all()
            self.state_tracker.update_test(
                test_id,
                increment_attempts=True,
                last_error=prod_result.error_message,
            )
            return False

        # Run regression check
        self.logger.info(f"{test_id}: Checking for regressions...")
        regression_result = self.test_runner.run_full_suite(
            model=self.fast_model,
            parallel=self.parallel,
            timeout=self.suite_timeout,
        )

        baseline_passing = self.state_tracker.state.baseline_passing
        regressions = self.test_runner.detect_regressions(
            baseline_passing, regression_result
        )

        if regressions:
            self.logger.warning(f"{test_id}: Caused regressions: {regressions}")
            test_state = self.state_tracker.get_test_state(test_id)

            if test_state.conflict_attempts >= 2:
                # Try conflict resolution
                self.logger.info(f"{test_id}: Attempting conflict resolution...")
                return self._resolve_conflict(test_id, test_case, fix, regressions[0])
            else:
                # Simple rollback and retry
                self.skill_editor.restore_all()
                self.state_tracker.update_test(
                    test_id,
                    increment_attempts=True,
                    increment_conflict_attempts=True,
                    last_error=f"Caused regressions: {regressions}",
                )
                return False

        # Success! Commit the fix
        self.logger.info(f"{test_id}: Fix successful, committing...")
        commit_sha = self._commit_fix(test_id, fix)

        self.state_tracker.update_test(
            test_id,
            status=TestStatus.FIXED,
            commit_sha=commit_sha,
            last_fix_proposal={"analysis": fix.analysis, "changes": fix.changes},
        )

        # Clear backups after successful commit
        self.skill_editor.cleanup_backups(keep_latest=0)

        # Update baseline to include this test as passing
        self.state_tracker.state.baseline_passing.append(test_id)
        self.state_tracker.save()

        if self.otel_enabled:
            self.tests_fixed_counter.add(1, {"test_id": test_id})
            self.fix_attempts_histogram.record(
                test_state.attempts + 1, {"test_id": test_id}
            )

        self.logger.info(f"{test_id}: FIXED!")
        return True

    def _resolve_conflict(
        self,
        test_a_id: str,
        test_a_case: TestCase,
        test_a_fix: FixProposal,
        regressed_test_id: str,
    ) -> bool:
        """Attempt to resolve a conflict between two tests.

        Args:
            test_a_id: The test we were fixing
            test_a_case: Test case for test A
            test_a_fix: The fix that caused the regression
            regressed_test_id: The test that regressed

        Returns:
            True if conflict was resolved, False otherwise
        """
        self.logger.info(
            f"Resolving conflict between {test_a_id} and {regressed_test_id}"
        )

        # Rollback first
        self.skill_editor.restore_all()

        # Get info for regressed test
        regressed_info = self.test_runner.get_test_info(regressed_test_id)
        if not regressed_info:
            self.logger.error(
                f"Could not find info for regressed test {regressed_test_id}"
            )
            return False

        test_b_case = TestCase(
            test_id=regressed_test_id,
            input_text=regressed_info.get("input", ""),
            expected_skill=regressed_info.get("expected_skill", ""),
            category=regressed_info.get("category", ""),
        )

        # Get conflict resolution from Claude
        resolution = self.claude_analyzer.resolve_conflict(
            test_a_case, test_a_fix, test_b_case
        )

        if not resolution.changes:
            self.logger.warning("No conflict resolution proposed")
            self.state_tracker.update_test(
                test_a_id,
                increment_attempts=True,
                last_error="No conflict resolution proposed",
            )
            return False

        # Apply resolution
        self.logger.info(f"Applying conflict resolution: {resolution.analysis}")
        try:
            self.skill_editor.apply_changes(resolution.changes, backup=True)
        except Exception as e:
            self.logger.error(f"Failed to apply conflict resolution: {e}")
            return False

        # Test both tests
        self.logger.info(f"Testing both {test_a_id} and {regressed_test_id}...")
        result_a = self.test_runner.run_single_test(test_a_id, model=self.fast_model)
        result_b = self.test_runner.run_single_test(
            regressed_test_id, model=self.fast_model
        )

        if not result_a.passed or not result_b.passed:
            self.logger.warning("Conflict resolution failed")
            self.skill_editor.restore_all()
            self.state_tracker.update_test(
                test_a_id,
                increment_attempts=True,
                last_error="Conflict resolution failed",
            )
            return False

        # Verify with production model
        self.logger.info("Verifying conflict resolution with production model...")
        result_a = self.test_runner.run_single_test(
            test_a_id, model=self.production_model
        )
        result_b = self.test_runner.run_single_test(
            regressed_test_id, model=self.production_model
        )

        if not result_a.passed or not result_b.passed:
            self.logger.warning("Conflict resolution failed production validation")
            self.skill_editor.restore_all()
            self.state_tracker.update_test(
                test_a_id,
                increment_attempts=True,
                last_error="Conflict resolution failed production validation",
            )
            return False

        # Full regression check
        regression_result = self.test_runner.run_full_suite(
            model=self.fast_model,
            parallel=self.parallel,
            timeout=self.suite_timeout,
        )

        baseline = self.state_tracker.state.baseline_passing
        new_regressions = self.test_runner.detect_regressions(
            baseline, regression_result
        )

        if new_regressions:
            self.logger.warning(
                f"Conflict resolution caused new regressions: {new_regressions}"
            )
            self.skill_editor.restore_all()
            self.state_tracker.update_test(
                test_a_id,
                increment_attempts=True,
                last_error=f"New regressions: {new_regressions}",
            )
            return False

        # Success! Commit
        commit_sha = self._commit_fix(
            test_a_id,
            resolution,
            message_suffix=f" (also fixes conflict with {regressed_test_id})",
        )

        self.state_tracker.update_test(
            test_a_id,
            status=TestStatus.FIXED,
            commit_sha=commit_sha,
        )

        self.skill_editor.cleanup_backups(keep_latest=0)

        self.logger.info(
            f"Conflict between {test_a_id} and {regressed_test_id} resolved!"
        )
        return True

    def _commit_fix(
        self,
        test_id: str,
        fix: FixProposal,
        message_suffix: str = "",
    ) -> str:
        """Commit a fix to git.

        Args:
            test_id: The test ID that was fixed
            fix: The fix that was applied
            message_suffix: Additional text for commit message

        Returns:
            The commit SHA
        """
        # Determine which skills were modified
        skills_modified = set()
        for change in fix.changes:
            skill = change.get("skill", "")
            if skill:
                skills_modified.add(skill.replace("jira-", ""))

        # Build commit message
        if len(skills_modified) == 1:
            scope = f"jira-{next(iter(skills_modified))}"
        else:
            scope = "jira-assistant"

        message = f"""fix({scope}): improve routing for {test_id}{message_suffix}

{fix.analysis}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"""

        # Stage and commit
        try:
            # Stage all SKILL.md changes
            subprocess.run(
                ["git", "add", "-A", "*.md"],
                cwd=self.skill_editor.skills_base_path,
                check=True,
                capture_output=True,
            )

            # Commit
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.skill_editor.skills_base_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Get commit SHA
            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.skill_editor.skills_base_path,
                check=True,
                capture_output=True,
                text=True,
            )

            return sha_result.stdout.strip()[:7]

        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Git commit failed: {e.stderr if e.stderr else e}")
            return ""

    def _print_summary(self, final_result: TestSuiteResult) -> None:
        """Print a summary of the remediation run."""
        summary = self.state_tracker.get_summary()

        self.logger.info("\n" + "=" * 60)
        self.logger.info("REMEDIATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Run ID: {summary['run_id']}")
        self.logger.info(f"Iterations: {summary['iteration']}")
        self.logger.info(f"Initial failures: {summary['total_initial_failures']}")
        self.logger.info(f"Fixed: {summary['fixed']}")
        self.logger.info(f"Unfixable: {summary['unfixable']}")
        self.logger.info(f"Final pass rate: {final_result.pass_rate:.1f}%")

        if final_result.failed:
            self.logger.info("\nRemaining failures:")
            for result in final_result.failed:
                self.logger.info(f"  - {result.test_id}: {result.error_message}")

        fixed_tests = self.state_tracker.get_fixed_tests()
        if fixed_tests:
            self.logger.info("\nFixed tests:")
            for test_id in fixed_tests:
                test_state = self.state_tracker.get_test_state(test_id)
                self.logger.info(
                    f"  - {test_id} (commit: {test_state.commit_sha}, "
                    f"attempts: {test_state.attempts})"
                )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated test remediation for routing tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full remediation (default: 4 parallel workers)
  python remediate_tests.py

  # Resume a previous run
  python remediate_tests.py --resume

  # Use more attempts and verbose logging
  python remediate_tests.py --max-attempts 10 --verbose

  # Use 8 parallel workers with longer timeout
  python remediate_tests.py --parallel 8 --suite-timeout 3600
""",
    )

    parser.add_argument(
        "--max-attempts",
        type=int,
        default=5,
        help="Maximum fix attempts per test (default: 5)",
    )
    parser.add_argument(
        "--fast-model",
        default="haiku",
        help="Model for fast iteration (default: haiku)",
    )
    parser.add_argument(
        "--production-model",
        default="sonnet",
        help="Model for production validation (default: sonnet)",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=4,
        help="Number of parallel test workers (default: 4)",
    )
    parser.add_argument(
        "--suite-timeout",
        type=int,
        default=2400,
        help="Timeout in seconds for full test suite (default: 2400 = 40 min)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from a previous run",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path(__file__).parent / "remediation.log",
        help="Path to log file",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    engine = RemediationEngine(
        max_attempts=args.max_attempts,
        fast_model=args.fast_model,
        production_model=args.production_model,
        parallel=args.parallel,
        suite_timeout=args.suite_timeout,
        log_file=args.log_file,
        verbose=args.verbose,
    )

    success = engine.run(resume=args.resume)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
