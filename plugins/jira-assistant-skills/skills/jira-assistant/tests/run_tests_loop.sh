#!/usr/bin/env bash
#
# Run routing tests in a loop N times
#
# Usage:
#   ./run_tests_loop.sh N [pytest-args...]
#
# Examples:
#   ./run_tests_loop.sh 10                    # Run all tests 10 times
#   ./run_tests_loop.sh 5 --otel              # Run 5 times with OTel
#   ./run_tests_loop.sh 3 -k "TC001"          # Run TC001 3 times
#   ./run_tests_loop.sh 10 --otel -k "direct" # Run direct tests 10 times with OTel

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for N argument
if [[ -z "$1" ]] || ! [[ "$1" =~ ^[0-9]+$ ]]; then
    echo "Usage: $0 N [pytest-args...]"
    echo ""
    echo "Arguments:"
    echo "  N              Number of times to run the test suite"
    echo "  pytest-args    Additional arguments passed to pytest"
    echo ""
    echo "Examples:"
    echo "  $0 10                      Run all tests 10 times"
    echo "  $0 5 --otel                Run 5 times with OpenTelemetry"
    echo "  $0 3 -k 'TC001'            Run TC001 3 times"
    echo "  $0 10 --otel -k 'direct'   Run direct tests 10 times with OTel"
    exit 1
fi

N=$1
shift  # Remove N from arguments, rest goes to pytest

echo "=============================================="
echo "Running routing tests $N times"
echo "Additional pytest args: $*"
echo "=============================================="
echo ""

PASSED=0
FAILED=0
TOTAL_DURATION=0

for i in $(seq 1 "$N"); do
    echo "----------------------------------------------"
    echo "Run $i of $N"
    echo "----------------------------------------------"

    START_TIME=$(date +%s)

    if pytest "$SCRIPT_DIR/test_routing.py" -v "$@"; then
        ((PASSED++)) || true
        RESULT="PASSED"
    else
        ((FAILED++)) || true
        RESULT="FAILED"
    fi

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    TOTAL_DURATION=$((TOTAL_DURATION + DURATION))

    echo ""
    echo "Run $i: $RESULT (${DURATION}s)"
    echo ""

    # Brief pause between runs to avoid rate limiting
    if [[ $i -lt $N ]]; then
        sleep 2
    fi
done

echo ""
echo "=============================================="
echo "SUMMARY"
echo "=============================================="
echo "Total runs:     $N"
echo "Passed runs:    $PASSED"
echo "Failed runs:    $FAILED"
echo "Success rate:   $(( PASSED * 100 / N ))%"
echo "Total duration: ${TOTAL_DURATION}s"
echo "Avg duration:   $(( TOTAL_DURATION / N ))s per run"
echo "=============================================="

# Exit with error if any runs failed
if [[ $FAILED -gt 0 ]]; then
    exit 1
fi
