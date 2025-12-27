---
name: jira-assistant-setup
description: Set up JIRA Assistant Skills with credentials and configuration
---

# JIRA Assistant Setup

You are helping the user set up JIRA Assistant Skills. Guide them through the process conversationally.

## Step 1: Check Prerequisites

First, verify the environment:

```bash
python3 --version
```

Check if dependencies are installed:
```bash
pip show requests keyring 2>/dev/null && echo "Core dependencies installed" || echo "Dependencies missing"
```

If dependencies are missing, install them:
```bash
pip install -r .claude/skills/shared/scripts/lib/requirements.txt
```

## Step 2: Get API Token

Tell the user they need an API token from Atlassian. Offer to open the browser:

"To connect to JIRA, you'll need an API token from Atlassian. I can open the page where you can create one.

Would you like me to open https://id.atlassian.com/manage-profile/security/api-tokens ?"

If they agree, use:
```bash
python3 -c "import webbrowser; webbrowser.open('https://id.atlassian.com/manage-profile/security/api-tokens')"
```

Guide them:
1. Click "Create API token"
2. Name it "JIRA Assistant Skills" or similar
3. Copy the token immediately (they won't see it again)

## Step 3: Collect Credentials

Ask the user for their JIRA credentials:

1. **JIRA Site URL**: Ask "What is your JIRA site URL? It should look like https://yourcompany.atlassian.net"

2. **Email**: Ask "What email address do you use to log into JIRA?"

3. **API Token**: Ask "Please paste your API token (I'll store it securely)"

4. **Profile Name**: Ask "What would you like to name this profile? (default: production)"

## Step 4: Run Setup

Once you have the credentials, run the setup script:

```bash
python3 setup.py --profile {profile_name}
```

Or if they want to do it manually, guide them to set environment variables:

For bash/zsh:
```bash
export JIRA_SITE_URL="https://company.atlassian.net"
export JIRA_EMAIL="user@company.com"
export JIRA_API_TOKEN="their-token-here"
```

For PowerShell:
```powershell
$env:JIRA_SITE_URL="https://company.atlassian.net"
$env:JIRA_EMAIL="user@company.com"
$env:JIRA_API_TOKEN="their-token-here"
```

## Step 5: Validate

Test the connection:

```bash
python3 .claude/skills/jira-issue/scripts/get_issue.py {any_issue_key} --profile {profile}
```

Or use the credential manager directly:
```bash
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.claude/skills/shared/scripts/lib')))
from credential_manager import validate_credentials
result = validate_credentials('{url}', '{email}', '{token}')
print(f\"Connected as: {result.get('displayName', 'Unknown')}\")
"
```

## Step 6: Confirm Success

If validation succeeds, tell the user:

"Your JIRA Assistant Skills are now set up! Here's what you can do:

**Test with a known issue:**
```bash
python3 .claude/skills/jira-issue/scripts/get_issue.py PROJ-123
```

**Or just ask me naturally:**
- 'Show me my open issues'
- 'What's blocking the release?'
- 'Create a bug for the login page crash'
- 'What did I work on this week?'

I'm ready to help you with JIRA!"

## Troubleshooting

If authentication fails:
- **401 Unauthorized**: Token is incorrect or expired. Create a new one.
- **403 Forbidden**: Email doesn't match the account, or the account lacks permissions.
- **Connection error**: Check the URL is correct and reachable.

If keychain storage fails:
- On macOS: The Keychain Access app may prompt for permission
- On Windows: Windows Credential Manager should work automatically
- On Linux: Ensure GNOME Keyring or KWallet is running

Fallback option: Store in settings.local.json with `--json-only` flag.
