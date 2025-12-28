# Health Checks & Diagnostics

Monitor system health and diagnose issues.

## Basic Health Check

```python
def check_jira_health(client):
    """Check if JIRA is accessible."""
    try:
        response = client.session.get(
            f"{client.base_url}/rest/api/3/myself",
            timeout=10
        )

        if response.status_code == 200:
            return {
                'status': 'healthy',
                'message': 'JIRA is accessible',
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
        else:
            return {
                'status': 'unhealthy',
                'message': f'HTTP {response.status_code}'
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': str(e)
        }
```

## Comprehensive Health Check

```python
def comprehensive_health_check(client, cache):
    """Perform comprehensive health check."""
    checks = {}

    # JIRA connectivity
    checks['jira_connectivity'] = check_jira_health(client)

    # Cache health
    stats = cache.get_stats()
    checks['cache_health'] = {
        'status': 'healthy' if stats.hit_rate > 0.5 else 'degraded',
        'hit_rate': f"{stats.hit_rate * 100:.1f}%",
        'entry_count': stats.entry_count
    }

    # Rate limit status
    response = client.session.get(f"{client.base_url}/rest/api/3/myself")
    remaining = int(response.headers.get('X-RateLimit-Remaining', 999))
    limit = int(response.headers.get('X-RateLimit-Limit', 1000))

    checks['rate_limit'] = {
        'status': 'healthy' if remaining / limit > 0.2 else 'warning',
        'remaining': remaining,
        'limit': limit
    }

    # Overall status
    statuses = [c.get('status') for c in checks.values()]
    if 'unhealthy' in statuses:
        overall = 'unhealthy'
    elif 'degraded' in statuses or 'warning' in statuses:
        overall = 'degraded'
    else:
        overall = 'healthy'

    return {'overall_status': overall, 'checks': checks}
```

## Quick CLI Health Check

```python
python -c "
from config_manager import get_jira_client
from cache import JiraCache

client = get_jira_client()
cache = JiraCache()

print('JIRA:', client.get('/rest/api/3/myself')['displayName'])
stats = cache.get_stats()
print(f'Cache: {stats.entry_count} entries, {stats.hit_rate*100:.1f}% hit rate')
"
```

## Scheduled Health Checks

Add to crontab for regular monitoring:

```bash
# Every 5 minutes
*/5 * * * * /path/to/health_check.sh >> /var/log/jira-health.log
```

## See Also

- [Performance Monitoring](PERFORMANCE_MONITORING.md)
- [Troubleshooting](../TROUBLESHOOTING.md)
