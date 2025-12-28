# Troubleshooting

Common issues and solutions for JIRA Assistant Skills.

---

## Authentication Errors

### "401 Unauthorized"

**Cause:** Invalid or expired API token.

**Solution:**
1. Verify your token at [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Regenerate if expired
3. Check `JIRA_EMAIL` matches the token's account

```bash
# Verify environment variables are set
echo $JIRA_API_TOKEN
echo $JIRA_EMAIL
echo $JIRA_SITE_URL
```

### "403 Forbidden"

**Cause:** Insufficient permissions.

**Solution:**
- Verify your account has project access
- Check you have required permissions (Browse, Create, Edit, etc.)
- For JSM, ensure Service Management permissions

---

## Connection Errors

### "Connection refused" or timeout

**Cause:** Network issues or incorrect URL.

**Solution:**
1. Verify URL format: `https://company.atlassian.net` (no trailing slash)
2. Test connectivity: `curl -I https://company.atlassian.net`
3. Check proxy settings if behind corporate firewall

### "SSL certificate error"

**Cause:** Certificate validation failure.

**Solution:**
- Ensure you're using `https://`
- Check corporate proxy isn't intercepting SSL
- Update certificates: `pip install --upgrade certifi`

---

## Script Errors

### "ModuleNotFoundError"

**Cause:** Dependencies not installed.

**Solution:**
```bash
pip install -r .claude/skills/shared/scripts/lib/requirements.txt
```

### "Issue not found"

**Cause:** Issue key doesn't exist or no access.

**Solution:**
- Verify issue key format: `PROJ-123`
- Check project access permissions
- Ensure issue exists in specified profile's JIRA instance

---

## Profile Issues

### "Profile not found"

**Cause:** Profile name doesn't match configuration.

**Solution:**
1. Check `settings.json` or `settings.local.json` for profile names
2. Profile names are case-sensitive
3. Verify JSON syntax is valid

---

## Rate Limiting

### "429 Too Many Requests"

**Cause:** JIRA API rate limit exceeded.

**Solution:**
- The client automatically retries with exponential backoff
- For bulk operations, use smaller batches
- Add delays between rapid sequential requests

---

## Common Fixes

### Reset configuration

```bash
# Check current config
cat .claude/settings.json
cat .claude/settings.local.json

# Verify environment
env | grep JIRA
```

### Test basic connectivity

```bash
python .claude/skills/jira-issue/scripts/get_issue.py KNOWN-ISSUE --profile development
```

### Enable verbose output

```bash
python script.py --verbose
```

---

## Getting Help

- 💬 [GitHub Discussions](https://github.com/grandcamel/jira-assistant-skills/discussions)
- 🐛 [Report Issues](https://github.com/grandcamel/jira-assistant-skills/issues)

---

## See Also

- [Quick Start Guide](quick-start.md)
- [Configuration Guide](configuration.md)
- [Scripts Reference](scripts-reference.md)
