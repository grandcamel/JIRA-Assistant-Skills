#!/usr/bin/env python3
"""Test runner wrapper for routing tests."""

import logging
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a single test."""

    test_id: str
    passed: bool
    input_text: str = ""
    expected_skill: str = ""
    actual_skill: str = ""
    response_text: str = ""
    duration_ms: int = 0
    error_message: str = ""


@dataclass
class TestSuiteResult:
    """Result of running a test suite."""

    passed: list[TestResult] = field(default_factory=list)
    failed: list[TestResult] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    total_duration_ms: int = 0
    error: str | None = None

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate as a percentage."""
        total = len(self.passed) + len(self.failed)
        if total == 0:
            return 0.0
        return (len(self.passed) / total) * 100

    @property
    def all_passed(self) -> bool:
        """Check if all tests passed."""
        return len(self.failed) == 0 and len(self.passed) > 0


class TestRunner:
    """Wrapper for running routing tests."""

    TESTS_DIR = Path(__file__).parent
    TEST_FILE = TESTS_DIR / "test_routing.py"

    def __init__(self, tests_dir: Path | None = None, otel: bool = True):
        """Initialize test runner.

        Args:
            tests_dir: Directory containing test files. If None, uses default.
            otel: Whether to enable OpenTelemetry export (default: True)
        """
        self.tests_dir = tests_dir or self.TESTS_DIR
        self.otel = otel

    def run_single_test(
        self,
        test_id: str,
        model: str = "haiku",
        timeout: int = 180,
    ) -> TestResult:
        """Run a single test by ID.

        Args:
            test_id: The test ID (e.g., "TC001")
            model: Claude model to use
            timeout: Timeout in seconds

        Returns:
            Test result
        """
        cmd = [
            "pytest",
            str(self.TEST_FILE),
            "-v",
            "-k",
            test_id,
            "--model",
            model,
            "--tb=short",
            "-x",  # Stop on first failure
        ]

        if self.otel:
            cmd.append("--otel")

        logger.info(f"Running test {test_id} with model {model}")
        logger.debug(f"Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.tests_dir,
            )
        except subprocess.TimeoutExpired:
            logger.warning(f"Test {test_id} timed out after {timeout}s")
            return TestResult(
                test_id=test_id,
                passed=False,
                error_message=f"Test timed out after {timeout}s",
            )

        # Parse output
        output = result.stdout + result.stderr
        passed = result.returncode == 0

        # Try to extract more details from output
        test_result = TestResult(
            test_id=test_id,
            passed=passed,
            error_message="" if passed else self._extract_error(output),
        )

        # Extract details from verbose output if available
        self._parse_test_output(test_result, output)

        logger.info(f"Test {test_id}: {'PASSED' if passed else 'FAILED'}")

        return test_result

    def run_tests(
        self,
        test_ids: list[str] | None = None,
        model: str = "haiku",
        parallel: int = 1,
        timeout: int = 600,
    ) -> TestSuiteResult:
        """Run multiple tests.

        Args:
            test_ids: List of test IDs to run. If None, runs all tests.
            model: Claude model to use
            parallel: Number of parallel workers (requires pytest-xdist)
            timeout: Timeout in seconds for the entire suite

        Returns:
            Suite result with passed/failed tests
        """
        cmd = [
            "pytest",
            str(self.TEST_FILE),
            "-v",
            "--model",
            model,
            "--tb=short",
        ]

        if self.otel:
            cmd.append("--otel")

        if test_ids:
            # Build filter expression
            filter_expr = " or ".join(test_ids)
            cmd.extend(["-k", filter_expr])

        if parallel > 1:
            cmd.extend(["-n", str(parallel)])

        logger.info(
            f"Running {len(test_ids) if test_ids else 'all'} tests with model {model}"
        )
        logger.debug(f"Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.tests_dir,
            )
        except subprocess.TimeoutExpired:
            logger.error(f"Test suite timed out after {timeout}s")
            return TestSuiteResult(error=f"Test suite timed out after {timeout}s")

        return self._parse_suite_output(result.stdout + result.stderr)

    def run_full_suite(
        self,
        model: str = "haiku",
        parallel: int = 1,
        timeout: int = 2400,
    ) -> TestSuiteResult:
        """Run the full test suite.

        Args:
            model: Claude model to use
            parallel: Number of parallel workers
            timeout: Timeout in seconds

        Returns:
            Suite result
        """
        return self.run_tests(
            test_ids=None,
            model=model,
            parallel=parallel,
            timeout=timeout,
        )

    def _extract_error(self, output: str) -> str:
        """Extract error message from pytest output."""
        # Look for assertion error
        match = re.search(r"AssertionError: (.+?)(?:\n|$)", output)
        if match:
            return match.group(1).strip()

        # Look for E lines (pytest error output)
        e_lines = re.findall(r"^E\s+(.+)$", output, re.MULTILINE)
        if e_lines:
            return " ".join(e_lines[:3])

        # Look for FAILED marker
        match = re.search(r"FAILED .+ - (.+?)(?:\n|$)", output)
        if match:
            return match.group(1).strip()

        return "Unknown error"

    def _parse_test_output(self, result: TestResult, output: str) -> None:
        """Parse verbose test output to extract details."""
        # Try to extract expected/actual skill from assertion
        match = re.search(
            r"Expected skill[:\s]+(\S+).*?Actual[:\s]+(\S+)",
            output,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            result.expected_skill = match.group(1)
            result.actual_skill = match.group(2)

        # Try to extract input text
        match = re.search(r"Input[:\s]+[\"'](.+?)[\"']", output, re.IGNORECASE)
        if match:
            result.input_text = match.group(1)

    def _parse_suite_output(self, output: str) -> TestSuiteResult:
        """Parse pytest output to extract all test results."""
        suite_result = TestSuiteResult()

        # Parse individual test results - multiple formats to handle
        # Sequential: test_routing.py::test_routing[TC001-...] PASSED
        # Parallel (xdist): [gw0] PASSED test_routing.py::test_routing[TC001-...]
        # Parallel (xdist): test_routing.py::test_routing[TC001-...]
        # followed by PASSED/FAILED on same or next line

        test_patterns = [
            # Standard pytest verbose format: test_routing.py::test_direct_routing[TC001] PASSED
            re.compile(
                r"test_routing\.py::test_\w+\[(\w+)\]\s+(PASSED|FAILED|SKIPPED)"
            ),
            # pytest-xdist format: [gwN] [NN%] STATUS test_routing.py::test_direct_routing[TC001]
            re.compile(
                r"\[gw\d+\]\s+\[\s*\d+%\]\s+(PASSED|FAILED|SKIPPED)\s+test_routing\.py::test_\w+\[(\w+)\]"
            ),
        ]

        found_tests = set()

        for pattern in test_patterns:
            for match in pattern.finditer(output):
                groups = match.groups()
                # Handle different group orders
                if groups[0] in ("PASSED", "FAILED", "SKIPPED"):
                    status, test_id = groups[0], groups[1]
                else:
                    test_id, status = groups[0], groups[1]

                # Avoid duplicates
                if test_id in found_tests:
                    continue
                found_tests.add(test_id)

                if status == "PASSED":
                    suite_result.passed.append(TestResult(test_id=test_id, passed=True))
                elif status == "FAILED":
                    # Try to extract error for this test
                    error = self._extract_test_error(output, test_id)
                    suite_result.failed.append(
                        TestResult(test_id=test_id, passed=False, error_message=error)
                    )
                elif status == "SKIPPED":
                    suite_result.skipped.append(test_id)

        # Parse summary line if available
        # Format: === 38 passed, 31 failed, 10 skipped in 123.45s ===
        summary_match = re.search(
            r"=+ (\d+) passed(?:, (\d+) failed)?(?:, (\d+) skipped)? in ([\d.]+)s =+",
            output,
        )
        if summary_match:
            duration_s = float(summary_match.group(4))
            suite_result.total_duration_ms = int(duration_s * 1000)

        logger.info(
            f"Suite complete: {len(suite_result.passed)} passed, "
            f"{len(suite_result.failed)} failed, {len(suite_result.skipped)} skipped"
        )

        return suite_result

    def _extract_test_error(self, output: str, test_id: str) -> str:
        """Extract error message for a specific test from suite output."""
        # Look for the FAILED section for this test - multiple formats
        patterns = [
            rf"FAILED test_routing\.py::test_\w+\[{test_id}\] - (.+?)(?:\n|$)",
            rf"FAILED test_routing\.py::test_\w+\[{test_id}-[^\]]+\] - (.+?)(?:\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1).strip()

        return "Unknown error"

    def _get_golden_test_set(self) -> list[dict]:
        """Import and return the GOLDEN_TEST_SET."""
        import sys

        # Add tests directory to path if not already there
        tests_dir = str(self.tests_dir)
        if tests_dir not in sys.path:
            sys.path.insert(0, tests_dir)

        try:
            # Force reimport to pick up latest changes
            if "test_routing" in sys.modules:
                del sys.modules["test_routing"]

            from test_routing import GOLDEN_TESTS

            return GOLDEN_TESTS
        except ImportError as e:
            logger.warning(f"Could not import test data: {e}")
            return []

    def get_test_info(self, test_id: str) -> dict | None:
        """Get test case information from test data.

        Args:
            test_id: The test ID

        Returns:
            Dictionary with test info or None if not found
        """
        for test in self._get_golden_test_set():
            if test.get("id") == test_id:
                return test

        return None

    def get_all_test_ids(self) -> list[str]:
        """Get list of all test IDs."""
        return [test["id"] for test in self._get_golden_test_set()]

    def detect_regressions(
        self,
        baseline: list[str],
        current_result: TestSuiteResult,
    ) -> list[str]:
        """Detect tests that regressed from passing to failing.

        Args:
            baseline: List of test IDs that were passing before
            current_result: Current test suite result

        Returns:
            List of test IDs that regressed
        """
        {r.test_id for r in current_result.passed}
        current_failing = {r.test_id for r in current_result.failed}

        regressions = [test_id for test_id in baseline if test_id in current_failing]

        if regressions:
            logger.warning(f"Detected {len(regressions)} regressions: {regressions}")

        return regressions
