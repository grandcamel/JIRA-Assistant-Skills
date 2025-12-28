# Comment Formats Reference

Advanced reference for comment formatting options.

---

## Input Formats

The `--format` option controls how your comment body is interpreted:

| Format | Description | Use Case |
|--------|-------------|----------|
| `text` | Plain text (default) | Simple comments |
| `markdown` | Markdown syntax | Formatted comments |
| `adf` | Raw ADF JSON | Advanced formatting |

---

## Plain Text (default)

```bash
python add_comment.py PROJ-123 --body "Simple plain text comment"
```

- No formatting applied
- Newlines preserved
- Special characters shown as-is

---

## Markdown

```bash
python add_comment.py PROJ-123 --format markdown --body "**Bold** and *italic*"
```

### Supported Syntax

| Element | Syntax | Result |
|---------|--------|--------|
| Bold | `**text**` | **text** |
| Italic | `*text*` | *text* |
| Code | `` `code` `` | `code` |
| Heading 1 | `# Heading` | Heading |
| Heading 2 | `## Heading` | Heading |
| Heading 3 | `### Heading` | Heading |
| Link | `[text](https://...)` | clickable link |
| Bullet list | `- item` | bullet item |
| Numbered list | `1. item` | numbered item |
| Code block | ` ```code``` ` | code block |

### Multi-line Example

```bash
python add_comment.py PROJ-123 --format markdown --body "$(cat <<'EOF'
## Update

Fixed the issue by:
1. Restarting the service
2. Clearing the cache

**Status:** Done
EOF
)"
```

---

## ADF (Advanced)

For complex formatting not supported by Markdown, use raw ADF JSON:

```bash
python add_comment.py PROJ-123 --format adf --body '{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Hello "},
        {"type": "text", "text": "world", "marks": [{"type": "strong"}]}
      ]
    }
  ]
}'
```

### ADF Structure

```json
{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Your text here"}
      ]
    }
  ]
}
```

### ADF Node Types

| Type | Description |
|------|-------------|
| `paragraph` | Text paragraph |
| `heading` | Heading (attrs: level 1-6) |
| `bulletList` | Unordered list |
| `orderedList` | Ordered list |
| `listItem` | List item |
| `codeBlock` | Code block |
| `blockquote` | Quote block |
| `rule` | Horizontal rule |
| `table` | Table |

### ADF Mark Types

| Mark | Description |
|------|-------------|
| `strong` | Bold |
| `em` | Italic |
| `code` | Inline code |
| `link` | Hyperlink (attrs: href) |
| `underline` | Underline |
| `strike` | Strikethrough |

---

## Using the Helper Library

For Python scripts, use the adf_helper module:

```python
from adf_helper import text_to_adf, markdown_to_adf, adf_to_text

# Plain text to ADF
adf = text_to_adf("Simple comment")

# Markdown to ADF
adf = markdown_to_adf("**Bold** text")

# ADF back to plain text
text = adf_to_text(adf_document)
```

---

## See Also

- [adf_guide.md](adf_guide.md) - Quick ADF usage guide
- [ADF Specification](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/) - Official docs
