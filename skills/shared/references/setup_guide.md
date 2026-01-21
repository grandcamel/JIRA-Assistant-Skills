# JIRA Assistant Skills - Setup Guide

Complete setup guide for getting started with JIRA Assistant Skills.

## Quick Start (Recommended)

The fastest way to get started:

### Option 1: One-Line Install

**macOS / Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/YOUR_ORG/jira-assistant-skills/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
iwr -useb https://raw.githubusercontent.com/YOUR_ORG/jira-assistant-skills/main/install.ps1 | iex
```

### Option 2: Interactive Setup Wizard

```bash
python setup.py
```

This wizard will:
1. Check your Python version
2. Install dependencies
3. Open the browser for API token creation
4. Prompt for your credentials
5. Validate the connection
6. Store credentials securely in your system keychain

### Option 3: Claude Code Slash Command

```
/jira-assistant-setup
```

Claude will guide you through the setup conversationally.

---

## Manual Setup

If you prefer manual configuration, follow these steps:

### Prerequisites

- Python 3.8 or higher
- JIRA Cloud or JIRA Service Management instance
- JIRA account with appropriate permissions

### Step 1: Install Dependencies

```bash
pip install jira-as
```

This installs all required dependencies including requests, tabulate, colorama, and python-dotenv.

### Step 2: Get JIRA API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "Claude Code Skills")
4. Copy the token (you won't see it again!)

## Step 3: Configure Environment Variables

Set these environment variables in your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export JIRA_SITE_URL="https://your-company.atlassian.net"
export JIRA_EMAIL="your-email@company.com"
export JIRA_API_TOKEN="your-api-token-here"
```

Or create a `.env` file:

```
JIRA_SITE_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token-here
```

## Step 4: Test Your Setup

```bash
# Test getting an existing issue
python get_issue.py PROJ-123

# Test searching
python jql_search.py "project = PROJ"
```

If these work, you're all set!

## Credential Storage Options

Credentials can be stored in multiple ways (checked in this order):

| Method | Security | Platform | Command |
|--------|----------|----------|---------|
| Environment variables | Variable | All | `export JIRA_API_TOKEN=...` |
| System keychain | Highest | All | `python setup.py` (default) |
| settings.local.json | Medium | All | `python setup.py --json-only` |

### System Keychain (Recommended)

The setup wizard stores credentials in your system keychain by default:
- **macOS**: Keychain Access
- **Windows**: Credential Manager
- **Linux**: GNOME Keyring / KWallet

### Environment Variables

Set these environment variables:
```bash
export JIRA_API_TOKEN="your-token"
export JIRA_EMAIL="your-email@company.com"
export JIRA_SITE_URL="https://company.atlassian.net"
```

For profile-specific tokens:
```bash
export JIRA_API_TOKEN_PRODUCTION="prod-token"
export JIRA_API_TOKEN_DEVELOPMENT="dev-token"
```

## Configuration Priority

Settings are checked in this order (first found wins):

1. Environment variables (highest priority)
2. System keychain
3. Hardcoded defaults

## Multiple Profiles

You can configure multiple JIRA instances:

```json
{
  "jira": {
    "default_profile": "dev",
    "profiles": {
      "dev": {
        "url": "https://company-dev.atlassian.net",
        "default_project": "DEV"
      },
      "staging": {
        "url": "https://company-staging.atlassian.net",
        "default_project": "STAGE"
      },
      "production": {
        "url": "https://company.atlassian.net",
        "default_project": "PROD"
      }
    }
  }
}
```

Use profiles:

```bash
# Use default profile
python get_issue.py PROJ-123

# Use specific profile
python get_issue.py PROJ-123 --profile production

# Override default via environment
export JIRA_PROFILE=staging
python get_issue.py STAGE-456
```

## Permissions Required

Minimum JIRA permissions needed:

- **Browse Projects** - View issues
- **Create Issues** - Create issues
- **Edit Issues** - Update issues
- **Delete Issues** - Delete issues (optional)
- **Add Comments** - Comment on issues
- **Transition Issues** - Change issue status
- **Assign Issues** - Assign issues

Check with your JIRA administrator if you don't have required permissions.

## Troubleshooting

See `troubleshooting.md` for common issues and solutions.

## Next Steps

- Read skill-specific SKILL.md files for usage examples
- Check `references/` directories for detailed API documentation
- Explore JQL templates in `jira-search/assets/templates/`
- Review issue templates in `jira-issue/assets/templates/`
