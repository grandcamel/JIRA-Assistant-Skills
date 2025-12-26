"""
Tests for jql_validate.py - Validate JQL syntax.
"""

import pytest
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.search
@pytest.mark.unit
class TestValidateJQL:
    """Tests for JQL validation."""

    def test_validate_valid_jql(self, mock_jira_client, sample_jql_parse_valid):
        """Test validating a correct JQL query."""
        mock_jira_client.parse_jql.return_value = sample_jql_parse_valid

        from jql_validate import validate_jql

        result = validate_jql(mock_jira_client, 'project = PROJ AND status = Open')

        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert 'structure' in result

    def test_validate_invalid_field(self, mock_jira_client, sample_jql_parse_invalid):
        """Test detecting invalid field names."""
        mock_jira_client.parse_jql.return_value = sample_jql_parse_invalid

        from jql_validate import validate_jql

        result = validate_jql(mock_jira_client, 'projct = PROJ AND statuss = Open')

        assert result['valid'] is False
        assert len(result['errors']) == 2
        assert 'projct' in result['errors'][0]

    def test_validate_invalid_operator(self, mock_jira_client):
        """Test detecting invalid operator for field type."""
        mock_jira_client.parse_jql.return_value = {
            'queries': [{
                'query': 'status ~ "Open"',
                'errors': ["The operator '~' is not supported by the 'status' field."]
            }]
        }

        from jql_validate import validate_jql

        result = validate_jql(mock_jira_client, 'status ~ "Open"')

        assert result['valid'] is False
        assert 'operator' in result['errors'][0].lower() or '~' in result['errors'][0]

    def test_validate_invalid_syntax(self, mock_jira_client):
        """Test detecting syntax errors."""
        mock_jira_client.parse_jql.return_value = {
            'queries': [{
                'query': 'project = AND status = Open',
                'errors': ["Error in the JQL Query: Expecting either a value or function."]
            }]
        }

        from jql_validate import validate_jql

        result = validate_jql(mock_jira_client, 'project = AND status = Open')

        assert result['valid'] is False
        assert len(result['errors']) > 0

    def test_validate_multiple_queries(self, mock_jira_client):
        """Test validating multiple queries at once."""
        mock_jira_client.parse_jql.return_value = {
            'queries': [
                {
                    'query': 'project = PROJ',
                    'errors': []
                },
                {
                    'query': 'type = Bug',
                    'errors': []
                }
            ]
        }

        from jql_validate import validate_multiple

        results = validate_multiple(mock_jira_client, ['project = PROJ', 'type = Bug'])

        assert len(results) == 2
        assert all(r['valid'] for r in results)

    def test_show_parsed_structure(self, mock_jira_client, sample_jql_parse_valid):
        """Test showing parsed query structure."""
        mock_jira_client.parse_jql.return_value = sample_jql_parse_valid

        from jql_validate import format_validation_result

        result = {
            'valid': True,
            'query': 'project = PROJ AND status = Open',
            'errors': [],
            'structure': sample_jql_parse_valid['queries'][0].get('structure')
        }
        output = format_validation_result(result, show_structure=True)

        assert 'Valid JQL' in output
        assert 'project' in output.lower()

    def test_suggest_corrections(self, mock_jira_client):
        """Test suggesting corrections for errors."""
        mock_jira_client.parse_jql.return_value = {
            'queries': [{
                'query': 'statuss = Open',
                'errors': ["Field 'statuss' does not exist or you do not have permission to view it."]
            }]
        }

        from jql_validate import validate_jql, suggest_correction

        result = validate_jql(mock_jira_client, 'statuss = Open')

        assert result['valid'] is False
        # Test suggestion function
        suggestion = suggest_correction('statuss', ['status', 'summary', 'sprint'])
        assert suggestion == 'status'


@pytest.mark.search
@pytest.mark.unit
class TestJqlValidateErrorHandling:
    """Test API error handling scenarios for jql_validate."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError
        mock_jira_client.parse_jql.side_effect = AuthenticationError(
            "Invalid API token"
        )

        from jql_validate import validate_jql

        with pytest.raises(AuthenticationError):
            validate_jql(mock_jira_client, 'project = PROJ')

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError
        mock_jira_client.parse_jql.side_effect = PermissionError(
            "You don't have permission to access this resource"
        )

        from jql_validate import validate_jql

        with pytest.raises(PermissionError):
            validate_jql(mock_jira_client, 'project = PROJ')

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_jira_client.parse_jql.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from jql_validate import validate_jql

        with pytest.raises(JiraError) as exc_info:
            validate_jql(mock_jira_client, 'project = PROJ')
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 internal server error."""
        from error_handler import JiraError
        mock_jira_client.parse_jql.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from jql_validate import validate_jql

        with pytest.raises(JiraError) as exc_info:
            validate_jql(mock_jira_client, 'project = PROJ')
        assert exc_info.value.status_code == 500
