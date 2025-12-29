# Best Practices Index

Quick navigation to optimization patterns and strategies.

## By Problem

| Problem | Solution Guide |
|---------|---------------|
| API responses are slow | [Cache Warming](CACHE_WARMING.md), [Connection Pooling](CONNECTION_POOLING.md) |
| Getting 429 rate limit errors | [Rate Limits](RATE_LIMITS.md), [Request Batching](REQUEST_BATCHING.md) |
| Cache hit rate is low | [Cache Warming](CACHE_WARMING.md), [Cache Invalidation](CACHE_INVALIDATION.md) |
| Requests timing out | [Timeout Configuration](TIMEOUT_CONFIGURATION.md) |
| Unexpected failures | [Error Handling](ERROR_HANDLING.md), [Common Pitfalls](COMMON_PITFALLS.md) |
| Need to debug issues | [Logging & Debug](LOGGING_DEBUG.md), [Health Checks](HEALTH_CHECKS.md) |

## By Topic

### Performance
- [Rate Limits](RATE_LIMITS.md) - Understanding and managing API rate limits
- [Request Batching](REQUEST_BATCHING.md) - Parallel execution for bulk operations
- [Connection Pooling](CONNECTION_POOLING.md) - Reusing TCP connections
- [Timeout Configuration](TIMEOUT_CONFIGURATION.md) - Preventing hung requests

### Caching
- [Cache Warming](CACHE_WARMING.md) - Pre-loading data for better performance
- [Cache Invalidation](CACHE_INVALIDATION.md) - Keeping cached data fresh

### Reliability
- [Error Handling](ERROR_HANDLING.md) - Robust error handling and retries
- [Health Checks](HEALTH_CHECKS.md) - Monitoring system health
- [Common Pitfalls](COMMON_PITFALLS.md) - Mistakes to avoid

### Operations
- [Performance Monitoring](PERFORMANCE_MONITORING.md) - Key metrics and alerting
- [Logging & Debug](LOGGING_DEBUG.md) - Troubleshooting and diagnostics

## Quick Reference

Need a fast answer? See [Quick Reference Card](QUICK_REFERENCE.md).

## See Also

- [Skill Overview](../../SKILL.md)
- [API Reference](../API_REFERENCE.md)
- [Troubleshooting](../TROUBLESHOOTING.md)
