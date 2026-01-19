# Common Pitfalls

Avoid these common mistakes when using JIRA APIs.

## Pitfall 1: Not Using Sessions

**Problem:** Creating new session for each request.
```python
for key in issue_keys:
    response = requests.get(f"{base_url}/rest/api/3/issue/{key}")
```

**Solution:** Reuse session for connection pooling.
```python
session = requests.Session()
for key in issue_keys:
    response = session.get(f"{base_url}/rest/api/3/issue/{key}")
```

**Impact:** 60% slower performance.

## Pitfall 2: Ignoring Rate Limits

**Problem:** Blasting requests without checking limits.

**Solution:** Monitor rate limits and back off when low.
```python
remaining = int(response.headers.get('X-RateLimit-Remaining', 1000))
if remaining < 100:
    time.sleep(60)
```

**Impact:** HTTP 429 errors, temporary API blocks.

## Pitfall 3: Not Handling Timeouts

**Problem:** No timeout - can hang forever.
```python
response = requests.get(url)  # Bad!
```

**Solution:** Always set timeout.
```python
response = requests.get(url, timeout=30)
```

**Impact:** Hung requests, resource exhaustion.

## Pitfall 4: Cache Stampede

**Problem:** All threads fetch same data when cache expires.

**Solution:** Use locking to prevent stampede.
```python
with lock:
    data = cache.get(key)
    if data is None:
        data = fetch_from_api(key)
        cache.set(key, data)
```

**Impact:** Thundering herd, API overload.

## Pitfall 5: Not Reading Response Bodies

**Problem:** Connection not released back to pool.
```python
response = session.get(url, stream=True)
# Connection not released!
```

**Solution:** Read body or close explicitly.
```python
response = session.get(url)
data = response.json()  # Releases connection
```

**Impact:** Connection pool exhaustion.

## Pitfall 6: Sharing Sessions Across Threads

**Problem:** `requests.Session` is not thread-safe.

**Solution:** Use thread-local sessions.
```python
thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session
```

**Impact:** Race conditions, corrupted requests.

## Pitfall 7: Over-Caching

**Problem:** Cache everything forever with long TTLs.

**Solution:** Use appropriate TTLs based on data type.
- Issues: 5 minutes
- Projects: 1 hour
- Fields: 1 day

**Impact:** Stale data, incorrect results.

## Pitfall 8: Not Using Bulk APIs

**Problem:** Fetching issues one by one.
```python
for i in range(1, 1001):
    issue = client.get_issue(f"PROJ-{i}")  # 500+ seconds!
```

**Solution:** Use JQL search.
```python
jql = "project = PROJ AND key >= PROJ-1 AND key <= PROJ-1000"
response = client.search_issues(jql, max_results=1000)  # 5-10 seconds
```

**Impact:** Slow performance, high API usage.

## Pitfall 9: Insufficient Error Handling

**Problem:** Fails on first error, no cleanup.

**Solution:** Handle errors gracefully.
```python
for key in keys:
    try:
        issue = client.get_issue(key)
        process(issue)
    except JiraError as e:
        logger.error(f"Failed: {key}: {e}")
```

**Impact:** Incomplete operations, data loss.

## Pitfall 10: Not Monitoring Cache Size

**Problem:** Cache grows without limit.

**Solution:** Monitor cache size and set limits.
```python
cache = JiraCache(max_size_mb=100)
stats = cache.get_stats()
if stats.total_size_bytes > 0.8 * cache.max_size:
    logger.warning("Cache at 80% capacity")
```

**Impact:** Disk space exhaustion, performance degradation.
