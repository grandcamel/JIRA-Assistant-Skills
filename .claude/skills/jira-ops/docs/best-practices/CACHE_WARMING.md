# Cache Warming Techniques

Pre-load data to reduce initial latency and prevent cache stampede.

## Why Warm the Cache?

- Reduce initial latency for common operations
- Prevent cache stampede during peak usage
- Improve user experience with faster responses
- Reduce API calls during production usage

## When to Warm

- Application startup
- After cache clear operations
- Before scheduled high-traffic periods
- After deploying to new environment

## Warming Strategies

### Strategy 1: Preload Metadata

```bash
python cache_warm.py --projects --fields --profile production
```

### Strategy 2: Warm by Project

```python
def warm_project_cache(client, cache, project_key):
    """Warm cache with recent issues from project."""
    project = client.get_project(project_key)
    cache.set(f"project:{project_key}", project, category="project")

    jql = f"project = {project_key} AND updated >= -30d ORDER BY updated DESC"
    issues = client.search_issues(jql, max_results=100)

    for issue in issues['issues']:
        cache.set(issue['key'], issue, category="issue")

    print(f"Warmed {len(issues['issues'])} issues for {project_key}")
```

### Strategy 3: Scheduled Warming

```bash
# Cron job to warm cache daily at 6 AM
0 6 * * * /usr/bin/python3 /path/to/cache_warm.py --all --profile production
```

## Best Practices

### Prioritize by Access Frequency

| Priority | Data Type | TTL | Warm Frequency |
|----------|-----------|-----|----------------|
| High | Projects, fields, users | 1 hour - 1 day | Daily |
| Medium | Recent issues (last 7 days) | 5 minutes | Hourly |
| Low | Old issues, archived data | 1 hour | On-demand |

### Warm During Off-Peak Hours

- Avoid warming during business hours (9 AM - 5 PM)
- Schedule for early morning (5-7 AM)
- Respect rate limits during warming

### Incremental Warming

```python
# Warm in stages with delays
warm_projects()
time.sleep(10)
warm_users()
time.sleep(10)
warm_recent_issues()
```

### Verify After Warming

```bash
python cache_warm.py --all
python cache_status.py
```

## See Also

- [Cache Invalidation](CACHE_INVALIDATION.md)
- [Performance Monitoring](PERFORMANCE_MONITORING.md)
