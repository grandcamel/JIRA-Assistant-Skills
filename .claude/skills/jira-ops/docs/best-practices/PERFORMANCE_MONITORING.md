# Performance Monitoring

Key metrics and monitoring strategies.

## Key Metrics

| Metric | Target | Critical | How to Measure |
|--------|--------|----------|----------------|
| Cache Hit Rate | > 70% | < 50% | `cache.get_stats().hit_rate` |
| Request Time | < 500ms | > 2000ms | `result.duration_ms` |
| Rate Limit Remaining | > 20% | < 5% | `X-RateLimit-Remaining` header |
| Cache Size | < 80% max | > 95% max | `cache.get_stats().total_size_bytes` |

## Monitoring Cache Performance

### Command-Line

```bash
python cache_status.py
```

### Programmatic

```python
from cache import JiraCache

cache = JiraCache()
stats = cache.get_stats()

print(f"Hit Rate: {stats.hit_rate * 100:.1f}%")
print(f"Total Entries: {stats.entry_count}")
print(f"Size: {stats.total_size_bytes / 1024 / 1024:.2f} MB")

if stats.hit_rate < 0.5:
    print("WARNING: Cache hit rate below 50%")
```

## Monitoring API Performance

```python
import time

start = time.time()
issue = client.get_issue("PROJ-123")
elapsed_ms = (time.time() - start) * 1000

print(f"Request took {elapsed_ms:.2f}ms")

if elapsed_ms > 2000:
    print("WARNING: Slow API response")
```

## Setting Up Alerts

### Cache Hit Rate Alert

```python
def check_cache_health(cache, threshold=0.5):
    stats = cache.get_stats()
    if stats.hit_rate < threshold:
        send_alert(
            level="WARNING",
            message=f"Cache hit rate is {stats.hit_rate * 100:.1f}%"
        )
```

### Rate Limit Alert

```python
def check_rate_limit_health(client, threshold=0.2):
    response = client.session.get(f"{client.base_url}/rest/api/3/myself")
    remaining = int(response.headers.get('X-RateLimit-Remaining', 999999))
    limit = int(response.headers.get('X-RateLimit-Limit', 1000000))

    if remaining / limit < threshold:
        send_alert(
            level="CRITICAL",
            message=f"Rate limit at {remaining}/{limit}"
        )
```

## See Also

- [Health Checks](HEALTH_CHECKS.md)
- [Logging & Debug](LOGGING_DEBUG.md)
