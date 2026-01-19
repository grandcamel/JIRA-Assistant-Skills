#!/usr/bin/env bash
#
# Build a customized team container image
#
# Generates a Dockerfile from a team configuration file, adding:
#   - Corporate CA certificates (e.g., Zscaler)
#   - Team-specific pip, npm, and apt packages
#   - Custom environment variables and labels
#
# The generated Dockerfile.team can be committed to version control
# for reproducible builds across your team.
#
# Usage:
#   ./build-team-image.sh --config team-config.yaml [options]
#
# Examples:
#   # Generate Dockerfile only (for review/commit)
#   ./build-team-image.sh --config team-config.yaml
#
#   # Generate and build immediately
#   ./build-team-image.sh --config team-config.yaml --build
#
#   # Build and push to registry
#   ./build-team-image.sh --config team-config.yaml --build --push
#
#   # Override output Dockerfile name
#   ./build-team-image.sh --config team-config.yaml --output Dockerfile.myteam

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

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }
echo_step() { echo -e "${BLUE}==>${NC} ${CYAN}$1${NC}"; }

# =============================================================================
# Configuration
# =============================================================================

CONFIG_FILE=""
OUTPUT_FILE="Dockerfile.team"
BUILD_IMAGE=false
PUSH_IMAGE=false
NO_CACHE=false

# =============================================================================
# Argument Parsing
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --config|-c)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --output|-o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --build|-b)
            BUILD_IMAGE=true
            shift
            ;;
        --push)
            PUSH_IMAGE=true
            BUILD_IMAGE=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --help|-h)
            cat << 'EOF'
Usage: build-team-image.sh --config <file> [options]

Generate a customized Dockerfile for your team's developer container.

Required:
  --config, -c FILE    Team configuration file (YAML format)

Options:
  --output, -o FILE    Output Dockerfile name (default: Dockerfile.team)
  --build, -b          Build the image after generating Dockerfile
  --push               Push image to registry after building (implies --build)
  --no-cache           Build without Docker cache
  --help, -h           Show this help message

Configuration File Format (YAML):
  image:
    base: grandcamel/claude-devcontainer:enhanced
    name: my-company/dev-container
    tag: latest

  certificate:
    file: zscaler.crt
    description: "Corporate proxy certificate"

  pip:
    - flask
    - requests

  npm:
    - typescript

  apt:
    - graphviz

  environment:
    TEAM_NAME: "My Team"

  labels:
    maintainer: "team@company.com"

Examples:
  # Generate Dockerfile for review
  ./build-team-image.sh --config team-config.yaml

  # Generate and build
  ./build-team-image.sh --config team-config.yaml --build

  # Build and push to registry
  ./build-team-image.sh --config team-config.yaml --build --push

See examples/team-config.yaml for a complete configuration template.
EOF
            exit 0
            ;;
        *)
            echo_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$CONFIG_FILE" ]]; then
    echo_error "Config file is required. Use --config <file>"
    echo "Use --help for usage information"
    exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo_error "Config file not found: $CONFIG_FILE"
    exit 1
fi

# =============================================================================
# YAML Parser (uses Python for portability)
# =============================================================================

parse_yaml() {
    local config_file="$1"
    python3 << EOF
import yaml
import sys
import os

config_file = "$config_file"

try:
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
except Exception as e:
    print(f"Error parsing config: {e}", file=sys.stderr)
    sys.exit(1)

# Helper to get nested values with defaults
def get(d, *keys, default=''):
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, {})
        else:
            return default
    return d if d else default

# Output as shell-friendly format (properly quoted)
import shlex
def quote(v):
    return shlex.quote(str(v)) if v else "''"

print(f"BASE_IMAGE={quote(get(config, 'image', 'base', default='grandcamel/claude-devcontainer:enhanced'))}")
print(f"IMAGE_NAME={quote(get(config, 'image', 'name', default='team/dev-container'))}")
print(f"IMAGE_TAG={quote(get(config, 'image', 'tag', default='latest'))}")
print(f"CERT_FILE={quote(get(config, 'certificate', 'file', default=''))}")
print(f"CERT_DESC={quote(get(config, 'certificate', 'description', default='Corporate CA certificate'))}")

# Lists as space-separated (quoted)
pip_pkgs = get(config, 'pip', default=[])
npm_pkgs = get(config, 'npm', default=[])
apt_pkgs = get(config, 'apt', default=[])
empty = "''"
print(f"PIP_PACKAGES={quote(' '.join(pip_pkgs)) if isinstance(pip_pkgs, list) and pip_pkgs else empty}")
print(f"NPM_PACKAGES={quote(' '.join(npm_pkgs)) if isinstance(npm_pkgs, list) and npm_pkgs else empty}")
print(f"APT_PACKAGES={quote(' '.join(apt_pkgs)) if isinstance(apt_pkgs, list) and apt_pkgs else empty}")

# Environment variables as KEY=VALUE pairs (quoted)
env_vars = get(config, 'environment', default={})
if isinstance(env_vars, dict):
    for k, v in env_vars.items():
        print(f"ENV_{k}={quote(v)}")

# Labels as KEY=VALUE pairs (quoted)
labels = get(config, 'labels', default={})
if isinstance(labels, dict):
    for k, v in labels.items():
        print(f"LABEL_{k}={quote(v)}")
EOF
}

# =============================================================================
# Main
# =============================================================================

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}       ${YELLOW}Team Container Image Builder${NC}                          ${CYAN}║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo_step "Parsing configuration: $CONFIG_FILE"

# Parse config into shell variables
eval "$(parse_yaml "$CONFIG_FILE")"

# Get config directory for relative paths
CONFIG_DIR="$(cd "$(dirname "$CONFIG_FILE")" && pwd)"

echo "  Base image:   $BASE_IMAGE"
echo "  Output image: $IMAGE_NAME:$IMAGE_TAG"
echo "  Certificate:  ${CERT_FILE:-none}"
echo "  Pip packages: ${PIP_PACKAGES:-none}"
echo "  Npm packages: ${NPM_PACKAGES:-none}"
echo "  Apt packages: ${APT_PACKAGES:-none}"
echo ""

# =============================================================================
# Generate Dockerfile
# =============================================================================

echo_step "Generating $OUTPUT_FILE"

# Resolve output path relative to config file location
OUTPUT_PATH="$CONFIG_DIR/$OUTPUT_FILE"

cat > "$OUTPUT_PATH" << DOCKERFILE_HEADER
# =============================================================================
# Team Developer Container
# =============================================================================
# Generated by: build-team-image.sh
# Config file:  $(basename "$CONFIG_FILE")
# Generated at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
#
# Build with:
#   docker build -t $IMAGE_NAME:$IMAGE_TAG -f $OUTPUT_FILE .
#
# Or use the build script:
#   ./scripts/build-team-image.sh --config $(basename "$CONFIG_FILE") --build
# =============================================================================

FROM $BASE_IMAGE

# Switch to root for package installation
USER root

DOCKERFILE_HEADER

# Add certificate if specified
if [[ -n "$CERT_FILE" ]]; then
    CERT_PATH="$CONFIG_DIR/$CERT_FILE"
    if [[ -f "$CERT_PATH" ]]; then
        echo_info "Including certificate: $CERT_FILE"
        cat >> "$OUTPUT_PATH" << DOCKERFILE_CERT
# =============================================================================
# Corporate CA Certificate ($CERT_DESC)
# =============================================================================
COPY $CERT_FILE /usr/local/share/ca-certificates/corporate-ca.crt
RUN update-ca-certificates

# Configure certificate for common tools
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

DOCKERFILE_CERT
    else
        echo_warn "Certificate file not found: $CERT_PATH (skipping)"
    fi
fi

# Add apt packages
if [[ -n "$APT_PACKAGES" ]]; then
    echo_info "Adding apt packages: $APT_PACKAGES"
    cat >> "$OUTPUT_PATH" << DOCKERFILE_APT
# =============================================================================
# System Packages (apt)
# =============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \\
    $APT_PACKAGES \\
    && rm -rf /var/lib/apt/lists/*

DOCKERFILE_APT
fi

# Add pip packages
if [[ -n "$PIP_PACKAGES" ]]; then
    echo_info "Adding pip packages: $PIP_PACKAGES"
    cat >> "$OUTPUT_PATH" << DOCKERFILE_PIP
# =============================================================================
# Python Packages (pip)
# =============================================================================
RUN pip3 install --no-cache-dir --break-system-packages \\
    $PIP_PACKAGES

DOCKERFILE_PIP
fi

# Add npm packages
if [[ -n "$NPM_PACKAGES" ]]; then
    echo_info "Adding npm packages: $NPM_PACKAGES"
    cat >> "$OUTPUT_PATH" << DOCKERFILE_NPM
# =============================================================================
# Node.js Packages (npm global)
# =============================================================================
RUN npm install -g \\
    $NPM_PACKAGES

DOCKERFILE_NPM
fi

# Add environment variables
ENV_VARS=$(set | grep "^ENV_" | sed 's/^ENV_//' || true)
if [[ -n "$ENV_VARS" ]]; then
    echo_info "Adding environment variables"
    echo "" >> "$OUTPUT_PATH"
    echo "# =============================================================================" >> "$OUTPUT_PATH"
    echo "# Team Environment Variables" >> "$OUTPUT_PATH"
    echo "# =============================================================================" >> "$OUTPUT_PATH"
    while IFS='=' read -r key value; do
        # Strip outer quotes added by shlex.quote
        value="${value#\'}"
        value="${value%\'}"
        echo "ENV $key=\"$value\"" >> "$OUTPUT_PATH"
    done <<< "$ENV_VARS"
fi

# Add labels
LABELS=$(set | grep "^LABEL_" | sed 's/^LABEL_//' || true)
if [[ -n "$LABELS" ]]; then
    echo "" >> "$OUTPUT_PATH"
    echo "# =============================================================================" >> "$OUTPUT_PATH"
    echo "# Image Labels" >> "$OUTPUT_PATH"
    echo "# =============================================================================" >> "$OUTPUT_PATH"
    while IFS='=' read -r key value; do
        # Strip outer quotes added by shlex.quote
        value="${value#\'}"
        value="${value%\'}"
        echo "LABEL $key=\"$value\"" >> "$OUTPUT_PATH"
    done <<< "$LABELS"
fi

# Switch back to non-root user
cat >> "$OUTPUT_PATH" << 'DOCKERFILE_FOOTER'

# =============================================================================
# Final Configuration
# =============================================================================
# Switch back to non-root user
USER devuser
WORKDIR /workspace

# Default to interactive bash
ENTRYPOINT ["/bin/bash"]
CMD ["-l"]
DOCKERFILE_FOOTER

echo_info "Generated: $OUTPUT_PATH"

# =============================================================================
# Build Image (optional)
# =============================================================================

if [[ "$BUILD_IMAGE" == "true" ]]; then
    echo ""
    echo_step "Building image: $IMAGE_NAME:$IMAGE_TAG"

    BUILD_ARGS=()
    if [[ "$NO_CACHE" == "true" ]]; then
        BUILD_ARGS+=("--no-cache")
    fi

    docker build \
        "${BUILD_ARGS[@]}" \
        -t "$IMAGE_NAME:$IMAGE_TAG" \
        -f "$OUTPUT_PATH" \
        "$CONFIG_DIR"

    echo_info "Image built: $IMAGE_NAME:$IMAGE_TAG"

    # Push if requested
    if [[ "$PUSH_IMAGE" == "true" ]]; then
        echo ""
        echo_step "Pushing image to registry"
        docker push "$IMAGE_NAME:$IMAGE_TAG"
        echo_info "Image pushed: $IMAGE_NAME:$IMAGE_TAG"
    fi
fi

# =============================================================================
# Summary
# =============================================================================

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}       ${CYAN}Complete!${NC}                                               ${GREEN}║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Generated:  $OUTPUT_PATH"
echo ""
echo "  Next steps:"
echo "    1. Review the generated Dockerfile"
echo "    2. Commit to version control"
echo "    3. Build with: docker build -t $IMAGE_NAME:$IMAGE_TAG -f $OUTPUT_FILE ."
if [[ "$BUILD_IMAGE" != "true" ]]; then
    echo ""
    echo "  Or build now with:"
    echo "    $0 --config $(basename "$CONFIG_FILE") --build"
fi
echo ""
