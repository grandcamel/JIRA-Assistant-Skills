#!/usr/bin/env bash
#
# Run routing tests in a sandboxed Docker container with tool restrictions
#
# Profiles control which Claude tools and JIRA CLI commands are allowed:
#   - read-only:   View/search only, no modifications
#   - search-only: JQL search operations only
#   - issue-only:  JIRA issue CRUD operations only
#   - full:        All tools and commands (default)
#
# Authentication modes:
# 1. OAuth (default) - Uses credentials from macOS Keychain (free with subscription)
# 2. API Key (--api-key) - Uses ANTHROPIC_API_KEY environment variable (paid)
# 3. API Key from config (--api-key-from-config) - Reads from ~/.claude.json (paid)
#
# Usage:
#   ./run_sandboxed.sh --profile <profile> [options] [-- pytest-args...]
#
# Examples:
#   ./run_sandboxed.sh --profile read-only              # Safe demo mode
#   ./run_sandboxed.sh --profile search-only -- -k TC005  # Test JQL routing
#   ./run_sandboxed.sh --profile issue-only --validate  # Run with validation tests
#   ./run_sandboxed.sh --profile full                   # Same as run_container_tests.sh
#

set -e

# Source shared library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib_container.sh"

# =============================================================================
# Profile Definitions
# =============================================================================

declare -A PROFILE_TOOLS
declare -A PROFILE_DESCRIPTION

# read-only: View and search, no modifications
PROFILE_TOOLS["read-only"]="Read Glob Grep WebFetch WebSearch Bash(jira-as issue get:*) Bash(jira-as search:*) Bash(jira-as fields list:*) Bash(jira-as fields get:*)"
PROFILE_DESCRIPTION["read-only"]="View/search only - no create, update, or delete operations"

# search-only: Just JQL search operations
PROFILE_TOOLS["search-only"]="Read Glob Grep Bash(jira-as search:*)"
PROFILE_DESCRIPTION["search-only"]="JQL search operations only"

# issue-only: JIRA issue CRUD operations
PROFILE_TOOLS["issue-only"]="Read Glob Grep Bash(jira-as issue:*)"
PROFILE_DESCRIPTION["issue-only"]="JIRA issue operations only (get, create, update, delete)"

# full: Everything allowed (default)
PROFILE_TOOLS["full"]=""
PROFILE_DESCRIPTION["full"]="All tools and commands allowed (no restrictions)"

# =============================================================================
# Script-specific Configuration
# =============================================================================

USE_API_KEY=false
USE_API_KEY_FROM_CONFIG=false
BUILD_IMAGE=false
PARALLEL=""
MODEL=""
KEEP_CONTAINER=false
PROFILE="full"
RUN_VALIDATION=false
PYTEST_ARGS=()

# =============================================================================
# Argument Parsing
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --validate)
            RUN_VALIDATION=true
            shift
            ;;
        --api-key)
            USE_API_KEY=true
            shift
            ;;
        --api-key-from-config)
            USE_API_KEY_FROM_CONFIG=true
            USE_API_KEY=true
            shift
            ;;
        --build)
            BUILD_IMAGE=true
            shift
            ;;
        --parallel)
            PARALLEL="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --keep)
            KEEP_CONTAINER=true
            shift
            ;;
        --list-profiles)
            echo "Available profiles:"
            echo ""
            for p in "${!PROFILE_DESCRIPTION[@]}"; do
                printf "  %-12s %s\n" "$p" "${PROFILE_DESCRIPTION[$p]}"
            done
            echo ""
            echo "Tool restrictions per profile:"
            echo ""
            for p in "${!PROFILE_TOOLS[@]}"; do
                tools="${PROFILE_TOOLS[$p]}"
                if [[ -z "$tools" ]]; then
                    tools="(no restrictions)"
                fi
                printf "  %-12s %s\n" "$p:" "$tools"
            done
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 --profile <profile> [options] [-- pytest-args...]"
            echo ""
            echo "Run routing tests in a sandboxed Docker container."
            echo ""
            echo "Profiles:"
            echo "  --profile NAME         Sandbox profile (read-only, search-only, issue-only, full)"
            echo "  --list-profiles        Show available profiles and their restrictions"
            echo "  --validate             Also run sandbox validation tests"
            echo ""
            echo "Authentication (choose one):"
            echo "  (default)              Use OAuth from macOS Keychain (free with subscription)"
            echo "  --api-key              Use ANTHROPIC_API_KEY environment variable (paid)"
            echo "  --api-key-from-config  Use primaryApiKey from ~/.claude.json (paid)"
            echo ""
            echo "Options:"
            echo "  --build         Rebuild Docker image before running"
            echo "  --parallel N    Run N tests in parallel (requires pytest-xdist)"
            echo "  --model NAME    Use specific model (sonnet, haiku, opus)"
            echo "  --keep          Don't remove container after run"
            echo "  --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --profile read-only                    # Safe demo mode"
            echo "  $0 --profile search-only -- -k 'TC005'    # Test JQL routing"
            echo "  $0 --profile issue-only --validate        # With validation tests"
            echo "  $0 --list-profiles                        # Show all profiles"
            echo "  $0 --profile full --api-key-from-config   # Windows with API key"
            exit 0
            ;;
        --)
            shift
            PYTEST_ARGS=("$@")
            break
            ;;
        *)
            PYTEST_ARGS+=("$1")
            shift
            ;;
    esac
done

# Validate profile
if [[ -z "${PROFILE_TOOLS[$PROFILE]+isset}" ]]; then
    echo_error "Unknown profile '$PROFILE'"
    echo "Use --list-profiles to see available profiles"
    exit 1
fi

# =============================================================================
# Main Runner
# =============================================================================

run_tests() {
    echo_status "PROFILE" "Profile: $PROFILE"
    echo_status "PROFILE" "Description: ${PROFILE_DESCRIPTION[$PROFILE]}"

    local allowed_tools="${PROFILE_TOOLS[$PROFILE]}"
    if [[ -n "$allowed_tools" ]]; then
        echo_status "PROFILE" "Allowed tools: $allowed_tools"
    else
        echo_status "PROFILE" "Allowed tools: (no restrictions)"
    fi
    echo ""

    echo_info "Starting sandboxed container tests..."

    local docker_args=("run")

    if [[ "$KEEP_CONTAINER" != "true" ]]; then
        docker_args+=("--rm")
    fi

    # Mount plugin directory read-only
    docker_args+=(
        "-v" "$PLUGIN_ROOT:/workspace/plugin:ro"
        "-v" "$SCRIPT_DIR:/workspace/tests:ro"
    )

    # Set working directory (use /tmp to avoid semantic confusion)
    docker_args+=("-w" "/tmp")

    # Authentication configuration
    if [[ "$USE_API_KEY" == "true" ]]; then
        docker_args+=("-e" "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}")
    else
        docker_args+=("-v" "$CREDS_TMP_DIR:/home/testrunner/.claude")
    fi

    # Enable host.docker.internal
    docker_args+=("--add-host" "host.docker.internal:host-gateway")

    # Container-specific environment
    docker_args+=(
        "-e" "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"
        "-e" "CLAUDE_CODE_ACTION=bypassPermissions"
        "-e" "OTLP_HTTP_ENDPOINT=http://host.docker.internal:4318"
        "-e" "CLAUDE_PLUGIN_DIR=/workspace/plugin"
        "-e" "SANDBOX_PROFILE=$PROFILE"
    )

    # Pass allowed tools if profile has restrictions
    if [[ -n "$allowed_tools" ]]; then
        docker_args+=("-e" "CLAUDE_ALLOWED_TOOLS=$allowed_tools")
    fi

    # Model selection
    if [[ -n "$MODEL" ]]; then
        docker_args+=("-e" "$(get_model_env "$MODEL")")
    fi

    # Build pytest command
    local pytest_cmd="pytest /workspace/tests/test_routing.py -v"

    # Add validation tests if requested
    if [[ "$RUN_VALIDATION" == "true" ]]; then
        pytest_cmd="pytest /workspace/tests/test_routing.py /workspace/tests/test_sandbox_validation.py -v"
    fi

    # Add parallel option
    if [[ -n "$PARALLEL" ]]; then
        pytest_cmd+=" -n $PARALLEL"
    fi

    # Add user-provided pytest args
    if [[ ${#PYTEST_ARGS[@]} -gt 0 ]]; then
        pytest_cmd+="$(quote_pytest_args "${PYTEST_ARGS[@]}")"
    fi

    # Override entrypoint to run shell command
    docker_args+=("--entrypoint" "/bin/bash")
    docker_args+=("$IMAGE_NAME:$IMAGE_TAG")
    docker_args+=("-c" "$pytest_cmd")

    # Run container
    echo_info "Running: docker ${docker_args[*]}"
    docker "${docker_args[@]}"
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo "=============================================="
    echo "JIRA Skills Sandboxed Test Runner"
    echo "=============================================="
    echo ""

    setup_cleanup_trap
    validate_auth "$USE_API_KEY" "$USE_API_KEY_FROM_CONFIG"
    ensure_image "$BUILD_IMAGE"
    run_tests

    echo ""
    echo_info "Sandboxed tests completed (profile: $PROFILE)"
}

main "$@"
