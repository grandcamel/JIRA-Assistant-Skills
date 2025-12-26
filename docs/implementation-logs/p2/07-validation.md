# Implementation Log: Add Missing Validation (P2-07)

## Overview

This implementation adds missing validation checks across three skills:
1. **jira-bulk**: Move priority validation before client creation
2. **jira-jsm**: Validate comma-separated lists are non-empty after parsing
3. **jira-ops**: Add single entry size validation and cache directory permission check

---

## 1. jira-bulk: bulk_set_priority.py

### Issue
Priority validation occurs inside `bulk_set_priority()` function after client may have been created. Should validate before any client creation.

### Before
```python
def main():
    parser = argparse.ArgumentParser(...)
    # ...
    args = parser.parse_args()

    try:
        issue_keys = None
        if args.issues:
            issue_keys = [k.strip() for k in args.issues.split(',')]

        result = bulk_set_priority(
            issue_keys=issue_keys,
            jql=args.jql,
            priority=args.priority,  # Validation happens inside function
            dry_run=args.dry_run,
            max_issues=args.max_issues,
            profile=args.profile
        )
```

### After
```python
def main():
    parser = argparse.ArgumentParser(...)
    # ...
    args = parser.parse_args()

    try:
        # Validate priority before any client creation
        priority = validate_priority(args.priority)

        issue_keys = None
        if args.issues:
            issue_keys = [k.strip() for k in args.issues.split(',')]

        result = bulk_set_priority(
            issue_keys=issue_keys,
            jql=args.jql,
            priority=priority,  # Already validated
            dry_run=args.dry_run,
            max_issues=args.max_issues,
            profile=args.profile
        )
```

### Error Message
No change to error message - uses existing `ValidationError`:
```
Invalid priority: 'invalid'. Valid priorities: Highest, High, Medium, Low, Lowest, Blocker, Critical, Major, Minor, Trivial
```

---

## 2. jira-jsm: Comma-separated List Validation

### Issue
Six scripts parse comma-separated account IDs but do not validate that the resulting list is non-empty after parsing.

### Scripts Modified
- `add_participant.py` - Added validation check
- `remove_participant.py` - Added validation check
- `create_request.py` - Added validation check for participants

Note: `add_customer.py`, `remove_customer.py`, `add_to_organization.py`, and `remove_from_organization.py` already have proper validation.

### Before (add_participant.py)
```python
account_ids = parse_account_ids(args.account_id) if args.account_id else None
usernames = parse_account_ids(args.username) if args.username else None

if args.dry_run:
    # ... proceeds without validating parsed list is non-empty
```

### After (add_participant.py)
```python
account_ids = parse_account_ids(args.account_id) if args.account_id else None
usernames = parse_account_ids(args.username) if args.username else None

# Validate parsed lists are non-empty
if account_ids is not None and len(account_ids) == 0:
    print_error("Account ID list is empty after parsing. Provide valid comma-separated IDs.")
    return 1
if usernames is not None and len(usernames) == 0:
    print_error("Username list is empty after parsing. Provide valid comma-separated usernames.")
    return 1

if args.dry_run:
```

### Error Messages
- `Account ID list is empty after parsing. Provide valid comma-separated IDs.`
- `Username list is empty after parsing. Provide valid comma-separated usernames.`
- `Participant list is empty after parsing. Provide valid comma-separated emails.`

---

## 3. jira-jsm: create_asset.py - Positive object_type_id Validation

### Issue
The `--type-id` argument accepts any integer including negative values. Should validate it is positive.

### Before
```python
parser.add_argument('--type-id', type=int, required=True,
                   help='Object type ID')

args = parser.parse_args()

try:
    attributes = parse_attributes(args.attr)
    asset = create_asset(args.type_id, attributes, args.dry_run)
```

### After
```python
parser.add_argument('--type-id', type=int, required=True,
                   help='Object type ID')

args = parser.parse_args()

try:
    # Validate object_type_id is positive
    if args.type_id <= 0:
        print(f"Error: --type-id must be a positive integer, got {args.type_id}", file=sys.stderr)
        sys.exit(1)

    attributes = parse_attributes(args.attr)
    asset = create_asset(args.type_id, attributes, args.dry_run)
```

### Error Message
```
Error: --type-id must be a positive integer, got -1
```

---

## 4. jira-ops: cache.py - Single Entry Size Validation

### Issue
The cache `set()` method does not validate that a single entry is not larger than the entire cache maximum size.

### Before
```python
def set(self, key: str, value: Any, category: str = "default",
        ttl: Optional[timedelta] = None) -> None:
    with self._lock:
        if ttl is None:
            ttl = self.ttl_defaults.get(category, self.ttl_defaults["default"])

        now = time.time()
        expires_at = now + ttl.total_seconds()
        value_json = json.dumps(value)
        size_bytes = len(value_json.encode('utf-8'))

        # Check if we need to evict entries
        self._evict_if_needed(size_bytes)
```

### After
```python
def set(self, key: str, value: Any, category: str = "default",
        ttl: Optional[timedelta] = None) -> None:
    with self._lock:
        if ttl is None:
            ttl = self.ttl_defaults.get(category, self.ttl_defaults["default"])

        now = time.time()
        expires_at = now + ttl.total_seconds()
        value_json = json.dumps(value)
        size_bytes = len(value_json.encode('utf-8'))

        # Validate single entry is not larger than max cache size
        if size_bytes > self.max_size:
            raise ValueError(
                f"Cache entry size ({size_bytes} bytes) exceeds maximum cache size "
                f"({self.max_size} bytes). Consider increasing max_size_mb or caching smaller data."
            )

        # Check if we need to evict entries
        self._evict_if_needed(size_bytes)
```

### Error Message
```
Cache entry size (150000000 bytes) exceeds maximum cache size (104857600 bytes). Consider increasing max_size_mb or caching smaller data.
```

---

## 5. jira-ops: cache.py - Cache Directory Permission Check

### Issue
The cache directory is created without verifying it has secure permissions (0700). Sensitive JIRA data could be exposed.

### Before
```python
def __init__(self, cache_dir: Optional[str] = None, max_size_mb: float = 100):
    self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".jira-skills" / "cache"
    self.cache_dir.mkdir(parents=True, exist_ok=True)

    self.max_size = int(max_size_mb * 1024 * 1024)  # Convert to bytes
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
    """
    self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".jira-skills" / "cache"
    self.cache_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    # Ensure restrictive permissions even if directory already exists
    # This protects against directory created with default permissions
    os.chmod(self.cache_dir, 0o700)

    self.max_size = int(max_size_mb * 1024 * 1024)  # Convert to bytes
```

### Implementation Notes
- Directory is created with mode 0o700 (owner read/write/execute only)
- `os.chmod()` is called unconditionally to fix permissions on existing directories
- Security note added to docstring explaining why permissions matter

---

## Summary

| Skill | File | Validation Added |
|-------|------|------------------|
| jira-bulk | `bulk_set_priority.py` | Priority validation moved before client creation |
| jira-jsm | `add_participant.py` | Non-empty list validation after parsing |
| jira-jsm | `remove_participant.py` | Non-empty list validation after parsing |
| jira-jsm | `create_request.py` | Non-empty participant list validation |
| jira-jsm | `create_asset.py` | Positive object_type_id validation |
| jira-ops | `cache.py` | Single entry size validation |
| jira-ops | `cache.py` | Cache directory permission check (0700) |

## Files Modified

1. `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-bulk/scripts/bulk_set_priority.py`
2. `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-jsm/scripts/add_participant.py`
3. `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-jsm/scripts/remove_participant.py`
4. `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-jsm/scripts/create_request.py`
5. `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-jsm/scripts/create_asset.py`
6. `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/shared/scripts/lib/cache.py`
