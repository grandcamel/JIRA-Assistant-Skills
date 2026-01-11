#!/usr/bin/env python3
"""
Delete a JIRA permission scheme.

Deletes a permission scheme that is not assigned to any projects.

Examples:
    # Delete with confirmation
    python delete_permission_scheme.py 10050 --confirm

    # Check if scheme is in use
    python delete_permission_scheme.py 10050 --check-only

    # Dry run
    python delete_permission_scheme.py 10050 --dry-run --confirm

Note: Cannot delete the default permission scheme or schemes that are
assigned to projects. Use assign_permission_scheme.py to reassign
projects first.
"""

import argparse
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    NotFoundError,
    ValidationError,
    get_jira_client,
    print_error,
)


def get_scheme_for_deletion(client, scheme_id: int) -> dict[str, Any]:
    """
    Get scheme info before deletion.

    Args:
        client: JIRA client instance
        scheme_id: Permission scheme ID

    Returns:
        Scheme object
    """
    return client.get_permission_scheme(scheme_id)


def check_scheme_in_use(client, scheme_id: int) -> tuple[bool, list[dict[str, Any]]]:
    """
    Check if a scheme is in use by any projects.

    Args:
        client: JIRA client instance
        scheme_id: Permission scheme ID

    Returns:
        Tuple of (is_in_use, list_of_projects)
    """
    # Search for projects using this scheme
    # Note: This requires iterating through projects since there's no direct API
    # We'll use the search endpoint with permission scheme filter if available

    projects = []
    start_at = 0
    max_results = 50

    while True:
        response = client.get(
            "/rest/api/3/project/search",
            params={
                "startAt": start_at,
                "maxResults": max_results,
                "expand": "permissionScheme",
            },
            operation="search projects for permission scheme",
        )

        for project in response.get("values", []):
            # Check if this project uses the scheme
            perm_scheme = project.get("permissionScheme", {})
            if perm_scheme.get("id") == scheme_id or str(perm_scheme.get("id")) == str(
                scheme_id
            ):
                projects.append(
                    {"key": project.get("key"), "name": project.get("name")}
                )

        if response.get("isLast", True):
            break
        start_at += max_results

    return len(projects) > 0, projects


def delete_permission_scheme(
    client, scheme_id: int, confirm: bool = False, dry_run: bool = False
) -> bool:
    """
    Delete a permission scheme.

    Args:
        client: JIRA client instance
        scheme_id: Permission scheme ID to delete
        confirm: Must be True to actually delete
        dry_run: If True, don't actually delete

    Returns:
        True if deleted (or would be deleted in dry-run)

    Raises:
        ValidationError: If confirmation not provided or scheme in use
    """
    if not confirm:
        raise ValidationError(
            "Deletion requires --confirm flag. "
            "Use --check-only to see if scheme is in use first."
        )

    if dry_run:
        return True

    client.delete_permission_scheme(scheme_id)
    return True


def format_check_result(
    scheme: dict[str, Any], in_use: bool, projects: list[dict[str, Any]]
) -> str:
    """Format usage check result."""
    lines = []
    lines.append(
        f"Permission Scheme: {scheme.get('name', 'Unknown')} (ID: {scheme.get('id')})"
    )

    if in_use:
        lines.append(f"\nScheme is IN USE by {len(projects)} project(s):")
        for proj in projects:
            lines.append(f"  - {proj['key']}: {proj['name']}")
        lines.append("\nCannot delete - reassign projects first.")
    else:
        lines.append("\nScheme is NOT in use by any projects.")
        lines.append("Safe to delete with --confirm flag.")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Delete a JIRA permission scheme",
        epilog="""
Examples:
  %(prog)s 10050 --confirm
  %(prog)s 10050 --check-only
  %(prog)s 10050 --dry-run --confirm
""",
    )
    parser.add_argument("scheme_id", type=int, help="Permission scheme ID to delete")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm deletion (required for actual delete)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check if scheme is in use, do not delete",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview deletion without making changes"
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )

    args = parser.parse_args(argv)

    try:
        client = get_jira_client()

        # Get scheme info
        scheme = get_scheme_for_deletion(client, args.scheme_id)

        # Check usage
        in_use, projects = check_scheme_in_use(client, args.scheme_id)

        if args.check_only:
            output = format_check_result(scheme, in_use, projects)
            print(output)
            return

        if in_use and not args.dry_run:
            print(format_check_result(scheme, in_use, projects))
            sys.exit(1)

        if args.dry_run:
            print("=== DRY RUN ===")
            print(f"Would delete: {scheme.get('name')} (ID: {args.scheme_id})")
            if in_use:
                print(f"WARNING: Scheme is used by {len(projects)} project(s)")
            print()
            print("No changes made (dry-run mode)")
            return

        delete_permission_scheme(client, scheme_id=args.scheme_id, confirm=args.confirm)

        print(f"Deleted permission scheme: {scheme.get('name')} (ID: {args.scheme_id})")

    except (JiraError, ValidationError, NotFoundError) as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)


if __name__ == "__main__":
    main()
