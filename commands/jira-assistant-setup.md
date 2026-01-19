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

Check if the jira-assistant-skills-lib package is installed:
```bash
pip show jira-assistant-skills-lib 2>/dev/null && echo "Library installed" || echo "Library missing"
```

If the library is missing, install it:
```bash
pip install jira-assistant-skills-lib>=0.1.5
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

## Step 4: Configure Environment

Guide the user to set environment variables:

For bash/zsh (add to ~/.bashrc or ~/.zshrc):
```bash
export JIRA_SITE_URL="https://company.atlassian.net"
export JIRA_EMAIL="user@company.com"
export JIRA_API_TOKEN="their-token-here"
```

For PowerShell (add to profile):
```powershell
$env:JIRA_SITE_URL="https://company.atlassian.net"
$env:JIRA_EMAIL="user@company.com"
$env:JIRA_API_TOKEN="their-token-here"
```

After setting, reload the shell:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

## Step 5: Validate Connection

Test the connection using the CLI:

```bash
jira-as issue get {any_issue_key}
```

Or test with a Python script:
```bash
python3 -c "
from jira_assistant_skills_lib import get_jira_client
client = get_jira_client()
me = client.get('/rest/api/3/myself')
print(f'Connected as: {me.get(\"displayName\", \"Unknown\")}')
"
```

## Step 6: Confirm Success

If validation succeeds, tell the user:

"Your JIRA Assistant Skills are now set up! Here's what you can do:

**Test with a known issue:**
```bash
jira-as issue get PROJ-123
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

If the CLI is not found:
- Ensure the plugin is installed: `pip install -e /path/to/plugin`
- Or use direct script execution: `python "${CLAUDE_PLUGIN_ROOT}/skills/jira-issue/scripts/get_issue.py" PROJ-123`

If import errors occur:
- Ensure the library is installed: `pip install jira-assistant-skills-lib>=0.1.5`
