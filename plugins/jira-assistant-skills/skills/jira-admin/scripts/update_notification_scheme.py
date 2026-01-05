#!/usr/bin/env python3
"""
Update notification scheme metadata in JIRA.

Updates the name and/or description of an existing notification scheme.

Usage:
    python update_notification_scheme.py 10000 --name "Updated Scheme Name"
    python update_notification_scheme.py 10000 --description "New description"
    python update_notification_scheme.py 10000 --name "Renamed Scheme" --description "Updated description"
    python update_notification_scheme.py 10000 --name "Test" --dry-run
    python update_notification_scheme.py 10000 --profile production --name "Prod Scheme"
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


def update_notification_scheme(
    client=None,
    scheme_id: str | None = None,
    name: str | None = None,
    description: str | None = None,
    dry_run: bool = False,
    profile: str | None = None,
) -> dict[str, Any]:
    """
    Update notification scheme metadata.

    Args:
        client: JiraClient instance (optional, created if not provided)
        scheme_id: Notification scheme ID
        name: New scheme name
        description: New scheme description
        dry_run: If True, show what would change without applying
        profile: JIRA profile to use

    Returns:
        Dict with success status and change details

    Raises:
        ValidationError: If no changes provided
        NotFoundError: If scheme not found
    """
    close_client = False
    if client is None:
        client = get_jira_client(profile)
        close_client = True

    try:
        # Validate at least one change is provided
        if not name and not description:
            raise ValidationError(
                "At least one change (name or description) must be provided"
            )

        # Get current scheme to show before/after
        current = client.get_notification_scheme(
            scheme_id, expand="notificationSchemeEvents"
        )

        # Build changes dict
        changes = {}
        data = {}

        if name is not None:
            changes["name"] = {"before": current.get("name"), "after": name}
            data["name"] = name

        if description is not None:
            changes["description"] = {
                "before": current.get("description"),
                "after": description,
            }
            data["description"] = description

        # Handle dry run
        if dry_run:
            return {
                "dry_run": True,
                "scheme_id": scheme_id,
                "current": {
                    "name": current.get("name"),
                    "description": current.get("description"),
                },
                "changes": changes,
            }

        # Apply the update
        client.update_notification_scheme(scheme_id, data)

        return {"success": True, "scheme_id": scheme_id, "changes": changes}

    finally:
        if close_client and hasattr(client, "close"):
            client.close()


def format_text_output(result: dict[str, Any]) -> str:
    """
    Format result as human-readable text.

    Args:
        result: Update result object

    Returns:
        Formatted text string
    """
    output = []
    scheme_id = result.get("scheme_id", "N/A")

    if result.get("dry_run"):
        output.append(f"[DRY RUN] Would update notification scheme {scheme_id}")
        output.append("")
        output.append("Changes:")

        changes = result.get("changes", {})
        for field, values in changes.items():
            before = values.get("before", "N/A")
            after = values.get("after", "N/A")
            output.append(f"  {field.title()}:")
            output.append(f'    Before: "{before}"')
            output.append(f'    After:  "{after}"')

        output.append("")
        output.append("No changes made (dry run mode)")
    else:
        output.append(f"Notification Scheme Updated: {scheme_id}")
        output.append("-" * 40)

        changes = result.get("changes", {})
        for field, values in changes.items():
            before = values.get("before", "N/A")
            after = values.get("after", "N/A")
            output.append(f'{field.title()}: "{before}" -> "{after}"')

        output.append("")
        output.append(f"Success! Notification scheme {scheme_id} updated.")

    return "\n".join(output)


def format_json_output(result: dict[str, Any]) -> str:
    """
    Format result as JSON.

    Args:
        result: Update result object

    Returns:
        JSON string
    """
    return json.dumps(result, indent=2)


def main(argv: list[str] | None = None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Update notification scheme metadata in JIRA",
        epilog="""
Examples:
    python update_notification_scheme.py 10000 --name "Updated Scheme Name"
    python update_notification_scheme.py 10000 --description "New description"
    python update_notification_scheme.py 10000 --name "Renamed Scheme" --description "Updated description"
    python update_notification_scheme.py 10000 --name "Test" --dry-run
        """,
    )
    parser.add_argument("scheme_id", help="Notification scheme ID")
    parser.add_argument("--name", "-n", help="New scheme name")
    parser.add_argument("--description", "-d", help="New scheme description")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would change without applying"
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", "-p", help="JIRA profile to use")

    args = parser.parse_args(argv)

    if not args.name and not args.description:
        parser.error("At least one of --name or --description must be provided")

    try:
        result = update_notification_scheme(
            scheme_id=args.scheme_id,
            name=args.name,
            description=args.description,
            dry_run=args.dry_run,
            profile=args.profile,
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
