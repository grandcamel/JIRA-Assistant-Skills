# Quick Start Guide

Get started with JIRA Operations in 5 minutes.

## Prerequisites

1. Python 3.8+ installed
2. JIRA credentials configured (environment variables or settings.json)

## Step 1: Verify Setup

```bash
# Check that credentials are set
echo $JIRA_API_TOKEN  # Should not be empty
echo $JIRA_EMAIL
echo $JIRA_SITE_URL
```

## Step 2: Check Cache Status

```bash
python cache_status.py
```

Expected output:
```
Cache Statistics:
  Total Size: 0 MB / 100 MB
  Entries: 0
  Hit Rate: N/A
```

## Step 3: Warm the Cache

```bash
python cache_warm.py --all --profile development
```

This pre-loads:
- Project metadata
- Field definitions
- User information

## Step 4: Discover Project Context

```bash
python discover_project.py PROJ --profile development
```

This creates intelligent defaults based on your project's patterns.

## Step 5: Verify Cache is Working

```bash
python cache_status.py
```

Expected output:
```
Cache Statistics:
  Total Size: 5 MB / 100 MB
  Entries: 234
  Hit Rate: N/A (no hits yet)
```

## Next Steps

- [Scripts Guide](SCRIPTS.md) - Learn all available commands
- [Configuration](CONFIG.md) - Customize TTL and settings
- [Best Practices](best-practices/INDEX.md) - Optimization patterns
