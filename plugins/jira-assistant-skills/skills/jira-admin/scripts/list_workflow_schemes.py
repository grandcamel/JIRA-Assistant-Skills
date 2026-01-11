#!/usr/bin/env python3
"""
List all workflow schemes in a JIRA instance.

Provides workflow scheme discovery with optional mappings and project info.
Requires 'Administer Jira' global permission.
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


def list_workflow_schemes(
    client,
    show_mappings: bool = False,
    show_projects: bool = False,
    max_results: int = 50,
    start_at: int = 0,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """
    List all workflow schemes with optional details.

    Args:
        client: JiraClient instance
        show_mappings: Include issue type to workflow mappings
        show_projects: Include projects using each scheme
        max_results: Maximum results per page
        start_at: Starting index for pagination
        fetch_all: Fetch all pages of results

    Returns:
        Dict with 'schemes' list, 'total', 'has_more'
    """
    all_schemes = []
    current_start = start_at
    has_more = True

    while has_more:
        response = client.get_workflow_schemes(
            start_at=current_start, max_results=max_results
        )

        schemes_data = response.get("values", [])

        for scheme_data in schemes_data:
            scheme = _parse_scheme(scheme_data)

            # Add mappings if requested
            if show_mappings:
                scheme["mappings"] = _parse_mappings(
                    scheme_data.get("issueTypeMappings", {})
                )

            all_schemes.append(scheme)

        # Check if more pages exist
        is_last = response.get("isLast", True)

        if fetch_all and not is_last:
            current_start += max_results
        else:
            has_more = False

    return {
        "schemes": all_schemes,
        "total": len(all_schemes)
        if fetch_all
        else response.get("total", len(all_schemes)),
        "has_more": not response.get("isLast", True) if not fetch_all else False,
    }


def _parse_scheme(scheme_data: dict[str, Any]) -> dict[str, Any]:
    """Parse workflow scheme data from API response."""
    return {
        "id": scheme_data.get("id"),
        "name": scheme_data.get("name", "Unknown"),
        "description": scheme_data.get("description", ""),
        "default_workflow": scheme_data.get("defaultWorkflow", ""),
        "is_draft": scheme_data.get("draft", False),
    }


def _parse_mappings(mappings: dict[str, str]) -> list[dict[str, str]]:
    """Parse issue type to workflow mappings."""
    result = []
    for issue_type_id, workflow_name in mappings.items():
        result.append({"issue_type_id": issue_type_id, "workflow_name": workflow_name})
    return result


def format_schemes_table(schemes: list[dict[str, Any]]) -> str:
    """Format workflow schemes as a table."""
    if not schemes:
        return "No workflow schemes found."

    table_data = []
    columns = ["id", "name", "default_workflow", "description"]
    headers = ["ID", "Name", "Default Workflow", "Description"]

    has_mappings = any("mappings" in s for s in schemes)
    if has_mappings:
        columns.append("mapping_count")
        headers.append("Mappings")

    for scheme in schemes:
        description = scheme.get("description", "")[:40]
        if len(scheme.get("description", "")) > 40:
            description += "..."

        row = {
            "id": str(scheme["id"]),
            "name": scheme["name"],
            "default_workflow": scheme.get("default_workflow", "-"),
            "description": description,
        }

        if has_mappings:
            row["mapping_count"] = str(len(scheme.get("mappings", [])))

        table_data.append(row)

    output = format_table(table_data, columns=columns, headers=headers)
    output += f"\n\nTotal: {len(schemes)} workflow schemes"
    return output


def format_schemes_json(schemes: list[dict[str, Any]]) -> str:
    """Format workflow schemes as JSON."""
    return json.dumps(schemes, indent=2, default=str)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="List all workflow schemes in a JIRA instance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all workflow schemes
  python list_workflow_schemes.py

  # Show issue type mappings
  python list_workflow_schemes.py --show-mappings

  # Show which projects use each scheme
  python list_workflow_schemes.py --show-projects

  # JSON output
  python list_workflow_schemes.py --output json

  # Fetch all pages
  python list_workflow_schemes.py --all

Note: Requires 'Administer Jira' global permission.
        """,
    )

    parser.add_argument(
        "--show-mappings",
        "-m",
        action="store_true",
        help="Show issue type to workflow mappings",
    )
    parser.add_argument(
        "--show-projects",
        "-p",
        action="store_true",
        help="Show projects using each scheme",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum results per page (default: 50)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="fetch_all",
        help="Fetch all pages of results",
    )

    args = parser.parse_args(argv)

    try:
        client = get_jira_client()

        result = list_workflow_schemes(
            client=client,
            show_mappings=args.show_mappings,
            show_projects=args.show_projects,
            max_results=args.max_results,
            fetch_all=args.fetch_all,
        )

        if args.output == "json":
            print(format_schemes_json(result["schemes"]))
        else:
            print(format_schemes_table(result["schemes"]))
            if result["has_more"]:
                print(
                    f"\n(Showing first {len(result['schemes'])} of {result['total']} schemes. Use --all to fetch all.)"
                )

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if "client" in locals():
            client.close()


if __name__ == "__main__":
    main()
