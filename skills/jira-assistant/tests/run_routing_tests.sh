#!/bin/bash
# Run routing tests for jira-assistant skill
#
# Usage:
#   ./run_routing_tests.sh              # Run all tests
#   ./run_routing_tests.sh direct       # Run only direct routing tests
#   ./run_routing_tests.sh quick        # Run first 5 tests only
#   ./run_routing_tests.sh TC001        # Run specific test by ID
#   ./run_routing_tests.sh --otel       # Run with OpenTelemetry metrics
#   ./run_routing_tests.sh direct --otel # Combine category and OTel

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check dependencies
if ! command -v claude &> /dev/null; then
    echo "Error: Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

if ! python3 -c "import pytest" &> /dev/null; then
    echo "Installing pytest..."
    pip install pytest pyyaml
fi

# Parse arguments
FILTER=""
OTEL_ARGS=""
EXTRA_ARGS=""

for arg in "$@"; do
    case "$arg" in
        --otel)
            # Check if OpenTelemetry is installed
            if ! python3 -c "import opentelemetry" &> /dev/null; then
                echo "Installing OpenTelemetry dependencies..."
                pip install -r requirements-otel.txt
            fi
            OTEL_ARGS="--otel"
            ;;
        --otlp-endpoint=*)
            OTEL_ARGS="$OTEL_ARGS $arg"
            ;;
        direct)
            FILTER="-k direct"
            ;;
        disambiguation|disambig)
            FILTER="-k disambiguation"
            ;;
        negative)
            FILTER="-k negative"
            ;;
        workflow)
            FILTER="-k workflow"
            ;;
        edge)
            FILTER="-k edge"
            ;;
        quick)
            # Run first 5 direct tests only
            FILTER="-k 'TC001 or TC002 or TC003 or TC004 or TC005'"
            ;;
        TC*)
            # Run specific test by ID
            FILTER="-k $arg"
            ;;
        all)
            FILTER=""
            ;;
        -*)
            # Pass through other pytest options
            EXTRA_ARGS="$EXTRA_ARGS $arg"
            ;;
        *)
            echo "Usage: $0 [direct|disambiguation|negative|workflow|edge|quick|TC###|all] [--otel] [--otlp-endpoint=URL]"
            exit 1
            ;;
    esac
done

echo "============================================"
echo "JIRA Assistant Routing Tests"
echo "============================================"
if [ -n "$OTEL_ARGS" ]; then
    echo "OpenTelemetry: ENABLED"
    echo "OTLP Endpoint: ${OTLP_HTTP_ENDPOINT:-http://localhost:4318}"
fi
echo ""
echo "Running: pytest test_routing.py -v $FILTER $OTEL_ARGS $EXTRA_ARGS"
echo ""

# Run tests
pytest test_routing.py -v $FILTER $OTEL_ARGS $EXTRA_ARGS

echo ""
echo "============================================"
echo "Tests complete"
echo "============================================"
