#!/usr/bin/env python3
"""
Remove a field from a JIRA screen.

Removes a field from a specific tab or searches all tabs.
"""

import argparse
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    NotFoundError,
    format_json,
    get_jira_client,
    print_error,
    print_success,
    print_warning,
)

# Fields that are typically required and should not be removed without warning
REQUIRED_FIELDS = {"summary", "issuetype", "project"}


def is_required_field(field_id: str) -> bool:
    """
    Check if a field is typically required.

    Args:
        field_id: Field ID

    Returns:
        True if field is typically required
    """
    return field_id.lower() in REQUIRED_FIELDS


def remove_field_from_screen(
    screen_id: int,
    field_id: str,
    tab_id: int | None = None,
    client=None,
    dry_run: bool = False,
    force: bool = False,
) -> bool | dict[str, Any]:
    """
    Remove a field from a screen.

    Args:
        screen_id: Screen ID
        field_id: Field ID to remove
        tab_id: Tab ID (if None, searches all tabs)
        client: JiraClient instance
        dry_run: If True, validate but don't make changes
        force: Skip confirmation for required fields

    Returns:
        True on success, or dict with dry-run status
    """
    if client is None:
        from jira_assistant_skills_lib import get_jira_client

        client = get_jira_client()

    # Check if it's a required field
    if is_required_field(field_id) and not force:
        print_warning(
            f"'{field_id}' is typically a required field. Use --force to remove."
        )

    if tab_id is not None:
        # Remove from specific tab
        if dry_run:
            # Check if field is actually on the tab
            fields = client.get_screen_tab_fields(screen_id, tab_id)
            field_ids = [f.get("id") for f in fields]

            if field_id in field_ids:
                return {
                    "dry_run": True,
                    "action": "remove_field",
                    "screen_id": screen_id,
                    "tab_id": tab_id,
                    "field_id": field_id,
                    "status": "would_succeed",
                }
            else:
                return {
                    "dry_run": True,
                    "action": "remove_field",
                    "screen_id": screen_id,
                    "tab_id": tab_id,
                    "field_id": field_id,
                    "status": "field_not_on_tab",
                }

        client.remove_field_from_screen_tab(screen_id, tab_id, field_id)
        return True

    # Search all tabs for the field
    tabs = client.get_screen_tabs(screen_id)
    found_tab_id = None

    for tab in tabs:
        fields = client.get_screen_tab_fields(screen_id, tab["id"])
        field_ids = [f.get("id") for f in fields]

        if field_id in field_ids:
            found_tab_id = tab["id"]
            break

    if found_tab_id is None:
        raise NotFoundError(f"Field '{field_id}' not found on screen {screen_id}")

    if dry_run:
        return {
            "dry_run": True,
            "action": "remove_field",
            "screen_id": screen_id,
            "tab_id": found_tab_id,
            "field_id": field_id,
            "status": "would_succeed",
            "found_on_tab": found_tab_id,
        }

    client.remove_field_from_screen_tab(screen_id, found_tab_id, field_id)
    return True


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Remove a field from a JIRA screen",
        epilog="""
Examples:
    # Remove field (searches all tabs)
    python remove_field_from_screen.py 1 customfield_10016

    # Remove field from specific tab
    python remove_field_from_screen.py 1 customfield_10016 --tab 10001

    # Dry run to validate
    python remove_field_from_screen.py 1 customfield_10016 --dry-run

    # Force removal of required field
    python remove_field_from_screen.py 1 summary --force

    # JSON output
    python remove_field_from_screen.py 1 customfield_10016 --output json
""",
    )

    parser.add_argument("screen_id", type=int, help="Screen ID")
    parser.add_argument("field_id", help="Field ID to remove")
    parser.add_argument(
        "--tab",
        "-t",
        dest="tab_id",
        type=int,
        help="Tab ID to remove field from (if not specified, searches all tabs)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate without making changes"
    )
    parser.add_argument(
        "--force", "-f", action="store_true", help="Force removal of required fields"
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
        client = get_jira_client()

        result = remove_field_from_screen(
            screen_id=args.screen_id,
            field_id=args.field_id,
            tab_id=args.tab_id,
            client=client,
            dry_run=args.dry_run,
            force=args.force,
        )

        if args.output == "json":
            if isinstance(result, bool):
                print(format_json({"success": result, "field_id": args.field_id}))
            else:
                print(format_json(result))
        else:
            if args.dry_run:
                status = result.get("status", "unknown")
                if status == "would_succeed":
                    tab_info = (
                        f" from tab {result.get('found_on_tab', result.get('tab_id'))}"
                    )
                    print(f"[DRY RUN] Would remove field '{args.field_id}'{tab_info}")
                else:
                    print("[DRY RUN] Field not found on screen")
            else:
                print_success(
                    f"Removed field '{args.field_id}' from screen {args.screen_id}"
                )

    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
