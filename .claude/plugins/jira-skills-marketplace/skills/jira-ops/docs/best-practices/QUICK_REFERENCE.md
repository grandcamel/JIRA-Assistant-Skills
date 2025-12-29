# Quick Reference Card

## Rate Limits

```bash
# Key limits
- Burst: 1,000 requests/min
- Total: 10,000 requests/min per instance
```

## Cache Operations

```bash
# Check cache status
python cache_status.py

# Warm cache
python cache_warm.py --all --profile production

# Clear cache
python cache_clear.py --force

# Clear by pattern
python cache_clear.py --pattern "PROJ-*" --category issue --force
```

## Request Batching

```python
from request_batcher import RequestBatcher

batcher = RequestBatcher(client, max_concurrent=10)
batcher.add("GET", "/rest/api/3/issue/PROJ-1")
batcher.add("GET", "/rest/api/3/issue/PROJ-2")
results = batcher.execute_sync()
```

## Connection Pooling

```python
from requests.adapters import HTTPAdapter

adapter = HTTPAdapter(
    pool_connections=10,
    pool_maxsize=50,
    pool_block=True
)
session.mount("https://", adapter)
```

## Timeout Configuration

```python
# Set timeout (connect, read)
response = client.get(endpoint, timeout=(10, 60))

# Common timeouts
- Single issue: 30s
- Search: 60s
- Bulk operations: 120s
```

## Error Handling

```python
from error_handler import JiraError

try:
    issue = client.get_issue(key)
except JiraError as e:
    if e.status_code == 429:
        time.sleep(60)  # Rate limited
    elif e.status_code in [500, 502, 503]:
        retry_with_backoff()  # Server error
```

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Cache hit rate | > 70% | < 50% |
| Request time | < 500ms | > 2000ms |
| Rate limit remaining | > 20% | < 5% |
| Error rate | < 1% | > 5% |

## Health Check

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

## Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Or via environment
export DEBUG=1
python script.py
```
