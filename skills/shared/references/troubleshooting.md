# JIRA Assistant Skills - Troubleshooting Guide

Common issues and solutions.

## Authentication Errors

### Error: "Authentication failed"

**Causes:**
- Invalid API token
- Wrong email address
- Token expired or revoked

**Solutions:**
1. Verify `JIRA_API_TOKEN` is set correctly
2. Check `JIRA_EMAIL` matches your JIRA account
3. Generate a new API token at https://id.atlassian.com/manage-profile/security/api-tokens
4. Ensure no extra spaces in token/email

**Test:**
```bash
echo $JIRA_API_TOKEN  # Should show your token
echo $JIRA_EMAIL      # Should show your email
```

### Error: "JIRA API token not configured"

**Solution:**
Set the environment variable:
```bash
export JIRA_API_TOKEN="your-token-here"
```

Also set `JIRA_EMAIL` and `JIRA_SITE_URL`:
```bash
export JIRA_EMAIL="your@email.com"
export JIRA_SITE_URL="https://your-company.atlassian.net"
```

## Permission Errors

### Error: "Permission denied" or 403

**Causes:**
- Insufficient JIRA permissions
- Project access restricted
- Issue-level security

**Solutions:**
1. Check project permissions with JIRA admin
2. Verify you're assigned the correct role
3. Ensure project is accessible to you

### Error: "You do not have permission to transition this issue"

**Cause:** Workflow conditions restrict who can execute transition

**Solution:**
- Check if you're the assignee (may be required)
- Verify your role has permission
- Contact JIRA admin to adjust workflow

## Connection Errors

### Error: "Connection timeout" or "Connection refused"

**Causes:**
- Wrong JIRA URL
- Network/firewall issues
- JIRA instance down

**Solutions:**
1. Verify `JIRA_SITE_URL` is correct
2. Test in browser: https://your-company.atlassian.net
3. Check VPN connection if required
4. The library has automatic retry with exponential backoff

### Error: "SSL Certificate verification failed"

**Solution:**
Ensure URL uses HTTPS (not HTTP):
```bash
export JIRA_SITE_URL="https://your-company.atlassian.net"
```

## Configuration Errors

### Error: "Profile 'X' not found"

**Solution:**
Verify `JIRA_PROFILE` environment variable is set to a valid profile name, or omit it to use the default.

### Error: "JIRA URL not configured"

**Solution:**
Set the environment variable:
```bash
export JIRA_SITE_URL="https://your-company.atlassian.net"
```

## Validation Errors

### Error: "Invalid issue key format"

**Cause:** Issue key doesn't match pattern PROJECT-123

**Solution:**
Use correct format:
```bash
# Wrong
python get_issue.py proj-123
python get_issue.py 123

# Right
python get_issue.py PROJ-123
```

### Error: "JQL query contains potentially dangerous pattern"

**Cause:** Query contains suspicious SQL-like patterns

**Solution:**
Review and fix your JQL query - ensure it's valid JIRA syntax, not SQL.

## API Errors

### Error: "Field 'X' is required"

**Solution:**
Provide the required field:
```bash
python update_issue.py PROJ-123 --fields '{"fieldX": "value"}'
```

### Error: "Field 'X' cannot be set"

**Causes:**
- Field doesn't exist in project
- Field type mismatch
- Field not on screen

**Solutions:**
1. Check field exists: Get issue and examine fields
2. Verify field format matches type
3. Contact JIRA admin to add field to screen

### Error: 429 Too Many Requests

**Cause:** API rate limit exceeded

**Solutions:**
1. Wait a few minutes before retrying
2. Reduce request frequency
3. Use pagination with smaller page sizes
4. Scripts have automatic retry with backoff

## Search Errors

### Error: "No transitions available"

**Cause:** Issue is in final state or workflow misconfigured

**Solutions:**
1. Check current status: `python get_issue.py PROJ-123`
2. View available transitions: `python get_transitions.py PROJ-123`
3. Contact admin if workflow is broken

### Error: "Ambiguous transition name"

**Solution:**
Use transition ID instead of name:
```bash
# Instead of
python transition_issue.py PROJ-123 --name "Done"

# Use
python transition_issue.py PROJ-123 --id 31
```

## Script Errors

### Error: "ModuleNotFoundError: No module named 'requests'"

**Solution:**
Install the shared library:
```bash
pip install jira-assistant-skills-lib
```

### Error: "File not found" for templates or references

**Cause:** Running script from wrong directory

**Solution:**
Scripts work from any directory when the library is installed:
```bash
python get_issue.py PROJ-123
```

## Debugging

### Enable Debug Mode

Set environment variable:
```bash
export JIRA_DEBUG=1
```

### Check Configuration

```python
python -c "
from jira_assistant_skills_lib import ConfigManager
config = ConfigManager()
print('Profiles:', config.list_profiles())
print('Default:', config.profile)
"
```

### Test API Connection

```python
python -c "
from jira_assistant_skills_lib import get_jira_client
client = get_jira_client()
print('Testing connection...')
result = client.get('/rest/api/3/myself')
print('Success! Logged in as:', result.get('emailAddress'))
"
```

## Getting Help

1. Check error message carefully - often contains solution
2. Review relevant SKILL.md file
3. Check reference documentation in skill's `references/` folder
4. Verify environment variables are set correctly
5. Test with simple case first (e.g., get a known issue)
6. Contact JIRA administrator for permission issues

## Common Gotchas

1. **Case sensitivity:** Issue keys must be uppercase (PROJ-123, not proj-123)
2. **Quotes in shell:** Use proper quoting for strings with spaces
3. **JSON format:** Custom fields require proper JSON syntax
4. **Profile names:** Profile names are case-sensitive
5. **Email vs Account ID:** Some operations require account ID, not email
