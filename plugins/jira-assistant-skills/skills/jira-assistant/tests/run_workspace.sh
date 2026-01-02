#!/usr/bin/env bash
#
# Run Claude in a container with a mounted workspace and JIRA access
#
# Combines file system operations with JIRA automation for hybrid workflows
# like organizing docs and closing related JIRA tickets.
#
# Authentication modes:
# 1. OAuth (default) - Uses credentials from macOS Keychain (free with subscription)
# 2. API Key (--api-key) - Uses ANTHROPIC_API_KEY environment variable (paid)
# 3. API Key from config (--api-key-from-config) - Reads from ~/.claude.json (paid)
#
# Usage:
#   ./run_workspace.sh --project <path> [options] [-- prompt or pytest-args]
#
# Examples:
#   # Interactive: organize docs and close JIRA subtask
#   ./run_workspace.sh --project ~/myproject --prompt "Organize the docs folder and close TES-123"
#
#   # Run specific workflow tests
#   ./run_workspace.sh --project ~/myproject --profile docs-jira -- -k "organize"
#
#   # Read-only mode for safe exploration
#   ./run_workspace.sh --project ~/myproject --readonly --prompt "What docs need updating?"
#
# Profiles:
#   docs-jira     File ops + JIRA issue/lifecycle (default)
#   code-review   File reading + JIRA comments
#   full-access   All file ops + all JIRA commands
#

set -e

# Source shared library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib_container.sh"

# =============================================================================
# Profile Definitions
# =============================================================================
# Each profile defines allowed tools for hybrid file + JIRA workflows
# =============================================================================

declare -A PROFILE_TOOLS
declare -A PROFILE_DESCRIPTION

# docs-jira: File operations + JIRA issue management (default)
PROFILE_TOOLS["docs-jira"]="Read Write Edit Glob Grep Bash(jira issue:*) Bash(jira lifecycle:*)"
PROFILE_DESCRIPTION["docs-jira"]="File operations + JIRA issue/lifecycle management"

# code-review: Read files + add JIRA comments
PROFILE_TOOLS["code-review"]="Read Glob Grep Bash(jira issue get:*) Bash(jira collaborate:*)"
PROFILE_DESCRIPTION["code-review"]="Read files + JIRA comments/collaboration"

# docs-only: Just file operations, no JIRA
PROFILE_TOOLS["docs-only"]="Read Write Edit Glob Grep"
PROFILE_DESCRIPTION["docs-only"]="File operations only, no JIRA access"

# full-access: Everything allowed
PROFILE_TOOLS["full-access"]=""
PROFILE_DESCRIPTION["full-access"]="All file and JIRA operations (no restrictions)"

# =============================================================================
# Script-specific Configuration
# =============================================================================

PROJECT_PATH=""
USE_API_KEY=false
USE_API_KEY_FROM_CONFIG=false
BUILD_IMAGE=false
READONLY=false
PROFILE="docs-jira"
MODEL=""
KEEP_CONTAINER=false
INTERACTIVE_PROMPT=""
PYTEST_ARGS=()

# =============================================================================
# Argument Parsing
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --project|-p)
            PROJECT_PATH="$2"
            shift 2
            ;;
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --readonly|--ro)
            READONLY=true
            shift
            ;;
        --prompt)
            INTERACTIVE_PROMPT="$2"
            shift 2
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
                printf "  %-14s %s\n" "$p" "${PROFILE_DESCRIPTION[$p]}"
            done
            echo ""
            echo "Tool restrictions per profile:"
            echo ""
            for p in "${!PROFILE_TOOLS[@]}"; do
                tools="${PROFILE_TOOLS[$p]}"
                if [[ -z "$tools" ]]; then
                    tools="(no restrictions)"
                fi
                printf "  %-14s %s\n" "$p:" "$tools"
            done
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 --project <path> [options] [-- prompt or pytest-args]"
            echo ""
            echo "Run Claude in a container with mounted workspace and JIRA access."
            echo ""
            echo "Required:"
            echo "  --project, -p PATH    Local project directory to mount"
            echo ""
            echo "Profiles:"
            echo "  --profile NAME        Workflow profile (docs-jira, code-review, docs-only, full-access)"
            echo "  --list-profiles       Show available profiles and their restrictions"
            echo ""
            echo "Authentication (choose one):"
            echo "  (default)              Use OAuth from macOS Keychain (free with subscription)"
            echo "  --api-key              Use ANTHROPIC_API_KEY environment variable (paid)"
            echo "  --api-key-from-config  Use primaryApiKey from ~/.claude.json (paid)"
            echo ""
            echo "Options:"
            echo "  --prompt TEXT         Run Claude with this prompt (interactive mode)"
            echo "  --readonly, --ro      Mount project as read-only"
            echo "  --build               Rebuild Docker image before running"
            echo "  --model NAME          Use specific model (sonnet, haiku, opus)"
            echo "  --keep                Don't remove container after run"
            echo "  --help                Show this help message"
            echo ""
            echo "Examples:"
            echo "  # Organize docs and close JIRA ticket"
            echo "  $0 --project ~/myproject --prompt \"Organize docs/ and close TES-123\""
            echo ""
            echo "  # Review code and add JIRA comment"
            echo "  $0 --project ~/myproject --profile code-review \\"
            echo "     --prompt \"Review src/auth.py and comment on TES-456\""
            echo ""
            echo "  # Safe exploration (read-only)"
            echo "  $0 --project ~/myproject --readonly \\"
            echo "     --prompt \"What documentation is missing?\""
            echo ""
            echo "  # Run pytest tests with workspace"
            echo "  $0 --project ~/myproject -- -k 'workspace_test'"
            echo ""
            echo "  # Windows: Use API key from .claude.json"
            echo "  $0 --project ~/myproject --api-key-from-config --prompt \"List docs\""
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

# Validate required arguments
if [[ -z "$PROJECT_PATH" ]]; then
    echo_error "--project is required"
    echo "Usage: $0 --project <path> [options]"
    exit 1
fi

# Resolve to absolute path
PROJECT_PATH="$(cd "$PROJECT_PATH" 2>/dev/null && pwd)" || {
    echo_error "Project path does not exist: $PROJECT_PATH"
    exit 1
}

# Validate profile
if [[ -z "${PROFILE_TOOLS[$PROFILE]+isset}" ]]; then
    echo_error "Unknown profile '$PROFILE'"
    echo "Use --list-profiles to see available profiles"
    exit 1
fi

# =============================================================================
# Main Runner
# =============================================================================

run_workspace() {
    local project_name
    project_name=$(basename "$PROJECT_PATH")

    echo_status "WORKSPACE" "Project: $project_name"
    echo_status "WORKSPACE" "Path: $PROJECT_PATH"
    echo_status "WORKSPACE" "Profile: $PROFILE"
    echo_status "WORKSPACE" "Description: ${PROFILE_DESCRIPTION[$PROFILE]}"

    local allowed_tools="${PROFILE_TOOLS[$PROFILE]}"
    if [[ -n "$allowed_tools" ]]; then
        echo_status "WORKSPACE" "Allowed tools: $allowed_tools"
    else
        echo_status "WORKSPACE" "Allowed tools: (no restrictions)"
    fi

    if [[ "$READONLY" == "true" ]]; then
        echo_status "WORKSPACE" "Mount mode: read-only"
    else
        echo_status "WORKSPACE" "Mount mode: read-write"
    fi
    echo ""

    echo_info "Starting workspace container..."

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

    # Mount project directory
    local mount_opts=""
    if [[ "$READONLY" == "true" ]]; then
        mount_opts=":ro"
    fi
    docker_args+=("-v" "$PROJECT_PATH:/workspace/project$mount_opts")

    # Set working directory to the project for natural file access
    docker_args+=("-w" "/workspace/project")

    # Authentication configuration
    if [[ "$USE_API_KEY" == "true" ]]; then
        docker_args+=("-e" "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}")
    else
        docker_args+=("-v" "$CREDS_TMP_DIR:/home/testrunner/.claude")
    fi

    # Enable host.docker.internal for container to reach host services
    docker_args+=("--add-host" "host.docker.internal:host-gateway")

    # Container-specific environment
    docker_args+=(
        "-e" "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"
        "-e" "CLAUDE_CODE_ACTION=bypassPermissions"
        "-e" "OTLP_HTTP_ENDPOINT=http://host.docker.internal:4318"
        "-e" "CLAUDE_PLUGIN_DIR=/workspace/plugin"
        "-e" "WORKSPACE_PROFILE=$PROFILE"
        "-e" "WORKSPACE_PROJECT=$project_name"
    )

    # Pass allowed tools if profile has restrictions
    if [[ -n "$allowed_tools" ]]; then
        docker_args+=("-e" "CLAUDE_ALLOWED_TOOLS=$allowed_tools")
    fi

    # Model selection
    if [[ -n "$MODEL" ]]; then
        docker_args+=("-e" "$(get_model_env "$MODEL")")
    fi

    # Determine run mode: interactive prompt or pytest
    local full_cmd
    if [[ -n "$INTERACTIVE_PROMPT" ]]; then
        # Interactive mode: run Claude with the prompt via stdin
        local escaped_prompt
        escaped_prompt=$(printf '%s' "$INTERACTIVE_PROMPT" | sed "s/'/'\\\\''/g")
        full_cmd="echo '$escaped_prompt' | claude --print --permission-mode dontAsk --plugin-dir /workspace/plugin"
    else
        # Test mode: run pytest
        full_cmd="pytest /workspace/tests/test_routing.py -v"

        # Add user-provided pytest args
        if [[ ${#PYTEST_ARGS[@]} -gt 0 ]]; then
            full_cmd+="$(quote_pytest_args "${PYTEST_ARGS[@]}")"
        fi
    fi

    # Override entrypoint to run shell command
    docker_args+=("--entrypoint" "/bin/bash")
    docker_args+=("$IMAGE_NAME:$IMAGE_TAG")
    docker_args+=("-c" "$full_cmd")

    # Run container
    echo_info "Running: docker ${docker_args[*]}"
    docker "${docker_args[@]}"
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo "=============================================="
    echo "JIRA Skills Workspace Runner"
    echo "=============================================="
    echo ""

    setup_cleanup_trap
    validate_auth "$USE_API_KEY" "$USE_API_KEY_FROM_CONFIG"
    ensure_image "$BUILD_IMAGE"
    run_workspace

    echo ""
    echo_info "Workspace session completed (profile: $PROFILE)"
}

main "$@"
