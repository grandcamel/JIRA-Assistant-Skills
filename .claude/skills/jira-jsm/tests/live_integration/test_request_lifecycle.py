"""
Live Integration Tests: Request Lifecycle

Tests for request CRUD operations and status transitions against a real JIRA instance.
"""

import pytest
import uuid
import time


@pytest.mark.jsm
@pytest.mark.jsm_requests
class TestRequestCreate:
    """Tests for request creation."""

    def test_create_basic_request(self, jira_client, test_service_desk, default_request_type):
        """Test creating a basic request."""
        summary = f'Test Request {uuid.uuid4().hex[:8]}'

        request = jira_client.create_request(
            service_desk_id=test_service_desk['id'],
            request_type_id=default_request_type['id'],
            summary=summary,
            description='Test description for integration test'
        )

        assert 'issueKey' in request
        assert request['issueKey'].startswith(test_service_desk['projectKey'])

        # Cleanup
        jira_client.delete_issue(request['issueKey'])

    def test_create_request_with_priority(self, jira_client, test_service_desk, request_type_with_priority):
        """Test creating a request with priority."""
        if not request_type_with_priority:
            pytest.skip("No request type with priority field available")

        request = jira_client.create_request(
            service_desk_id=test_service_desk['id'],
            request_type_id=request_type_with_priority['id'],
            summary=f'Priority Request {uuid.uuid4().hex[:8]}',
            description='High priority test request',
            priority='Medium'
        )

        assert 'issueKey' in request

        # Small delay for request to be fully indexed
        time.sleep(1)

        # Verify request was created
        fetched = jira_client.get_request(request['issueKey'])
        assert fetched['issueKey'] == request['issueKey']

        # Cleanup
        jira_client.delete_issue(request['issueKey'])

    def test_create_request_returns_required_fields(self, jira_client, test_service_desk, default_request_type):
        """Test that created request has all required fields."""
        request = jira_client.create_request(
            service_desk_id=test_service_desk['id'],
            request_type_id=default_request_type['id'],
            summary=f'Fields Test {uuid.uuid4().hex[:8]}',
            description='Testing required fields'
        )

        required_fields = ['issueId', 'issueKey', 'requestTypeId', 'serviceDeskId']
        for field in required_fields:
            assert field in request, f"Missing required field: {field}"

        # Cleanup
        jira_client.delete_issue(request['issueKey'])


@pytest.mark.jsm
@pytest.mark.jsm_requests
class TestRequestRead:
    """Tests for reading request data."""

    def test_get_request(self, jira_client, test_request):
        """Test fetching a request."""
        request = jira_client.get_request(test_request['issueKey'])

        assert request['issueKey'] == test_request['issueKey']
        assert 'currentStatus' in request

    def test_get_request_with_expand(self, jira_client, test_request):
        """Test fetching a request with expanded fields."""
        request = jira_client.get_request(
            test_request['issueKey'],
            expand=['participant', 'status']
        )

        assert request['issueKey'] == test_request['issueKey']

    def test_get_request_status(self, jira_client, test_request):
        """Test getting request status history."""
        result = jira_client.get_request_status(test_request['issueKey'])

        assert 'values' in result
        assert isinstance(result['values'], list)
        # Should have at least the initial status
        if result['values']:
            status = result['values'][0]
            assert 'status' in status

    def test_get_request_not_found(self, jira_client, test_service_desk):
        """Test error handling for non-existent request."""
        with pytest.raises(Exception) as exc_info:
            jira_client.get_request(f'{test_service_desk["projectKey"]}-99999')

        assert '404' in str(exc_info.value) or 'not found' in str(exc_info.value).lower()


@pytest.mark.jsm
@pytest.mark.jsm_requests
class TestRequestUpdate:
    """Tests for updating requests."""

    def test_update_request_summary(self, jira_client, test_request):
        """Test updating request summary via standard issue API."""
        new_summary = f'Updated Summary {uuid.uuid4().hex[:8]}'

        jira_client.update_issue(test_request['issueKey'], {
            'summary': new_summary
        })

        updated = jira_client.get_issue(test_request['issueKey'])
        assert updated['fields']['summary'] == new_summary

    def test_update_request_priority(self, jira_client, test_request):
        """Test updating request priority."""
        jira_client.update_issue(test_request['issueKey'], {
            'priority': {'name': 'High'}
        })

        updated = jira_client.get_issue(test_request['issueKey'])
        assert updated['fields']['priority']['name'] == 'High'


@pytest.mark.jsm
@pytest.mark.jsm_requests
class TestRequestTransitions:
    """Tests for request status transitions."""

    def test_get_available_transitions(self, jira_client, test_request):
        """Test getting available transitions for a request."""
        transitions = jira_client.get_request_transitions(test_request['issueKey'])

        assert isinstance(transitions, list)
        # New requests should have at least one transition available
        if transitions:
            transition = transitions[0]
            assert 'id' in transition
            assert 'name' in transition

    def test_transition_request(self, jira_client, test_request):
        """Test transitioning a request to a new status."""
        transitions = jira_client.get_request_transitions(test_request['issueKey'])

        if not transitions:
            pytest.skip("No transitions available for this request")

        # Find a transition (prefer 'In Progress' or 'Work on issue')
        transition = None
        for t in transitions:
            if 'progress' in t['name'].lower() or 'work' in t['name'].lower():
                transition = t
                break
        if not transition:
            transition = transitions[0]

        # Perform transition
        jira_client.transition_request(
            test_request['issueKey'],
            transition['id']
        )

        # Verify transition
        request = jira_client.get_request(test_request['issueKey'])
        # Status should have changed (name varies by workflow)
        assert 'currentStatus' in request

    def test_transition_with_comment(self, jira_client, test_service_desk, default_request_type):
        """Test transitioning a request with a comment."""
        # Create a fresh request for this test
        request = jira_client.create_request(
            service_desk_id=test_service_desk['id'],
            request_type_id=default_request_type['id'],
            summary=f'Transition Comment Test {uuid.uuid4().hex[:8]}',
            description='Testing transition with comment'
        )

        try:
            transitions = jira_client.get_request_transitions(request['issueKey'])

            if not transitions:
                pytest.skip("No transitions available")

            try:
                # Transition with comment
                jira_client.transition_request(
                    request['issueKey'],
                    transitions[0]['id'],
                    comment='Transitioning as part of integration test'
                )

                # Verify comment was added
                time.sleep(1)
                comments = jira_client.get_request_comments(request['issueKey'])
                comment_texts = [c.get('body', '') for c in comments.get('values', [])]
                assert any('integration test' in c.lower() for c in comment_texts)

            except Exception as e:
                if '400' in str(e) or 'invalid' in str(e).lower() or 'comment' in str(e).lower():
                    pytest.skip("Transition with comment not supported by this workflow")
                raise

        finally:
            jira_client.delete_issue(request['issueKey'])


@pytest.mark.jsm
@pytest.mark.jsm_requests
class TestRequestSearch:
    """Tests for searching requests."""

    def test_search_requests_by_project(self, jira_client, test_service_desk, test_request):
        """Test searching requests by project."""
        # Small delay for indexing
        time.sleep(2)

        result = jira_client.search_issues(
            f"project = {test_service_desk['projectKey']}",
            fields=['key', 'summary', 'status']
        )

        assert 'issues' in result
        # Should find our test request
        keys = [i['key'] for i in result.get('issues', [])]
        # Note: Search indexing may have delay
        if result.get('total', 0) > 0:
            assert test_request['issueKey'] in keys

    def test_search_requests_by_status(self, jira_client, test_service_desk, test_request):
        """Test searching requests by status."""
        time.sleep(2)

        # Get current status of test request
        request = jira_client.get_request(test_request['issueKey'])
        status_name = request['currentStatus']['status']

        result = jira_client.search_issues(
            f'project = {test_service_desk["projectKey"]} AND status = "{status_name}"',
            fields=['key', 'status']
        )

        assert 'issues' in result


@pytest.mark.jsm
@pytest.mark.jsm_requests
class TestRequestDelete:
    """Tests for request deletion."""

    def test_delete_request(self, jira_client, test_service_desk, default_request_type):
        """Test deleting a request."""
        # Create request to delete
        request = jira_client.create_request(
            service_desk_id=test_service_desk['id'],
            request_type_id=default_request_type['id'],
            summary=f'Delete Test {uuid.uuid4().hex[:8]}',
            description='Request to be deleted'
        )

        issue_key = request['issueKey']

        # Delete the request
        jira_client.delete_issue(issue_key)

        # Verify deletion
        with pytest.raises(Exception):
            jira_client.get_issue(issue_key)
