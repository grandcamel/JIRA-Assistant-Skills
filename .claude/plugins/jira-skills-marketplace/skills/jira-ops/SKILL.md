---
name: "JIRA Operations"
description: "Cache management, request batching, and operational utilities. Use when optimizing performance, managing cache, or diagnosing JIRA API issues."
triggers:
  - "Cache hit rate drops below 50%"
  - "JIRA API responses slower than 2 seconds"
  - "Setting up new JIRA profile/instance"
  - "Before bulk operations (warm cache first)"
  - "After modifying projects (invalidate cache)"
  - "Troubleshooting 429 rate limit errors"
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

## What This Skill Does

- **Project Discovery**: Discover project metadata, workflows, and patterns for intelligent defaults
- **Cache Status Monitoring**: Display cache statistics (size, entries, hit rates)
- **Cache Clearing**: Remove cache entries by category, pattern, or all at once
- **Cache Warming**: Pre-load project metadata and field definitions
- **Request Batching**: Parallel request execution for bulk operations (programmatic API)

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

## Common Tasks (30-Second Solutions)

### Check cache status
```bash
python cache_status.py
```

### Warm the cache
```bash
python cache_warm.py --all --profile production
```

### Clear stale cache
```bash
python cache_clear.py --force
```

See [Scripts Guide](docs/SCRIPTS.md) for complete documentation.

## Scripts

| Script | Description |
|--------|-------------|
| `discover_project.py` | Discover project metadata, workflows, and patterns |
| `cache_status.py` | Display cache statistics (size, entries, hit rate) |
| `cache_clear.py` | Clear cache entries (all, by category, or by pattern) |
| `cache_warm.py` | Pre-warm cache with commonly accessed data |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Cache database error |
| 4 | Network error |

## Configuration

Cache is stored in `~/.jira-skills/cache/` with configurable TTL per category.

See [Configuration Guide](docs/CONFIG.md) for details.

## Shared Libraries

This skill uses shared infrastructure from `.claude/skills/shared/scripts/lib/`:

| Library | Description |
|---------|-------------|
| `cache.py` | SQLite-based caching with TTL and LRU eviction |
| `request_batcher.py` | Parallel request batching for bulk operations |

See [API Reference](docs/API_REFERENCE.md) for programmatic usage.

## Documentation

- [Quick Start Guide](docs/QUICK_START.md) - Get started in 5 minutes
- [Scripts Guide](docs/SCRIPTS.md) - Detailed script documentation
- [API Reference](docs/API_REFERENCE.md) - Programmatic cache and batcher APIs
- [Configuration](docs/CONFIG.md) - TTL and profile settings
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Security](docs/SECURITY.md) - Cache security considerations
- [Best Practices](docs/best-practices/INDEX.md) - Optimization patterns

## Testing

```bash
cd /path/to/Jira-Assistant-Skills
PYTHONPATH=".claude/skills/shared/scripts/lib:.claude/skills/jira-ops/scripts" \
  python -m pytest .claude/skills/jira-ops/tests/ -v
```
