"""
Tests for suggest_kb.py script.

Tests KB suggestion functionality for service requests.
"""

import pytest
from unittest.mock import patch, Mock
import json
from pathlib import Path
import sys

scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import suggest_kb


@pytest.mark.jsm
@pytest.mark.unit
class TestSuggestKB:
    """Test KB suggestion functionality."""

    def test_suggest_kb_basic(self, mock_jira_client, sample_kb_search_results):
        """Test suggesting articles based on request."""
        mock_jira_client.suggest_kb_for_request.return_value = sample_kb_search_results[:3]

        with patch('suggest_kb.get_jira_client', return_value=mock_jira_client):
            suggestions = suggest_kb.suggest_kb("REQ-123")

        assert len(suggestions) == 3
        mock_jira_client.suggest_kb_for_request.assert_called_once_with("REQ-123", 5)

    def test_suggest_kb_max_suggestions(self, mock_jira_client, sample_kb_search_results):
        """Test limiting number of suggestions."""
        mock_jira_client.suggest_kb_for_request.return_value = sample_kb_search_results[:2]

        with patch('suggest_kb.get_jira_client', return_value=mock_jira_client):
            suggestions = suggest_kb.suggest_kb("REQ-123", max_suggestions=2)

        assert len(suggestions) == 2
        mock_jira_client.suggest_kb_for_request.assert_called_once_with("REQ-123", 2)

    def test_suggest_kb_no_matches(self, mock_jira_client):
        """Test when no relevant articles found."""
        mock_jira_client.suggest_kb_for_request.return_value = []

        with patch('suggest_kb.get_jira_client', return_value=mock_jira_client):
            suggestions = suggest_kb.suggest_kb("REQ-123")

        assert len(suggestions) == 0

    def test_format_text(self, sample_kb_search_results):
        """Test human-readable output format."""
        output = suggest_kb.format_text(sample_kb_search_results[:3], "REQ-123")

        assert "REQ-123" in output
        assert "3 suggestions" in output
        assert "How to reset your password" in output

    def test_format_text_no_suggestions(self):
        """Test text format with no suggestions."""
        output = suggest_kb.format_text([], "REQ-123")

        assert "No KB article suggestions" in output
        assert "REQ-123" in output

    def test_format_json(self, sample_kb_search_results):
        """Test JSON output format."""
        output = suggest_kb.format_json(sample_kb_search_results)

        data = json.loads(output)
        assert len(data) >= 1
        assert 'title' in data[0]
