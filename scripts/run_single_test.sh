#!/usr/bin/env bash
# Run a single test or test file for iterative fixing
#
# Usage:
#   ./scripts/run_single_test.sh jira-admin test_list_projects.py
#   ./scripts/run_single_test.sh jira-bulk test_bulk_assign.py::TestBulkAssignToUser
#   ./scripts/run_single_test.sh jira-dev test_branch_names.py::TestBranchNameGeneration::test_basic_branch_name
#   ./scripts/run_single_test.sh jira-search -k "test_validate"
#
# Examples:
#   # Run all tests in a file
#   ./scripts/run_single_test.sh jira-bulk test_bulk_assign.py
#
#   # Run a specific test class
#   ./scripts/run_single_test.sh jira-bulk test_bulk_assign.py::TestBulkAssignToUser
#
#   # Run a specific test method
#   ./scripts/run_single_test.sh jira-bulk test_bulk_assign.py::TestBulkAssignToUser::test_bulk_assign_to_user_by_account_id
#
#   # Run tests matching a keyword
#   ./scripts/run_single_test.sh jira-search -k "validate"
#
#   # Run with verbose output and show locals
#   ./scripts/run_single_test.sh jira-admin test_list_projects.py -v --tb=long
#
#   # Re-run only failed tests from last run
#   ./scripts/run_single_test.sh jira-admin --lf
#
#   # Run tests and stop on first failure
#   ./scripts/run_single_test.sh jira-admin test_list_projects.py -x

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_ROOT="$PROJECT_ROOT/skills"

# Available skills
ALL_SKILLS=(
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

show_help() {
    echo "Usage: $0 SKILL [TEST_SPEC] [PYTEST_OPTIONS...]"
    echo ""
    echo "Run a single test or test file for iterative fixing."
    echo ""
    echo "Arguments:"
    echo "  SKILL       The skill to test (required)"
    echo "  TEST_SPEC   Test file, class, or method (optional)"
    echo "              Can be: test_file.py"
    echo "                      test_file.py::TestClass"
    echo "                      test_file.py::TestClass::test_method"
    echo ""
    echo "Pytest Options (passed through):"
    echo "  -v, --verbose    Verbose output"
    echo "  -x               Stop on first failure"
    echo "  --lf             Re-run only failed tests from last run"
    echo "  --ff             Run failed tests first, then rest"
    echo "  -k EXPR          Run tests matching expression"
    echo "  --tb=STYLE       Traceback style (short, long, line, no)"
    echo "  --pdb            Drop into debugger on failure"
    echo ""
    echo "Available skills:"
    for skill in "${ALL_SKILLS[@]}"; do
        echo "  - $skill"
    done
    echo ""
    echo "Examples:"
    echo "  $0 jira-bulk test_bulk_assign.py"
    echo "  $0 jira-bulk test_bulk_assign.py::TestBulkAssignToUser"
    echo "  $0 jira-search -k 'validate'"
    echo "  $0 jira-admin test_list_projects.py -v --tb=long"
    echo "  $0 jira-admin --lf"
}

# Check for help flag
if [[ $# -eq 0 ]] || [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# First argument is the skill
SKILL="$1"
shift

# Validate skill
valid_skill=false
for s in "${ALL_SKILLS[@]}"; do
    if [[ "$s" == "$SKILL" ]]; then
        valid_skill=true
        break
    fi
done

if ! $valid_skill; then
    echo -e "${RED}Error: Unknown skill '$SKILL'${NC}"
    echo ""
    echo "Available skills:"
    for skill in "${ALL_SKILLS[@]}"; do
        echo "  - $skill"
    done
    exit 1
fi

# Build test path
TEST_PATH="$SKILLS_ROOT/$SKILL/tests"

if [[ ! -d "$TEST_PATH" ]]; then
    echo -e "${RED}Error: Test directory not found: $TEST_PATH${NC}"
    exit 1
fi

# Collect pytest arguments
PYTEST_ARGS=()
TEST_SPEC=""

while [[ $# -gt 0 ]]; do
    case $1 in
        test_*.py*)
            # This is a test file specification
            TEST_SPEC="$1"
            shift
            ;;
        *)
            # Pass through to pytest
            PYTEST_ARGS+=("$1")
            shift
            ;;
    esac
done

# Change to test directory to avoid conftest conflicts
cd "$TEST_PATH"

echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Running Tests: $SKILL${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Test directory:${NC} $TEST_PATH"

if [[ -n "$TEST_SPEC" ]]; then
    echo -e "${YELLOW}Test spec:${NC} $TEST_SPEC"
fi

if [[ ${#PYTEST_ARGS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Pytest args:${NC} ${PYTEST_ARGS[*]}"
fi

echo ""

# Build the pytest command
PYTEST_CMD=(python -m pytest)

if [[ -n "$TEST_SPEC" ]]; then
    # Check if test spec includes a path or just a filename
    if [[ "$TEST_SPEC" == *"/"* ]]; then
        PYTEST_CMD+=("$TEST_SPEC")
    else
        # Look for the test file in the tests directory (including subdirectories)
        TEST_FILE=$(find . -name "${TEST_SPEC%%::*}" -type f 2>/dev/null | head -1)
        if [[ -n "$TEST_FILE" ]]; then
            # If there's a class/method specifier, append it
            if [[ "$TEST_SPEC" == *"::"* ]]; then
                SPECIFIER="${TEST_SPEC#*::}"
                PYTEST_CMD+=("${TEST_FILE}::${SPECIFIER}")
            else
                PYTEST_CMD+=("$TEST_FILE")
            fi
        else
            PYTEST_CMD+=("$TEST_SPEC")
        fi
    fi
else
    # No test spec - run all tests (excluding live_integration)
    PYTEST_CMD+=(. --ignore-glob="**/live_integration/*")
fi

# Add any pytest args
PYTEST_CMD+=("${PYTEST_ARGS[@]}")

# Default to verbose and short traceback if no verbosity specified
if [[ ! " ${PYTEST_ARGS[*]} " =~ " -v " ]] && [[ ! " ${PYTEST_ARGS[*]} " =~ " --verbose " ]] && [[ ! " ${PYTEST_ARGS[*]} " =~ " -q " ]]; then
    PYTEST_CMD+=(-v)
fi

if [[ ! " ${PYTEST_ARGS[*]} " =~ " --tb=" ]]; then
    PYTEST_CMD+=(--tb=short)
fi

# Run pytest
echo -e "${YELLOW}Running:${NC} ${PYTEST_CMD[*]}"
echo ""

"${PYTEST_CMD[@]}"
exit_code=$?

echo ""
if [[ $exit_code -eq 0 ]]; then
    echo -e "${GREEN}Tests passed!${NC}"
else
    echo -e "${RED}Tests failed (exit code: $exit_code)${NC}"
fi

exit $exit_code
