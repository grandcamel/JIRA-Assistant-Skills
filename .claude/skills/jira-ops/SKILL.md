---
name: "JIRA Operations"
description: "Cache management and operational utilities for JIRA Assistant - cache warming, clearing, status monitoring. Use when optimizing performance, managing cache, or checking operational status."
---

# JIRA Operations Skill

Cache management, request batching, and operational utilities for JIRA Assistant.

## When to Use This Skill

Use this skill when you need to:
- **Discover project context**: Auto-discover project metadata, workflows, and usage patterns
- **Monitor cache status**: Check cache size, entry counts, and hit rates
- **Clear cache data**: Remove stale or sensitive cached data
- **Pre-warm cache**: Load commonly accessed data for better performance
- **Optimize performance**: Reduce API calls through effective caching
- **Troubleshoot slowness**: Diagnose cache-related performance issues
- **Prepare for production**: Warm cache before heavy usage periods

## What This Skill Does

- **Project Discovery**: Discover project metadata, workflows, and usage patterns to enable intelligent defaults
- **Cache Status Monitoring**: Display detailed cache statistics including size, entries, hit rates, and breakdowns by category
- **Cache Clearing**: Remove cache entries by category, pattern, or all at once with dry-run support
- **Cache Warming**: Pre-load project metadata, field definitions, and other frequently accessed data
- **Request Batching**: Parallel request execution for bulk operations (programmatic API)
- **Performance Optimization**: Reduce JIRA API calls through intelligent caching with configurable TTL

## Quick Start

```bash
# Discover project context for intelligent defaults
python discover_project.py PROJ --profile development

# Check cache status
python cache_status.py

# Clear cache
python cache_clear.py --force

# Warm cache with project/field data
python cache_warm.py --all --profile production
```

## Scripts

### Project Discovery

| Script | Description |
|--------|-------------|
| `discover_project.py` | Discover project metadata, workflows, and patterns for intelligent defaults |

### Cache Management

| Script | Description |
|--------|-------------|
| `cache_status.py` | Display cache statistics (size, entries, hit rate) |
| `cache_clear.py` | Clear cache entries (all, by category, or by pattern) |
| `cache_warm.py` | Pre-warm cache with commonly accessed data |

## Script Details

### discover_project.py

Discover JIRA project context and save to skill directory for intelligent defaults.

```bash
# Discover and save to shareable skill directory
python discover_project.py PROJ

# Use specific profile
python discover_project.py PROJ --profile development

# Save to personal settings.local.json instead
python discover_project.py PROJ --personal

# Save to both skill directory and settings.local.json
python discover_project.py PROJ --both

# Custom sample size and period
python discover_project.py PROJ --sample-size 200 --days 60

# Output as JSON without saving
python discover_project.py PROJ --output json --no-save
```

**What Gets Discovered:**

- **Metadata**: Issue types, components, versions, priorities, assignable users
- **Workflows**: Valid status transitions for each issue type
- **Patterns**: Common assignees, labels, priorities based on recent activity
- **Defaults**: Auto-generated sensible defaults based on patterns

**Output:**

Creates a skill directory at `.claude/skills/jira-project-{PROJECT_KEY}/`:
```
jira-project-PROJ/
├── SKILL.md              # Skill documentation
├── context/
│   ├── metadata.json     # Issue types, components, versions
│   ├── workflows.json    # Status transitions per issue type
│   └── patterns.json     # Usage patterns from recent issues
└── defaults.json         # Auto-generated default values
```

### cache_status.py

Display JIRA cache statistics and status.

```bash
# Show cache status
python cache_status.py

# Output as JSON
python cache_status.py --json
```

**Output:**
```
Cache Statistics:
  Total Size: 12.5 MB / 100 MB
  Entries: 1,234
  Hit Rate: 78% (1000 hits, 234 misses)

By Category:
  issue: 800 entries, 8 MB
  project: 50 entries, 1 MB
  user: 200 entries, 2 MB
  field: 184 entries, 1.5 MB
```

### cache_clear.py

Clear JIRA cache entries.

```bash
# Clear all cache
python cache_clear.py --force

# Clear specific category
python cache_clear.py --category issue --force

# Clear by pattern
python cache_clear.py --pattern "PROJ-*" --category issue --force

# Dry run
python cache_clear.py --dry-run
```

### cache_warm.py

Pre-warm JIRA cache with commonly accessed data.

```bash
# Cache projects
python cache_warm.py --projects

# Cache field definitions
python cache_warm.py --fields

# Cache everything
python cache_warm.py --all --profile production --verbose
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (invalid arguments, operation failed) |
| 2 | Configuration error (missing credentials, invalid profile) |
| 3 | Cache database error (cannot open, corrupted, permission denied) |
| 4 | Network error (cannot connect to JIRA) |

## Configuration

Cache is stored in `~/.jira-skills/cache/` with the following TTL defaults:

| Category | TTL | Description |
|----------|-----|-------------|
| `issue` | 5 minutes | Issue data (frequently updated) |
| `project` | 1 hour | Project metadata |
| `user` | 1 hour | User information |
| `field` | 1 day | Field definitions |
| `search` | 1 minute | Search results |

## Security Considerations

**IMPORTANT: The cache directory contains sensitive data and should be protected.**

### Cached Sensitive Data

The cache may contain:
- **Issue details**: Confidential project information, bug descriptions, internal discussions
- **User information**: Account IDs, email addresses, display names
- **Project metadata**: Internal project names, configurations, custom fields
- **Search results**: Query responses that may reveal organizational structure

### Protection Measures

1. **Restrictive permissions**: The cache directory is created with `0700` permissions (owner read/write/execute only)
2. **Local storage only**: Cache is stored in user's home directory, not shared locations
3. **No credential storage**: API tokens and passwords are never cached (only used in-memory)
4. **TTL expiration**: Data automatically expires based on category TTL settings

### Best Practices

- Do not share the cache directory with other users
- Clear cache before sharing a machine: `python cache_clear.py --force`
- Use separate profiles for development/production to avoid data mixing
- Consider clearing cache after working with highly sensitive projects

## Shared Libraries

This skill uses shared infrastructure from `.claude/skills/shared/scripts/lib/`:

| Library | Description |
|---------|-------------|
| `cache.py` | SQLite-based caching with TTL and LRU eviction |
| `request_batcher.py` | Parallel request batching for bulk operations |

### Using the Cache Programmatically

```python
from cache import JiraCache

# Create cache instance
cache = JiraCache()

# Cache an issue
cache.set("PROJ-123", issue_data, category="issue")

# Retrieve cached issue
issue = cache.get("PROJ-123", category="issue")

# Invalidate by pattern
cache.invalidate(pattern="PROJ-*", category="issue")

# Get statistics
stats = cache.get_stats()
print(f"Hit rate: {stats.hit_rate * 100:.1f}%")
```

### Using Request Batching

```python
from request_batcher import RequestBatcher, batch_fetch_issues

# Option 1: Convenience function
issues = batch_fetch_issues(client, ["PROJ-1", "PROJ-2", "PROJ-3"])

# Option 2: Manual batching
batcher = RequestBatcher(client, max_concurrent=10)
id1 = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
id2 = batcher.add("GET", "/rest/api/3/issue/PROJ-2")

results = batcher.execute_sync(progress_callback=lambda c, t: print(f"{c}/{t}"))

for request_id, result in results.items():
    if result.success:
        print(f"Got: {result.data['key']}")
    else:
        print(f"Error: {result.error}")
```

## Troubleshooting

### Common Issues and Solutions

#### Cache Database Cannot Be Opened

```bash
$ python cache_status.py
Error: Cannot open cache database
```

**Causes and Solutions:**

1. **Cache directory doesn't exist**
   ```bash
   # Create the cache directory
   mkdir -p ~/.jira-skills/cache/
   ```

2. **Insufficient permissions**
   ```bash
   # Fix permissions on cache directory
   chmod 755 ~/.jira-skills/cache/
   chmod 644 ~/.jira-skills/cache/*.db 2>/dev/null || true
   ```

3. **Corrupted database file**
   ```bash
   # Remove and recreate the cache
   rm -f ~/.jira-skills/cache/jira_cache.db
   python cache_warm.py --all  # Recreate with fresh data
   ```

4. **Disk full**
   ```bash
   # Check disk space
   df -h ~/.jira-skills/cache/

   # Clear old cache if needed
   python cache_clear.py --force
   ```

#### Cannot Connect to JIRA

```bash
$ python cache_warm.py --all
Error: config_manager not available. Cannot connect to JIRA.
```

**Causes and Solutions:**

1. **Missing JIRA credentials**
   ```bash
   # Verify environment variables are set
   echo $JIRA_API_TOKEN  # Should not be empty
   echo $JIRA_EMAIL
   echo $JIRA_SITE_URL
   ```

2. **Invalid profile specified**
   ```bash
   # List available profiles
   cat .claude/settings.json | jq '.profiles | keys'

   # Use correct profile
   python cache_warm.py --all --profile development
   ```

3. **Network connectivity issues**
   ```bash
   # Test JIRA connectivity
   curl -s -o /dev/null -w "%{http_code}" https://your-company.atlassian.net
   ```

4. **Expired API token**
   - Generate a new API token at https://id.atlassian.com/manage/api-tokens
   - Update JIRA_API_TOKEN environment variable

#### Cache Warm Takes Too Long

**Causes and Solutions:**

1. **Too many projects/fields to cache**
   ```bash
   # Warm only specific categories
   python cache_warm.py --projects  # Just projects
   python cache_warm.py --fields    # Just fields
   ```

2. **Rate limiting from JIRA**
   - Add `--verbose` flag to see request timing
   - Wait a few minutes and retry
   - Use `--profile` to target a specific JIRA instance

3. **Large JIRA instance**
   - Consider caching only frequently used projects
   - Run cache warming during off-peak hours

#### Cache Not Improving Performance

**Causes and Solutions:**

1. **Cache TTL too short**
   - Default TTL values may be too aggressive
   - Frequently updated data (issues) has short TTL by design

2. **Wrong category being cached**
   ```bash
   # Check what's in the cache
   python cache_status.py

   # Verify the category you need is cached
   # issues: 5 min TTL
   # projects: 1 hour TTL
   # fields: 1 day TTL
   ```

3. **Cache invalidation happening too often**
   - Review any automation that might be clearing cache
   - Check for scripts calling `cache.invalidate()` unnecessarily

#### Permission Denied Errors

```bash
$ python cache_clear.py --force
PermissionError: [Errno 13] Permission denied: '/home/user/.jira-skills/cache/jira_cache.db'
```

**Solutions:**

1. **Fix file ownership**
   ```bash
   sudo chown -R $(whoami) ~/.jira-skills/
   ```

2. **Fix file permissions**
   ```bash
   chmod -R u+rw ~/.jira-skills/
   ```

3. **Running as different user**
   - Ensure you're running as the same user who created the cache

### Debug Mode

For detailed debugging, set the DEBUG environment variable:

```bash
# Enable debug logging
export DEBUG=1
python cache_warm.py --all --verbose

# Or for a single command
DEBUG=1 python cache_status.py
```

### Reset Everything

If all else fails, reset the cache completely:

```bash
# Remove all cache data
rm -rf ~/.jira-skills/cache/

# Recreate directory
mkdir -p ~/.jira-skills/cache/

# Warm with fresh data
python cache_warm.py --all --profile development
```

## Error Handling

All scripts provide meaningful error messages:

```bash
$ python cache_status.py
Error: Cannot open cache database

$ python cache_warm.py --all
Error: config_manager not available. Cannot connect to JIRA.
```

## Testing

Run tests with:

```bash
cd /path/to/Jira-Assistant-Skills
PYTHONPATH=".claude/skills/shared/scripts/lib:.claude/skills/jira-ops/scripts" \
  python -m pytest .claude/skills/jira-ops/tests/ -v
```

## Best Practices

For comprehensive guidance on cache management strategies, performance optimization, and operational workflows, see [Best Practices Guide](docs/BEST_PRACTICES.md).

## Roadmap

Future enhancements planned:
- Rate limiting integration
- Offline mode support
- Audit logging
- Undo/redo capability

See `docs/implementation-plans/ROBUSTNESS_SCALE_IMPLEMENTATION_PLAN.md` for details.
