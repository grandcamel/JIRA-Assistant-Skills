#!/usr/bin/env bash
# Fast Iteration Test Runner for JIRA Assistant Routing Tests
#
# Optimizes the fix-test-pass/fail cycle using:
#   1. Parallel execution (pytest-xdist)
#   2. Targeted test filtering by skill or test ID
#   3. Fast model option (haiku) for quick iteration
#
# Usage:
#   ./fast_test.sh                           # Run all tests with defaults
#   ./fast_test.sh --skill agile             # Test only jira-agile routing
#   ./fast_test.sh --skill bulk,dev          # Test multiple skills
#   ./fast_test.sh --id TC012,TC015          # Test specific test IDs
#   ./fast_test.sh --fast                    # Use haiku model (faster)
#   ./fast_test.sh --parallel 4              # Run 4 tests in parallel
#   ./fast_test.sh --smoke                   # Run 5 key tests only (~1.5 min)
#   ./fast_test.sh --failed                  # Re-run only failed tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Defaults
PARALLEL=""
MODEL_ARGS=""
FILTER=""
EXTRA_ARGS="-v"
RERUN_FAILED=""

# Skill to test ID mapping (function-based for compatibility)
get_skill_tests() {
    local skill="$1"
    case "$skill" in
        issue)       echo "TC001 or TC002 or TC003 or TC004 or TC039 or TC047" ;;
        search)      echo "TC005 or TC006 or TC007 or TC008" ;;
        lifecycle)   echo "TC009 or TC010 or TC011 or TC040" ;;
        agile)       echo "TC012 or TC013 or TC014 or TC015 or TC031" ;;
        collaborate) echo "TC016 or TC017 or TC018 or TC042" ;;
        relationships) echo "TC019 or TC020 or TC021 or TC063" ;;
        time)        echo "TC022 or TC023 or TC075" ;;
        bulk)        echo "TC024 or TC025 or TC041 or TC036" ;;
        dev)         echo "TC026 or TC027 or TC079" ;;
        fields)      echo "TC028 or TC077" ;;
        ops)         echo "TC029 or TC078" ;;
        admin)       echo "TC030" ;;
        jsm)         echo "TC055 or TC076" ;;
        *)           echo "" ;;
    esac
}

# Smoke test - one representative from each major skill
SMOKE_TESTS="TC001 or TC005 or TC009 or TC012 or TC019"

print_usage() {
    echo "Fast Iteration Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skill SKILL[,SKILL...]   Test specific skill(s): issue, search, lifecycle,"
    echo "                             agile, collaborate, relationships, time, bulk,"
    echo "                             dev, fields, ops, admin, jsm"
    echo "  --id TC###[,TC###...]      Test specific test ID(s)"
    echo "  --smoke                    Run 5 smoke tests (~1.5 min with --fast)"
    echo "  --failed                   Re-run only previously failed tests"
    echo "  --fast                     Use haiku model (faster, may differ slightly)"
    echo "  --production               Use default model (slower, matches production)"
    echo "  --parallel N               Run N tests in parallel (default: sequential)"
    echo "  --all                      Run all tests"
    echo "  -h, --help                 Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 --skill agile --fast --parallel 2   # Fast iteration on agile"
    echo "  $0 --smoke --fast                       # Quick smoke test"
    echo "  $0 --id TC012,TC015 --fast             # Test specific cases"
    echo "  $0 --production                         # Full production validation"
    echo ""
    echo "Timing estimates:"
    echo "  Smoke (5 tests):    ~1.5 min with --fast, ~2.5 min without"
    echo "  Single skill:       ~2-4 min with --fast"
    echo "  All tests:          ~10 min with --fast --parallel 4"
    echo "  All tests (prod):   ~22 min sequential"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skill)
            shift
            IFS=',' read -ra SKILLS <<< "$1"
            SKILL_FILTER=""
            for skill in "${SKILLS[@]}"; do
                skill=$(echo "$skill" | tr '[:upper:]' '[:lower:]')
                tests=$(get_skill_tests "$skill")
                if [[ -n "$tests" ]]; then
                    if [[ -n "$SKILL_FILTER" ]]; then
                        SKILL_FILTER="$SKILL_FILTER or $tests"
                    else
                        SKILL_FILTER="$tests"
                    fi
                else
                    echo "Error: Unknown skill '$skill'"
                    echo "Valid skills: issue, search, lifecycle, agile, collaborate,"
                    echo "              relationships, time, bulk, dev, fields, ops, admin, jsm"
                    exit 1
                fi
            done
            FILTER="-k \"$SKILL_FILTER\""
            shift
            ;;
        --id)
            shift
            IFS=',' read -ra IDS <<< "$1"
            ID_FILTER=""
            for id in "${IDS[@]}"; do
                if [[ -n "$ID_FILTER" ]]; then
                    ID_FILTER="$ID_FILTER or $id"
                else
                    ID_FILTER="$id"
                fi
            done
            FILTER="-k \"$ID_FILTER\""
            shift
            ;;
        --smoke)
            FILTER="-k \"$SMOKE_TESTS\""
            shift
            ;;
        --failed)
            RERUN_FAILED="--lf"
            shift
            ;;
        --fast)
            MODEL_ARGS="--model haiku"
            shift
            ;;
        --production)
            MODEL_ARGS=""
            shift
            ;;
        --parallel)
            shift
            PARALLEL="-n $1"
            shift
            ;;
        --all)
            FILTER=""
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Build command
CMD="pytest test_routing.py $EXTRA_ARGS $FILTER $MODEL_ARGS $PARALLEL $RERUN_FAILED"

# Print what we're running
echo "============================================"
echo "Fast Iteration Test Runner"
echo "============================================"
echo ""
echo "Command: $CMD"
echo ""
if [[ -n "$MODEL_ARGS" ]]; then
    echo "Model: haiku (fast iteration mode)"
else
    echo "Model: default (production mode)"
fi
if [[ -n "$PARALLEL" ]]; then
    echo "Parallel: $PARALLEL"
else
    echo "Parallel: sequential"
fi
echo ""
echo "============================================"
echo ""

# Run tests
eval $CMD

echo ""
echo "============================================"
echo "Tests complete"
echo "============================================"
