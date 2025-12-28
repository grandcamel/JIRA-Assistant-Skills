# Connection Pooling

Reuse TCP connections to improve performance.

## Why Connection Pooling?

- Up to 60% reduction in per-request latency
- Eliminates TCP handshake overhead
- Reuses TLS/SSL sessions

## Built-in Configuration

JiraClient uses connection pooling by default:

```python
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
```

Default pool settings:
- `pool_connections`: 10
- `pool_maxsize`: 10
- `pool_block`: False

## Custom Configuration

For high-volume applications:

```python
from requests.adapters import HTTPAdapter

adapter = HTTPAdapter(
    pool_connections=20,
    pool_maxsize=50,
    pool_block=True
)

session = requests.Session()
session.mount("https://", adapter)
```

## Configuration Guidelines

| Scenario | pool_connections | pool_maxsize |
|----------|------------------|--------------|
| Single JIRA instance | 1-5 | 20-50 |
| Multiple JIRA instances | 10-20 | 10-20 |
| Low concurrency | 1 | 10 |
| High concurrency (50+ threads) | 5-10 | 50-100 |

## Best Practices

### Reuse Sessions

```python
# Good: Reuse session
session = requests.Session()

def get_issue(issue_key):
    return session.get(f"{base_url}/rest/api/3/issue/{issue_key}")
```

### Read Response Bodies

```python
# Release connection by reading body
response = session.get(url)
data = response.json()
```

### Thread-Local Sessions

For multi-threaded applications:

```python
import threading

thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session
```

## See Also

- [Timeout Configuration](TIMEOUT_CONFIGURATION.md)
- [Common Pitfalls](COMMON_PITFALLS.md)
