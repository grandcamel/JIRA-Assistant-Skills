# Error Handling & Retry Strategies

Robust error handling for JIRA API operations.

## Built-in Retry Logic

JiraClient automatically retries on transient errors:

```python
# Retry timeline: 0s, 1s, 2s, 4s
retry_strategy = Retry(
    total=3,
    backoff_factor=2.0,
    status_forcelist=[429, 500, 502, 503, 504]
)
```

## Error Classification

| Error Code | Meaning | Action |
|------------|---------|--------|
| 400 | Bad Request | Don't retry, fix request |
| 401 | Unauthorized | Check credentials |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Handle gracefully |
| **429** | Rate Limited | **Retry with backoff** |
| **500-504** | Server Error | **Retry with backoff** |

## Error Handling Patterns

### Pattern 1: Fail Fast

For non-critical operations:

```python
try:
    optional_data = client.get_issue_comments(key)
except JiraError as e:
    print(f"Warning: Could not fetch comments: {e}")
    optional_data = []
```

### Pattern 2: Fallback Strategy

```python
def get_issue_with_fallback(client, cache, issue_key):
    # Try cache first
    issue = cache.get(issue_key, category="issue")
    if issue:
        return issue

    # Try API
    try:
        issue = client.get_issue(issue_key)
        cache.set(issue_key, issue, category="issue")
        return issue
    except JiraError:
        pass

    # No fallback available
    raise Exception(f"Could not fetch {issue_key}")
```

### Pattern 3: Graceful Degradation

```python
successes = []
failures = []

for key in keys:
    try:
        issue = client.get_issue(key)
        process(issue)
        successes.append(key)
    except JiraError as e:
        failures.append((key, str(e)))
        logger.error(f"Failed to process {key}: {e}")

print(f"Succeeded: {len(successes)}, Failed: {len(failures)}")
```

## Custom Retry Decorator

```python
def retry_with_backoff(max_retries=3, base_delay=1.0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except JiraError as e:
                    if attempt == max_retries:
                        raise
                    if e.status_code not in [429, 500, 502, 503, 504]:
                        raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
            return None
        return wrapper
    return decorator
```

## See Also

- [Rate Limits](RATE_LIMITS.md)
- [Health Checks](HEALTH_CHECKS.md)
