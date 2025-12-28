# Rate Limit Handling

JIRA Cloud limits API calls to 1,000 requests/minute. Use cache warming and request batching to stay within limits.

See [Atlassian Rate Limiting](https://developer.atlassian.com/cloud/jira/platform/rate-limiting/) for official documentation.

## Rate Limit Reference

| Limit Type | Default | Window |
|------------|---------|--------|
| Burst Limit | 1,000 requests/min | Per second |
| Total Instance Limit | 10,000 requests/min | Per minute |
| Points-based | Varies by operation | Per hour |

## Detecting Rate Limits

**HTTP 429 Response Headers:**
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `Retry-After`: Seconds to wait before retrying

## Best Practices

### 1. Monitor Rate Limit Headers

```python
response = client.get('/rest/api/3/issue/PROJ-123')
remaining = response.headers.get('X-RateLimit-Remaining')
if remaining and int(remaining) < 100:
    print(f"Warning: Only {remaining} requests remaining")
```

### 2. Use Exponential Backoff

The JiraClient automatically retries with exponential backoff on 429 errors.

### 3. Batch Related Requests

- Use JQL search instead of fetching issues individually
- Combine field updates into single update operations
- Use [Request Batching](REQUEST_BATCHING.md) for parallel execution

### 4. Cache Aggressively

- Cache metadata (projects, users, fields) for hours
- Cache issue data for minutes
- Use [Cache Warming](CACHE_WARMING.md) to pre-load data

### 5. Spread Requests Over Time

```python
# Use controlled concurrency
batcher = RequestBatcher(client, max_concurrent=10)
for key in issue_keys:
    batcher.add("GET", f"/rest/api/3/issue/{key}")
results = batcher.execute_sync()
```

## See Also

- [Request Batching](REQUEST_BATCHING.md)
- [Cache Warming](CACHE_WARMING.md)
- [Error Handling](ERROR_HANDLING.md)
