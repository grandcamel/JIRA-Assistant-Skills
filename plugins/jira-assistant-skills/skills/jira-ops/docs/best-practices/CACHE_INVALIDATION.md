# Cache Invalidation Patterns

Strategies for keeping cached data fresh.

## Invalidation Strategies

### Strategy 1: Time-Based (TTL)

```python
cache.set(key, value, category="issue")   # Expires in 5 minutes
cache.set(key, value, category="project") # Expires in 1 hour
cache.set(key, value, category="field")   # Expires in 1 day
```

Custom TTL:
```python
from datetime import timedelta
cache.set(key, value, category="custom", ttl=timedelta(minutes=30))
```

### Strategy 2: Event-Based

```python
def update_issue(client, cache, issue_key, update_data):
    client.update_issue(issue_key, update_data)
    cache.invalidate(key=issue_key, category="issue")
```

### Strategy 3: Pattern-Based

```python
# Invalidate all issues in a project
cache.invalidate(pattern="PROJ-*", category="issue")

# Invalidate all user data
cache.invalidate(category="user")
```

### Strategy 4: Cascade Invalidation

```python
def delete_project(client, cache, project_key):
    client.delete_project(project_key)
    cache.invalidate(pattern=f"{project_key}-*", category="issue")
    cache.invalidate(key=f"project:{project_key}", category="project")
```

## When to Invalidate

| Event | Action | Scope |
|-------|--------|-------|
| Issue created | Invalidate search results | Pattern |
| Issue updated | Invalidate specific issue | Key |
| Issue deleted | Invalidate issue + search | Key + pattern |
| Project updated | Invalidate project metadata | Key |
| Bulk operation | Invalidate entire category | Category |

## Best Practices

### Prefer TTL Over Manual Invalidation

Trust TTL expiration for most use cases. Manual invalidation adds complexity.

### Use Dry-Run for Pattern Invalidation

```bash
python cache_clear.py --pattern "PROJ-*" --category issue --dry-run
```

### Avoid Cache Stampede

Use locking when cache expires to prevent multiple threads from hitting the API simultaneously:

```python
import threading

locks = {}
lock_lock = threading.Lock()

def get_data(key):
    data = cache.get(key)
    if data is None:
        with lock_lock:
            if key not in locks:
                locks[key] = threading.Lock()
            lock = locks[key]

        with lock:
            data = cache.get(key)  # Double-check
            if data is None:
                data = fetch_from_api(key)
                cache.set(key, data)
    return data
```

## See Also

- [Cache Warming](CACHE_WARMING.md)
- [Common Pitfalls](COMMON_PITFALLS.md) - Cache stampede prevention
