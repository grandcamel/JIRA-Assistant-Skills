#!/usr/bin/env python3
"""
Manage Sprint lifecycle in JIRA - start, close, update sprints.

Usage:
    python manage_sprint.py --sprint 456 --start
    python manage_sprint.py --sprint 456 --close
    python manage_sprint.py --sprint 456 --close --move-incomplete-to 457
    python manage_sprint.py --sprint 456 --extend-by 3d
    python manage_sprint.py --board 123 --get-active
"""

import argparse
import json
import sys

# Add shared lib to path
# Imports from shared library
from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    parse_date_to_iso,
    print_error,
    print_success,
    print_warning,
)


def _parse_date_safe(date_str: str) -> str:
    """Parse date string into ISO format, converting ValueError to ValidationError."""
    if not date_str:
        return None
    try:
        return parse_date_to_iso(date_str)
    except ValueError as e:
        raise ValidationError(str(e))


def start_sprint(
    sprint_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
    profile: str | None = None,
    client=None,
) -> dict:
    """
    Start a sprint (transition from 'future' to 'active').

    Args:
        sprint_id: Sprint ID to start
        start_date: Optional start date (defaults to now)
        end_date: Optional end date (required if not already set)
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Updated sprint data

    Raises:
        JiraError: If API call fails
    """
    if not sprint_id:
        raise ValidationError("Sprint ID is required")

    # Initialize client
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        # Build update data
        update_data = {"state": "active"}

        if start_date:
            update_data["start_date"] = _parse_date_safe(start_date)

        if end_date:
            update_data["end_date"] = _parse_date_safe(end_date)

        # Update sprint via Agile API
        result = client.update_sprint(sprint_id, **update_data)
        return result

    finally:
        if should_close:
            client.close()


def close_sprint(
    sprint_id: int,
    move_incomplete_to: int | None = None,
    profile: str | None = None,
    client=None,
) -> dict:
    """
    Close a sprint (transition from 'active' to 'closed').

    Args:
        sprint_id: Sprint ID to close
        move_incomplete_to: Sprint ID to move incomplete issues to
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Updated sprint data with optional moved_issues count

    Raises:
        JiraError: If API call fails
    """
    if not sprint_id:
        raise ValidationError("Sprint ID is required")

    # Initialize client
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        result = {}

        # If moving incomplete issues, do that first
        if move_incomplete_to:
            move_result = client.move_issues_to_sprint(sprint_id, move_incomplete_to)
            result["moved_issues"] = move_result.get("movedIssues", 0)

        # Close the sprint
        update_data = {"state": "closed"}
        sprint_result = client.update_sprint(sprint_id, **update_data)

        # Merge results
        result.update(sprint_result)
        return result

    finally:
        if should_close:
            client.close()


def update_sprint(
    sprint_id: int,
    name: str | None = None,
    goal: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    profile: str | None = None,
    client=None,
) -> dict:
    """
    Update sprint metadata.

    Args:
        sprint_id: Sprint ID to update
        name: New sprint name
        goal: New sprint goal
        start_date: New start date
        end_date: New end date
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Updated sprint data

    Raises:
        JiraError: If API call fails
    """
    if not sprint_id:
        raise ValidationError("Sprint ID is required")

    # Initialize client
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        # Build update data
        update_data = {}

        if name:
            update_data["name"] = name

        if goal:
            update_data["goal"] = goal

        if start_date:
            update_data["start_date"] = _parse_date_safe(start_date)

        if end_date:
            update_data["end_date"] = _parse_date_safe(end_date)

        if not update_data:
            raise ValidationError("At least one field to update is required")

        # Update sprint via Agile API
        result = client.update_sprint(sprint_id, **update_data)
        return result

    finally:
        if should_close:
            client.close()


def get_active_sprint(board_id: int, profile: str | None = None, client=None) -> dict:
    """
    Get the currently active sprint for a board.

    Args:
        board_id: Board ID to query
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Active sprint data or None if no active sprint

    Raises:
        JiraError: If API call fails
    """
    if not board_id:
        raise ValidationError("Board ID is required")

    # Initialize client
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        # Get sprints for board, filtered to active state
        result = client.get_board_sprints(board_id, state="active")

        sprints = result.get("values", [])
        if sprints:
            return sprints[0]  # Return first active sprint
        return None

    finally:
        if should_close:
            client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Manage Sprint lifecycle in JIRA",
        epilog="Example: python manage_sprint.py --sprint 456 --start",
    )

    # Target selection
    parser.add_argument("--sprint", "-s", type=int, help="Sprint ID to manage")
    parser.add_argument("--board", "-b", type=int, help="Board ID (for --get-active)")

    # Actions
    parser.add_argument("--start", action="store_true", help="Start the sprint")
    parser.add_argument("--close", action="store_true", help="Close the sprint")
    parser.add_argument(
        "--get-active", action="store_true", help="Get active sprint for board"
    )

    # Options for actions
    parser.add_argument(
        "--move-incomplete-to",
        type=int,
        help="Sprint ID to move incomplete issues to (with --close)",
    )
    parser.add_argument("--name", "-n", help="New sprint name")
    parser.add_argument("--goal", "-g", help="New sprint goal")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")

    parser.add_argument("--profile", help="JIRA profile to use")
    parser.add_argument(
        "--output", "-o", choices=["text", "json"], default="text", help="Output format"
    )

    args = parser.parse_args(argv)

    try:
        result = None

        if args.get_active:
            if not args.board:
                parser.error("--board is required with --get-active")
            result = get_active_sprint(board_id=args.board, profile=args.profile)

            if result:
                if args.output == "json":
                    print(json.dumps(result, indent=2))
                else:
                    print_success(
                        f"Active sprint: {result['name']} (ID: {result['id']})"
                    )
                    print(f"State: {result['state']}")
                    if result.get("goal"):
                        print(f"Goal: {result['goal']}")
            else:
                print_warning("No active sprint found for this board")

        elif args.start:
            if not args.sprint:
                parser.error("--sprint is required with --start")
            result = start_sprint(
                sprint_id=args.sprint,
                start_date=args.start_date,
                end_date=args.end_date,
                profile=args.profile,
            )
            if args.output == "json":
                print(json.dumps(result, indent=2))
            else:
                print_success(f"Started sprint: {result['name']}")

        elif args.close:
            if not args.sprint:
                parser.error("--sprint is required with --close")
            result = close_sprint(
                sprint_id=args.sprint,
                move_incomplete_to=args.move_incomplete_to,
                profile=args.profile,
            )
            if args.output == "json":
                print(json.dumps(result, indent=2))
            else:
                print_success(f"Closed sprint: {result['name']}")
                if "moved_issues" in result:
                    print(
                        f"Moved {result['moved_issues']} incomplete issues to next sprint"
                    )

        elif args.name or args.goal or args.start_date or args.end_date:
            if not args.sprint:
                parser.error("--sprint is required for updates")
            result = update_sprint(
                sprint_id=args.sprint,
                name=args.name,
                goal=args.goal,
                start_date=args.start_date,
                end_date=args.end_date,
                profile=args.profile,
            )
            if args.output == "json":
                print(json.dumps(result, indent=2))
            else:
                print_success(f"Updated sprint: {result['name']}")

        else:
            parser.error(
                "No action specified. Use --start, --close, --get-active, or update options."
            )

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except ValidationError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
