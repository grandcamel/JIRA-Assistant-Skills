"""JSM (Jira Service Management) commands for service desks, requests, SLAs.

This module provides CLI commands for JSM operations including:
- Service desk management
- Request type configuration
- Service requests and comments
- Customer and organization management
- Queue management
- SLA tracking and reporting
- Approval workflows
- Knowledge Base articles
- Asset/CMDB management (requires JSM Premium)
"""

import csv
import json
import sys
from datetime import datetime
from io import StringIO
from typing import Any

import click

from jira_assistant_skills_lib import (
    JiraError,
    NotFoundError,
    PermissionError,
    format_json,
    get_jira_client,
    print_error,
    print_success,
)

from ..cli_utils import handle_jira_errors

# =============================================================================
# Helper Functions
# =============================================================================


def _parse_comma_list(value: str) -> list[str]:
    """Parse comma-separated values into a list."""
    return [v.strip() for v in value.split(",") if v.strip()]


def _parse_attributes(attr_list: list[str]) -> dict[str, str]:
    """Parse attribute list (name=value format) into dict."""
    attributes = {}
    for attr_str in attr_list:
        if "=" not in attr_str:
            raise ValueError(
                f"Invalid attribute format: {attr_str}. Expected: name=value"
            )
        name, value = attr_str.split("=", 1)
        attributes[name.strip()] = value.strip()
    return attributes


def _format_datetime(dt_str: str) -> str:
    """Format ISO datetime string to human-readable format."""
    if not dt_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return dt_str[:16] if len(dt_str) >= 16 else dt_str


def _format_sla_time(millis: int) -> str:
    """Format milliseconds to human-readable time."""
    if millis < 0:
        return "Overdue"
    hours = millis // 3600000
    minutes = (millis % 3600000) // 60000
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _is_sla_breached(sla: dict[str, Any]) -> bool:
    """Check if an SLA is breached."""
    ongoing = sla.get("ongoingCycle")
    if ongoing and ongoing.get("breached"):
        return True
    completed = sla.get("completedCycles", [])
    return bool(completed and completed[-1].get("breached"))


# =============================================================================
# Service Desk Implementation Functions
# =============================================================================


def _list_service_desks_impl(
    start: int = 0, limit: int = 50, project_key_filter: str | None = None
) -> dict[str, Any]:
    """List all JSM service desks."""
    client = get_jira_client()
    try:
        service_desks = client.get_service_desks(start=start, limit=limit)

        # Apply filter if specified
        if project_key_filter:
            filtered = [
                sd
                for sd in service_desks.get("values", [])
                if project_key_filter.upper() in sd.get("projectKey", "").upper()
            ]
            service_desks = {
                **service_desks,
                "values": filtered,
                "size": len(filtered),
            }

        return service_desks
    finally:
        client.close()


def _get_service_desk_impl(service_desk_id: str) -> dict[str, Any]:
    """Get service desk details by ID."""
    client = get_jira_client()
    try:
        return client.get_service_desk(service_desk_id)
    finally:
        client.close()


def _create_service_desk_impl(
    project_key: str, name: str, description: str | None = None
) -> dict[str, Any]:
    """Create a new service desk."""
    with get_jira_client() as client:
        return client.create_service_desk(
            project_key=project_key, name=name, description=description
        )


def _format_service_desks(service_desks: dict[str, Any]) -> str:
    """Format service desks as text."""
    values = service_desks.get("values", [])

    if not values:
        return "No service desks found.\n\nNote: Ensure Jira Service Management is enabled for this instance."

    lines = [
        "Available Service Desks:",
        "",
        f"{'ID':<4} {'Project Key':<15} {'Project Name':<30} {'Project ID':<10}",
        f"{'--':<4} {'-----------':<15} {'------------':<30} {'----------':<10}",
    ]

    for sd in values:
        lines.append(
            f"{sd.get('id', ''):<4} {sd.get('projectKey', ''):<15} "
            f"{sd.get('projectName', ''):<30} {sd.get('projectId', ''):<10}"
        )

    lines.append("")
    lines.append(f"Total: {len(values)} service desk{'s' if len(values) != 1 else ''}")

    return "\n".join(lines)


def _format_service_desk(service_desk: dict[str, Any]) -> str:
    """Format a single service desk as text."""
    lines = [
        "Service Desk Details:",
        "",
        f"ID:           {service_desk.get('id', '')}",
        f"Project ID:   {service_desk.get('projectId', '')}",
        f"Project Key:  {service_desk.get('projectKey', '')}",
        f"Project Name: {service_desk.get('projectName', '')}",
    ]
    return "\n".join(lines)


# =============================================================================
# Request Type Implementation Functions
# =============================================================================


def _list_request_types_impl(
    service_desk_id: str,
    start: int = 0,
    limit: int = 50,
    name_filter: str | None = None,
) -> dict[str, Any]:
    """List request types for a service desk."""
    client = get_jira_client()
    try:
        request_types = client.get_request_types(
            service_desk_id, start=start, limit=limit
        )

        if name_filter:
            filtered = [
                rt
                for rt in request_types.get("values", [])
                if name_filter.lower() in rt.get("name", "").lower()
            ]
            request_types = {
                **request_types,
                "values": filtered,
                "size": len(filtered),
            }

        return request_types
    finally:
        client.close()


def _get_request_type_impl(
    service_desk_id: str, request_type_id: str
) -> dict[str, Any]:
    """Get request type details."""
    client = get_jira_client()
    try:
        return client.get_request_type(service_desk_id, request_type_id)
    finally:
        client.close()


def _get_request_type_fields_impl(
    service_desk_id: str, request_type_id: str
) -> list[dict[str, Any]]:
    """Get fields for a request type."""
    with get_jira_client() as client:
        return client.get_request_type_fields(service_desk_id, request_type_id)


def _format_request_types(
    request_types: dict[str, Any], show_issue_types: bool = False
) -> str:
    """Format request types as text."""
    values = request_types.get("values", [])

    if not values:
        return "No request types found."

    lines = ["Request Types:", ""]

    if show_issue_types:
        lines.append(f"{'ID':<4} {'Name':<30} {'Description':<40} {'Issue Type':<15}")
        lines.append(f"{'--':<4} {'----':<30} {'-----------':<40} {'----------':<15}")

        for rt in values:
            lines.append(
                f"{rt.get('id', ''):<4} {rt.get('name', '')[:28]:<30} "
                f"{rt.get('description', '')[:38]:<40} {rt.get('issueTypeId', ''):<15}"
            )
    else:
        lines.append(f"{'ID':<4} {'Name':<30} {'Description':<50}")
        lines.append(f"{'--':<4} {'----':<30} {'-----------':<50}")

        for rt in values:
            lines.append(
                f"{rt.get('id', ''):<4} {rt.get('name', '')[:28]:<30} "
                f"{rt.get('description', '')[:48]:<50}"
            )

    lines.append("")
    lines.append(f"Total: {len(values)} request type{'s' if len(values) != 1 else ''}")

    return "\n".join(lines)


def _format_request_type(request_type: dict[str, Any]) -> str:
    """Format a single request type as text."""
    lines = [
        "Request Type Details:",
        "",
        f"ID:             {request_type.get('id', '')}",
        f"Name:           {request_type.get('name', '')}",
        f"Description:    {request_type.get('description', '')}",
    ]

    if "helpText" in request_type:
        lines.append(f"Help Text:      {request_type.get('helpText', '')}")

    lines.append("")
    lines.append(f"Service Desk ID: {request_type.get('serviceDeskId', '')}")
    lines.append(f"Issue Type ID:   {request_type.get('issueTypeId', '')}")

    if "groupIds" in request_type:
        groups = request_type.get("groupIds", [])
        lines.append(f"Groups:          {', '.join(groups) if groups else 'None'}")

    return "\n".join(lines)


def _format_request_type_fields(fields: list[dict[str, Any]]) -> str:
    """Format request type fields as text."""
    if not fields:
        return "No fields defined for this request type."

    lines = ["Request Type Fields:", ""]
    lines.append(f"{'Field ID':<20} {'Name':<25} {'Required':<10}")
    lines.append("-" * 60)

    for field in fields:
        field_id = field.get("fieldId", "N/A")
        name = field.get("name", "N/A")
        required = "Yes" if field.get("required", False) else "No"
        lines.append(f"{field_id:<20} {name:<25} {required:<10}")

    return "\n".join(lines)


# =============================================================================
# Request Implementation Functions
# =============================================================================


def _list_requests_impl(
    service_desk_id: str,
    status: str | None = None,
    jql: str | None = None,
    max_results: int = 50,
    start_at: int = 0,
) -> dict[str, Any]:
    """List service requests for a service desk."""
    # Build JQL query
    jql_parts = [f'project="{service_desk_id}"']

    if status:
        jql_parts.append(f'status="{status}"')

    if jql:
        jql_parts.append(f"({jql})")

    final_jql = " AND ".join(jql_parts)

    with get_jira_client() as client:
        return client.search_issues(
            jql=final_jql, max_results=max_results, start_at=start_at
        )


def _create_request_impl(
    service_desk_id: int,
    request_type_id: int,
    summary: str,
    description: str | None = None,
    fields: dict[str, Any] | None = None,
    on_behalf_of: str | None = None,
) -> dict[str, Any]:
    """Create a new service request."""
    with get_jira_client() as client:
        return client.create_request(
            service_desk_id=service_desk_id,
            request_type_id=request_type_id,
            summary=summary,
            description=description,
            fields=fields,
            raise_on_behalf_of=on_behalf_of,
        )


def _get_request_impl(
    issue_key: str, show_sla: bool = False, show_participants: bool = False
) -> dict[str, Any]:
    """Get service request details."""
    expand = []
    if show_sla:
        expand.append("sla")
    if show_participants:
        expand.append("participant")

    with get_jira_client() as client:
        return client.get_request(issue_key, expand=expand if expand else None)


def _get_request_status_impl(issue_key: str) -> dict[str, Any]:
    """Get request status."""
    with get_jira_client() as client:
        return client.get_request_status(issue_key)


def _transition_request_impl(
    issue_key: str,
    transition_id: str | None = None,
    transition_name: str | None = None,
    comment: str | None = None,
    public: bool = True,
) -> None:
    """Transition a service request."""
    with get_jira_client() as client:
        if transition_name and not transition_id:
            transitions = client.get_request_transitions(issue_key)
            matching = [t for t in transitions if t["name"] == transition_name]

            if not matching:
                available = [t["name"] for t in transitions]
                raise ValueError(
                    f"Transition '{transition_name}' not found. "
                    f"Available: {', '.join(available)}"
                )

            transition_id = matching[0]["id"]

        if not transition_id:
            raise ValueError("Either transition_id or transition_name must be provided")

        client.transition_request(
            issue_key, transition_id, comment=comment, public=public
        )


def _list_request_transitions_impl(issue_key: str) -> list[dict[str, Any]]:
    """List available transitions for a request."""
    with get_jira_client() as client:
        return client.get_request_transitions(issue_key)


def _add_request_comment_impl(
    issue_key: str, body: str, public: bool = True
) -> dict[str, Any]:
    """Add a comment to a service request."""
    with get_jira_client() as client:
        return client.add_request_comment(issue_key, body, public=public)


def _get_request_comments_impl(
    issue_key: str,
    public_only: bool = False,
    internal_only: bool = False,
) -> list[dict[str, Any]]:
    """Get comments for a request."""
    with get_jira_client() as client:
        return client.get_request_comments(
            issue_key, public=public_only if public_only else None
        )


def _format_requests(issues: list[dict[str, Any]]) -> str:
    """Format request list as text."""
    if not issues:
        return "No requests found."

    lines = [
        "",
        f"{'Key':<12} {'Summary':<40} {'Status':<20} {'Reporter'}",
        "-" * 100,
    ]

    for issue in issues:
        key = issue.get("key", "N/A")
        fields = issue.get("fields", {})
        summary = fields.get("summary", "N/A")
        if len(summary) > 37:
            summary = summary[:37] + "..."
        status = fields.get("status", {}).get("name", "N/A")
        reporter = fields.get("reporter", {}).get("emailAddress", "N/A")
        lines.append(f"{key:<12} {summary:<40} {status:<20} {reporter}")

    return "\n".join(lines)


def _format_request(request: dict[str, Any], show_fields: bool = False) -> str:
    """Format a single request as text."""
    lines = [f"\nRequest: {request.get('issueKey')}", "=" * 60, ""]

    # Summary
    for field in request.get("requestFieldValues", []):
        if field.get("fieldId") == "summary":
            lines.append(f"Summary: {field.get('value', 'N/A')}")
            lines.append("")
            break

    # Request type
    req_type = request.get("requestType", {})
    lines.append(f"Request Type: {req_type.get('name', 'N/A')}")
    lines.append(f"Service Desk ID: {request.get('serviceDeskId', 'N/A')}")

    # Status
    status = request.get("currentStatus", {})
    lines.append(
        f"Status: {status.get('status', 'N/A')} ({status.get('statusCategory', 'N/A')})"
    )
    lines.append("")

    # Field values
    if show_fields:
        lines.append("Fields:")
        for field in request.get("requestFieldValues", []):
            if field.get("fieldId") != "summary":
                label = field.get("label", field.get("fieldId"))
                value = field.get("value", "N/A")
                lines.append(f"  {label}: {value}")
        lines.append("")

    # Reporter
    reporter = request.get("reporter", {})
    lines.append(f"Reporter: {reporter.get('emailAddress', 'N/A')}")

    # Dates
    created = request.get("createdDate", {})
    lines.append(f"Created: {created.get('friendly', 'N/A')}")
    lines.append("")

    # SLA information
    if "sla" in request:
        lines.append("SLA Information:")
        for sla_metric in request["sla"].get("values", []):
            name = sla_metric.get("name")
            ongoing = sla_metric.get("ongoingCycle", {})

            if ongoing.get("breached"):
                status_icon = "BREACHED"
            else:
                remaining = ongoing.get("remainingTime", {}).get("millis", 0)
                if remaining > 0:
                    status_icon = f"{_format_sla_time(remaining)} remaining"
                else:
                    status_icon = "Met"

            lines.append(f"  {name}: {status_icon}")
        lines.append("")

    # Links
    links = request.get("_links", {})
    lines.append("Links:")
    if "web" in links:
        lines.append(f"  Customer Portal: {links['web']}")
    if "agent" in links:
        lines.append(f"  Agent View: {links['agent']}")

    return "\n".join(lines)


def _format_transitions(transitions: list[dict[str, Any]]) -> str:
    """Format available transitions as text."""
    lines = [
        "",
        f"{'ID':<6} {'Name':<30} {'To Status'}",
        "-" * 60,
    ]

    for t in transitions:
        tid = t.get("id", "N/A")
        name = t.get("name", "N/A")
        to_status = t.get("to", {}).get("name", "N/A")
        lines.append(f"{tid:<6} {name:<30} {to_status}")

    return "\n".join(lines)


# =============================================================================
# Participant Implementation Functions
# =============================================================================


def _get_participants_impl(issue_key: str) -> list[dict[str, Any]]:
    """Get participants for a request."""
    with get_jira_client() as client:
        return client.get_request_participants(issue_key)


def _add_participants_impl(
    issue_key: str,
    account_ids: list[str] | None = None,
    usernames: list[str] | None = None,
) -> dict[str, Any]:
    """Add participants to a request."""
    with get_jira_client() as client:
        return client.add_request_participants(
            issue_key, account_ids=account_ids, usernames=usernames
        )


def _remove_participant_impl(issue_key: str, account_id: str) -> None:
    """Remove a participant from a request."""
    with get_jira_client() as client:
        client.remove_request_participant(issue_key, account_id)


def _format_participants(participants: list[dict[str, Any]]) -> str:
    """Format participants as text."""
    if not participants:
        return "No participants found."

    lines = [
        "Participants:",
        "",
        f"{'Account ID':<30} {'Display Name':<25} {'Email'}",
        "-" * 80,
    ]

    for p in participants:
        account_id = p.get("accountId", "N/A")
        name = p.get("displayName", "N/A")
        email = p.get("emailAddress", "N/A")
        lines.append(f"{account_id:<30} {name:<25} {email}")

    return "\n".join(lines)


# =============================================================================
# Customer Implementation Functions
# =============================================================================


def _list_customers_impl(
    service_desk_id: str,
    query: str | None = None,
    start: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    """List customers for a service desk."""
    with get_jira_client() as client:
        return client.get_service_desk_customers(
            service_desk_id, query=query, start=start, limit=limit
        )


def _create_customer_impl(
    service_desk_id: str, email: str, display_name: str | None = None
) -> dict[str, Any]:
    """Create a new customer."""
    with get_jira_client() as client:
        return client.create_customer(
            service_desk_id, email=email, display_name=display_name
        )


def _add_customer_impl(service_desk_id: str, account_ids: list[str]) -> None:
    """Add existing users as customers to a service desk."""
    with get_jira_client() as client:
        client.add_customers_to_service_desk(service_desk_id, account_ids)


def _remove_customer_impl(service_desk_id: str, account_ids: list[str]) -> None:
    """Remove customers from a service desk."""
    with get_jira_client() as client:
        client.remove_customers_from_service_desk(service_desk_id, account_ids)


def _format_customers(customers_data: dict[str, Any]) -> str:
    """Format customers as text."""
    customers = customers_data.get("values", [])
    total = customers_data.get("size", len(customers))

    if not customers:
        return "No customers found."

    lines = [
        "Customers:",
        "",
        f"{'Email':<30} {'Display Name':<25} {'Active':<10}",
        "-" * 70,
    ]

    active_count = 0
    for customer in customers:
        email = customer.get("emailAddress", "N/A")
        name = customer.get("displayName", "N/A")
        active = customer.get("active", False)
        if active:
            active_count += 1
        lines.append(f"{email:<30} {name:<25} {'Yes' if active else 'No':<10}")

    lines.append("")
    lines.append(f"Total: {total} customers ({active_count} active)")

    return "\n".join(lines)


# =============================================================================
# Organization Implementation Functions
# =============================================================================


def _list_organizations_impl(start: int = 0, limit: int = 50) -> dict[str, Any]:
    """List all organizations."""
    with get_jira_client() as client:
        return client.get_organizations(start=start, limit=limit)


def _get_organization_impl(organization_id: int) -> dict[str, Any]:
    """Get organization details."""
    with get_jira_client() as client:
        return client.get_organization(organization_id)


def _create_organization_impl(name: str) -> dict[str, Any]:
    """Create a new organization."""
    with get_jira_client() as client:
        return client.create_organization(name)


def _delete_organization_impl(organization_id: int) -> None:
    """Delete an organization."""
    with get_jira_client() as client:
        client.delete_organization(organization_id)


def _add_to_organization_impl(organization_id: int, account_ids: list[str]) -> None:
    """Add users to an organization."""
    with get_jira_client() as client:
        client.add_users_to_organization(organization_id, account_ids)


def _remove_from_organization_impl(
    organization_id: int, account_ids: list[str]
) -> None:
    """Remove users from an organization."""
    with get_jira_client() as client:
        client.remove_users_from_organization(organization_id, account_ids)


def _format_organizations(organizations_data: dict[str, Any]) -> str:
    """Format organizations as text."""
    organizations = organizations_data.get("values", [])

    if not organizations:
        return "No organizations found."

    lines = [
        "Organizations:",
        "",
        f"{'ID':<10} {'Name'}",
        "-" * 60,
    ]

    for org in organizations:
        lines.append(f"{org.get('id'):<10} {org.get('name')}")

    lines.append("")
    lines.append(f"Total: {len(organizations)} organization(s)")

    return "\n".join(lines)


def _format_organization(organization: dict[str, Any]) -> str:
    """Format a single organization as text."""
    lines = [
        "Organization Details:",
        "",
        f"ID:   {organization.get('id')}",
        f"Name: {organization.get('name')}",
    ]
    return "\n".join(lines)


# =============================================================================
# Queue Implementation Functions
# =============================================================================


def _list_queues_impl(service_desk_id: int) -> dict[str, Any]:
    """List queues for a service desk."""
    with get_jira_client() as client:
        return client.get_service_desk_queues(service_desk_id)


def _get_queue_impl(service_desk_id: int, queue_id: int) -> dict[str, Any]:
    """Get queue details."""
    with get_jira_client() as client:
        return client.get_queue(service_desk_id, queue_id)


def _get_queue_issues_impl(
    service_desk_id: int, queue_id: int, max_results: int = 50
) -> dict[str, Any]:
    """Get issues in a queue."""
    with get_jira_client() as client:
        return client.get_queue_issues(service_desk_id, queue_id, limit=max_results)


def _format_queues(queues_data: dict[str, Any], show_jql: bool = False) -> str:
    """Format queues as text."""
    queues = queues_data.get("values", [])

    lines = [f"\nQueues: {len(queues)} total", "=" * 80, ""]

    for queue in queues:
        queue_id = queue.get("id")
        name = queue.get("name")
        jql = queue.get("jql", "N/A")

        lines.append(f"[{queue_id}] {name}")
        if show_jql:
            lines.append(f"  JQL: {jql}")

    return "\n".join(lines)


def _format_queue(queue: dict[str, Any]) -> str:
    """Format a single queue as text."""
    lines = [
        f"\nQueue: {queue.get('name')}",
        "=" * 80,
        f"ID: {queue.get('id')}",
        f"JQL: {queue.get('jql', 'N/A')}",
    ]
    return "\n".join(lines)


# =============================================================================
# SLA Implementation Functions
# =============================================================================


def _get_sla_impl(issue_key: str) -> dict[str, Any]:
    """Get SLA information for an issue."""
    with get_jira_client() as client:
        return client.get_request_slas(issue_key)


def _check_sla_breach_impl(issue_key: str) -> dict[str, Any]:
    """Check if an issue is breaching SLA."""
    with get_jira_client() as client:
        sla_data = client.get_request_slas(issue_key)
        slas = sla_data.get("values", [])

        breached = []
        at_risk = []
        ok = []

        for sla in slas:
            name = sla.get("name")
            if _is_sla_breached(sla):
                breached.append(name)
            else:
                ongoing = sla.get("ongoingCycle", {})
                remaining = ongoing.get("remainingTime", {}).get("millis", 0)
                if remaining > 0 and remaining < 3600000:  # Less than 1 hour
                    at_risk.append(name)
                else:
                    ok.append(name)

        return {
            "issue_key": issue_key,
            "breached": breached,
            "at_risk": at_risk,
            "ok": ok,
            "total": len(slas),
        }


def _generate_sla_report_impl(
    project: str | None = None,
    service_desk_id: int | None = None,
    jql: str | None = None,
    sla_name: str | None = None,
    breached_only: bool = False,
) -> dict[str, Any]:
    """Generate SLA compliance report."""
    with get_jira_client() as client:
        # Build JQL query
        if jql:
            query = jql
        elif project:
            query = f"project = {project}"
        elif service_desk_id:
            sd = client.get_service_desk(str(service_desk_id))
            project_key = sd.get("projectKey")
            query = f"project = {project_key}"
        else:
            raise ValueError("Must specify --project, --service-desk, or --jql")

        results = client.search_issues(query, max_results=1000)
        issues = results.get("issues", [])

        report_data = []
        for issue in issues:
            issue_key = issue.get("key")
            try:
                sla_data = client.get_request_slas(issue_key)
                slas = sla_data.get("values", [])

                if sla_name:
                    slas = [s for s in slas if s.get("name") == sla_name]

                if breached_only:
                    slas = [s for s in slas if _is_sla_breached(s)]

                if slas:
                    for sla in slas:
                        report_data.append(
                            {
                                "issue_key": issue_key,
                                "summary": issue.get("fields", {}).get("summary"),
                                "sla": sla,
                            }
                        )
            except Exception:
                pass

    return {
        "total_issues": len(issues),
        "total_slas": len(report_data),
        "report_data": report_data,
    }


def _format_sla(sla_data: dict[str, Any]) -> str:
    """Format SLA information as text."""
    slas = sla_data.get("values", [])

    if not slas:
        return "No SLA information available for this issue."

    lines = ["SLA Information:", ""]

    for sla in slas:
        name = sla.get("name")
        ongoing = sla.get("ongoingCycle", {})

        if ongoing.get("breached"):
            status = "BREACHED"
        else:
            remaining = ongoing.get("remainingTime", {}).get("millis", 0)
            if remaining > 0:
                status = f"{_format_sla_time(remaining)} remaining"
            else:
                status = "Met"

        lines.append(f"  {name}: {status}")

    return "\n".join(lines)


def _format_sla_breach_check(result: dict[str, Any]) -> str:
    """Format SLA breach check result as text."""
    lines = [f"\nSLA Breach Check for {result['issue_key']}", "=" * 60, ""]

    if result["breached"]:
        lines.append("BREACHED SLAs:")
        for name in result["breached"]:
            lines.append(f"  - {name}")
        lines.append("")

    if result["at_risk"]:
        lines.append("AT RISK (< 1 hour):")
        for name in result["at_risk"]:
            lines.append(f"  - {name}")
        lines.append("")

    if result["ok"]:
        lines.append("OK:")
        for name in result["ok"]:
            lines.append(f"  - {name}")

    return "\n".join(lines)


def _format_sla_report_text(report: dict[str, Any]) -> str:
    """Format SLA report as text."""
    lines = [
        "\nSLA Compliance Report",
        "=" * 80,
        f"Total Issues: {report['total_issues']}",
        f"Total SLA Metrics: {report['total_slas']}",
        "",
    ]

    for entry in report["report_data"][:10]:
        issue_key = entry["issue_key"]
        summary = entry["summary"]
        sla = entry["sla"]
        sla_name = sla.get("name")
        is_breached = _is_sla_breached(sla)

        lines.append(f"{issue_key}: {summary[:60]}")
        lines.append(f"  SLA: {sla_name} - {'BREACHED' if is_breached else 'OK'}")

    return "\n".join(lines)


def _format_sla_report_csv(report: dict[str, Any]) -> str:
    """Format SLA report as CSV."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Request Key", "Summary", "SLA Name", "Breached"])

    for entry in report["report_data"]:
        writer.writerow(
            [
                entry["issue_key"],
                entry["summary"],
                entry["sla"].get("name"),
                "Yes" if _is_sla_breached(entry["sla"]) else "No",
            ]
        )

    return output.getvalue()


# =============================================================================
# Approval Implementation Functions
# =============================================================================


def _get_approvals_impl(issue_key: str) -> list[dict[str, Any]]:
    """Get approvals for an issue."""
    with get_jira_client() as client:
        return client.get_request_approvals(issue_key)


def _list_pending_approvals_impl(
    service_desk_id: int | None = None,
) -> list[dict[str, Any]]:
    """List pending approvals."""
    with get_jira_client() as client:
        return client.get_pending_approvals(service_desk_id=service_desk_id)


def _answer_approval_impl(
    issue_key: str,
    approval_id: str,
    decision: str,
) -> dict[str, Any]:
    """Approve or decline an approval request."""
    with get_jira_client() as client:
        return client.answer_approval(issue_key, approval_id, decision)


def _get_approval_details_impl(issue_key: str, approval_id: str) -> dict[str, Any]:
    """Get approval details."""
    with get_jira_client() as client:
        return client.get_request_approval(issue_key, approval_id)


def _format_approvals(approvals: list[dict[str, Any]], issue_key: str) -> str:
    """Format approvals as text."""
    if not approvals:
        return f"No approvals found for {issue_key}."

    lines = [f"\nApprovals for {issue_key}:", ""]
    lines.append(f"{'ID':<10} {'Name':<25} {'Status':<15} {'Approvers'}")
    lines.append("-" * 80)

    for approval in approvals:
        approval_id = approval.get("id", "N/A")
        name = approval.get("name", "N/A")
        status = approval.get("status", "N/A")
        approvers = approval.get("approvers", [])
        approvers_str = ", ".join([a.get("displayName", "Unknown") for a in approvers])

        lines.append(f"{approval_id:<10} {name:<25} {status:<15} {approvers_str}")

    return "\n".join(lines)


def _format_pending_approvals(approvals: list[dict[str, Any]]) -> str:
    """Format pending approvals as text."""
    if not approvals:
        return "No pending approvals found."

    lines = ["Pending Approvals:", ""]
    lines.append(f"{'Issue Key':<12} {'Approval ID':<12} {'Name':<25} {'Created'}")
    lines.append("-" * 80)

    for approval in approvals:
        issue_key = approval.get("issueKey", "N/A")
        approval_id = approval.get("id", "N/A")
        name = approval.get("name", "N/A")
        created = _format_datetime(approval.get("createdDate", ""))

        lines.append(f"{issue_key:<12} {approval_id:<12} {name:<25} {created}")

    return "\n".join(lines)


# =============================================================================
# Knowledge Base Implementation Functions
# =============================================================================


def _search_kb_impl(
    service_desk_id: int, query: str, max_results: int = 50
) -> list[dict[str, Any]]:
    """Search KB articles."""
    with get_jira_client() as client:
        return client.search_kb_articles(service_desk_id, query, max_results)


def _get_kb_article_impl(article_id: str) -> dict[str, Any]:
    """Get a KB article."""
    with get_jira_client() as client:
        return client.get_kb_article(article_id)


def _suggest_kb_impl(issue_key: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Suggest KB articles for an issue."""
    with get_jira_client() as client:
        return client.suggest_kb_articles(issue_key, max_results)


def _format_kb_search_results(articles: list[dict[str, Any]]) -> str:
    """Format KB search results as text."""
    if not articles:
        return "No KB articles found matching your query."

    lines = [f"Knowledge Base Search Results ({len(articles)} articles):", ""]

    for article in articles:
        lines.append(f"Title: {article['title']}")
        if "excerpt" in article:
            excerpt = article["excerpt"].replace("<em>", "").replace("</em>", "")
            lines.append(f"Excerpt: {excerpt}")
        if "_links" in article and "self" in article["_links"]:
            lines.append(f"URL: {article['_links']['self']}")
        lines.append("")

    return "\n".join(lines)


def _format_kb_article(article: dict[str, Any]) -> str:
    """Format a KB article as text."""
    lines = [
        f"KB Article: {article.get('title', 'N/A')}",
        "=" * 60,
        "",
        article.get("body", {}).get("content", "No content available"),
    ]
    return "\n".join(lines)


# =============================================================================
# Asset Implementation Functions (JSM Premium)
# =============================================================================


def _check_assets_license(client) -> None:
    """Check if Assets license is available."""
    if not client.has_assets_license():
        click.echo(
            "ERROR: Assets/Insight not available. Requires JSM Premium license.",
            err=True,
        )
        sys.exit(1)


def _list_assets_impl(
    object_type: str | None = None, iql: str | None = None, max_results: int = 100
) -> list[dict[str, Any]]:
    """List assets with optional filtering."""
    with get_jira_client() as client:
        _check_assets_license(client)
        return client.list_assets(object_type, iql, max_results)


def _get_asset_impl(asset_id: int) -> dict[str, Any]:
    """Get asset details."""
    with get_jira_client() as client:
        _check_assets_license(client)
        return client.get_asset(asset_id)


def _create_asset_impl(
    object_type_id: int, attributes: dict[str, str], dry_run: bool = False
) -> dict[str, Any] | None:
    """Create a new asset."""
    with get_jira_client() as client:
        _check_assets_license(client)

        if dry_run:
            return None

        return client.create_asset(object_type_id, attributes)


def _update_asset_impl(asset_id: int, attributes: dict[str, str]) -> dict[str, Any]:
    """Update an asset."""
    with get_jira_client() as client:
        _check_assets_license(client)
        return client.update_asset(asset_id, attributes)


def _link_asset_impl(asset_id: int, issue_key: str, comment: str | None = None) -> None:
    """Link an asset to an issue."""
    with get_jira_client() as client:
        _check_assets_license(client)
        client.link_asset_to_request(asset_id, issue_key)

        if comment:
            client.add_request_comment(issue_key, comment, public=False)


def _find_affected_assets_impl(issue_key: str) -> list[dict[str, Any]]:
    """Find assets affected by an issue."""
    with get_jira_client() as client:
        _check_assets_license(client)
        return client.find_affected_assets(issue_key)


def _format_assets(assets: list[dict[str, Any]]) -> str:
    """Format assets as text."""
    if not assets:
        return "No assets found matching criteria."

    lines = [f"Assets ({len(assets)} total):", ""]

    for asset in assets:
        lines.append(f"Key: {asset.get('objectKey', 'N/A')}")
        lines.append(f"Label: {asset.get('label', 'N/A')}")

        if "objectType" in asset:
            lines.append(f"Type: {asset['objectType'].get('name', 'N/A')}")

        if "attributes" in asset:
            for attr in asset["attributes"][:3]:
                attr_name = attr.get("objectTypeAttribute", {}).get("name", "Unknown")
                values = attr.get("objectAttributeValues", [])
                if values:
                    attr_value = values[0].get("value", "N/A")
                    lines.append(f"  {attr_name}: {attr_value}")

        lines.append("")

    return "\n".join(lines)


def _format_asset(asset: dict[str, Any]) -> str:
    """Format a single asset as text."""
    lines = [
        f"Asset: {asset.get('objectKey', 'N/A')} ({asset.get('label', 'N/A')})",
        "",
    ]

    if "objectType" in asset:
        lines.append(f"Object Type: {asset['objectType'].get('name', 'N/A')}")

    if "attributes" in asset:
        lines.append("\nAttributes:")
        for attr in asset["attributes"]:
            attr_name = attr.get("objectTypeAttribute", {}).get("name", "Unknown")
            values = attr.get("objectAttributeValues", [])
            if values:
                attr_value = values[0].get("value", "N/A")
                lines.append(f"  {attr_name}: {attr_value}")

    if "_links" in asset and "self" in asset["_links"]:
        lines.append(f"\nURL: {asset['_links']['self']}")

    return "\n".join(lines)


# =============================================================================
# CLI Commands
# =============================================================================


@click.group()
def jsm():
    """Commands for Jira Service Management (service desks, requests, SLAs)."""
    pass


# -----------------------------------------------------------------------------
# Service Desk Commands
# -----------------------------------------------------------------------------


@jsm.group(name="service-desk")
def service_desk():
    """Manage service desks."""
    pass


@service_desk.command(name="list")
@click.option("--filter", "-f", "project_filter", help="Filter by project key/name")
@click.option("--start", "-s", type=int, default=0, help="Starting index (default: 0)")
@click.option(
    "--limit", "-l", type=int, default=50, help="Maximum results (default: 50)"
)
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def service_desk_list(ctx, project_filter: str, start: int, limit: int, output: str):
    """List all service desks."""
    result = _list_service_desks_impl(
        start=start, limit=limit, project_key_filter=project_filter
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_service_desks(result))


@service_desk.command(name="get")
@click.argument("service_desk_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def service_desk_get(ctx, service_desk_id: str, output: str):
    """Get service desk details."""
    result = _get_service_desk_impl(service_desk_id)

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_service_desk(result))


@service_desk.command(name="create")
@click.argument("project_key")
@click.argument("name")
@click.option("--description", "-d", help="Service desk description")
@click.option("--dry-run", is_flag=True, help="Show what would be created")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def service_desk_create(
    ctx, project_key: str, name: str, description: str, dry_run: bool, output: str
):
    """Create a new service desk."""
    if dry_run:
        click.echo("DRY RUN MODE - No changes will be made\n")
        click.echo("Would create service desk:")
        click.echo(f"  Project Key: {project_key}")
        click.echo(f"  Name: {name}")
        if description:
            click.echo(f"  Description: {description}")
        return

    result = _create_service_desk_impl(project_key, name, description)

    if output == "json":
        click.echo(format_json(result))
    else:
        print_success("Service desk created successfully!")
        click.echo(_format_service_desk(result))


# -----------------------------------------------------------------------------
# Request Type Commands
# -----------------------------------------------------------------------------


@jsm.group(name="request-type")
def request_type():
    """Manage request types."""
    pass


@request_type.command(name="list")
@click.argument("service_desk_id")
@click.option("--filter", "-f", "name_filter", help="Filter by name pattern")
@click.option(
    "--show-issue-types", "-i", is_flag=True, help="Show underlying JIRA issue types"
)
@click.option("--start", "-s", type=int, default=0, help="Starting index (default: 0)")
@click.option(
    "--limit", "-l", type=int, default=50, help="Maximum results (default: 50)"
)
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def request_type_list(
    ctx,
    service_desk_id: str,
    name_filter: str,
    show_issue_types: bool,
    start: int,
    limit: int,
    output: str,
):
    """List request types for a service desk."""
    result = _list_request_types_impl(
        service_desk_id, start=start, limit=limit, name_filter=name_filter
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_request_types(result, show_issue_types))


@request_type.command(name="get")
@click.argument("service_desk_id")
@click.argument("request_type_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def request_type_get(ctx, service_desk_id: str, request_type_id: str, output: str):
    """Get request type details."""
    result = _get_request_type_impl(service_desk_id, request_type_id)

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_request_type(result))


@request_type.command(name="fields")
@click.argument("service_desk_id")
@click.argument("request_type_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def request_type_fields(ctx, service_desk_id: str, request_type_id: str, output: str):
    """Get fields for a request type."""
    result = _get_request_type_fields_impl(service_desk_id, request_type_id)

    if output == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(_format_request_type_fields(result))


# -----------------------------------------------------------------------------
# Request Commands
# -----------------------------------------------------------------------------


@jsm.group()
def request():
    """Manage service requests."""
    pass


@request.command(name="list")
@click.argument("service_desk_id")
@click.option("--status", "-s", help="Filter by status")
@click.option("--jql", "-j", help="Additional JQL filter")
@click.option("--max-results", "-m", type=int, default=50, help="Maximum results")
@click.option("--start-at", type=int, default=0, help="Pagination offset")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def request_list(
    ctx,
    service_desk_id: str,
    status: str,
    jql: str,
    max_results: int,
    start_at: int,
    output: str,
):
    """List requests for a service desk."""
    result = _list_requests_impl(
        service_desk_id,
        status=status,
        jql=jql,
        max_results=max_results,
        start_at=start_at,
    )

    issues = result.get("issues", [])
    total = result.get("total", 0)

    if output == "json":
        click.echo(json.dumps(issues, indent=2))
    else:
        click.echo(_format_requests(issues))
        click.echo(f"\nTotal: {total} requests")

        if total > len(issues):
            remaining = total - len(issues) - start_at
            if remaining > 0:
                click.echo(
                    f"Showing {len(issues)} of {total} "
                    f"(use --start-at {start_at + len(issues)} for next page)"
                )


@request.command(name="create")
@click.argument("service_desk_id", type=int)
@click.argument("request_type_id", type=int)
@click.option("--summary", "-s", required=True, help="Request summary")
@click.option("--description", "-d", help="Request description")
@click.option("--fields", "-f", help="Additional fields as JSON")
@click.option("--on-behalf-of", help="Create on behalf of customer (account ID)")
@click.option("--dry-run", is_flag=True, help="Show what would be created")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def request_create(
    ctx,
    service_desk_id: int,
    request_type_id: int,
    summary: str,
    description: str,
    fields: str,
    on_behalf_of: str,
    dry_run: bool,
    output: str,
):
    """Create a new service request."""
    if dry_run:
        click.echo("DRY RUN MODE - No changes will be made\n")
        click.echo("Would create request:")
        click.echo(f"  Service Desk: {service_desk_id}")
        click.echo(f"  Request Type: {request_type_id}")
        click.echo(f"  Summary: {summary}")
        if description:
            click.echo(f"  Description: {description}")
        if on_behalf_of:
            click.echo(f"  On behalf of: {on_behalf_of}")
        return

    fields_dict = json.loads(fields) if fields else None

    result = _create_request_impl(
        service_desk_id=service_desk_id,
        request_type_id=request_type_id,
        summary=summary,
        description=description,
        fields=fields_dict,
        on_behalf_of=on_behalf_of,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        print_success(f"Request created: {result.get('issueKey')}")
        click.echo(_format_request(result))


@request.command(name="get")
@click.argument("issue_key")
@click.option("--show-sla", is_flag=True, help="Include SLA information")
@click.option("--show-participants", is_flag=True, help="Include participant list")
@click.option("--full", is_flag=True, help="Show all details")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def request_get(
    ctx,
    issue_key: str,
    show_sla: bool,
    show_participants: bool,
    full: bool,
    output: str,
):
    """Get request details."""
    show_sla = show_sla or full
    show_participants = show_participants or full

    result = _get_request_impl(
        issue_key, show_sla=show_sla, show_participants=show_participants
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_request(result, show_fields=full))


@request.command(name="status")
@click.argument("issue_key")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def request_status(ctx, issue_key: str, output: str):
    """Get request status."""
    result = _get_request_status_impl(issue_key)

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(f"Status: {result.get('status', 'N/A')}")
        click.echo(f"Category: {result.get('statusCategory', 'N/A')}")


@request.command(name="transition")
@click.argument("issue_key")
@click.option("--to", "transition_name", help="Transition name")
@click.option("--transition-id", help="Transition ID")
@click.option("--comment", "-c", help="Transition comment")
@click.option("--public", is_flag=True, default=True, help="Make comment public")
@click.option("--internal", is_flag=True, help="Make comment internal")
@click.option("--show-transitions", is_flag=True, help="Show available transitions")
@click.option("--dry-run", is_flag=True, help="Show what would be done")
@click.pass_context
@handle_jira_errors
def request_transition(
    ctx,
    issue_key: str,
    transition_name: str,
    transition_id: str,
    comment: str,
    public: bool,
    internal: bool,
    show_transitions: bool,
    dry_run: bool,
):
    """Transition a request to a new status."""
    if show_transitions:
        transitions = _list_request_transitions_impl(issue_key)
        click.echo(f"\nAvailable transitions for {issue_key}:")
        click.echo(_format_transitions(transitions))
        return

    if not transition_name and not transition_id:
        print_error("Either --to or --transition-id must be provided")
        ctx.exit(1)

    is_public = not internal

    if dry_run:
        click.echo("DRY RUN MODE - No changes will be made\n")
        click.echo(f"Would transition request {issue_key}:")
        if transition_name:
            click.echo(f"  To: {transition_name}")
        if transition_id:
            click.echo(f"  Transition ID: {transition_id}")
        if comment:
            visibility = "Public" if is_public else "Internal"
            click.echo(f"  Comment: {comment}")
            click.echo(f"  Visibility: {visibility}")
        return

    _transition_request_impl(
        issue_key=issue_key,
        transition_id=transition_id,
        transition_name=transition_name,
        comment=comment,
        public=is_public,
    )

    print_success(f"Request {issue_key} transitioned successfully!")
    if comment:
        visibility = "public" if is_public else "internal"
        click.echo(f"Comment added ({visibility}): {comment}")


@request.command(name="comment")
@click.argument("issue_key")
@click.argument("body")
@click.option("--internal", "-i", is_flag=True, help="Internal comment (agent-only)")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def request_comment(ctx, issue_key: str, body: str, internal: bool, output: str):
    """Add a comment to a request."""
    is_public = not internal

    result = _add_request_comment_impl(issue_key, body, public=is_public)

    if output == "json":
        click.echo(format_json(result))
    else:
        comment_id = result.get("id", "unknown")
        visibility = "Public" if is_public else "Internal"
        click.echo(f"\nAdded comment to {issue_key} (ID: {comment_id})")
        click.echo(f"Visibility: {visibility}")


@request.command(name="comments")
@click.argument("issue_key")
@click.option("--public-only", "-p", is_flag=True, help="Show only public comments")
@click.option("--internal-only", is_flag=True, help="Show only internal comments")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def request_comments(
    ctx, issue_key: str, public_only: bool, internal_only: bool, output: str
):
    """Get comments for a request."""
    result = _get_request_comments_impl(
        issue_key, public_only=public_only, internal_only=internal_only
    )

    if output == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        if not result:
            click.echo(f"No comments found for {issue_key}.")
        else:
            click.echo(f"\nComments for {issue_key}:\n")
            for comment in result:
                visibility = "Public" if comment.get("public", True) else "Internal"
                author = comment.get("author", {}).get("displayName", "Unknown")
                created = _format_datetime(comment.get("created", ""))
                body = comment.get("body", "")
                click.echo(f"[{visibility}] {author} ({created}):")
                click.echo(f"  {body[:100]}...")
                click.echo("")


# Participant commands (under request group)
@request.command(name="participants")
@click.argument("issue_key")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def request_participants(ctx, issue_key: str, output: str):
    """Get participants for a request."""
    result = _get_participants_impl(issue_key)

    if output == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(_format_participants(result))


@request.command(name="add-participant")
@click.argument("issue_key")
@click.option("--account-id", required=True, help="Account ID(s) (comma-separated)")
@click.option("--dry-run", is_flag=True, help="Show what would be added")
@click.pass_context
@handle_jira_errors
def request_add_participant(ctx, issue_key: str, account_id: str, dry_run: bool):
    """Add participants to a request."""
    account_ids = _parse_comma_list(account_id)

    if not account_ids:
        print_error("No valid account IDs provided")
        ctx.exit(1)

    if dry_run:
        click.echo("DRY RUN MODE - No changes will be made\n")
        click.echo(f"Would add {len(account_ids)} participant(s) to {issue_key}:")
        for aid in account_ids:
            click.echo(f"  - {aid}")
        return

    _add_participants_impl(issue_key, account_ids=account_ids)
    print_success(f"Added {len(account_ids)} participant(s) to {issue_key}")


@request.command(name="remove-participant")
@click.argument("issue_key")
@click.argument("account_id")
@click.pass_context
@handle_jira_errors
def request_remove_participant(ctx, issue_key: str, account_id: str):
    """Remove a participant from a request."""
    _remove_participant_impl(issue_key, account_id)
    print_success(f"Removed participant {account_id} from {issue_key}")


# -----------------------------------------------------------------------------
# Customer Commands
# -----------------------------------------------------------------------------


@jsm.group()
def customer():
    """Manage customers."""
    pass


@customer.command(name="list")
@click.argument("service_desk_id")
@click.option("--query", "-q", help="Search query for email/name filtering")
@click.option("--start", type=int, default=0, help="Starting index (default: 0)")
@click.option("--limit", type=int, default=50, help="Maximum results (default: 50)")
@click.option("--count", is_flag=True, help="Show count only")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def customer_list(
    ctx,
    service_desk_id: str,
    query: str,
    start: int,
    limit: int,
    count: bool,
    output: str,
):
    """List customers for a service desk."""
    result = _list_customers_impl(
        service_desk_id, query=query, start=start, limit=limit
    )

    if count:
        click.echo(result.get("size", len(result.get("values", []))))
        return

    if output == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(_format_customers(result))


@customer.command(name="create")
@click.argument("service_desk_id")
@click.argument("email")
@click.option("--display-name", "-n", help="Customer display name")
@click.option("--dry-run", is_flag=True, help="Show what would be created")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def customer_create(
    ctx, service_desk_id: str, email: str, display_name: str, dry_run: bool, output: str
):
    """Create a new customer."""
    if dry_run:
        click.echo("DRY RUN MODE - No changes will be made\n")
        click.echo("Would create customer:")
        click.echo(f"  Service Desk: {service_desk_id}")
        click.echo(f"  Email: {email}")
        if display_name:
            click.echo(f"  Display Name: {display_name}")
        return

    result = _create_customer_impl(service_desk_id, email, display_name)

    if output == "json":
        click.echo(format_json(result))
    else:
        print_success("Customer created successfully!")
        click.echo(f"Account ID: {result.get('accountId')}")
        click.echo(f"Email: {result.get('emailAddress')}")


@customer.command(name="add")
@click.argument("service_desk_id")
@click.option("--account-id", required=True, help="Account ID(s) (comma-separated)")
@click.option("--dry-run", is_flag=True, help="Show what would be added")
@click.pass_context
@handle_jira_errors
def customer_add(ctx, service_desk_id: str, account_id: str, dry_run: bool):
    """Add existing users as customers."""
    account_ids = _parse_comma_list(account_id)

    if not account_ids:
        print_error("No valid account IDs provided")
        ctx.exit(1)

    if dry_run:
        click.echo("DRY RUN MODE - No changes will be made\n")
        click.echo(f"Would add {len(account_ids)} customer(s) to {service_desk_id}:")
        for aid in account_ids:
            click.echo(f"  - {aid}")
        return

    _add_customer_impl(service_desk_id, account_ids)
    print_success(
        f"Added {len(account_ids)} customer(s) to service desk {service_desk_id}"
    )


@customer.command(name="remove")
@click.argument("service_desk_id")
@click.option("--account-id", required=True, help="Account ID(s) (comma-separated)")
@click.option("--dry-run", is_flag=True, help="Show what would be removed")
@click.pass_context
@handle_jira_errors
def customer_remove(ctx, service_desk_id: str, account_id: str, dry_run: bool):
    """Remove customers from a service desk."""
    account_ids = _parse_comma_list(account_id)

    if not account_ids:
        print_error("No valid account IDs provided")
        ctx.exit(1)

    if dry_run:
        click.echo("DRY RUN MODE - No changes will be made\n")
        click.echo(
            f"Would remove {len(account_ids)} customer(s) from {service_desk_id}:"
        )
        for aid in account_ids:
            click.echo(f"  - {aid}")
        return

    _remove_customer_impl(service_desk_id, account_ids)
    print_success(
        f"Removed {len(account_ids)} customer(s) from service desk {service_desk_id}"
    )


# -----------------------------------------------------------------------------
# Organization Commands
# -----------------------------------------------------------------------------


@jsm.group()
def organization():
    """Manage organizations."""
    pass


@organization.command(name="list")
@click.option("--start", type=int, default=0, help="Starting index (default: 0)")
@click.option("--limit", type=int, default=50, help="Maximum results (default: 50)")
@click.option("--count", is_flag=True, help="Show count only")
@click.option(
    "--output", "-o", type=click.Choice(["text", "json", "csv"]), default="text"
)
@click.pass_context
@handle_jira_errors
def organization_list(ctx, start: int, limit: int, count: bool, output: str):
    """List all organizations."""
    result = _list_organizations_impl(start=start, limit=limit)
    organizations = result.get("values", [])

    if count:
        click.echo(len(organizations))
        return

    if output == "json":
        click.echo(json.dumps(organizations, indent=2))
    elif output == "csv":
        click.echo("ID,Name")
        for org in organizations:
            click.echo(f"{org.get('id')},{org.get('name')}")
    else:
        click.echo(_format_organizations(result))


@organization.command(name="get")
@click.argument("organization_id", type=int)
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def organization_get(ctx, organization_id: int, output: str):
    """Get organization details."""
    result = _get_organization_impl(organization_id)

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_organization(result))


@organization.command(name="create")
@click.option("--name", required=True, help="Organization name")
@click.option("--dry-run", is_flag=True, help="Show what would be created")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def organization_create(ctx, name: str, dry_run: bool, output: str):
    """Create a new organization."""
    if not name or not name.strip():
        print_error("Organization name cannot be empty")
        ctx.exit(1)

    if dry_run:
        click.echo("DRY RUN MODE - No changes will be made\n")
        click.echo("Would create organization:")
        click.echo(f"  Name: {name}")
        return

    result = _create_organization_impl(name)

    if output == "json":
        click.echo(format_json(result))
    else:
        print_success("Organization created successfully!")
        click.echo(_format_organization(result))


@organization.command(name="delete")
@click.argument("organization_id", type=int)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted")
@click.pass_context
@handle_jira_errors
def organization_delete(ctx, organization_id: int, force: bool, dry_run: bool):
    """Delete an organization."""
    if dry_run:
        click.echo("DRY RUN MODE - No changes will be made\n")
        click.echo(f"Would delete organization: {organization_id}")
        return

    if not force:
        if not click.confirm(f"Delete organization {organization_id}?"):
            click.echo("Cancelled.")
            return

    _delete_organization_impl(organization_id)
    print_success(f"Organization {organization_id} deleted")


@organization.command(name="add-customer")
@click.argument("organization_id", type=int)
@click.option("--account-id", required=True, help="Account ID(s) (comma-separated)")
@click.option("--dry-run", is_flag=True, help="Show what would be added")
@click.pass_context
@handle_jira_errors
def organization_add_customer(
    ctx, organization_id: int, account_id: str, dry_run: bool
):
    """Add customers to an organization."""
    account_ids = _parse_comma_list(account_id)

    if not account_ids:
        print_error("No valid account IDs provided")
        ctx.exit(1)

    if dry_run:
        click.echo("DRY RUN MODE - No changes will be made\n")
        click.echo(
            f"Would add {len(account_ids)} customer(s) to organization {organization_id}:"
        )
        for aid in account_ids:
            click.echo(f"  - {aid}")
        return

    _add_to_organization_impl(organization_id, account_ids)
    print_success(
        f"Added {len(account_ids)} customer(s) to organization {organization_id}"
    )


@organization.command(name="remove-customer")
@click.argument("organization_id", type=int)
@click.option("--account-id", required=True, help="Account ID(s) (comma-separated)")
@click.option("--dry-run", is_flag=True, help="Show what would be removed")
@click.pass_context
@handle_jira_errors
def organization_remove_customer(
    ctx, organization_id: int, account_id: str, dry_run: bool
):
    """Remove customers from an organization."""
    account_ids = _parse_comma_list(account_id)

    if not account_ids:
        print_error("No valid account IDs provided")
        ctx.exit(1)

    if dry_run:
        click.echo("DRY RUN MODE - No changes will be made\n")
        click.echo(
            f"Would remove {len(account_ids)} customer(s) from organization {organization_id}:"
        )
        for aid in account_ids:
            click.echo(f"  - {aid}")
        return

    _remove_from_organization_impl(organization_id, account_ids)
    print_success(
        f"Removed {len(account_ids)} customer(s) from organization {organization_id}"
    )


# -----------------------------------------------------------------------------
# Queue Commands
# -----------------------------------------------------------------------------


@jsm.group()
def queue():
    """Manage queues."""
    pass


@queue.command(name="list")
@click.argument("service_desk_id", type=int)
@click.option("--show-jql", is_flag=True, help="Show JQL queries for each queue")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def queue_list(ctx, service_desk_id: int, show_jql: bool, output: str):
    """List queues for a service desk."""
    result = _list_queues_impl(service_desk_id)

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_queues(result, show_jql))


@queue.command(name="get")
@click.argument("service_desk_id", type=int)
@click.argument("queue_id", type=int)
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def queue_get(ctx, service_desk_id: int, queue_id: int, output: str):
    """Get queue details."""
    result = _get_queue_impl(service_desk_id, queue_id)

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_queue(result))


@queue.command(name="issues")
@click.argument("service_desk_id", type=int)
@click.argument("queue_id", type=int)
@click.option("--max-results", "-m", type=int, default=50, help="Maximum results")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def queue_issues(
    ctx, service_desk_id: int, queue_id: int, max_results: int, output: str
):
    """Get issues in a queue."""
    result = _get_queue_issues_impl(service_desk_id, queue_id, max_results)

    issues = result.get("values", [])

    if output == "json":
        click.echo(json.dumps(issues, indent=2))
    else:
        click.echo(_format_requests(issues))
        click.echo(f"\nTotal: {len(issues)} issue(s)")


# -----------------------------------------------------------------------------
# SLA Commands
# -----------------------------------------------------------------------------


@jsm.group()
def sla():
    """Manage SLAs."""
    pass


@sla.command(name="get")
@click.argument("issue_key")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def sla_get(ctx, issue_key: str, output: str):
    """Get SLA information for an issue."""
    result = _get_sla_impl(issue_key)

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_sla(result))


@sla.command(name="check-breach")
@click.argument("issue_key")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def sla_check_breach(ctx, issue_key: str, output: str):
    """Check if an issue is breaching SLA."""
    result = _check_sla_breach_impl(issue_key)

    if output == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(_format_sla_breach_check(result))


@sla.command(name="report")
@click.option("--project", "-p", help="Project key")
@click.option("--service-desk", "-s", type=int, help="Service desk ID")
@click.option("--jql", "-j", help="Custom JQL query")
@click.option("--sla-name", help="Filter to specific SLA")
@click.option("--breached-only", is_flag=True, help="Only show breached SLAs")
@click.option(
    "--output", "-o", type=click.Choice(["text", "csv", "json"]), default="text"
)
@click.pass_context
@handle_jira_errors
def sla_report(
    ctx,
    project: str,
    service_desk: int,
    jql: str,
    sla_name: str,
    breached_only: bool,
    output: str,
):
    """Generate SLA compliance report."""
    if not any([project, service_desk, jql]):
        print_error("Must specify --project, --service-desk, or --jql")
        ctx.exit(1)

    result = _generate_sla_report_impl(
        project=project,
        service_desk_id=service_desk,
        jql=jql,
        sla_name=sla_name,
        breached_only=breached_only,
    )

    if output == "json":
        click.echo(json.dumps(result, indent=2))
    elif output == "csv":
        click.echo(_format_sla_report_csv(result))
    else:
        click.echo(_format_sla_report_text(result))


# -----------------------------------------------------------------------------
# Approval Commands
# -----------------------------------------------------------------------------


@jsm.group()
def approval():
    """Manage approvals."""
    pass


@approval.command(name="list")
@click.argument("issue_key")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def approval_list(ctx, issue_key: str, output: str):
    """Get approvals for an issue."""
    result = _get_approvals_impl(issue_key)

    if output == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(_format_approvals(result, issue_key))


@approval.command(name="pending")
@click.option("--service-desk-id", "-s", type=int, help="Filter by service desk")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def approval_pending(ctx, service_desk_id: int, output: str):
    """List pending approvals."""
    result = _list_pending_approvals_impl(service_desk_id=service_desk_id)

    if output == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(_format_pending_approvals(result))


@approval.command(name="approve")
@click.argument("issue_key")
@click.option("--approval-id", required=True, multiple=True, help="Approval ID(s)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option("--dry-run", is_flag=True, help="Show what would be approved")
@click.pass_context
@handle_jira_errors
def approval_approve(ctx, issue_key: str, approval_id: tuple, yes: bool, dry_run: bool):
    """Approve approval request(s)."""
    for aid in approval_id:
        # Get approval details
        try:
            approval = _get_approval_details_impl(issue_key, aid)
        except (JiraError, NotFoundError, PermissionError) as e:
            print_error(f"Could not get approval {aid}: {e}")
            continue

        approval_name = approval.get("name", "Unknown")
        approvers = approval.get("approvers", [])
        approvers_str = ", ".join([a.get("displayName", "Unknown") for a in approvers])
        created = _format_datetime(approval.get("createdDate", ""))

        click.echo(f"\nApproval ID:   {aid}")
        click.echo(f"Name:          {approval_name}")
        click.echo(f"Approvers:     {approvers_str}")
        click.echo(f"Created:       {created}")

        if dry_run:
            click.echo(f"\n[DRY RUN] Would approve approval {aid} for {issue_key}")
            continue

        if not yes:
            if not click.confirm("\nApprove?"):
                click.echo("Cancelled.")
                continue

        result = _answer_approval_impl(issue_key, aid, "approve")
        completed = _format_datetime(result.get("completedDate", ""))

        print_success(f"Approval {aid} APPROVED for {issue_key}")
        click.echo(f"Completed: {completed}")


@approval.command(name="decline")
@click.argument("issue_key")
@click.option("--approval-id", required=True, multiple=True, help="Approval ID(s)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option("--dry-run", is_flag=True, help="Show what would be declined")
@click.pass_context
@handle_jira_errors
def approval_decline(ctx, issue_key: str, approval_id: tuple, yes: bool, dry_run: bool):
    """Decline approval request(s)."""
    for aid in approval_id:
        # Get approval details
        try:
            approval = _get_approval_details_impl(issue_key, aid)
        except (JiraError, NotFoundError, PermissionError) as e:
            print_error(f"Could not get approval {aid}: {e}")
            continue

        approval_name = approval.get("name", "Unknown")
        approvers = approval.get("approvers", [])
        approvers_str = ", ".join([a.get("displayName", "Unknown") for a in approvers])
        created = _format_datetime(approval.get("createdDate", ""))

        click.echo(f"\nApproval ID:   {aid}")
        click.echo(f"Name:          {approval_name}")
        click.echo(f"Approvers:     {approvers_str}")
        click.echo(f"Created:       {created}")
        click.echo(
            "\nWarning: Declining this approval may prevent the change from proceeding."
        )

        if dry_run:
            click.echo(f"\n[DRY RUN] Would decline approval {aid} for {issue_key}")
            continue

        if not yes:
            if not click.confirm("\nDecline?"):
                click.echo("Cancelled.")
                continue

        result = _answer_approval_impl(issue_key, aid, "decline")
        completed = _format_datetime(result.get("completedDate", ""))

        print_success(f"Approval {aid} DECLINED for {issue_key}")
        click.echo(f"Completed: {completed}")


# -----------------------------------------------------------------------------
# Knowledge Base Commands
# -----------------------------------------------------------------------------


@jsm.group()
def kb():
    """Manage Knowledge Base articles."""
    pass


@kb.command(name="search")
@click.option("--service-desk", "-s", type=int, required=True, help="Service desk ID")
@click.option("--query", "-q", required=True, help="Search query")
@click.option("--max-results", "-m", type=int, default=50, help="Maximum results")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def kb_search(ctx, service_desk: int, query: str, max_results: int, output: str):
    """Search Knowledge Base articles."""
    result = _search_kb_impl(service_desk, query, max_results)

    if output == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(_format_kb_search_results(result))


@kb.command(name="get")
@click.argument("article_id")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def kb_get(ctx, article_id: str, output: str):
    """Get a Knowledge Base article."""
    result = _get_kb_article_impl(article_id)

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_kb_article(result))


@kb.command(name="suggest")
@click.argument("issue_key")
@click.option("--max-results", "-m", type=int, default=5, help="Maximum suggestions")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def kb_suggest(ctx, issue_key: str, max_results: int, output: str):
    """Suggest KB articles for an issue."""
    result = _suggest_kb_impl(issue_key, max_results)

    if output == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(_format_kb_search_results(result))


# -----------------------------------------------------------------------------
# Asset Commands (JSM Premium)
# -----------------------------------------------------------------------------


@jsm.group()
def asset():
    """Manage Assets/CMDB (requires JSM Premium)."""
    pass


@asset.command(name="list")
@click.option("--type", "-t", "object_type", help="Object type name filter")
@click.option("--iql", "-i", help="IQL query string for filtering")
@click.option("--max-results", "-m", type=int, default=100, help="Maximum results")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def asset_list(ctx, object_type: str, iql: str, max_results: int, output: str):
    """List assets."""
    result = _list_assets_impl(object_type, iql, max_results)

    if output == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(_format_assets(result))


@asset.command(name="get")
@click.option("--id", "asset_id", type=int, required=True, help="Asset object ID")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def asset_get(ctx, asset_id: int, output: str):
    """Get asset details."""
    result = _get_asset_impl(asset_id)

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_asset(result))


@asset.command(name="create")
@click.option("--type-id", type=int, required=True, help="Object type ID")
@click.option(
    "--attr",
    multiple=True,
    required=True,
    help="Attribute in format name=value (can use multiple times)",
)
@click.option("--dry-run", is_flag=True, help="Show what would be created")
@click.pass_context
@handle_jira_errors
def asset_create(ctx, type_id: int, attr: tuple, dry_run: bool):
    """Create a new asset."""
    if type_id <= 0:
        print_error(f"--type-id must be a positive integer, got {type_id}")
        ctx.exit(1)

    try:
        attributes = _parse_attributes(list(attr))
    except ValueError as e:
        print_error(str(e))
        ctx.exit(1)

    if dry_run:
        click.echo("DRY RUN: Would create asset with:")
        click.echo(f"  Object Type ID: {type_id}")
        click.echo(f"  Attributes: {json.dumps(attributes, indent=4)}")
        return

    result = _create_asset_impl(type_id, attributes)

    print_success("Asset created successfully!")
    click.echo(f"Asset ID: {result.get('id')}")
    click.echo(f"Asset Key: {result.get('objectKey')}")


@asset.command(name="update")
@click.argument("asset_id", type=int)
@click.option(
    "--attr",
    multiple=True,
    required=True,
    help="Attribute in format name=value (can use multiple times)",
)
@click.option("--dry-run", is_flag=True, help="Show what would be updated")
@click.pass_context
@handle_jira_errors
def asset_update(ctx, asset_id: int, attr: tuple, dry_run: bool):
    """Update an asset."""
    try:
        attributes = _parse_attributes(list(attr))
    except ValueError as e:
        print_error(str(e))
        ctx.exit(1)

    if dry_run:
        click.echo("DRY RUN: Would update asset with:")
        click.echo(f"  Asset ID: {asset_id}")
        click.echo(f"  Attributes: {json.dumps(attributes, indent=4)}")
        return

    result = _update_asset_impl(asset_id, attributes)

    print_success("Asset updated successfully!")
    click.echo(f"Asset Key: {result.get('objectKey')}")


@asset.command(name="link")
@click.option("--request", "-r", required=True, help="Request issue key")
@click.option("--asset-id", type=int, required=True, help="Asset object ID")
@click.option("--comment", "-c", help="Optional comment about the link")
@click.pass_context
@handle_jira_errors
def asset_link(ctx, request: str, asset_id: int, comment: str):
    """Link an asset to a request."""
    _link_asset_impl(asset_id, request, comment)
    print_success(f"Asset {asset_id} linked to {request} successfully!")


@asset.command(name="find-affected")
@click.argument("issue_key")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def asset_find_affected(ctx, issue_key: str, output: str):
    """Find assets affected by an issue."""
    result = _find_affected_assets_impl(issue_key)

    if output == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        if not result:
            click.echo(f"No assets found affected by {issue_key}")
        else:
            click.echo(f"Assets affected by {issue_key}:\n")
            click.echo(_format_assets(result))
