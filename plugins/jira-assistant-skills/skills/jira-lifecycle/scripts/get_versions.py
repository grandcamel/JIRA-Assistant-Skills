#!/usr/bin/env python3
"""
Get project versions in JIRA.

Usage:
    python get_versions.py PROJ
    python get_versions.py PROJ --released
    python get_versions.py PROJ --unreleased
    python get_versions.py --id 10000 --counts
"""

import argparse
import json
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    format_table,
    get_jira_client,
    print_error,
)


def get_versions(project: str) -> list[dict[str, Any]]:
    """
    Get all versions for a project.

    Args:
        project: Project key (e.g., PROJ)

    Returns:
        List of version data
    """
    client = get_jira_client()
    result = client.get_versions(project)
    client.close()

    return result


def get_version_by_id(version_id: str) -> dict[str, Any]:
    """
    Get a specific version by ID.

    Args:
        version_id: Version ID

    Returns:
        Version data
    """
    client = get_jira_client()
    result = client.get_version(version_id)
    client.close()

    return result


def filter_versions(
    versions: list[dict[str, Any]],
    released: bool | None = None,
    archived: bool | None = None,
) -> list[dict[str, Any]]:
    """
    Filter versions by status.

    Args:
        versions: List of versions
        released: Filter by released status (True/False/None for all)
        archived: Filter by archived status (True/False/None for all)

    Returns:
        Filtered list of versions
    """
    filtered = versions

    if released is not None:
        filtered = [v for v in filtered if v.get("released") == released]

    if archived is not None:
        filtered = [v for v in filtered if v.get("archived") == archived]

    return filtered


def get_version_issue_counts(version_id: str) -> dict[str, Any]:
    """
    Get issue counts for a version.

    Args:
        version_id: Version ID

    Returns:
        Issue counts (fixed, affected, etc.)
    """
    client = get_jira_client()
    result = client.get_version_issue_counts(version_id)
    client.close()

    return result


def get_version_unresolved_count(version_id: str) -> dict[str, Any]:
    """
    Get unresolved issue count for a version.

    Args:
        version_id: Version ID

    Returns:
        Unresolved issue count
    """
    client = get_jira_client()
    result = client.get_version_unresolved_count(version_id)
    client.close()

    return result


def display_versions_table(versions: list[dict[str, Any]]) -> None:
    """
    Display versions in table format.

    Args:
        versions: List of versions
    """
    if not versions:
        print("No versions found.")
        return

    # Prepare table data
    table_data = []
    for version in versions:
        table_data.append(
            {
                "id": version.get("id", ""),
                "name": version.get("name", ""),
                "description": version.get("description", "")[:40] or "",
                "released": "Yes" if version.get("released") else "No",
                "archived": "Yes" if version.get("archived") else "No",
                "release_date": version.get("releaseDate", ""),
            }
        )

    print(
        format_table(
            table_data,
            columns=[
                "id",
                "name",
                "description",
                "released",
                "archived",
                "release_date",
            ],
            headers=[
                "ID",
                "Name",
                "Description",
                "Released",
                "Archived",
                "Release Date",
            ],
        )
    )


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Get project versions in JIRA",
        epilog="""
Examples:
  %(prog)s PROJ
  %(prog)s PROJ --released
  %(prog)s PROJ --unreleased --output json
  %(prog)s --id 10000
  %(prog)s --id 10000 --counts
        """,
    )

    parser.add_argument("project", nargs="?", help="Project key (e.g., PROJ)")
    parser.add_argument("--id", help="Get specific version by ID")
    parser.add_argument(
        "--released", action="store_true", help="Filter for released versions only"
    )
    parser.add_argument(
        "--unreleased", action="store_true", help="Filter for unreleased versions only"
    )
    parser.add_argument(
        "--archived", action="store_true", help="Filter for archived versions only"
    )
    parser.add_argument(
        "--counts",
        action="store_true",
        help="Show issue counts for the version (requires --id)",
    )
    parser.add_argument(
        "--output",
        "-O",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )

    args = parser.parse_args(argv)

    # Validate arguments
    if args.id:
        # Get specific version
        if args.project:
            print_error("Error: Cannot specify both project and --id")
            sys.exit(1)
    else:
        # Get project versions
        if not args.project:
            print_error("Error: Must specify either project or --id")
            sys.exit(1)

    if args.counts and not args.id:
        print_error("Error: --counts requires --id")
        sys.exit(1)

    if args.released and args.unreleased:
        print_error("Error: Cannot specify both --released and --unreleased")
        sys.exit(1)

    try:
        if args.id:
            # Get specific version
            version = get_version_by_id(args.id)

            if args.counts:
                # Get issue counts
                counts = get_version_issue_counts(args.id)
                unresolved = get_version_unresolved_count(args.id)

                print(f"Version: {version['name']} (ID: {version['id']})")
                print("\nIssue Counts:")
                print(f"  Fixed: {counts['issuesFixedCount']}")
                print(f"  Affected: {counts['issuesAffectedCount']}")
                print(f"  Unresolved: {unresolved['issuesUnresolvedCount']}")
                print(f"  Total: {unresolved['issuesCount']}")
            else:
                # Show version details
                if args.output == "json":
                    print(json.dumps(version, indent=2))
                else:
                    print(f"Version: {version['name']} (ID: {version['id']})")
                    if version.get("description"):
                        print(f"Description: {version['description']}")
                    if version.get("startDate"):
                        print(f"Start Date: {version['startDate']}")
                    if version.get("releaseDate"):
                        print(f"Release Date: {version['releaseDate']}")
                    print(f"Released: {'Yes' if version.get('released') else 'No'}")
                    print(f"Archived: {'Yes' if version.get('archived') else 'No'}")
        else:
            # Get project versions
            versions = get_versions(args.project)

            # Apply filters
            if args.released:
                versions = filter_versions(versions, released=True)
            elif args.unreleased:
                versions = filter_versions(versions, released=False)

            if args.archived:
                versions = filter_versions(versions, archived=True)

            # Output
            if args.output == "json":
                print(json.dumps(versions, indent=2))
            else:
                print(f"Versions for project {args.project}:\n")
                display_versions_table(versions)
                print(f"\nTotal: {len(versions)} version(s)")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
