"""
Live Integration Test Configuration for jira-ops skill.

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-ops/tests/live_integration/ --profile development -v
"""

import os
import shutil
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from jira_assistant_skills_lib import JiraCache, JiraClient, get_jira_client


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--profile",
        action="store",
        default=os.environ.get("JIRA_PROFILE", "development"),
        help="JIRA profile to use (default: development)",
    )


@pytest.fixture(scope="session")
def jira_profile(request) -> str:
    """Get the JIRA profile from command line."""
    return request.config.getoption("--profile")


@pytest.fixture(scope="session")
def jira_client(jira_profile) -> Generator[JiraClient, None, None]:
    """Create a JIRA client for the test session."""
    client = get_jira_client(jira_profile)
    yield client
    client.close()


@pytest.fixture(scope="function")
def temp_cache_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for cache tests."""
    temp_dir = Path(tempfile.mkdtemp(prefix="jira_cache_test_"))
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def test_cache(temp_cache_dir) -> Generator[JiraCache, None, None]:
    """Create a test cache instance with temporary storage."""
    cache = JiraCache(cache_dir=str(temp_cache_dir))
    yield cache
    cache.close()
