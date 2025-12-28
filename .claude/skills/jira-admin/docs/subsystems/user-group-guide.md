# User & Group Management Guide

Deep-dive reference for JIRA user and group management including search, membership, and group operations.

---

## When to Use User & Group Scripts

Use these scripts when you need to:
- Search for users by name or email
- Get user details and group memberships
- Create, list, or delete groups
- View group members
- Add or remove users from groups
- Audit team membership and access

---

## Understanding Users & Groups

### Key Concepts

- **Account ID**: GDPR-compliant unique user identifier (not username)
- **Group**: Collection of users for permission management
- **System Groups**: Built-in groups (jira-administrators, jira-users) that cannot be deleted
- **Project Roles**: Different from groups - roles are project-specific

### GDPR Compliance

JIRA Cloud uses `accountId` for all user references (not usernames). This is required for:
- Privacy-restricted fields (email, timezone, locale)
- Deleted/anonymized users
- Cross-instance user identification

---

## Scripts Reference

### User Management

| Script | Description |
|--------|-------------|
| `search_users.py` | Search users by name/email, find assignable users for projects |
| `get_user.py` | Get user details by account ID or email, including groups |

### Group Management

| Script | Description |
|--------|-------------|
| `list_groups.py` | List all groups with optional member counts |
| `get_group_members.py` | Get members of a specific group |
| `create_group.py` | Create a new group |
| `delete_group.py` | Delete a group (requires confirmation) |

### Membership Management

| Script | Description |
|--------|-------------|
| `add_user_to_group.py` | Add a user to a group |
| `remove_user_from_group.py` | Remove a user from a group |

---

## Examples

### User Search and Retrieval

```bash
# Search for users
python search_users.py "john"
python search_users.py "john.doe@example.com"
python search_users.py "john" --project PROJ --assignable
python search_users.py "john" --all --include-groups

# Get user details
python get_user.py --email john.doe@example.com
python get_user.py --account-id 5b10ac8d82e05b22cc7d4ef5
python get_user.py --me --include-groups
python get_user.py --email john@example.com --output json
```

### Group Operations

```bash
# List groups
python list_groups.py
python list_groups.py --query "developers"
python list_groups.py --include-members
python list_groups.py --show-system --output json

# Get group members
python get_group_members.py "jira-developers"
python get_group_members.py "jira-developers" --include-inactive
python get_group_members.py --group-id abc123 --output csv > members.csv

# Create a group
python create_group.py "mobile-team"
python create_group.py "external-contractors" --dry-run

# Delete a group
python delete_group.py "old-team" --confirm
python delete_group.py "old-team" --swap "new-team" --confirm
python delete_group.py "test-group" --dry-run
```

### Membership Operations

```bash
# Add user to group
python add_user_to_group.py john@example.com --group "jira-developers"
python add_user_to_group.py --account-id 5b10ac8d82e05b22cc7d4ef5 --group "mobile-team"
python add_user_to_group.py john@example.com --group "team" --dry-run

# Remove user from group
python remove_user_from_group.py john@example.com --group "jira-developers" --confirm
python remove_user_from_group.py --account-id 5b10ac8d82e05b22cc7d4ef5 --group "old-team" --confirm
python remove_user_from_group.py jane@example.com --group "team" --dry-run
```

---

## Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| Search/view users | Browse users and groups |
| Get user details | Browse users and groups |
| List/view groups | Browse users and groups |
| Create group | Site administration |
| Delete group | Site administration |
| Add user to group | Site administration |
| Remove user from group | Site administration |

---

## GDPR & Privacy Considerations

This feature implements GDPR-compliant user handling:
- Uses `accountId` for all user references (not username)
- Handles privacy-restricted fields gracefully (shown as "[hidden]")
- Respects user privacy settings for email, timezone, and locale
- Properly handles "unknown" account IDs for deleted/anonymized users

---

## Important Notes

1. **User creation/deactivation** is NOT available via standard JIRA API - requires Cloud Admin API
2. **System groups** (jira-administrators, jira-users, etc.) cannot be deleted
3. **Adding/removing users is idempotent** - no error if already member or not member
4. **Email lookup may fail** if user has privacy controls enabled
5. **Group names are case-insensitive** for search but case-preserved
6. **All operations require appropriate permissions** - Site administration for most write operations

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| **403 Forbidden** | Insufficient permissions | Verify Site administration permission |
| **404 Not Found** | User or group doesn't exist | Check account ID or group name |
| **400 Bad Request** | Invalid email format | Validate email format |
| **Privacy Error** | User has privacy controls | Use account ID instead of email |

---

## Related Guides

- [BEST_PRACTICES.md](../BEST_PRACTICES.md#user--group-management) - User/Group best practices
- [DECISION-TREE.md](../DECISION-TREE.md#i-want-to-manage-users--groups) - Quick script finder
- [QUICK-REFERENCE.md](../QUICK-REFERENCE.md#users--groups) - Command syntax reference
