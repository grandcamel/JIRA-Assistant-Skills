"""
Tests for get_kb_article.py script.

Tests KB article retrieval and formatting.
"""

import pytest
from unittest.mock import patch, Mock
import json
from pathlib import Path
import sys

scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import get_kb_article


@pytest.mark.jsm
@pytest.mark.unit
class TestGetKBArticle:
    """Test KB article retrieval functionality."""

    def test_get_kb_article_by_id(self, mock_jira_client, sample_kb_article):
        """Test fetching article by ID."""
        mock_jira_client.get_kb_article.return_value = sample_kb_article

        with patch('get_kb_article.get_jira_client', return_value=mock_jira_client):
            result = get_kb_article.get_kb_article("131073")

        assert result['id'] == "131073"
        assert result['title'] == "How to reset your password"
        mock_jira_client.get_kb_article.assert_called_once_with("131073")

    def test_format_text(self, sample_kb_article):
        """Test human-readable output."""
        output = get_kb_article.format_text(sample_kb_article)

        assert "How to reset your password" in output
        assert "If you forgot your" in output

    def test_format_json(self, sample_kb_article):
        """Test JSON output format."""
        output = get_kb_article.format_json(sample_kb_article)

        data = json.loads(output)
        assert data['id'] == "131073"
        assert data['title'] == "How to reset your password"

    def test_get_kb_article_with_source(self, sample_kb_article):
        """Test article includes source information."""
        output = get_kb_article.format_text(sample_kb_article)

        assert "Source: confluence" in output

    def test_get_kb_article_with_link(self, sample_kb_article):
        """Test article includes URL link."""
        output = get_kb_article.format_text(sample_kb_article)

        assert "URL:" in output
        assert "wiki/spaces/KB/pages/131073" in output

    def test_get_kb_article_error(self, mock_jira_client):
        """Test error when article doesn't exist."""
        from error_handler import NotFoundError
        mock_jira_client.get_kb_article.side_effect = NotFoundError("Article not found")

        with patch('get_kb_article.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(NotFoundError, match="Article not found"):
                get_kb_article.get_kb_article("999999")
