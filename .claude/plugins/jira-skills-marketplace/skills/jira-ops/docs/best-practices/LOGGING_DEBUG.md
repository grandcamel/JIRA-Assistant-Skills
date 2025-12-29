# Logging & Debugging

Configure logging for troubleshooting and monitoring.

## Logging Levels

| Level | Usage | Example |
|-------|-------|---------|
| DEBUG | Detailed diagnostic info | "Cache hit for PROJ-123" |
| INFO | General informational events | "Fetched 100 issues in 2.5s" |
| WARNING | Potentially harmful situations | "Cache hit rate below 50%" |
| ERROR | Error events | "Failed to fetch PROJ-123" |
| CRITICAL | Severe errors | "Rate limit exceeded" |

## Basic Setup

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

## What to Log

### API Requests
```python
logger.debug(f"GET /rest/api/3/issue/{issue_key}")
logger.info(f"Fetched issue {issue_key} in {elapsed_ms:.2f}ms")
```

### Cache Operations
```python
logger.debug(f"Cache hit for {key}")
logger.info(f"Cache hit rate: {stats.hit_rate * 100:.1f}%")
```

### Errors and Retries
```python
logger.error(f"Failed to fetch {issue_key}: {error}")
logger.warning(f"Retry {attempt}/{max_retries}")
```

## Debug Mode

Enable debug logging:

```bash
# Environment variable
export DEBUG=1
python cache_warm.py --all

# Or via command-line flag
python cache_warm.py --all --verbose
```

In code:
```python
import os

if os.getenv("DEBUG"):
    logging.basicConfig(level=logging.DEBUG)
```

## Request Logging

```python
import logging
import http.client

# Enable HTTP debug logging
http.client.HTTPConnection.debuglevel = 1
logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)
```

## See Also

- [Health Checks](HEALTH_CHECKS.md)
- [Performance Monitoring](PERFORMANCE_MONITORING.md)
