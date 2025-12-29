#!/usr/bin/env python3
"""
List and search JIRA projects.

Lists all projects with filtering by type, category, and search query.
Supports pagination and multiple output formats.

Examples:
    # List all projects
    python list_projects.py

    # Filter by type
    python list_projects.py --type software

    # Search by name
    python list_projects.py --search "mobile"

    # Include archived projects
    python list_projects.py --include-archived

    # Export to CSV
    python list_projects.py --output csv > projects.csv
"""

import argparse
import sys
import json
import csv
from io import StringIO
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import JiraError, print_error


def list_projects(
    query: Optional[str] = None,
    project_type: Optional[str] = None,
    category_id: Optional[int] = None,
    include_archived: bool = False,
    expand: Optional[List[str]] = None,
    start_at: int = 0,
    max_results: int = 50,
    output_format: str = "table",
    client=None
) -> Dict[str, Any]:
    """
    List and search projects.

    Args:
        query: Search term for project name/key
        project_type: Filter by type (software, business, service_desk)
        category_id: Filter by category ID
        include_archived: Include archived projects
        expand: Fields to expand
        start_at: Starting index for pagination
        max_results: Maximum results per page
        output_format: Output format (table, json, csv)
        client: JiraClient instance (optional)

    Returns:
        Search results with values, total, isLast

    Raises:
        JiraError: If API call fails
    """
    # Create client if not provided
    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        # Build status filter
        status = ['live']
        if include_archived:
            status.append('archived')

        result = client.search_projects(
            query=query,
            type_key=project_type,
            category_id=category_id,
            status=status,
            expand=expand,
            start_at=start_at,
            max_results=max_results
        )

        return result

    finally:
        if should_close:
            client.close()


def list_trash_projects(
    start_at: int = 0,
    max_results: int = 50,
    client=None
) -> Dict[str, Any]:
    """
    List projects in trash.

    Args:
        start_at: Starting index for pagination
        max_results: Maximum results per page
        client: JiraClient instance (optional)

    Returns:
        Trashed projects with values, total, isLast

    Raises:
        JiraError: If API call fails
    """
    # Create client if not provided
    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        result = client.search_projects(
            status=['deleted'],
            start_at=start_at,
            max_results=max_results
        )

        return result

    finally:
        if should_close:
            client.close()


def format_table(projects: List[Dict[str, Any]]) -> str:
    """Format projects as table."""
    if not projects:
        return "No projects found."

    headers = ["Key", "Name", "Type", "Category", "Lead"]
    rows = []

    for proj in projects:
        category = proj.get('projectCategory', {})
        category_name = category.get('name', '-') if category else '-'

        lead = proj.get('lead', {})
        lead_name = lead.get('displayName', '-') if lead else '-'

        rows.append([
            proj.get('key', '-'),
            proj.get('name', '-')[:40],
            proj.get('projectTypeKey', '-'),
            category_name,
            lead_name[:20]
        ])

    # Use tabulate if available, otherwise simple format
    try:
        from tabulate import tabulate
        return tabulate(rows, headers=headers, tablefmt="grid")
    except ImportError:
        # Simple format
        lines = ["\t".join(headers)]
        lines.append("-" * 80)
        for row in rows:
            lines.append("\t".join(str(x) for x in row))
        return "\n".join(lines)


def format_csv(projects: List[Dict[str, Any]]) -> str:
    """Format projects as CSV."""
    if not projects:
        return ""

    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Key", "Name", "Type", "Category", "Lead", "ID", "URL"])

    # Rows
    for proj in projects:
        category = proj.get('projectCategory', {})
        category_name = category.get('name', '') if category else ''

        lead = proj.get('lead', {})
        lead_name = lead.get('displayName', '') if lead else ''

        writer.writerow([
            proj.get('key', ''),
            proj.get('name', ''),
            proj.get('projectTypeKey', ''),
            category_name,
            lead_name,
            proj.get('id', ''),
            proj.get('self', '')
        ])

    return output.getvalue()


def format_output(result: Dict[str, Any], output_format: str = "table") -> str:
    """Format search results for output."""
    projects = result.get('values', [])

    if output_format == "json":
        return json.dumps(result, indent=2)

    if output_format == "csv":
        return format_csv(projects)

    # Table format
    lines = [format_table(projects)]

    # Add pagination info
    total = result.get('total', len(projects))
    start_at = result.get('startAt', 0)

    if total > len(projects):
        lines.append(f"\nShowing {start_at + 1}-{start_at + len(projects)} of {total} projects")
        if not result.get('isLast', True):
            lines.append(f"Use --start-at {start_at + len(projects)} to see more")

    return "\n".join(lines)


def format_trash_output(result: Dict[str, Any], output_format: str = "table") -> str:
    """Format trash results for output."""
    projects = result.get('values', [])

    if output_format == "json":
        return json.dumps(result, indent=2)

    if not projects:
        return "No projects in trash."

    if output_format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Key", "Name", "Deleted Date", "Retention Till", "Deleted By"])

        for proj in projects:
            deleted_by = proj.get('deletedBy', {})
            deleted_by_name = deleted_by.get('displayName', '') if deleted_by else ''

            writer.writerow([
                proj.get('key', ''),
                proj.get('name', ''),
                proj.get('deletedDate', ''),
                proj.get('retentionTillDate', ''),
                deleted_by_name
            ])
        return output.getvalue()

    # Table format
    lines = ["Projects in Trash:", "=" * 60, ""]

    headers = ["Key", "Name", "Deleted Date", "Restore By"]
    rows = []

    for proj in projects:
        deleted_by = proj.get('deletedBy', {})

        rows.append([
            proj.get('key', '-'),
            proj.get('name', '-')[:30],
            proj.get('deletedDate', '-')[:10],
            proj.get('retentionTillDate', '-')[:10]
        ])

    try:
        from tabulate import tabulate
        lines.append(tabulate(rows, headers=headers, tablefmt="grid"))
    except ImportError:
        lines.append("\t".join(headers))
        lines.append("-" * 60)
        for row in rows:
            lines.append("\t".join(str(x) for x in row))

    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="List and search JIRA projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all projects
  %(prog)s

  # Filter by type
  %(prog)s --type software

  # Search by name
  %(prog)s --search "mobile"

  # Include archived projects
  %(prog)s --include-archived

  # List trashed projects
  %(prog)s --trash

  # Export to CSV
  %(prog)s --output csv > projects.csv
        """
    )

    # Filter options
    parser.add_argument(
        "--search", "-s",
        help="Search projects by name or key"
    )
    parser.add_argument(
        "--type", "-t",
        choices=['software', 'business', 'service_desk'],
        help="Filter by project type"
    )
    parser.add_argument(
        "--category", "-c",
        type=int,
        help="Filter by category ID"
    )
    parser.add_argument(
        "--include-archived",
        action="store_true",
        help="Include archived projects"
    )
    parser.add_argument(
        "--trash",
        action="store_true",
        help="List projects in trash instead"
    )

    # Pagination
    parser.add_argument(
        "--start-at",
        type=int,
        default=0,
        help="Starting index for pagination (default: 0)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum results per page (default: 50)"
    )

    # Expand options
    parser.add_argument(
        "--expand", "-e",
        help="Comma-separated fields to expand (description, lead, issueTypes)"
    )

    # Output options
    parser.add_argument(
        "--output", "-o",
        choices=['table', 'json', 'csv'],
        default='table',
        help="Output format (default: table)"
    )
    parser.add_argument(
        "--profile",
        help="Configuration profile to use"
    )

    args = parser.parse_args()

    try:
        client = get_jira_client(profile=args.profile)

        # Handle trash listing
        if args.trash:
            result = list_trash_projects(
                start_at=args.start_at,
                max_results=args.max_results,
                client=client
            )
            print(format_trash_output(result, args.output))
            sys.exit(0)

        # Parse expand list
        expand_list = None
        if args.expand:
            expand_list = [x.strip() for x in args.expand.split(',')]

        result = list_projects(
            query=args.search,
            project_type=args.type,
            category_id=args.category,
            include_archived=args.include_archived,
            expand=expand_list,
            start_at=args.start_at,
            max_results=args.max_results,
            output_format=args.output,
            client=client
        )

        print(format_output(result, args.output))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    main()
