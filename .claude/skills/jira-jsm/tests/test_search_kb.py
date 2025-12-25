"""
Tests for search_kb.py script.

Tests KB article search functionality with query terms and result formatting.
"""

import pytest
from unittest.mock import patch, Mock
import json
from pathlib import Path
import sys

scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import search_kb


class TestSearchKB:
    """Test KB search functionality."""

    def test_search_kb_basic(self, mock_jira_client, sample_kb_search_results):
        """Test basic KB search with query term."""
        mock_jira_client.search_kb_articles.return_value = sample_kb_search_results

        with patch('search_kb.get_jira_client', return_value=mock_jira_client):
            results = search_kb.search_kb(1, "password")

        assert len(results) == 3
        assert results[0]['title'] == "How to reset your password"
        mock_jira_client.search_kb_articles.assert_called_once_with(1, "password", 50)

    def test_search_kb_with_max_results(self, mock_jira_client, sample_kb_search_results):
        """Test search with custom max results limit."""
        mock_jira_client.search_kb_articles.return_value = sample_kb_search_results[:2]

        with patch('search_kb.get_jira_client', return_value=mock_jira_client):
            results = search_kb.search_kb(1, "password", max_results=2)

        assert len(results) == 2
        mock_jira_client.search_kb_articles.assert_called_once_with(1, "password", 2)

    def test_search_kb_no_results(self, mock_jira_client):
        """Test behavior when no articles match."""
        mock_jira_client.search_kb_articles.return_value = []

        with patch('search_kb.get_jira_client', return_value=mock_jira_client):
            results = search_kb.search_kb(1, "nonexistent")

        assert len(results) == 0

    def test_format_text(self, sample_kb_search_results):
        """Test human-readable output format."""
        output = search_kb.format_text(sample_kb_search_results)

        assert "Knowledge Base Search Results (3 articles)" in output
        assert "How to reset your password" in output
        assert "Password policy requirements" in output
        assert "Troubleshooting login issues" in output

    def test_format_text_no_results(self):
        """Test text format with no results."""
        output = search_kb.format_text([])

        assert "No KB articles found" in output

    def test_format_json(self, sample_kb_search_results):
        """Test JSON output format."""
        output = search_kb.format_json(sample_kb_search_results)

        data = json.loads(output)
        assert len(data) == 3
        assert data[0]['id'] == "131073"

    def test_search_kb_with_highlighting(self, sample_kb_search_results):
        """Test search with excerpts highlighting."""
        # Verify excerpts contain <em> tags for highlighting
        assert '<em>password</em>' in sample_kb_search_results[0]['excerpt']
