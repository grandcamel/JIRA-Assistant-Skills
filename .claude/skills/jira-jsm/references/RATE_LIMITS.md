# JSM Rate Limiting Reference

Guidance for handling API rate limits in JSM Cloud.

## JIRA Cloud Rate Limits

| Tier | Limit | Notes |
|------|-------|-------|
| Standard | ~100-200 req/min | Varies by endpoint and instance |
| Concurrent | ~10 | Simultaneous requests |

---

## Built-in Rate Limit Handling

The shared JIRA client automatically handles rate limits:

- **HTTP 429 Response**: Automatically retries with exponential backoff
- **Retry Attempts**: Up to 3 retries per request
- **Backoff Strategy**: Exponential delay (1s, 2s, 4s)

---

## Response Headers

Check these headers for rate limit status:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Remaining` | Requests remaining in window |
| `X-RateLimit-Reset` | Timestamp when limit resets |
| `Retry-After` | Seconds to wait (on 429 response) |

---

## Best Practices

### 1. Batch Requests

```bash
# Preferred: Add multiple items at once
python add_participant.py SD-123 \
  --users "user1@example.com,user2@example.com,user3@example.com"

# Avoid: Multiple individual calls
# python add_participant.py SD-123 --users "user1@example.com"
# python add_participant.py SD-123 --users "user2@example.com"
```

### 2. Add Delays for Bulk Operations

```bash
for issue in SD-{100..200}; do
    python transition_request.py $issue --status "Resolved"
    sleep 0.5  # 500ms delay between requests
done
```

### 3. Use Pagination

```bash
# Limit results per request
python list_requests.py --service-desk 1 --max-results 50 --start 0
python list_requests.py --service-desk 1 --max-results 50 --start 50
```

### 4. Cache Static Data

Data that rarely changes can be cached:

```bash
# Cache request types for reuse
python list_request_types.py --service-desk 1 --output json > /tmp/request-types.json
```

---

## Handling Rate Limit Errors

If you encounter rate limit errors despite retries:

```
Error: HTTP 429 Too Many Requests
Hint: Wait and retry after the rate limit window resets (usually 1 minute)
```

**Solutions**:
1. Reduce request frequency
2. Implement longer delays between operations
3. Spread operations over time
4. Contact Atlassian support for rate limit increases (enterprise)

---

## Cloud vs Data Center

| Platform | Rate Limit | Notes |
|----------|-----------|-------|
| Cloud | Enforced per-user | Automatic throttling |
| Data Center | Configurable | Admin-controlled |

---

*Last updated: December 2025*
