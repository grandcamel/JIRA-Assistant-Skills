#!/usr/bin/env python3
"""
List sprints for a board or project.

Usage:
    python list_sprints.py --board 123
    python list_sprints.py --project DEMO
    python list_sprints.py --project DEMO --state active
    python list_sprints.py --board 123 --state closed --output json
"""

import argparse
import json
import sys
from datetime import datetime

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
)
from jira_assistant_skills_lib.validators import validate_project_key


def get_board_for_project(project_key: str, client=None) -> dict | None:
    """
    Find the first Scrum board for a project.

    Args:
        project_key: Project key (e.g., DEMO)
        client: JiraClient instance (for testing)

    Returns:
        Board data or None if no board found

    Raises:
        JiraError: If API call fails
    """
    if not client:
        client = get_jira_client()
        should_close = True
    else:
        should_close = False

    try:
        result = client.get_all_boards(project_key=project_key)
        boards = result.get("values", [])
        # Prefer Scrum boards for sprint management
        scrum_boards = [b for b in boards if b.get("type") == "scrum"]
        if scrum_boards:
            return scrum_boards[0]
        # Fall back to any board
        if boards:
            return boards[0]
        return None
    finally:
        if should_close:
            client.close()


def list_sprints(
    board_id: int | None = None,
    project_key: str | None = None,
    state: str | None = None,
    max_results: int = 50,
    client=None,
) -> dict:
    """
    List sprints for a board or project.

    Args:
        board_id: Board ID to query
        project_key: Project key (will find board automatically)
        state: Filter by state (active, closed, future)
        max_results: Maximum sprints to return
        client: JiraClient instance (for testing)

    Returns:
        Dict with 'sprints' list and 'board' info

    Raises:
        ValidationError: If neither board_id nor project_key provided
        JiraError: If API call fails
    """
    if not board_id and not project_key:
        raise ValidationError("Either --board or --project is required")

    if not client:
        client = get_jira_client()
        should_close = True
    else:
        should_close = False

    try:
        board = None
        actual_board_id = board_id

        # If project key provided, find the board
        if project_key and not board_id:
            validate_project_key(project_key)
            board = get_board_for_project(project_key, client)
            if not board:
                raise ValidationError(
                    f"No board found for project {project_key}. "
                    "Ensure the project has a Scrum or Kanban board configured."
                )
            actual_board_id = board["id"]

        # Get sprints for the board
        result = client.get_board_sprints(
            actual_board_id, state=state, max_results=max_results
        )
        sprints = result.get("values", [])

        return {
            "board": board or {"id": actual_board_id},
            "sprints": sprints,
            "state_filter": state,
            "total": len(sprints),
        }
    finally:
        if should_close:
            client.close()


def format_sprint_list(data: dict, output_format: str = "text") -> str:
    """
    Format sprint list for output.

    Args:
        data: Sprint list data from list_sprints()
        output_format: Output format ('text' or 'json')

    Returns:
        Formatted string
    """
    if output_format == "json":
        return json.dumps(data, indent=2)

    sprints = data.get("sprints", [])
    board = data.get("board", {})
    state_filter = data.get("state_filter")

    lines = []

    # Header
    board_name = board.get("name", f"Board {board.get('id', 'Unknown')}")
    if state_filter:
        lines.append(f"Sprints for {board_name} (state: {state_filter}):")
    else:
        lines.append(f"Sprints for {board_name}:")
    lines.append("")

    if not sprints:
        lines.append("  No sprints found.")
        return "\n".join(lines)

    # Sprint table
    lines.append(f"{'ID':<8} {'State':<10} {'Name':<30} {'Dates'}")
    lines.append("-" * 80)

    for sprint in sprints:
        sprint_id = sprint.get("id", "")
        state = sprint.get("state", "unknown")
        name = sprint.get("name", "Unnamed")
        if len(name) > 28:
            name = name[:25] + "..."

        # Format dates
        start_date = sprint.get("startDate", "")
        end_date = sprint.get("endDate", "")
        dates = ""
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                dates = f"{start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')}"
            except (ValueError, TypeError):
                dates = f"{start_date[:10]} → {end_date[:10]}"

        lines.append(f"{sprint_id:<8} {state:<10} {name:<30} {dates}")

    lines.append("")
    lines.append(f"Total: {len(sprints)} sprint(s)")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="List sprints for a board or project",
        epilog="""Examples:
    jira agile sprint list --project DEMO
    jira agile sprint list --board 123
    jira agile sprint list --project DEMO --state active
    jira agile sprint list --project DEMO --state closed --output json
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--board", "-b", type=int, help="Board ID")
    parser.add_argument(
        "--project", "-p", help="Project key (will find board automatically)"
    )
    parser.add_argument(
        "--state",
        "-s",
        choices=["active", "closed", "future"],
        help="Filter by sprint state",
    )
    parser.add_argument(
        "--max-results", "-m", type=int, default=50, help="Maximum sprints to return"
    )
    parser.add_argument(
        "--output", "-o", choices=["text", "json"], default="text", help="Output format"
    )

    args = parser.parse_args(argv)

    if not args.board and not args.project:
        parser.error("Either --board or --project is required")

    try:
        result = list_sprints(
            board_id=args.board,
            project_key=args.project,
            state=args.state,
            max_results=args.max_results,
        )

        output = format_sprint_list(result, args.output)
        print(output)

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
