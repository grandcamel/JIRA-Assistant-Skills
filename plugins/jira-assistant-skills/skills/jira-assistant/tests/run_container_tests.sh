#!/usr/bin/env bash
#
# Run routing tests in a Docker container with isolated environment
#
# Authentication modes:
# 1. OAuth (default) - Uses credentials from macOS Keychain (free with subscription)
# 2. API Key (--api-key) - Uses ANTHROPIC_API_KEY (paid)
#
# Usage:
#   ./run_container_tests.sh [options] [-- pytest-args...]
#
# Examples:
#   ./run_container_tests.sh                       # Run with OAuth (macOS)
#   ./run_container_tests.sh --parallel 4          # Parallel with OAuth
#   ./run_container_tests.sh --api-key             # Run with API key
#   ./run_container_tests.sh -- -k "TC001"         # Single test
#
# Environment Variables:
#   ANTHROPIC_API_KEY     - API key (only needed with --api-key)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
IMAGE_NAME="jira-skills-test-runner"
IMAGE_TAG="latest"
CREDS_TMP_DIR=""

# Default options
USE_API_KEY=false
BUILD_IMAGE=false
PARALLEL=""
MODEL=""
KEEP_CONTAINER=false
PYTEST_ARGS=()

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-key)
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
            echo "  (default)       Use OAuth from macOS Keychain (free with subscription)"
            echo "  --api-key       Use ANTHROPIC_API_KEY environment variable (paid)"
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
            echo "  $0 --api-key                 # Use API key instead"
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

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Cleanup function
cleanup() {
    local exit_code=$?

    # Remove temporary credentials directory
    if [[ -n "$CREDS_TMP_DIR" && -d "$CREDS_TMP_DIR" ]]; then
        rm -rf "$CREDS_TMP_DIR"
    fi

    exit $exit_code
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

# Get OAuth credentials from macOS Keychain
get_oauth_credentials() {
    if [[ "$(uname)" != "Darwin" ]]; then
        echo_error "OAuth mode requires macOS (for Keychain access)"
        echo "Use --api-key mode on Linux, or run tests on macOS."
        return 1
    fi

    local creds
    creds=$(security find-generic-password -a "$USER" -s 'Claude Code-credentials' -w 2>/dev/null) || {
        echo_error "Cannot access Claude Code credentials in Keychain"
        echo ""
        echo "Make sure you're logged into Claude Code:"
        echo "  claude login"
        return 1
    }

    # Verify credentials are valid JSON with required fields
    if ! echo "$creds" | jq -e '.claudeAiOauth.accessToken' >/dev/null 2>&1; then
        echo_error "Invalid credentials format in Keychain"
        echo "Try logging in again: claude login"
        return 1
    fi

    echo "$creds"
}

# Create credentials directory for container
create_credentials_dir() {
    CREDS_TMP_DIR=$(mktemp -d)

    local creds
    creds=$(get_oauth_credentials) || return 1

    echo "$creds" > "$CREDS_TMP_DIR/.credentials.json"
    chmod 600 "$CREDS_TMP_DIR/.credentials.json"

    echo_info "OAuth credentials prepared for container"
    return 0
}

# Validate authentication
validate_auth() {
    if [[ "$USE_API_KEY" == "true" ]]; then
        if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
            echo_error "ANTHROPIC_API_KEY is not set"
            echo ""
            echo "Export your API key:"
            echo "  export ANTHROPIC_API_KEY='sk-ant-api03-...'"
            echo ""
            echo "Or use OAuth mode (default) on macOS."
            exit 1
        fi
        echo_info "Using API key authentication"
    else
        if ! create_credentials_dir; then
            exit 1
        fi
        echo_info "Using OAuth authentication (free with subscription)"
    fi
}

# Build Docker image
build_image() {
    echo_info "Building Docker image: $IMAGE_NAME:$IMAGE_TAG"

    docker build \
        -t "$IMAGE_NAME:$IMAGE_TAG" \
        -f "$SCRIPT_DIR/Dockerfile" \
        "$SCRIPT_DIR"

    echo_info "Image built successfully"
}

# Check if image exists
check_image() {
    if ! docker image inspect "$IMAGE_NAME:$IMAGE_TAG" &>/dev/null; then
        echo_warn "Image not found, building..."
        build_image
    fi
}

# Run tests in container
run_tests() {
    echo_info "Starting container tests..."

    # Build docker run command
    local docker_args=(
        "run"
    )

    # Remove container after run unless --keep
    if [[ "$KEEP_CONTAINER" != "true" ]]; then
        docker_args+=("--rm")
    fi

    # Mount plugin directory read-only
    docker_args+=(
        "-v" "$PLUGIN_ROOT:/workspace/plugin:ro"
        "-v" "$SCRIPT_DIR:/workspace/tests:ro"
    )

    # Set working directory
    docker_args+=("-w" "/workspace/tests")

    # Authentication configuration
    if [[ "$USE_API_KEY" == "true" ]]; then
        docker_args+=("-e" "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}")
    else
        # Mount OAuth credentials
        docker_args+=("-v" "$CREDS_TMP_DIR:/home/testrunner/.claude")
    fi

    # Container-specific environment
    docker_args+=(
        "-e" "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"
        "-e" "CLAUDE_CODE_ACTION=bypassPermissions"
    )

    # Model selection
    if [[ -n "$MODEL" ]]; then
        case "$MODEL" in
            haiku)
                docker_args+=("-e" "ANTHROPIC_MODEL=claude-haiku-3-5-20241022")
                ;;
            sonnet)
                docker_args+=("-e" "ANTHROPIC_MODEL=claude-sonnet-4-20250514")
                ;;
            opus)
                docker_args+=("-e" "ANTHROPIC_MODEL=claude-opus-4-20250514")
                ;;
            *)
                docker_args+=("-e" "ANTHROPIC_MODEL=$MODEL")
                ;;
        esac
    fi

    # Build the full command: install plugin, then run pytest
    local install_cmd="claude plugins add /workspace/plugin --local 2>/dev/null || true"

    # Build pytest command
    local pytest_cmd="pytest test_routing.py -v"

    # Add parallel option
    if [[ -n "$PARALLEL" ]]; then
        pytest_cmd+=" -n $PARALLEL"
    fi

    # Add user-provided pytest args
    if [[ ${#PYTEST_ARGS[@]} -gt 0 ]]; then
        pytest_cmd+=" ${PYTEST_ARGS[*]}"
    fi

    # Combine: install plugin then run tests
    local full_cmd="$install_cmd && $pytest_cmd"

    # Override entrypoint to run shell command
    docker_args+=("--entrypoint" "/bin/bash")
    docker_args+=("$IMAGE_NAME:$IMAGE_TAG")
    docker_args+=("-c" "$full_cmd")

    # Run container
    echo_info "Running: docker ${docker_args[*]}"
    docker "${docker_args[@]}"
}

# Main execution
main() {
    echo "=============================================="
    echo "JIRA Skills Container Test Runner"
    echo "=============================================="
    echo ""

    # Validate authentication
    validate_auth

    # Build image if requested or needed
    if [[ "$BUILD_IMAGE" == "true" ]]; then
        build_image
    else
        check_image
    fi

    # Run tests
    run_tests

    echo ""
    echo_info "Container tests completed"
}

main "$@"
