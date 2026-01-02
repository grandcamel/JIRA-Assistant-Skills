#!/usr/bin/env bash
#
# Run routing tests in a Docker container with isolated environment
#
# This script supports three authentication modes:
# 1. Token Server (--token-server) - Auto-refreshing OAuth via host server (recommended for long jobs)
# 2. OAuth Token (ANTHROPIC_AUTH_TOKEN) - Static token, 5-min TTL (for quick tests)
# 3. API Key (ANTHROPIC_API_KEY) - Uses API credits (paid)
#
# Usage:
#   ./run_container_tests.sh [options] [-- pytest-args...]
#
# Examples:
#   ./run_container_tests.sh --token-server             # Auto-refresh OAuth (recommended)
#   ./run_container_tests.sh                            # Run with static OAuth token
#   ./run_container_tests.sh --api-key                  # Run with API key (paid)
#   ./run_container_tests.sh --token-server --parallel 4  # Long job with parallelism
#   ./run_container_tests.sh -- -k "TC001" -v           # Pass args to pytest
#
# Environment Variables:
#   ANTHROPIC_AUTH_TOKEN  - OAuth token for subscription-based auth (static)
#   ANTHROPIC_API_KEY     - API key for API-based auth
#   TOKEN_SERVER_PORT     - Port for token server (default: 9876)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
IMAGE_NAME="jira-skills-test-runner"
IMAGE_TAG="latest"
TOKEN_SERVER_PORT="${TOKEN_SERVER_PORT:-9876}"
SETTINGS_TMP_DIR=""

# Default options
USE_API_KEY=false
USE_TOKEN_SERVER=false
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
        --token-server)
            USE_TOKEN_SERVER=true
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
            echo "Authentication Options:"
            echo "  --token-server  Use auto-refreshing OAuth via host token server (recommended for long jobs)"
            echo "  --api-key       Use ANTHROPIC_API_KEY instead of OAuth token (paid)"
            echo "  (default)       Use static ANTHROPIC_AUTH_TOKEN (5-min TTL)"
            echo ""
            echo "Other Options:"
            echo "  --build         Rebuild Docker image before running"
            echo "  --parallel N    Run N tests in parallel (requires pytest-xdist)"
            echo "  --model NAME    Use specific model (sonnet, haiku, opus)"
            echo "  --keep          Don't remove container after run"
            echo "  --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --token-server              # Long running job with auto-refresh"
            echo "  $0 --token-server --parallel 4 # Parallel with auto-refresh"
            echo "  $0 --build --parallel 4        # Rebuild and run 4 parallel"
            echo "  $0 -- -k 'direct' -v           # Run only direct tests"
            echo ""
            echo "Token Server Mode (--token-server):"
            echo "  - Starts a local HTTP server that serves fresh tokens from macOS Keychain"
            echo "  - Container uses apiKeyHelper to fetch tokens every 4 minutes"
            echo "  - Supports jobs longer than 5 minutes without token expiry"
            echo "  - Automatically cleans up on exit"
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

    # Stop token server if we started it
    if [[ "$USE_TOKEN_SERVER" == "true" ]]; then
        echo_info "Stopping token server..."
        "$SCRIPT_DIR/token-server.sh" --stop 2>/dev/null || true
    fi

    # Remove temporary settings directory
    if [[ -n "$SETTINGS_TMP_DIR" && -d "$SETTINGS_TMP_DIR" ]]; then
        rm -rf "$SETTINGS_TMP_DIR"
    fi

    exit $exit_code
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

# Start token server for auto-refresh mode
start_token_server() {
    echo_info "Starting token server for OAuth auto-refresh..."

    # Check if token server script exists
    if [[ ! -x "$SCRIPT_DIR/token-server.sh" ]]; then
        echo_error "token-server.sh not found or not executable"
        exit 1
    fi

    # Start the server
    "$SCRIPT_DIR/token-server.sh" --port "$TOKEN_SERVER_PORT"

    # Wait a moment for server to start
    sleep 1

    # Verify server is running
    if ! curl -s "http://localhost:$TOKEN_SERVER_PORT" >/dev/null 2>&1; then
        echo_error "Token server failed to start"
        exit 1
    fi

    echo_info "Token server running on port $TOKEN_SERVER_PORT"
}

# Create settings.json with apiKeyHelper for container
create_container_settings() {
    SETTINGS_TMP_DIR=$(mktemp -d)
    local settings_file="$SETTINGS_TMP_DIR/settings.json"

    # Create settings.json with apiKeyHelper pointing to host token server
    cat > "$settings_file" << EOF
{
  "apiKeyHelper": "curl -s http://host.docker.internal:${TOKEN_SERVER_PORT}"
}
EOF

    echo_info "Created container settings with apiKeyHelper"
    echo "$SETTINGS_TMP_DIR"
}

# Validate authentication
validate_auth() {
    if [[ "$USE_TOKEN_SERVER" == "true" ]]; then
        # Token server mode - verify we can get a token from keychain
        if ! security find-generic-password -a "$USER" -s 'Claude Code-credentials' -w >/dev/null 2>&1; then
            echo_error "Cannot access Claude Code credentials in Keychain"
            echo "Make sure you're logged into Claude Code"
            exit 1
        fi
        echo_info "Using token server mode (auto-refresh OAuth)"
    elif [[ "$USE_API_KEY" == "true" ]]; then
        if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
            echo_error "ANTHROPIC_API_KEY is not set"
            echo "Export your API key: export ANTHROPIC_API_KEY='sk-ant-...'"
            exit 1
        fi
        echo_info "Using API key authentication (paid)"
    else
        if [[ -z "${ANTHROPIC_AUTH_TOKEN:-}" ]]; then
            echo_error "ANTHROPIC_AUTH_TOKEN is not set"
            echo ""
            echo "Options:"
            echo ""
            echo "1. Use token server for long jobs (recommended):"
            echo "   $0 --token-server"
            echo ""
            echo "2. Use static OAuth token (5-min TTL):"
            echo "   export ANTHROPIC_AUTH_TOKEN=\$(security find-generic-password -a \$USER -s 'Claude Code-credentials' -w | jq -r .claudeAiOauth.accessToken)"
            echo "   $0"
            echo ""
            echo "3. Use API key (paid):"
            echo "   export ANTHROPIC_API_KEY='sk-ant-...'"
            echo "   $0 --api-key"
            exit 1
        fi
        echo_info "Using static OAuth token (5-min TTL)"
        echo_warn "For jobs >5 minutes, use --token-server flag"
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
    if [[ "$USE_TOKEN_SERVER" == "true" ]]; then
        # Token server mode: mount settings.json with apiKeyHelper
        docker_args+=(
            "-v" "$SETTINGS_TMP_DIR/settings.json:/home/testrunner/.claude/settings.json:ro"
        )
        # Add Docker host networking for host.docker.internal
        docker_args+=("--add-host" "host.docker.internal:host-gateway")
    elif [[ "$USE_API_KEY" == "true" ]]; then
        docker_args+=("-e" "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}")
    else
        docker_args+=("-e" "ANTHROPIC_AUTH_TOKEN=${ANTHROPIC_AUTH_TOKEN}")
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
    # Plugin is mounted at /workspace/plugin, install it so Claude Code can find SKILL.md files
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

    # Start token server if using that mode
    if [[ "$USE_TOKEN_SERVER" == "true" ]]; then
        start_token_server
        create_container_settings
    fi

    # Run tests
    run_tests

    echo ""
    echo_info "Container tests completed"
}

main "$@"
