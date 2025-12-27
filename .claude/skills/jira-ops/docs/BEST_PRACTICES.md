# JIRA Operations Best Practices Guide

Comprehensive guide to optimizing JIRA API performance, implementing effective caching strategies, managing rate limits, and building robust operational workflows.

---

## Table of Contents

1. [API Rate Limiting Awareness](#api-rate-limiting-awareness)
2. [Request Batching Strategies](#request-batching-strategies)
3. [Cache Warming Techniques](#cache-warming-techniques)
4. [Cache Invalidation Patterns](#cache-invalidation-patterns)
5. [Performance Monitoring](#performance-monitoring)
6. [Error Handling & Retry Strategies](#error-handling--retry-strategies)
7. [Connection Pooling](#connection-pooling)
8. [Timeout Configuration](#timeout-configuration)
9. [Logging & Debugging](#logging--debugging)
10. [Health Checks & Diagnostics](#health-checks--diagnostics)
11. [Common Pitfalls](#common-pitfalls)
12. [Quick Reference Card](#quick-reference-card)

---

## API Rate Limiting Awareness

### Understanding JIRA Cloud Rate Limits

JIRA Cloud uses a **points-based model** to measure API usage. Instead of simply counting requests, each API call consumes points based on the work it performs—such as the amount of data returned or the complexity of the operation.

**Key Facts:**
- All endpoints are rate-limited to **1,000 requests per minute** per instance
- Total limit of **10,000 requests per minute** per instance
- Effective February 2, 2026, new points-based limits will be enforced
- Burst limits and quota limits are enforced independently

### Rate Limit Reference Table

| Limit Type | Window | Default Limit | Applies To |
|------------|--------|---------------|------------|
| **Burst Limit** | Per second | 1,000 requests/min | Prevents traffic spikes |
| **Quota Limit** | Per hour | Tier 1: Standard quota<br>Tier 2: Elevated (by request) | Sustained usage |
| **Total Instance Limit** | Per minute | 10,000 requests/min | Entire instance |
| **Points-based** | Per hour | Varies by operation | Complex operations cost more |

### Points-Based Model Details

| Operation Type | Point Cost | Examples |
|----------------|------------|----------|
| **Write Operations** | 1 point each | Create issue, update issue, delete issue |
| **Simple Reads** | 1 point | Get single issue, get project |
| **Complex Reads** | Variable (1-10+) | Search with many results, bulk operations |
| **Large Payloads** | Higher cost | Attachments, bulk exports |

**Example:**
- Creating 50 issues in a batch = 50 points (50 issues × 1 point each)
- Searching with 1,000 results may cost 10+ points

### Detecting Rate Limits

**HTTP 429 Response:**
```bash
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640995200
Retry-After: 60
```

**Response Headers:**
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `Retry-After`: Seconds to wait before retrying

### Best Practices for Rate Limit Management

**1. Monitor Rate Limit Headers**
```python
response = client.get('/rest/api/3/issue/PROJ-123')
remaining = response.headers.get('X-RateLimit-Remaining')
if remaining and int(remaining) < 100:
    print(f"Warning: Only {remaining} requests remaining")
```

**2. Implement Exponential Backoff**
```python
# Already implemented in jira_client.py
retry_strategy = Retry(
    total=3,
    backoff_factor=2.0,  # 1s, 2s, 4s delays
    status_forcelist=[429, 500, 502, 503, 504]
)
```

**3. Batch Related Requests**
- Use JQL search instead of fetching issues individually
- Combine field updates into single update operations
- Leverage bulk APIs when available

**4. Cache Aggressively**
- Cache metadata (projects, users, fields) for hours
- Cache issue data for minutes
- Use cache to avoid redundant API calls

**5. Spread Requests Over Time**
```python
# Don't: Blast 1000 requests at once
for key in issue_keys:
    issue = client.get_issue(key)

# Do: Batch with controlled concurrency
batcher = RequestBatcher(client, max_concurrent=10)
for key in issue_keys:
    batcher.add("GET", f"/rest/api/3/issue/{key}")
results = batcher.execute_sync()
```

**6. Request Tier 2 Access for High-Volume Apps**
- Tier 1: Default for all apps
- Tier 2: Elevated quotas (requires review and approval)
- Contact Atlassian support with usage patterns

---

## Request Batching Strategies

### When to Use Request Batching

**Good Candidates:**
- Fetching multiple issues (10+)
- Bulk updates to issue fields
- Loading related data (issues + comments + worklogs)
- Exporting large datasets

**Poor Candidates:**
- Single issue operations
- Time-critical operations requiring immediate response
- Operations with complex dependencies

### Using RequestBatcher

**Basic Usage:**
```python
from request_batcher import RequestBatcher

batcher = RequestBatcher(client, max_concurrent=10)

# Add requests
id1 = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
id2 = batcher.add("GET", "/rest/api/3/issue/PROJ-2")
id3 = batcher.add("GET", "/rest/api/3/issue/PROJ-3")

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

**Convenience Function:**
```python
from request_batcher import batch_fetch_issues

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

### Batching Best Practices

**1. Choose Appropriate Concurrency**

| Scenario | Recommended max_concurrent |
|----------|---------------------------|
| Small batches (< 50 requests) | 5-10 |
| Medium batches (50-500) | 10-20 |
| Large batches (500+) | 20-50 |
| Rate limit sensitive | 5 |

**2. Handle Partial Failures**
```python
results = batcher.execute_sync()

successes = [r for r in results.values() if r.success]
failures = [r for r in results.values() if not r.success]

print(f"Succeeded: {len(successes)}, Failed: {len(failures)}")

# Retry failures with exponential backoff
if failures:
    retry_batcher = RequestBatcher(client, max_concurrent=5)
    for result in failures:
        retry_batcher.add(result.method, result.endpoint)
```

**3. Monitor Performance**
```python
results = batcher.execute_sync()

total_time = sum(r.duration_ms for r in results.values())
avg_time = total_time / len(results)

print(f"Average request time: {avg_time:.2f}ms")
print(f"Total time: {total_time/1000:.2f}s")
```

**4. Batch Size Optimization**

| Batch Size | Strategy |
|------------|----------|
| 1-10 | Sequential requests acceptable |
| 10-100 | Use batching with max_concurrent=10 |
| 100-1000 | Use batching with max_concurrent=20, consider pagination |
| 1000+ | Split into chunks, process over multiple hours |

### Advanced Batching Patterns

**Pattern 1: Dependency Batching**
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
        comment_batcher.add(
            "GET",
            f"/rest/api/3/issue/{key}/comment"
        )
comments = comment_batcher.execute_sync()
```

**Pattern 2: Mixed Operation Batching**
```python
batcher = RequestBatcher(client, max_concurrent=10)

# Mix reads and writes
batcher.add("GET", "/rest/api/3/issue/PROJ-1")
batcher.add("POST", "/rest/api/3/issue", data=new_issue_data)
batcher.add("PUT", "/rest/api/3/issue/PROJ-2", data=update_data)

results = batcher.execute_sync()
```

**Pattern 3: Paginated Batch Fetching**
```python
def batch_fetch_all_issues(client, jql, max_results=100):
    """Fetch all issues matching JQL using batching."""
    total = None
    start_at = 0
    all_issues = []

    while total is None or start_at < total:
        response = client.search_issues(
            jql,
            start_at=start_at,
            max_results=max_results
        )

        total = response['total']
        all_issues.extend(response['issues'])
        start_at += max_results

        print(f"Fetched {len(all_issues)}/{total} issues")

    return all_issues
```

---

## Cache Warming Techniques

### Why Warm the Cache?

**Benefits:**
- Reduce initial latency for common operations
- Prevent cache stampede during peak usage
- Improve user experience with faster responses
- Reduce API calls during production usage

**When to Warm:**
- Application startup
- After cache clear operations
- Before scheduled high-traffic periods
- After deploying to new environment

### Cache Warming Strategies

**Strategy 1: Preload Metadata**
```bash
# Warm projects and fields (rarely change, high value)
python cache_warm.py --projects --fields --profile production
```

**Strategy 2: Warm by Usage Pattern**
```python
# Identify most-accessed data from logs
# Warm cache with that data

from cache import JiraCache
from config_manager import get_jira_client

cache = JiraCache()
client = get_jira_client()

# Warm top 100 most accessed issues
top_issues = ["PROJ-1", "PROJ-42", "PROJ-100", ...]  # From analytics
for key in top_issues:
    issue = client.get_issue(key)
    cache.set(key, issue, category="issue")
```

**Strategy 3: Warm by Project**
```python
def warm_project_cache(client, cache, project_key):
    """Warm cache with recent issues from project."""
    # Get project metadata
    project = client.get_project(project_key)
    cache.set(f"project:{project_key}", project, category="project")

    # Get recent issues (last 30 days)
    jql = f"project = {project_key} AND updated >= -30d ORDER BY updated DESC"
    issues = client.search_issues(jql, max_results=100)

    for issue in issues['issues']:
        key = issue['key']
        cache.set(key, issue, category="issue")

    print(f"Warmed {len(issues['issues'])} issues for {project_key}")
```

**Strategy 4: Scheduled Warming**
```bash
# Cron job to warm cache daily at 6 AM
0 6 * * * /usr/bin/python3 /path/to/cache_warm.py --all --profile production
```

### Cache Warming Best Practices

**1. Prioritize by Access Frequency**

| Priority | Data Type | TTL | Warm Frequency |
|----------|-----------|-----|----------------|
| High | Projects, fields, users | 1 hour - 1 day | Daily |
| Medium | Recent issues (last 7 days) | 5 minutes | Hourly |
| Low | Old issues, archived data | 1 hour | On-demand |

**2. Warm During Off-Peak Hours**
- Avoid warming during business hours (9 AM - 5 PM)
- Schedule for early morning (5-7 AM)
- Respect rate limits during warming

**3. Monitor Warming Performance**
```python
import time

start_time = time.time()

# Warm cache
python cache_warm.py --all --verbose

elapsed = time.time() - start_time
print(f"Cache warming took {elapsed:.2f}s")
```

**4. Incremental Warming**
```python
# Don't warm everything at once
# Warm in stages with delays

# Stage 1: Critical metadata
warm_projects()
time.sleep(10)

# Stage 2: User data
warm_users()
time.sleep(10)

# Stage 3: Recent issues
warm_recent_issues()
```

**5. Verify Cache After Warming**
```bash
# Check cache status after warming
python cache_warm.py --all
python cache_status.py

# Expected output:
# Cache Statistics:
#   Total Size: 45 MB / 100 MB
#   Entries: 5,234
#   Hit Rate: N/A (no hits yet)
```

---

## Cache Invalidation Patterns

### Cache Invalidation Strategies

**Strategy 1: Time-Based (TTL)**
```python
# Already built into JiraCache
cache.set(key, value, category="issue")  # Expires in 5 minutes
cache.set(key, value, category="project")  # Expires in 1 hour
cache.set(key, value, category="field")  # Expires in 1 day

# Custom TTL
from datetime import timedelta
cache.set(key, value, category="custom", ttl=timedelta(minutes=30))
```

**Strategy 2: Event-Based Invalidation**
```python
def update_issue(client, cache, issue_key, update_data):
    """Update issue and invalidate cache."""
    # Update in JIRA
    client.update_issue(issue_key, update_data)

    # Invalidate cache
    cache.invalidate(key=issue_key, category="issue")

    # Optionally: Refresh cache immediately
    updated_issue = client.get_issue(issue_key)
    cache.set(issue_key, updated_issue, category="issue")
```

**Strategy 3: Pattern-Based Invalidation**
```python
# Invalidate all issues in a project
cache.invalidate(pattern="PROJ-*", category="issue")

# Invalidate all user data
cache.invalidate(category="user")

# Invalidate specific pattern
cache.invalidate(pattern="project:*:metadata", category="project")
```

**Strategy 4: Cascade Invalidation**
```python
def delete_project(client, cache, project_key):
    """Delete project and cascade invalidate."""
    # Delete in JIRA
    client.delete_project(project_key)

    # Cascade invalidate
    cache.invalidate(pattern=f"{project_key}-*", category="issue")
    cache.invalidate(key=f"project:{project_key}", category="project")
    cache.invalidate(pattern=f"search:*project={project_key}*", category="search")
```

### When to Invalidate

| Event | Invalidation Action | Scope |
|-------|---------------------|-------|
| Issue created | Invalidate search results | Pattern: `search:*project=PROJ*` |
| Issue updated | Invalidate specific issue | Key: `PROJ-123` |
| Issue deleted | Invalidate issue + search | Key + pattern |
| Project updated | Invalidate project metadata | Key: `project:PROJ` |
| User updated | Invalidate user data | Key: `user:accountId` |
| Field created/updated | Invalidate all field data | Category: `field` |
| Bulk operation | Invalidate entire category | Category: `issue` |

### Invalidation Best Practices

**1. Prefer TTL Over Manual Invalidation**
```python
# Don't: Manually track and invalidate
def get_issue(key):
    issue = cache.get(key, category="issue")
    if issue is None:
        issue = client.get_issue(key)
        cache.set(key, issue, category="issue")
    # Need to manually invalidate on every update!
    return issue

# Do: Trust TTL
def get_issue(key):
    issue = cache.get(key, category="issue")  # Auto-expires in 5 min
    if issue is None:
        issue = client.get_issue(key)
        cache.set(key, issue, category="issue")
    return issue
```

**2. Use Dry-Run for Pattern Invalidation**
```bash
# Preview what will be invalidated
python cache_clear.py --pattern "PROJ-*" --category issue --dry-run

# Output:
# Would clear 234 entries matching pattern "PROJ-*" in category "issue"

# Then execute
python cache_clear.py --pattern "PROJ-*" --category issue --force
```

**3. Log Invalidation Events**
```python
import logging

logger = logging.getLogger(__name__)

def invalidate_with_logging(cache, **kwargs):
    """Invalidate cache with logging."""
    before_stats = cache.get_stats()
    count = cache.invalidate(**kwargs)
    after_stats = cache.get_stats()

    logger.info(
        f"Invalidated {count} entries. "
        f"Cache size: {before_stats.entry_count} → {after_stats.entry_count}"
    )
```

**4. Avoid Cache Stampede**
```python
# Problem: Cache expires, 100 requests hit API at once
def get_issue_bad(key):
    issue = cache.get(key, category="issue")
    if issue is None:
        issue = client.get_issue(key)  # Stampede!
        cache.set(key, issue, category="issue")
    return issue

# Solution: Use locking or stale-while-revalidate
import threading

locks = {}
locks_lock = threading.Lock()

def get_issue_good(key):
    issue = cache.get(key, category="issue")
    if issue is None:
        # Acquire lock for this key
        with locks_lock:
            if key not in locks:
                locks[key] = threading.Lock()
            lock = locks[key]

        with lock:
            # Double-check cache after acquiring lock
            issue = cache.get(key, category="issue")
            if issue is None:
                issue = client.get_issue(key)
                cache.set(key, issue, category="issue")

    return issue
```

---

## Performance Monitoring

### Key Performance Metrics

| Metric | Target | Critical Threshold | How to Measure |
|--------|--------|-------------------|----------------|
| **Cache Hit Rate** | > 70% | < 50% | `cache.get_stats().hit_rate` |
| **Average Request Time** | < 500ms | > 2000ms | `result.duration_ms` |
| **Rate Limit Remaining** | > 20% | < 5% | `X-RateLimit-Remaining` header |
| **Cache Size** | < 80% max | > 95% max | `cache.get_stats().total_size_bytes` |
| **Error Rate** | < 1% | > 5% | Failed requests / total requests |

### Monitoring Cache Performance

**Check Cache Hit Rate:**
```bash
python cache_status.py

# Output:
# Cache Statistics:
#   Total Size: 12.5 MB / 100 MB
#   Entries: 1,234
#   Hit Rate: 78% (1000 hits, 234 misses)
```

**Programmatic Monitoring:**
```python
from cache import JiraCache

cache = JiraCache()
stats = cache.get_stats()

print(f"Hit Rate: {stats.hit_rate * 100:.1f}%")
print(f"Total Entries: {stats.entry_count}")
print(f"Size: {stats.total_size_bytes / 1024 / 1024:.2f} MB")

# Alert if hit rate is low
if stats.hit_rate < 0.5:
    print("WARNING: Cache hit rate below 50%")
```

### Monitoring API Performance

**Track Request Timing:**
```python
import time

start = time.time()
issue = client.get_issue("PROJ-123")
elapsed_ms = (time.time() - start) * 1000

print(f"Request took {elapsed_ms:.2f}ms")

if elapsed_ms > 2000:
    print("WARNING: Slow API response")
```

**Monitor Rate Limits:**
```python
def get_with_rate_limit_check(client, endpoint):
    """Get with rate limit monitoring."""
    response = client.session.get(f"{client.base_url}{endpoint}")

    remaining = response.headers.get('X-RateLimit-Remaining')
    limit = response.headers.get('X-RateLimit-Limit')

    if remaining and limit:
        remaining_pct = int(remaining) / int(limit)
        if remaining_pct < 0.2:
            print(f"WARNING: Only {remaining}/{limit} requests remaining")

    return response.json()
```

### Performance Dashboards

**Create Daily Performance Report:**
```python
def generate_performance_report(cache):
    """Generate daily performance report."""
    stats = cache.get_stats()

    report = f"""
    === Daily Performance Report ===
    Date: {datetime.now().strftime('%Y-%m-%d')}

    Cache Performance:
      - Hit Rate: {stats.hit_rate * 100:.1f}%
      - Total Hits: {stats.hits:,}
      - Total Misses: {stats.misses:,}
      - Total Entries: {stats.entry_count:,}
      - Cache Size: {stats.total_size_bytes / 1024 / 1024:.2f} MB

    By Category:
    """

    for category, data in stats.by_category.items():
        report += f"\n      {category}: {data['count']:,} entries, "
        report += f"{data['size_bytes'] / 1024 / 1024:.2f} MB"

    return report
```

### Setting Up Alerts

**Cache Hit Rate Alert:**
```python
def check_cache_health(cache, threshold=0.5):
    """Alert if cache hit rate is below threshold."""
    stats = cache.get_stats()

    if stats.hit_rate < threshold:
        send_alert(
            level="WARNING",
            message=f"Cache hit rate is {stats.hit_rate * 100:.1f}% "
                   f"(threshold: {threshold * 100:.1f}%)"
        )
```

**Rate Limit Alert:**
```python
def check_rate_limit_health(client, threshold=0.2):
    """Alert if approaching rate limit."""
    # Make a cheap API call to check headers
    response = client.session.get(f"{client.base_url}/rest/api/3/myself")

    remaining = int(response.headers.get('X-RateLimit-Remaining', 999999))
    limit = int(response.headers.get('X-RateLimit-Limit', 1000000))

    if remaining / limit < threshold:
        send_alert(
            level="CRITICAL",
            message=f"Rate limit at {remaining}/{limit} "
                   f"({remaining/limit * 100:.1f}%)"
        )
```

---

## Error Handling & Retry Strategies

### Built-in Retry Logic

**JiraClient Automatic Retry:**
```python
# From jira_client.py
retry_strategy = Retry(
    total=3,                     # Max 3 retries
    backoff_factor=2.0,          # Exponential backoff: 1s, 2s, 4s
    status_forcelist=[429, 500, 502, 503, 504],  # Retry on these codes
    allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
)
```

**Retry Timeline:**
- Attempt 1: Immediate
- Attempt 2: After 1 second (2^0 * 2.0)
- Attempt 3: After 2 seconds (2^1 * 2.0)
- Attempt 4: After 4 seconds (2^2 * 2.0)

### Custom Retry Strategies

**Retry with Custom Backoff:**
```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=60.0):
    """Decorator for retry with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except JiraError as e:
                    if attempt == max_retries:
                        raise

                    # Only retry on transient errors
                    if e.status_code not in [429, 500, 502, 503, 504]:
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)

                    # Add jitter to prevent thundering herd
                    delay *= (0.5 + random.random())

                    print(f"Retry {attempt + 1}/{max_retries} after {delay:.2f}s")
                    time.sleep(delay)

            return None
        return wrapper
    return decorator

@retry_with_backoff(max_retries=5, base_delay=2.0)
def fetch_critical_data(client, issue_key):
    """Fetch critical data with aggressive retry."""
    return client.get_issue(issue_key)
```

### Error Handling Patterns

**Pattern 1: Fail Fast**
```python
# For non-critical operations, fail immediately
try:
    optional_data = client.get_issue_comments(key)
except JiraError as e:
    print(f"Warning: Could not fetch comments: {e}")
    optional_data = []
```

**Pattern 2: Retry with Circuit Breaker**
```python
class CircuitBreaker:
    """Prevent cascading failures."""
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"

            raise

# Usage
breaker = CircuitBreaker(failure_threshold=5, timeout=60)
try:
    issue = breaker.call(client.get_issue, "PROJ-123")
except Exception as e:
    print(f"Circuit breaker prevented call: {e}")
```

**Pattern 3: Fallback Strategy**
```python
def get_issue_with_fallback(client, cache, issue_key):
    """Try cache, then API, then stale cache, then error."""
    # Try cache first
    issue = cache.get(issue_key, category="issue")
    if issue:
        return issue

    # Try API
    try:
        issue = client.get_issue(issue_key)
        cache.set(issue_key, issue, category="issue")
        return issue
    except JiraError as e:
        print(f"API error: {e}")

    # Try stale cache (ignoring TTL)
    # This requires custom cache implementation
    stale_issue = cache.get_stale(issue_key, category="issue")
    if stale_issue:
        print("Warning: Using stale cached data")
        return stale_issue

    # No fallback available
    raise Exception(f"Could not fetch {issue_key}")
```

### Error Classification

| Error Code | Meaning | Action |
|------------|---------|--------|
| **400** | Bad Request | Don't retry, fix request |
| **401** | Unauthorized | Check credentials, don't retry |
| **403** | Forbidden | Check permissions, don't retry |
| **404** | Not Found | Don't retry, handle gracefully |
| **429** | Rate Limited | **Retry with backoff** |
| **500** | Server Error | **Retry with backoff** |
| **502** | Bad Gateway | **Retry with backoff** |
| **503** | Service Unavailable | **Retry with backoff** |
| **504** | Gateway Timeout | **Retry with backoff** |

---

## Connection Pooling

### Understanding Connection Pooling

**What is Connection Pooling?**
- Reuses TCP connections across multiple HTTP requests
- Eliminates overhead of establishing new connections
- Significantly improves performance for multiple requests to same host

**Performance Impact:**
- Up to 60% reduction in per-request latency
- Eliminates TCP handshake overhead (3-way handshake)
- Reuses TLS/SSL sessions

### Built-in Connection Pooling

**JiraClient Configuration:**
```python
# From jira_client.py - already configured!
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)
```

**Default Pool Settings:**
- `pool_connections`: 10 (number of connection pools to cache)
- `pool_maxsize`: 10 (connections per pool)
- `pool_block`: False (don't block waiting for connection)

### Custom Connection Pool Configuration

**For High-Volume Applications:**
```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Create custom adapter with larger pool
adapter = HTTPAdapter(
    pool_connections=20,    # Cache connections to 20 different hosts
    pool_maxsize=50,        # Max 50 connections per host
    pool_block=True,        # Block if pool exhausted (safer)
    max_retries=retry_strategy
)

session = requests.Session()
session.mount("https://", adapter)
session.mount("http://", adapter)
```

### Pool Configuration Guidelines

| Scenario | pool_connections | pool_maxsize | Reasoning |
|----------|------------------|--------------|-----------|
| **Single JIRA instance** | 1-5 | 20-50 | One host, many connections |
| **Multiple JIRA instances** | 10-20 | 10-20 | Many hosts, fewer per host |
| **Low concurrency** | 1 | 10 | Default is fine |
| **High concurrency (50+ threads)** | 5-10 | 50-100 | Support many parallel requests |
| **Batch operations** | 5 | 50 | High parallelism to one host |

### Connection Pool Best Practices

**1. Reuse Sessions**
```python
# Don't: Create new session per request
def get_issue_bad(issue_key):
    session = requests.Session()  # New pool each time!
    response = session.get(f"{base_url}/rest/api/3/issue/{issue_key}")
    return response.json()

# Do: Reuse session
session = requests.Session()  # Created once

def get_issue_good(issue_key):
    response = session.get(f"{base_url}/rest/api/3/issue/{issue_key}")
    return response.json()
```

**2. Read Response Bodies**
```python
# Don't: Leave connections hanging
response = session.get(url, stream=True)
# Connection not released if body not read!

# Do: Read the body or close explicitly
response = session.get(url, stream=True)
response.close()  # Release connection

# Or better: Read the body
response = session.get(url)
data = response.json()  # Body read, connection released
```

**3. Thread-Safe Sessions**
```python
import threading

# Don't: Share session across threads (not thread-safe!)
session = requests.Session()

def worker(issue_key):
    return session.get(f"{base_url}/rest/api/3/issue/{issue_key}")

threads = [threading.Thread(target=worker, args=(key,)) for key in keys]

# Do: Use thread-local sessions
thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session

def worker(issue_key):
    session = get_session()
    return session.get(f"{base_url}/rest/api/3/issue/{issue_key}")
```

**4. Monitor Pool Utilization**
```python
# Access pool statistics (requires accessing internal HTTPAdapter)
adapter = session.get_adapter("https://")
pool_manager = adapter.poolmanager

# Note: These are internal APIs, may change
print(f"Pools: {pool_manager.pools}")
print(f"Connection pools: {len(pool_manager.pools)}")
```

**5. Configure for Workload**
```python
# For batch processing (many requests, high concurrency)
batch_adapter = HTTPAdapter(
    pool_connections=5,
    pool_maxsize=50,
    pool_block=True
)

# For interactive requests (low concurrency, quick response)
interactive_adapter = HTTPAdapter(
    pool_connections=5,
    pool_maxsize=10,
    pool_block=False
)
```

---

## Timeout Configuration

### Why Timeouts Matter

**Without Timeouts:**
- Requests can hang indefinitely
- Threads/resources tied up
- Cascading failures
- Poor user experience

**With Timeouts:**
- Fail fast on slow responses
- Free up resources
- Prevent cascading failures
- Predictable behavior

### Timeout Types

**Connect Timeout:**
- Time to establish connection
- Typically 3-10 seconds
- Should be multiple of 3 (TCP retransmission window)

**Read Timeout:**
- Time waiting for server response
- Typically 10-60 seconds
- Depends on operation complexity

### Built-in Timeout Configuration

**JiraClient Default:**
```python
# From jira_client.py
def __init__(self, base_url, email, api_token, timeout=30):
    self.timeout = timeout  # 30 seconds default
```

**Request-Level Timeout:**
```python
# Single timeout value (applies to both connect and read)
response = client.session.get(url, timeout=30)

# Tuple: (connect_timeout, read_timeout)
response = client.session.get(url, timeout=(10, 60))
```

### Timeout Best Practices

**1. Always Set Timeouts**
```python
# Don't: No timeout (can hang forever!)
response = requests.get(url)

# Do: Set appropriate timeout
response = requests.get(url, timeout=30)
```

**2. Choose Appropriate Values**

| Operation Type | Connect Timeout | Read Timeout | Total |
|----------------|----------------|--------------|-------|
| **Get single issue** | 10s | 20s | 30s |
| **Search (small)** | 10s | 30s | 40s |
| **Search (large)** | 10s | 60s | 70s |
| **Create issue** | 10s | 20s | 30s |
| **Bulk export** | 10s | 120s | 130s |
| **Upload attachment** | 10s | 60s | 70s |

**3. Handle Timeout Errors**
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

**4. Progressive Timeouts**
```python
def get_with_progressive_timeout(client, endpoint, base_timeout=30):
    """Try with increasing timeouts."""
    timeouts = [base_timeout, base_timeout * 2, base_timeout * 3]

    for attempt, timeout in enumerate(timeouts):
        try:
            return client.get(endpoint, timeout=timeout)
        except requests.exceptions.Timeout:
            if attempt == len(timeouts) - 1:
                raise
            print(f"Timeout after {timeout}s, retrying with {timeouts[attempt+1]}s")
```

**5. Environment-Specific Timeouts**
```python
import os

# Production: Shorter timeouts (fail fast)
if os.getenv("ENV") == "production":
    DEFAULT_TIMEOUT = 30

# Development: Longer timeouts (debugging)
else:
    DEFAULT_TIMEOUT = 120

client = JiraClient(base_url, email, token, timeout=DEFAULT_TIMEOUT)
```

---

## Logging & Debugging

### Logging Levels

| Level | Usage | Example |
|-------|-------|---------|
| **DEBUG** | Detailed diagnostic info | "Cache hit for PROJ-123" |
| **INFO** | General informational events | "Fetched 100 issues in 2.5s" |
| **WARNING** | Potentially harmful situations | "Cache hit rate below 50%" |
| **ERROR** | Error events (might continue) | "Failed to fetch PROJ-123" |
| **CRITICAL** | Severe errors (might abort) | "Rate limit exceeded, pausing" |

### Setting Up Logging

**Basic Logging Setup:**
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/jira-ops.log'),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger(__name__)
```

**Advanced Logging Configuration:**
```python
import logging
import logging.handlers

# Create logger
logger = logging.getLogger('jira_ops')
logger.setLevel(logging.DEBUG)

# Console handler (INFO and above)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)

# File handler (DEBUG and above, rotated)
file_handler = logging.handlers.RotatingFileHandler(
    '/var/log/jira-ops.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(file_formatter)

# Add handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)
```

### What to Log

**1. API Requests**
```python
logger.debug(f"GET /rest/api/3/issue/{issue_key}")
logger.info(f"Fetched issue {issue_key} in {elapsed_ms:.2f}ms")
```

**2. Cache Operations**
```python
logger.debug(f"Cache hit for {key} in category {category}")
logger.debug(f"Cache miss for {key}, fetching from API")
logger.info(f"Cache hit rate: {stats.hit_rate * 100:.1f}%")
```

**3. Errors and Retries**
```python
logger.error(f"Failed to fetch {issue_key}: {error}")
logger.warning(f"Retry {attempt}/{max_retries} after {delay}s")
```

**4. Performance Metrics**
```python
logger.info(f"Batch completed: {success_count} successes, {failure_count} failures")
logger.info(f"Average request time: {avg_time_ms:.2f}ms")
```

**5. Rate Limiting**
```python
logger.warning(f"Rate limit: {remaining}/{limit} requests remaining")
logger.critical(f"Rate limit exceeded, pausing for {retry_after}s")
```

### Debug Mode

**Enable Debug Logging:**
```bash
# Environment variable
export DEBUG=1
python cache_warm.py --all

# Or via command-line flag
python cache_warm.py --all --verbose
```

**Debug Logging in Code:**
```python
import os

if os.getenv("DEBUG"):
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
```

### Request Logging

**Log HTTP Requests:**
```python
import logging
import http.client

# Enable HTTP debug logging
http.client.HTTPConnection.debuglevel = 1

# Configure logging for requests
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
```

**Custom Request Logging:**
```python
class LoggingJiraClient(JiraClient):
    """JiraClient with request/response logging."""

    def get(self, endpoint, **kwargs):
        logger.debug(f"GET {endpoint} params={kwargs.get('params')}")
        start = time.time()

        try:
            result = super().get(endpoint, **kwargs)
            elapsed = (time.time() - start) * 1000
            logger.info(f"GET {endpoint} completed in {elapsed:.2f}ms")
            return result
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.error(f"GET {endpoint} failed after {elapsed:.2f}ms: {e}")
            raise
```

### Structured Logging

**JSON Logging for Log Aggregation:**
```python
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
        }

        # Add extra fields
        if hasattr(record, 'issue_key'):
            log_data['issue_key'] = record.issue_key
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms

        return json.dumps(log_data)

# Use JSON formatter
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger = logging.getLogger('jira_ops')
logger.addHandler(handler)

# Log with extra context
logger.info("Fetched issue", extra={'issue_key': 'PROJ-123', 'duration_ms': 245})
```

---

## Health Checks & Diagnostics

### Health Check Endpoints

**Basic Health Check:**
```python
def check_jira_health(client):
    """Check if JIRA is accessible."""
    try:
        # Try to get current user (lightweight operation)
        response = client.session.get(
            f"{client.base_url}/rest/api/3/myself",
            timeout=10
        )

        if response.status_code == 200:
            return {
                'status': 'healthy',
                'message': 'JIRA is accessible',
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
        else:
            return {
                'status': 'unhealthy',
                'message': f'HTTP {response.status_code}',
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': str(e)
        }
```

**Comprehensive Health Check:**
```python
def comprehensive_health_check(client, cache):
    """Perform comprehensive health check."""
    checks = {}

    # Check JIRA connectivity
    checks['jira_connectivity'] = check_jira_health(client)

    # Check cache health
    cache_stats = cache.get_stats()
    checks['cache_health'] = {
        'status': 'healthy' if cache_stats.hit_rate > 0.5 else 'degraded',
        'hit_rate': f"{cache_stats.hit_rate * 100:.1f}%",
        'entry_count': cache_stats.entry_count,
        'size_mb': cache_stats.total_size_bytes / 1024 / 1024
    }

    # Check rate limit status
    try:
        response = client.session.get(f"{client.base_url}/rest/api/3/myself")
        remaining = int(response.headers.get('X-RateLimit-Remaining', 999))
        limit = int(response.headers.get('X-RateLimit-Limit', 1000))

        checks['rate_limit'] = {
            'status': 'healthy' if remaining / limit > 0.2 else 'warning',
            'remaining': remaining,
            'limit': limit,
            'percent_remaining': f"{remaining / limit * 100:.1f}%"
        }
    except Exception as e:
        checks['rate_limit'] = {
            'status': 'unknown',
            'error': str(e)
        }

    # Overall status
    statuses = [check.get('status') for check in checks.values()]
    if 'unhealthy' in statuses:
        overall_status = 'unhealthy'
    elif 'degraded' in statuses or 'warning' in statuses:
        overall_status = 'degraded'
    else:
        overall_status = 'healthy'

    return {
        'overall_status': overall_status,
        'checks': checks,
        'timestamp': datetime.now().isoformat()
    }
```

### Diagnostic Scripts

**Connection Diagnostic:**
```bash
#!/bin/bash
# diagnose_connection.sh

echo "=== JIRA Connection Diagnostic ==="
echo ""

echo "1. Checking environment variables..."
if [ -z "$JIRA_API_TOKEN" ]; then
    echo "   ❌ JIRA_API_TOKEN not set"
else
    echo "   ✓ JIRA_API_TOKEN set"
fi

if [ -z "$JIRA_EMAIL" ]; then
    echo "   ❌ JIRA_EMAIL not set"
else
    echo "   ✓ JIRA_EMAIL set"
fi

if [ -z "$JIRA_SITE_URL" ]; then
    echo "   ❌ JIRA_SITE_URL not set"
else
    echo "   ✓ JIRA_SITE_URL set"
    echo "   URL: $JIRA_SITE_URL"
fi

echo ""
echo "2. Checking network connectivity..."
if curl -s -o /dev/null -w "%{http_code}" "$JIRA_SITE_URL" | grep -q "200\|401"; then
    echo "   ✓ JIRA instance is reachable"
else
    echo "   ❌ Cannot reach JIRA instance"
fi

echo ""
echo "3. Testing API authentication..."
python -c "
from config_manager import get_jira_client
try:
    client = get_jira_client()
    myself = client.get('/rest/api/3/myself')
    print('   ✓ Authentication successful')
    print(f'   User: {myself[\"displayName\"]} ({myself[\"emailAddress\"]})')
except Exception as e:
    print(f'   ❌ Authentication failed: {e}')
"

echo ""
echo "4. Checking cache status..."
python cache_status.py --json 2>/dev/null | python -m json.tool || echo "   ❌ Cache not accessible"
```

**Performance Diagnostic:**
```python
def diagnose_performance(client, cache):
    """Diagnose performance issues."""
    print("=== Performance Diagnostic ===\n")

    # Test API latency
    print("1. Testing API latency...")
    latencies = []
    for i in range(5):
        start = time.time()
        try:
            client.session.get(f"{client.base_url}/rest/api/3/myself")
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            print(f"   Attempt {i+1}: {latency:.2f}ms")
        except Exception as e:
            print(f"   Attempt {i+1}: ERROR - {e}")

    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        print(f"   Average: {avg_latency:.2f}ms")

        if avg_latency > 1000:
            print("   ⚠ High latency detected (>1000ms)")
        else:
            print("   ✓ Latency within acceptable range")

    # Test cache performance
    print("\n2. Testing cache performance...")
    cache_stats = cache.get_stats()
    print(f"   Hit rate: {cache_stats.hit_rate * 100:.1f}%")
    print(f"   Entries: {cache_stats.entry_count:,}")
    print(f"   Size: {cache_stats.total_size_bytes / 1024 / 1024:.2f} MB")

    if cache_stats.hit_rate < 0.5:
        print("   ⚠ Low cache hit rate (<50%)")
        print("   Recommendation: Warm cache or increase TTL")
    else:
        print("   ✓ Cache performing well")

    # Test request batching
    print("\n3. Testing request batching...")
    test_keys = ["PROJ-1", "PROJ-2", "PROJ-3"]  # Use real keys

    # Sequential
    start = time.time()
    for key in test_keys:
        try:
            client.get_issue(key)
        except:
            pass
    sequential_time = time.time() - start
    print(f"   Sequential: {sequential_time:.2f}s")

    # Batched
    start = time.time()
    batcher = RequestBatcher(client, max_concurrent=3)
    for key in test_keys:
        batcher.add("GET", f"/rest/api/3/issue/{key}")
    batcher.execute_sync()
    batched_time = time.time() - start
    print(f"   Batched: {batched_time:.2f}s")

    improvement = (1 - batched_time / sequential_time) * 100
    print(f"   Improvement: {improvement:.1f}%")
```

### Monitoring Scripts

**Create Health Check Cron Job:**
```bash
# Add to crontab: */5 * * * *
#!/bin/bash
# health_check_cron.sh

OUTPUT=$(python -c "
from config_manager import get_jira_client
from cache import JiraCache
import json

client = get_jira_client()
cache = JiraCache()

# Run health check
result = comprehensive_health_check(client, cache)
print(json.dumps(result, indent=2))
")

# Log to file
echo "$OUTPUT" >> /var/log/jira-health.log

# Alert if unhealthy
if echo "$OUTPUT" | grep -q '"overall_status": "unhealthy"'; then
    echo "JIRA Health Check Failed" | mail -s "Alert: JIRA Unhealthy" admin@company.com
fi
```

---

## Common Pitfalls

### Pitfall 1: Not Using Sessions

**Problem:**
```python
# Creates new session for each request!
for key in issue_keys:
    response = requests.get(f"{base_url}/rest/api/3/issue/{key}")
```

**Solution:**
```python
# Reuse session for connection pooling
session = requests.Session()
for key in issue_keys:
    response = session.get(f"{base_url}/rest/api/3/issue/{key}")
```

**Impact:** 60% slower performance, higher latency

---

### Pitfall 2: Ignoring Rate Limits

**Problem:**
```python
# Blast 10,000 requests without checking rate limits
for i in range(10000):
    client.get_issue(f"PROJ-{i}")
# HTTP 429 errors start appearing!
```

**Solution:**
```python
# Monitor rate limits and back off
for i in range(10000):
    # Check rate limit before each batch
    if i % 100 == 0:
        response = client.session.get(f"{base_url}/rest/api/3/myself")
        remaining = int(response.headers.get('X-RateLimit-Remaining', 1000))

        if remaining < 100:
            print(f"Rate limit low ({remaining}), sleeping...")
            time.sleep(60)

    client.get_issue(f"PROJ-{i}")
```

**Impact:** HTTP 429 errors, temporary API blocks

---

### Pitfall 3: Not Handling Timeouts

**Problem:**
```python
# No timeout - can hang forever!
response = requests.get(url)
```

**Solution:**
```python
# Always set timeout
response = requests.get(url, timeout=30)
```

**Impact:** Hung requests, resource exhaustion

---

### Pitfall 4: Cache Stampede

**Problem:**
```python
# 100 threads all fetch same data when cache expires
def get_data(key):
    data = cache.get(key)
    if data is None:
        # All 100 threads hit this simultaneously!
        data = expensive_api_call(key)
        cache.set(key, data)
    return data
```

**Solution:**
```python
# Use locking to prevent stampede
import threading

locks = {}
lock_lock = threading.Lock()

def get_data(key):
    data = cache.get(key)
    if data is None:
        # Get or create lock for this key
        with lock_lock:
            if key not in locks:
                locks[key] = threading.Lock()
            lock = locks[key]

        # Only one thread fetches, others wait
        with lock:
            # Double-check cache after acquiring lock
            data = cache.get(key)
            if data is None:
                data = expensive_api_call(key)
                cache.set(key, data)

    return data
```

**Impact:** Thundering herd, API overload

---

### Pitfall 5: Not Reading Response Bodies

**Problem:**
```python
# Connection not released back to pool!
response = session.get(url, stream=True)
# Do something else...
```

**Solution:**
```python
# Always read body or close explicitly
response = session.get(url, stream=True)
response.close()  # Release connection

# Or read the body
response = session.get(url)
data = response.json()  # Automatically releases connection
```

**Impact:** Connection pool exhaustion

---

### Pitfall 6: Sharing Sessions Across Threads

**Problem:**
```python
# requests.Session is NOT thread-safe!
session = requests.Session()

def worker(key):
    return session.get(f"{base_url}/rest/api/3/issue/{key}")

threads = [threading.Thread(target=worker, args=(key,)) for key in keys]
for t in threads:
    t.start()
```

**Solution:**
```python
# Use thread-local sessions
import threading

thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session

def worker(key):
    session = get_session()
    return session.get(f"{base_url}/rest/api/3/issue/{key}")
```

**Impact:** Race conditions, corrupted requests

---

### Pitfall 7: Over-Caching

**Problem:**
```python
# Cache everything forever!
cache.set(key, value, ttl=timedelta(days=365))
```

**Solution:**
```python
# Use appropriate TTLs based on data type
cache.set(issue_key, issue, category="issue")  # 5 min TTL
cache.set(project_key, project, category="project")  # 1 hour TTL
cache.set(field_id, field, category="field")  # 1 day TTL
```

**Impact:** Stale data, incorrect results

---

### Pitfall 8: Not Using Bulk APIs

**Problem:**
```python
# Fetch 1000 issues one by one
for i in range(1, 1001):
    issue = client.get_issue(f"PROJ-{i}")
# Takes 500+ seconds!
```

**Solution:**
```python
# Use JQL search to fetch in bulk
jql = "project = PROJ AND key >= PROJ-1 AND key <= PROJ-1000"
response = client.search_issues(jql, max_results=1000)
issues = response['issues']
# Takes 5-10 seconds!
```

**Impact:** Slow performance, high API usage

---

### Pitfall 9: Insufficient Error Handling

**Problem:**
```python
# Fails on first error, no cleanup
for key in keys:
    issue = client.get_issue(key)  # Crash if any fail!
    process(issue)
```

**Solution:**
```python
# Handle errors gracefully
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

**Impact:** Incomplete operations, data loss

---

### Pitfall 10: Not Monitoring Cache Size

**Problem:**
```python
# Cache grows without limit
while True:
    data = fetch_data()
    cache.set(unique_key(), data)  # Cache grows forever!
# Eventually runs out of disk space
```

**Solution:**
```python
# Monitor cache size and set limits
cache = JiraCache(max_size_mb=100)  # Limit to 100 MB

# Regular monitoring
stats = cache.get_stats()
if stats.total_size_bytes > 0.8 * cache.max_size:
    logger.warning(f"Cache at {stats.total_size_bytes / cache.max_size * 100:.1f}% capacity")
```

**Impact:** Disk space exhaustion, performance degradation

---

## Quick Reference Card

### Rate Limits

```bash
# Monitor rate limits
curl -H "Authorization: Basic ..." https://your-site.atlassian.net/rest/api/3/myself -v 2>&1 | grep RateLimit

# Key limits
- Burst: 1,000 requests/min
- Quota: Tier-based hourly limit
- Total: 10,000 requests/min per instance
```

### Cache Operations

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

### Request Batching

```python
from request_batcher import RequestBatcher

# Batch requests
batcher = RequestBatcher(client, max_concurrent=10)
batcher.add("GET", "/rest/api/3/issue/PROJ-1")
batcher.add("GET", "/rest/api/3/issue/PROJ-2")
results = batcher.execute_sync()
```

### Connection Pooling

```python
# Configure adapter
from requests.adapters import HTTPAdapter

adapter = HTTPAdapter(
    pool_connections=10,  # Number of connection pools
    pool_maxsize=50,      # Max connections per pool
    pool_block=True       # Block if pool exhausted
)
session.mount("https://", adapter)
```

### Timeout Configuration

```python
# Set timeout (connect, read)
response = client.get(endpoint, timeout=(10, 60))

# Common timeouts
- Single issue: 30s
- Search: 60s
- Bulk operations: 120s
```

### Error Handling

```python
from error_handler import JiraError

try:
    issue = client.get_issue(key)
except JiraError as e:
    if e.status_code == 429:
        # Rate limited - back off
        time.sleep(60)
    elif e.status_code in [500, 502, 503]:
        # Server error - retry
        retry_with_backoff()
    else:
        # Client error - don't retry
        logger.error(f"Error: {e}")
```

### Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Cache hit rate | > 70% | < 50% |
| Request time | < 500ms | > 2000ms |
| Rate limit remaining | > 20% | < 5% |
| Error rate | < 1% | > 5% |

### Health Check

```python
# Quick health check
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

### Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
export DEBUG=1
python script.py
```

---

## Additional Resources

### Official Documentation

- [Atlassian Rate Limiting](https://developer.atlassian.com/cloud/jira/platform/rate-limiting/)
- [JIRA Cloud Platform API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Python Requests Documentation](https://requests.readthedocs.io/)

### Related Articles

- [Scaling responsibly: evolving our API rate limits](https://www.atlassian.com/blog/platform/evolving-api-rate-limits)
- [Production Ready Requests](https://blog.ian.stapletoncordas.co/2024/03/production-ready-requests)
- [Requests' secret: pool_connections and pool_maxsize](https://laike9m.com/blog/requests-secret-pool_connections-and-pool_maxsize,89/)

### Internal Documentation

- [JIRA Operations Skill](/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-ops/SKILL.md)
- [Shared Library Documentation](/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/shared/README.md)
- [CLAUDE.md Project Guide](/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/CLAUDE.md)

---

*Last updated: December 2024*
*Version: 1.0.0*
