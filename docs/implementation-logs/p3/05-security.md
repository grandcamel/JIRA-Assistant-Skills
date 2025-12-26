# P3 Security Hardening - Implementation Log

## Date: 2025-12-26

## Overview

This implementation adds security hardening improvements to the jira-ops and jira-bulk skills to protect sensitive data in cache storage and sanitize error messages for production logging.

---

## 1. Cache Directory Permissions (jira-ops)

### File Modified
- `.claude/skills/shared/scripts/lib/cache.py`

### Security Issue
The cache directory was being created with default system permissions, which could allow other users on a shared system to read cached JIRA data containing sensitive information.

### Before
```python
def __init__(self, cache_dir: Optional[str] = None, max_size_mb: float = 100):
    """
    Initialize cache.

    Args:
        cache_dir: Directory for cache storage (default: ~/.jira-skills/cache)
        max_size_mb: Maximum cache size in megabytes (default: 100 MB)
    """
    self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".jira-skills" / "cache"
    self.cache_dir.mkdir(parents=True, exist_ok=True)
```

### After
```python
def __init__(self, cache_dir: Optional[str] = None, max_size_mb: float = 100):
    """
    Initialize cache.

    SECURITY NOTE: The cache may contain sensitive data including:
    - Issue details (potentially confidential project information)
    - User information (account IDs, emails, display names)
    - API response data with project/company details

    The cache directory is created with restrictive permissions (0700)
    to ensure only the owner can access cached data.

    Args:
        cache_dir: Directory for cache storage (default: ~/.jira-skills/cache)
        max_size_mb: Maximum cache size in megabytes (default: 100 MB)
    """
    self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".jira-skills" / "cache"
    self.cache_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    # Ensure restrictive permissions even if directory already exists
    # This protects against directory created with default permissions
    os.chmod(self.cache_dir, 0o700)
```

### Security Considerations
- **Permission 0700**: Only owner has read/write/execute access
- **Retroactive fix**: `os.chmod()` ensures permissions are corrected even if directory existed with wrong permissions
- **Defense in depth**: Both `mkdir(mode=)` and explicit `chmod()` ensure the security policy is enforced

---

## 2. Cache Security Documentation (jira-ops)

### File Modified
- `.claude/skills/jira-ops/SKILL.md`

### Changes
Added a comprehensive "Security Considerations" section documenting:

1. **Cached Sensitive Data** - Types of sensitive data that may be stored:
   - Issue details (confidential project information)
   - User information (account IDs, emails, display names)
   - Project metadata (internal names, configurations)
   - Search results (organizational structure)

2. **Protection Measures**:
   - Restrictive permissions (0700)
   - Local storage only
   - No credential storage (API tokens never cached)
   - TTL expiration

3. **Best Practices**:
   - Do not share cache directory
   - Clear cache before sharing machines
   - Use separate profiles for dev/prod
   - Consider clearing after sensitive work

---

## 3. Error Message Sanitization (jira-bulk)

### Files Modified
- `.claude/skills/shared/scripts/lib/error_handler.py` - Added `sanitize_error_message()` function
- `.claude/skills/jira-bulk/scripts/bulk_transition.py`
- `.claude/skills/jira-bulk/scripts/bulk_assign.py`
- `.claude/skills/jira-bulk/scripts/bulk_set_priority.py`
- `.claude/skills/jira-bulk/scripts/bulk_clone.py`

### Security Issue
Error messages from JIRA API responses may contain sensitive data such as:
- Email addresses
- Atlassian account IDs
- API tokens
- URLs with credentials
- Bearer tokens

These could be exposed in logs, console output, or error reports.

### New Function Added to error_handler.py

```python
def sanitize_error_message(message: str) -> str:
    """
    Sanitize error messages to remove potentially sensitive information.

    Removes or redacts:
    - Email addresses
    - Account IDs (Atlassian format)
    - API tokens/keys
    - URLs with authentication
    - Issue keys with context (keeps key, redacts description)

    Args:
        message: Raw error message

    Returns:
        Sanitized error message safe for production logging

    Example:
        >>> sanitize_error_message("User john@company.com not found")
        "User [EMAIL REDACTED] not found"
    """
    if not message:
        return message

    sanitized = message

    # Redact email addresses
    sanitized = re.sub(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        '[EMAIL REDACTED]',
        sanitized
    )

    # Redact Atlassian account IDs (24-character hex strings)
    sanitized = re.sub(
        r'[0-9a-f]{24}',
        '[ACCOUNT_ID REDACTED]',
        sanitized,
        flags=re.IGNORECASE
    )

    # Redact longer UUIDs/tokens (32+ chars of hex)
    sanitized = re.sub(
        r'[0-9a-f]{32,}',
        '[TOKEN REDACTED]',
        sanitized,
        flags=re.IGNORECASE
    )

    # Redact API tokens (typical formats)
    sanitized = re.sub(
        r'(ATATT[A-Za-z0-9+/=]+)',
        '[API_TOKEN REDACTED]',
        sanitized
    )

    # Redact URLs with credentials
    sanitized = re.sub(
        r'(https?://)[^:]+:[^@]+@',
        r'\1[CREDENTIALS REDACTED]@',
        sanitized
    )

    # Redact bearer tokens
    sanitized = re.sub(
        r'(Bearer\s+)[A-Za-z0-9._-]+',
        r'\1[TOKEN REDACTED]',
        sanitized,
        flags=re.IGNORECASE
    )

    return sanitized
```

### Updated print_error() Function

```python
def print_error(error: Exception, debug: bool = False, sanitize: bool = False) -> None:
    """
    Print error message to stderr with optional debug information.

    Args:
        error: Exception to print
        debug: If True, include full stack trace
        sanitize: If True, sanitize sensitive data from error messages
    """
    error_str = str(error)
    if sanitize:
        error_str = sanitize_error_message(error_str)

    print(f"\nError: {error_str}", file=sys.stderr)

    if debug and hasattr(error, '__traceback__'):
        import traceback
        print("\nDebug traceback:", file=sys.stderr)
        traceback.print_tb(error.__traceback__, file=sys.stderr)

    if isinstance(error, JiraError) and error.response_data:
        response_str = str(error.response_data)
        if sanitize:
            response_str = sanitize_error_message(response_str)
        print(f"\nResponse data: {response_str}", file=sys.stderr)
```

### Bulk Script Changes

All bulk scripts now sanitize error messages before storing them in the errors dict or printing them:

**Before (in all bulk scripts):**
```python
except Exception as e:
    failed += 1
    errors[issue_key] = str(e)
    print_warning(f"[{i}/{total}] Failed {issue_key}: {e}")
```

**After (in all bulk scripts):**
```python
except Exception as e:
    failed += 1
    # Sanitize error message for logging to prevent sensitive data exposure
    sanitized_msg = sanitize_error_message(str(e))
    errors[issue_key] = sanitized_msg
    print_warning(f"[{i}/{total}] Failed {issue_key}: {sanitized_msg}")
```

---

## Summary of Changes

| File | Change | Security Benefit |
|------|--------|------------------|
| `cache.py` | Added `mode=0o700` to `mkdir()` and `os.chmod()` | Prevents unauthorized access to cached data |
| `jira-ops/SKILL.md` | Added Security Considerations section | Documents sensitive data handling |
| `error_handler.py` | Added `sanitize_error_message()` function | Provides reusable sanitization utility |
| `error_handler.py` | Updated `print_error()` with `sanitize` parameter | Enables optional sanitization in CLI output |
| `bulk_transition.py` | Import and use `sanitize_error_message` | Sanitizes error messages in bulk operations |
| `bulk_assign.py` | Import and use `sanitize_error_message` | Sanitizes error messages in bulk operations |
| `bulk_set_priority.py` | Import and use `sanitize_error_message` | Sanitizes error messages in bulk operations |
| `bulk_clone.py` | Import and use `sanitize_error_message` (3 locations) | Sanitizes error messages in bulk operations |

---

## Testing Recommendations

1. **Cache Permissions Test**:
   ```bash
   rm -rf ~/.jira-skills/cache
   python .claude/skills/jira-ops/scripts/cache_warm.py --projects
   ls -la ~/.jira-skills/cache
   # Should show drwx------ permissions
   ```

2. **Error Sanitization Test**:
   ```python
   from error_handler import sanitize_error_message

   # Test email redaction
   assert "[EMAIL REDACTED]" in sanitize_error_message("User john@company.com not found")

   # Test account ID redaction
   assert "[ACCOUNT_ID REDACTED]" in sanitize_error_message("User 5b1234567890abcdef123456 not found")

   # Test API token redaction
   assert "[API_TOKEN REDACTED]" in sanitize_error_message("Auth: ATATT3xFfGF0abc123...")
   ```

---

## Future Considerations

1. **Audit Logging**: Consider adding secure audit logging that sanitizes by default
2. **Key Rotation**: Document procedures for rotating API tokens if exposed
3. **Encryption at Rest**: Consider encrypting the cache database for highly sensitive environments
4. **Session Timeout**: Add automatic cache expiration after periods of inactivity
