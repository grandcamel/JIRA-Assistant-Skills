#!/usr/bin/env python3
"""
List all statuses in a JIRA instance.

Provides status discovery with filtering by category and workflow.
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    format_table,
    get_jira_client,
    print_error,
)

# Category key mapping
CATEGORY_MAP = {"TODO": "new", "IN_PROGRESS": "indeterminate", "DONE": "done"}


def list_statuses(
    client,
    category: str | None = None,
    workflow: str | None = None,
    search: str | None = None,
    group_by: str | None = None,
    show_usage: bool = False,
    use_search: bool = False,
) -> dict[str, Any]:
    """
    List all statuses with optional filtering.

    Args:
        client: JiraClient instance
        category: Filter by category ('TODO', 'IN_PROGRESS', 'DONE')
        workflow: Filter to statuses in a specific workflow
        search: Search string for status name
        group_by: Group by field ('category')
        show_usage: Include workflow usage information
        use_search: Use search endpoint instead of get all

    Returns:
        Dict with 'statuses' list and optional 'groups'
    """
    if use_search or search:
        # Use search endpoint
        search_category = CATEGORY_MAP.get(category.upper()) if category else None
        response = client.search_statuses(
            search_string=search, status_category=search_category, max_results=200
        )
        statuses_data = response.get("values", [])
    else:
        # Get all statuses
        statuses_data = client.get_all_statuses()

    # Parse statuses
    statuses = []
    for status_data in statuses_data:
        status = _parse_status(status_data)

        # Filter by category
        if category:
            status_cat_key = status.get("category_key", "")
            if status_cat_key != CATEGORY_MAP.get(category.upper()):
                continue

        statuses.append(status)

    # Filter by workflow if specified
    if workflow:
        statuses = _filter_by_workflow(client, statuses, workflow)

    # Add usage info if requested
    if show_usage:
        statuses = _add_usage_info(client, statuses)

    # Group if requested
    result = {"statuses": statuses}

    if group_by == "category":
        result["groups"] = _group_by_category(statuses)

    return result


def _parse_status(status_data: dict[str, Any]) -> dict[str, Any]:
    """Parse status data from API response."""
    cat = status_data.get("statusCategory", {})

    return {
        "id": status_data.get("id", ""),
        "name": status_data.get("name", "Unknown"),
        "description": status_data.get("description", ""),
        "category_name": cat.get("name", "Unknown"),
        "category_key": cat.get("key", ""),
        "category_color": cat.get("colorName", ""),
        "scope_type": status_data.get("scope", {}).get("type", "GLOBAL"),
    }


def _filter_by_workflow(
    client, statuses: list[dict[str, Any]], workflow_name: str
) -> list[dict[str, Any]]:
    """Filter statuses to those in a specific workflow."""
    try:
        response = client.search_workflows(
            workflow_name=workflow_name, expand="statuses", max_results=1
        )
        workflows = response.get("values", [])

        if not workflows:
            return statuses

        workflow_statuses = workflows[0].get("statuses", [])
        workflow_status_ids = {str(s.get("id", "")) for s in workflow_statuses}

        return [s for s in statuses if s["id"] in workflow_status_ids]

    except JiraError:
        return statuses


def _add_usage_info(client, statuses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add workflow usage information to statuses."""
    try:
        response = client.search_workflows(expand="statuses", max_results=100)
        workflows = response.get("values", [])

        # Build status to workflow mapping
        status_workflows = {}
        for wf in workflows:
            wf_name = wf.get("id", {}).get("name", wf.get("name", "Unknown"))
            for s in wf.get("statuses", []):
                sid = str(s.get("id", ""))
                if sid not in status_workflows:
                    status_workflows[sid] = []
                status_workflows[sid].append(wf_name)

        # Add usage to statuses
        for status in statuses:
            workflows = status_workflows.get(status["id"], [])
            status["workflow_count"] = len(workflows)
            status["workflows"] = workflows

    except JiraError:
        pass

    return statuses


def _group_by_category(
    statuses: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group statuses by category."""
    groups = {}
    for status in statuses:
        cat = status.get("category_name", "Unknown")
        if cat not in groups:
            groups[cat] = []
        groups[cat].append(status)
    return groups


def format_statuses_table(statuses: list[dict[str, Any]]) -> str:
    """Format statuses as a table."""
    if not statuses:
        return "No statuses found."

    table_data = []
    columns = ["id", "name", "category", "scope", "description"]
    headers = ["ID", "Name", "Category", "Scope", "Description"]

    has_usage = any("workflow_count" in s for s in statuses)
    if has_usage:
        columns.append("workflow_count")
        headers.append("Workflows")

    for status in statuses:
        description = status.get("description", "")[:30]
        if len(status.get("description", "")) > 30:
            description += "..."

        row = {
            "id": status["id"],
            "name": status["name"],
            "category": status.get("category_name", "-"),
            "scope": "Global" if status.get("scope_type") == "GLOBAL" else "Project",
            "description": description,
        }

        if has_usage:
            row["workflow_count"] = str(status.get("workflow_count", "-"))

        table_data.append(row)

    output = format_table(table_data, columns=columns, headers=headers)
    output += f"\n\nTotal: {len(statuses)} statuses"
    return output


def format_statuses_json(statuses: list[dict[str, Any]]) -> str:
    """Format statuses as JSON."""
    return json.dumps(statuses, indent=2, default=str)


def format_grouped_statuses(groups: dict[str, list[dict[str, Any]]]) -> str:
    """Format grouped statuses for display."""
    lines = []

    for category, statuses in groups.items():
        lines.append(f"\n{category} ({len(statuses)} statuses)")
        lines.append("-" * 40)

        for status in statuses:
            lines.append(f"  {status['id']}: {status['name']}")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="List all statuses in a JIRA instance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all statuses
  python list_statuses.py

  # Filter by category
  python list_statuses.py --category TODO
  python list_statuses.py --category IN_PROGRESS
  python list_statuses.py --category DONE

  # Filter by workflow
  python list_statuses.py --workflow "Software Development Workflow"

  # Group by category
  python list_statuses.py --group-by category

  # Show workflow usage
  python list_statuses.py --show-usage

  # Search by name
  python list_statuses.py --search "Progress"

  # JSON output
  python list_statuses.py --output json
        """,
    )

    parser.add_argument(
        "--category",
        "-c",
        choices=["TODO", "IN_PROGRESS", "DONE"],
        help="Filter by status category",
    )
    parser.add_argument(
        "--workflow", "-w", help="Filter to statuses in a specific workflow"
    )
    parser.add_argument("--search", "-s", help="Search statuses by name")
    parser.add_argument(
        "--group-by", choices=["category"], help="Group results by field"
    )
    parser.add_argument(
        "--show-usage",
        "-u",
        action="store_true",
        help="Show workflow usage for each status",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument("--profile", help="Configuration profile to use")

    args = parser.parse_args(argv)

    try:
        client = get_jira_client(profile=args.profile)

        result = list_statuses(
            client=client,
            category=args.category,
            workflow=args.workflow,
            search=args.search,
            group_by=args.group_by,
            show_usage=args.show_usage,
            use_search=bool(args.search),
        )

        if args.output == "json":
            if "groups" in result:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(format_statuses_json(result["statuses"]))
        else:
            if "groups" in result:
                print(format_grouped_statuses(result["groups"]))
            else:
                print(format_statuses_table(result["statuses"]))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if "client" in locals():
            client.close()


if __name__ == "__main__":
    main()
