#!/bin/bash
# Post-create script for JIRA Assistant Skills Sandbox
# This script runs after the container is created

set -e

SKILLS_PATH="skills"

echo "========================================"
echo "  JIRA Assistant Skills Sandbox Setup"
echo "========================================"
echo ""

# Install development dependencies
echo "[1/4] Installing development tools..."
pip3 install --break-system-packages pytest pytest-cov black ruff --quiet 2>/dev/null || \
pip3 install pytest pytest-cov black ruff --quiet
echo "      Done."

# Verify installation
echo "[2/4] Verifying Python dependencies..."
python3 -c "import requests, tabulate, colorama, tqdm; print('      All dependencies verified.')"

# Install Claude Code plugin
echo "[3/4] Installing JIRA Assistant Skills plugin..."
if command -v claude &> /dev/null; then
    claude plugin install ./. 2>/dev/null || echo "      Plugin install skipped (may already be installed)"
    echo "      Done."
else
    echo "      Claude Code not found, skipping plugin install."
fi

# Check for JIRA credentials
echo "[4/4] Checking JIRA configuration..."
if [ -z "$JIRA_API_TOKEN" ] || [ -z "$JIRA_EMAIL" ] || [ -z "$JIRA_SITE_URL" ]; then
    echo ""
    echo "========================================"
    echo "  JIRA Credentials Not Configured"
    echo "========================================"
    echo ""
    echo "To use JIRA Assistant Skills, configure these environment variables:"
    echo ""
    echo "  Option A: Codespace Secrets (https://github.com/settings/codespaces)"
    echo "  Option B: Export in terminal:"
    echo ""
    echo "     export JIRA_SITE_URL=\"https://company.atlassian.net\""
    echo "     export JIRA_EMAIL=\"you@company.com\""
    echo "     export JIRA_API_TOKEN=\"your-token\""
    echo ""
    echo "  Get your API token: https://id.atlassian.com/manage-profile/security/api-tokens"
    echo ""
    echo "For now, you can explore the skills without a JIRA connection:"
    echo ""
    echo "  # View available scripts"
    echo "  ls $SKILLS_PATH/*/scripts/"
    echo ""
    echo "  # Read skill documentation"
    echo "  cat $SKILLS_PATH/jira-issue/SKILL.md"
    echo ""
    echo "  # View script help"
    echo "  python3 $SKILLS_PATH/jira-issue/scripts/get_issue.py --help"
    echo ""
    echo "  # Ask Claude about JIRA"
    echo "  claude \"What JIRA skills are available?\""
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
    echo "    # Use Claude with natural language"
    echo "    claude \"Show my open JIRA issues\""
    echo "    claude \"Create a bug: Login button broken\""
    echo ""
    echo "    # Or use scripts directly"
    echo "    python3 $SKILLS_PATH/jira-search/scripts/jql_search.py \"assignee = currentUser()\""
    echo "    python3 $SKILLS_PATH/jira-issue/scripts/get_issue.py PROJ-123"
    echo ""
    echo "    # Run Claude in dangerously-skip-permissions mode (sandbox is secure)"
    echo "    claude --dangerously-skip-permissions"
    echo ""
fi

echo "========================================"
echo "  Sandbox Security Active"
echo "========================================"
echo ""
echo "  This container has firewall restrictions."
echo "  Only whitelisted domains are accessible:"
echo "    - GitHub, npm, Claude API"
echo "    - Atlassian/JIRA Cloud"
echo "    - VS Code marketplace"
echo ""
echo "  You can safely use: claude --dangerously-skip-permissions"
echo ""
