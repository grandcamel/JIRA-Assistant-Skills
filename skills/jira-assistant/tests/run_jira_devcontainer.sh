#!/usr/bin/env bash
#
# Run the JIRA Skills developer container
#
# This is a thin wrapper around claude-devcontainer with JIRA-specific defaults:
#   - Mounts the JIRA plugin directory
#   - Sets JIRA-optimized environment variables
#
# Usage:
#   ./run_jira_devcontainer.sh [options] [-- command...]
#
# Examples:
#   # Interactive shell
#   ./run_jira_devcontainer.sh
#
#   # With enhanced tools (starship, eza, bat, etc.)
#   ./run_jira_devcontainer.sh --enhanced
#
#   # Use pre-built enhanced image
#   ./run_jira_devcontainer.sh --use-enhanced
#
# For all options, see: ./claude-devcontainer/scripts/run.sh --help
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUBMODULE_DIR="$SCRIPT_DIR/claude-devcontainer"

# Verify submodule is initialized
if [[ ! -f "$SUBMODULE_DIR/scripts/run.sh" ]]; then
    echo "Error: claude-devcontainer submodule not initialized"
    echo "Run: git submodule update --init --recursive"
    exit 1
fi

# Set JIRA-specific defaults via environment variables
export CLAUDE_DEVCONTAINER_IMAGE="${CLAUDE_DEVCONTAINER_IMAGE:-jira-skills-dev}"
export CLAUDE_DEVCONTAINER_TAG="${CLAUDE_DEVCONTAINER_TAG:-latest}"

# Auto-set plugin directory to the JIRA plugin root
JIRA_PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
export CLAUDE_PLUGIN_DIR="${CLAUDE_PLUGIN_DIR:-$JIRA_PLUGIN_ROOT}"

# Delegate to the submodule's run script
exec "$SUBMODULE_DIR/scripts/run.sh" "$@"
