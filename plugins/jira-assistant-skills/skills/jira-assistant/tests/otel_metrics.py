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
import time
from contextlib import contextmanager
from pathlib import Path

# OpenTelemetry imports
try:
    import opentelemetry.version
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter,
    )
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.semconv.resource import ResourceAttributes
    from opentelemetry.trace import Status, StatusCode

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

# Suite span state (for parent-child hierarchy)
_suite_span = None
_suite_context = None
_suite_token = None
_suite_start_time = None

# Worker span state (child of suite, parent of tests)
_worker_span = None
_worker_context = None
_worker_token = None
_worker_start_time = None
_worker_id = None

# Metric instruments
_test_counter = None
_duration_histogram = None
_cost_histogram = None
_accuracy_gauge = None
_tool_use_accuracy_gauge = None
_accuracy_value = {"value": 0.0}
_tool_use_accuracy_value = {"value": 0.0}


def _get_git_info() -> dict:
    """Get git commit SHA and branch."""
    info = {"commit": "unknown", "branch": "unknown"}
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=PLUGIN_DIR,
        )
        if result.returncode == 0:
            info["commit"] = result.stdout.strip()[:12]

        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=PLUGIN_DIR,
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
            ["claude", "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            # Parse version from output like "claude 1.0.0"
            match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
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
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv(
            "DEPLOYMENT_ENV", "development"
        ),
        # Host
        ResourceAttributes.HOST_NAME: socket.gethostname(),
        ResourceAttributes.OS_TYPE: platform.system(),
        ResourceAttributes.OS_VERSION: platform.release(),
        # Runtime
        "python.version": platform.python_version(),
        "python.implementation": platform.python_implementation(),
        # OpenTelemetry SDK
        "otel.sdk.version": opentelemetry.version.__version__
        if OTEL_AVAILABLE
        else "N/A",
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
        print(
            "OpenTelemetry not available. Install with: pip install -r requirements-otel.txt"
        )
        return False

    if _metrics_initialized:
        return True

    try:
        # Build resource with comprehensive attributes
        resource_attrs = get_resource_attributes()
        resource = Resource.create(resource_attrs)

        # Log resource attributes for debugging
        print("OpenTelemetry Resource Attributes:")
        for key in [
            "service.version",
            "vcs.commit.sha",
            "vcs.branch",
            "skill.version",
            "golden_set.version",
        ]:
            print(f"  {key}: {resource_attrs.get(key, 'N/A')}")

        # Setup metrics
        metric_exporter = OTLPMetricExporter(
            endpoint=f"{OTLP_HTTP_ENDPOINT}/v1/metrics"
        )
        metric_reader = PeriodicExportingMetricReader(
            metric_exporter,
            export_interval_millis=5000,  # Export every 5 seconds
        )
        meter_provider = MeterProvider(
            resource=resource, metric_readers=[metric_reader]
        )
        metrics.set_meter_provider(meter_provider)
        _meter = metrics.get_meter("routing_tests", _get_plugin_version())

        # Setup tracing
        trace_exporter = OTLPSpanExporter(endpoint=f"{OTLP_HTTP_ENDPOINT}/v1/traces")
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        trace.set_tracer_provider(tracer_provider)
        _tracer = trace.get_tracer("routing_tests", _get_plugin_version())

        # Create metric instruments with descriptive units
        _test_counter = _meter.create_counter(
            name="routing_test_total",
            description="Total number of routing tests executed",
            unit="{test}",
        )

        _duration_histogram = _meter.create_histogram(
            name="routing_test_duration_seconds",
            description="Duration of routing tests",
            unit="s",
        )

        _cost_histogram = _meter.create_histogram(
            name="routing_test_cost_usd",
            description="API cost per routing test",
            unit="USD",
        )

        _accuracy_gauge = _meter.create_observable_gauge(
            name="routing_accuracy_percent",
            description="Current routing accuracy percentage",
            unit="%",
            callbacks=[
                lambda options: [metrics.Observation(_accuracy_value["value"], {})]
            ],
        )

        _tool_use_accuracy_gauge = _meter.create_observable_gauge(
            name="tool_use_accuracy_percent",
            description="Current tool use accuracy percentage (expected commands matched)",
            unit="%",
            callbacks=[
                lambda options: [
                    metrics.Observation(_tool_use_accuracy_value["value"], {})
                ]
            ],
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


def _extract_code_blocks(text: str) -> list[str]:
    """
    Extract code blocks from markdown text.

    Returns a list of code block contents (including the ``` markers).
    """
    # Match fenced code blocks: ```language\n...\n```
    pattern = r"```[\w]*\n.*?```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches


def update_tool_use_accuracy(matched: int, total: int):
    """
    Update the tool use accuracy gauge.

    Args:
        matched: Number of matched patterns
        total: Total number of patterns
    """
    if total > 0:
        _tool_use_accuracy_value["value"] = (matched / total) * 100


def record_test_result(
    test_id: str,
    category: str,
    input_text: str,
    expected_skill: str | None,
    actual_skill: str | None,
    passed: bool,
    duration_ms: int,
    cost_usd: float,
    asked_clarification: bool = False,
    session_id: str = "",
    model: str = "unknown",
    tokens_input: int = 0,
    tokens_output: int = 0,
    retry_count: int = 0,
    disambiguation_options: list | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    # New parameters for tool use accuracy
    response_text: str = "",
    tool_use_accuracy: float | None = None,
    tool_use_matched: int | None = None,
    tool_use_total: int | None = None,
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
        response_text: Full response text from Claude
        tool_use_accuracy: Accuracy of expected command matching (0.0-1.0)
        tool_use_matched: Number of expected command patterns matched
        tool_use_total: Total number of expected command patterns
    """
    if not _metrics_initialized:
        return

    # Normalize values
    expected = expected_skill or "none"
    actual = actual_skill or "none"
    result = "passed" if passed else "failed"
    routing_correct = (
        "true"
        if (
            expected == actual or (asked_clarification and category == "disambiguation")
        )
        else "false"
    )

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
    _duration_histogram.record(
        duration_ms / 1000.0, {"category": category, "result": result, "model": model}
    )

    # Record cost
    if cost_usd > 0:
        _cost_histogram.record(cost_usd, {"category": category, "model": model})

    # Create detailed trace span with correct duration
    # Backdate the span start time so spanmetrics captures the actual test duration
    # If suite context exists, create span as child of suite span
    if _tracer:
        end_time_ns = time.time_ns()
        start_time_ns = end_time_ns - (duration_ms * 1_000_000)  # Convert ms to ns

        # Use worker context as parent (falls back to suite context)
        parent_context = get_worker_context()

        with _tracer.start_as_current_span(
            f"routing_test_{test_id}",
            context=parent_context,
            start_time=start_time_ns,
        ) as span:
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
                span.set_attribute(
                    "test.disambiguation_options", ",".join(disambiguation_options)
                )

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

            # Version control context (from resource attributes, added as span attributes for filtering)
            resource_attrs = get_resource_attributes()
            span.set_attribute(
                "skill.version", resource_attrs.get("skill.version", "unknown")
            )
            span.set_attribute(
                "vcs.branch", resource_attrs.get("vcs.branch", "unknown")
            )
            span.set_attribute(
                "vcs.commit.sha", resource_attrs.get("vcs.commit.sha", "unknown")
            )

            # Tool use accuracy context
            if tool_use_accuracy is not None:
                span.set_attribute("tool_use.accuracy", tool_use_accuracy)
                span.set_attribute("tool_use.accuracy_percent", tool_use_accuracy * 100)
            if tool_use_matched is not None:
                span.set_attribute("tool_use.matched_patterns", tool_use_matched)
            if tool_use_total is not None:
                span.set_attribute("tool_use.total_patterns", tool_use_total)
            if tool_use_total and tool_use_total > 0:
                span.set_attribute(
                    "tool_use.passed",
                    tool_use_accuracy >= 0.5 if tool_use_accuracy else False,
                )

            # Add span events for prompt and response (for detailed tracing)
            span.add_event(
                "prompt",
                attributes={
                    "prompt.text": input_text[:2000],  # Truncate for size
                    "prompt.length": len(input_text),
                    "prompt.word_count": len(input_text.split()),
                },
            )

            if response_text:
                # Extract code blocks from response for analysis
                code_blocks = _extract_code_blocks(response_text)
                span.add_event(
                    "response",
                    attributes={
                        "response.text": response_text[
                            :4000
                        ],  # Larger limit for response
                        "response.length": len(response_text),
                        "response.word_count": len(response_text.split()),
                        "response.code_block_count": len(code_blocks),
                        "response.has_bash_command": any(
                            "```bash" in b or "```sh" in b for b in code_blocks
                        ),
                    },
                )

                # Add separate event for each code block (up to 5)
                for i, block in enumerate(code_blocks[:5]):
                    span.add_event(
                        f"code_block_{i}",
                        attributes={
                            "code_block.index": i,
                            "code_block.content": block[:1000],
                            "code_block.length": len(block),
                        },
                    )

            # Set span status
            if passed:
                span.set_status(Status(StatusCode.OK))
            else:
                span.set_status(
                    Status(StatusCode.ERROR, f"Expected {expected}, got {actual}")
                )


def update_accuracy(passed: int, total: int):
    """
    Update the accuracy gauge.

    Args:
        passed: Number of passed tests
        total: Total number of tests run
    """
    if total > 0:
        _accuracy_value["value"] = (passed / total) * 100


def start_suite_span(
    suite_name: str = "routing_test_suite",
    model: str = "unknown",
    parallel_workers: int = 1,
) -> str | None:
    """
    Start a suite-level span that will be parent to all test spans.

    This should be called at pytest_sessionstart. Individual test spans
    will be created as children of this span.

    Args:
        suite_name: Name for the suite span
        model: Claude model being used
        parallel_workers: Number of parallel workers (for xdist)

    Returns:
        Serialized trace context (traceparent format) for xdist propagation,
        or None if telemetry not initialized.
    """
    global _suite_span, _suite_context, _suite_token, _suite_start_time

    if not _metrics_initialized or not _tracer:
        return None

    try:
        from opentelemetry import context
        from opentelemetry.trace.propagation.tracecontext import (
            TraceContextTextMapPropagator,
        )

        _suite_start_time = time.time_ns()

        # Create the suite span (don't use context manager - we'll end it manually)
        _suite_span = _tracer.start_span(
            suite_name,
            start_time=_suite_start_time,
        )

        # Set initial attributes
        resource_attrs = get_resource_attributes()
        _suite_span.set_attribute("suite.name", suite_name)
        _suite_span.set_attribute("suite.model", model)
        _suite_span.set_attribute("suite.parallel_workers", parallel_workers)
        _suite_span.set_attribute(
            "suite.skill_version", resource_attrs.get("skill.version", "unknown")
        )
        _suite_span.set_attribute(
            "suite.vcs_branch", resource_attrs.get("vcs.branch", "unknown")
        )
        _suite_span.set_attribute(
            "suite.vcs_commit", resource_attrs.get("vcs.commit.sha", "unknown")
        )

        # Set suite span as current context
        _suite_context = trace.set_span_in_context(_suite_span)
        _suite_token = context.attach(_suite_context)

        # Serialize context for xdist workers
        carrier = {}
        TraceContextTextMapPropagator().inject(carrier, _suite_context)
        traceparent = carrier.get("traceparent", "")

        print(f"Started suite span: {suite_name} (traceparent: {traceparent[:50]}...)")
        return traceparent

    except Exception as e:
        print(f"Failed to start suite span: {e}")
        return None


def get_suite_context():
    """
    Get the current suite context for creating child spans.

    Returns:
        The suite context, or None if no suite span is active.
    """
    return _suite_context


def set_suite_context_from_traceparent(traceparent: str) -> bool:
    """
    Set the suite context from a serialized traceparent string.

    This is used by pytest-xdist workers to inherit the parent suite span
    from the main process.

    Args:
        traceparent: Serialized trace context in W3C traceparent format

    Returns:
        True if context was set successfully, False otherwise.
    """
    global _suite_context, _suite_token

    if not _metrics_initialized:
        return False

    try:
        from opentelemetry import context
        from opentelemetry.trace.propagation.tracecontext import (
            TraceContextTextMapPropagator,
        )

        carrier = {"traceparent": traceparent}
        _suite_context = TraceContextTextMapPropagator().extract(carrier)
        _suite_token = context.attach(_suite_context)

        print(f"Inherited suite context from traceparent: {traceparent[:50]}...")
        return True

    except Exception as e:
        print(f"Failed to set suite context: {e}")
        return False


def end_suite_span(
    passed: int,
    failed: int,
    skipped: int,
    total_cost_usd: float = 0.0,
):
    """
    End the suite span with final summary attributes.

    This should be called at pytest_sessionfinish.

    Args:
        passed: Number of passed tests
        failed: Number of failed tests
        skipped: Number of skipped tests
        total_cost_usd: Total API cost
    """
    global _suite_span, _suite_context, _suite_token, _suite_start_time

    if not _suite_span:
        return

    try:
        from opentelemetry import context

        # Calculate duration
        end_time_ns = time.time_ns()
        duration_ms = (
            (end_time_ns - _suite_start_time) / 1_000_000 if _suite_start_time else 0
        )

        total = passed + failed
        accuracy = (passed / total * 100) if total > 0 else 0

        # Set final attributes
        _suite_span.set_attribute("suite.passed", passed)
        _suite_span.set_attribute("suite.failed", failed)
        _suite_span.set_attribute("suite.skipped", skipped)
        _suite_span.set_attribute("suite.total", passed + failed + skipped)
        _suite_span.set_attribute("suite.executed", total)
        _suite_span.set_attribute("suite.accuracy_percent", accuracy)
        _suite_span.set_attribute("suite.duration_ms", duration_ms)
        _suite_span.set_attribute("suite.duration_seconds", duration_ms / 1000.0)
        _suite_span.set_attribute("suite.cost_usd", total_cost_usd)

        # Set status based on failures
        if failed > 0:
            _suite_span.set_status(Status(StatusCode.ERROR, f"{failed} tests failed"))
        else:
            _suite_span.set_status(Status(StatusCode.OK))

        # End the span
        _suite_span.end(end_time=end_time_ns)

        # Detach context
        if _suite_token:
            context.detach(_suite_token)

        print(
            f"Ended suite span: {passed} passed, {failed} failed, accuracy {accuracy:.1f}%"
        )

        # Update accuracy gauge
        update_accuracy(passed, total)

    except Exception as e:
        print(f"Failed to end suite span: {e}")

    finally:
        _suite_span = None
        _suite_context = None
        _suite_token = None
        _suite_start_time = None


def start_worker_span(
    worker_id: str = "main",
) -> bool:
    """
    Start a worker-level span that will be parent to test spans.

    This should be called when a pytest worker starts (or at session start
    for sequential runs). Worker spans are children of the suite span.

    Args:
        worker_id: Worker identifier (e.g., "main", "gw0", "gw1")

    Returns:
        True if worker span was started successfully, False otherwise.
    """
    global _worker_span, _worker_context, _worker_token, _worker_start_time, _worker_id

    if not _metrics_initialized or not _tracer:
        return False

    # Need suite context as parent
    if not _suite_context:
        print(f"Warning: No suite context for worker {worker_id}")
        return False

    try:
        from opentelemetry import context

        _worker_id = worker_id
        _worker_start_time = time.time_ns()

        # Create worker span as child of suite span
        _worker_span = _tracer.start_span(
            f"worker_{worker_id}",
            context=_suite_context,
            start_time=_worker_start_time,
        )

        # Set worker attributes
        _worker_span.set_attribute("worker.id", worker_id)
        _worker_span.set_attribute(
            "worker.type", "xdist" if worker_id.startswith("gw") else "main"
        )

        # Set worker span as current context
        _worker_context = trace.set_span_in_context(_worker_span)
        _worker_token = context.attach(_worker_context)

        print(f"Started worker span: worker_{worker_id}")
        return True

    except Exception as e:
        print(f"Failed to start worker span: {e}")
        return False


def get_worker_context():
    """
    Get the current worker context for creating child spans.

    Returns:
        The worker context if available, otherwise suite context, or None.
    """
    return _worker_context or _suite_context


def end_worker_span(
    passed: int = 0,
    failed: int = 0,
    skipped: int = 0,
):
    """
    End the worker span with summary attributes.

    This should be called when a pytest worker finishes.

    Args:
        passed: Number of passed tests in this worker
        failed: Number of failed tests in this worker
        skipped: Number of skipped tests in this worker
    """
    global _worker_span, _worker_context, _worker_token, _worker_start_time, _worker_id

    if not _worker_span:
        return

    try:
        from opentelemetry import context

        # Calculate duration
        end_time_ns = time.time_ns()
        duration_ms = (
            (end_time_ns - _worker_start_time) / 1_000_000 if _worker_start_time else 0
        )

        passed + failed

        # Set final attributes
        _worker_span.set_attribute("worker.passed", passed)
        _worker_span.set_attribute("worker.failed", failed)
        _worker_span.set_attribute("worker.skipped", skipped)
        _worker_span.set_attribute("worker.total", passed + failed + skipped)
        _worker_span.set_attribute("worker.duration_ms", duration_ms)

        # Set status based on failures
        if failed > 0:
            _worker_span.set_status(
                Status(
                    StatusCode.ERROR, f"{failed} tests failed in worker {_worker_id}"
                )
            )
        else:
            _worker_span.set_status(Status(StatusCode.OK))

        # End the span
        _worker_span.end(end_time=end_time_ns)

        # Detach context
        if _worker_token:
            context.detach(_worker_token)

        print(
            f"Ended worker span: worker_{_worker_id} ({passed} passed, {failed} failed)"
        )

    except Exception as e:
        print(f"Failed to end worker span: {e}")

    finally:
        _worker_span = None
        _worker_context = None
        _worker_token = None
        _worker_start_time = None
        _worker_id = None


def record_test_session_summary(
    passed: int,
    failed: int,
    skipped: int,
    total_duration_ms: int,
    total_cost_usd: float,
    categories: dict | None = None,
    skills_tested: list | None = None,
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
            span.set_attribute(
                "session.avg_test_duration_ms",
                total_duration_ms / total if total > 0 else 0,
            )

            # Cost
            span.set_attribute("session.cost_usd", total_cost_usd)
            span.set_attribute(
                "session.avg_cost_per_test_usd",
                total_cost_usd / total if total > 0 else 0,
            )

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
            span.set_attribute(
                "session.plugin_version", attrs.get("service.version", "unknown")
            )
            span.set_attribute(
                "session.skill_version", attrs.get("skill.version", "unknown")
            )
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
        if hasattr(meter_provider, "force_flush"):
            meter_provider.force_flush()
        if hasattr(meter_provider, "shutdown"):
            meter_provider.shutdown()

        tracer_provider = trace.get_tracer_provider()
        if hasattr(tracer_provider, "force_flush"):
            tracer_provider.force_flush()
        if hasattr(tracer_provider, "shutdown"):
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
    import urllib.error
    import urllib.request

    try:
        req = urllib.request.Request(
            f"{OTLP_HTTP_ENDPOINT}/v1/metrics",
            method="POST",
            headers={"Content-Type": "application/x-protobuf"},
        )
        urllib.request.urlopen(req, timeout=5, data=b"")
    except urllib.error.HTTPError as e:
        # 400/415 means endpoint is reachable but rejected empty payload
        return e.code in (400, 415)
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
