#!/usr/bin/env bash
#
# Run routing tests in a Docker container with isolated environment
#
# Authentication modes:
# 1. OAuth (default) - Uses credentials from macOS Keychain (free with subscription)
# 2. API Key (--api-key) - Uses ANTHROPIC_API_KEY environment variable (paid)
# 3. API Key from config (--api-key-from-config) - Reads from ~/.claude.json (paid)
#
# Usage:
#   ./run_container_tests.sh [options] [-- pytest-args...]
#
# Examples:
#   ./run_container_tests.sh                       # Run with OAuth (macOS)
#   ./run_container_tests.sh --parallel 4          # Parallel with OAuth
#   ./run_container_tests.sh --api-key             # Run with API key from env
#   ./run_container_tests.sh --api-key-from-config # Run with API key from .claude.json
#   ./run_container_tests.sh -- -k "TC001"         # Single test
#
# Environment Variables:
#   ANTHROPIC_API_KEY     - API key (only needed with --api-key)
#

set -e

# Source shared library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib_container.sh"

# =============================================================================
# Script-specific Configuration
# =============================================================================

USE_API_KEY=false
USE_API_KEY_FROM_CONFIG=false
BUILD_IMAGE=false
PARALLEL=""
MODEL=""
KEEP_CONTAINER=false
PYTEST_ARGS=()

# =============================================================================
# Argument Parsing
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
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
        --help|-h)
            echo "Usage: $0 [options] [-- pytest-args...]"
            echo ""
            echo "Run routing tests in a Docker container."
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
            echo "  $0                           # Run all tests with OAuth"
            echo "  $0 --parallel 4              # 4 parallel workers"
            echo "  $0 -- -k 'TC001' -v          # Single test"
            echo "  $0 --api-key                 # Use API key from environment"
            echo "  $0 --api-key-from-config     # Use API key from .claude.json"
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

# =============================================================================
# Main Runner
# =============================================================================

run_tests() {
    echo_info "Starting container tests..."

    # Build docker run command
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
    )

    # Model selection
    if [[ -n "$MODEL" ]]; then
        docker_args+=("-e" "$(get_model_env "$MODEL")")
    fi

    # Build pytest command
    local pytest_cmd="pytest /workspace/tests/test_routing.py -v"

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
    echo "JIRA Skills Container Test Runner"
    echo "=============================================="
    echo ""

    setup_cleanup_trap
    validate_auth "$USE_API_KEY" "$USE_API_KEY_FROM_CONFIG"
    ensure_image "$BUILD_IMAGE"
    run_tests

    echo ""
    echo_info "Container tests completed"
}

main "$@"
