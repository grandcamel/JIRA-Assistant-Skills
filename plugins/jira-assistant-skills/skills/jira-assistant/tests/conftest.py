"""Pytest configuration for routing tests."""

import os
import sys
from pathlib import Path

import pytest
import time

# Add tests directory to path for otel_metrics import
TESTS_DIR = Path(__file__).parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

# OpenTelemetry integration (optional)
try:
    from otel_metrics import (
        init_telemetry,
        record_test_result,
        record_test_session_summary,
        start_suite_span,
        end_suite_span,
        set_suite_context_from_traceparent,
        start_worker_span,
        end_worker_span,
        shutdown as otel_shutdown,
        OTEL_AVAILABLE
    )
except ImportError:
    OTEL_AVAILABLE = False
    init_telemetry = None
    record_test_result = None
    record_test_session_summary = None
    start_suite_span = None
    end_suite_span = None
    set_suite_context_from_traceparent = None
    start_worker_span = None
    end_worker_span = None
    otel_shutdown = None

# Environment variable for xdist trace context propagation
TRACEPARENT_ENV_VAR = "PYTEST_OTEL_TRACEPARENT"


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--otel",
        action="store_true",
        default=False,
        help="Enable OpenTelemetry metrics export"
    )
    parser.addoption(
        "--otlp-endpoint",
        action="store",
        default="http://localhost:4318",
        help="OTLP HTTP endpoint (default: http://localhost:4318)"
    )
    parser.addoption(
        "--model",
        action="store",
        default=None,
        help="Claude model to use (e.g., 'haiku' for fast iteration, 'sonnet' for production)"
    )


def pytest_configure(config):
    """Register custom markers and initialize telemetry."""
    config.addinivalue_line(
        "markers", "direct: Direct routing tests (high certainty)"
    )
    config.addinivalue_line(
        "markers", "disambiguation: Disambiguation tests (ask for clarification)"
    )
    config.addinivalue_line(
        "markers", "negative: Negative trigger tests (should NOT route to skill)"
    )
    config.addinivalue_line(
        "markers", "context: Context-dependent tests (require session state)"
    )
    config.addinivalue_line(
        "markers", "workflow: Multi-skill workflow tests"
    )
    config.addinivalue_line(
        "markers", "edge: Edge case tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (each test calls Claude API)"
    )

    # Initialize OpenTelemetry if requested
    if config.getoption("--otel") and OTEL_AVAILABLE:
        import os
        os.environ["OTLP_HTTP_ENDPOINT"] = config.getoption("--otlp-endpoint")
        if init_telemetry():
            config._otel_enabled = True
        else:
            config._otel_enabled = False
            print("Warning: OpenTelemetry initialization failed")
    else:
        config._otel_enabled = False
        if config.getoption("--otel") and not OTEL_AVAILABLE:
            print("Warning: OpenTelemetry not available. Install with: pip install -r requirements-otel.txt")


def pytest_sessionstart(session):
    """Start suite and worker spans at session start."""
    config = session.config

    if not getattr(config, '_otel_enabled', False):
        return

    # Check if we're an xdist worker
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")

    if worker_id:
        # We're an xdist worker - inherit suite context from main process
        traceparent = os.environ.get(TRACEPARENT_ENV_VAR)
        if traceparent and set_suite_context_from_traceparent:
            set_suite_context_from_traceparent(traceparent)
            # Start worker span for this xdist worker
            if start_worker_span:
                start_worker_span(worker_id)
    else:
        # We're the main process (or not using xdist) - start the suite span
        if start_suite_span:
            model = config.getoption("--model") or "unknown"

            # Detect xdist worker count
            try:
                num_workers = int(config.getoption("numprocesses", 0) or 0)
            except (TypeError, ValueError):
                num_workers = 0

            traceparent = start_suite_span(
                suite_name="routing_test_suite",
                model=model,
                parallel_workers=max(1, num_workers),
            )

            # Store traceparent for xdist workers
            if traceparent:
                os.environ[TRACEPARENT_ENV_VAR] = traceparent
                config._suite_traceparent = traceparent

            # For non-xdist runs, start a "main" worker span
            if num_workers == 0 and start_worker_span:
                start_worker_span("main")


def pytest_sessionfinish(session, exitstatus):
    """End worker and suite spans at session finish."""
    config = session.config

    if not getattr(config, '_otel_enabled', False):
        return

    # Get counts from terminal reporter if available
    reporter = config.pluginmanager.get_plugin("terminalreporter")
    if reporter:
        passed = len(reporter.stats.get("passed", []))
        failed = len(reporter.stats.get("failed", []))
        skipped = len(reporter.stats.get("skipped", []))
    else:
        # Fall back to cost_tracker counts
        cost_tracker = getattr(config, '_cost_tracker', None)
        if cost_tracker:
            passed = cost_tracker.get("passed", 0)
            failed = cost_tracker.get("failed", 0)
            skipped = cost_tracker.get("skipped", 0)
        else:
            passed = failed = skipped = 0

    # Check if we're an xdist worker
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")

    if worker_id:
        # End this worker's span
        if end_worker_span:
            end_worker_span(passed=passed, failed=failed, skipped=skipped)
        return  # Workers don't end the suite span

    # Main process: end worker span (for non-xdist), then suite span
    if end_worker_span:
        end_worker_span(passed=passed, failed=failed, skipped=skipped)

    if end_suite_span:
        # Get cost from cost_tracker if available
        cost_tracker = getattr(config, '_cost_tracker', None)
        total_cost = cost_tracker.get("total_cost_usd", 0.0) if cost_tracker else 0.0

        end_suite_span(
            passed=passed,
            failed=failed,
            skipped=skipped,
            total_cost_usd=total_cost,
        )


def pytest_unconfigure(config):
    """Shutdown telemetry on exit."""
    if getattr(config, '_otel_enabled', False) and otel_shutdown:
        otel_shutdown()


def pytest_collection_modifyitems(config, items):
    """Mark all routing tests as slow by default."""
    for item in items:
        if "test_routing" in item.nodeid:
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def otel_enabled(request):
    """Check if OpenTelemetry is enabled for this session."""
    return getattr(request.config, '_otel_enabled', False)


@pytest.fixture(scope="session")
def claude_model(request):
    """Get the Claude model to use for tests."""
    return request.config.getoption("--model")


# Module-level config storage for access from test_routing.py
_test_config = {}


@pytest.fixture(scope="session", autouse=True)
def _store_test_config(request):
    """Store test config for module-level access."""
    _test_config["model"] = request.config.getoption("--model")
    yield
    _test_config.clear()


def get_test_model() -> str | None:
    """Get the configured model for tests. Called from test_routing.py."""
    return _test_config.get("model")


@pytest.fixture(scope="session")
def cost_tracker(request):
    """Track cumulative cost across test session."""
    tracker = {
        "total_cost_usd": 0.0,
        "total_duration_ms": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "start_time": time.time()
    }

    # Store in config for pytest_sessionfinish access
    request.config._cost_tracker = tracker

    yield tracker

    # Print summary
    print(f"\n\nTotal API cost: ${tracker['total_cost_usd']:.4f}")
    print(f"Total API time: {tracker['total_duration_ms'] / 1000:.1f}s")

    # Record session summary to OpenTelemetry (legacy - suite span now handles this)
    if getattr(request.config, '_otel_enabled', False) and record_test_session_summary:
        elapsed_ms = int((time.time() - tracker["start_time"]) * 1000)
        record_test_session_summary(
            passed=tracker["passed"],
            failed=tracker["failed"],
            skipped=tracker["skipped"],
            total_duration_ms=elapsed_ms,
            total_cost_usd=tracker["total_cost_usd"]
        )


@pytest.fixture(scope="function")
def record_otel(request, otel_enabled, cost_tracker):
    """
    Fixture to record test results to OpenTelemetry.

    Usage in test:
        def test_something(record_otel):
            result = run_test()
            record_otel(
                test_id="TC001",
                category="direct",
                input_text="create a bug",
                expected_skill="jira-issue",
                actual_skill=result.skill_loaded,
                passed=True,
                duration_ms=result.duration_ms,
                cost_usd=result.cost_usd
            )
    """
    # Get model from pytest config for OTel recording
    configured_model = request.config.getoption("--model") or "unknown"

    def _record(
        test_id: str,
        category: str,
        input_text: str,
        expected_skill: str,
        actual_skill: str,
        passed: bool,
        duration_ms: int,
        cost_usd: float,
        asked_clarification: bool = False,
        session_id: str = "",
        tokens_input: int = 0,
        tokens_output: int = 0,
        response_text: str = "",
        tool_use_accuracy: float | None = None,
        tool_use_matched: int | None = None,
        tool_use_total: int | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
    ):
        # Update cost tracker
        cost_tracker["total_cost_usd"] += cost_usd
        cost_tracker["total_duration_ms"] += duration_ms
        if passed:
            cost_tracker["passed"] += 1
        else:
            cost_tracker["failed"] += 1

        # Auto-classify error type if not provided
        classified_error_type = error_type
        classified_error_message = error_message
        if not passed and not classified_error_type:
            if expected_skill and actual_skill and expected_skill != actual_skill:
                classified_error_type = "misroute"
                classified_error_message = f"Expected {expected_skill}, got {actual_skill}"
            elif not actual_skill or actual_skill == "none":
                classified_error_type = "no_skill_detected"
                classified_error_message = "No skill was detected in response"
            elif asked_clarification and category != "disambiguation":
                classified_error_type = "unexpected_clarification"
                classified_error_message = "Asked for clarification when direct routing expected"
            else:
                classified_error_type = "assertion_failed"
                classified_error_message = "Test assertion failed"

        # Record to OpenTelemetry if enabled
        if otel_enabled and record_test_result:
            record_test_result(
                test_id=test_id,
                category=category,
                input_text=input_text,
                expected_skill=expected_skill or "none",
                actual_skill=actual_skill or "none",
                passed=passed,
                duration_ms=duration_ms,
                cost_usd=cost_usd,
                asked_clarification=asked_clarification,
                session_id=session_id,
                model=configured_model,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                response_text=response_text,
                tool_use_accuracy=tool_use_accuracy,
                tool_use_matched=tool_use_matched,
                tool_use_total=tool_use_total,
                error_type=classified_error_type,
                error_message=classified_error_message,
            )

    return _record
