"""
Unit tests for adf_helper module.

Tests wiki_markup_to_adf() and _parse_wiki_inline() functions for
converting JIRA wiki markup to Atlassian Document Format (ADF).
"""

import pytest
import sys
from pathlib import Path

# Add lib path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts' / 'lib'))

from jira_assistant_skills_lib import wiki_markup_to_adf, _parse_wiki_inline


@pytest.mark.unit
class TestWikiMarkupToAdf:
    """Tests for wiki_markup_to_adf function."""

    def test_empty_text(self):
        """Test handling of empty input."""
        result = wiki_markup_to_adf("")
        assert result == {
            "version": 1,
            "type": "doc",
            "content": []
        }

    def test_none_text(self):
        """Test handling of None input."""
        result = wiki_markup_to_adf(None)
        assert result == {
            "version": 1,
            "type": "doc",
            "content": []
        }

    def test_plain_text(self):
        """Test plain text without formatting."""
        result = wiki_markup_to_adf("Hello world")
        assert result["version"] == 1
        assert result["type"] == "doc"
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "paragraph"
        assert result["content"][0]["content"][0]["text"] == "Hello world"

    def test_bold_text(self):
        """Test *bold* formatting."""
        result = wiki_markup_to_adf("*Bold text*")
        content = result["content"][0]["content"]
        assert len(content) == 1
        assert content[0]["text"] == "Bold text"
        assert content[0]["marks"] == [{"type": "strong"}]

    def test_wiki_link(self):
        """Test [text|url] link formatting."""
        result = wiki_markup_to_adf("[Click here|https://example.com]")
        content = result["content"][0]["content"]
        assert len(content) == 1
        assert content[0]["text"] == "Click here"
        assert content[0]["marks"] == [
            {"type": "link", "attrs": {"href": "https://example.com"}}
        ]

    def test_mixed_bold_and_text(self):
        """Test combination of bold and plain text."""
        result = wiki_markup_to_adf("*Commit:* abc123")
        content = result["content"][0]["content"]
        assert len(content) == 2
        assert content[0]["text"] == "Commit:"
        assert content[0]["marks"] == [{"type": "strong"}]
        assert content[1]["text"] == " abc123"

    def test_bold_with_link(self):
        """Test bold field with link value (common commit format)."""
        result = wiki_markup_to_adf("*Commit:* [abc123|https://github.com/org/repo/commit/abc123]")
        content = result["content"][0]["content"]
        # Should be 3 parts: bold "Commit:", space " ", link "abc123"
        assert len(content) == 3
        # Bold label
        assert content[0]["text"] == "Commit:"
        assert content[0]["marks"] == [{"type": "strong"}]
        # Space between bold and link
        assert content[1]["text"] == " "
        # Linked value
        assert content[2]["text"] == "abc123"
        assert content[2]["marks"] == [
            {"type": "link", "attrs": {"href": "https://github.com/org/repo/commit/abc123"}}
        ]

    def test_multiline_text(self):
        """Test multiple lines create multiple paragraphs."""
        result = wiki_markup_to_adf("Line 1\nLine 2\nLine 3")
        assert len(result["content"]) == 3
        assert result["content"][0]["content"][0]["text"] == "Line 1"
        assert result["content"][1]["content"][0]["text"] == "Line 2"
        assert result["content"][2]["content"][0]["text"] == "Line 3"

    def test_empty_lines_skipped(self):
        """Test empty lines are not included."""
        result = wiki_markup_to_adf("Line 1\n\nLine 2")
        assert len(result["content"]) == 2

    def test_commit_comment_format(self):
        """Test typical commit comment format from link_commit.py."""
        comment = """Commit linked to this issue:

*Commit:* [abc1234|https://github.com/org/repo/commit/abc1234]
*Message:* Fix login bug
*Author:* John Doe
*Branch:* feature/fix-login
*Repository:* https://github.com/org/repo"""

        result = wiki_markup_to_adf(comment)

        # Should have 6 paragraphs (empty line is skipped)
        assert len(result["content"]) == 6

        # First line is plain text header
        assert result["content"][0]["content"][0]["text"] == "Commit linked to this issue:"

        # Second paragraph should have bold Commit: and a link
        commit_para = result["content"][1]["content"]
        bold_found = False
        link_found = False
        for node in commit_para:
            marks = node.get("marks", [])
            for mark in marks:
                if mark.get("type") == "strong":
                    bold_found = True
                if mark.get("type") == "link":
                    link_found = True
        assert bold_found, "Commit line should have bold text"
        assert link_found, "Commit line should have link"

    def test_pr_comment_format(self):
        """Test typical PR comment format from link_pr.py."""
        comment = """Pull Request linked to this issue:

*Pull Request:* [#123|https://github.com/org/repo/pull/123]
*Title:* Add new feature
*Status:* OPEN
*Author:* Jane Smith"""

        result = wiki_markup_to_adf(comment)

        # Should have 5 paragraphs
        assert len(result["content"]) == 5

        # PR line should have bold and link
        pr_para = result["content"][1]["content"]
        bold_found = False
        link_found = False
        for node in pr_para:
            marks = node.get("marks", [])
            for mark in marks:
                if mark.get("type") == "strong":
                    bold_found = True
                if mark.get("type") == "link":
                    link_found = True
        assert bold_found
        assert link_found


@pytest.mark.unit
class TestParseWikiInline:
    """Tests for _parse_wiki_inline helper function."""

    def test_empty_string(self):
        """Test empty string returns empty text node."""
        result = _parse_wiki_inline("")
        assert result == [{"type": "text", "text": ""}]

    def test_plain_text_only(self):
        """Test plain text without formatting."""
        result = _parse_wiki_inline("Plain text here")
        assert len(result) == 1
        assert result[0]["text"] == "Plain text here"
        assert "marks" not in result[0]

    def test_bold_only(self):
        """Test bold text only."""
        result = _parse_wiki_inline("*bold*")
        assert len(result) == 1
        assert result[0]["text"] == "bold"
        assert result[0]["marks"] == [{"type": "strong"}]

    def test_link_only(self):
        """Test wiki link only."""
        result = _parse_wiki_inline("[text|http://example.com]")
        assert len(result) == 1
        assert result[0]["text"] == "text"
        assert result[0]["marks"] == [
            {"type": "link", "attrs": {"href": "http://example.com"}}
        ]

    def test_text_before_bold(self):
        """Test plain text before bold."""
        result = _parse_wiki_inline("Hello *world*")
        assert len(result) == 2
        assert result[0]["text"] == "Hello "
        assert result[1]["text"] == "world"
        assert result[1]["marks"] == [{"type": "strong"}]

    def test_text_after_bold(self):
        """Test plain text after bold."""
        result = _parse_wiki_inline("*Hello* world")
        assert len(result) == 2
        assert result[0]["text"] == "Hello"
        assert result[0]["marks"] == [{"type": "strong"}]
        assert result[1]["text"] == " world"

    def test_multiple_bold_sections(self):
        """Test multiple bold sections."""
        result = _parse_wiki_inline("*first* and *second*")
        assert len(result) == 3
        assert result[0]["text"] == "first"
        assert result[0]["marks"] == [{"type": "strong"}]
        assert result[1]["text"] == " and "
        assert result[2]["text"] == "second"
        assert result[2]["marks"] == [{"type": "strong"}]

    def test_bold_with_colon(self):
        """Test bold text with colon (common field format)."""
        result = _parse_wiki_inline("*Field:* value")
        assert len(result) == 2
        assert result[0]["text"] == "Field:"
        assert result[0]["marks"] == [{"type": "strong"}]
        assert result[1]["text"] == " value"

    def test_link_with_special_chars_in_url(self):
        """Test link with special characters in URL."""
        result = _parse_wiki_inline("[click|https://example.com/path?query=1&other=2]")
        assert len(result) == 1
        assert result[0]["text"] == "click"
        assert result[0]["marks"][0]["attrs"]["href"] == "https://example.com/path?query=1&other=2"

    def test_bold_followed_by_link(self):
        """Test bold followed by link (field with link value)."""
        result = _parse_wiki_inline("*Commit:* [abc|http://example.com]")
        # Should be: bold "Commit:", space, link "abc"
        assert len(result) == 3
        assert result[0]["text"] == "Commit:"
        assert result[0]["marks"] == [{"type": "strong"}]
        assert result[1]["text"] == " "
        assert result[2]["text"] == "abc"
        assert result[2]["marks"][0]["type"] == "link"
