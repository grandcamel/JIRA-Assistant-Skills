# Request Batching Strategies

Execute multiple API requests in parallel to improve performance.

## When to Use Batching

**Good Candidates:**
- Fetching multiple issues (10+)
- Bulk updates to issue fields
- Loading related data (issues + comments + worklogs)
- Exporting large datasets

**Poor Candidates:**
- Single issue operations
- Time-critical operations requiring immediate response
- Operations with complex dependencies

## Basic Usage

```python
from request_batcher import RequestBatcher

batcher = RequestBatcher(client, max_concurrent=10)

# Add requests
batcher.add("GET", "/rest/api/3/issue/PROJ-1")
batcher.add("GET", "/rest/api/3/issue/PROJ-2")
batcher.add("GET", "/rest/api/3/issue/PROJ-3")

# Execute in parallel
results = batcher.execute_sync(
    progress_callback=lambda done, total: print(f"{done}/{total}")
)

# Process results
for request_id, result in results.items():
    if result.success:
        print(f"Success: {result.data['key']}")
    else:
        print(f"Error: {result.error}")
```

## Concurrency Guidelines

| Scenario | Recommended max_concurrent |
|----------|---------------------------|
| Small batches (< 50 requests) | 5-10 |
| Medium batches (50-500) | 10-20 |
| Large batches (500+) | 20-50 |
| Rate limit sensitive | 5 |

## Handling Partial Failures

```python
results = batcher.execute_sync()

successes = [r for r in results.values() if r.success]
failures = [r for r in results.values() if not r.success]

print(f"Succeeded: {len(successes)}, Failed: {len(failures)}")
```

## Dependency Batching Pattern

```python
# Fetch issues first
issue_batcher = RequestBatcher(client)
for key in issue_keys:
    issue_batcher.add("GET", f"/rest/api/3/issue/{key}")
issues = issue_batcher.execute_sync()

# Then fetch comments for successful issues
comment_batcher = RequestBatcher(client)
for key, result in issues.items():
    if result.success:
        comment_batcher.add("GET", f"/rest/api/3/issue/{key}/comment")
comments = comment_batcher.execute_sync()
```

## See Also

- [API Reference](../API_REFERENCE.md) - Full RequestBatcher documentation
- [Rate Limits](RATE_LIMITS.md) - Stay within API limits
