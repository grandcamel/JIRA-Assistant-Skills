#!/usr/bin/env python3
"""
E2E Test Runner for Claude Code Plugins

Executes test cases defined in YAML against the Claude Code CLI.
"""

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class TestResult:
    """Result of a single test execution."""

    test_id: str
    name: str
    status: TestStatus
    duration: float
    output: str = ""
    error: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SuiteResult:
    """Result of a test suite execution."""

    suite_name: str
    description: str
    tests: list[TestResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.PASSED)

    @property
    def failed(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.FAILED)

    @property
    def total(self) -> int:
        return len(self.tests)


class ClaudeCodeRunner:
    """Wrapper for executing Claude Code CLI commands."""

    def __init__(
        self,
        working_dir: Path,
        timeout: int = 120,
        model: str = "claude-sonnet-4-20250514",
        verbose: bool = False,
    ):
        self.working_dir = working_dir
        self.timeout = timeout
        self.model = model
        self.verbose = verbose
        self._check_prerequisites()

    def _check_prerequisites(self):
        """Verify Claude Code CLI is available."""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Claude CLI error: {result.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                "Claude Code CLI not found. Install: npm install -g @anthropic-ai/claude-code"
            )

    def _check_authentication(self) -> bool:
        """Check if authentication is configured."""
        if os.environ.get("ANTHROPIC_API_KEY"):
            return True
        claude_dir = Path.home() / ".claude"
        return bool(claude_dir.exists() and (claude_dir / "credentials.json").exists())

    def send_prompt(self, prompt: str, timeout: int | None = None) -> dict[str, Any]:
        """Send a prompt to Claude Code and capture the response."""
        timeout = timeout or self.timeout
        start_time = time.time()

        cmd = [
            "claude",
            "--print",
            "--output-format",
            "text",
            "--model",
            self.model,
            "--max-turns",
            "1",
            prompt,
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "CLAUDE_CODE_SKIP_OOBE": "1"},
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "exit_code": result.returncode,
                "duration": time.time() - start_time,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Command timed out after {timeout}s",
                "exit_code": -1,
                "duration": timeout,
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "exit_code": -1,
                "duration": time.time() - start_time,
            }

    def install_plugin(self, plugin_path: str = ".") -> dict[str, Any]:
        """Install a plugin from the given path."""
        return self.send_prompt(f"/plugin {plugin_path}")


class TestCaseValidator:
    """Validates test output against expected outcomes."""

    @staticmethod
    def validate(output: str, error: str, expect: dict[str, Any]) -> dict[str, Any]:
        """Validate output against expectations."""
        failures = []
        details = {}
        combined_output = f"{output}\n{error}".lower()

        if expect.get("success") is True:
            if "error:" in error.lower() or "exception" in error.lower():
                failures.append("Expected success but got error")

        if "output_contains" in expect:
            for expected_text in expect["output_contains"]:
                if expected_text.lower() not in combined_output:
                    failures.append(f"Output missing: '{expected_text}'")
                else:
                    details[f"contains_{expected_text}"] = True

        if "output_contains_any" in expect:
            found_any = False
            for expected_text in expect["output_contains_any"]:
                if expected_text.lower() in combined_output:
                    found_any = True
                    break
            if not found_any:
                failures.append(
                    f"Output missing any of: {expect['output_contains_any']}"
                )

        if expect.get("no_errors"):
            error_patterns = [r"error:", r"exception:", r"traceback", r"failed:"]
            for pattern in error_patterns:
                if re.search(pattern, combined_output, re.IGNORECASE):
                    if "error handling" not in combined_output:
                        failures.append(f"Found error pattern: {pattern}")
                        break

        if expect.get("no_crashes"):
            crash_patterns = [
                r"segmentation fault",
                r"core dumped",
                r"fatal error",
                r"panic:",
            ]
            for pattern in crash_patterns:
                if re.search(pattern, combined_output, re.IGNORECASE):
                    failures.append(f"Found crash indicator: {pattern}")

        return {"passed": len(failures) == 0, "failures": failures, "details": details}


class E2ETestRunner:
    """Main test runner that orchestrates E2E tests."""

    def __init__(
        self,
        test_cases_path: Path,
        working_dir: Path,
        timeout: int = 120,
        model: str = "claude-sonnet-4-20250514",
        verbose: bool = False,
    ):
        self.test_cases_path = test_cases_path
        self.working_dir = working_dir
        self.timeout = timeout
        self.model = model
        self.verbose = verbose
        self.claude = ClaudeCodeRunner(
            working_dir=working_dir,
            timeout=timeout,
            model=model,
            verbose=verbose,
        )
        self.validator = TestCaseValidator()

    def load_test_cases(self) -> dict[str, Any]:
        """Load test cases from YAML file."""
        with open(self.test_cases_path) as f:
            return yaml.safe_load(f)

    def run_test(self, test: dict[str, Any]) -> TestResult:
        """Run a single test case."""
        test_id = test["id"]
        name = test["name"]
        prompt = test["prompt"]
        expect = test.get("expect", {})
        timeout = test.get("timeout", self.timeout)

        if self.verbose:
            print(f"  Running: {name}")

        result = self.claude.send_prompt(prompt, timeout=timeout)

        if result["exit_code"] == -1 and "timed out" in result["error"]:
            return TestResult(
                test_id=test_id,
                name=name,
                status=TestStatus.TIMEOUT,
                duration=result["duration"],
                output=result["output"],
                error=result["error"],
            )

        validation = self.validator.validate(result["output"], result["error"], expect)
        status = TestStatus.PASSED if validation["passed"] else TestStatus.FAILED

        return TestResult(
            test_id=test_id,
            name=name,
            status=status,
            duration=result["duration"],
            output=result["output"],
            error=result["error"],
            details={"validation": validation, "exit_code": result["exit_code"]},
        )

    def run_suite(self, suite_name: str, suite: dict[str, Any]) -> SuiteResult:
        """Run all tests in a suite."""
        result = SuiteResult(
            suite_name=suite_name, description=suite.get("description", "")
        )

        if self.verbose:
            print(f"\nSuite: {suite_name}")

        for test in suite.get("tests", []):
            test_result = self.run_test(test)
            result.tests.append(test_result)

            if self.verbose:
                symbol = "✓" if test_result.status == TestStatus.PASSED else "✗"
                print(f"  {symbol} {test_result.name} ({test_result.duration:.1f}s)")

        return result

    def run_all(self, suites: list[str] | None = None) -> list[SuiteResult]:
        """Run all test suites."""
        test_cases = self.load_test_cases()
        results = []

        for suite_name, suite in test_cases.get("suites", {}).items():
            if suites and suite_name not in suites:
                continue
            suite_result = self.run_suite(suite_name, suite)
            results.append(suite_result)

        return results

    def print_summary(self, results: list[SuiteResult]) -> bool:
        """Print test execution summary."""
        total_passed = sum(r.passed for r in results)
        total_failed = sum(r.failed for r in results)
        total_tests = sum(r.total for r in results)

        print("\n" + "=" * 60)
        print("E2E TEST SUMMARY")
        print("=" * 60)

        for result in results:
            status = "PASS" if result.failed == 0 else "FAIL"
            print(f"  {result.suite_name}: {result.passed}/{result.total} ({status})")

        print("-" * 60)
        print(f"  Total: {total_passed}/{total_tests} passed")

        if total_failed > 0:
            print(f"\n  FAILURES ({total_failed}):")
            for result in results:
                for test in result.tests:
                    if test.status != TestStatus.PASSED:
                        print(f"    - {result.suite_name}::{test.test_id}")

        print("=" * 60)
        return total_failed == 0

    def write_json_report(self, results: list[SuiteResult], output_path: Path):
        """Write results to JSON file."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "suites": [
                {
                    "name": r.suite_name,
                    "passed": r.passed,
                    "failed": r.failed,
                    "tests": [
                        {
                            "id": t.test_id,
                            "name": t.name,
                            "status": t.status.value,
                            "duration": t.duration,
                        }
                        for t in r.tests
                    ],
                }
                for r in results
            ],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    def write_junit_report(self, results: list[SuiteResult], output_path: Path):
        """Write results to JUnit XML format."""
        from xml.etree import ElementTree as ET

        testsuites = ET.Element("testsuites")

        for suite in results:
            testsuite = ET.SubElement(
                testsuites,
                "testsuite",
                name=suite.suite_name,
                tests=str(suite.total),
                failures=str(suite.failed),
            )

            for test in suite.tests:
                testcase = ET.SubElement(
                    testsuite,
                    "testcase",
                    name=test.name,
                    classname=suite.suite_name,
                    time=str(test.duration),
                )
                if test.status != TestStatus.PASSED:
                    failure = ET.SubElement(
                        testcase, "failure", message=test.status.value
                    )
                    failure.text = test.error or str(test.details)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        tree = ET.ElementTree(testsuites)
        tree.write(output_path, encoding="unicode", xml_declaration=True)

    def write_html_report(self, results: list[SuiteResult], output_path: Path):
        """Write results to HTML report."""
        total_passed = sum(r.passed for r in results)
        total_failed = sum(r.failed for r in results)
        total_tests = sum(r.total for r in results)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>E2E Test Report</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; margin: 40px; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .passed {{ color: #22c55e; }}
        .failed {{ color: #ef4444; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <h1>E2E Test Report</h1>
    <div class="summary">
        <p><strong>Total:</strong> {total_tests} tests</p>
        <p class="passed"><strong>Passed:</strong> {total_passed}</p>
        <p class="failed"><strong>Failed:</strong> {total_failed}</p>
        <p><strong>Model:</strong> {self.model}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
"""
        for suite in results:
            html += f"<h2>{suite.suite_name}</h2><table><tr><th>Test</th><th>Status</th><th>Duration</th></tr>"
            for test in suite.tests:
                status_class = (
                    "passed" if test.status == TestStatus.PASSED else "failed"
                )
                html += f'<tr><td>{test.name}</td><td class="{status_class}">{test.status.value}</td><td>{test.duration:.1f}s</td></tr>'
            html += "</table>"

        html += "</body></html>"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)
