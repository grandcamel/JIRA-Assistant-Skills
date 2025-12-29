# Atlassian Document Format (ADF) Guide

Quick guide for using ADF in comments and descriptions.

## Using Our Helper Library

The easiest way to create ADF content is using our helper library:

```python
from adf_helper import text_to_adf, markdown_to_adf

# Plain text
adf = text_to_adf("This is a simple comment")

# Markdown
markdown = """
# Heading

This is **bold** and this is *italic*.

- Bullet 1
- Bullet 2
"""
adf = markdown_to_adf(markdown)
```

## With Scripts

```bash
# Plain text (default)
python add_comment.py PROJ-123 --body "Simple comment"

# Markdown
python add_comment.py PROJ-123 --body "**Bold** text" --format markdown

# Complex markdown
python add_comment.py PROJ-123 --format markdown --body "$(cat <<'EOF'
## Update

Fixed the issue by:
1. Restarting the service
2. Clearing the cache

**Status:** Done
EOF
)"
```

## Supported Markdown

- Headings: `#`, `##`, `###`
- Bold: `**text**`
- Italic: `*text*`
- Code: `` `code` ``
- Links: `[text](https://...)`
- Bullet lists: `- item`
- Numbered lists: `1. item`
- Code blocks: ` ```code``` `

## Direct ADF Format

For advanced use cases, you can provide ADF JSON directly:

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

## See Also

- `field_formats.md` in jira-issue skill for complete ADF reference
- [ADF Specification](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)
