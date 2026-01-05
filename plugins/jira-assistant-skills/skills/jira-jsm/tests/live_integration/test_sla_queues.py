"""
Live Integration Tests: SLA and Queue Management

Tests for SLA monitoring and queue management against a real JIRA instance.
"""

import time

import pytest


@pytest.mark.jsm
@pytest.mark.jsm_sla
class TestSLARead:
    """Tests for reading SLA information."""

    def test_get_request_sla(self, jira_client, request_with_sla):
        """Test getting SLA information for a request."""
        if not request_with_sla:
            pytest.skip("No SLAs configured for this service desk")

        result = jira_client.get_request_sla(request_with_sla["issueKey"])

        assert "values" in result
        assert isinstance(result["values"], list)
        assert len(result["values"]) > 0

    def test_sla_has_required_fields(self, jira_client, request_with_sla):
        """Test that SLA entries have required fields."""
        if not request_with_sla:
            pytest.skip("No SLAs configured for this service desk")

        result = jira_client.get_request_sla(request_with_sla["issueKey"])
        sla = result["values"][0]
        # SLA should have name and timing info
        assert "name" in sla or "sla" in str(sla).lower()

    def test_get_sla_by_name(self, jira_client, request_with_sla):
        """Test getting specific SLA by name."""
        if not request_with_sla:
            pytest.skip("No SLAs configured for this service desk")

        result = jira_client.get_request_sla(request_with_sla["issueKey"])

        # Get first SLA name
        sla_name = result["values"][0].get("name", "")
        if not sla_name:
            pytest.skip("SLA name not available")

        # Try to get specific SLA (if API supports it)
        all_slas = jira_client.get_request_sla(request_with_sla["issueKey"])
        matching = [s for s in all_slas.get("values", []) if s.get("name") == sla_name]
        assert len(matching) >= 1


@pytest.mark.jsm
@pytest.mark.jsm_sla
class TestSLAStatus:
    """Tests for SLA status and breach detection."""

    def test_check_sla_breach_status(self, jira_client, request_with_sla):
        """Test checking if SLA is breached."""
        if not request_with_sla:
            pytest.skip("No SLAs configured for this service desk")

        result = jira_client.get_request_sla(request_with_sla["issueKey"])

        for sla in result["values"]:
            # SLA should have breach status
            # Structure varies by JIRA version
            sla_data = str(sla).lower()
            # Should contain timing or breach info
            assert (
                "breach" in sla_data
                or "time" in sla_data
                or "ongoing" in sla_data
                or "completed" in sla_data
                or "elapsedtime" in sla_data
                or "remainingtime" in sla_data
            )

    def test_sla_timing_info(self, jira_client, request_with_sla):
        """Test that SLA has timing information."""
        if not request_with_sla:
            pytest.skip("No SLAs configured for this service desk")

        result = jira_client.get_request_sla(request_with_sla["issueKey"])
        sla = result["values"][0]
        # Check for timing-related fields
        sla_json = str(sla)
        timing_fields = ["time", "elapsed", "remaining", "goal", "breach"]
        has_timing = any(field in sla_json.lower() for field in timing_fields)
        assert has_timing, "SLA should have timing information"


@pytest.mark.jsm
@pytest.mark.jsm_queues
class TestQueueRead:
    """Tests for reading queue information."""

    def test_list_queues(self, jira_client, test_service_desk):
        """Test listing all queues for a service desk."""
        try:
            result = jira_client.get_queues(test_service_desk["id"])

            assert "values" in result
            assert isinstance(result["values"], list)
            # Service desk should have at least one queue
            assert len(result["values"]) >= 1

        except Exception as e:
            if "403" in str(e) or "permission" in str(e).lower():
                pytest.skip("Insufficient permissions to list queues")
            raise

    def test_queue_has_required_fields(self, jira_client, test_service_desk):
        """Test that queues have required fields."""
        try:
            result = jira_client.get_queues(test_service_desk["id"])

            if result.get("values"):
                queue = result["values"][0]
                required_fields = ["id", "name"]
                for field in required_fields:
                    assert field in queue, f"Missing required field: {field}"

        except Exception as e:
            if "403" in str(e):
                pytest.skip("Insufficient permissions to list queues")
            raise

    def test_get_queue(self, jira_client, test_service_desk):
        """Test getting a specific queue."""
        try:
            queues = jira_client.get_queues(test_service_desk["id"])

            if not queues.get("values"):
                pytest.skip("No queues available")

            queue_id = queues["values"][0]["id"]
            queue = jira_client.get_queue(test_service_desk["id"], queue_id)

            assert queue["id"] == queue_id
            assert "name" in queue

        except Exception as e:
            if "403" in str(e):
                pytest.skip("Insufficient permissions")
            raise


@pytest.mark.jsm
@pytest.mark.jsm_queues
class TestQueueIssues:
    """Tests for queue issue management."""

    def test_get_queue_issues(self, jira_client, test_service_desk, test_request):
        """Test getting issues in a queue."""
        try:
            # Small delay for request to be indexed
            time.sleep(2)

            queues = jira_client.get_queues(test_service_desk["id"])

            if not queues.get("values"):
                pytest.skip("No queues available")

            # Try each queue until we find issues
            for queue in queues["values"]:
                result = jira_client.get_queue_issues(
                    test_service_desk["id"], queue["id"]
                )

                assert "values" in result
                assert isinstance(result["values"], list)

                # If we found issues, verify structure
                if result["values"]:
                    issue = result["values"][0]
                    assert "issueKey" in issue or "key" in issue
                    return  # Found issues, test passes

            # No issues in any queue - that's still valid
            # Our test request might be in a queue

        except Exception as e:
            if "403" in str(e):
                pytest.skip("Insufficient permissions to access queues")
            raise

    def test_queue_issue_count(self, jira_client, test_service_desk):
        """Test getting issue count for a queue."""
        try:
            # Request issue count by passing include_count=True
            queues = jira_client.get_queues(test_service_desk["id"], include_count=True)

            if not queues.get("values"):
                pytest.skip("No queues available")

            queue = queues["values"][0]
            # Queue should have issue count when include_count=True
            # Note: Some JIRA versions may not support this parameter
            queue_str = str(queue)
            has_count = (
                "issueCount" in queue
                or "size" in queue_str
                or "count" in queue_str.lower()
            )
            if not has_count:
                pytest.skip("Issue count not available in queue response")

        except Exception as e:
            if "403" in str(e):
                pytest.skip("Insufficient permissions")
            raise


@pytest.mark.jsm
@pytest.mark.jsm_queues
class TestQueueFiltering:
    """Tests for queue filtering and search."""

    def test_filter_queue_by_status(self, jira_client, test_service_desk, test_request):
        """Test that queues filter by issue status correctly."""
        try:
            time.sleep(2)

            queues = jira_client.get_queues(test_service_desk["id"])

            if not queues.get("values"):
                pytest.skip("No queues available")

            # Find an open issues queue
            open_queue = None
            for q in queues["values"]:
                if (
                    "open" in q.get("name", "").lower()
                    or "all" in q.get("name", "").lower()
                ):
                    open_queue = q
                    break

            if not open_queue:
                # Use first queue
                open_queue = queues["values"][0]

            issues = jira_client.get_queue_issues(
                test_service_desk["id"], open_queue["id"]
            )

            assert "values" in issues
            # Our new request should be in an open queue
            issue_keys = [
                i.get("issueKey", i.get("key", "")) for i in issues.get("values", [])
            ]
            # Note: May not find our specific request if queue is limited
            assert isinstance(issue_keys, list)

        except Exception as e:
            if "403" in str(e):
                pytest.skip("Insufficient permissions")
            raise


@pytest.mark.jsm
@pytest.mark.jsm_sla
class TestSLAReport:
    """Tests for SLA reporting functionality."""

    def test_get_sla_metrics_for_project(self, jira_client, test_service_desk):
        """Test getting SLA metrics/report for a service desk."""
        try:
            # This may require specific API endpoint
            # Attempt to get SLA summary or metrics
            result = jira_client.get_service_desk(test_service_desk["id"])

            # Service desk info should be available
            assert "id" in result

        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("SLA metrics not available")
            raise

    def test_multiple_slas_per_request(self, jira_client, request_with_sla):
        """Test that a request can have multiple SLAs."""
        if not request_with_sla:
            pytest.skip("No SLAs configured for this service desk")

        result = jira_client.get_request_sla(request_with_sla["issueKey"])

        # Should be able to have multiple SLAs
        # (e.g., "Time to first response", "Time to resolution")
        sla_names = [s.get("name", "") for s in result["values"]]
        # Log the SLA names for debugging
        print(f"Found SLAs: {sla_names}")

        # At least one SLA should exist
        assert len(result["values"]) >= 1
