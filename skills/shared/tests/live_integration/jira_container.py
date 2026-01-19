"""
Thread-safe JIRA container management for live integration tests.

Uses a singleton pattern with double-checked locking to ensure only one
container is started, even when tests run in parallel with pytest-xdist.

Usage:
    from jira_container import get_jira_connection

    @pytest.fixture(scope="session")
    def jira_connection():
        return get_jira_connection()
"""

import os
import threading
import time
from dataclasses import dataclass
from typing import Optional

# Global singleton state
_shared_connection: Optional["JiraConnection"] = None
_connection_lock = threading.Lock()


@dataclass
class JiraConnection:
    """Connection details for a JIRA instance."""

    base_url: str
    email: str
    api_token: str
    is_container: bool = False
    container: Optional[object] = None

    def __post_init__(self):
        """Initialize reference counting."""
        self._ref_count = 0
        self._lock = threading.Lock()
        self._is_started = False

    def start(self) -> "JiraConnection":
        """Start or reuse the connection (reference counted)."""
        with self._lock:
            self._ref_count += 1
            if self._is_started:
                return self
            self._is_started = True
        return self

    def stop(self):
        """Stop the connection when last reference is released."""
        with self._lock:
            self._ref_count -= 1
            if self._ref_count > 0:
                return
            if self.is_container and self.container:
                try:
                    self.container.stop()
                except Exception:
                    pass
            self._is_started = False


class JiraContainer:
    """
    JIRA container wrapper for testcontainers.

    Note: JIRA Server/Data Center containers require a license and
    significant resources. For most testing, use a cloud sandbox instance
    via environment variables instead.

    This class is provided for completeness and future DC testing needs.
    """

    # Default configuration
    DEFAULT_IMAGE = "atlassian/jira-software:latest"
    DEFAULT_PORTS = {"8080/tcp": 8080}

    def __init__(
        self,
        image: Optional[str] = None,
        startup_timeout: int = 300,
        health_interval: int = 10,
    ):
        """
        Initialize JIRA container configuration.

        Args:
            image: Docker image to use (default: atlassian/jira-software:latest)
            startup_timeout: Maximum seconds to wait for startup
            health_interval: Seconds between health checks
        """
        self.image = image or os.getenv("JIRA_TEST_IMAGE", self.DEFAULT_IMAGE)
        self.startup_timeout = int(
            os.getenv("JIRA_TEST_STARTUP_TIMEOUT", startup_timeout)
        )
        self.health_interval = int(
            os.getenv("JIRA_TEST_HEALTH_INTERVAL", health_interval)
        )

        self._container = None
        self._ref_count = 0
        self._lock = threading.Lock()
        self._is_started = False

    def start(self) -> "JiraContainer":
        """
        Start the JIRA container (reference counted).

        Returns:
            Self for chaining
        """
        with self._lock:
            self._ref_count += 1
            if self._is_started:
                return self

            try:
                from testcontainers.core.container import DockerContainer

                self._container = DockerContainer(self.image)
                for container_port, host_port in self.DEFAULT_PORTS.items():
                    self._container.with_bind_ports(container_port, host_port)

                # JIRA requires specific environment variables
                self._container.with_env("ATL_JDBC_URL", "jdbc:h2:file:/var/jira/dbconfig")
                self._container.with_env("JVM_MINIMUM_MEMORY", "1024m")
                self._container.with_env("JVM_MAXIMUM_MEMORY", "2048m")

                self._container.start()
                self._wait_for_ready()
                self._is_started = True

            except ImportError:
                raise RuntimeError(
                    "testcontainers package not installed. "
                    "Install with: pip install testcontainers docker"
                )
            except Exception as e:
                self._cleanup()
                raise RuntimeError(f"Failed to start JIRA container: {e}")

        return self

    def stop(self):
        """Stop the container when last reference is released."""
        with self._lock:
            self._ref_count -= 1
            if self._ref_count > 0:
                return
            self._cleanup()
            self._is_started = False

    def _cleanup(self):
        """Clean up container resources."""
        if self._container:
            try:
                self._container.stop()
            except Exception:
                pass
            self._container = None

    def _wait_for_ready(self):
        """Wait for JIRA to be ready with dual-phase health check."""
        start_time = time.time()

        while time.time() - start_time < self.startup_timeout:
            try:
                # Check if container is still running
                if not self._container:
                    raise RuntimeError("Container stopped unexpectedly")

                # Try to connect to JIRA REST API
                import urllib.request

                url = f"http://localhost:8080/rest/api/2/serverInfo"
                req = urllib.request.Request(url, method="GET")
                req.add_header("Accept", "application/json")

                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        return True

            except Exception:
                pass

            time.sleep(self.health_interval)

        raise RuntimeError(
            f"JIRA container did not become ready within {self.startup_timeout}s"
        )

    @property
    def base_url(self) -> str:
        """Get the base URL for the JIRA instance."""
        return "http://localhost:8080"


def get_jira_connection() -> JiraConnection:
    """
    Get a thread-safe singleton JIRA connection.

    Uses double-checked locking to ensure only one connection is created
    even when called from multiple threads or pytest-xdist workers.

    The connection source is determined by environment variables:
    - If JIRA_TEST_URL is set: Use external JIRA instance
    - Otherwise: Start a local container (requires testcontainers)

    Returns:
        JiraConnection with connection details

    Raises:
        RuntimeError: If connection cannot be established
    """
    global _shared_connection

    # Fast path: return existing connection
    if _shared_connection is not None:
        return _shared_connection.start()

    # Slow path: acquire lock and create connection
    with _connection_lock:
        # Double-check after acquiring lock
        if _shared_connection is not None:
            return _shared_connection.start()

        # Check for external JIRA instance
        test_url = os.getenv("JIRA_TEST_URL")
        if test_url:
            # Use external JIRA (cloud or self-hosted)
            email = os.getenv("JIRA_TEST_EMAIL") or os.getenv("JIRA_EMAIL")
            token = os.getenv("JIRA_TEST_TOKEN") or os.getenv("JIRA_API_TOKEN")

            if not email or not token:
                raise RuntimeError(
                    "JIRA_TEST_URL is set but JIRA_TEST_EMAIL/JIRA_TEST_TOKEN "
                    "(or JIRA_EMAIL/JIRA_API_TOKEN) are not configured"
                )

            _shared_connection = JiraConnection(
                base_url=test_url,
                email=email,
                api_token=token,
                is_container=False,
            )
        else:
            # Start container (requires testcontainers)
            container = JiraContainer()
            container.start()

            _shared_connection = JiraConnection(
                base_url=container.base_url,
                email="admin",  # Default JIRA admin
                api_token="admin",  # Default password for container
                is_container=True,
                container=container,
            )

        return _shared_connection.start()


def cleanup_connection():
    """
    Clean up the singleton connection.

    Call this at session end to properly stop containers.
    """
    global _shared_connection
    with _connection_lock:
        if _shared_connection:
            _shared_connection.stop()
            _shared_connection = None
