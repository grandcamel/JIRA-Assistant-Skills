# JIRA API Examples

Complete request and response examples for JIRA issue operations.

---

## Create Issue

### Basic Bug Creation

**Request:**
```bash
python create_issue.py --project PROJ --type Bug \
  --summary "Login fails on mobile Safari" \
  --priority High \
  --description "Users unable to login on Safari 17+ on iOS"
```

**API Request (POST /rest/api/3/issue):**
```json
{
  "fields": {
    "project": {
      "key": "PROJ"
    },
    "issuetype": {
      "name": "Bug"
    },
    "summary": "Login fails on mobile Safari",
    "priority": {
      "name": "High"
    },
    "description": {
      "type": "doc",
      "version": 1,
      "content": [
        {
          "type": "paragraph",
          "content": [
            {
              "type": "text",
              "text": "Users unable to login on Safari 17+ on iOS"
            }
          ]
        }
      ]
    }
  }
}
```

**Response (201 Created):**
```json
{
  "id": "10042",
  "key": "PROJ-123",
  "self": "https://your-domain.atlassian.net/rest/api/3/issue/10042"
}
```

---

### Story with Agile Fields

**Request:**
```bash
python create_issue.py --project PROJ --type Story \
  --summary "Users can reset password via email" \
  --epic PROJ-100 \
  --story-points 5 \
  --sprint 42
```

**API Request:**
```json
{
  "fields": {
    "project": {"key": "PROJ"},
    "issuetype": {"name": "Story"},
    "summary": "Users can reset password via email",
    "customfield_10014": "PROJ-100",
    "customfield_10016": 5
  }
}
```

Note: Sprint assignment requires a separate API call to add the issue to the sprint.

---

### Task with Issue Links

**Request:**
```bash
python create_issue.py --project PROJ --type Task \
  --summary "Setup database migrations" \
  --blocks PROJ-200,PROJ-201 \
  --estimate "2d"
```

**API Requests (two steps):**

1. Create issue:
```json
{
  "fields": {
    "project": {"key": "PROJ"},
    "issuetype": {"name": "Task"},
    "summary": "Setup database migrations",
    "timetracking": {
      "originalEstimate": "2d"
    }
  }
}
```

2. Create links (POST /rest/api/3/issueLink for each):
```json
{
  "type": {"name": "Blocks"},
  "inwardIssue": {"key": "PROJ-200"},
  "outwardIssue": {"key": "PROJ-NEW"}
}
```

---

## Get Issue

### Basic Retrieval

**Request:**
```bash
python get_issue.py PROJ-123
```

**API Request:**
```
GET /rest/api/3/issue/PROJ-123
```

**Response:**
```json
{
  "id": "10042",
  "key": "PROJ-123",
  "self": "https://your-domain.atlassian.net/rest/api/3/issue/10042",
  "fields": {
    "summary": "Login fails on mobile Safari",
    "status": {
      "name": "To Do",
      "id": "10000",
      "statusCategory": {
        "key": "new",
        "name": "To Do"
      }
    },
    "priority": {
      "name": "High",
      "id": "2"
    },
    "issuetype": {
      "name": "Bug",
      "id": "10004"
    },
    "assignee": {
      "accountId": "5b10ac8d82e05b22cc7d4ef5",
      "displayName": "John Doe",
      "emailAddress": "john@example.com"
    },
    "reporter": {
      "accountId": "5b10ac8d82e05b22cc7d4ef5",
      "displayName": "Jane Smith"
    },
    "created": "2025-01-15T10:30:00.000+0000",
    "updated": "2025-01-16T14:20:00.000+0000"
  }
}
```

---

### With Links and Time Tracking

**Request:**
```bash
python get_issue.py PROJ-123 --detailed --show-links --show-time
```

**API Request:**
```
GET /rest/api/3/issue/PROJ-123?expand=changelog
```

**Response includes:**
```json
{
  "fields": {
    "issuelinks": [
      {
        "type": {
          "name": "Blocks",
          "inward": "is blocked by",
          "outward": "blocks"
        },
        "outwardIssue": {
          "key": "PROJ-200",
          "fields": {
            "summary": "Deploy to production",
            "status": {"name": "Blocked"}
          }
        }
      }
    ],
    "timetracking": {
      "originalEstimate": "2d",
      "remainingEstimate": "1d 4h",
      "timeSpent": "4h",
      "originalEstimateSeconds": 57600,
      "remainingEstimateSeconds": 43200,
      "timeSpentSeconds": 14400
    }
  }
}
```

---

## Update Issue

### Update Priority and Assignee

**Request:**
```bash
python update_issue.py PROJ-123 --priority Critical --assignee self
```

**API Request (PUT /rest/api/3/issue/PROJ-123):**
```json
{
  "fields": {
    "priority": {"name": "Critical"},
    "assignee": {"accountId": "your-account-id"}
  }
}
```

**Response:** `204 No Content`

---

### Update Without Notifications

**Request:**
```bash
python update_issue.py PROJ-123 --summary "Updated title" --no-notify
```

**API Request:**
```
PUT /rest/api/3/issue/PROJ-123?notifyUsers=false
```

```json
{
  "fields": {
    "summary": "Updated title"
  }
}
```

---

### Unassign Issue

**Request:**
```bash
python update_issue.py PROJ-123 --assignee none
```

**API Request:**
```json
{
  "fields": {
    "assignee": null
  }
}
```

---

## Delete Issue

### With Confirmation

**Request:**
```bash
python delete_issue.py PROJ-456
```

Output:
```
Are you sure you want to delete PROJ-456? (y/N): y
Issue PROJ-456 deleted successfully.
```

### Force Delete

**Request:**
```bash
python delete_issue.py PROJ-456 --force
```

**API Request:**
```
DELETE /rest/api/3/issue/PROJ-456
```

**Response:** `204 No Content`

---

## ADF Description Examples

### Simple Paragraph

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "This is a simple description."}
      ]
    }
  ]
}
```

### With Heading and List

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "heading",
      "attrs": {"level": 2},
      "content": [{"type": "text", "text": "Steps to Reproduce"}]
    },
    {
      "type": "orderedList",
      "content": [
        {
          "type": "listItem",
          "content": [
            {
              "type": "paragraph",
              "content": [{"type": "text", "text": "Go to login page"}]
            }
          ]
        },
        {
          "type": "listItem",
          "content": [
            {
              "type": "paragraph",
              "content": [{"type": "text", "text": "Enter credentials"}]
            }
          ]
        }
      ]
    }
  ]
}
```

### With Code Block

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "paragraph",
      "content": [{"type": "text", "text": "Error from console:"}]
    },
    {
      "type": "codeBlock",
      "attrs": {"language": "javascript"},
      "content": [
        {"type": "text", "text": "TypeError: Cannot read property 'user' of undefined\n  at login.js:42"}
      ]
    }
  ]
}
```

---

## Error Response Examples

### 400 Bad Request - Missing Required Field

```json
{
  "errorMessages": [],
  "errors": {
    "summary": "You must specify a summary of the issue."
  }
}
```

### 400 Bad Request - Invalid Field Value

```json
{
  "errorMessages": [],
  "errors": {
    "priority": "Priority name 'Super High' is not valid."
  }
}
```

### 401 Unauthorized

```json
{
  "message": "Client must be authenticated to access this resource."
}
```

### 403 Forbidden

```json
{
  "errorMessages": [
    "You do not have the permission to see the specified issue."
  ],
  "errors": {}
}
```

### 404 Not Found

```json
{
  "errorMessages": [
    "Issue does not exist or you do not have permission to see it."
  ],
  "errors": {}
}
```

### 429 Rate Limited

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
```

---

## Markdown to ADF Conversion

The scripts automatically convert Markdown to ADF:

**Input (Markdown):**
```markdown
## Bug Report

**Steps:**
1. Go to login
2. Enter credentials
3. Click *Login*

`Error: Session timeout`
```

**Output (ADF):**
```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "heading",
      "attrs": {"level": 2},
      "content": [{"type": "text", "text": "Bug Report"}]
    },
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Steps:", "marks": [{"type": "strong"}]}
      ]
    },
    {
      "type": "orderedList",
      "content": [
        {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Go to login"}]}]},
        {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Enter credentials"}]}]},
        {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Click "}, {"type": "text", "text": "Login", "marks": [{"type": "em"}]}]}]}
      ]
    },
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Error: Session timeout", "marks": [{"type": "code"}]}
      ]
    }
  ]
}
```

---

*Last updated: December 2025*
