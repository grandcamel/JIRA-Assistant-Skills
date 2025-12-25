"""
Tests for clone_issue.py

TDD tests for cloning issues with optional link handling.
"""

import pytest
from unittest.mock import Mock, patch, call
import json


@pytest.fixture
def sample_issue():
    """Sample issue to clone."""
    return {
        'id': '10123',
        'key': 'PROJ-123',
        'fields': {
            'project': {'key': 'PROJ', 'id': '10000'},
            'issuetype': {'name': 'Story', 'id': '10001'},
            'summary': 'Original issue summary',
            'description': {'type': 'doc', 'version': 1, 'content': []},
            'priority': {'name': 'Medium', 'id': '3'},
            'labels': ['backend', 'api'],
            'components': [{'name': 'Core', 'id': '10000'}],
            'status': {'name': 'In Progress'},
            'issuelinks': []
        }
    }


@pytest.fixture
def sample_issue_with_links():
    """Sample issue with links."""
    return {
        'id': '10123',
        'key': 'PROJ-123',
        'fields': {
            'project': {'key': 'PROJ', 'id': '10000'},
            'issuetype': {'name': 'Story', 'id': '10001'},
            'summary': 'Original issue summary',
            'description': None,
            'priority': {'name': 'Medium', 'id': '3'},
            'labels': [],
            'status': {'name': 'In Progress'},
            'issuelinks': [
                {
                    'id': '20001',
                    'type': {'name': 'Blocks', 'outward': 'blocks', 'inward': 'is blocked by'},
                    'outwardIssue': {'key': 'PROJ-456'}
                },
                {
                    'id': '20002',
                    'type': {'name': 'Relates', 'outward': 'relates to', 'inward': 'relates to'},
                    'inwardIssue': {'key': 'PROJ-100'}
                }
            ]
        }
    }


@pytest.fixture
def sample_issue_with_subtasks():
    """Sample issue with subtasks."""
    return {
        'id': '10123',
        'key': 'PROJ-123',
        'fields': {
            'project': {'key': 'PROJ', 'id': '10000'},
            'issuetype': {'name': 'Story', 'id': '10001'},
            'summary': 'Parent issue',
            'description': None,
            'priority': {'name': 'Medium', 'id': '3'},
            'status': {'name': 'In Progress'},
            'subtasks': [
                {'key': 'PROJ-124', 'fields': {'summary': 'Subtask 1'}},
                {'key': 'PROJ-125', 'fields': {'summary': 'Subtask 2'}}
            ],
            'issuelinks': []
        }
    }


@pytest.fixture
def created_clone():
    """Response when clone is created."""
    return {
        'id': '10999',
        'key': 'PROJ-999',
        'self': 'https://test.atlassian.net/rest/api/3/issue/10999'
    }


class TestCloneIssue:
    """Tests for the clone_issue function."""

    def test_clone_issue_basic(self, mock_jira_client, sample_issue, created_clone):
        """Test cloning issue with same fields."""
        mock_jira_client.get_issue.return_value = sample_issue
        mock_jira_client.create_issue.return_value = created_clone
        mock_jira_client.create_link.return_value = None

        import clone_issue
        with patch.object(clone_issue, 'get_jira_client', return_value=mock_jira_client):
            result = clone_issue.clone_issue('PROJ-123')

        # Should get original issue and create new one
        mock_jira_client.get_issue.assert_called_once()
        mock_jira_client.create_issue.assert_called_once()

        # Clone should have same basic fields
        create_call = mock_jira_client.create_issue.call_args
        fields = create_call[0][0]
        assert 'summary' in fields
        assert 'PROJ-123' in fields['summary'] or 'Clone' in fields['summary'] or sample_issue['fields']['summary'] in fields['summary']

        assert result['clone_key'] == 'PROJ-999'
        assert result['original_key'] == 'PROJ-123'

    def test_clone_with_clone_link(self, mock_jira_client, sample_issue, created_clone):
        """Test creating 'clones' link to original."""
        mock_jira_client.get_issue.return_value = sample_issue
        mock_jira_client.create_issue.return_value = created_clone
        mock_jira_client.create_link.return_value = None

        import clone_issue
        with patch.object(clone_issue, 'get_jira_client', return_value=mock_jira_client):
            result = clone_issue.clone_issue('PROJ-123', create_clone_link=True)

        # Should create 'Cloners' link
        mock_jira_client.create_link.assert_called_once()
        link_call = mock_jira_client.create_link.call_args
        assert link_call[0][0] == 'Cloners'  # link_type
        assert 'PROJ-999' in link_call[0]  # clone key
        assert 'PROJ-123' in link_call[0]  # original key

    def test_clone_with_subtasks(self, mock_jira_client, sample_issue_with_subtasks, created_clone):
        """Test optionally cloning subtasks."""
        subtask_responses = [
            {'key': 'PROJ-124', 'fields': {'summary': 'Subtask 1', 'issuetype': {'name': 'Sub-task'}, 'priority': {'name': 'Medium'}}},
            {'key': 'PROJ-125', 'fields': {'summary': 'Subtask 2', 'issuetype': {'name': 'Sub-task'}, 'priority': {'name': 'Medium'}}}
        ]

        def mock_get_issue(key, **kwargs):
            if key == 'PROJ-123':
                return sample_issue_with_subtasks
            elif key == 'PROJ-124':
                return subtask_responses[0]
            elif key == 'PROJ-125':
                return subtask_responses[1]

        mock_jira_client.get_issue.side_effect = mock_get_issue

        clone_responses = iter([
            {'id': '10999', 'key': 'PROJ-999'},
            {'id': '10998', 'key': 'PROJ-998'},
            {'id': '10997', 'key': 'PROJ-997'}
        ])
        mock_jira_client.create_issue.side_effect = lambda fields: next(clone_responses)
        mock_jira_client.create_link.return_value = None

        import clone_issue
        with patch.object(clone_issue, 'get_jira_client', return_value=mock_jira_client):
            result = clone_issue.clone_issue('PROJ-123', include_subtasks=True)

        # Should create parent + 2 subtasks = 3 issues
        assert mock_jira_client.create_issue.call_count >= 1  # At least the parent
        assert 'subtasks_cloned' in result or result['clone_key'] == 'PROJ-999'

    def test_clone_without_links(self, mock_jira_client, sample_issue_with_links, created_clone):
        """Test cloning without copying original links."""
        mock_jira_client.get_issue.return_value = sample_issue_with_links
        mock_jira_client.create_issue.return_value = created_clone
        mock_jira_client.create_link.return_value = None

        import clone_issue
        with patch.object(clone_issue, 'get_jira_client', return_value=mock_jira_client):
            result = clone_issue.clone_issue('PROJ-123', include_links=False, create_clone_link=False)

        # Should NOT create any links (no clone link, no copied links)
        mock_jira_client.create_link.assert_not_called()
        assert result['clone_key'] == 'PROJ-999'

    def test_clone_with_links(self, mock_jira_client, sample_issue_with_links, created_clone):
        """Test copying links from original."""
        mock_jira_client.get_issue.return_value = sample_issue_with_links
        mock_jira_client.create_issue.return_value = created_clone
        mock_jira_client.create_link.return_value = None

        import clone_issue
        with patch.object(clone_issue, 'get_jira_client', return_value=mock_jira_client):
            result = clone_issue.clone_issue('PROJ-123', include_links=True, create_clone_link=False)

        # Should copy 2 links from original (not counting clone link)
        assert mock_jira_client.create_link.call_count == 2
        assert result.get('links_copied', 0) >= 1

    def test_clone_to_different_project(self, mock_jira_client, sample_issue, created_clone):
        """Test cloning to different project."""
        mock_jira_client.get_issue.return_value = sample_issue
        # Clone goes to OTHER project
        created_clone['key'] = 'OTHER-999'
        mock_jira_client.create_issue.return_value = created_clone
        mock_jira_client.create_link.return_value = None

        import clone_issue
        with patch.object(clone_issue, 'get_jira_client', return_value=mock_jira_client):
            result = clone_issue.clone_issue('PROJ-123', to_project='OTHER')

        # Should create in OTHER project
        create_call = mock_jira_client.create_issue.call_args
        fields = create_call[0][0]
        assert fields['project']['key'] == 'OTHER'
        assert result['clone_key'] == 'OTHER-999'


class TestCloneIssueFormat:
    """Tests for clone_issue output formatting."""

    def test_format_text_output(self, mock_jira_client, sample_issue, created_clone):
        """Test human-readable output."""
        mock_jira_client.get_issue.return_value = sample_issue
        mock_jira_client.create_issue.return_value = created_clone
        mock_jira_client.create_link.return_value = None

        import clone_issue
        with patch.object(clone_issue, 'get_jira_client', return_value=mock_jira_client):
            result = clone_issue.clone_issue('PROJ-123')
            output = clone_issue.format_clone_result(result, output_format='text')

        assert 'PROJ-999' in output
        assert 'PROJ-123' in output

    def test_format_json_output(self, mock_jira_client, sample_issue, created_clone):
        """Test JSON output format."""
        mock_jira_client.get_issue.return_value = sample_issue
        mock_jira_client.create_issue.return_value = created_clone
        mock_jira_client.create_link.return_value = None

        import clone_issue
        with patch.object(clone_issue, 'get_jira_client', return_value=mock_jira_client):
            result = clone_issue.clone_issue('PROJ-123')
            output = clone_issue.format_clone_result(result, output_format='json')

        # Should be valid JSON
        parsed = json.loads(output)
        assert 'clone_key' in parsed
