#!/bin/bash
# Post-create script for JIRA Assistant Skills Codespace
# This script runs after the container is created

set -e

echo "========================================"
echo "  JIRA Assistant Skills Setup"
echo "========================================"
echo ""

# Install Python dependencies
echo "[1/4] Installing Python dependencies..."
pip install --upgrade pip --quiet
pip install -r .claude/skills/shared/scripts/lib/requirements.txt --quiet
echo "      Done."

# Install development dependencies
echo "[2/4] Installing development tools..."
pip install pytest pytest-cov black ruff --quiet
echo "      Done."

# Verify installation
echo "[3/4] Verifying installation..."
python -c "import requests, tabulate, colorama, tqdm; print('      All dependencies verified.')"

# Check for JIRA credentials
echo "[4/4] Checking JIRA configuration..."
if [ -z "$JIRA_API_TOKEN" ] || [ -z "$JIRA_EMAIL" ] || [ -z "$JIRA_SITE_URL" ]; then
    echo ""
    echo "========================================"
    echo "  JIRA Credentials Not Configured"
    echo "========================================"
    echo ""
    echo "To use JIRA Assistant Skills, configure these secrets in your Codespace:"
    echo ""
    echo "  1. Go to: https://github.com/settings/codespaces"
    echo "  2. Add these secrets (scoped to this repository):"
    echo ""
    echo "     JIRA_SITE_URL    Your JIRA Cloud URL (e.g., https://company.atlassian.net)"
    echo "     JIRA_EMAIL       Your Atlassian account email"
    echo "     JIRA_API_TOKEN   API token from https://id.atlassian.com/manage-profile/security/api-tokens"
    echo ""
    echo "  3. Restart your Codespace to apply the secrets"
    echo ""
    echo "For now, you can explore the skills without a JIRA connection:"
    echo ""
    echo "  # View available scripts"
    echo "  ls .claude/skills/*/scripts/"
    echo ""
    echo "  # Read skill documentation"
    echo "  cat .claude/skills/jira-issue/SKILL.md"
    echo ""
    echo "  # View script help"
    echo "  python .claude/skills/jira-issue/scripts/get_issue.py --help"
    echo ""
else
    echo "      JIRA credentials configured."
    echo ""
    echo "========================================"
    echo "  Ready to Use!"
    echo "========================================"
    echo ""
    echo "  Try these commands:"
    echo ""
    echo "    # Search for issues"
    echo "    python .claude/skills/jira-search/scripts/jql_search.py \"project = YOUR_PROJECT\""
    echo ""
    echo "    # Get issue details"
    echo "    python .claude/skills/jira-issue/scripts/get_issue.py PROJ-123"
    echo ""
    echo "    # View all skills"
    echo "    ls .claude/skills/"
    echo ""
fi

echo "========================================"
echo ""
