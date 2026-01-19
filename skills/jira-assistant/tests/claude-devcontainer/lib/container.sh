#!/usr/bin/env bash
#
# Shared library for claude-devcontainer scripts
#
# This file contains common functions used by:
#   - run.sh (main developer container)
#   - run-sandboxed.sh (restricted tool access)
#   - run-workspace.sh (hybrid workflows)
#   - run-tests.sh (CI test patterns)
#
# Usage: source this file at the top of each script
#   source "$(dirname "${BASH_SOURCE[0]}")/../lib/container.sh"
#

# =============================================================================
# Common Configuration
# =============================================================================

LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$LIB_DIR/.." && pwd)"
IMAGE_NAME="${CLAUDE_DEVCONTAINER_IMAGE:-claude-devcontainer}"
IMAGE_TAG="${CLAUDE_DEVCONTAINER_TAG:-latest}"
CREDS_TMP_DIR=""

# Plugin/workspace directory (can be overridden by scripts)
PLUGIN_DIR="${CLAUDE_PLUGIN_DIR:-}"

# =============================================================================
# Color Output
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }
echo_status() { echo -e "${CYAN}[$1]${NC} $2"; }
echo_step() { echo -e "${BLUE}==>${NC} ${CYAN}$1${NC}"; }

# =============================================================================
# Cleanup
# =============================================================================

lib_cleanup() {
    local exit_code=$?
    if [[ -n "$CREDS_TMP_DIR" && -d "$CREDS_TMP_DIR" ]]; then
        rm -rf "$CREDS_TMP_DIR"
    fi
    exit $exit_code
}

# Set up cleanup trap (call this in your script's init)
setup_cleanup_trap() {
    trap lib_cleanup EXIT INT TERM
}

# =============================================================================
# API Key from Config
# =============================================================================

get_api_key_from_config() {
    local config_paths=(
        "$HOME/.claude.json"
        "$HOME/.claude/.claude.json"
        "${APPDATA:-}/.claude.json"
        "${APPDATA:-}/claude/.claude.json"
    )

    for config_path in "${config_paths[@]}"; do
        if [[ -f "$config_path" ]]; then
            local api_key
            api_key=$(jq -r '.primaryApiKey // empty' "$config_path" 2>/dev/null)
            if [[ -n "$api_key" && "$api_key" != "null" ]]; then
                echo "$api_key"
                return 0
            fi
        fi
    done

    echo_error "No primaryApiKey found in .claude.json"
    echo ""
    echo "Searched locations:"
    for config_path in "${config_paths[@]}"; do
        if [[ -n "$config_path" ]]; then
            echo "  - $config_path"
        fi
    done
    echo ""
    echo "Ensure your .claude.json contains:"
    echo '  { "primaryApiKey": "sk-ant-api03-..." }'
    return 1
}

# =============================================================================
# OAuth Credentials (macOS Keychain)
# =============================================================================

get_oauth_credentials() {
    if [[ "$(uname)" != "Darwin" ]]; then
        echo_error "OAuth mode requires macOS (for Keychain access)"
        echo "Use --api-key or --api-key-from-config on Linux/Windows."
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

    if ! echo "$creds" | jq -e '.claudeAiOauth.accessToken' >/dev/null 2>&1; then
        echo_error "Invalid credentials format in Keychain"
        echo "Try logging in again: claude login"
        return 1
    fi

    echo "$creds"
}

create_credentials_dir() {
    CREDS_TMP_DIR=$(mktemp -d)
    local creds
    creds=$(get_oauth_credentials) || return 1
    echo "$creds" > "$CREDS_TMP_DIR/.credentials.json"
    chmod 600 "$CREDS_TMP_DIR/.credentials.json"
    echo_info "OAuth credentials prepared for container"
    return 0
}

# =============================================================================
# Authentication Validation
# =============================================================================

# Arguments:
#   $1 - USE_API_KEY (true/false)
#   $2 - USE_API_KEY_FROM_CONFIG (true/false)
validate_auth() {
    local use_api_key="${1:-false}"
    local use_api_key_from_config="${2:-false}"

    if [[ "$use_api_key" == "true" ]]; then
        if [[ "$use_api_key_from_config" == "true" ]]; then
            ANTHROPIC_API_KEY=$(get_api_key_from_config) || exit 1
            export ANTHROPIC_API_KEY
            echo_info "Using API key from .claude.json"
        elif [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
            echo_error "ANTHROPIC_API_KEY is not set"
            echo ""
            echo "Export your API key:"
            echo "  export ANTHROPIC_API_KEY='sk-ant-api03-...'"
            echo ""
            echo "Or use --api-key-from-config to read from .claude.json"
            echo "Or use OAuth mode (default) on macOS."
            exit 1
        else
            echo_info "Using API key from environment"
        fi
    else
        if ! create_credentials_dir; then
            exit 1
        fi
        echo_info "Using OAuth authentication (free with subscription)"
    fi
}

# =============================================================================
# Docker Image Management
# =============================================================================

build_image() {
    local dockerfile="${1:-$PROJECT_ROOT/Dockerfile}"
    echo_info "Building Docker image: $IMAGE_NAME:$IMAGE_TAG"
    docker build \
        -t "$IMAGE_NAME:$IMAGE_TAG" \
        -f "$dockerfile" \
        "$PROJECT_ROOT"
    echo_info "Image built successfully"
}

check_image() {
    if ! docker image inspect "$IMAGE_NAME:$IMAGE_TAG" &>/dev/null; then
        echo_warn "Image not found, building..."
        build_image
    fi
}

ensure_image() {
    local force_build="${1:-false}"
    local dockerfile="${2:-}"
    if [[ "$force_build" == "true" ]]; then
        build_image "$dockerfile"
    else
        check_image
    fi
}

# =============================================================================
# Docker Run Helpers
# =============================================================================

# Build base docker args common to all scripts
# Arguments:
#   $1 - keep_container (true/false)
#   $2 - use_api_key (true/false)
#   $3 - home_user (default: devuser)
build_base_docker_args() {
    local keep_container="${1:-false}"
    local use_api_key="${2:-false}"
    local home_user="${3:-devuser}"

    local docker_args=("run")

    if [[ "$keep_container" != "true" ]]; then
        docker_args+=("--rm")
    fi

    # Mount project root (for config access)
    docker_args+=("-v" "$PROJECT_ROOT:/workspace/devcontainer:ro")

    # Authentication configuration
    if [[ "$use_api_key" == "true" ]]; then
        docker_args+=("-e" "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}")
    else
        docker_args+=("-v" "$CREDS_TMP_DIR:/home/$home_user/.claude")
    fi

    # Enable host.docker.internal
    docker_args+=("--add-host" "host.docker.internal:host-gateway")

    # Container-specific environment
    docker_args+=(
        "-e" "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"
        "-e" "CLAUDE_CODE_ACTION=bypassPermissions"
        "-e" "OTLP_HTTP_ENDPOINT=http://host.docker.internal:4318"
        "-e" "TERM=xterm-256color"
    )

    # Plugin directory (if specified)
    if [[ -n "$PLUGIN_DIR" ]]; then
        docker_args+=(
            "-v" "$PLUGIN_DIR:/workspace/plugin:ro"
            "-e" "CLAUDE_PLUGIN_DIR=/workspace/plugin"
        )
    fi

    # Return args by printing (caller captures with $())
    printf '%s\n' "${docker_args[@]}"
}

# Add model environment variable
# Arguments:
#   $1 - model name (haiku, sonnet, opus, or full model ID)
get_model_env() {
    local model="$1"
    case "$model" in
        haiku)
            echo "ANTHROPIC_MODEL=claude-haiku-3-5-20241022"
            ;;
        sonnet)
            echo "ANTHROPIC_MODEL=claude-sonnet-4-20250514"
            ;;
        opus)
            echo "ANTHROPIC_MODEL=claude-opus-4-20250514"
            ;;
        *)
            echo "ANTHROPIC_MODEL=$model"
            ;;
    esac
}

# =============================================================================
# Pytest Args Helper
# =============================================================================

# Quote pytest args for shell execution
# Arguments:
#   $@ - pytest args array
quote_pytest_args() {
    local quoted=""
    for arg in "$@"; do
        local escaped_arg
        escaped_arg=$(printf '%s' "$arg" | sed "s/'/'\\\\''/g")
        quoted+=" '$escaped_arg'"
    done
    echo "$quoted"
}

# =============================================================================
# Version Information
# =============================================================================

get_version() {
    if [[ -f "$PROJECT_ROOT/VERSION" ]]; then
        cat "$PROJECT_ROOT/VERSION"
    else
        echo "dev"
    fi
}
