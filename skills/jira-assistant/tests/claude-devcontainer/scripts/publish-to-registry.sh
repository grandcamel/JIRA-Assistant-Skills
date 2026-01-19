#!/usr/bin/env bash
#
# Publish team container image to a private registry
#
# Handles the complete workflow:
#   1. Authenticate to private registry
#   2. Build image from team config
#   3. Tag with git version (from tag or commit)
#   4. Push to registry
#
# Supports self-hosted registries like Harbor, Nexus, GitLab Registry, etc.
#
# Usage:
#   ./publish-to-registry.sh --config team-config.yaml --registry registry.company.com
#
# Examples:
#   # Publish with username/password (will prompt)
#   ./publish-to-registry.sh --config team-config.yaml --registry harbor.company.com
#
#   # Publish with token (for CI or scripted use)
#   ./publish-to-registry.sh --config team-config.yaml --registry harbor.company.com --token $REGISTRY_TOKEN
#
#   # Publish specific version (overrides git tag)
#   ./publish-to-registry.sh --config team-config.yaml --registry harbor.company.com --version 2.0.0
#
#   # Dry run (shows what would happen)
#   ./publish-to-registry.sh --config team-config.yaml --registry harbor.company.com --dry-run

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
REGISTRY=""
REGISTRY_USER=""
REGISTRY_TOKEN=""
VERSION=""
IMAGE_NAME=""
DRY_RUN=false
NO_CACHE=false
SKIP_LOGIN=false

# =============================================================================
# Argument Parsing
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --config|-c)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --registry|-r)
            REGISTRY="$2"
            shift 2
            ;;
        --user|-u)
            REGISTRY_USER="$2"
            shift 2
            ;;
        --token|-t)
            REGISTRY_TOKEN="$2"
            shift 2
            ;;
        --version|-v)
            VERSION="$2"
            shift 2
            ;;
        --image|-i)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --skip-login)
            SKIP_LOGIN=true
            shift
            ;;
        --help|-h)
            cat << 'EOF'
Usage: publish-to-registry.sh --config <file> --registry <url> [options]

Publish team container image to a private registry.

Required:
  --config, -c FILE     Team configuration file (YAML format)
  --registry, -r URL    Registry URL (e.g., harbor.company.com, nexus.internal:5000)

Authentication:
  --user, -u USER       Registry username (will prompt if not provided)
  --token, -t TOKEN     Registry password/token (will prompt if not provided)
  --skip-login          Skip docker login (if already authenticated)

Versioning:
  --version, -v VER     Override version tag (default: git tag or commit SHA)
  --image, -i NAME      Override image name from config

Options:
  --dry-run             Show what would happen without executing
  --no-cache            Build without Docker cache
  --help, -h            Show this help message

Environment Variables:
  REGISTRY_USER         Default registry username
  REGISTRY_TOKEN        Default registry password/token

Examples:
  # Interactive (prompts for credentials)
  ./publish-to-registry.sh --config team-config.yaml --registry harbor.company.com

  # With credentials
  ./publish-to-registry.sh --config team-config.yaml --registry harbor.company.com \
    --user deployer --token $REGISTRY_TOKEN

  # Specific version
  ./publish-to-registry.sh --config team-config.yaml --registry harbor.company.com \
    --version 2.0.0

  # Dry run
  ./publish-to-registry.sh --config team-config.yaml --registry harbor.company.com --dry-run

Typical Workflow:
  1. Create git tag:     git tag v1.0.0
  2. Publish image:      ./publish-to-registry.sh -c team-config.yaml -r harbor.company.com
  3. Team pulls image:   docker pull harbor.company.com/team/dev:1.0.0
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

# =============================================================================
# Validation
# =============================================================================

if [[ -z "$CONFIG_FILE" ]]; then
    echo_error "Config file is required. Use --config <file>"
    exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo_error "Config file not found: $CONFIG_FILE"
    exit 1
fi

if [[ -z "$REGISTRY" ]]; then
    echo_error "Registry URL is required. Use --registry <url>"
    exit 1
fi

# =============================================================================
# Get Version from Git
# =============================================================================

get_version() {
    if [[ -n "$VERSION" ]]; then
        echo "$VERSION"
        return
    fi

    # Try to get version from git tag
    local git_tag
    git_tag=$(git describe --tags --exact-match 2>/dev/null || true)

    if [[ -n "$git_tag" ]]; then
        # Strip 'v' prefix if present (v1.0.0 -> 1.0.0)
        echo "${git_tag#v}"
        return
    fi

    # Fall back to short commit SHA
    local commit_sha
    commit_sha=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")
    echo "$commit_sha"
}

# =============================================================================
# Parse Config for Image Name
# =============================================================================

get_image_name_from_config() {
    python3 << EOF
import yaml
try:
    with open("$CONFIG_FILE", 'r') as f:
        config = yaml.safe_load(f)
    name = config.get('image', {}).get('name', 'team/dev-container')
    # Extract just the image name without registry prefix
    if '/' in name:
        parts = name.split('/')
        if '.' in parts[0] or ':' in parts[0]:
            # Has registry prefix, remove it
            name = '/'.join(parts[1:])
    print(name)
except Exception as e:
    print('team/dev-container')
EOF
}

# =============================================================================
# Main
# =============================================================================

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}       ${YELLOW}Publish to Private Registry${NC}                            ${CYAN}║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Determine version
PUBLISH_VERSION=$(get_version)

# Determine image name
if [[ -z "$IMAGE_NAME" ]]; then
    IMAGE_NAME=$(get_image_name_from_config)
fi

# Full image reference
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}"

echo_step "Configuration"
echo "  Config:    $CONFIG_FILE"
echo "  Registry:  $REGISTRY"
echo "  Image:     $IMAGE_NAME"
echo "  Version:   $PUBLISH_VERSION"
echo "  Full ref:  ${FULL_IMAGE}:${PUBLISH_VERSION}"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
    echo_warn "DRY RUN - No changes will be made"
    echo ""
fi

# =============================================================================
# Step 1: Authenticate to Registry
# =============================================================================

if [[ "$SKIP_LOGIN" != "true" ]]; then
    echo_step "Authenticating to registry: $REGISTRY"

    # Get credentials from env or prompt
    if [[ -z "$REGISTRY_USER" ]]; then
        REGISTRY_USER="${REGISTRY_USER:-$REGISTRY_USER_ENV}"
        if [[ -z "$REGISTRY_USER" ]]; then
            read -p "  Username: " REGISTRY_USER
        fi
    fi

    if [[ -z "$REGISTRY_TOKEN" ]]; then
        REGISTRY_TOKEN="${REGISTRY_TOKEN:-$REGISTRY_TOKEN_ENV}"
        if [[ -z "$REGISTRY_TOKEN" ]]; then
            read -s -p "  Password/Token: " REGISTRY_TOKEN
            echo ""
        fi
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        echo_info "[DRY RUN] Would run: docker login $REGISTRY -u $REGISTRY_USER"
    else
        echo "$REGISTRY_TOKEN" | docker login "$REGISTRY" -u "$REGISTRY_USER" --password-stdin
        echo_info "Authenticated successfully"
    fi
    echo ""
fi

# =============================================================================
# Step 2: Generate Dockerfile
# =============================================================================

echo_step "Generating Dockerfile from config"

CONFIG_DIR="$(cd "$(dirname "$CONFIG_FILE")" && pwd)"
DOCKERFILE_PATH="$CONFIG_DIR/Dockerfile.team"

if [[ "$DRY_RUN" == "true" ]]; then
    echo_info "[DRY RUN] Would generate: $DOCKERFILE_PATH"
else
    "$SCRIPT_DIR/build-team-image.sh" --config "$CONFIG_FILE" --output Dockerfile.team
fi
echo ""

# =============================================================================
# Step 3: Build Image
# =============================================================================

echo_step "Building image: ${FULL_IMAGE}:${PUBLISH_VERSION}"

BUILD_ARGS=()
if [[ "$NO_CACHE" == "true" ]]; then
    BUILD_ARGS+=("--no-cache")
fi

if [[ "$DRY_RUN" == "true" ]]; then
    echo_info "[DRY RUN] Would run: docker build ${BUILD_ARGS[*]} -t ${FULL_IMAGE}:${PUBLISH_VERSION} -f $DOCKERFILE_PATH $CONFIG_DIR"
else
    docker build \
        "${BUILD_ARGS[@]}" \
        -t "${FULL_IMAGE}:${PUBLISH_VERSION}" \
        -t "${FULL_IMAGE}:latest" \
        -f "$DOCKERFILE_PATH" \
        "$CONFIG_DIR"
    echo_info "Image built successfully"
fi
echo ""

# =============================================================================
# Step 4: Push Image
# =============================================================================

echo_step "Pushing image to registry"

if [[ "$DRY_RUN" == "true" ]]; then
    echo_info "[DRY RUN] Would run: docker push ${FULL_IMAGE}:${PUBLISH_VERSION}"
    echo_info "[DRY RUN] Would run: docker push ${FULL_IMAGE}:latest"
else
    docker push "${FULL_IMAGE}:${PUBLISH_VERSION}"
    docker push "${FULL_IMAGE}:latest"
    echo_info "Image pushed successfully"
fi
echo ""

# =============================================================================
# Summary
# =============================================================================

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}       ${CYAN}Published Successfully!${NC}                                 ${GREEN}║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Image:    ${FULL_IMAGE}:${PUBLISH_VERSION}"
echo "  Latest:   ${FULL_IMAGE}:latest"
echo ""
echo "  Team members can pull with:"
echo "    docker pull ${FULL_IMAGE}:${PUBLISH_VERSION}"
echo ""
echo "  Or use with run.sh:"
echo "    ./scripts/run.sh --image ${FULL_IMAGE} --tag ${PUBLISH_VERSION}"
echo ""
