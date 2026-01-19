# Troubleshooting Guide

Common issues and solutions for jira-ops.

## Cache Database Cannot Be Opened

```
Error: Cannot open cache database
```

### Causes and Solutions

**1. Cache directory doesn't exist**
```bash
mkdir -p ~/.jira-skills/cache/
```

**2. Insufficient permissions**
```bash
chmod 755 ~/.jira-skills/cache/
chmod 644 ~/.jira-skills/cache/*.db 2>/dev/null || true
```

**3. Corrupted database file**
```bash
rm -f ~/.jira-skills/cache/jira_cache.db
python cache_warm.py --all  # Recreate with fresh data
```

**4. Disk full**
```bash
df -h ~/.jira-skills/cache/
python cache_clear.py --force
```

## Cannot Connect to JIRA

```
Error: config_manager not available. Cannot connect to JIRA.
```

### Causes and Solutions

**1. Missing JIRA credentials**
```bash
echo $JIRA_API_TOKEN  # Should not be empty
echo $JIRA_EMAIL
echo $JIRA_SITE_URL
```

**2. Invalid profile specified**
```bash
cat .claude/settings.json | jq '.profiles | keys'
python cache_warm.py --all --profile development
```

**3. Network connectivity issues**
```bash
curl -s -o /dev/null -w "%{http_code}" https://your-company.atlassian.net
```

**4. Expired API token**
- Generate new token at https://id.atlassian.com/manage/api-tokens
- Update `JIRA_API_TOKEN` environment variable

## Cache Warm Takes Too Long

### Solutions

**1. Warm only specific categories**
```bash
python cache_warm.py --projects
python cache_warm.py --fields
```

**2. Rate limiting from JIRA**
- Add `--verbose` flag to see request timing
- Wait a few minutes and retry
- Run during off-peak hours

## Cache Not Improving Performance

### Check What's Cached

```bash
python cache_status.py
```

### Common Issues

**1. Cache TTL too short**
- Issues have 5 minute TTL by design
- Projects have 1 hour TTL
- Fields have 1 day TTL

**2. Wrong category being cached**
- Verify the category you need is actually cached

**3. Cache invalidation happening too often**
- Review automation that might be clearing cache

## Permission Denied Errors

```
PermissionError: [Errno 13] Permission denied
```

### Solutions

**1. Fix file ownership**
```bash
sudo chown -R $(whoami) ~/.jira-skills/
```

**2. Fix file permissions**
```bash
chmod -R u+rw ~/.jira-skills/
```

## Debug Mode

For detailed debugging:

```bash
# Enable debug logging
export DEBUG=1
python cache_warm.py --all --verbose

# Or for a single command
DEBUG=1 python cache_status.py
```

## Reset Everything

If all else fails:

```bash
# Remove all cache data
rm -rf ~/.jira-skills/cache/

# Recreate directory
mkdir -p ~/.jira-skills/cache/

# Warm with fresh data
python cache_warm.py --all --profile development
```
