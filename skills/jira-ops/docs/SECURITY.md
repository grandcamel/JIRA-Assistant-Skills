# Security Considerations

The cache directory contains sensitive data and should be protected.

## Cached Sensitive Data

The cache may contain:

- **Issue details**: Confidential project information, bug descriptions, internal discussions
- **User information**: Account IDs, email addresses, display names
- **Project metadata**: Internal project names, configurations, custom fields
- **Search results**: Query responses that may reveal organizational structure

## Protection Measures

1. **Restrictive permissions**: Cache directory created with `0700` permissions (owner read/write/execute only)
2. **Local storage only**: Cache stored in user's home directory, not shared locations
3. **No credential storage**: API tokens and passwords never cached (only used in-memory)
4. **TTL expiration**: Data automatically expires based on category TTL settings

## Best Practices

- Do not share the cache directory with other users
- Clear cache before sharing a machine:
  ```bash
  python cache_clear.py --force
  ```
- Use separate profiles for development/production to avoid data mixing
- Consider clearing cache after working with highly sensitive projects
