#!/usr/bin/env bash
# Run all unit tests for each skill separately to avoid namespace conflicts
#
# Usage:
#   ./scripts/run_tests.sh              # Run all unit tests
#   ./scripts/run_tests.sh --verbose    # Run with verbose output
#   ./scripts/run_tests.sh --parallel   # Run skills in parallel
#   ./scripts/run_tests.sh --fail-fast  # Stop on first failure
#   ./scripts/run_tests.sh --skill jira-bulk  # Run specific skill only

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
SKILLS_ROOT="$PROJECT_ROOT/plugins/jira-assistant-skills/skills"

# All skills to test
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

# Parse arguments
VERBOSE=""
PARALLEL=false
FAIL_FAST=false
SPECIFIC_SKILL=""
COVERAGE=false
COVERAGE_REPORT=""
MIN_COVERAGE=0
PYTEST_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -f|--fail-fast)
            FAIL_FAST=true
            shift
            ;;
        -s|--skill)
            SPECIFIC_SKILL="$2"
            shift 2
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        --coverage-report)
            COVERAGE_REPORT="$2"
            shift 2
            ;;
        --min-coverage)
            MIN_COVERAGE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose           Show verbose test output"
            echo "  -p, --parallel          Run skill tests in parallel"
            echo "  -f, --fail-fast         Stop on first skill failure"
            echo "  -s, --skill NAME        Run tests for specific skill only"
            echo "  -c, --coverage          Enable coverage collection"
            echo "  --coverage-report TYPE  Coverage report type (term, html, xml, json)"
            echo "  --min-coverage PCT      Minimum coverage percentage (fail if below)"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Coverage Examples:"
            echo "  $0 --coverage                    # Basic coverage report"
            echo "  $0 --coverage --coverage-report html  # HTML report in htmlcov/"
            echo "  $0 --coverage --coverage-report xml   # XML report for CI"
            echo "  $0 --coverage --min-coverage 95  # Fail if coverage < 95%"
            echo ""
            echo "Available skills:"
            for skill in "${ALL_SKILLS[@]}"; do
                echo "  - $skill"
            done
            exit 0
            ;;
        *)
            # Pass unknown args to pytest
            PYTEST_ARGS="$PYTEST_ARGS $1"
            shift
            ;;
    esac
done

# Determine which skills to test
if [[ -n "$SPECIFIC_SKILL" ]]; then
    SKILLS=("$SPECIFIC_SKILL")
else
    SKILLS=("${ALL_SKILLS[@]}")
fi

# Results tracking
declare -A SKILL_RESULTS
declare -A SKILL_PASSED
declare -A SKILL_FAILED
TOTAL_PASSED=0
TOTAL_FAILED=0
FAILED_SKILLS=()

# Function to run tests for a single skill
run_skill_tests() {
    local skill=$1
    local test_path="$SKILLS_ROOT/$skill/tests"
    local scripts_path="$SKILLS_ROOT/$skill/scripts"
    local result_file=$(mktemp)

    if [[ ! -d "$test_path" ]]; then
        echo "SKIP:0:0:No tests directory" > "$result_file"
        echo "$result_file"
        return
    fi

    # Count unit tests (excluding live_integration)
    local unit_test_count
    unit_test_count=$(find "$test_path" -name "test_*.py" -not -path "*live_integration*" 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$unit_test_count" -eq 0 ]]; then
        echo "SKIP:0:0:No unit tests (live_integration only)" > "$result_file"
        echo "$result_file"
        return
    fi

    # Run pytest from the skill's test directory to avoid conftest conflicts
    cd "$test_path"

    local pytest_output
    local exit_code=0

    # Build coverage arguments
    local coverage_args=""
    if $COVERAGE; then
        # Cover the skill's scripts directory
        if [[ -d "$scripts_path" ]]; then
            coverage_args="--cov=$scripts_path --cov-append"
        fi

        # Add report format if specified
        case "$COVERAGE_REPORT" in
            html)
                coverage_args="$coverage_args --cov-report=html:$PROJECT_ROOT/htmlcov"
                ;;
            xml)
                coverage_args="$coverage_args --cov-report=xml:$PROJECT_ROOT/coverage.xml"
                ;;
            json)
                coverage_args="$coverage_args --cov-report=json:$PROJECT_ROOT/coverage.json"
                ;;
            term|"")
                coverage_args="$coverage_args --cov-report=term-missing"
                ;;
        esac

        # Add minimum coverage threshold if specified
        if [[ "$MIN_COVERAGE" -gt 0 ]]; then
            coverage_args="$coverage_args --cov-fail-under=$MIN_COVERAGE"
        fi
    fi

    # Run pytest and capture output
    # Use --ignore to exclude live_integration directory (more reliable than --ignore-glob when running from test dir)
    if pytest_output=$(python -m pytest . \
        --ignore=live_integration \
        --ignore-glob="**/live_integration/*" \
        --tb=short \
        -q \
        $VERBOSE \
        $coverage_args \
        $PYTEST_ARGS 2>&1); then
        exit_code=0
    else
        exit_code=$?
    fi

    # Parse pytest output for pass/fail counts
    local passed=0
    local failed=0

    # Try to extract counts from pytest output (e.g., "103 passed" or "7 failed, 110 passed")
    if [[ "$pytest_output" =~ ([0-9]+)\ passed ]]; then
        passed="${BASH_REMATCH[1]}"
    fi
    if [[ "$pytest_output" =~ ([0-9]+)\ failed ]]; then
        failed="${BASH_REMATCH[1]}"
    fi

    if [[ $exit_code -eq 0 ]]; then
        echo "PASS:$passed:$failed:$pytest_output" > "$result_file"
    else
        echo "FAIL:$passed:$failed:$pytest_output" > "$result_file"
    fi

    cd "$PROJECT_ROOT"
    echo "$result_file"
}

# Clear coverage data if collecting coverage
if $COVERAGE; then
    rm -f "$PROJECT_ROOT/.coverage" "$PROJECT_ROOT/.coverage.*"
    echo -e "${YELLOW}Coverage collection enabled${NC}"
    if [[ -n "$COVERAGE_REPORT" ]]; then
        echo -e "${YELLOW}Report format: $COVERAGE_REPORT${NC}"
    fi
    if [[ "$MIN_COVERAGE" -gt 0 ]]; then
        echo -e "${YELLOW}Minimum coverage: ${MIN_COVERAGE}%${NC}"
    fi
    echo ""
fi

# Print header
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Unit Tests - JIRA Assistant Skills${NC}"
if $COVERAGE; then
    echo -e "${BLUE}  (with coverage)${NC}"
fi
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo ""

# Run tests for each skill
for skill in "${SKILLS[@]}"; do
    echo -e "${YELLOW}Testing:${NC} $skill"

    result_file=$(run_skill_tests "$skill")
    result=$(cat "$result_file")
    rm -f "$result_file"

    # Parse result
    IFS=':' read -r status passed failed output <<< "$result"

    case $status in
        PASS)
            echo -e "  ${GREEN}✓ PASSED${NC} ($passed passed)"
            SKILL_RESULTS[$skill]="PASS"
            SKILL_PASSED[$skill]=$passed
            SKILL_FAILED[$skill]=$failed
            TOTAL_PASSED=$((TOTAL_PASSED + passed))
            ;;
        FAIL)
            echo -e "  ${RED}✗ FAILED${NC} ($passed passed, $failed failed)"
            SKILL_RESULTS[$skill]="FAIL"
            SKILL_PASSED[$skill]=$passed
            SKILL_FAILED[$skill]=$failed
            TOTAL_PASSED=$((TOTAL_PASSED + passed))
            TOTAL_FAILED=$((TOTAL_FAILED + failed))
            FAILED_SKILLS+=("$skill")

            if [[ -n "$VERBOSE" ]]; then
                echo "$output" | tail -20
            fi

            if $FAIL_FAST; then
                echo ""
                echo -e "${RED}Stopping due to --fail-fast${NC}"
                break
            fi
            ;;
        SKIP)
            echo -e "  ${YELLOW}⊘ SKIPPED${NC} ($output)"
            SKILL_RESULTS[$skill]="SKIP"
            ;;
    esac
done

# Print summary
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo ""

# Results table
printf "%-20s %10s %10s %10s\n" "Skill" "Passed" "Failed" "Status"
printf "%-20s %10s %10s %10s\n" "────────────────────" "──────────" "──────────" "──────────"

for skill in "${SKILLS[@]}"; do
    status="${SKILL_RESULTS[$skill]:-SKIP}"
    passed="${SKILL_PASSED[$skill]:-0}"
    failed="${SKILL_FAILED[$skill]:-0}"

    case $status in
        PASS)
            printf "%-20s %10s %10s ${GREEN}%10s${NC}\n" "$skill" "$passed" "$failed" "PASS"
            ;;
        FAIL)
            printf "%-20s %10s %10s ${RED}%10s${NC}\n" "$skill" "$passed" "$failed" "FAIL"
            ;;
        SKIP)
            printf "%-20s %10s %10s ${YELLOW}%10s${NC}\n" "$skill" "-" "-" "SKIP"
            ;;
    esac
done

printf "%-20s %10s %10s %10s\n" "────────────────────" "──────────" "──────────" "──────────"
printf "%-20s %10s %10s\n" "TOTAL" "$TOTAL_PASSED" "$TOTAL_FAILED"

echo ""

# Generate combined coverage report if coverage was collected
if $COVERAGE; then
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Coverage Report${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
    echo ""

    # Combine coverage data from all skills
    cd "$PROJECT_ROOT"

    # Generate final report
    case "$COVERAGE_REPORT" in
        html)
            echo -e "${GREEN}HTML coverage report generated: htmlcov/index.html${NC}"
            ;;
        xml)
            echo -e "${GREEN}XML coverage report generated: coverage.xml${NC}"
            ;;
        json)
            echo -e "${GREEN}JSON coverage report generated: coverage.json${NC}"
            ;;
        *)
            # Show terminal summary
            if command -v coverage &> /dev/null; then
                coverage report --show-missing 2>/dev/null || true
            fi
            ;;
    esac

    echo ""
fi

# Exit status
FINAL_EXIT_CODE=0

if [[ ${#FAILED_SKILLS[@]} -gt 0 ]]; then
    echo -e "${RED}Failed skills:${NC}"
    for skill in "${FAILED_SKILLS[@]}"; do
        echo "  - $skill"
    done
    echo ""
    echo -e "${RED}Unit tests failed. Fix failures before merging to main.${NC}"
    FINAL_EXIT_CODE=1
else
    echo -e "${GREEN}All unit tests passed!${NC}"
fi

# Check minimum coverage if specified
if $COVERAGE && [[ "$MIN_COVERAGE" -gt 0 ]]; then
    if command -v coverage &> /dev/null; then
        ACTUAL_COVERAGE=$(coverage report 2>/dev/null | grep "^TOTAL" | awk '{print int($NF)}' || echo "0")
        if [[ "$ACTUAL_COVERAGE" -lt "$MIN_COVERAGE" ]]; then
            echo ""
            echo -e "${RED}Coverage ${ACTUAL_COVERAGE}% is below minimum ${MIN_COVERAGE}%${NC}"
            FINAL_EXIT_CODE=1
        else
            echo -e "${GREEN}Coverage ${ACTUAL_COVERAGE}% meets minimum ${MIN_COVERAGE}%${NC}"
        fi
    fi
fi

exit $FINAL_EXIT_CODE
