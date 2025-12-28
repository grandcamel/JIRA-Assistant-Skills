# JIRA Field Formats Reference

This document describes the format requirements for common JIRA fields when creating or updating issues.

---

## Quick Index

Jump to field category:

| Category | Fields | Section |
|----------|--------|---------|
| **Rich Text** | Description, Environment, Comments | [Atlassian Document Format](#atlassian-document-format-adf) |
| **Identity** | Project, Issue Type | [Standard Fields](#standard-field-formats) |
| **Assignment** | Assignee, Reporter | [User Assignment](#user-assignment) |
| **Categorization** | Priority, Labels, Components | [Standard Fields](#standard-field-formats) |
| **Time** | Due Date, Time Tracking | [Standard Fields](#standard-field-formats) |
| **Versions** | Fix Versions | [Standard Fields](#standard-field-formats) |
| **Custom** | Text, Number, Select, User Picker, etc. | [Custom Fields](#custom-fields) |

---

## Atlassian Document Format (ADF)

JIRA Cloud uses ADF for rich text fields like `description`, `environment`, and comments.

### Basic ADF Structure

```json
{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {
          "type": "text",
          "text": "Hello world"
        }
      ]
    }
  ]
}
```

### Common ADF Nodes

#### Paragraph

```json
{
  "type": "paragraph",
  "content": [
    {"type": "text", "text": "This is a paragraph"}
  ]
}
```

#### Heading

```json
{
  "type": "heading",
  "attrs": {"level": 1},
  "content": [
    {"type": "text", "text": "Heading Text"}
  ]
}
```

Levels: 1-6

#### Bullet List

```json
{
  "type": "bulletList",
  "content": [
    {
      "type": "listItem",
      "content": [
        {
          "type": "paragraph",
          "content": [{"type": "text", "text": "Item 1"}]
        }
      ]
    },
    {
      "type": "listItem",
      "content": [
        {
          "type": "paragraph",
          "content": [{"type": "text", "text": "Item 2"}]
        }
      ]
    }
  ]
}
```

#### Numbered List

```json
{
  "type": "orderedList",
  "content": [
    {
      "type": "listItem",
      "content": [
        {
          "type": "paragraph",
          "content": [{"type": "text", "text": "First"}]
        }
      ]
    }
  ]
}
```

#### Code Block

```json
{
  "type": "codeBlock",
  "attrs": {"language": "python"},
  "content": [
    {
      "type": "text",
      "text": "def hello():\n    print('Hello')"
    }
  ]
}
```

#### Text Formatting

**Bold:**
```json
{
  "type": "text",
  "text": "Bold text",
  "marks": [{"type": "strong"}]
}
```

**Italic:**
```json
{
  "type": "text",
  "text": "Italic text",
  "marks": [{"type": "em"}]
}
```

**Inline Code:**
```json
{
  "type": "text",
  "text": "code",
  "marks": [{"type": "code"}]
}
```

**Link:**
```json
{
  "type": "text",
  "text": "Click here",
  "marks": [
    {
      "type": "link",
      "attrs": {"href": "https://example.com"}
    }
  ]
}
```

## Standard Field Formats

### Project

**Format:** Object with key or ID

```json
{
  "project": {
    "key": "PROJ"
  }
}
```

or

```json
{
  "project": {
    "id": "10000"
  }
}
```

### Issue Type

**Format:** Object with name or ID

```json
{
  "issuetype": {
    "name": "Bug"
  }
}
```

or

```json
{
  "issuetype": {
    "id": "10004"
  }
}
```

### Priority

**Format:** Object with name or ID

```json
{
  "priority": {
    "name": "High"
  }
}
```

### Assignee

**Format:** Object with accountId, emailAddress, or null

```json
{
  "assignee": {
    "accountId": "5b10ac8d82e05b22cc7d4ef5"
  }
}
```

To unassign:
```json
{
  "assignee": null
}
```

### Labels

**Format:** Array of strings

```json
{
  "labels": ["bug", "production", "urgent"]
}
```

### Components

**Format:** Array of objects with name or ID

```json
{
  "components": [
    {"name": "Backend"},
    {"name": "Frontend"}
  ]
}
```

### Fix Versions

**Format:** Array of objects with name or ID

```json
{
  "fixVersions": [
    {"name": "1.0"},
    {"name": "1.1"}
  ]
}
```

### Due Date

**Format:** String in YYYY-MM-DD format

```json
{
  "duedate": "2023-12-31"
}
```

### Time Tracking

**Format:** Object with originalEstimate, remainingEstimate

```json
{
  "timetracking": {
    "originalEstimate": "2h",
    "remainingEstimate": "1h 30m"
  }
}
```

Time formats: `1h`, `30m`, `2h 30m`, `1d`, `1w 2d 3h`

## Custom Fields

Custom fields use the format `customfield_XXXXX` where XXXXX is the field ID.

### Text Field

```json
{
  "customfield_10001": "Text value"
}
```

### Number Field

```json
{
  "customfield_10002": 42
}
```

### Date Field

```json
{
  "customfield_10003": "2023-12-31"
}
```

### DateTime Field

```json
{
  "customfield_10004": "2023-12-31T14:30:00.000+0000"
}
```

### Select List (Single)

```json
{
  "customfield_10005": {
    "value": "Option 1"
  }
}
```

### Select List (Multi)

```json
{
  "customfield_10006": [
    {"value": "Option 1"},
    {"value": "Option 2"}
  ]
}
```

### Checkbox

```json
{
  "customfield_10007": [
    {"value": "Checked Item 1"},
    {"value": "Checked Item 2"}
  ]
}
```

### Radio Buttons

```json
{
  "customfield_10008": {
    "value": "Selected Option"
  }
}
```

### User Picker (Single)

```json
{
  "customfield_10009": {
    "accountId": "5b10ac8d82e05b22cc7d4ef5"
  }
}
```

### User Picker (Multi)

```json
{
  "customfield_10010": [
    {"accountId": "5b10ac8d82e05b22cc7d4ef5"},
    {"accountId": "6a20bd9e93f16c33dd8e5fg6"}
  ]
}
```

### URL Field

```json
{
  "customfield_10011": "https://example.com"
}
```

### Labels (Custom)

```json
{
  "customfield_10012": ["label1", "label2"]
}
```

## Finding Custom Field IDs

To find custom field IDs:

1. **Via API:**
   ```
   GET /rest/api/3/field
   ```

2. **Via Issue JSON:**
   Get an issue and look at the fields returned

3. **Via JIRA UI:**
   - Go to Settings > Issues > Custom fields
   - Click on a custom field
   - The ID is in the URL: `customfield_10001`

## Validation Rules

### Summary
- **Required:** Yes
- **Type:** String
- **Max Length:** 255 characters

### Description
- **Required:** No (but recommended)
- **Type:** ADF object or string (legacy)
- **Max Length:** No limit

### Project
- **Required:** Yes
- **Type:** Object with key or ID

### Issue Type
- **Required:** Yes
- **Type:** Object with name or ID
- **Must be valid** for the project

### Priority
- **Required:** No
- **Type:** Object with name or ID
- **Must be valid** priority value

### Assignee
- **Required:** No
- **Type:** Object with accountId or null
- **Must have permission** to be assigned

### Labels
- **Required:** No
- **Type:** Array of strings
- **Format:** No spaces, alphanumeric + dashes/underscores

## Markdown to ADF Conversion

Our `adf_helper.py` library supports converting Markdown to ADF:

**Supported Markdown:**
- Headings: `# ## ###`
- Bold: `**text**`
- Italic: `*text*`
- Code: `` `code` ``
- Links: `[text](https://...)`
- Bullet lists: `- item`
- Numbered lists: `1. item`
- Code blocks: ` ```code``` `

**Example:**
```python
from adf_helper import markdown_to_adf

description = """
# Bug Report

## Steps to Reproduce
1. Go to login page
2. Enter credentials
3. Click **Login**

## Expected
User should be logged in

## Actual
Error message appears
"""

adf = markdown_to_adf(description)
```

## References

### Internal
- [API Examples](EXAMPLES.md) - Complete request/response examples
- [API Reference](api_reference.md) - Endpoint documentation

### External
- [ADF Specification](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)
- [ADF Builder](https://developer.atlassian.com/cloud/jira/platform/apis/document/playground/)
- [Field Types Reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/)
- [Custom Fields API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-custom-field-options/)
