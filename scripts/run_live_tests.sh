#!/bin/bash
# Run live integration tests for each skill separately to avoid namespace conflicts
# Requires JIRA credentials: JIRA_API_TOKEN, JIRA_EMAIL, JIRA_SITE_URL

set -e  # Exit on first failure

# Parse arguments
PROFILE="development"
SKIP_PREMIUM=""
EXTRA_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --skip-premium)
            SKIP_PREMIUM="--skip-premium"
            shift
            ;;
        *)
            EXTRA_ARGS="$EXTRA_ARGS $1"
            shift
            ;;
    esac
done

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
echo "Running Live Integration Tests"
echo "Profile: $PROFILE"
echo "=========================================="
echo ""

# Check for credentials
if [ -z "$JIRA_API_TOKEN" ] || [ -z "$JIRA_EMAIL" ] || [ -z "$JIRA_SITE_URL" ]; then
    echo "ERROR: Missing JIRA credentials"
    echo "Required environment variables:"
    echo "  JIRA_API_TOKEN - API token from id.atlassian.com"
    echo "  JIRA_EMAIL     - Your Atlassian email"
    echo "  JIRA_SITE_URL  - Your JIRA URL (e.g., https://company.atlassian.net)"
    exit 1
fi

echo "JIRA Site: $JIRA_SITE_URL"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_ROOT="$PROJECT_ROOT/skills"

for skill in "${SKILLS[@]}"; do
    echo "----------------------------------------"
    echo "Testing: $skill"
    echo "----------------------------------------"

    TEST_PATH="$SKILLS_ROOT/$skill/tests/live_integration/"

    if [ -d "$TEST_PATH" ]; then
        # Build command with appropriate flags
        CMD="python -m pytest $TEST_PATH --profile $PROFILE -v"

        # Add skip-premium for JSM
        if [ "$skill" == "jira-jsm" ] && [ -n "$SKIP_PREMIUM" ]; then
            CMD="$CMD $SKIP_PREMIUM"
        fi

        # Add any extra args
        if [ -n "$EXTRA_ARGS" ]; then
            CMD="$CMD $EXTRA_ARGS"
        fi

        echo "Running: $CMD"
        if eval $CMD; then
            echo "✓ $skill: PASSED"
        else
            echo "✗ $skill: FAILED"
            FAILED_SKILLS+=("$skill")
            ((TOTAL_FAILED++))
        fi
    else
        echo "⊘ $skill: No live_integration directory"
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
echo "All live integration tests passed!"
exit 0
