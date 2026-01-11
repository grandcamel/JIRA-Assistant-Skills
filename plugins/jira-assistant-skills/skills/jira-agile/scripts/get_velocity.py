#!/usr/bin/env python3
"""
Calculate velocity metrics from completed sprints.

Usage:
    python get_velocity.py --project DEMO
    python get_velocity.py --project DEMO --sprints 5
    python get_velocity.py --board 123 --sprints 3
    python get_velocity.py --project DEMO --output json
"""

import argparse
import json
import sys
from statistics import mean, stdev

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_agile_fields,
    get_jira_client,
    print_error,
    print_success,
)
from jira_assistant_skills_lib.validators import validate_project_key


def get_board_for_project(
    project_key: str, client=None
) -> dict | None:
    """Find the first Scrum board for a project."""
    if not client:
        client = get_jira_client()
        should_close = True
    else:
        should_close = False

    try:
        result = client.get_all_boards(project_key=project_key)
        boards = result.get("values", [])
        scrum_boards = [b for b in boards if b.get("type") == "scrum"]
        if scrum_boards:
            return scrum_boards[0]
        if boards:
            return boards[0]
        return None
    finally:
        if should_close:
            client.close()


def get_velocity(
    board_id: int | None = None,
    project_key: str | None = None,
    num_sprints: int = 3,
    client=None,
) -> dict:
    """
    Calculate velocity from completed sprints.

    Args:
        board_id: Board ID to query
        project_key: Project key (will find board automatically)
        num_sprints: Number of closed sprints to analyze
        client: JiraClient instance (for testing)

    Returns:
        Dict with velocity metrics and sprint details

    Raises:
        ValidationError: If inputs invalid or no closed sprints
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
        actual_board_id = board_id
        board_name = None

        # If project key provided, find the board
        if project_key and not board_id:
            validate_project_key(project_key)
            board = get_board_for_project(project_key, client)
            if not board:
                raise ValidationError(
                    f"No board found for project {project_key}. "
                    "Ensure the project has a Scrum board configured."
                )
            actual_board_id = board["id"]
            board_name = board.get("name")

        # Get closed sprints
        result = client.get_board_sprints(
            actual_board_id, state="closed", max_results=num_sprints
        )
        sprints = result.get("values", [])

        if not sprints:
            raise ValidationError(
                "No closed sprints found. Velocity requires completed sprints. "
                "Close a sprint to start tracking velocity."
            )

        # Sort by end date descending (most recent first)
        sprints = sorted(
            sprints,
            key=lambda s: s.get("endDate", ""),
            reverse=True,
        )[:num_sprints]

        # Get story points field
        agile_fields = get_agile_fields()
        story_points_field = agile_fields["story_points"]

        # Calculate points for each sprint
        sprint_data = []
        for sprint in sprints:
            sprint_id = sprint["id"]
            sprint_name = sprint.get("name", f"Sprint {sprint_id}")

            # Get completed issues in this sprint
            jql = f"sprint = {sprint_id} AND status = Done"
            search_result = client.search_issues(
                jql, fields=["summary", "status", story_points_field], max_results=200
            )
            issues = search_result.get("issues", [])

            # Sum story points
            completed_points = 0
            completed_count = 0
            for issue in issues:
                fields = issue.get("fields", {})
                points = fields.get(story_points_field) or 0
                completed_points += points
                completed_count += 1

            sprint_data.append(
                {
                    "sprint_id": sprint_id,
                    "sprint_name": sprint_name,
                    "completed_points": completed_points,
                    "completed_issues": completed_count,
                    "start_date": sprint.get("startDate", "")[:10]
                    if sprint.get("startDate")
                    else None,
                    "end_date": sprint.get("endDate", "")[:10]
                    if sprint.get("endDate")
                    else None,
                }
            )

        # Calculate velocity metrics
        velocities = [s["completed_points"] for s in sprint_data]
        avg_velocity = mean(velocities) if velocities else 0
        velocity_stdev = stdev(velocities) if len(velocities) > 1 else 0
        min_velocity = min(velocities) if velocities else 0
        max_velocity = max(velocities) if velocities else 0
        total_points = sum(velocities)

        return {
            "project_key": project_key,
            "board_id": actual_board_id,
            "board_name": board_name,
            "sprints_analyzed": len(sprint_data),
            "average_velocity": round(avg_velocity, 1),
            "velocity_stdev": round(velocity_stdev, 1),
            "min_velocity": min_velocity,
            "max_velocity": max_velocity,
            "total_points": total_points,
            "sprints": sprint_data,
        }
    finally:
        if should_close:
            client.close()


def format_velocity(data: dict, output_format: str = "text") -> str:
    """Format velocity data for output."""
    if output_format == "json":
        return json.dumps(data, indent=2)

    lines = []

    # Header
    project = data.get("project_key") or f"Board {data.get('board_id')}"
    lines.append(f"Velocity Report: {project}")
    lines.append("=" * 60)
    lines.append("")

    # Summary
    lines.append("Summary:")
    lines.append(f"  Average Velocity: {data['average_velocity']} points/sprint")
    lines.append(f"  Range: {data['min_velocity']} - {data['max_velocity']} points")
    if data["velocity_stdev"] > 0:
        lines.append(f"  Std Dev: {data['velocity_stdev']} points")
    lines.append(f"  Sprints Analyzed: {data['sprints_analyzed']}")
    lines.append("")

    # Sprint breakdown
    lines.append("Sprint Breakdown:")
    lines.append(f"{'Sprint':<30} {'Points':>8} {'Issues':>8} {'Dates'}")
    lines.append("-" * 70)

    for sprint in data["sprints"]:
        name = sprint["sprint_name"]
        if len(name) > 28:
            name = name[:25] + "..."
        points = sprint["completed_points"]
        issues = sprint["completed_issues"]
        dates = ""
        if sprint.get("start_date") and sprint.get("end_date"):
            dates = f"{sprint['start_date']} → {sprint['end_date']}"
        lines.append(f"{name:<30} {points:>8} {issues:>8} {dates}")

    lines.append("-" * 70)
    lines.append(f"{'Total':<30} {data['total_points']:>8}")
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Calculate velocity from completed sprints",
        epilog="""Examples:
    jira agile velocity --project DEMO
    jira agile velocity --project DEMO --sprints 5
    jira agile velocity --board 123 --sprints 3
    jira agile velocity --project DEMO --output json
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--board", "-b", type=int, help="Board ID")
    parser.add_argument(
        "--project", "-p", help="Project key (will find board automatically)"
    )
    parser.add_argument(
        "--sprints",
        "-n",
        type=int,
        default=3,
        help="Number of closed sprints to analyze (default: 3)",
    )
    parser.add_argument(
        "--output", "-o", choices=["text", "json"], default="text", help="Output format"
    )

    args = parser.parse_args(argv)

    if not args.board and not args.project:
        parser.error("Either --board or --project is required")

    try:
        result = get_velocity(
            board_id=args.board,
            project_key=args.project,
            num_sprints=args.sprints,
        )

        output = format_velocity(result, args.output)
        print(output)

        if args.output == "text":
            print_success(
                f"Velocity: {result['average_velocity']} points/sprint "
                f"(based on {result['sprints_analyzed']} sprints)"
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
