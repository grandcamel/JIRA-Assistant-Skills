# Quick Start Guide

Get up and running with JIRA Assistant Skills in 5 minutes.

---

## Prerequisites

- **Python 3.8+** — Check with `python --version`
- **Claude Code** — The Anthropic CLI tool
- **JIRA Cloud account** — With API token permissions

---

## Step 1: Install Dependencies

```bash
pip install -r .claude/skills/shared/scripts/lib/requirements.txt
```

This installs:
- `requests` — HTTP client
- `tabulate` — Table formatting
- `colorama` — Colored terminal output
- `python-dotenv` — Environment variable management

---

## Step 2: Get Your API Token

1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Give it a name (e.g., "Claude Code")
4. Copy the token — you won't see it again!

---

## Step 3: Configure Credentials

### Option A: Environment Variables (Recommended)

```bash
export JIRA_API_TOKEN="your-api-token"
export JIRA_EMAIL="your@email.com"
export JIRA_SITE_URL="https://your-company.atlassian.net"
```

Add these to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) to persist them.

### Option B: Settings File

Create `.claude/settings.local.json` (gitignored):

```json
{
  "jira": {
    "default_profile": "production",
    "profiles": {
      "production": {
        "url": "https://your-company.atlassian.net",
        "email": "your@email.com",
        "api_token": "your-api-token",
        "project_keys": ["PROJ", "TEAM"],
        "default_project": "PROJ"
      }
    }
  }
}
```

---

## Step 4: Verify Connection

```bash
# Test with a known issue key
python .claude/skills/jira-issue/scripts/get_issue.py PROJ-123
```

You should see issue details. If not, check [Troubleshooting](troubleshooting.md).

---

## Step 5: Start Using

Now just talk to Claude:

```bash
# In your terminal with Claude Code
claude "Show me my open issues"
claude "Create a bug: Login button broken"
claude "What's blocking the release?"
```

---

## Multi-Environment Setup

For dev/staging/prod environments, see [Configuration Guide](configuration.md).

---

## Next Steps

- [Scripts Reference](scripts-reference.md) — All available commands
- [Configuration Guide](configuration.md) — Advanced setup
- [Troubleshooting](troubleshooting.md) — Common issues
