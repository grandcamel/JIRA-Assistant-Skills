"""
OpenTelemetry instrumentation for routing tests.

Exports metrics and traces to OTLP endpoints for observability.

Resource Attributes (static, per-process):
- service.name, service.version, service.namespace
- deployment.environment
- host.name, os.type, os.version
- python.version, otel.sdk.version
- vcs.commit.sha, vcs.branch
- skill.version, golden_set.version

Metrics exported:
- routing_test_total: Counter with labels (category, result, expected_skill, actual_skill, model)
- routing_test_duration_seconds: Histogram of test durations
- routing_test_cost_usd: Histogram of API costs per test
- routing_accuracy_percent: Gauge of current accuracy percentage

Traces exported:
- routing_test_{id}: Span per test with comprehensive attributes
- routing_test_session: Span for full test session
"""

import hashlib
import json
import os
import platform
import re
import socket
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

# OpenTelemetry imports
try:
    from opentelemetry import metrics, trace
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.semconv.resource import ResourceAttributes
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.trace import Status, StatusCode
    import opentelemetry.version
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

# Configuration
OTLP_HTTP_ENDPOINT = os.getenv("OTLP_HTTP_ENDPOINT", "http://localhost:4318")
SERVICE_NAME = "jira-assistant-routing-tests"
SERVICE_NAMESPACE = "jira-assistant-skills"

# Paths
TESTS_DIR = Path(__file__).parent
PLUGIN_DIR = TESTS_DIR.parent.parent.parent
PLUGIN_JSON = PLUGIN_DIR / "plugin.json"
SKILL_MD = TESTS_DIR.parent / "SKILL.md"
GOLDEN_YAML = TESTS_DIR / "routing_golden.yaml"

# Global state
_meter = None
_tracer = None
_metrics_initialized = False
_resource_attributes = {}

# Metric instruments
_test_counter = None
_duration_histogram = None
_cost_histogram = None
_accuracy_gauge = None
_accuracy_value = {"value": 0.0}


def _get_git_info() -> dict:
    """Get git commit SHA and branch."""
    info = {"commit": "unknown", "branch": "unknown"}
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=PLUGIN_DIR
        )
        if result.returncode == 0:
            info["commit"] = result.stdout.strip()[:12]

        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=5,
            cwd=PLUGIN_DIR
        )
        if result.returncode == 0:
            info["branch"] = result.stdout.strip() or "detached"
    except Exception:
        pass
    return info


def _get_plugin_version() -> str:
    """Get version from plugin.json."""
    try:
        with open(PLUGIN_JSON) as f:
            data = json.load(f)
            return data.get("version", "unknown")
    except Exception:
        return "unknown"


def _get_skill_version() -> str:
    """Get version from SKILL.md frontmatter."""
    try:
        content = SKILL_MD.read_text()
        match = re.search(r'^version:\s*["\']?([^"\'\n]+)', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return "unknown"


def _get_golden_set_version() -> str:
    """Get version from routing_golden.yaml."""
    try:
        content = GOLDEN_YAML.read_text()
        match = re.search(r'^version:\s*["\']?([^"\'\n]+)', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return "unknown"


def _get_claude_version() -> str:
    """Get Claude CLI version."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            # Parse version from output like "claude 1.0.0"
            match = re.search(r'(\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
    except Exception:
        pass
    return "unknown"


def _build_resource_attributes() -> dict:
    """Build comprehensive resource attributes."""
    git_info = _get_git_info()

    attrs = {
        # Service identification
        ResourceAttributes.SERVICE_NAME: SERVICE_NAME,
        ResourceAttributes.SERVICE_VERSION: _get_plugin_version(),
        ResourceAttributes.SERVICE_NAMESPACE: SERVICE_NAMESPACE,

        # Deployment
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("DEPLOYMENT_ENV", "development"),

        # Host
        ResourceAttributes.HOST_NAME: socket.gethostname(),
        ResourceAttributes.OS_TYPE: platform.system(),
        ResourceAttributes.OS_VERSION: platform.release(),

        # Runtime
        "python.version": platform.python_version(),
        "python.implementation": platform.python_implementation(),

        # OpenTelemetry SDK
        "otel.sdk.version": opentelemetry.version.__version__ if OTEL_AVAILABLE else "N/A",

        # Version Control
        "vcs.commit.sha": git_info["commit"],
        "vcs.branch": git_info["branch"],
        "vcs.repository": "jira-assistant-skills",

        # Skill/Test versions
        "skill.version": _get_skill_version(),
        "golden_set.version": _get_golden_set_version(),
        "claude.cli.version": _get_claude_version(),

        # Test framework
        "test.framework": "pytest",
        "test.type": "routing",
    }

    return attrs


def get_resource_attributes() -> dict:
    """Get cached resource attributes."""
    global _resource_attributes
    if not _resource_attributes:
        _resource_attributes = _build_resource_attributes()
    return _resource_attributes


def init_telemetry() -> bool:
    """
    Initialize OpenTelemetry metrics and tracing with rich resource attributes.

    Returns:
        True if initialization succeeded, False otherwise.
    """
    global _meter, _tracer, _metrics_initialized
    global _test_counter, _duration_histogram, _cost_histogram, _accuracy_gauge

    if not OTEL_AVAILABLE:
        print("OpenTelemetry not available. Install with: pip install -r requirements-otel.txt")
        return False

    if _metrics_initialized:
        return True

    try:
        # Build resource with comprehensive attributes
        resource_attrs = get_resource_attributes()
        resource = Resource.create(resource_attrs)

        # Log resource attributes for debugging
        print(f"OpenTelemetry Resource Attributes:")
        for key in ["service.version", "vcs.commit.sha", "vcs.branch", "skill.version", "golden_set.version"]:
            print(f"  {key}: {resource_attrs.get(key, 'N/A')}")

        # Setup metrics
        metric_exporter = OTLPMetricExporter(
            endpoint=f"{OTLP_HTTP_ENDPOINT}/v1/metrics"
        )
        metric_reader = PeriodicExportingMetricReader(
            metric_exporter,
            export_interval_millis=5000  # Export every 5 seconds
        )
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader]
        )
        metrics.set_meter_provider(meter_provider)
        _meter = metrics.get_meter("routing_tests", _get_plugin_version())

        # Setup tracing
        trace_exporter = OTLPSpanExporter(
            endpoint=f"{OTLP_HTTP_ENDPOINT}/v1/traces"
        )
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        trace.set_tracer_provider(tracer_provider)
        _tracer = trace.get_tracer("routing_tests", _get_plugin_version())

        # Create metric instruments with descriptive units
        _test_counter = _meter.create_counter(
            name="routing_test_total",
            description="Total number of routing tests executed",
            unit="{test}"
        )

        _duration_histogram = _meter.create_histogram(
            name="routing_test_duration_seconds",
            description="Duration of routing tests",
            unit="s"
        )

        _cost_histogram = _meter.create_histogram(
            name="routing_test_cost_usd",
            description="API cost per routing test",
            unit="USD"
        )

        _accuracy_gauge = _meter.create_observable_gauge(
            name="routing_accuracy_percent",
            description="Current routing accuracy percentage",
            unit="%",
            callbacks=[lambda options: [
                metrics.Observation(_accuracy_value["value"], {})
            ]]
        )

        _metrics_initialized = True
        print(f"OpenTelemetry initialized. Exporting to {OTLP_HTTP_ENDPOINT}")
        return True

    except Exception as e:
        print(f"Failed to initialize OpenTelemetry: {e}")
        return False


def _hash_input(text: str) -> str:
    """Create a privacy-safe hash of input text."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def record_test_result(
    test_id: str,
    category: str,
    input_text: str,
    expected_skill: Optional[str],
    actual_skill: Optional[str],
    passed: bool,
    duration_ms: int,
    cost_usd: float,
    asked_clarification: bool = False,
    session_id: str = "",
    model: str = "unknown",
    tokens_input: int = 0,
    tokens_output: int = 0,
    retry_count: int = 0,
    disambiguation_options: Optional[list] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None
):
    """
    Record a single test result with comprehensive context.

    Args:
        test_id: Test case ID (e.g., TC001)
        category: Test category (direct, disambiguation, negative, etc.)
        input_text: User input that was tested
        expected_skill: Expected skill to be routed to
        actual_skill: Actual skill that was routed to
        passed: Whether the test passed
        duration_ms: Test duration in milliseconds
        cost_usd: API cost in USD
        asked_clarification: Whether Claude asked for clarification
        session_id: Claude session ID for correlation
        model: Claude model used (opus, sonnet, haiku)
        tokens_input: Input token count
        tokens_output: Output token count
        retry_count: Number of API retries
        disambiguation_options: Skills offered for disambiguation
        error_type: Type of error if failed
        error_message: Error message if failed
    """
    if not _metrics_initialized:
        return

    # Normalize values
    expected = expected_skill or "none"
    actual = actual_skill or "none"
    result = "passed" if passed else "failed"
    routing_correct = "true" if (expected == actual or (asked_clarification and category == "disambiguation")) else "false"

    # Metric labels (keep cardinality reasonable)
    metric_labels = {
        "category": category,
        "result": result,
        "expected_skill": expected,
        "actual_skill": actual,
        "routing_correct": routing_correct,
        "model": model,
        "clarification_asked": str(asked_clarification).lower(),
    }

    if error_type:
        metric_labels["error_type"] = error_type

    # Record counter
    _test_counter.add(1, metric_labels)

    # Record duration (convert ms to seconds for standard units)
    _duration_histogram.record(duration_ms / 1000.0, {
        "category": category,
        "result": result,
        "model": model
    })

    # Record cost
    if cost_usd > 0:
        _cost_histogram.record(cost_usd, {
            "category": category,
            "model": model
        })

    # Create detailed trace span
    if _tracer:
        with _tracer.start_as_current_span(f"routing_test_{test_id}") as span:
            # Test identification
            span.set_attribute("test.id", test_id)
            span.set_attribute("test.category", category)
            span.set_attribute("test.name", f"routing_test_{test_id}")

            # Input context (truncate for size, include hash for correlation)
            span.set_attribute("test.input", input_text[:500])
            span.set_attribute("test.input.length", len(input_text))
            span.set_attribute("test.input.hash", _hash_input(input_text))
            span.set_attribute("test.input.word_count", len(input_text.split()))

            # Routing context
            span.set_attribute("test.expected_skill", expected)
            span.set_attribute("test.actual_skill", actual)
            span.set_attribute("test.routing_correct", passed)
            span.set_attribute("test.asked_clarification", asked_clarification)

            if disambiguation_options:
                span.set_attribute("test.disambiguation_options", ",".join(disambiguation_options))

            # Result context
            span.set_attribute("test.passed", passed)
            span.set_attribute("test.result", result)
            span.set_attribute("test.duration_ms", duration_ms)
            span.set_attribute("test.duration_seconds", duration_ms / 1000.0)
            span.set_attribute("test.cost_usd", cost_usd)

            # Claude context
            span.set_attribute("claude.session_id", session_id)
            span.set_attribute("claude.model", model)
            span.set_attribute("claude.tokens.input", tokens_input)
            span.set_attribute("claude.tokens.output", tokens_output)
            span.set_attribute("claude.tokens.total", tokens_input + tokens_output)
            span.set_attribute("claude.retry_count", retry_count)

            # Error context
            if error_type:
                span.set_attribute("error.type", error_type)
            if error_message:
                span.set_attribute("error.message", error_message[:500])

            # Set span status
            if passed:
                span.set_status(Status(StatusCode.OK))
            else:
                span.set_status(Status(
                    StatusCode.ERROR,
                    f"Expected {expected}, got {actual}"
                ))


def update_accuracy(passed: int, total: int):
    """
    Update the accuracy gauge.

    Args:
        passed: Number of passed tests
        total: Total number of tests run
    """
    if total > 0:
        _accuracy_value["value"] = (passed / total) * 100


def record_test_session_summary(
    passed: int,
    failed: int,
    skipped: int,
    total_duration_ms: int,
    total_cost_usd: float,
    categories: Optional[dict] = None,
    skills_tested: Optional[list] = None
):
    """
    Record summary metrics for a complete test session.

    Args:
        passed: Number of passed tests
        failed: Number of failed tests
        skipped: Number of skipped tests
        total_duration_ms: Total session duration
        total_cost_usd: Total API cost
        categories: Dict of category -> count
        skills_tested: List of skills that were tested
    """
    if not _metrics_initialized:
        return

    total = passed + failed
    if total > 0:
        update_accuracy(passed, total)

    # Create summary trace
    if _tracer:
        with _tracer.start_as_current_span("routing_test_session") as span:
            # Session results
            span.set_attribute("session.passed", passed)
            span.set_attribute("session.failed", failed)
            span.set_attribute("session.skipped", skipped)
            span.set_attribute("session.total", passed + failed + skipped)
            span.set_attribute("session.executed", passed + failed)

            # Accuracy
            accuracy = (passed / total * 100) if total > 0 else 0
            span.set_attribute("session.accuracy_percent", accuracy)
            span.set_attribute("session.pass_rate", passed / total if total > 0 else 0)

            # Performance
            span.set_attribute("session.duration_ms", total_duration_ms)
            span.set_attribute("session.duration_seconds", total_duration_ms / 1000.0)
            span.set_attribute("session.avg_test_duration_ms", total_duration_ms / total if total > 0 else 0)

            # Cost
            span.set_attribute("session.cost_usd", total_cost_usd)
            span.set_attribute("session.avg_cost_per_test_usd", total_cost_usd / total if total > 0 else 0)

            # Categories breakdown
            if categories:
                for cat, count in categories.items():
                    span.set_attribute(f"session.category.{cat}", count)

            # Skills coverage
            if skills_tested:
                span.set_attribute("session.skills_tested", ",".join(skills_tested))
                span.set_attribute("session.skills_count", len(skills_tested))

            # Resource context (for correlation)
            attrs = get_resource_attributes()
            span.set_attribute("session.plugin_version", attrs.get("service.version", "unknown"))
            span.set_attribute("session.skill_version", attrs.get("skill.version", "unknown"))
            span.set_attribute("session.commit", attrs.get("vcs.commit.sha", "unknown"))


@contextmanager
def test_span(test_id: str, category: str, input_text: str):
    """
    Context manager for creating a test span.

    Usage:
        with test_span("TC001", "direct", "create a bug") as span:
            result = run_test()
            span.set_attribute("test.actual_skill", result.skill)
    """
    if not _tracer:
        yield None
        return

    with _tracer.start_as_current_span(f"routing_test_{test_id}") as span:
        span.set_attribute("test.id", test_id)
        span.set_attribute("test.category", category)
        span.set_attribute("test.input", input_text[:500])
        span.set_attribute("test.input.hash", _hash_input(input_text))
        yield span


def shutdown():
    """Flush and shutdown telemetry exporters."""
    if not _metrics_initialized:
        return

    try:
        # Get providers and force flush
        meter_provider = metrics.get_meter_provider()
        if hasattr(meter_provider, 'force_flush'):
            meter_provider.force_flush()
        if hasattr(meter_provider, 'shutdown'):
            meter_provider.shutdown()

        tracer_provider = trace.get_tracer_provider()
        if hasattr(tracer_provider, 'force_flush'):
            tracer_provider.force_flush()
        if hasattr(tracer_provider, 'shutdown'):
            tracer_provider.shutdown()

        print("OpenTelemetry shutdown complete.")
    except Exception as e:
        print(f"Error during OpenTelemetry shutdown: {e}")


def test_connectivity() -> bool:
    """
    Test connectivity to OTLP endpoint.

    Returns:
        True if connection successful, False otherwise.
    """
    import urllib.request
    import urllib.error

    try:
        req = urllib.request.Request(
            f"{OTLP_HTTP_ENDPOINT}/v1/metrics",
            method="POST",
            headers={"Content-Type": "application/x-protobuf"}
        )
        urllib.request.urlopen(req, timeout=5, data=b"")
    except urllib.error.HTTPError as e:
        # 400/415 means endpoint is reachable but rejected empty payload
        if e.code in (400, 415):
            return True
        return False
    except Exception:
        return False

    return True


if __name__ == "__main__":
    # Quick connectivity and attribute test
    print(f"Testing OTLP endpoint: {OTLP_HTTP_ENDPOINT}")
    print("\nResource Attributes:")
    for k, v in get_resource_attributes().items():
        print(f"  {k}: {v}")

    if test_connectivity():
        print("\nOTLP endpoint is reachable!")
        if init_telemetry():
            # Send a test metric
            record_test_result(
                test_id="TEST001",
                category="connectivity",
                input_text="connectivity test",
                expected_skill="test",
                actual_skill="test",
                passed=True,
                duration_ms=100,
                cost_usd=0.001,
                model="test",
            )
            print("Test metric sent. Check your observability stack.")
            shutdown()
    else:
        print(f"\nCannot reach OTLP endpoint at {OTLP_HTTP_ENDPOINT}")
        print("Ensure your OpenTelemetry collector is running.")
