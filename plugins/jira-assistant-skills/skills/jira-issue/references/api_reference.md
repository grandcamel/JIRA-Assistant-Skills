# JIRA Issue API Reference

This document provides API reference information for JIRA issue operations using the REST API v3.

## Endpoints

### Create Issue

**POST** `/rest/api/3/issue`

Creates a new issue or subtask.

**Request Body:**
```json
{
  "fields": {
    "project": {
      "key": "PROJ"
    },
    "issuetype": {
      "name": "Bug"
    },
    "summary": "Something's wrong",
    "description": {
      "type": "doc",
      "version": 1,
      "content": [...]
    },
    "priority": {
      "name": "High"
    },
    "assignee": {
      "accountId": "5b10ac8d82e05b22cc7d4ef5"
    },
    "labels": ["bug", "production"],
    "components": [
      {"name": "Backend"}
    ]
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "10000",
  "key": "PROJ-123",
  "self": "https://your-domain.atlassian.net/rest/api/3/issue/10000"
}
```

### Get Issue

**GET** `/rest/api/3/issue/{issueIdOrKey}`

Returns the details for an issue.

**Query Parameters:**
- `fields` - Comma-separated list of fields to return (default: all)
- `expand` - Comma-separated list of expandable resources

**Response:** `200 OK`
```json
{
  "id": "10000",
  "key": "PROJ-123",
  "self": "https://your-domain.atlassian.net/rest/api/3/issue/10000",
  "fields": {
    "summary": "Issue summary",
    "description": {...},
    "status": {
      "name": "To Do",
      "id": "10000"
    },
    "priority": {
      "name": "Medium"
    },
    "assignee": {
      "accountId": "5b10ac8d82e05b22cc7d4ef5",
      "displayName": "John Doe",
      "emailAddress": "john@example.com"
    },
    "reporter": {...},
    "created": "2023-01-15T10:30:00.000+0000",
    "updated": "2023-01-16T14:20:00.000+0000"
  }
}
```

### Update Issue

**PUT** `/rest/api/3/issue/{issueIdOrKey}`

Edits an issue.

**Query Parameters:**
- `notifyUsers` - Whether to send notifications (default: true)

**Request Body:**
```json
{
  "fields": {
    "summary": "Updated summary",
    "priority": {
      "name": "High"
    },
    "assignee": {
      "accountId": "5b10ac8d82e05b22cc7d4ef5"
    }
  }
}
```

**Response:** `204 No Content`

### Delete Issue

**DELETE** `/rest/api/3/issue/{issueIdOrKey}`

Deletes an issue.

**Query Parameters:**
- `deleteSubtasks` - Whether to delete subtasks (default: false)

**Response:** `204 No Content`

## Common Fields

### Standard Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `summary` | string | Issue title | "Login button broken" |
| `description` | ADF object | Issue description | See ADF format |
| `issuetype` | object | Issue type | `{"name": "Bug"}` |
| `project` | object | Project | `{"key": "PROJ"}` |
| `priority` | object | Priority level | `{"name": "High"}` |
| `assignee` | object | Assigned user | `{"accountId": "..."}` |
| `reporter` | object | Reporter (auto-set) | `{"accountId": "..."}` |
| `labels` | array | Labels/tags | `["bug", "urgent"]` |
| `components` | array | Components | `[{"name": "Backend"}]` |
| `fixVersions` | array | Fix versions | `[{"name": "1.0"}]` |
| `duedate` | string | Due date | "2023-12-31" |
| `environment` | ADF object | Environment info | See ADF format |

### Priority Values

Common priority values (may vary by JIRA instance):
- `Highest`
- `High`
- `Medium`
- `Low`
- `Lowest`

### Issue Type Values

Standard issue types:
- `Bug`
- `Task`
- `Story`
- `Epic`
- `Subtask`

For JIRA Service Management:
- `Service Request`
- `Incident`
- `Problem`
- `Change`

## User Assignment

Users can be specified in three ways:

1. **By Account ID:**
```json
{
  "assignee": {
    "accountId": "5b10ac8d82e05b22cc7d4ef5"
  }
}
```

2. **By Email (Cloud only):**
```json
{
  "assignee": {
    "emailAddress": "user@example.com"
  }
}
```

3. **Unassign:**
```json
{
  "assignee": null
}
```

## Error Responses

### 400 Bad Request
Invalid field values or missing required fields.

```json
{
  "errorMessages": [],
  "errors": {
    "summary": "Summary is required",
    "priority": "Invalid priority value"
  }
}
```

### 401 Unauthorized
Authentication failed.

### 403 Forbidden
User doesn't have permission to perform the operation.

### 404 Not Found
Issue or project doesn't exist.

## Rate Limiting

JIRA Cloud enforces rate limits:
- **Per user:** ~600 requests per minute
- **Per app:** Varies by plan

When rate limited, you'll receive:
- **Status:** 429 Too Many Requests
- **Header:** `Retry-After: <seconds>`

## Best Practices

1. **Use specific fields:** Request only the fields you need with the `fields` parameter
2. **Batch operations:** Use bulk APIs when updating multiple issues
3. **Handle rate limits:** Implement exponential backoff
4. **Cache issue metadata:** Cache issue types, priorities, etc.
5. **Validate before API calls:** Check required fields locally first
6. **Use ADF format:** Always use Atlassian Document Format for rich text fields

## References

- [JIRA REST API v3 Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Issue API Endpoints](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/)
- [Atlassian Document Format](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)
