"""
Comprehensive tests for JSM Phase 4: SLA & Queue Management.

Covers all 6 scripts:
- get_sla.py (8 tests)
- check_sla_breach.py (7 tests)
- sla_report.py (8 tests)
- list_queues.py (6 tests)
- get_queue.py (6 tests)
- get_queue_issues.py (5 tests)

Total: 40 tests
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import check_sla_breach
import get_queue
import get_queue_issues
import get_sla
import list_queues
import sla_report

# ========== Test Fixtures ==========


@pytest.fixture
def mock_ongoing_sla():
    """SLA with ongoing cycle."""
    return {
        "id": "1",
        "name": "Time to First Response",
        "ongoingCycle": {
            "startTime": {"friendly": "15/Jan/25 10:00 AM"},
            "breachTime": {"friendly": "15/Jan/25 2:00 PM"},
            "breached": False,
            "paused": False,
            "goalDuration": {"millis": 14400000, "friendly": "4h"},
            "elapsedTime": {"millis": 7200000, "friendly": "2h"},
            "remainingTime": {"millis": 7200000, "friendly": "2h"},
        },
        "completedCycles": [],
    }


@pytest.fixture
def mock_breached_sla():
    """SLA that has breached."""
    return {
        "id": "2",
        "name": "Time to Resolution",
        "ongoingCycle": {
            "startTime": {"friendly": "15/Jan/25 10:00 AM"},
            "breachTime": {"friendly": "17/Jan/25 10:00 AM"},
            "breached": True,
            "paused": False,
            "goalDuration": {"millis": 172800000, "friendly": "2d"},
            "elapsedTime": {"millis": 180000000, "friendly": "2d 2h"},
            "remainingTime": {"millis": -7200000, "friendly": "-2h"},
        },
        "completedCycles": [],
    }


@pytest.fixture
def mock_met_sla():
    """SLA that was met."""
    return {
        "id": "1",
        "name": "Time to First Response",
        "ongoingCycle": None,
        "completedCycles": [
            {
                "startTime": {"friendly": "15/Jan/25 10:00 AM"},
                "stopTime": {"friendly": "15/Jan/25 11:30 AM"},
                "breached": False,
                "goalDuration": {"millis": 14400000, "friendly": "4h"},
                "elapsedTime": {"millis": 5400000, "friendly": "1h 30m"},
                "remainingTime": {"millis": 9000000, "friendly": "2h 30m"},
            }
        ],
    }


@pytest.fixture
def mock_queues():
    """Mock queue list."""
    return {
        "size": 3,
        "start": 0,
        "limit": 50,
        "isLastPage": True,
        "values": [
            {
                "id": "1",
                "name": "Open Requests",
                "jql": "project = SD AND status = Open",
            },
            {
                "id": "2",
                "name": "Waiting for Customer",
                "jql": "project = SD AND status = 'Waiting for customer'",
            },
            {
                "id": "3",
                "name": "Breached SLAs",
                "jql": "project = SD AND 'SLA Status' = Breached",
            },
        ],
    }


@pytest.fixture
def mock_queue_issues():
    """Mock queue issues."""
    return {
        "size": 2,
        "start": 0,
        "limit": 50,
        "isLastPage": True,
        "values": [
            {
                "issueKey": "SD-123",
                "fields": {
                    "summary": "Login not working",
                    "status": {"name": "Open"},
                    "priority": {"name": "High"},
                },
            },
            {
                "issueKey": "SD-124",
                "fields": {
                    "summary": "Email sync issue",
                    "status": {"name": "Open"},
                    "priority": {"name": "Medium"},
                },
            },
        ],
    }


# ========== get_sla.py Tests (8 tests) ==========


def test_get_all_slas(mock_ongoing_sla, mock_met_sla):
    """Test fetching all SLAs for a request."""
    mock_client = Mock()
    mock_client.get_request_slas.return_value = {
        "values": [mock_ongoing_sla, mock_met_sla],
        "size": 2,
    }

    with patch("get_sla.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = get_sla.get_slas("SD-123")

    assert len(result["values"]) == 2
    mock_client.get_request_slas.assert_called_once_with("SD-123")


def test_get_specific_sla(mock_ongoing_sla):
    """Test fetching specific SLA metric by ID."""
    mock_client = Mock()
    mock_client.get_request_sla.return_value = mock_ongoing_sla

    with patch("get_sla.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = get_sla.get_slas("SD-123", sla_id="1")

    assert result["name"] == "Time to First Response"
    mock_client.get_request_sla.assert_called_once_with("SD-123", "1")


def test_get_sla_ongoing_cycle(mock_ongoing_sla):
    """Test SLA with ongoing cycle (not yet completed)."""
    assert mock_ongoing_sla["ongoingCycle"] is not None
    assert not mock_ongoing_sla["ongoingCycle"]["breached"]
    assert mock_ongoing_sla["ongoingCycle"]["remainingTime"]["millis"] > 0


def test_get_sla_completed_cycles(mock_met_sla):
    """Test SLA with completed cycles."""
    assert len(mock_met_sla["completedCycles"]) > 0
    assert not mock_met_sla["completedCycles"][0]["breached"]


def test_get_sla_paused():
    """Test SLA in paused state."""
    paused_sla = {
        "id": "1",
        "name": "Test SLA",
        "ongoingCycle": {"paused": True, "breached": False},
    }
    assert paused_sla["ongoingCycle"]["paused"]


def test_get_sla_breached(mock_breached_sla):
    """Test SLA that has breached."""
    assert mock_breached_sla["ongoingCycle"]["breached"]
    assert mock_breached_sla["ongoingCycle"]["remainingTime"]["millis"] < 0


def test_format_text_output(mock_ongoing_sla):
    """Test human-readable SLA status output."""
    sla_data = {"values": [mock_ongoing_sla]}
    text = get_sla.format_sla_text(sla_data)
    assert "Time to First Response" in text
    assert "2h" in text


def test_format_json_output(mock_ongoing_sla):
    """Test JSON output format."""
    sla_data = {"values": [mock_ongoing_sla]}
    json_str = get_sla.format_sla_json(sla_data)
    parsed = json.loads(json_str)
    assert "values" in parsed


# ========== check_sla_breach.py Tests (7 tests) ==========


def test_check_no_breach(mock_ongoing_sla):
    """Test request with all SLAs within target."""
    mock_client = Mock()
    mock_client.get_request_slas.return_value = {"values": [mock_ongoing_sla]}

    with patch("check_sla_breach.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = check_sla_breach.check_sla_breach("SD-123")

    assert not result["has_breach"]
    assert len(result["breached"]) == 0


def test_check_breached_sla(mock_breached_sla):
    """Test request with breached SLA."""
    mock_client = Mock()
    mock_client.get_request_slas.return_value = {"values": [mock_breached_sla]}

    with patch("check_sla_breach.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = check_sla_breach.check_sla_breach("SD-123")

    assert result["has_breach"]
    assert len(result["breached"]) == 1


def test_check_at_risk():
    """Test SLA approaching breach (< 20% remaining)."""
    at_risk_sla = {
        "id": "1",
        "name": "Test SLA",
        "ongoingCycle": {
            "breached": False,
            "paused": False,
            "goalDuration": {"millis": 14400000},  # 4h
            "remainingTime": {"millis": 1800000},  # 30m = 12.5% < 20%
        },
    }
    mock_client = Mock()
    mock_client.get_request_slas.return_value = {"values": [at_risk_sla]}

    with patch("check_sla_breach.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = check_sla_breach.check_sla_breach("SD-123")

    assert result["has_risk"]
    assert len(result["at_risk"]) == 1


def test_check_paused_sla():
    """Test handling of paused SLAs."""
    paused_sla = {
        "id": "1",
        "name": "Test SLA",
        "ongoingCycle": {"breached": False, "paused": True},
    }
    mock_client = Mock()
    mock_client.get_request_slas.return_value = {"values": [paused_sla]}

    with patch("check_sla_breach.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = check_sla_breach.check_sla_breach("SD-123")

    assert len(result["paused"]) == 1


def test_check_multiple_breaches(mock_breached_sla):
    """Test request with multiple breached SLAs."""
    import copy

    breached_sla2 = copy.deepcopy(mock_breached_sla)
    breached_sla2["id"] = "3"
    breached_sla2["name"] = "Another Breached SLA"

    mock_client = Mock()
    mock_client.get_request_slas.return_value = {
        "values": [mock_breached_sla, breached_sla2]
    }

    with patch("check_sla_breach.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = check_sla_breach.check_sla_breach("SD-123")

    assert len(result["breached"]) == 2


def test_warning_threshold_configurable():
    """Test configurable at-risk threshold."""
    at_risk_sla = {
        "id": "1",
        "name": "Test SLA",
        "ongoingCycle": {
            "breached": False,
            "paused": False,
            "goalDuration": {"millis": 14400000},  # 4h
            "remainingTime": {"millis": 3600000},  # 1h = 25% (>20% but <30%)
        },
    }
    mock_client = Mock()
    mock_client.get_request_slas.return_value = {"values": [at_risk_sla]}

    with patch("check_sla_breach.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client

        # With default 20% threshold - not at risk
        result20 = check_sla_breach.check_sla_breach("SD-123", threshold=20.0)
        assert not result20["has_risk"]

        # With 30% threshold - is at risk
        result30 = check_sla_breach.check_sla_breach("SD-123", threshold=30.0)
        assert result30["has_risk"]


def test_filter_by_sla_name(mock_ongoing_sla, mock_breached_sla):
    """Test checking specific SLA only."""
    mock_client = Mock()
    mock_client.get_request_slas.return_value = {
        "values": [mock_ongoing_sla, mock_breached_sla]
    }

    with patch("check_sla_breach.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = check_sla_breach.check_sla_breach(
            "SD-123", sla_name="Time to First Response"
        )

    assert result["total_slas"] == 1


# ========== sla_report.py Tests (8 tests) ==========


def test_report_by_project(mock_ongoing_sla):
    """Test SLA report for all requests in project."""
    mock_client = Mock()
    mock_client.search_issues.return_value = {
        "issues": [{"key": "SD-123", "fields": {"summary": "Test"}}]
    }
    mock_client.get_request_slas.return_value = {"values": [mock_ongoing_sla]}

    with patch("sla_report.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = sla_report.generate_sla_report(project="SD")

    assert result["total_issues"] == 1
    assert result["total_slas"] == 1


def test_report_by_jql(mock_ongoing_sla):
    """Test SLA report for JQL results."""
    mock_client = Mock()
    mock_client.search_issues.return_value = {
        "issues": [{"key": "SD-123", "fields": {"summary": "Test"}}]
    }
    mock_client.get_request_slas.return_value = {"values": [mock_ongoing_sla]}

    with patch("sla_report.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = sla_report.generate_sla_report(jql="project = SD")

    assert result["total_issues"] == 1


def test_report_by_service_desk(mock_ongoing_sla):
    """Test SLA report for service desk."""
    mock_client = Mock()
    mock_client.get_service_desk.return_value = {"projectKey": "SD"}
    mock_client.search_issues.return_value = {
        "issues": [{"key": "SD-123", "fields": {"summary": "Test"}}]
    }
    mock_client.get_request_slas.return_value = {"values": [mock_ongoing_sla]}

    with patch("sla_report.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = sla_report.generate_sla_report(service_desk_id=1)

    assert result["total_issues"] == 1


def test_report_breach_summary(mock_breached_sla):
    """Test breach summary statistics."""
    assert sla_report._is_breached(mock_breached_sla)


def test_report_by_sla_name(mock_ongoing_sla):
    """Test filtering to specific SLA metric."""
    mock_client = Mock()
    mock_client.search_issues.return_value = {
        "issues": [{"key": "SD-123", "fields": {"summary": "Test"}}]
    }
    mock_client.get_request_slas.return_value = {"values": [mock_ongoing_sla]}

    with patch("sla_report.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = sla_report.generate_sla_report(
            project="SD", sla_name="Time to First Response"
        )

    assert result["total_slas"] == 1


def test_report_csv_export(mock_ongoing_sla):
    """Test CSV export for spreadsheet import."""
    report = {
        "total_issues": 1,
        "total_slas": 1,
        "report_data": [
            {"issue_key": "SD-123", "summary": "Test", "sla": mock_ongoing_sla}
        ],
    }
    csv_output = sla_report.format_report_csv(report)
    assert "Request Key" in csv_output
    assert "SD-123" in csv_output


def test_report_json_export(mock_ongoing_sla):
    """Test JSON export for programmatic use."""
    report = {
        "total_issues": 1,
        "total_slas": 1,
        "report_data": [
            {"issue_key": "SD-123", "summary": "Test", "sla": mock_ongoing_sla}
        ],
    }
    json_output = sla_report.format_report_json(report)
    parsed = json.loads(json_output)
    assert parsed["total_issues"] == 1


def test_report_breached_only(mock_breached_sla, mock_ongoing_sla):
    """Test filtering to breached SLAs only."""
    mock_client = Mock()
    mock_client.search_issues.return_value = {
        "issues": [{"key": "SD-123", "fields": {"summary": "Test"}}]
    }
    mock_client.get_request_slas.return_value = {
        "values": [mock_ongoing_sla, mock_breached_sla]
    }

    with patch("sla_report.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = sla_report.generate_sla_report(project="SD", breached_only=True)

    assert result["total_slas"] == 1  # Only breached SLA


# ========== list_queues.py Tests (6 tests) ==========


def test_list_all_queues(mock_queues):
    """Test listing all queues for service desk."""
    mock_client = Mock()
    mock_client.get_service_desk_queues.return_value = mock_queues

    with patch("list_queues.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = list_queues.list_queues(1)

    assert result["size"] == 3
    assert len(result["values"]) == 3


def test_list_queues_with_jql(mock_queues):
    """Test showing queue JQL queries."""
    text = list_queues.format_queues_text(mock_queues, show_jql=True)
    assert "JQL:" in text
    assert "project = SD" in text


def test_list_queues_empty():
    """Test service desk with no queues."""
    empty_queues = {"size": 0, "values": []}
    mock_client = Mock()
    mock_client.get_service_desk_queues.return_value = empty_queues

    with patch("list_queues.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = list_queues.list_queues(1)

    assert result["size"] == 0


def test_format_queues_text_output(mock_queues):
    """Test human-readable table output."""
    text = list_queues.format_queues_text(mock_queues)
    assert "Open Requests" in text
    assert "3 total" in text


def test_format_queues_json_output(mock_queues):
    """Test JSON output format."""
    json_str = list_queues.format_queues_json(mock_queues)
    parsed = json.loads(json_str)
    assert parsed["size"] == 3


# ========== get_queue.py Tests (6 tests) ==========


def test_get_queue_details(mock_queues):
    """Test getting specific queue by ID."""
    queue = mock_queues["values"][0]
    mock_client = Mock()
    mock_client.get_queue.return_value = queue

    with patch("get_queue.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = get_queue.get_queue(1, 1)

    assert result["name"] == "Open Requests"


def test_get_queue_format_text():
    """Test text formatting of queue details."""
    queue = {"id": "1", "name": "Test Queue", "jql": "project = SD"}
    text = get_queue.format_queue_text(queue)
    assert "Test Queue" in text
    assert "project = SD" in text


def test_get_queue_format_json():
    """Test JSON formatting of queue details."""
    queue = {"id": "1", "name": "Test Queue"}
    json_str = get_queue.format_queue_json(queue)
    parsed = json.loads(json_str)
    assert parsed["name"] == "Test Queue"


def test_get_queue_with_count():
    """Test getting queue with issue count."""
    queue = {"id": "1", "name": "Test Queue", "issueCount": 42}
    mock_client = Mock()
    mock_client.get_queue.return_value = queue

    with patch("get_queue.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = get_queue.get_queue(1, 1)

    assert "issueCount" in result


def test_get_queue_not_found():
    """Test handling queue not found."""
    from jira_assistant_skills_lib import JiraError

    mock_client = Mock()
    mock_client.get_queue.side_effect = JiraError("Queue not found")

    with patch("get_queue.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        with pytest.raises(JiraError):
            get_queue.get_queue(1, 999)


def test_get_queue_jql_display():
    """Test that JQL is properly displayed in queue details."""
    queue = {"id": "1", "name": "Test Queue", "jql": "project = SD AND status = Open"}
    text = get_queue.format_queue_text(queue)
    assert "project = SD AND status = Open" in text


# ========== get_queue_issues.py Tests (5 tests) ==========


def test_get_queue_issues(mock_queue_issues):
    """Test fetching issues in queue."""
    mock_client = Mock()
    mock_client.get_queue_issues.return_value = mock_queue_issues

    with patch("get_queue_issues.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = get_queue_issues.get_queue_issues(1, 1)

    assert result["size"] == 2
    assert len(result["values"]) == 2


def test_get_queue_issues_pagination(mock_queue_issues):
    """Test paginated results."""
    mock_client = Mock()
    mock_client.get_queue_issues.return_value = mock_queue_issues

    with patch("get_queue_issues.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        get_queue_issues.get_queue_issues(1, 1, start=10, limit=25)

    mock_client.get_queue_issues.assert_called_once_with(1, 1, 10, 25)


def test_get_queue_issues_empty():
    """Test queue with no issues."""
    empty_issues = {"size": 0, "values": []}
    mock_client = Mock()
    mock_client.get_queue_issues.return_value = empty_issues

    with patch("get_queue_issues.get_jira_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        result = get_queue_issues.get_queue_issues(1, 1)

    assert result["size"] == 0


def test_format_queue_issues_text(mock_queue_issues):
    """Test human-readable table output."""
    text = get_queue_issues.format_issues_text(mock_queue_issues)
    assert "SD-123" in text
    assert "Login not working" in text


def test_format_queue_issues_json(mock_queue_issues):
    """Test JSON output format."""
    json_str = get_queue_issues.format_issues_json(mock_queue_issues)
    parsed = json.loads(json_str)
    assert parsed["size"] == 2


# ========== Additional Integration Tests ==========


def test_sla_utils_integration():
    """Test JSM utils integration with SLA data."""
    from jsm_utils import (
        calculate_sla_percentage,
        format_duration,
        format_sla_time,
        get_sla_status_emoji,
        get_sla_status_text,
        is_sla_at_risk,
    )

    # Test time formatting
    time_dict = {"friendly": "15/Jan/25 10:00 AM", "iso8601": "2025-01-15T10:00:00Z"}
    assert format_sla_time(time_dict) == "15/Jan/25 10:00 AM"

    # Test duration formatting
    duration = {"millis": 7200000, "friendly": "2h"}
    assert format_duration(duration) == "2h"

    # Test percentage calculation
    percentage = calculate_sla_percentage(7200000, 14400000)
    assert percentage == 50.0

    # Test at-risk detection
    assert is_sla_at_risk(1800000, 14400000, 20.0)  # 12.5% < 20%
    assert not is_sla_at_risk(3600000, 14400000, 20.0)  # 25% > 20%

    # Test status emoji and text
    breached_sla = {"ongoingCycle": {"breached": True}}
    assert get_sla_status_emoji(breached_sla) == "✗"
    assert get_sla_status_text(breached_sla) == "BREACHED"
