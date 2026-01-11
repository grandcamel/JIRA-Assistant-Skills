"""Tests for JSM CLI commands."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from jira_assistant_skills.cli.commands.jsm_cmds import (
    # Approval impl
    _format_approvals,
    _format_asset,
    # Asset impl
    _format_assets,
    # Customer impl
    _format_customers,
    _format_datetime,
    _format_kb_article,
    # KB impl
    _format_kb_search_results,
    _format_organization,
    # Organization impl
    _format_organizations,
    # Participant impl
    _format_participants,
    _format_pending_approvals,
    _format_queue,
    # Queue impl
    _format_queues,
    _format_request,
    _format_request_type_fields,
    _format_request_types,
    # Request impl
    _format_requests,
    _format_service_desk,
    _format_service_desks,
    # SLA impl
    _format_sla,
    _format_sla_breach_check,
    _format_sla_report_csv,
    _format_sla_report_text,
    _format_sla_time,
    _format_transitions,
    _is_sla_breached,
    # Request Type impl
    _parse_attributes,
    # Helper functions
    _parse_comma_list,
    # CLI commands
    jsm,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_client():
    """Mock JIRA client."""
    client = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=None)
    return client


@pytest.fixture
def sample_service_desks():
    """Sample service desks data."""
    return {
        "values": [
            {
                "id": "1",
                "projectId": "10001",
                "projectKey": "SD",
                "projectName": "Service Desk",
            },
            {
                "id": "2",
                "projectId": "10002",
                "projectKey": "IT",
                "projectName": "IT Support",
            },
        ],
        "size": 2,
    }


@pytest.fixture
def sample_request_types():
    """Sample request types data."""
    return {
        "values": [
            {
                "id": "1",
                "name": "Hardware Request",
                "description": "Request new hardware",
                "serviceDeskId": "1",
                "issueTypeId": "10001",
            },
            {
                "id": "2",
                "name": "Software Request",
                "description": "Request software installation",
                "serviceDeskId": "1",
                "issueTypeId": "10002",
            },
        ],
        "size": 2,
    }


@pytest.fixture
def sample_request():
    """Sample request data."""
    return {
        "issueKey": "SD-123",
        "serviceDeskId": "1",
        "requestType": {"name": "Hardware Request"},
        "currentStatus": {"status": "Open", "statusCategory": "To Do"},
        "requestFieldValues": [
            {"fieldId": "summary", "value": "Need new laptop"},
            {"fieldId": "description", "value": "My laptop is broken"},
        ],
        "reporter": {"emailAddress": "user@example.com"},
        "createdDate": {"friendly": "2024-01-15"},
        "_links": {
            "web": "https://example.atlassian.net/servicedesk/customer/portal/1/SD-123",
            "agent": "https://example.atlassian.net/browse/SD-123",
        },
    }


@pytest.fixture
def sample_customers():
    """Sample customers data."""
    return {
        "values": [
            {
                "accountId": "abc123",
                "displayName": "John Doe",
                "emailAddress": "john@example.com",
                "active": True,
            },
            {
                "accountId": "def456",
                "displayName": "Jane Smith",
                "emailAddress": "jane@example.com",
                "active": True,
            },
        ],
        "size": 2,
    }


@pytest.fixture
def sample_organizations():
    """Sample organizations data."""
    return {
        "values": [
            {"id": "1", "name": "Acme Corp"},
            {"id": "2", "name": "Beta Industries"},
        ],
        "size": 2,
    }


@pytest.fixture
def sample_queues():
    """Sample queues data."""
    return {
        "values": [
            {"id": "1", "name": "Unassigned", "jql": "assignee is EMPTY"},
            {"id": "2", "name": "My Queue", "jql": "assignee = currentUser()"},
        ],
        "size": 2,
    }


@pytest.fixture
def sample_sla_data():
    """Sample SLA data."""
    return {
        "values": [
            {
                "name": "Time to first response",
                "ongoingCycle": {
                    "breached": False,
                    "remainingTime": {"millis": 7200000},  # 2 hours
                },
            },
            {
                "name": "Time to resolution",
                "ongoingCycle": {
                    "breached": True,
                    "remainingTime": {"millis": -3600000},  # -1 hour (overdue)
                },
            },
        ],
    }


@pytest.fixture
def sample_approvals():
    """Sample approvals data."""
    return [
        {
            "id": "10001",
            "name": "Manager Approval",
            "status": "pending",
            "approvers": [{"displayName": "Manager User"}],
            "createdDate": "2024-01-15T10:00:00Z",
        },
    ]


@pytest.fixture
def sample_kb_articles():
    """Sample KB articles."""
    return [
        {
            "title": "How to reset password",
            "excerpt": "This article explains how to <em>reset</em> your password.",
            "_links": {"self": "https://example.com/kb/1"},
        },
        {
            "title": "VPN Setup Guide",
            "excerpt": "Instructions for setting up <em>VPN</em> connection.",
            "_links": {"self": "https://example.com/kb/2"},
        },
    ]


@pytest.fixture
def sample_assets():
    """Sample assets data."""
    return [
        {
            "objectKey": "SRV-001",
            "label": "Web Server 1",
            "objectType": {"name": "Server"},
            "attributes": [
                {
                    "objectTypeAttribute": {"name": "IP Address"},
                    "objectAttributeValues": [{"value": "192.168.1.100"}],
                },
            ],
        },
        {
            "objectKey": "SRV-002",
            "label": "Database Server",
            "objectType": {"name": "Server"},
            "attributes": [
                {
                    "objectTypeAttribute": {"name": "IP Address"},
                    "objectAttributeValues": [{"value": "192.168.1.101"}],
                },
            ],
        },
    ]


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestParseCommaList:
    """Tests for _parse_comma_list."""

    def test_parse_simple_list(self):
        """Test parsing simple comma-separated list."""
        result = _parse_comma_list("a,b,c")
        assert result == ["a", "b", "c"]

    def test_parse_with_spaces(self):
        """Test parsing list with spaces."""
        result = _parse_comma_list("a, b , c")
        assert result == ["a", "b", "c"]

    def test_parse_single_value(self):
        """Test parsing single value."""
        result = _parse_comma_list("single")
        assert result == ["single"]

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        result = _parse_comma_list("")
        assert result == []

    def test_parse_with_empty_values(self):
        """Test parsing list with empty values."""
        result = _parse_comma_list("a,,b, ,c")
        assert result == ["a", "b", "c"]


class TestParseAttributes:
    """Tests for _parse_attributes."""

    def test_parse_single_attribute(self):
        """Test parsing single attribute."""
        result = _parse_attributes(["name=value"])
        assert result == {"name": "value"}

    def test_parse_multiple_attributes(self):
        """Test parsing multiple attributes."""
        result = _parse_attributes(["name=John", "age=30"])
        assert result == {"name": "John", "age": "30"}

    def test_parse_attribute_with_spaces(self):
        """Test parsing attribute with spaces in value."""
        result = _parse_attributes(["name = John Doe"])
        assert result == {"name": "John Doe"}

    def test_parse_attribute_with_equals_in_value(self):
        """Test parsing attribute with equals sign in value."""
        result = _parse_attributes(["formula=a=b+c"])
        assert result == {"formula": "a=b+c"}

    def test_parse_invalid_format_raises(self):
        """Test invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid attribute format"):
            _parse_attributes(["invalid_no_equals"])


class TestFormatDatetime:
    """Tests for _format_datetime."""

    def test_format_iso_datetime(self):
        """Test formatting ISO datetime."""
        result = _format_datetime("2024-01-15T10:30:00Z")
        assert result == "2024-01-15 10:30"

    def test_format_empty_string(self):
        """Test formatting empty string."""
        result = _format_datetime("")
        assert result == "Unknown"

    def test_format_invalid_string(self):
        """Test formatting invalid string (truncates)."""
        result = _format_datetime("some invalid date string")
        assert result == "some invalid dat"


class TestFormatSlaTime:
    """Tests for _format_sla_time."""

    def test_format_hours_and_minutes(self):
        """Test formatting hours and minutes."""
        result = _format_sla_time(7200000)  # 2 hours
        assert result == "2h 0m"

    def test_format_minutes_only(self):
        """Test formatting minutes only."""
        result = _format_sla_time(1800000)  # 30 minutes
        assert result == "30m"

    def test_format_negative_overdue(self):
        """Test formatting negative (overdue)."""
        result = _format_sla_time(-3600000)
        assert result == "Overdue"


class TestIsSlaBreached:
    """Tests for _is_sla_breached."""

    def test_ongoing_breached(self):
        """Test ongoing cycle breached."""
        sla = {"ongoingCycle": {"breached": True}}
        assert _is_sla_breached(sla) is True

    def test_ongoing_not_breached(self):
        """Test ongoing cycle not breached."""
        sla = {"ongoingCycle": {"breached": False}}
        assert _is_sla_breached(sla) is False

    def test_completed_breached(self):
        """Test completed cycle breached."""
        sla = {"completedCycles": [{"breached": True}]}
        assert _is_sla_breached(sla) is True

    def test_no_breach(self):
        """Test no breach."""
        sla = {"ongoingCycle": {"breached": False}, "completedCycles": []}
        assert _is_sla_breached(sla) is False


# =============================================================================
# Service Desk Formatting Tests
# =============================================================================


class TestFormatServiceDesks:
    """Tests for _format_service_desks."""

    def test_format_service_desks(self, sample_service_desks):
        """Test formatting service desks."""
        result = _format_service_desks(sample_service_desks)
        assert "Available Service Desks:" in result
        assert "SD" in result
        assert "IT Support" in result
        assert "Total: 2 service desks" in result

    def test_format_empty_service_desks(self):
        """Test formatting empty service desks."""
        result = _format_service_desks({"values": []})
        assert "No service desks found" in result


class TestFormatServiceDesk:
    """Tests for _format_service_desk."""

    def test_format_single_service_desk(self):
        """Test formatting single service desk."""
        sd = {
            "id": "1",
            "projectId": "10001",
            "projectKey": "SD",
            "projectName": "Service Desk",
        }
        result = _format_service_desk(sd)
        assert "Service Desk Details:" in result
        assert "ID:           1" in result
        assert "Project Key:  SD" in result


# =============================================================================
# Request Type Formatting Tests
# =============================================================================


class TestFormatRequestTypes:
    """Tests for _format_request_types."""

    def test_format_request_types(self, sample_request_types):
        """Test formatting request types."""
        result = _format_request_types(sample_request_types)
        assert "Request Types:" in result
        assert "Hardware Request" in result
        assert "Software Request" in result
        assert "Total: 2 request types" in result

    def test_format_request_types_with_issue_types(self, sample_request_types):
        """Test formatting request types with issue types."""
        result = _format_request_types(sample_request_types, show_issue_types=True)
        assert "Issue Type" in result

    def test_format_empty_request_types(self):
        """Test formatting empty request types."""
        result = _format_request_types({"values": []})
        assert "No request types found" in result


class TestFormatRequestTypeFields:
    """Tests for _format_request_type_fields."""

    def test_format_fields(self):
        """Test formatting request type fields."""
        fields = [
            {"fieldId": "summary", "name": "Summary", "required": True},
            {"fieldId": "description", "name": "Description", "required": False},
        ]
        result = _format_request_type_fields(fields)
        assert "Request Type Fields:" in result
        assert "summary" in result
        assert "Yes" in result

    def test_format_empty_fields(self):
        """Test formatting empty fields."""
        result = _format_request_type_fields([])
        assert "No fields defined" in result


# =============================================================================
# Request Formatting Tests
# =============================================================================


class TestFormatRequests:
    """Tests for _format_requests."""

    def test_format_requests(self):
        """Test formatting request list."""
        issues = [
            {
                "key": "SD-123",
                "fields": {
                    "summary": "Test issue",
                    "status": {"name": "Open"},
                    "reporter": {"emailAddress": "user@example.com"},
                },
            }
        ]
        result = _format_requests(issues)
        assert "SD-123" in result
        assert "Test issue" in result
        assert "Open" in result

    def test_format_empty_requests(self):
        """Test formatting empty requests."""
        result = _format_requests([])
        assert "No requests found" in result


class TestFormatRequest:
    """Tests for _format_request."""

    def test_format_request(self, sample_request):
        """Test formatting single request."""
        result = _format_request(sample_request)
        assert "Request: SD-123" in result
        assert "Need new laptop" in result
        assert "Hardware Request" in result
        assert "Open" in result

    def test_format_request_with_sla(self, sample_request, sample_sla_data):
        """Test formatting request with SLA data."""
        request = {**sample_request, "sla": sample_sla_data}
        result = _format_request(request)
        assert "SLA Information:" in result


class TestFormatTransitions:
    """Tests for _format_transitions."""

    def test_format_transitions(self):
        """Test formatting transitions."""
        transitions = [
            {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
            {"id": "21", "name": "Resolve", "to": {"name": "Resolved"}},
        ]
        result = _format_transitions(transitions)
        assert "Start Progress" in result
        assert "In Progress" in result


# =============================================================================
# Customer and Organization Formatting Tests
# =============================================================================


class TestFormatCustomers:
    """Tests for _format_customers."""

    def test_format_customers(self, sample_customers):
        """Test formatting customers."""
        result = _format_customers(sample_customers)
        assert "Customers:" in result
        assert "john@example.com" in result
        assert "John Doe" in result
        assert "Total: 2 customers" in result

    def test_format_empty_customers(self):
        """Test formatting empty customers."""
        result = _format_customers({"values": []})
        assert "No customers found" in result


class TestFormatOrganizations:
    """Tests for _format_organizations."""

    def test_format_organizations(self, sample_organizations):
        """Test formatting organizations."""
        result = _format_organizations(sample_organizations)
        assert "Organizations:" in result
        assert "Acme Corp" in result
        assert "Beta Industries" in result
        assert "Total: 2 organization(s)" in result

    def test_format_empty_organizations(self):
        """Test formatting empty organizations."""
        result = _format_organizations({"values": []})
        assert "No organizations found" in result


class TestFormatOrganization:
    """Tests for _format_organization."""

    def test_format_organization(self):
        """Test formatting single organization."""
        org = {"id": "1", "name": "Acme Corp"}
        result = _format_organization(org)
        assert "Organization Details:" in result
        assert "ID:   1" in result
        assert "Name: Acme Corp" in result


# =============================================================================
# Queue Formatting Tests
# =============================================================================


class TestFormatQueues:
    """Tests for _format_queues."""

    def test_format_queues(self, sample_queues):
        """Test formatting queues."""
        result = _format_queues(sample_queues)
        assert "Queues: 2 total" in result
        assert "Unassigned" in result
        assert "My Queue" in result

    def test_format_queues_with_jql(self, sample_queues):
        """Test formatting queues with JQL."""
        result = _format_queues(sample_queues, show_jql=True)
        assert "JQL:" in result
        assert "assignee is EMPTY" in result


class TestFormatQueue:
    """Tests for _format_queue."""

    def test_format_queue(self):
        """Test formatting single queue."""
        queue = {"id": "1", "name": "Unassigned", "jql": "assignee is EMPTY"}
        result = _format_queue(queue)
        assert "Queue: Unassigned" in result
        assert "ID: 1" in result


# =============================================================================
# SLA Formatting Tests
# =============================================================================


class TestFormatSla:
    """Tests for _format_sla."""

    def test_format_sla(self, sample_sla_data):
        """Test formatting SLA data."""
        result = _format_sla(sample_sla_data)
        assert "SLA Information:" in result
        assert "Time to first response" in result
        assert "2h 0m remaining" in result
        assert "BREACHED" in result

    def test_format_empty_sla(self):
        """Test formatting empty SLA data."""
        result = _format_sla({"values": []})
        assert "No SLA information available" in result


class TestFormatSlaBreachCheck:
    """Tests for _format_sla_breach_check."""

    def test_format_breach_check(self):
        """Test formatting SLA breach check."""
        result_data = {
            "issue_key": "SD-123",
            "breached": ["Time to resolution"],
            "at_risk": ["Time to response"],
            "ok": ["Time to acknowledge"],
        }
        result = _format_sla_breach_check(result_data)
        assert "SLA Breach Check for SD-123" in result
        assert "BREACHED SLAs:" in result
        assert "AT RISK" in result
        assert "OK:" in result


class TestFormatSlaReport:
    """Tests for SLA report formatting."""

    def test_format_sla_report_text(self):
        """Test formatting SLA report as text."""
        report = {
            "total_issues": 10,
            "total_slas": 20,
            "report_data": [
                {
                    "issue_key": "SD-123",
                    "summary": "Test issue",
                    "sla": {
                        "name": "Time to response",
                        "ongoingCycle": {"breached": False},
                    },
                }
            ],
        }
        result = _format_sla_report_text(report)
        assert "SLA Compliance Report" in result
        assert "Total Issues: 10" in result
        assert "SD-123" in result

    def test_format_sla_report_csv(self):
        """Test formatting SLA report as CSV."""
        report = {
            "total_issues": 1,
            "total_slas": 1,
            "report_data": [
                {
                    "issue_key": "SD-123",
                    "summary": "Test issue",
                    "sla": {
                        "name": "Time to response",
                        "ongoingCycle": {"breached": True},
                    },
                }
            ],
        }
        result = _format_sla_report_csv(report)
        assert "Request Key,Summary,SLA Name,Breached" in result
        assert "SD-123" in result
        assert "Yes" in result


# =============================================================================
# Approval Formatting Tests
# =============================================================================


class TestFormatApprovals:
    """Tests for _format_approvals."""

    def test_format_approvals(self, sample_approvals):
        """Test formatting approvals."""
        result = _format_approvals(sample_approvals, "SD-123")
        assert "Approvals for SD-123" in result
        assert "Manager Approval" in result
        assert "pending" in result

    def test_format_empty_approvals(self):
        """Test formatting empty approvals."""
        result = _format_approvals([], "SD-123")
        assert "No approvals found" in result


class TestFormatPendingApprovals:
    """Tests for _format_pending_approvals."""

    def test_format_pending_approvals(self):
        """Test formatting pending approvals."""
        approvals = [
            {
                "issueKey": "SD-123",
                "id": "10001",
                "name": "Manager Approval",
                "createdDate": "2024-01-15T10:00:00Z",
            }
        ]
        result = _format_pending_approvals(approvals)
        assert "Pending Approvals:" in result
        assert "SD-123" in result
        assert "Manager Approval" in result

    def test_format_empty_pending(self):
        """Test formatting empty pending approvals."""
        result = _format_pending_approvals([])
        assert "No pending approvals found" in result


# =============================================================================
# KB Formatting Tests
# =============================================================================


class TestFormatKbSearchResults:
    """Tests for _format_kb_search_results."""

    def test_format_kb_results(self, sample_kb_articles):
        """Test formatting KB search results."""
        result = _format_kb_search_results(sample_kb_articles)
        assert "Knowledge Base Search Results" in result
        assert "How to reset password" in result
        assert "VPN Setup Guide" in result
        # HTML tags should be stripped
        assert "<em>" not in result

    def test_format_empty_kb_results(self):
        """Test formatting empty KB results."""
        result = _format_kb_search_results([])
        assert "No KB articles found" in result


class TestFormatKbArticle:
    """Tests for _format_kb_article."""

    def test_format_kb_article(self):
        """Test formatting KB article."""
        article = {
            "title": "Password Reset Guide",
            "body": {"content": "Here's how to reset your password..."},
        }
        result = _format_kb_article(article)
        assert "KB Article: Password Reset Guide" in result
        assert "Here's how to reset" in result


# =============================================================================
# Asset Formatting Tests
# =============================================================================


class TestFormatAssets:
    """Tests for _format_assets."""

    def test_format_assets(self, sample_assets):
        """Test formatting assets."""
        result = _format_assets(sample_assets)
        assert "Assets (2 total):" in result
        assert "SRV-001" in result
        assert "Web Server 1" in result
        assert "192.168.1.100" in result

    def test_format_empty_assets(self):
        """Test formatting empty assets."""
        result = _format_assets([])
        assert "No assets found" in result


class TestFormatAsset:
    """Tests for _format_asset."""

    def test_format_asset(self, sample_assets):
        """Test formatting single asset."""
        result = _format_asset(sample_assets[0])
        assert "Asset: SRV-001" in result
        assert "Object Type: Server" in result
        assert "IP Address: 192.168.1.100" in result


# =============================================================================
# Participant Formatting Tests
# =============================================================================


class TestFormatParticipants:
    """Tests for _format_participants."""

    def test_format_participants(self):
        """Test formatting participants."""
        participants = [
            {
                "accountId": "abc123",
                "displayName": "John Doe",
                "emailAddress": "john@example.com",
            }
        ]
        result = _format_participants(participants)
        assert "Participants:" in result
        assert "John Doe" in result
        assert "john@example.com" in result

    def test_format_empty_participants(self):
        """Test formatting empty participants."""
        result = _format_participants([])
        assert "No participants found" in result


# =============================================================================
# CLI Command Tests
# =============================================================================


class TestServiceDeskListCommand:
    """Tests for service-desk list command."""

    @patch("jira_assistant_skills.cli.commands.jsm_cmds.get_jira_client")
    def test_list_service_desks(
        self, mock_get_client, runner, mock_client, sample_service_desks
    ):
        """Test listing service desks."""
        mock_get_client.return_value = mock_client
        mock_client.get_service_desks.return_value = sample_service_desks

        result = runner.invoke(jsm, ["service-desk", "list"])
        assert result.exit_code == 0
        assert "SD" in result.output

    @patch("jira_assistant_skills.cli.commands.jsm_cmds.get_jira_client")
    def test_list_service_desks_json(
        self, mock_get_client, runner, mock_client, sample_service_desks
    ):
        """Test listing service desks in JSON format."""
        mock_get_client.return_value = mock_client
        mock_client.get_service_desks.return_value = sample_service_desks

        result = runner.invoke(jsm, ["service-desk", "list", "--output", "json"])
        assert result.exit_code == 0
        assert '"projectKey"' in result.output


class TestServiceDeskGetCommand:
    """Tests for service-desk get command."""

    @patch("jira_assistant_skills.cli.commands.jsm_cmds.get_jira_client")
    def test_get_service_desk(self, mock_get_client, runner, mock_client):
        """Test getting service desk details."""
        mock_get_client.return_value = mock_client
        mock_client.get_service_desk.return_value = {
            "id": "1",
            "projectId": "10001",
            "projectKey": "SD",
            "projectName": "Service Desk",
        }

        result = runner.invoke(jsm, ["service-desk", "get", "1"])
        assert result.exit_code == 0
        assert "Service Desk Details:" in result.output


class TestServiceDeskCreateCommand:
    """Tests for service-desk create command."""

    @patch("jira_assistant_skills.cli.commands.jsm_cmds.get_jira_client")
    def test_create_service_desk_dry_run(self, mock_get_client, runner):
        """Test creating service desk with dry run."""
        result = runner.invoke(
            jsm, ["service-desk", "create", "PROJ", "Test Desk", "--dry-run"]
        )
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.output
        assert "PROJ" in result.output


class TestRequestTypeListCommand:
    """Tests for request-type list command."""

    @patch("jira_assistant_skills.cli.commands.jsm_cmds.get_jira_client")
    def test_list_request_types(
        self, mock_get_client, runner, mock_client, sample_request_types
    ):
        """Test listing request types."""
        mock_get_client.return_value = mock_client
        mock_client.get_request_types.return_value = sample_request_types

        result = runner.invoke(jsm, ["request-type", "list", "1"])
        assert result.exit_code == 0
        assert "Hardware Request" in result.output


class TestRequestListCommand:
    """Tests for request list command."""

    @patch("jira_assistant_skills.cli.commands.jsm_cmds.get_jira_client")
    def test_list_requests(self, mock_get_client, runner, mock_client):
        """Test listing requests."""
        mock_get_client.return_value.__enter__.return_value = mock_client
        mock_get_client.return_value.__exit__.return_value = None
        mock_client.search_issues.return_value = {
            "issues": [
                {
                    "key": "SD-123",
                    "fields": {
                        "summary": "Test",
                        "status": {"name": "Open"},
                        "reporter": {"emailAddress": "test@example.com"},
                    },
                }
            ],
            "total": 1,
        }

        result = runner.invoke(jsm, ["request", "list", "SD"])
        assert result.exit_code == 0
        assert "SD-123" in result.output


class TestRequestCreateCommand:
    """Tests for request create command."""

    def test_create_request_dry_run(self, runner):
        """Test creating request with dry run."""
        result = runner.invoke(
            jsm,
            ["request", "create", "1", "10", "--summary", "Test request", "--dry-run"],
        )
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.output
        assert "Test request" in result.output


class TestRequestTransitionCommand:
    """Tests for request transition command."""

    @patch("jira_assistant_skills.cli.commands.jsm_cmds.get_jira_client")
    def test_show_transitions(self, mock_get_client, runner, mock_client):
        """Test showing available transitions."""
        mock_get_client.return_value.__enter__.return_value = mock_client
        mock_get_client.return_value.__exit__.return_value = None
        mock_client.get_request_transitions.return_value = [
            {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}}
        ]

        result = runner.invoke(
            jsm, ["request", "transition", "SD-123", "--show-transitions"]
        )
        assert result.exit_code == 0
        assert "Start Progress" in result.output

    def test_transition_dry_run(self, runner):
        """Test transition with dry run."""
        result = runner.invoke(
            jsm,
            ["request", "transition", "SD-123", "--to", "In Progress", "--dry-run"],
        )
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.output


class TestCustomerListCommand:
    """Tests for customer list command."""

    @patch("jira_assistant_skills.cli.commands.jsm_cmds.get_jira_client")
    def test_list_customers(
        self, mock_get_client, runner, mock_client, sample_customers
    ):
        """Test listing customers."""
        mock_get_client.return_value.__enter__.return_value = mock_client
        mock_get_client.return_value.__exit__.return_value = None
        mock_client.get_service_desk_customers.return_value = sample_customers

        result = runner.invoke(jsm, ["customer", "list", "1"])
        assert result.exit_code == 0
        assert "john@example.com" in result.output


class TestOrganizationListCommand:
    """Tests for organization list command."""

    @patch("jira_assistant_skills.cli.commands.jsm_cmds.get_jira_client")
    def test_list_organizations(
        self, mock_get_client, runner, mock_client, sample_organizations
    ):
        """Test listing organizations."""
        mock_get_client.return_value.__enter__.return_value = mock_client
        mock_get_client.return_value.__exit__.return_value = None
        mock_client.get_organizations.return_value = sample_organizations

        result = runner.invoke(jsm, ["organization", "list"])
        assert result.exit_code == 0
        assert "Acme Corp" in result.output


class TestOrganizationCreateCommand:
    """Tests for organization create command."""

    def test_create_organization_dry_run(self, runner):
        """Test creating organization with dry run."""
        result = runner.invoke(
            jsm, ["organization", "create", "--name", "Test Org", "--dry-run"]
        )
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.output
        assert "Test Org" in result.output


class TestQueueListCommand:
    """Tests for queue list command."""

    @patch("jira_assistant_skills.cli.commands.jsm_cmds.get_jira_client")
    def test_list_queues(self, mock_get_client, runner, mock_client, sample_queues):
        """Test listing queues."""
        mock_get_client.return_value.__enter__.return_value = mock_client
        mock_get_client.return_value.__exit__.return_value = None
        mock_client.get_service_desk_queues.return_value = sample_queues

        result = runner.invoke(jsm, ["queue", "list", "1"])
        assert result.exit_code == 0
        assert "Unassigned" in result.output


class TestSlaGetCommand:
    """Tests for sla get command."""

    @patch("jira_assistant_skills.cli.commands.jsm_cmds.get_jira_client")
    def test_get_sla(self, mock_get_client, runner, mock_client, sample_sla_data):
        """Test getting SLA information."""
        mock_get_client.return_value.__enter__.return_value = mock_client
        mock_get_client.return_value.__exit__.return_value = None
        mock_client.get_request_slas.return_value = sample_sla_data

        result = runner.invoke(jsm, ["sla", "get", "SD-123"])
        assert result.exit_code == 0
        assert "SLA Information:" in result.output


class TestSlaReportCommand:
    """Tests for sla report command."""

    def test_sla_report_missing_args(self, runner):
        """Test SLA report with missing arguments."""
        result = runner.invoke(jsm, ["sla", "report"])
        assert result.exit_code == 1
        assert "Must specify" in result.output


class TestApprovalListCommand:
    """Tests for approval list command."""

    @patch("jira_assistant_skills.cli.commands.jsm_cmds.get_jira_client")
    def test_list_approvals(
        self, mock_get_client, runner, mock_client, sample_approvals
    ):
        """Test listing approvals."""
        mock_get_client.return_value.__enter__.return_value = mock_client
        mock_get_client.return_value.__exit__.return_value = None
        mock_client.get_request_approvals.return_value = sample_approvals

        result = runner.invoke(jsm, ["approval", "list", "SD-123"])
        assert result.exit_code == 0
        assert "Manager Approval" in result.output


class TestKbSearchCommand:
    """Tests for kb search command."""

    @patch("jira_assistant_skills.cli.commands.jsm_cmds.get_jira_client")
    def test_search_kb(self, mock_get_client, runner, mock_client, sample_kb_articles):
        """Test searching KB articles."""
        mock_get_client.return_value.__enter__.return_value = mock_client
        mock_get_client.return_value.__exit__.return_value = None
        mock_client.search_kb_articles.return_value = sample_kb_articles

        result = runner.invoke(
            jsm, ["kb", "search", "--service-desk", "1", "--query", "password"]
        )
        assert result.exit_code == 0
        assert "How to reset password" in result.output


class TestAssetListCommand:
    """Tests for asset list command."""

    @patch("jira_assistant_skills.cli.commands.jsm_cmds.get_jira_client")
    def test_list_assets(self, mock_get_client, runner, mock_client, sample_assets):
        """Test listing assets."""
        mock_get_client.return_value.__enter__.return_value = mock_client
        mock_get_client.return_value.__exit__.return_value = None
        mock_client.has_assets_license.return_value = True
        mock_client.list_assets.return_value = sample_assets

        result = runner.invoke(jsm, ["asset", "list"])
        assert result.exit_code == 0
        assert "SRV-001" in result.output


class TestAssetCreateCommand:
    """Tests for asset create command."""

    def test_create_asset_dry_run(self, runner):
        """Test creating asset with dry run."""
        result = runner.invoke(
            jsm,
            [
                "asset",
                "create",
                "--type-id",
                "5",
                "--attr",
                "Name=Server1",
                "--attr",
                "IP=192.168.1.1",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "Server1" in result.output

    def test_create_asset_invalid_type_id(self, runner):
        """Test creating asset with invalid type ID."""
        result = runner.invoke(
            jsm,
            ["asset", "create", "--type-id", "0", "--attr", "Name=Test"],
        )
        assert result.exit_code == 1
        assert "must be a positive integer" in result.output
