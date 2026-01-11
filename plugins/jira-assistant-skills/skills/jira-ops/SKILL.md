---
name: "jira-operations"
description: "Cache management, request batching, and operational utilities. Use when optimizing performance, managing cache, or diagnosing JIRA API issues."
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
triggers:
  - "Cache hit rate drops below 50%"
  - "JIRA API responses slower than 2 seconds"
  - "Setting up new JIRA instance"
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

**IMPORTANT:** Always use the `jira-as` CLI. Never run Python scripts directly.

- **Project Discovery**: Discover project metadata, workflows, and patterns for intelligent defaults
- **Cache Status Monitoring**: Display cache statistics (size, entries, hit rates)
- **Cache Clearing**: Remove cache entries by category, pattern, or all at once
- **Cache Warming**: Pre-load project metadata and field definitions
- **Request Batching**: Parallel request execution for bulk operations (programmatic API)

## Quick Start

```bash
# Discover project context (saves to skill directory by default)
jira-as ops discover-project PROJ

# Check cache status
jira-as ops cache-status

# Clear all cache
jira-as ops cache-clear --force

# Warm cache with all metadata
jira-as ops cache-warm --all
```

## Common Tasks (30-Second Solutions)

### Check cache status
```bash
# Basic status
jira-as ops cache-status

# Output as JSON
jira-as ops cache-status --json

# Verbose output
jira-as ops cache-status --verbose
```

### Warm the cache
```bash
# Cache project list
jira-as ops cache-warm --projects

# Cache field definitions
jira-as ops cache-warm --fields

# Cache all available metadata with verbose output
jira-as ops cache-warm --all --verbose
```

### Clear cache
```bash
# Clear all cache (with confirmation)
jira-as ops cache-clear

# Clear all cache (skip confirmation)
jira-as ops cache-clear --force

# Clear only issue cache
jira-as ops cache-clear --category issue --force

# Preview what would be cleared
jira-as ops cache-clear --dry-run

# Clear keys matching pattern
jira-as ops cache-clear --pattern "PROJ-*" --category issue --force
```

### Discover project context
```bash
# Discover and save to skill directory (default)
jira-as ops discover-project PROJ

# Save to settings.local.json for personal use
jira-as ops discover-project PROJ --personal

# Save to both locations
jira-as ops discover-project PROJ --both

# Output JSON without saving
jira-as ops discover-project PROJ --output json --no-save

# Custom sample size and period
jira-as ops discover-project PROJ --sample-size 200 --days 60
```

See [Commands Guide](docs/COMMANDS.md) for complete documentation.

## Available Commands

All commands support `--help` for full documentation.

| Command | Description |
|---------|-------------|
| `jira-as ops discover-project` | Discover project metadata, workflows, and patterns |
| `jira-as ops cache-status` | Display cache statistics (size, entries, hit rate) |
| `jira-as ops cache-clear` | Clear cache entries (all, by category, or by pattern) |
| `jira-as ops cache-warm` | Pre-warm cache with commonly accessed data |

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

This skill uses shared infrastructure from `jira-assistant-skills-lib`:

| Library | Description |
|---------|-------------|
| `cache.py` | SQLite-based caching with TTL and LRU eviction |
| `request_batcher.py` | Parallel request batching for bulk operations |

See [API Reference](docs/API_REFERENCE.md) for programmatic usage.

## Documentation

- [Quick Start Guide](docs/QUICK_START.md) - Get started in 5 minutes
- [Scripts Guide](docs/SCRIPTS.md) - Detailed script documentation
- [API Reference](docs/API_REFERENCE.md) - Programmatic cache and batcher APIs
- [Configuration](docs/CONFIG.md) - TTL settings
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Security](docs/SECURITY.md) - Cache security considerations
- [Best Practices](docs/best-practices/INDEX.md) - Optimization patterns

