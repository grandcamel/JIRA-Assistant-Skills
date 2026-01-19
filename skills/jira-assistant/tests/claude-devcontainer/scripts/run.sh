#!/usr/bin/env bash
#
# Run a batteries-included developer container with Claude Code and common toolchains
#
# Provides a fully-loaded development environment with:
#   Languages:  Python 3, Node.js 20, Go 1.22, Rust (stable)
#   Tools:      git, jq, yq, ripgrep, fd, fzf, httpie, shellcheck
#   Cloud:      AWS CLI, GitHub CLI
#   Databases:  PostgreSQL, MySQL, Redis, SQLite clients
#   Build:      make, cmake, gcc
#   Containers: Docker CLI (mount socket for Docker-in-Docker)
#
# Authentication modes:
# 1. OAuth (default) - Uses credentials from macOS Keychain (free with subscription)
# 2. API Key (--api-key) - Uses ANTHROPIC_API_KEY environment variable (paid)
# 3. API Key from config (--api-key-from-config) - Reads from ~/.claude.json (paid)
#
# Usage:
#   ./run.sh [options] [-- command...]
#
# Examples:
#   # Interactive shell with current directory mounted
#   ./run.sh
#
#   # Mount specific project
#   ./run.sh --project ~/myproject
#
#   # Run a command
#   ./run.sh -- python3 --version
#
#   # Enable Docker-in-Docker
#   ./run.sh --docker
#
#   # Persist caches across sessions
#   ./run.sh --persist-cache
#
#   # Install additional packages
#   ./run.sh --pip flask,sqlalchemy --npm lodash
#   ./run.sh --apt graphviz --pip pydot

set -e

# Source shared library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/container.sh"

# Override image name for dev container
DEV_IMAGE_NAME="${CLAUDE_DEVCONTAINER_IMAGE:-grandcamel/claude-devcontainer}"
DEV_IMAGE_TAG="${CLAUDE_DEVCONTAINER_TAG:-latest}"

# =============================================================================
# Script-specific Configuration
# =============================================================================

PROJECT_PATH=""
USE_API_KEY=false
USE_API_KEY_FROM_CONFIG=false
BUILD_IMAGE=false
MOUNT_DOCKER=false
PERSIST_CACHE=false
PORTS=()
ENV_VARS=()
VOLUMES=()
MODEL=""
CONTAINER_NAME=""
DETACH=false
COMMAND_ARGS=()
PIP_PACKAGES=()
NPM_PACKAGES=()
APT_PACKAGES=()
ENHANCED_MODE=false
CLAUDE_VERSION=""
CUSTOM_IMAGE=""
CUSTOM_TAG=""
PUSH_IMAGE=false
USE_ENHANCED_IMAGE=false

# =============================================================================
# Argument Parsing
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --project|-p)
            PROJECT_PATH="$2"
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
        --docker)
            MOUNT_DOCKER=true
            shift
            ;;
        --persist-cache)
            PERSIST_CACHE=true
            shift
            ;;
        --port|-P)
            PORTS+=("$2")
            shift 2
            ;;
        --env|-e)
            ENV_VARS+=("$2")
            shift 2
            ;;
        --volume|-v)
            VOLUMES+=("$2")
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        --detach|-d)
            DETACH=true
            shift
            ;;
        --pip)
            IFS=',' read -ra pkgs <<< "$2"
            PIP_PACKAGES+=("${pkgs[@]}")
            shift 2
            ;;
        --npm)
            IFS=',' read -ra pkgs <<< "$2"
            NPM_PACKAGES+=("${pkgs[@]}")
            shift 2
            ;;
        --apt)
            IFS=',' read -ra pkgs <<< "$2"
            APT_PACKAGES+=("${pkgs[@]}")
            shift 2
            ;;
        --enhanced)
            ENHANCED_MODE=true
            shift
            ;;
        --claude-version)
            CLAUDE_VERSION="$2"
            shift 2
            ;;
        --image)
            CUSTOM_IMAGE="$2"
            shift 2
            ;;
        --tag)
            CUSTOM_TAG="$2"
            shift 2
            ;;
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        --use-enhanced)
            USE_ENHANCED_IMAGE=true
            shift
            ;;
        --plugin-dir)
            PLUGIN_DIR="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options] [-- command...]"
            echo ""
            echo "Run a batteries-included developer container with Claude Code."
            echo ""
            echo "Included Tools:"
            echo "  Languages:    Python 3, Node.js 20, Go 1.22, Rust (stable)"
            echo "  CLI Tools:    git, jq, yq, ripgrep, fd, fzf, httpie, shellcheck, tree"
            echo "  Cloud:        AWS CLI, GitHub CLI"
            echo "  Databases:    PostgreSQL, MySQL, Redis, SQLite clients"
            echo "  Build:        make, cmake, gcc, pkg-config"
            echo "  Node.js:      TypeScript, ESLint, Prettier, yarn, pnpm"
            echo "  Python:       pytest, black, ruff, mypy, poetry, uv, ipython"
            echo ""
            echo "Options:"
            echo "  --project, -p PATH    Mount project directory (default: current directory)"
            echo "  --docker              Mount Docker socket for Docker-in-Docker"
            echo "  --persist-cache       Persist Go, Cargo, npm caches across sessions"
            echo "  --port, -P PORT       Expose port (can be used multiple times)"
            echo "  --env, -e VAR=VAL     Set environment variable (can be used multiple times)"
            echo "  --volume, -v SRC:DST  Mount additional volume (can be used multiple times)"
            echo "  --name NAME           Container name (for reattaching)"
            echo "  --detach, -d          Run in background"
            echo "  --build               Rebuild Docker image before running"
            echo "  --model NAME          Claude model (sonnet, haiku, opus)"
            echo "  --claude-version VER  Use specific Claude Code version (e.g., 2.0.69)"
            echo "  --plugin-dir PATH     Mount a Claude Code plugin directory"
            echo ""
            echo "Custom Image (for private registries):"
            echo "  --image NAME          Custom image name (e.g., registry.company.com/team/dev)"
            echo "  --tag TAG             Custom image tag (default: latest)"
            echo "  --push                Push image to registry after building (requires --build)"
            echo "  --use-enhanced        Use pre-built enhanced image (instant startup)"
            echo "                        Build with: ./build-enhanced.sh"
            echo ""
            echo "Additional Packages (installed at container start):"
            echo "  --pip PKG[,PKG,...]   Install Python packages (can be used multiple times)"
            echo "  --npm PKG[,PKG,...]   Install npm packages globally (can be used multiple times)"
            echo "  --apt PKG[,PKG,...]   Install system packages via apt (can be used multiple times)"
            echo ""
            echo "Enhanced Mode:"
            echo "  --enhanced            Install enhanced CLI tools at runtime:"
            echo "                        - Starship prompt (fast, customizable)"
            echo "                        - eza (modern ls), bat (cat with highlighting)"
            echo "                        - delta (better git diff), zoxide (smart cd)"
            echo "                        - btop (system monitor), lazygit (git TUI)"
            echo "                        - tmux (configured), neovim + kickstart"
            echo "                        - direnv (per-directory environments)"
            echo ""
            echo "Authentication (choose one):"
            echo "  (default)              Use OAuth from macOS Keychain (free with subscription)"
            echo "  --api-key              Use ANTHROPIC_API_KEY environment variable (paid)"
            echo "  --api-key-from-config  Use primaryApiKey from ~/.claude.json (paid)"
            echo ""
            echo "Examples:"
            echo "  # Interactive shell with current directory"
            echo "  $0"
            echo ""
            echo "  # Mount specific project"
            echo "  $0 --project ~/myproject"
            echo ""
            echo "  # Run a command"
            echo "  $0 -- python3 --version"
            echo ""
            echo "  # Full development setup with Docker and port forwarding"
            echo "  $0 --project ~/app --docker --port 3000:3000 --port 8080:8080"
            echo ""
            echo "  # Persist caches for faster subsequent runs"
            echo "  $0 --persist-cache --project ~/myproject"
            echo ""
            echo "  # Named container (can reattach with: docker exec -it mydev bash)"
            echo "  $0 --name mydev --detach"
            echo ""
            echo "  # Install additional packages"
            echo "  $0 --pip flask,sqlalchemy --npm lodash"
            echo "  $0 --apt graphviz --pip pydot"
            echo ""
            echo "  # Enhanced mode with modern CLI tools"
            echo "  $0 --enhanced"
            echo "  $0 --enhanced --project ~/myproject --persist-cache"
            echo ""
            echo "  # Use specific Claude Code version"
            echo "  $0 --claude-version 2.0.69"
            echo ""
            echo "  # Build and push to private registry"
            echo "  $0 --build --image registry.company.com/team/claude-dev --tag v1.0 --push"
            echo ""
            echo "  # Use image from private registry"
            echo "  $0 --image registry.company.com/team/claude-dev --tag v1.0"
            echo ""
            echo "  # Use pre-built enhanced image (instant startup)"
            echo "  $0 --use-enhanced"
            exit 0
            ;;
        --)
            shift
            COMMAND_ARGS=("$@")
            break
            ;;
        *)
            COMMAND_ARGS+=("$1")
            shift
            ;;
    esac
done

# Default to current directory if no project specified
if [[ -z "$PROJECT_PATH" ]]; then
    PROJECT_PATH="$(pwd)"
fi

# Resolve to absolute path
PROJECT_PATH="$(cd "$PROJECT_PATH" 2>/dev/null && pwd)" || {
    echo_error "Project path does not exist: $PROJECT_PATH"
    exit 1
}

# Apply --use-enhanced (overrides defaults, but custom image/tag take precedence)
if [[ "$USE_ENHANCED_IMAGE" == "true" ]]; then
    DEV_IMAGE_NAME="grandcamel/claude-devcontainer"
    DEV_IMAGE_TAG="enhanced"
fi

# Apply custom image name/tag if specified (takes precedence over --use-enhanced)
if [[ -n "$CUSTOM_IMAGE" ]]; then
    DEV_IMAGE_NAME="$CUSTOM_IMAGE"
fi
if [[ -n "$CUSTOM_TAG" ]]; then
    DEV_IMAGE_TAG="$CUSTOM_TAG"
fi

# Validate --push requires --build
if [[ "$PUSH_IMAGE" == "true" ]] && [[ "$BUILD_IMAGE" != "true" ]]; then
    echo_error "--push requires --build flag"
    exit 1
fi

# =============================================================================
# Image Management
# =============================================================================

build_dev_image() {
    local dockerfile="$PROJECT_ROOT/Dockerfile"

    # Use enhanced Dockerfile if building enhanced image
    if [[ "$USE_ENHANCED_IMAGE" == "true" ]] || [[ "$DEV_IMAGE_NAME" == *"enhanced"* ]] || [[ "$DEV_IMAGE_TAG" == "enhanced" ]]; then
        dockerfile="$PROJECT_ROOT/Dockerfile.enhanced"
    fi

    echo_info "Building developer container image: $DEV_IMAGE_NAME:$DEV_IMAGE_TAG"
    docker build \
        -t "$DEV_IMAGE_NAME:$DEV_IMAGE_TAG" \
        -f "$dockerfile" \
        "$PROJECT_ROOT"
    echo_info "Image built successfully"
}

push_dev_image() {
    echo_info "Pushing image to registry: $DEV_IMAGE_NAME:$DEV_IMAGE_TAG"
    docker push "$DEV_IMAGE_NAME:$DEV_IMAGE_TAG"
    echo_info "Image pushed successfully"
}

check_dev_image() {
    if ! docker image inspect "$DEV_IMAGE_NAME:$DEV_IMAGE_TAG" &>/dev/null; then
        echo_warn "Dev image not found, building (this may take several minutes)..."
        build_dev_image
    fi
}

ensure_dev_image() {
    local force_build="$1"
    local push_after_build="$2"
    if [[ "$force_build" == "true" ]]; then
        build_dev_image
        if [[ "$push_after_build" == "true" ]]; then
            push_dev_image
        fi
    else
        check_dev_image
    fi
}

# =============================================================================
# Main Runner
# =============================================================================

run_devcontainer() {
    local project_name
    project_name=$(basename "$PROJECT_PATH")

    echo_status "DEV" "Project: $project_name"
    echo_status "DEV" "Path: $PROJECT_PATH"

    if [[ "$MOUNT_DOCKER" == "true" ]]; then
        echo_status "DEV" "Docker: enabled (socket mounted)"
    fi

    if [[ "$PERSIST_CACHE" == "true" ]]; then
        echo_status "DEV" "Cache: persistent volumes enabled"
    fi

    if [[ ${#PORTS[@]} -gt 0 ]]; then
        echo_status "DEV" "Ports: ${PORTS[*]}"
    fi

    if [[ ${#PIP_PACKAGES[@]} -gt 0 ]]; then
        echo_status "DEV" "Pip packages: ${PIP_PACKAGES[*]}"
    fi

    if [[ ${#NPM_PACKAGES[@]} -gt 0 ]]; then
        echo_status "DEV" "Npm packages: ${NPM_PACKAGES[*]}"
    fi

    if [[ ${#APT_PACKAGES[@]} -gt 0 ]]; then
        echo_status "DEV" "Apt packages: ${APT_PACKAGES[*]}"
    fi

    if [[ "$USE_ENHANCED_IMAGE" == "true" ]]; then
        echo_status "DEV" "Using pre-built enhanced image (instant startup)"
    elif [[ "$ENHANCED_MODE" == "true" ]]; then
        echo_status "DEV" "Enhanced mode: starship, eza, bat, delta, zoxide, btop, lazygit, tmux, neovim, direnv"
    fi

    if [[ -n "$CLAUDE_VERSION" ]]; then
        echo_status "DEV" "Claude Code version: $CLAUDE_VERSION"
    fi

    if [[ -n "$CUSTOM_IMAGE" ]] || [[ -n "$CUSTOM_TAG" ]]; then
        echo_status "DEV" "Image: $DEV_IMAGE_NAME:$DEV_IMAGE_TAG"
    fi
    echo ""

    echo_info "Starting developer container..."

    # Build docker run command
    local docker_args=("run")

    # Interactive or detached mode
    if [[ "$DETACH" == "true" ]]; then
        docker_args+=("-d")
    elif [[ ${#COMMAND_ARGS[@]} -gt 0 ]]; then
        # Running a command, don't need TTY
        docker_args+=("--rm")
    else
        # Interactive shell
        docker_args+=("-it" "--rm")
    fi

    # Container name
    if [[ -n "$CONTAINER_NAME" ]]; then
        docker_args+=("--name" "$CONTAINER_NAME")
    fi

    # Mount config directory if enhanced mode (for runtime setup)
    if [[ "$ENHANCED_MODE" == "true" ]] && [[ "$USE_ENHANCED_IMAGE" != "true" ]]; then
        docker_args+=("-v" "$PROJECT_ROOT/config:/workspace/config:ro")
    fi

    # Mount project directory
    docker_args+=("-v" "$PROJECT_PATH:/workspace/project")

    # Set working directory to project
    docker_args+=("-w" "/workspace/project")

    # Plugin directory (if specified)
    if [[ -n "$PLUGIN_DIR" ]]; then
        docker_args+=("-v" "$PLUGIN_DIR:/workspace/plugin:ro")
        docker_args+=("-e" "CLAUDE_PLUGIN_DIR=/workspace/plugin")
    fi

    # Authentication configuration
    if [[ "$USE_API_KEY" == "true" ]]; then
        docker_args+=("-e" "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}")
    else
        docker_args+=("-v" "$CREDS_TMP_DIR:/home/devuser/.claude")
    fi

    # Enable host.docker.internal
    docker_args+=("--add-host" "host.docker.internal:host-gateway")

    # Docker socket for Docker-in-Docker
    if [[ "$MOUNT_DOCKER" == "true" ]]; then
        if [[ -S /var/run/docker.sock ]]; then
            docker_args+=("-v" "/var/run/docker.sock:/var/run/docker.sock")
        else
            echo_warn "Docker socket not found at /var/run/docker.sock"
        fi
    fi

    # Persistent cache volumes
    if [[ "$PERSIST_CACHE" == "true" ]]; then
        docker_args+=(
            "-v" "claude-devcontainer-go-cache:/home/devuser/go"
            "-v" "claude-devcontainer-cargo-cache:/usr/local/cargo/registry"
            "-v" "claude-devcontainer-npm-cache:/home/devuser/.npm"
            "-v" "claude-devcontainer-pip-cache:/home/devuser/.cache/pip"
        )
    fi

    # Port forwarding
    for port in "${PORTS[@]}"; do
        docker_args+=("-p" "$port")
    done

    # Additional environment variables
    for env_var in "${ENV_VARS[@]}"; do
        docker_args+=("-e" "$env_var")
    done

    # Additional volumes
    for vol in "${VOLUMES[@]}"; do
        docker_args+=("-v" "$vol")
    done

    # Container-specific environment
    docker_args+=(
        "-e" "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"
        "-e" "CLAUDE_CODE_ACTION=bypassPermissions"
        "-e" "OTLP_HTTP_ENDPOINT=http://host.docker.internal:4318"
        "-e" "TERM=xterm-256color"
    )

    # Model selection
    if [[ -n "$MODEL" ]]; then
        docker_args+=("-e" "$(get_model_env "$MODEL")")
    fi

    # Image name
    docker_args+=("$DEV_IMAGE_NAME:$DEV_IMAGE_TAG")

    # Build initialization commands for package installation
    local init_commands=()

    # Enhanced mode setup (run first for best experience)
    # Skip if using pre-built enhanced image (tools already installed)
    if [[ "$ENHANCED_MODE" == "true" ]] && [[ "$USE_ENHANCED_IMAGE" != "true" ]]; then
        init_commands+=("/workspace/config/setup-enhanced.sh")
    fi

    # Apt packages (requires sudo, run first)
    if [[ ${#APT_PACKAGES[@]} -gt 0 ]]; then
        local apt_list="${APT_PACKAGES[*]}"
        init_commands+=("echo '📦 Installing apt packages: $apt_list'")
        init_commands+=("sudo apt-get update -qq")
        init_commands+=("sudo apt-get install -y -qq ${APT_PACKAGES[*]}")
    fi

    # Pip packages
    if [[ ${#PIP_PACKAGES[@]} -gt 0 ]]; then
        local pip_list="${PIP_PACKAGES[*]}"
        init_commands+=("echo '🐍 Installing pip packages: $pip_list'")
        init_commands+=("pip install -q ${PIP_PACKAGES[*]}")
    fi

    # Npm packages (global install)
    if [[ ${#NPM_PACKAGES[@]} -gt 0 ]]; then
        local npm_list="${NPM_PACKAGES[*]}"
        init_commands+=("echo '📦 Installing npm packages: $npm_list'")
        init_commands+=("npm install -g --silent ${NPM_PACKAGES[*]}")
    fi

    # Claude Code version override
    if [[ -n "$CLAUDE_VERSION" ]]; then
        init_commands+=("echo '🤖 Installing Claude Code v$CLAUDE_VERSION'")
        init_commands+=("sudo npm uninstall -g @anthropic-ai/claude-code 2>/dev/null || true")
        init_commands+=("sudo npm install -g @anthropic-ai/claude-code@$CLAUDE_VERSION")
    fi

    # Command to run (default: interactive bash with login shell)
    if [[ ${#init_commands[@]} -gt 0 ]]; then
        # Has init commands - need to run them first
        local init_script
        init_script=$(IFS=';'; echo "${init_commands[*]}")

        if [[ ${#COMMAND_ARGS[@]} -gt 0 ]]; then
            # Init + user command
            docker_args+=("-c" "$init_script; ${COMMAND_ARGS[*]}")
        else
            # Init + interactive shell
            docker_args+=("-c" "$init_script; exec bash -l")
        fi
    else
        # No init commands
        if [[ ${#COMMAND_ARGS[@]} -gt 0 ]]; then
            # Just user command
            docker_args+=("-c" "${COMMAND_ARGS[*]}")
        else
            # Interactive login shell
            docker_args+=("-l")
        fi
    fi

    # Run container
    echo_info "Running: docker ${docker_args[*]}"
    docker "${docker_args[@]}"
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo "=============================================="
    echo "Claude Dev Container"
    echo "=============================================="
    echo ""
    echo "Batteries included: Python, Node.js, Go, Rust, AWS CLI, GitHub CLI,"
    echo "                    PostgreSQL/MySQL/Redis clients, and more."
    echo ""

    setup_cleanup_trap
    validate_auth "$USE_API_KEY" "$USE_API_KEY_FROM_CONFIG"
    ensure_dev_image "$BUILD_IMAGE" "$PUSH_IMAGE"
    run_devcontainer

    if [[ "$DETACH" != "true" ]]; then
        echo ""
        echo_info "Developer container session ended"
    else
        echo ""
        echo_info "Developer container started in background"
        if [[ -n "$CONTAINER_NAME" ]]; then
            echo_info "Attach with: docker exec -it $CONTAINER_NAME bash"
            echo_info "Stop with:   docker stop $CONTAINER_NAME"
        fi
    fi
}

main "$@"
