#!/usr/bin/env bash
# ==============================================================================
# Version Sync Script
# ==============================================================================
# Synchronizes version numbers across all files that need to stay in sync.
# Source of truth: VERSION file
#
# Usage:
#   ./scripts/sync-version.sh           # Sync all files to VERSION
#   ./scripts/sync-version.sh --check   # Check if files are in sync (exit 1 if not)
#   ./scripts/sync-version.sh --set X.Y.Z  # Set new version and sync all files
#
# Files synced:
#   - VERSION (source of truth)
#   - .claude-plugin/plugin.json
#   - .claude-plugin/marketplace.json
#   - .release-please-manifest.json
#   - pyproject.toml (main project)
#   - jira-assistant-skills-lib/pyproject.toml (if updating lib)
#   - jira-assistant-skills-lib/src/jira_assistant_skills_lib/__init__.py
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Files to sync
VERSION_FILE="$PROJECT_ROOT/VERSION"
PLUGIN_JSON="$PROJECT_ROOT/.claude-plugin/plugin.json"
MARKETPLACE_JSON="$PROJECT_ROOT/.claude-plugin/marketplace.json"
RELEASE_MANIFEST="$PROJECT_ROOT/.release-please-manifest.json"
PYPROJECT="$PROJECT_ROOT/pyproject.toml"
LIB_PYPROJECT="$PROJECT_ROOT/jira-assistant-skills-lib/pyproject.toml"
LIB_INIT="$PROJECT_ROOT/jira-assistant-skills-lib/src/jira_assistant_skills_lib/__init__.py"

# Helper functions
info() { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

get_version_from_file() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        echo ""
        return
    fi

    case "$file" in
        *VERSION)
            cat "$file" | tr -d '[:space:]'
            ;;
        *plugin.json)
            if command -v jq &> /dev/null; then
                jq -r '.version//empty' "$file" 2>/dev/null || echo ""
            else
                grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$file" | \
                    head -1 | sed 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/'
            fi
            ;;
        *marketplace.json)
            if command -v jq &> /dev/null; then
                jq -r '.metadata.version//empty' "$file" 2>/dev/null || echo ""
            else
                grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$file" | \
                    head -1 | sed 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/'
            fi
            ;;
        *.release-please-manifest.json)
            if command -v jq &> /dev/null; then
                jq -r '.["."//empty]' "$file" 2>/dev/null || echo ""
            else
                grep -o '"\\."[[:space:]]*:[[:space:]]*"[^"]*"' "$file" | \
                    head -1 | sed 's/.*"\\.": "\([^"]*\)".*/\1/'
            fi
            ;;
        *pyproject.toml)
            grep '^version' "$file" | head -1 | sed 's/version[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/'
            ;;
        *__init__.py)
            grep '__version__' "$file" | sed 's/__version__[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/'
            ;;
        *)
            echo ""
            ;;
    esac
}

update_version_in_file() {
    local file="$1"
    local new_version="$2"

    if [[ ! -f "$file" ]]; then
        warn "File not found: $file"
        return 1
    fi

    case "$file" in
        *VERSION)
            echo "$new_version" > "$file"
            ;;
        *plugin.json)
            if command -v jq &> /dev/null; then
                local tmp=$(mktemp)
                jq ".version = \"$new_version\"" "$file" > "$tmp" && mv "$tmp" "$file"
            else
                sed -i.bak "s/\"version\"[[:space:]]*:[[:space:]]*\"[^\"]*\"/\"version\": \"$new_version\"/" "$file"
                rm -f "$file.bak"
            fi
            ;;
        *marketplace.json)
            if command -v jq &> /dev/null; then
                local tmp=$(mktemp)
                jq ".metadata.version = \"$new_version\" | .plugins[0].version = \"$new_version\"" "$file" > "$tmp" && mv "$tmp" "$file"
            else
                # Update both version fields (metadata.version and plugins[0].version)
                sed -i.bak "s/\"version\"[[:space:]]*:[[:space:]]*\"[^\"]*\"/\"version\": \"$new_version\"/g" "$file"
                rm -f "$file.bak"
            fi
            ;;
        *.release-please-manifest.json)
            if command -v jq &> /dev/null; then
                local tmp=$(mktemp)
                jq ".[\".\"] = \"$new_version\"" "$file" > "$tmp" && mv "$tmp" "$file"
            else
                sed -i.bak "s/\"\\.\": \"[^\"]*\"/\".\": \"$new_version\"/" "$file"
                rm -f "$file.bak"
            fi
            ;;
        *pyproject.toml)
            sed -i.bak "s/^version[[:space:]]*=[[:space:]]*\"[^\"]*\"/version = \"$new_version\"/" "$file"
            rm -f "$file.bak"
            ;;
        *__init__.py)
            sed -i.bak "s/__version__[[:space:]]*=[[:space:]]*\"[^\"]*\"/__version__ = \"$new_version\"/" "$file"
            rm -f "$file.bak"
            ;;
        *)
            error "Unknown file type: $file"
            return 1
            ;;
    esac

    success "Updated $file to $new_version"
}

check_versions() {
    local source_version
    source_version=$(get_version_from_file "$VERSION_FILE")

    if [[ -z "$source_version" ]]; then
        error "Could not read version from VERSION file"
        return 1
    fi

    info "Source of truth (VERSION): $source_version"
    echo ""

    local all_synced=true
    local files=("$PLUGIN_JSON" "$MARKETPLACE_JSON" "$RELEASE_MANIFEST" "$PYPROJECT")

    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            local file_version
            file_version=$(get_version_from_file "$file")
            local relative_file="${file#$PROJECT_ROOT/}"

            if [[ "$file_version" == "$source_version" ]]; then
                success "$relative_file: $file_version"
            else
                error "$relative_file: $file_version (expected $source_version)"
                all_synced=false
            fi
        fi
    done

    # Check lib separately (has its own version)
    if [[ -f "$LIB_PYPROJECT" ]]; then
        local lib_version
        lib_version=$(get_version_from_file "$LIB_PYPROJECT")
        info "Library version (separate): $lib_version"
    fi

    echo ""
    if $all_synced; then
        success "All versions are in sync!"
        return 0
    else
        error "Version mismatch detected. Run './scripts/sync-version.sh' to fix."
        return 1
    fi
}

sync_versions() {
    local source_version
    source_version=$(get_version_from_file "$VERSION_FILE")

    if [[ -z "$source_version" ]]; then
        error "Could not read version from VERSION file"
        return 1
    fi

    info "Syncing all files to version: $source_version"
    echo ""

    local files=("$PLUGIN_JSON" "$MARKETPLACE_JSON" "$RELEASE_MANIFEST" "$PYPROJECT")

    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            update_version_in_file "$file" "$source_version"
        fi
    done

    echo ""
    success "Version sync complete!"
}

set_version() {
    local new_version="$1"

    # Validate semver format
    if ! [[ "$new_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?(\+[a-zA-Z0-9.]+)?$ ]]; then
        error "Invalid version format: $new_version"
        error "Expected semver format: X.Y.Z[-prerelease][+build]"
        return 1
    fi

    info "Setting version to: $new_version"
    echo ""

    # Update VERSION file first (source of truth)
    update_version_in_file "$VERSION_FILE" "$new_version"

    # Then sync all other files
    sync_versions
}

# Main script
main() {
    case "${1:-sync}" in
        --check|-c)
            check_versions
            ;;
        --set|-s)
            if [[ -z "${2:-}" ]]; then
                error "Usage: $0 --set X.Y.Z"
                exit 1
            fi
            set_version "$2"
            ;;
        sync|--sync)
            sync_versions
            ;;
        --help|-h)
            echo "Usage: $0 [OPTION]"
            echo ""
            echo "Options:"
            echo "  (none), sync    Sync all files to VERSION file"
            echo "  --check, -c     Check if all versions are in sync"
            echo "  --set, -s X.Y.Z Set new version and sync all files"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "Files synchronized:"
            echo "  - VERSION (source of truth)"
            echo "  - .claude-plugin/plugin.json"
            echo "  - .claude-plugin/marketplace.json"
            echo "  - .release-please-manifest.json"
            echo "  - pyproject.toml"
            ;;
        *)
            error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
}

main "$@"
