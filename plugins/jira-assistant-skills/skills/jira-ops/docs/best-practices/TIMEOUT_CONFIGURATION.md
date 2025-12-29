# Timeout Configuration

Prevent hung requests with appropriate timeouts.

## Why Timeouts Matter

Without timeouts:
- Requests can hang indefinitely
- Threads/resources tied up
- Cascading failures

## Timeout Types

- **Connect Timeout**: Time to establish connection (3-10 seconds)
- **Read Timeout**: Time waiting for server response (10-60 seconds)

## Built-in Configuration

JiraClient uses a 30-second default timeout.

## Setting Timeouts

```python
# Single timeout value
response = client.session.get(url, timeout=30)

# Tuple: (connect_timeout, read_timeout)
response = client.session.get(url, timeout=(10, 60))
```

## Recommended Values

| Operation Type | Connect | Read | Total |
|----------------|---------|------|-------|
| Get single issue | 10s | 20s | 30s |
| Search (small) | 10s | 30s | 40s |
| Search (large) | 10s | 60s | 70s |
| Create issue | 10s | 20s | 30s |
| Bulk export | 10s | 120s | 130s |
| Upload attachment | 10s | 60s | 70s |

## Handling Timeout Errors

```python
import requests

try:
    response = client.get_issue(issue_key)
except requests.exceptions.ConnectTimeout:
    print("Connection timeout - could not reach JIRA")
except requests.exceptions.ReadTimeout:
    print("Read timeout - JIRA took too long to respond")
except requests.exceptions.Timeout:
    print("Generic timeout error")
```

## Environment-Specific Timeouts

```python
import os

if os.getenv("ENV") == "production":
    DEFAULT_TIMEOUT = 30  # Fail fast
else:
    DEFAULT_TIMEOUT = 120  # Debugging
```

## See Also

- [Connection Pooling](CONNECTION_POOLING.md)
- [Error Handling](ERROR_HANDLING.md)
