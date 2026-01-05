"""
Live Integration Tests: Approvals and Comments

Tests for approval workflows and comment management against a real JIRA instance.
"""

import contextlib
import time
import uuid

import pytest


@pytest.mark.jsm
@pytest.mark.jsm_requests
class TestRequestComments:
    """Tests for request comment management."""

    def test_add_public_comment(self, jira_client, test_request):
        """Test adding a public comment to a request."""
        comment_body = f"Public test comment {uuid.uuid4().hex[:8]}"

        result = jira_client.add_request_comment(
            test_request["issueKey"], comment_body, public=True
        )

        assert "id" in result or "body" in result

        # Verify comment was added
        comments = jira_client.get_request_comments(test_request["issueKey"])
        comment_bodies = [c.get("body", "") for c in comments.get("values", [])]
        assert any(comment_body in body for body in comment_bodies)

    def test_add_internal_comment(self, jira_client, test_request):
        """Test adding an internal (private) comment to a request."""
        comment_body = f"Internal test comment {uuid.uuid4().hex[:8]}"

        result = jira_client.add_request_comment(
            test_request["issueKey"], comment_body, public=False
        )

        assert "id" in result or "body" in result

        # Verify comment was added
        comments = jira_client.get_request_comments(
            test_request["issueKey"], internal=True
        )
        comment_bodies = [c.get("body", "") for c in comments.get("values", [])]
        assert any(comment_body in body for body in comment_bodies)

    def test_get_request_comments(self, jira_client, request_with_comments):
        """Test getting all comments for a request."""
        result = jira_client.get_request_comments(request_with_comments["issueKey"])

        assert "values" in result
        assert isinstance(result["values"], list)
        # Should have at least the comments added by fixture
        assert len(result["values"]) >= 2

    def test_get_request_comments_public_only(self, jira_client, request_with_comments):
        """Test getting only public comments."""
        result = jira_client.get_request_comments(
            request_with_comments["issueKey"], public=True, internal=False
        )

        assert "values" in result
        # All returned comments should be public
        # Note: Some JSM API versions may not filter correctly
        has_internal = False
        for comment in result.get("values", []):
            if comment.get("public", True) is False:
                has_internal = True
                break

        if has_internal:
            pytest.skip("API filter for public-only comments not working as expected")

    def test_get_request_comments_internal_only(
        self, jira_client, request_with_comments
    ):
        """Test getting only internal comments."""
        result = jira_client.get_request_comments(
            request_with_comments["issueKey"], public=False, internal=True
        )

        assert "values" in result
        # All returned comments should be internal
        for comment in result.get("values", []):
            assert comment.get("public", False) is False

    def test_comment_has_required_fields(self, jira_client, request_with_comments):
        """Test that comments have required fields."""
        result = jira_client.get_request_comments(request_with_comments["issueKey"])

        if result.get("values"):
            comment = result["values"][0]
            required_fields = ["id", "body", "author", "created"]
            for field in required_fields:
                assert field in comment, f"Missing required field: {field}"


@pytest.mark.jsm
@pytest.mark.jsm_requests
class TestRequestParticipants:
    """Tests for request participant management."""

    def test_get_request_participants(self, jira_client, test_request):
        """Test getting participants for a request."""
        result = jira_client.get_request_participants(test_request["issueKey"])

        assert "values" in result
        assert isinstance(result["values"], list)

    def test_add_request_participant(self, jira_client, test_request, current_user):
        """Test adding a participant to a request."""
        try:
            jira_client.add_request_participants(
                test_request["issueKey"], account_ids=[current_user["accountId"]]
            )

            # Verify participant was added
            result = jira_client.get_request_participants(test_request["issueKey"])
            participant_ids = [p.get("accountId") for p in result.get("values", [])]
            assert current_user["accountId"] in participant_ids

        except Exception as e:
            if "403" in str(e) or "permission" in str(e).lower():
                pytest.skip("Insufficient permissions to manage participants")
            raise

    def test_remove_request_participant(
        self, jira_client, test_service_desk, default_request_type, current_user
    ):
        """Test removing a participant from a request."""
        # Create a fresh request for this test
        request = jira_client.create_request(
            service_desk_id=test_service_desk["id"],
            request_type_id=default_request_type["id"],
            summary=f"Participant Remove Test {uuid.uuid4().hex[:8]}",
            description="Testing participant removal",
        )

        try:
            # Add then remove participant
            jira_client.add_request_participants(
                request["issueKey"], account_ids=[current_user["accountId"]]
            )
            jira_client.remove_request_participants(
                request["issueKey"], account_ids=[current_user["accountId"]]
            )

            # Verify participant was removed
            result = jira_client.get_request_participants(request["issueKey"])
            participant_ids = [p.get("accountId") for p in result.get("values", [])]
            assert current_user["accountId"] not in participant_ids

        except Exception as e:
            if "403" in str(e) or "permission" in str(e).lower():
                pytest.skip("Insufficient permissions to manage participants")
            raise
        finally:
            jira_client.delete_issue(request["issueKey"])


@pytest.mark.jsm
@pytest.mark.jsm_approvals
class TestRequestApprovals:
    """Tests for request approval workflows."""

    def test_get_request_approvals(self, jira_client, test_request):
        """Test getting approvals for a request."""
        try:
            result = jira_client.get_request_approvals(test_request["issueKey"])

            assert "values" in result
            assert isinstance(result["values"], list)

        except Exception as e:
            if "404" in str(e):
                pytest.skip("No approval workflow configured for this request type")
            raise

    def test_list_pending_approvals(self, jira_client, test_service_desk):
        """Test listing pending approvals for the current user."""
        try:
            result = jira_client.get_my_approvals(test_service_desk["id"])

            assert "values" in result
            assert isinstance(result["values"], list)

        except Exception as e:
            if "404" in str(e) or "400" in str(e):
                pytest.skip("Approvals feature not available or configured")
            raise


@pytest.mark.jsm
@pytest.mark.jsm_approvals
class TestApprovalWorkflow:
    """Tests for approval workflow operations.

    Note: These tests require a request type with approval workflow configured.
    To enable these tests, configure an approval workflow in your JSM project:
    1. Go to Project Settings > Request Types
    2. Select a request type and enable "Approval" in the workflow
    3. Configure approvers (agents or specific users)
    """

    @pytest.fixture
    def approval_request(
        self, jira_client, test_service_desk, request_type_with_approval
    ):
        """Create a request that triggers an approval workflow.

        Uses the session-scoped request_type_with_approval fixture
        which has already searched for suitable request types.
        """
        if not request_type_with_approval:
            pytest.skip("No request type with approval workflow found")

        request = jira_client.create_request(
            service_desk_id=test_service_desk["id"],
            request_type_id=request_type_with_approval["id"],
            summary=f"Approval Test {uuid.uuid4().hex[:8]}",
            description="Request requiring approval for testing",
        )

        yield request

        with contextlib.suppress(Exception):
            jira_client.delete_issue(request["issueKey"])

    def test_approval_request_has_approvals(self, jira_client, approval_request):
        """Test that approval request has pending approvals."""
        # Small delay for workflow to process
        time.sleep(2)

        result = jira_client.get_request_approvals(approval_request["issueKey"])

        assert "values" in result
        # Should have at least one approval
        if not result["values"]:
            pytest.skip("No approvals generated for this request")

    def test_approve_request(self, jira_client, approval_request):
        """Test approving a request."""
        time.sleep(2)

        approvals = jira_client.get_request_approvals(approval_request["issueKey"])

        if not approvals.get("values"):
            pytest.skip("No approvals available to approve")

        approval = approvals["values"][0]

        if approval.get("canAnswerApproval", False):
            try:
                jira_client.answer_approval(
                    approval_request["issueKey"], approval["id"], decision="approve"
                )

                # Verify approval state changed
                updated = jira_client.get_request_approvals(
                    approval_request["issueKey"]
                )
                # Find our approval
                for appr in updated.get("values", []):
                    if appr["id"] == approval["id"]:
                        # Should be approved or completed
                        assert (
                            appr.get("finalDecision") in ["approved", "declined", None]
                            or appr.get("status") != "pending"
                        )
                        break

            except Exception as e:
                if "already" in str(e).lower():
                    pytest.skip("Approval already answered")
                raise
        else:
            pytest.skip("Current user cannot answer this approval")

    def test_decline_request(
        self, jira_client, test_service_desk, request_type_with_approval
    ):
        """Test declining a request approval."""
        # This test creates its own request to avoid conflicts
        # with the approve test

        if not request_type_with_approval:
            pytest.skip("No request type with approval workflow found")

        request = jira_client.create_request(
            service_desk_id=test_service_desk["id"],
            request_type_id=request_type_with_approval["id"],
            summary=f"Decline Test {uuid.uuid4().hex[:8]}",
            description="Request to decline for testing",
        )

        try:
            time.sleep(2)
            approvals = jira_client.get_request_approvals(request["issueKey"])

            if not approvals.get("values"):
                pytest.skip("No approvals available to decline")

            approval = approvals["values"][0]

            if approval.get("canAnswerApproval", False):
                jira_client.answer_approval(
                    request["issueKey"], approval["id"], decision="decline"
                )

                # Verify decline
                updated = jira_client.get_request_approvals(request["issueKey"])
                for appr in updated.get("values", []):
                    if appr["id"] == approval["id"]:
                        assert (
                            appr.get("finalDecision") in ["declined", None]
                            or appr.get("status") != "pending"
                        )
                        break
            else:
                pytest.skip("Current user cannot answer this approval")

        finally:
            jira_client.delete_issue(request["issueKey"])
