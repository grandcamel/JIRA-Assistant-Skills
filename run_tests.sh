#!/bin/bash
# Run all unit tests for each skill separately to avoid namespace conflicts

set -e  # Exit on first failure

SKILLS=(
    "jira-admin"
    "jira-agile"
    "jira-bulk"
    "jira-collaborate"
    "jira-dev"
    "jira-fields"
    "jira-issue"
    "jira-jsm"
    "jira-lifecycle"
    "jira-ops"
    "jira-relationships"
    "jira-search"
    "jira-time"
    "shared"
)

TOTAL_PASSED=0
TOTAL_FAILED=0
FAILED_SKILLS=()

echo "=========================================="
echo "Running Unit Tests for All Skills"
echo "=========================================="
echo ""

for skill in "${SKILLS[@]}"; do
    echo "----------------------------------------"
    echo "Testing: $skill"
    echo "----------------------------------------"

    TEST_PATH=".claude/skills/$skill/tests/"

    if [ -d "$TEST_PATH" ]; then
        # Check if there are any unit tests (not in live_integration)
        UNIT_TEST_COUNT=$(find "$TEST_PATH" -name "test_*.py" -not -path "*live_integration*" 2>/dev/null | wc -l | tr -d ' ')

        if [ "$UNIT_TEST_COUNT" -eq 0 ]; then
            echo "⊘ $skill: No unit tests (live_integration only)"
        else
            # Run tests, ignoring live_integration
            if ./venv/bin/pytest "$TEST_PATH" --ignore-glob="**/live_integration/*" -q 2>&1; then
                echo "✓ $skill: PASSED"
            else
                echo "✗ $skill: FAILED"
                FAILED_SKILLS+=("$skill")
                ((TOTAL_FAILED++))
            fi
        fi
    else
        echo "⊘ $skill: No tests directory"
    fi
    echo ""
done

echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Skills tested: ${#SKILLS[@]}"
echo "Failed: ${#FAILED_SKILLS[@]}"

if [ ${#FAILED_SKILLS[@]} -gt 0 ]; then
    echo ""
    echo "Failed skills:"
    for skill in "${FAILED_SKILLS[@]}"; do
        echo "  - $skill"
    done
    exit 1
fi

echo ""
echo "All tests passed!"
exit 0
