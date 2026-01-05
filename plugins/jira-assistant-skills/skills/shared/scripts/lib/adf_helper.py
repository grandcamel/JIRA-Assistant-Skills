"""
Atlassian Document Format (ADF) utilities.

Provides functions to convert between markdown, plain text, and ADF format
used by JIRA for rich text fields like descriptions and comments.
"""

import re
from typing import Any


def text_to_adf(text: str) -> dict[str, Any]:
    """
    Convert plain text to ADF format.

    Args:
        text: Plain text string

    Returns:
        ADF document dictionary
    """
    if not text:
        return {"version": 1, "type": "doc", "content": []}

    paragraphs = text.split("\n")
    content = []

    for para in paragraphs:
        if para.strip():
            content.append(
                {"type": "paragraph", "content": [{"type": "text", "text": para}]}
            )

    return {"version": 1, "type": "doc", "content": content if content else []}


def markdown_to_adf(markdown: str) -> dict[str, Any]:
    """
    Convert markdown to ADF format (basic conversion).

    Supports:
    - Headings (# ## ###)
    - Bold (**text**)
    - Italic (*text*)
    - Code (`code`)
    - Links [text](url)
    - Bullet lists (- item)
    - Numbered lists (1. item)
    - Code blocks (```code```)

    Args:
        markdown: Markdown text

    Returns:
        ADF document dictionary
    """
    if not markdown:
        return text_to_adf("")

    lines = markdown.split("\n")
    content = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            content.append(
                {
                    "type": "codeBlock",
                    "content": [{"type": "text", "text": "\n".join(code_lines)}],
                }
            )
            i += 1
            continue

        if line.startswith("# "):
            content.append(
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": line[2:].strip()}],
                }
            )
        elif line.startswith("## "):
            content.append(
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": line[3:].strip()}],
                }
            )
        elif line.startswith("### "):
            content.append(
                {
                    "type": "heading",
                    "attrs": {"level": 3},
                    "content": [{"type": "text", "text": line[4:].strip()}],
                }
            )
        elif line.startswith("- ") or line.startswith("* "):
            list_items = []
            while i < len(lines) and (
                lines[i].startswith("- ") or lines[i].startswith("* ")
            ):
                item_text = lines[i][2:].strip()
                list_items.append(
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": _parse_inline_formatting(item_text),
                            }
                        ],
                    }
                )
                i += 1
            content.append({"type": "bulletList", "content": list_items})
            continue
        elif re.match(r"^\d+\.\s", line):
            list_items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i]):
                item_text = re.sub(r"^\d+\.\s", "", lines[i])
                list_items.append(
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": _parse_inline_formatting(item_text),
                            }
                        ],
                    }
                )
                i += 1
            content.append({"type": "orderedList", "content": list_items})
            continue
        elif line.strip():
            content.append(
                {"type": "paragraph", "content": _parse_inline_formatting(line)}
            )

        i += 1

    return {"version": 1, "type": "doc", "content": content if content else []}


def _parse_inline_formatting(text: str) -> list[dict[str, Any]]:
    """
    Parse inline markdown formatting (bold, italic, code, links).

    Args:
        text: Text with inline markdown

    Returns:
        List of ADF text nodes with formatting
    """
    if not text:
        return [{"type": "text", "text": ""}]

    result = []
    remaining = text

    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    bold_pattern = r"\*\*([^*]+)\*\*"
    italic_pattern = r"\*([^*]+)\*"
    code_pattern = r"`([^`]+)`"

    while remaining:
        link_match = re.search(link_pattern, remaining)
        bold_match = re.search(bold_pattern, remaining)
        italic_match = re.search(italic_pattern, remaining)
        code_match = re.search(code_pattern, remaining)

        matches = [
            (link_match, "link") if link_match else None,
            (bold_match, "bold") if bold_match else None,
            (italic_match, "italic") if italic_match else None,
            (code_match, "code") if code_match else None,
        ]
        matches = [m for m in matches if m is not None]

        if not matches:
            if remaining:
                result.append({"type": "text", "text": remaining})
            break

        matches.sort(key=lambda x: x[0].start())
        match, match_type = matches[0]

        if match.start() > 0:
            result.append({"type": "text", "text": remaining[: match.start()]})

        if match_type == "link":
            result.append(
                {
                    "type": "text",
                    "text": match.group(1),
                    "marks": [{"type": "link", "attrs": {"href": match.group(2)}}],
                }
            )
        elif match_type == "bold":
            result.append(
                {"type": "text", "text": match.group(1), "marks": [{"type": "strong"}]}
            )
        elif match_type == "italic":
            result.append(
                {"type": "text", "text": match.group(1), "marks": [{"type": "em"}]}
            )
        elif match_type == "code":
            result.append(
                {"type": "text", "text": match.group(1), "marks": [{"type": "code"}]}
            )

        remaining = remaining[match.end() :]

    return result if result else [{"type": "text", "text": ""}]


def adf_to_text(adf: dict[str, Any]) -> str:
    """
    Convert ADF to plain text (extract text content).

    Args:
        adf: ADF document dictionary

    Returns:
        Plain text string
    """
    if not adf or "content" not in adf:
        return ""

    lines = []
    for node in adf["content"]:
        lines.append(_node_to_text(node))

    return "\n".join(lines).strip()


def _node_to_text(node: dict[str, Any]) -> str:
    """
    Convert a single ADF node to text.

    Args:
        node: ADF node dictionary

    Returns:
        Plain text string
    """
    node_type = node.get("type")

    if node_type == "text":
        return node.get("text", "")

    if node_type == "paragraph":
        content = node.get("content", [])
        return " ".join(_node_to_text(n) for n in content)

    if node_type == "heading":
        content = node.get("content", [])
        level = node.get("attrs", {}).get("level", 1)
        prefix = "#" * level
        return f"{prefix} {' '.join(_node_to_text(n) for n in content)}"

    if node_type in ("bulletList", "orderedList"):
        items = node.get("content", [])
        result = []
        for i, item in enumerate(items):
            prefix = "-" if node_type == "bulletList" else f"{i + 1}."
            item_content = item.get("content", [])
            text = " ".join(_node_to_text(n) for n in item_content)
            result.append(f"{prefix} {text}")
        return "\n".join(result)

    if node_type == "listItem":
        content = node.get("content", [])
        return " ".join(_node_to_text(n) for n in content)

    if node_type == "codeBlock":
        content = node.get("content", [])
        code = " ".join(_node_to_text(n) for n in content)
        return f"```\n{code}\n```"

    if "content" in node:
        return " ".join(_node_to_text(n) for n in node["content"])

    return ""


def create_adf_paragraph(text: str, **marks) -> dict[str, Any]:
    """
    Create an ADF paragraph with optional formatting.

    Args:
        text: Text content
        **marks: Formatting marks (bold=True, italic=True, etc.)

    Returns:
        ADF paragraph node
    """
    text_marks = []
    if marks.get("bold"):
        text_marks.append({"type": "strong"})
    if marks.get("italic"):
        text_marks.append({"type": "em"})
    if marks.get("code"):
        text_marks.append({"type": "code"})
    if marks.get("link"):
        text_marks.append({"type": "link", "attrs": {"href": marks["link"]}})

    text_node = {"type": "text", "text": text}
    if text_marks:
        text_node["marks"] = text_marks

    return {"type": "paragraph", "content": [text_node]}


def create_adf_heading(text: str, level: int = 1) -> dict[str, Any]:
    """
    Create an ADF heading.

    Args:
        text: Heading text
        level: Heading level (1-6)

    Returns:
        ADF heading node
    """
    return {
        "type": "heading",
        "attrs": {"level": min(max(level, 1), 6)},
        "content": [{"type": "text", "text": text}],
    }


def create_adf_code_block(code: str, language: str = "") -> dict[str, Any]:
    """
    Create an ADF code block.

    Args:
        code: Code content
        language: Programming language (optional)

    Returns:
        ADF code block node
    """
    attrs = {}
    if language:
        attrs["language"] = language

    node = {"type": "codeBlock", "content": [{"type": "text", "text": code}]}

    if attrs:
        node["attrs"] = attrs

    return node


def wiki_markup_to_adf(text: str) -> dict[str, Any]:
    """
    Convert JIRA wiki markup to ADF format.

    Supports:
    - *bold* -> strong text
    - [text|url] -> linked text
    - Plain text paragraphs

    This is commonly used for formatting commit/PR comments that use
    wiki-style markup like "*Field:* [link_text|url]".

    Args:
        text: Text with wiki markup

    Returns:
        ADF document dictionary

    Example:
        >>> wiki_markup_to_adf("*Commit:* [abc123|https://github.com/org/repo/commit/abc123]")
        {
            "version": 1,
            "type": "doc",
            "content": [...]
        }
    """
    if not text:
        return {"version": 1, "type": "doc", "content": []}

    lines = text.split("\n")
    content_blocks = []

    for line in lines:
        if line.strip():
            content_blocks.append(
                {"type": "paragraph", "content": _parse_wiki_inline(line)}
            )

    return {
        "version": 1,
        "type": "doc",
        "content": content_blocks if content_blocks else [],
    }


def _parse_wiki_inline(text: str) -> list[dict[str, Any]]:
    """
    Parse wiki-style inline formatting.

    Handles:
    - *bold text* -> strong
    - [text|url] -> link

    Args:
        text: Text with wiki inline formatting

    Returns:
        List of ADF text nodes with formatting
    """
    if not text:
        return [{"type": "text", "text": ""}]

    result = []
    remaining = text

    # Patterns for wiki markup
    # *bold* - matches *text* but not ** (empty bold)
    bold_pattern = r"\*([^*]+)\*"
    # [text|url] - wiki-style links
    link_pattern = r"\[([^\]|]+)\|([^\]]+)\]"

    while remaining:
        bold_match = re.search(bold_pattern, remaining)
        link_match = re.search(link_pattern, remaining)

        # Collect valid matches
        matches = []
        if bold_match:
            matches.append((bold_match, "bold"))
        if link_match:
            matches.append((link_match, "link"))

        if not matches:
            # No more matches, add remaining text
            if remaining:
                result.append({"type": "text", "text": remaining})
            break

        # Process the match that appears first
        matches.sort(key=lambda x: x[0].start())
        match, match_type = matches[0]

        # Add any text before the match
        if match.start() > 0:
            result.append({"type": "text", "text": remaining[: match.start()]})

        if match_type == "bold":
            result.append(
                {"type": "text", "text": match.group(1), "marks": [{"type": "strong"}]}
            )
        elif match_type == "link":
            result.append(
                {
                    "type": "text",
                    "text": match.group(1),
                    "marks": [{"type": "link", "attrs": {"href": match.group(2)}}],
                }
            )

        remaining = remaining[match.end() :]

    return result if result else [{"type": "text", "text": ""}]
