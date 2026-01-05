"""
JSM Live Integration Test Configuration

Pytest fixtures for running integration tests against a real JIRA Service Management instance.
Creates a temporary service desk project, runs tests, and cleans up all resources.

Usage:
    pytest tests/live_integration/ --profile development -v
    pytest tests/live_integration/ --profile development --keep-project -v
    pytest tests/live_integration/ --profile development --service-desk-id 1 -v

Environment:
    Requires JIRA admin permissions to create/delete service desk projects.
    Uses the profile specified via --profile flag or JIRA_PROFILE env var.

Note:
    Some features like Assets/CMDB require JSM Premium license.
    Tests requiring premium features are marked with @pytest.mark.jsm_premium.
"""

import contextlib
import os
import time
import uuid
from collections.abc import Generator
from typing import Any

import pytest

from jira_assistant_skills_lib import JiraClient, get_jira_client


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--profile",
        action="store",
        default=os.environ.get("JIRA_PROFILE", "development"),
        help="JIRA profile to use (default: development)",
    )
    parser.addoption(
        "--keep-project",
        action="store_true",
        default=False,
        help="Keep the test service desk after tests complete (for debugging)",
    )
    parser.addoption(
        "--service-desk-id",
        action="store",
        default=None,
        help="Use existing service desk ID instead of creating one (skips cleanup)",
    )
    parser.addoption(
        "--skip-premium",
        action="store_true",
        default=False,
        help="Skip tests requiring JSM Premium license",
    )


# Note: Common markers (jsm, jsm_premium, jsm_requests, jsm_customers, jsm_approvals,
#       jsm_sla, jsm_queues, jsm_kb) are defined in the root pytest.ini.


def pytest_collection_modifyitems(config, items):
    """Skip premium tests if --skip-premium flag is set."""
    if config.getoption("--skip-premium"):
        skip_premium = pytest.mark.skip(reason="Skipping JSM Premium tests")
        for item in items:
            if "jsm_premium" in item.keywords:
                item.add_marker(skip_premium)


@pytest.fixture(scope="session")
def jira_profile(request) -> str:
    """Get the JIRA profile from command line."""
    return request.config.getoption("--profile")


@pytest.fixture(scope="session")
def keep_project(request) -> bool:
    """Check if service desk should be kept after tests."""
    return request.config.getoption("--keep-project")


@pytest.fixture(scope="session")
def existing_service_desk_id(request) -> str | None:
    """Get existing service desk ID if specified."""
    return request.config.getoption("--service-desk-id")


@pytest.fixture(scope="session")
def jira_client(jira_profile) -> Generator[JiraClient, None, None]:
    """Create a JIRA client for the test session."""
    client = get_jira_client(jira_profile)
    yield client
    client.close()


@pytest.fixture(scope="session")
def test_service_desk(
    jira_client, keep_project, existing_service_desk_id
) -> Generator[dict[str, Any], None, None]:
    """
    Create a unique test service desk for the session.

    The project key is generated as JSM + 6 random hex chars (e.g., JSMA1B2C3).

    Yields:
        Service desk data with keys: 'id', 'projectId', 'projectKey', 'projectName'
    """
    if existing_service_desk_id:
        # Use existing service desk - no cleanup
        service_desk = jira_client.get_service_desk(existing_service_desk_id)
        yield {
            "id": service_desk["id"],
            "projectId": service_desk["projectId"],
            "projectKey": service_desk["projectKey"],
            "projectName": service_desk["projectName"],
            "is_temporary": False,
        }
        return

    # Generate unique project key
    unique_suffix = uuid.uuid4().hex[:6].upper()
    project_key = f"JSM{unique_suffix}"
    project_name = f"JSM Integration Test {project_key}"

    print(f"\n{'=' * 60}")
    print(f"Creating test service desk: {project_key}")
    print(f"{'=' * 60}")

    # Create the service desk project
    try:
        service_desk = jira_client.create_service_desk(
            project_key=project_key, project_name=project_name, project_type="software"
        )
    except Exception as e:
        # Fallback: Create via project API with JSM template
        print(f"Service Desk API failed, trying project API: {e}")
        jira_client.create_project(
            key=project_key,
            name=project_name,
            project_type_key="service_desk",
            template_key="com.atlassian.servicedesk:itil-v2-service-desk-project",
            description="Temporary service desk for live integration tests",
        )
        # Wait for service desk to be created
        time.sleep(3)
        # Get service desk by project key
        service_desks = jira_client.get_service_desks()
        service_desk = next(
            (
                sd
                for sd in service_desks.get("values", [])
                if sd.get("projectKey") == project_key
            ),
            None,
        )
        if not service_desk:
            raise RuntimeError(f"Failed to find service desk for project {project_key}")

    service_desk_data = {
        "id": service_desk["id"],
        "projectId": service_desk["projectId"],
        "projectKey": service_desk.get("projectKey", project_key),
        "projectName": service_desk.get("projectName", project_name),
        "is_temporary": True,
    }

    print(f"Service desk created: {project_key} (ID: {service_desk['id']})")

    yield service_desk_data

    # Cleanup
    if not keep_project and service_desk_data.get("is_temporary", True):
        print(f"\n{'=' * 60}")
        print(f"Cleaning up test service desk: {project_key}")
        print(f"{'=' * 60}")
        cleanup_service_desk(jira_client, project_key, service_desk_data["id"])


def cleanup_service_desk(
    client: JiraClient, project_key: str, service_desk_id: str
) -> None:
    """
    Clean up all resources in a service desk before deletion.

    Order of cleanup:
    1. Delete all organizations created for testing
    2. Delete all requests (issues)
    3. Delete the project (cascades to service desk)
    """
    try:
        # Step 1: Delete organizations created for this project
        print("  Checking for test organizations...")
        try:
            orgs = client.get_service_desk_organizations(service_desk_id)
            for org in orgs.get("values", []):
                if org.get("name", "").startswith("Test Org"):
                    try:
                        client.delete_organization(org["id"])
                        print(f"    Deleted organization: {org['name']}")
                    except Exception as e:
                        print(f"    Warning: Could not delete org {org['id']}: {e}")
        except Exception as e:
            print(f"  Warning: Could not list organizations: {e}")

        # Step 2: Delete all issues/requests
        print(f"  Deleting requests in {project_key}...")
        issues_deleted = 0

        while True:
            result = client.search_issues(
                f"project = {project_key} ORDER BY created DESC",
                fields=["key", "issuetype"],
                max_results=50,
            )
            issues = result.get("issues", [])
            if not issues:
                break

            for issue in issues:
                try:
                    client.delete_issue(issue["key"])
                    issues_deleted += 1
                except Exception as e:
                    print(f"    Warning: Could not delete {issue['key']}: {e}")

        print(f"  Deleted {issues_deleted} requests")

        # Step 3: Delete the project
        print(f"  Deleting project {project_key}...")
        client.delete_project(project_key, enable_undo=True)
        print(f"  Project {project_key} deleted (in trash for 60 days)")

    except Exception as e:
        print(f"  Error during cleanup: {e}")
        raise


@pytest.fixture(scope="session")
def default_request_type(jira_client, test_service_desk) -> dict[str, Any]:
    """
    Get the default request type for the service desk.

    Returns the first available request type (usually 'Get IT help' or similar).
    """
    request_types = jira_client.get_request_types(test_service_desk["id"])
    types = request_types.get("values", [])
    if not types:
        pytest.skip("No request types available in service desk")
    return types[0]


@pytest.fixture(scope="session")
def request_type_with_priority(jira_client, test_service_desk) -> dict[str, Any] | None:
    """
    Find a request type that supports the priority field.

    Returns None if no request type supports priority (test should skip).
    """
    request_types = jira_client.get_request_types(test_service_desk["id"])

    for rt in request_types.get("values", []):
        try:
            fields = jira_client.get_request_type_fields(
                test_service_desk["id"], rt["id"]
            )
            field_ids = [
                f.get("fieldId", "") for f in fields.get("requestTypeFields", [])
            ]
            if "priority" in field_ids:
                return rt
        except Exception:
            continue

    return None


@pytest.fixture(scope="session")
def request_type_with_approval(jira_client, test_service_desk) -> dict[str, Any] | None:
    """
    Find a request type that has an approval workflow configured.

    Returns None if no request type has approval workflow (test should skip).
    """
    request_types = jira_client.get_request_types(test_service_desk["id"])

    for rt in request_types.get("values", []):
        try:
            fields = jira_client.get_request_type_fields(
                test_service_desk["id"], rt["id"]
            )
            field_ids = [
                f.get("fieldId", "").lower()
                for f in fields.get("requestTypeFields", [])
            ]
            # Look for approval-related fields
            if any("approv" in fid for fid in field_ids):
                return rt
        except Exception:
            continue

    return None


@pytest.fixture(scope="session")
def kb_article(jira_client, test_service_desk) -> dict[str, Any] | None:
    """
    Find an existing knowledge base article for testing.

    Returns None if no articles exist (test should skip).
    """
    try:
        # Search for any article
        result = jira_client.search_knowledge_base(test_service_desk["id"], query="*")
        articles = result.get("values", [])
        if articles:
            return articles[0]
    except Exception:
        pass

    # Try common search terms
    for query in ["help", "guide", "how to", "password", "access"]:
        try:
            result = jira_client.search_knowledge_base(
                test_service_desk["id"], query=query
            )
            articles = result.get("values", [])
            if articles:
                return articles[0]
        except Exception:
            continue

    return None


@pytest.fixture(scope="session")
def request_with_sla(
    jira_client, test_service_desk, default_request_type
) -> dict[str, Any] | None:
    """
    Create a request and check if it has SLAs configured.

    Returns the request if SLAs are available, None otherwise.
    """
    request = jira_client.create_request(
        service_desk_id=test_service_desk["id"],
        request_type_id=default_request_type["id"],
        summary=f"SLA Test Request {uuid.uuid4().hex[:8]}",
        description="Request for SLA testing",
    )

    try:
        # Check if SLAs are configured
        sla_result = jira_client.get_request_sla(request["issueKey"])
        if sla_result.get("values"):
            # Has SLAs - return the request
            return request
    except Exception:
        pass

    # No SLAs - cleanup and return None
    with contextlib.suppress(Exception):
        jira_client.delete_issue(request["issueKey"])

    return None


@pytest.fixture(scope="function")
def test_request(
    jira_client, test_service_desk, default_request_type
) -> Generator[dict[str, Any], None, None]:
    """
    Create a test request for individual tests.

    Yields:
        Request data with 'issueKey', 'issueId', etc.
    """
    request = jira_client.create_request(
        service_desk_id=test_service_desk["id"],
        request_type_id=default_request_type["id"],
        summary=f"Test Request {uuid.uuid4().hex[:8]}",
        description="Test request for live integration tests",
    )

    yield request

    # Cleanup
    try:
        jira_client.delete_issue(request["issueKey"])
    except Exception:
        pass  # Request may have been deleted by test


@pytest.fixture(scope="function")
def test_organization(
    jira_client, test_service_desk
) -> Generator[dict[str, Any], None, None]:
    """
    Create a test organization for individual tests.

    Yields:
        Organization data with 'id', 'name', etc.
    """
    org = jira_client.create_organization(name=f"Test Org {uuid.uuid4().hex[:8]}")

    # Add organization to service desk
    try:
        jira_client.add_organization_to_service_desk(test_service_desk["id"], org["id"])
    except Exception:
        pass  # May already be added or feature not available

    yield org

    # Cleanup
    with contextlib.suppress(Exception):
        jira_client.delete_organization(org["id"])


@pytest.fixture(scope="function")
def test_customer(
    jira_client, test_service_desk
) -> Generator[dict[str, Any], None, None]:
    """
    Create a test customer for individual tests.

    Note: Creating customers requires proper permissions and may fail
    if the user is not a service desk agent.

    Yields:
        Customer data with 'accountId', 'displayName', etc.
    """
    unique_id = uuid.uuid4().hex[:8]
    email = f"test.customer.{unique_id}@example.com"

    try:
        customer = jira_client.create_customer(
            email=email,
            display_name=f"Test Customer {unique_id}",
            service_desk_id=test_service_desk["id"],
        )
    except Exception as e:
        pytest.skip(f"Cannot create test customer: {e}")

    yield customer

    # No cleanup needed - customers cannot be deleted via API


@pytest.fixture(scope="function")
def request_with_comments(
    jira_client, test_service_desk, default_request_type
) -> Generator[dict[str, Any], None, None]:
    """
    Create a test request with comments for testing comment functionality.

    Yields:
        Request data with added comments
    """
    request = jira_client.create_request(
        service_desk_id=test_service_desk["id"],
        request_type_id=default_request_type["id"],
        summary=f"Request with Comments {uuid.uuid4().hex[:8]}",
        description="Test request with comments",
    )

    # Add a public comment
    jira_client.add_request_comment(
        request["issueKey"], "Public test comment for integration tests", public=True
    )

    # Add an internal comment
    jira_client.add_request_comment(
        request["issueKey"], "Internal test comment for integration tests", public=False
    )

    yield request

    # Cleanup
    with contextlib.suppress(Exception):
        jira_client.delete_issue(request["issueKey"])


@pytest.fixture(scope="session")
def current_user(jira_client) -> dict[str, Any]:
    """Get the current authenticated user."""
    return jira_client.get_current_user()


def get_available_transitions(
    client: JiraClient, issue_key: str
) -> list[dict[str, Any]]:
    """Helper to get available transitions for a request."""
    return client.get_request_transitions(issue_key)


def transition_request(
    client: JiraClient,
    issue_key: str,
    transition_id: str,
    comment: str | None = None,
) -> None:
    """Helper to transition a request to a new status."""
    client.transition_request(issue_key, transition_id, comment=comment)
