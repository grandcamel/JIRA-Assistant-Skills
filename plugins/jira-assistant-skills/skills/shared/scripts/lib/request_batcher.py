"""
Request batching layer for JIRA API operations.

Provides efficient batching of multiple API requests for parallel
execution with configurable concurrency limits.

Features:
- Collect multiple requests for batch execution
- Parallel execution with max concurrency limit
- Progress reporting via callback
- Partial failure handling (one error doesn't stop others)
- Result mapping back to original request IDs
- Support for GET, POST, PUT, DELETE methods
"""

import asyncio
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any


@dataclass
class BatchResult:
    """Result of a single batched request."""

    request_id: str
    method: str
    endpoint: str
    success: bool
    data: Any | None = None
    error: str | None = None
    duration_ms: float = 0


class BatchError(Exception):
    """Error during batch execution."""

    pass


class RequestBatcher:
    """
    Batch multiple requests for efficient parallel execution.

    Example:
        batcher = RequestBatcher(client, max_concurrent=10)
        id1 = batcher.add("GET", "/rest/api/3/issue/PROJ-1")
        id2 = batcher.add("GET", "/rest/api/3/issue/PROJ-2")
        results = await batcher.execute()
        # or synchronously:
        results = batcher.execute_sync()
    """

    def __init__(self, client, max_concurrent: int = 10):
        """
        Initialize request batcher.

        Args:
            client: JiraClient instance for making requests
            max_concurrent: Maximum number of concurrent requests (default: 10)
        """
        self.client = client
        self.max_concurrent = max_concurrent
        self.requests: list[dict[str, Any]] = []
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)

    def add(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        operation: str | None = None,
    ) -> str:
        """
        Add request to batch.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters (for GET requests)
            data: Request body (for POST/PUT requests)
            operation: Description for error messages

        Returns:
            Request ID for result mapping
        """
        request_id = str(uuid.uuid4())

        self.requests.append(
            {
                "id": request_id,
                "method": method.upper(),
                "endpoint": endpoint,
                "params": params,
                "data": data,
                "operation": operation or f"{method} {endpoint}",
            }
        )

        return request_id

    def clear(self) -> None:
        """Clear all pending requests."""
        self.requests.clear()

    async def execute(
        self, progress_callback: Callable[[int, int], None] | None = None
    ) -> dict[str, BatchResult]:
        """
        Execute all batched requests in parallel.

        Args:
            progress_callback: Optional callback(completed, total) for progress updates

        Returns:
            Dict mapping request IDs to BatchResult objects
        """
        if not self.requests:
            return {}

        total = len(self.requests)
        results: dict[str, BatchResult] = {}
        completed = 0
        completed_lock = asyncio.Lock()

        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def execute_request(request: dict[str, Any]) -> None:
            nonlocal completed

            async with semaphore:
                start_time = time.time()
                request_id = request["id"]

                try:
                    # Execute the request synchronously in thread pool
                    loop = asyncio.get_event_loop()
                    data = await loop.run_in_executor(
                        self._executor, self._execute_single_request, request
                    )

                    duration_ms = (time.time() - start_time) * 1000
                    results[request_id] = BatchResult(
                        request_id=request_id,
                        method=request["method"],
                        endpoint=request["endpoint"],
                        success=True,
                        data=data,
                        duration_ms=duration_ms,
                    )

                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    results[request_id] = BatchResult(
                        request_id=request_id,
                        method=request["method"],
                        endpoint=request["endpoint"],
                        success=False,
                        error=str(e),
                        duration_ms=duration_ms,
                    )

                # Update progress
                async with completed_lock:
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total)

        # Execute all requests concurrently
        tasks = [execute_request(req) for req in self.requests]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results

    def _execute_single_request(self, request: dict[str, Any]) -> Any:
        """
        Execute a single request synchronously.

        Args:
            request: Request configuration dict

        Returns:
            Response data

        Raises:
            Exception on failure
        """
        method = request["method"]
        endpoint = request["endpoint"]
        params = request.get("params")
        data = request.get("data")
        operation = request.get("operation", f"{method} {endpoint}")

        if method == "GET":
            return self.client.get(endpoint, params=params, operation=operation)
        elif method == "POST":
            return self.client.post(endpoint, data=data, operation=operation)
        elif method == "PUT":
            return self.client.put(endpoint, data=data, operation=operation)
        elif method == "DELETE":
            return self.client.delete(endpoint, operation=operation)
        else:
            raise BatchError(f"Unsupported HTTP method: {method}")

    def execute_sync(
        self, progress_callback: Callable[[int, int], None] | None = None
    ) -> dict[str, BatchResult]:
        """
        Execute batch synchronously (wrapper for async execute).

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Dict mapping request IDs to BatchResult objects
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, create new loop
                import nest_asyncio

                nest_asyncio.apply()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            return loop.run_until_complete(self.execute(progress_callback))
        except RuntimeError:
            # Fallback: create a new loop if the existing one can't run
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.execute(progress_callback))
            finally:
                loop.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._executor.shutdown(wait=False)
        return False


def batch_fetch_issues(
    client,
    issue_keys: list[str],
    progress_callback: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    """
    Convenience function to fetch multiple issues in batch.

    Args:
        client: JiraClient instance
        issue_keys: List of issue keys to fetch
        progress_callback: Optional progress callback

    Returns:
        Dict mapping issue keys to issue data (or error)
    """
    batcher = RequestBatcher(client)
    key_to_id = {}

    for key in issue_keys:
        request_id = batcher.add("GET", f"/rest/api/3/issue/{key}")
        key_to_id[key] = request_id

    results = batcher.execute_sync(progress_callback)

    # Map back to issue keys
    issues = {}
    for key, request_id in key_to_id.items():
        result = results.get(request_id)
        if result and result.success:
            issues[key] = result.data
        else:
            issues[key] = {"error": result.error if result else "Unknown error"}

    return issues
