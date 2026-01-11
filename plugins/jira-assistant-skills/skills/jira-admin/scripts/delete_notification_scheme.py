#!/usr/bin/env python3
"""
Delete a notification scheme from JIRA.

Deletes an existing notification scheme after validation.

Usage:
    python delete_notification_scheme.py 10000
    python delete_notification_scheme.py 10000 --force
    python delete_notification_scheme.py 10000 --dry-run
    python delete_notification_scheme.py 10000
"""

import argparse
import json
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
)


def delete_notification_scheme(
    client=None,
    scheme_id: str | None = None,
    force: bool = False,
    confirmed: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Delete a notification scheme.

    Args:
        client: JiraClient instance (optional, created if not provided)
        scheme_id: Notification scheme ID to delete
        force: If True, bypass confirmation prompt
        confirmed: If False and not force, raise error requiring confirmation
        dry_run: If True, show what would be deleted without deleting

    Returns:
        Dict with success status and deleted scheme details

    Raises:
        ValidationError: If scheme is in use by projects
        NotFoundError: If scheme not found
    """
    close_client = False
    if client is None:
        client = get_jira_client()
        close_client = True

    try:
        # Get scheme details first
        scheme = client.get_notification_scheme(
            scheme_id, expand="notificationSchemeEvents"
        )
        scheme_name = scheme.get("name", "Unknown")

        # Check if scheme is in use by projects
        project_mappings = client.get_notification_scheme_projects(
            notification_scheme_id=[scheme_id]
        )
        projects_using = [
            p
            for p in project_mappings.get("values", [])
            if str(p.get("notificationSchemeId")) == str(scheme_id)
        ]

        if projects_using:
            raise ValidationError(
                f"Cannot delete notification scheme '{scheme_name}' (ID: {scheme_id}). "
                f"It is in use by {len(projects_using)} project(s). "
                f"Reassign those projects to a different scheme first."
            )

        # Handle dry run
        if dry_run:
            return {
                "dry_run": True,
                "scheme_id": scheme_id,
                "scheme_name": scheme_name,
                "would_delete": True,
            }

        # Require confirmation unless force
        if not force and not confirmed:
            raise ValidationError(
                "Deletion requires confirmation. Use --force to bypass, or confirm interactively."
            )

        # Delete the scheme
        client.delete_notification_scheme(scheme_id)

        return {"success": True, "scheme_id": scheme_id, "scheme_name": scheme_name}

    finally:
        if close_client and hasattr(client, "close"):
            client.close()


def format_text_output(result: dict[str, Any]) -> str:
    """
    Format result as human-readable text.

    Args:
        result: Delete result object

    Returns:
        Formatted text string
    """
    output = []
    scheme_id = result.get("scheme_id", "N/A")
    scheme_name = result.get("scheme_name", "N/A")

    if result.get("dry_run"):
        output.append("[DRY RUN] Would delete notification scheme")
        output.append("")
        output.append(f"ID:   {scheme_id}")
        output.append(f"Name: {scheme_name}")
        output.append("")
        output.append("No changes made (dry run mode)")
    else:
        output.append("Notification Scheme Deleted")
        output.append("-" * 40)
        output.append(f"ID:   {scheme_id}")
        output.append(f"Name: {scheme_name}")
        output.append("")
        output.append(
            f'Success! Notification scheme "{scheme_name}" (ID: {scheme_id}) deleted.'
        )

    return "\n".join(output)


def format_json_output(result: dict[str, Any]) -> str:
    """
    Format result as JSON.

    Args:
        result: Delete result object

    Returns:
        JSON string
    """
    return json.dumps(result, indent=2)


def main(argv: list[str] | None = None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Delete a notification scheme from JIRA",
        epilog="""
Examples:
    python delete_notification_scheme.py 10000
    python delete_notification_scheme.py 10000 --force
    python delete_notification_scheme.py 10000 --dry-run
        """,
    )
    parser.add_argument("scheme_id", help="Notification scheme ID")
    parser.add_argument(
        "--force", "-f", action="store_true", help="Force deletion without confirmation"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        # Interactive confirmation if not forced
        confirmed = args.force
        if not args.force and not args.dry_run:
            print(f"This will permanently delete notification scheme {args.scheme_id}.")
            response = input("Are you sure? (yes/no): ")
            confirmed = response.lower() in ("yes", "y")

        result = delete_notification_scheme(
            scheme_id=args.scheme_id,
            force=args.force,
            confirmed=confirmed,
            dry_run=args.dry_run,
        )

        if args.output == "json":
            print(format_json_output(result))
        else:
            print(format_text_output(result))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
