#!/usr/bin/env python3
"""
Get backlog issues for a JIRA board.

Usage:
    python get_backlog.py --board 123
    python get_backlog.py --project DEMO
    python get_backlog.py --project DEMO --filter "priority=High"
    python get_backlog.py --board 123 --group-by epic
    python get_backlog.py --project DEMO --max-results 50
"""

import argparse
import json
import sys

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_agile_fields,
    get_jira_client,
    print_error,
    print_success,
)


def get_board_for_project(
    project_key: str,
    profile: str | None = None,
    client=None,
) -> int:
    """
    Get the board ID for a project.

    Args:
        project_key: Project key (e.g., DEMO)
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Board ID

    Raises:
        ValidationError: If no boards found for project
    """
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        result = client.get_all_boards(project_key=project_key, max_results=10)
        boards = result.get("values", [])

        if not boards:
            raise ValidationError(f"No boards found for project {project_key}")

        # Prefer scrum boards over kanban for backlog
        scrum_boards = [b for b in boards if b.get("type") == "scrum"]
        if scrum_boards:
            return scrum_boards[0]["id"]

        # Fall back to first board
        return boards[0]["id"]

    finally:
        if should_close:
            client.close()


def get_backlog(
    board_id: int | None = None,
    project_key: str | None = None,
    jql_filter: str | None = None,
    max_results: int = 100,
    group_by_epic: bool = False,
    profile: str | None = None,
    client=None,
) -> dict:
    """
    Get backlog issues for a board.

    Args:
        board_id: Board ID (required if project_key not provided)
        project_key: Project key to look up board (alternative to board_id)
        jql_filter: Additional JQL filter
        max_results: Maximum issues to return
        group_by_epic: Group results by epic
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Backlog data with issues and optional grouping
    """
    if not board_id and not project_key:
        raise ValidationError("Either board ID or project key is required")

    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        # Resolve board_id from project_key if not provided
        if not board_id and project_key:
            board_id = get_board_for_project(project_key, profile, client)

        # Get Agile field IDs from configuration
        agile_fields = get_agile_fields(profile)
        epic_link_field = agile_fields["epic_link"]
        agile_fields["story_points"]

        result = client.get_board_backlog(
            board_id, jql=jql_filter, max_results=max_results
        )

        # Store field IDs in result for use in main()
        result["_agile_fields"] = agile_fields

        if group_by_epic:
            by_epic = {}
            no_epic = []
            for issue in result.get("issues", []):
                epic_key = issue["fields"].get(epic_link_field)
                if epic_key:
                    if epic_key not in by_epic:
                        by_epic[epic_key] = []
                    by_epic[epic_key].append(issue)
                else:
                    no_epic.append(issue)
            result["by_epic"] = by_epic
            result["no_epic"] = no_epic

        return result

    finally:
        if should_close:
            client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Get backlog issues for a JIRA board",
        epilog="Example: python get_backlog.py --project DEMO",
    )

    parser.add_argument("--board", "-b", type=int, help="Board ID")
    parser.add_argument("--project", "-p", help="Project key (alternative to --board)")
    parser.add_argument("--filter", "-f", help="JQL filter")
    parser.add_argument(
        "--max-results",
        "-m",
        type=int,
        default=100,
        help="Maximum results (default: 100)",
    )
    parser.add_argument("--group-by", choices=["epic"], help="Group results")
    parser.add_argument("--profile", help="JIRA profile to use")
    parser.add_argument(
        "--output", "-o", choices=["text", "json"], default="text", help="Output format"
    )

    args = parser.parse_args(argv)

    # Validate that at least one of --board or --project is provided
    if not args.board and not args.project:
        parser.error("Either --board or --project is required")

    try:
        result = get_backlog(
            board_id=args.board,
            project_key=args.project,
            jql_filter=args.filter,
            max_results=args.max_results,
            group_by_epic=(args.group_by == "epic"),
            profile=args.profile,
        )

        if args.output == "json":
            # Remove internal field IDs before JSON output
            output = {k: v for k, v in result.items() if not k.startswith("_")}
            print(json.dumps(output, indent=2))
        else:
            issues = result.get("issues", [])
            story_points_field = result.get("_agile_fields", {}).get(
                "story_points", "customfield_10016"
            )
            print_success(
                f"Backlog: {len(issues)}/{result.get('total', len(issues))} issues"
            )

            if args.group_by == "epic" and "by_epic" in result:
                for epic_key, epic_issues in result["by_epic"].items():
                    print(f"\n[{epic_key}] ({len(epic_issues)} issues)")
                    for issue in epic_issues:
                        points = issue["fields"].get(story_points_field, "")
                        pts_str = f" ({points} pts)" if points else ""
                        print(
                            f"  {issue['key']} - {issue['fields']['summary']}{pts_str}"
                        )
                if result.get("no_epic"):
                    print(f"\n[No Epic] ({len(result['no_epic'])} issues)")
                    for issue in result["no_epic"]:
                        print(f"  {issue['key']} - {issue['fields']['summary']}")
            else:
                for issue in issues:
                    status = issue["fields"]["status"]["name"]
                    summary = issue["fields"]["summary"]
                    points = issue["fields"].get(story_points_field, "")
                    pts_str = f" ({points} pts)" if points else ""
                    print(f"  [{status}] {issue['key']} - {summary}{pts_str}")

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
