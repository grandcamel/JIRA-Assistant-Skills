# JIRA Assistant Skills - Quick Setup Guide

Get started with JIRA Assistant Skills in under 5 minutes.

## Prerequisites

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **JIRA Cloud account** - With API token creation permissions
- **Claude Code** - For the full conversational experience

## Quick Start Options

### Option 1: One-Line Install (Recommended)

**macOS / Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/YOUR_ORG/jira-assistant-skills/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
iwr -useb https://raw.githubusercontent.com/YOUR_ORG/jira-assistant-skills/main/install.ps1 | iex
```

### Option 2: Claude Code Slash Command

If you already have the skills installed:
```
/jira-assistant-setup
```

Claude will guide you through the setup conversationally.

### Option 3: Interactive Setup Script

```bash
# Clone the repository
git clone https://github.com/YOUR_ORG/jira-assistant-skills.git
cd jira-assistant-skills

# Run the setup wizard
python setup.py
```

---

## Step-by-Step Guide

### Step 1: Create an API Token

1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)

2. Click **"Create API token"**

3. Enter a label like **"JIRA Assistant Skills"**

4. Click **"Create"**

5. **Copy the token immediately** - you won't be able to see it again!

> **Tip:** Store the token somewhere safe temporarily while you complete setup.

### Step 2: Run the Setup Wizard

The setup wizard will:
- Open your browser to the API token page
- Prompt for your credentials
- Validate the connection
- Store credentials securely in your system keychain

```bash
python setup.py
```

**Example session:**
```
==================================================
 JIRA Assistant Skills - Setup Wizard
==================================================

Checking environment...
  [OK] Python 3.11.0
  [OK] keyring available (macOS Keychain)

Step 1: Get JIRA API Token
--------------------------
Opening browser to: https://id.atlassian.com/manage-profile/security/api-tokens

Press Enter when you have your API token ready...

Step 2: Enter Credentials
-------------------------
Profile name [production]:
JIRA Site URL (e.g., https://company.atlassian.net): https://mycompany.atlassian.net
Email address: user@mycompany.com
API Token: ********

Step 3: Validating Connection
-----------------------------
  [OK] Authenticated as: John Developer
  [OK] Account ID: 5a48ac...

Step 4: Storing Credentials
---------------------------
  [OK] Credentials stored in: macOS Keychain

==================================================
 Setup Complete!
==================================================
```

### Step 3: Verify the Setup

Test with a known issue key:

```bash
python .claude/skills/jira-issue/scripts/get_issue.py PROJ-123
```

Or validate your credentials:

```bash
python setup.py --validate-only
```

---

## Credential Storage Options

Your credentials can be stored in multiple ways:

| Method | Security | Platform | How to Use |
|--------|----------|----------|------------|
| **System Keychain** | Highest | All | Default (automatic) |
| **settings.local.json** | Medium | All | `--json-only` flag |
| **Environment Variables** | Variable | All | `--env-only` flag |

### Priority Order

When looking up credentials, the system checks in this order:

1. **Environment variables** (highest priority)
   - `JIRA_SITE_URL`
   - `JIRA_EMAIL`
   - `JIRA_API_TOKEN` or `JIRA_API_TOKEN_PRODUCTION`

2. **System keychain**
   - macOS: Keychain Access
   - Windows: Credential Manager
   - Linux: GNOME Keyring / KWallet

3. **settings.local.json** (gitignored)
   - Located at `.claude/settings.local.json`

---

## Multiple Profiles

Set up different profiles for different JIRA instances:

```bash
# Set up production profile
python setup.py --profile production

# Set up development profile
python setup.py --profile development

# Use a specific profile
python .claude/skills/jira-issue/scripts/get_issue.py DEV-123 --profile development
```

---

## Setup Options

```bash
python setup.py --help

Options:
  --profile PROFILE     Profile name (default: production)
  --no-browser          Don't open browser for API token page
  --json-only           Store in settings.local.json only
  --env-only            Show environment variable commands
  --validate-only       Validate existing credentials
```

---

## Troubleshooting

### "Authentication failed"

- **Check your email**: Must match your Atlassian account exactly
- **Regenerate the token**: Tokens can't be viewed again after creation
- **Check permissions**: Ensure your account has API access

### "Cannot connect to JIRA"

- **Verify the URL**: Should be `https://yourcompany.atlassian.net`
- **Check network**: Ensure you can access JIRA in your browser
- **Firewall/VPN**: Some networks block API access

### "Keychain not available"

- **macOS**: Open Keychain Access app and unlock it
- **Windows**: Credential Manager should work automatically
- **Linux**: Install and start GNOME Keyring: `sudo apt install gnome-keyring`

Use `--json-only` as a fallback:
```bash
python setup.py --json-only
```

### "Permission denied" on install.sh

```bash
chmod +x install.sh
./install.sh
```

---

## What's Next?

After setup, you can:

1. **Ask Claude naturally:**
   - "Show me my open issues"
   - "What's blocking the release?"
   - "Create a bug for the login crash"

2. **Use scripts directly:**
   ```bash
   python .claude/skills/jira-search/scripts/jql_search.py "assignee = currentUser()"
   ```

3. **Explore the skills:**
   - See [README.md](../../README.md) for the full skill catalog
   - Each skill has its own `SKILL.md` with examples

---

## Need Help?

- **Full documentation**: [README.md](../../README.md)
- **Troubleshooting guide**: [troubleshooting.md](../../.claude/skills/shared/references/troubleshooting.md)
- **Ask Claude**: Just describe what you need!
