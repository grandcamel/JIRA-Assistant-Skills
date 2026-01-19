#!/usr/bin/env bash
#
# Build the enhanced developer container image
#
# Creates a pre-built image with all enhanced CLI tools installed,
# eliminating runtime setup time. Ideal for teams that want instant
# container startup with full tooling.
#
# Usage:
#   ./build-enhanced.sh [options]
#
# Examples:
#   # Build with default name (grandcamel/claude-devcontainer:enhanced)
#   ./build-enhanced.sh
#
#   # Build with custom name for private registry
#   ./build-enhanced.sh --image registry.company.com/team/dev-enhanced --tag v1.0
#
#   # Build and push to registry
#   ./build-enhanced.sh --image registry.company.com/team/dev-enhanced --tag v1.0 --push
#
#   # Build with corporate CA certificate (e.g., Zscaler)
#   ./build-enhanced.sh --ca-cert zscaler.crt

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# =============================================================================
# Colors and Output Helpers
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo_step() {
    echo -e "${BLUE}==>${NC} ${CYAN}$1${NC}"
}

# =============================================================================
# Configuration
# =============================================================================

IMAGE_NAME="grandcamel/claude-devcontainer"
IMAGE_TAG="enhanced"
PUSH_IMAGE=false
CA_CERT=""
NO_CACHE=false

# =============================================================================
# Argument Parsing
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        --ca-cert)
            CA_CERT="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Build the enhanced developer container with pre-installed tools."
            echo ""
            echo "Pre-installed Tools:"
            echo "  - Starship prompt (fast, customizable)"
            echo "  - eza (modern ls), bat (cat with highlighting)"
            echo "  - delta (better git diff), zoxide (smart cd)"
            echo "  - btop (system monitor), lazygit (git TUI)"
            echo "  - tmux (configured), neovim + kickstart"
            echo "  - direnv (per-directory environments)"
            echo ""
            echo "Options:"
            echo "  --image NAME    Image name (default: grandcamel/claude-devcontainer)"
            echo "  --tag TAG       Image tag (default: enhanced)"
            echo "  --push          Push image to registry after building"
            echo "  --ca-cert FILE  Corporate CA certificate (e.g., zscaler.crt)"
            echo "  --no-cache      Build without Docker cache"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "Examples:"
            echo "  # Build with default name"
            echo "  $0"
            echo ""
            echo "  # Build for private registry"
            echo "  $0 --image registry.company.com/team/dev-enhanced --tag v1.0"
            echo ""
            echo "  # Build and push"
            echo "  $0 --image registry.company.com/team/dev-enhanced --tag v1.0 --push"
            echo ""
            echo "  # Build with Zscaler certificate"
            echo "  $0 --ca-cert zscaler.crt"
            echo ""
            echo "After building, use the image with:"
            echo "  ./run.sh --use-enhanced"
            echo "  ./run.sh --image $IMAGE_NAME --tag $IMAGE_TAG"
            exit 0
            ;;
        *)
            echo_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# =============================================================================
# Main Build
# =============================================================================

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}       ${YELLOW}Enhanced Developer Container Build${NC}                    ${CYAN}║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo_step "Configuration"
echo "  Image:     $IMAGE_NAME:$IMAGE_TAG"
echo "  Push:      $PUSH_IMAGE"
echo "  CA Cert:   ${CA_CERT:-none}"
echo "  No Cache:  $NO_CACHE"
echo ""

# Build arguments
BUILD_ARGS=()

if [[ -n "$CA_CERT" ]]; then
    if [[ ! -f "$PROJECT_ROOT/$CA_CERT" ]]; then
        echo_error "CA certificate not found: $PROJECT_ROOT/$CA_CERT"
        exit 1
    fi
    BUILD_ARGS+=("--build-arg" "EXTRA_CA_CERT=$CA_CERT")
    echo_info "Using CA certificate: $CA_CERT"
fi

if [[ "$NO_CACHE" == "true" ]]; then
    BUILD_ARGS+=("--no-cache")
fi

# Build the image
echo_step "Building enhanced image (this may take 10-15 minutes)..."
echo ""

docker build \
    "${BUILD_ARGS[@]}" \
    -t "$IMAGE_NAME:$IMAGE_TAG" \
    -f "$PROJECT_ROOT/Dockerfile.enhanced" \
    "$PROJECT_ROOT"

echo ""
echo_info "Image built successfully: $IMAGE_NAME:$IMAGE_TAG"

# Push if requested
if [[ "$PUSH_IMAGE" == "true" ]]; then
    echo ""
    echo_step "Pushing image to registry..."
    docker push "$IMAGE_NAME:$IMAGE_TAG"
    echo_info "Image pushed successfully"
fi

# Summary
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}       ${CYAN}Build Complete!${NC}                                        ${GREEN}║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Image: $IMAGE_NAME:$IMAGE_TAG"
echo ""
echo "  Usage:"
echo "    ./scripts/run.sh --use-enhanced"
echo "    ./scripts/run.sh --image $IMAGE_NAME --tag $IMAGE_TAG"
echo ""
echo "  Pre-installed tools:"
echo "    starship, eza, bat, delta, zoxide, btop, lazygit, tmux, neovim, direnv"
echo ""
