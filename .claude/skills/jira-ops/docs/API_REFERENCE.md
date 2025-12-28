# API Reference

Programmatic APIs for cache and request batching.

## JiraCache

SQLite-based caching with TTL and LRU eviction.

### Import

```python
from cache import JiraCache
```

### Basic Usage

```python
cache = JiraCache()

# Cache an issue
cache.set("PROJ-123", issue_data, category="issue")

# Retrieve cached issue
issue = cache.get("PROJ-123", category="issue")

# Invalidate by pattern
cache.invalidate(pattern="PROJ-*", category="issue")

# Get statistics
stats = cache.get_stats()
print(f"Hit rate: {stats.hit_rate * 100:.1f}%")
```

### Methods

#### `set(key, value, category, ttl=None)`

Store a value in the cache.

| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | str | Unique identifier |
| `value` | any | JSON-serializable data |
| `category` | str | Cache category (issue, project, user, field, search) |
| `ttl` | timedelta | Optional custom TTL (overrides category default) |

#### `get(key, category)`

Retrieve a value from the cache.

Returns `None` if not found or expired.

#### `invalidate(key=None, pattern=None, category=None)`

Remove entries from the cache.

| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | str | Specific key to invalidate |
| `pattern` | str | Pattern with wildcards (e.g., "PROJ-*") |
| `category` | str | Invalidate entire category |

Returns the number of entries removed.

#### `get_stats()`

Get cache statistics.

Returns a `CacheStats` object with:
- `hit_rate`: Float (0.0 to 1.0)
- `hits`: Integer
- `misses`: Integer
- `entry_count`: Integer
- `total_size_bytes`: Integer
- `by_category`: Dict with per-category stats

## RequestBatcher

Parallel request execution for bulk operations.

### Import

```python
from request_batcher import RequestBatcher, batch_fetch_issues
```

### Basic Usage

```python
batcher = RequestBatcher(client, max_concurrent=10)

# Add requests
id1 = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
id2 = batcher.add("GET", "/rest/api/3/issue/PROJ-2")

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

### Convenience Function

```python
issues = batch_fetch_issues(
    client,
    ["PROJ-1", "PROJ-2", "PROJ-3"],
    progress_callback=lambda done, total: print(f"{done}/{total}")
)

for key, data in issues.items():
    if "error" in data:
        print(f"{key}: {data['error']}")
    else:
        print(f"{key}: {data['fields']['summary']}")
```

### Methods

#### `add(method, endpoint, data=None)`

Add a request to the batch.

| Parameter | Type | Description |
|-----------|------|-------------|
| `method` | str | HTTP method (GET, POST, PUT, DELETE) |
| `endpoint` | str | API endpoint path |
| `data` | dict | Optional request body |

Returns a unique request ID.

#### `execute_sync(progress_callback=None)`

Execute all queued requests in parallel.

| Parameter | Type | Description |
|-----------|------|-------------|
| `progress_callback` | callable | Optional `(completed, total)` callback |

Returns a dict mapping request IDs to `BatchResult` objects.

### BatchResult

| Attribute | Type | Description |
|-----------|------|-------------|
| `success` | bool | Whether request succeeded |
| `data` | dict | Response data (if successful) |
| `error` | str | Error message (if failed) |
| `duration_ms` | float | Request duration in milliseconds |

## Exit Codes

All scripts use consistent exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (invalid arguments, operation failed) |
| 2 | Configuration error (missing credentials, invalid profile) |
| 3 | Cache database error (cannot open, corrupted, permission denied) |
| 4 | Network error (cannot connect to JIRA) |
