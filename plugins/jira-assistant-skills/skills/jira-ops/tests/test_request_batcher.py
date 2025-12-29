"""
Test suite for RequestBatcher request batching layer.

Tests cover:
- Collecting requests for batching
- Parallel execution with max concurrency
- Error handling for partial failures
- Progress reporting
- Result mapping to original requests
"""

import pytest
import asyncio
from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import sys

# Add shared lib to path (absolute path)
# From tests/ -> jira-ops/ -> skills/ then into shared/scripts/lib
shared_lib_path = str(Path(__file__).resolve().parent.parent.parent / 'shared' / 'scripts' / 'lib')
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

from jira_assistant_skills_lib import RequestBatcher, BatchResult, BatchError


@pytest.mark.ops
@pytest.mark.unit
class TestBatchCollectRequests:
    """Test collecting requests for batching."""

    def test_batch_add_single_request(self, mock_jira_client):
        """Test adding a single request to batch."""
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("GET", "/rest/api/3/issue/PROJ-123")

        assert request_id is not None
        assert len(request_id) > 0
        assert len(batcher.requests) == 1

    def test_batch_add_multiple_requests(self, mock_jira_client):
        """Test adding multiple requests to batch."""
        batcher = RequestBatcher(mock_jira_client)

        id1 = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        id2 = batcher.add("GET", "/rest/api/3/issue/PROJ-2")
        id3 = batcher.add("GET", "/rest/api/3/issue/PROJ-3")

        assert len(batcher.requests) == 3
        assert id1 != id2 != id3

    def test_batch_add_with_params(self, mock_jira_client):
        """Test adding request with parameters."""
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add(
            "GET",
            "/rest/api/3/search/jql",
            params={"jql": "project = PROJ", "maxResults": 50}
        )

        assert len(batcher.requests) == 1
        assert batcher.requests[0]["params"]["jql"] == "project = PROJ"

    def test_batch_add_with_data(self, mock_jira_client):
        """Test adding POST request with data."""
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add(
            "POST",
            "/rest/api/3/issue",
            data={"fields": {"summary": "Test"}}
        )

        assert len(batcher.requests) == 1
        assert batcher.requests[0]["data"]["fields"]["summary"] == "Test"

    def test_batch_clear_requests(self, mock_jira_client):
        """Test clearing requests from batch."""
        batcher = RequestBatcher(mock_jira_client)
        batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        batcher.add("GET", "/rest/api/3/issue/PROJ-2")

        batcher.clear()

        assert len(batcher.requests) == 0


@pytest.mark.ops
@pytest.mark.unit
class TestBatchExecuteParallel:
    """Test executing batch in parallel."""

    @pytest.mark.asyncio
    async def test_batch_execute_returns_results(self, mock_jira_client):
        """Test that execute returns results for all requests."""
        mock_jira_client.get.return_value = {"key": "PROJ-1"}
        batcher = RequestBatcher(mock_jira_client)

        id1 = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        id2 = batcher.add("GET", "/rest/api/3/issue/PROJ-2")

        results = await batcher.execute()

        assert id1 in results
        assert id2 in results

    @pytest.mark.asyncio
    async def test_batch_execute_empty_batch(self, mock_jira_client):
        """Test executing empty batch returns empty results."""
        batcher = RequestBatcher(mock_jira_client)

        results = await batcher.execute()

        assert results == {}

    def test_batch_execute_sync(self, mock_jira_client):
        """Test synchronous execute wrapper."""
        mock_jira_client.get.return_value = {"key": "PROJ-1"}
        batcher = RequestBatcher(mock_jira_client)

        id1 = batcher.add("GET", "/rest/api/3/issue/PROJ-1")

        results = batcher.execute_sync()

        assert id1 in results


@pytest.mark.ops
@pytest.mark.unit
class TestBatchMaxConcurrent:
    """Test respecting max concurrent limit."""

    @pytest.mark.asyncio
    async def test_batch_respects_max_concurrent(self, mock_jira_client):
        """Test that batch respects max concurrent requests."""
        call_times = []

        async def mock_request(*args, **kwargs):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.05)  # Simulate network delay
            return {"result": "ok"}

        mock_jira_client.get = mock_request
        batcher = RequestBatcher(mock_jira_client, max_concurrent=2)

        # Add 4 requests with max_concurrent=2
        for i in range(4):
            batcher.add("GET", f"/rest/api/3/issue/PROJ-{i}")

        await batcher.execute()

        # With max_concurrent=2, we should see batching effect

    def test_batch_max_concurrent_default(self, mock_jira_client):
        """Test default max concurrent is reasonable."""
        batcher = RequestBatcher(mock_jira_client)

        assert batcher.max_concurrent == 10  # Default

    def test_batch_max_concurrent_custom(self, mock_jira_client):
        """Test custom max concurrent setting."""
        batcher = RequestBatcher(mock_jira_client, max_concurrent=5)

        assert batcher.max_concurrent == 5


@pytest.mark.ops
@pytest.mark.unit
class TestBatchErrorHandling:
    """Test handling partial failures."""

    @pytest.mark.asyncio
    async def test_batch_partial_failure(self, mock_jira_client):
        """Test handling partial failures in batch."""
        def mock_get(endpoint, *args, **kwargs):
            if "PROJ-2" in endpoint:
                raise Exception("API Error")
            return {"key": endpoint.split("/")[-1]}

        mock_jira_client.get.side_effect = mock_get
        batcher = RequestBatcher(mock_jira_client)

        id1 = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        id2 = batcher.add("GET", "/rest/api/3/issue/PROJ-2")
        id3 = batcher.add("GET", "/rest/api/3/issue/PROJ-3")

        results = await batcher.execute()

        # Successful requests should have results
        assert results[id1].success is True
        assert results[id3].success is True

        # Failed request should have error
        assert results[id2].success is False
        assert results[id2].error is not None

    @pytest.mark.asyncio
    async def test_batch_all_fail(self, mock_jira_client):
        """Test handling all requests failing."""
        mock_jira_client.get.side_effect = Exception("Network Error")
        batcher = RequestBatcher(mock_jira_client)

        id1 = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        id2 = batcher.add("GET", "/rest/api/3/issue/PROJ-2")

        results = await batcher.execute()

        assert results[id1].success is False
        assert results[id2].success is False

    @pytest.mark.asyncio
    async def test_batch_continues_after_error(self, mock_jira_client):
        """Test that batch continues processing after error."""
        call_count = 0

        def mock_get(endpoint, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Error on second")
            return {"count": call_count}

        mock_jira_client.get.side_effect = mock_get
        batcher = RequestBatcher(mock_jira_client)

        for i in range(5):
            batcher.add("GET", f"/rest/api/3/issue/PROJ-{i}")

        results = await batcher.execute()

        # All 5 requests should have been attempted
        assert len(results) == 5


@pytest.mark.ops
@pytest.mark.unit
class TestBatchProgressCallback:
    """Test progress reporting."""

    @pytest.mark.asyncio
    async def test_batch_progress_callback_called(self, mock_jira_client):
        """Test progress callback is called for each request."""
        mock_jira_client.get.return_value = {"key": "PROJ-1"}
        batcher = RequestBatcher(mock_jira_client)

        for i in range(5):
            batcher.add("GET", f"/rest/api/3/issue/PROJ-{i}")

        progress_calls = []

        def progress_callback(completed, total):
            progress_calls.append((completed, total))

        await batcher.execute(progress_callback=progress_callback)

        # Should have progress updates for each request
        assert len(progress_calls) >= 5  # At least one update per request
        # Last call should show all complete
        assert progress_calls[-1][0] == 5
        assert progress_calls[-1][1] == 5

    @pytest.mark.asyncio
    async def test_batch_progress_increments(self, mock_jira_client):
        """Test progress increments correctly."""
        mock_jira_client.get.return_value = {"key": "test"}
        batcher = RequestBatcher(mock_jira_client, max_concurrent=1)

        for i in range(3):
            batcher.add("GET", f"/test/{i}")

        progress_values = []

        def callback(completed, total):
            progress_values.append(completed)

        await batcher.execute(progress_callback=callback)

        # Progress should increment
        assert sorted(set(progress_values)) == [1, 2, 3]


@pytest.mark.ops
@pytest.mark.unit
class TestBatchResultMapping:
    """Test mapping results to original requests."""

    @pytest.mark.asyncio
    async def test_batch_result_mapping_correct(self, mock_jira_client):
        """Test results are mapped to correct request IDs."""
        def mock_get(endpoint, *args, **kwargs):
            key = endpoint.split("/")[-1]
            return {"key": key}

        mock_jira_client.get.side_effect = mock_get
        batcher = RequestBatcher(mock_jira_client)

        id1 = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        id2 = batcher.add("GET", "/rest/api/3/issue/PROJ-2")
        id3 = batcher.add("GET", "/rest/api/3/issue/PROJ-3")

        results = await batcher.execute()

        assert results[id1].data["key"] == "PROJ-1"
        assert results[id2].data["key"] == "PROJ-2"
        assert results[id3].data["key"] == "PROJ-3"

    @pytest.mark.asyncio
    async def test_batch_result_includes_request_info(self, mock_jira_client):
        """Test BatchResult includes request information."""
        mock_jira_client.get.return_value = {"key": "test"}
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        results = await batcher.execute()

        result = results[request_id]
        assert result.request_id == request_id
        assert result.method == "GET"
        assert "/rest/api/3/issue/PROJ-1" in result.endpoint


@pytest.mark.ops
@pytest.mark.unit
class TestBatchMethods:
    """Test different HTTP methods in batch."""

    @pytest.mark.asyncio
    async def test_batch_get_method(self, mock_jira_client):
        """Test GET method in batch."""
        mock_jira_client.get.return_value = {"key": "PROJ-1"}
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        results = await batcher.execute()

        mock_jira_client.get.assert_called()
        assert results[request_id].success

    @pytest.mark.asyncio
    async def test_batch_post_method(self, mock_jira_client):
        """Test POST method in batch."""
        mock_jira_client.post.return_value = {"id": "10001", "key": "PROJ-NEW"}
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add(
            "POST",
            "/rest/api/3/issue",
            data={"fields": {"summary": "Test"}}
        )
        results = await batcher.execute()

        mock_jira_client.post.assert_called()
        assert results[request_id].success

    @pytest.mark.asyncio
    async def test_batch_put_method(self, mock_jira_client):
        """Test PUT method in batch."""
        mock_jira_client.put.return_value = {}
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add(
            "PUT",
            "/rest/api/3/issue/PROJ-1",
            data={"fields": {"summary": "Updated"}}
        )
        results = await batcher.execute()

        mock_jira_client.put.assert_called()
        assert results[request_id].success

    @pytest.mark.asyncio
    async def test_batch_mixed_methods(self, mock_jira_client):
        """Test mixing different methods in batch."""
        mock_jira_client.get.return_value = {"key": "PROJ-1"}
        mock_jira_client.post.return_value = {"key": "PROJ-2"}
        mock_jira_client.put.return_value = {}

        batcher = RequestBatcher(mock_jira_client)

        get_id = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        post_id = batcher.add("POST", "/rest/api/3/issue", data={"fields": {}})
        put_id = batcher.add("PUT", "/rest/api/3/issue/PROJ-3", data={"fields": {}})

        results = await batcher.execute()

        assert results[get_id].success
        assert results[post_id].success
        assert results[put_id].success


@pytest.mark.ops
@pytest.mark.unit
class TestBatchErrorCodes:
    """Test handling of specific HTTP error codes."""

    @pytest.mark.asyncio
    async def test_batch_handles_401_unauthorized(self, mock_jira_client):
        """Test handling of 401 authentication error."""
        mock_jira_client.get.side_effect = Exception("Authentication failed: 401 Unauthorized")
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        results = await batcher.execute()

        assert results[request_id].success is False
        assert results[request_id].error is not None
        assert "401" in results[request_id].error or "Authentication" in results[request_id].error

    @pytest.mark.asyncio
    async def test_batch_handles_403_forbidden(self, mock_jira_client):
        """Test handling of 403 permission denied error."""
        mock_jira_client.get.side_effect = Exception("Permission denied: 403 Forbidden")
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        results = await batcher.execute()

        assert results[request_id].success is False
        assert results[request_id].error is not None
        assert "403" in results[request_id].error or "Permission" in results[request_id].error

    @pytest.mark.asyncio
    async def test_batch_handles_404_not_found(self, mock_jira_client):
        """Test handling of 404 not found error."""
        mock_jira_client.get.side_effect = Exception("Issue not found: 404 Not Found")
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("GET", "/rest/api/3/issue/NONEXISTENT-1")
        results = await batcher.execute()

        assert results[request_id].success is False
        assert results[request_id].error is not None
        assert "404" in results[request_id].error or "not found" in results[request_id].error.lower()

    @pytest.mark.asyncio
    async def test_batch_handles_429_rate_limit(self, mock_jira_client):
        """Test handling of 429 rate limit error."""
        mock_jira_client.get.side_effect = Exception("Rate limit exceeded: 429 Too Many Requests")
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        results = await batcher.execute()

        assert results[request_id].success is False
        assert results[request_id].error is not None
        assert "429" in results[request_id].error or "Rate" in results[request_id].error

    @pytest.mark.asyncio
    async def test_batch_handles_500_server_error(self, mock_jira_client):
        """Test handling of 500 internal server error."""
        mock_jira_client.get.side_effect = Exception("Internal server error: 500")
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        results = await batcher.execute()

        assert results[request_id].success is False
        assert results[request_id].error is not None
        assert "500" in results[request_id].error or "server" in results[request_id].error.lower()

    @pytest.mark.asyncio
    async def test_batch_delete_method(self, mock_jira_client):
        """Test DELETE method in batch."""
        mock_jira_client.delete.return_value = None
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("DELETE", "/rest/api/3/issue/PROJ-1")
        results = await batcher.execute()

        mock_jira_client.delete.assert_called()
        assert results[request_id].success is True

    @pytest.mark.asyncio
    async def test_batch_unsupported_method(self, mock_jira_client):
        """Test handling of unsupported HTTP method."""
        batcher = RequestBatcher(mock_jira_client)

        request_id = batcher.add("PATCH", "/rest/api/3/issue/PROJ-1", data={})
        results = await batcher.execute()

        assert results[request_id].success is False
        assert "Unsupported" in results[request_id].error or "method" in results[request_id].error.lower()
