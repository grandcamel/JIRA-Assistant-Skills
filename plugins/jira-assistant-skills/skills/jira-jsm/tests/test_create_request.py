"""
Tests for create_request.py script.

Tests creating JSM service requests with request types, custom fields,
participants, and on-behalf-of functionality.
"""

import sys
from pathlib import Path

import pytest

# Add scripts to path
scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import create_request


@pytest.mark.jsm
@pytest.mark.unit
class TestCreateRequestBasic:
    """Test basic request creation functionality."""

    def test_create_request_basic(self, mock_jira_client, sample_request_response):
        """Test creating request with summary and description."""
        mock_jira_client.create_request.return_value = sample_request_response

        result = create_request.create_service_request(
            service_desk_id="1",
            request_type_id="10",
            summary="Email not working",
            description="Cannot send emails",
        )

        assert result["issueKey"] == "SD-101"
        assert result["requestTypeId"] == "10"
        mock_jira_client.create_request.assert_called_once()

    def test_create_request_with_request_type(
        self, mock_jira_client, sample_request_response
    ):
        """Test creating request with specific request type."""
        mock_jira_client.create_request.return_value = sample_request_response

        create_request.create_service_request(
            service_desk_id="1",
            request_type_id="10",
            summary="Test request",
            description="Test",
        )

        call_args = mock_jira_client.create_request.call_args
        assert call_args[1]["request_type_id"] == "10"

    def test_create_request_with_custom_fields(
        self, mock_jira_client, sample_request_response
    ):
        """Test creating request with JSM custom fields."""
        mock_jira_client.create_request.return_value = sample_request_response

        custom_fields = {"priority": "High", "impact": "Multiple Users"}

        create_request.create_service_request(
            service_desk_id="1",
            request_type_id="10",
            summary="Server down",
            description="Production server not responding",
            custom_fields=custom_fields,
        )

        call_args = mock_jira_client.create_request.call_args
        fields = call_args[1]["fields"]
        assert fields["priority"] == "High"
        assert fields["impact"] == "Multiple Users"

    def test_create_request_with_participants(
        self, mock_jira_client, sample_request_response
    ):
        """Test adding participants when creating request."""
        mock_jira_client.create_request.return_value = sample_request_response

        participants = ["alice@example.com", "bob@example.com"]

        create_request.create_service_request(
            service_desk_id="1",
            request_type_id="10",
            summary="Team access request",
            description="Need access for team",
            participants=participants,
        )

        call_args = mock_jira_client.create_request.call_args
        assert call_args[1]["participants"] == participants

    def test_create_request_on_behalf_of(
        self, mock_jira_client, sample_request_response
    ):
        """Test creating request on behalf of another user."""
        mock_jira_client.create_request.return_value = sample_request_response

        create_request.create_service_request(
            service_desk_id="1",
            request_type_id="10",
            summary="Password reset",
            description="User needs password reset",
            on_behalf_of="customer@example.com",
        )

        call_args = mock_jira_client.create_request.call_args
        assert call_args[1]["on_behalf_of"] == "customer@example.com"

    def test_create_request_validate_required_fields(self, mock_jira_client):
        """Test validation of required fields for request type."""
        with pytest.raises(ValueError, match="summary is required"):
            create_request.create_service_request(
                service_desk_id="1",
                request_type_id="10",
                summary="",
                description="Test",
            )

    def test_create_request_with_priority(
        self, mock_jira_client, sample_request_response
    ):
        """Test setting priority during creation."""
        mock_jira_client.create_request.return_value = sample_request_response

        create_request.create_service_request(
            service_desk_id="1",
            request_type_id="10",
            summary="Urgent issue",
            description="Production down",
            custom_fields={"priority": "High"},
        )

        call_args = mock_jira_client.create_request.call_args
        assert call_args[1]["fields"]["priority"] == "High"

    def test_create_request_invalid_request_type(self, mock_jira_client):
        """Test error when request type doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.create_request.side_effect = NotFoundError(
            "Request type not found"
        )

        with pytest.raises(NotFoundError, match="Request type not found"):
            create_request.create_service_request(
                service_desk_id="1",
                request_type_id="999",
                summary="Test",
                description="Test",
            )


@pytest.mark.jsm
@pytest.mark.unit
class TestCreateRequestApiErrors:
    """Test API error handling scenarios for create_request."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_jira_client.create_request.side_effect = AuthenticationError(
            "Invalid token"
        )

        with pytest.raises(AuthenticationError):
            create_request.create_service_request(
                service_desk_id="1",
                request_type_id="10",
                summary="Test",
                description="Test",
            )

    def test_permission_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.create_request.side_effect = PermissionError("Access denied")

        with pytest.raises(PermissionError):
            create_request.create_service_request(
                service_desk_id="1",
                request_type_id="10",
                summary="Test",
                description="Test",
            )

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.create_request.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        with pytest.raises(JiraError) as exc_info:
            create_request.create_service_request(
                service_desk_id="1",
                request_type_id="10",
                summary="Test",
                description="Test",
            )
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.create_request.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        with pytest.raises(JiraError) as exc_info:
            create_request.create_service_request(
                service_desk_id="1",
                request_type_id="10",
                summary="Test",
                description="Test",
            )
        assert exc_info.value.status_code == 500
