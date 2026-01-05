#!/usr/bin/env python3
"""
Move issues to a Sprint or back to the backlog in JIRA.

Usage:
    python move_to_sprint.py --sprint 456 --issues PROJ-1,PROJ-2,PROJ-3
    python move_to_sprint.py --sprint 456 --jql "project=PROJ AND status='To Do'"
    python move_to_sprint.py --sprint 456 --issues PROJ-1 --rank top
    python move_to_sprint.py --backlog --issues PROJ-5
    python move_to_sprint.py --sprint 456 --issues PROJ-1,PROJ-2 --dry-run
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
    print_error,
    print_success,
    print_warning,
    validate_issue_key,
)


def move_to_sprint(
    sprint_id: int,
    issue_keys: list[str] | None = None,
    jql: str | None = None,
    dry_run: bool = False,
    rank_position: str | None = None,
    profile: str | None = None,
    client=None,
) -> dict:
    """
    Move issues to a sprint.

    Args:
        sprint_id: Target sprint ID
        issue_keys: List of issue keys to move
        jql: JQL query to find issues to move
        dry_run: Preview changes without making them
        rank_position: Position to rank issues ('top', 'bottom')
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Result dictionary with counts:
        - moved: Number of issues moved
        - failed: Number of failures
        - would_move: Number that would be moved (dry-run only)

    Raises:
        ValidationError: If inputs are invalid
        JiraError: If API call fails
    """
    if not sprint_id:
        raise ValidationError("Sprint ID is required")

    if not issue_keys and not jql:
        raise ValidationError("Either issue_keys or jql is required")

    # Initialize client
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        # Collect issues to move
        issues_to_move = []

        if issue_keys:
            issues_to_move.extend([validate_issue_key(k) for k in issue_keys])

        if jql:
            search_result = client.search_issues(jql, max_results=1000)
            jql_issues = [issue["key"] for issue in search_result.get("issues", [])]
            issues_to_move.extend(jql_issues)

        if not issues_to_move:
            return {"moved": 0, "failed": 0, "message": "No issues to move"}

        # Dry run mode
        if dry_run:
            return {"would_move": len(issues_to_move), "issues": issues_to_move}

        # Move issues to sprint
        client.move_issues_to_sprint(sprint_id, issues_to_move, rank=rank_position)

        return {"moved": len(issues_to_move), "failed": 0}

    finally:
        if should_close:
            client.close()


def move_to_backlog(
    issue_keys: list[str] | None = None,
    jql: str | None = None,
    dry_run: bool = False,
    profile: str | None = None,
    client=None,
) -> dict:
    """
    Move issues back to the backlog (remove from sprint).

    Args:
        issue_keys: List of issue keys to move
        jql: JQL query to find issues to move
        dry_run: Preview changes without making them
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Result dictionary with counts

    Raises:
        ValidationError: If inputs are invalid
        JiraError: If API call fails
    """
    if not issue_keys and not jql:
        raise ValidationError("Either issue_keys or jql is required")

    # Initialize client
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        # Collect issues to move
        issues_to_move = []

        if issue_keys:
            issues_to_move.extend([validate_issue_key(k) for k in issue_keys])

        if jql:
            search_result = client.search_issues(jql, max_results=1000)
            jql_issues = [issue["key"] for issue in search_result.get("issues", [])]
            issues_to_move.extend(jql_issues)

        if not issues_to_move:
            return {"moved_to_backlog": 0, "message": "No issues to move"}

        # Dry run mode
        if dry_run:
            return {
                "would_move_to_backlog": len(issues_to_move),
                "issues": issues_to_move,
            }

        # Move issues to backlog
        client.move_issues_to_backlog(issues_to_move)

        return {"moved_to_backlog": len(issues_to_move)}

    finally:
        if should_close:
            client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Move issues to a Sprint or backlog in JIRA",
        epilog="Example: python move_to_sprint.py --sprint 456 --issues PROJ-1,PROJ-2",
    )

    # Target
    parser.add_argument("--sprint", "-s", type=int, help="Target sprint ID")
    parser.add_argument(
        "--backlog",
        "-b",
        action="store_true",
        help="Move to backlog (remove from sprint)",
    )

    # Issue selection
    parser.add_argument("--issues", "-i", help="Comma-separated issue keys")
    parser.add_argument("--jql", "-j", help="JQL query to find issues")

    # Options
    parser.add_argument(
        "--rank", "-r", choices=["top", "bottom"], help="Rank position after moving"
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Preview changes without making them",
    )

    parser.add_argument("--profile", help="JIRA profile to use")
    parser.add_argument(
        "--output", "-o", choices=["text", "json"], default="text", help="Output format"
    )

    args = parser.parse_args(argv)

    try:
        # Validate arguments
        if not args.sprint and not args.backlog:
            parser.error("Either --sprint or --backlog is required")

        if args.sprint and args.backlog:
            parser.error("Cannot specify both --sprint and --backlog")

        if not args.issues and not args.jql:
            parser.error("Either --issues or --jql is required")

        # Parse issue keys
        issue_keys = (
            [k.strip() for k in args.issues.split(",")] if args.issues else None
        )

        # Dry run message
        if args.dry_run:
            print_warning("DRY RUN MODE - No changes will be made")

        # Execute operation
        if args.backlog:
            result = move_to_backlog(
                issue_keys=issue_keys,
                jql=args.jql,
                dry_run=args.dry_run,
                profile=args.profile,
            )

            if args.output == "json":
                print(json.dumps(result, indent=2))
            elif args.dry_run:
                print(
                    f"Would move {result.get('would_move_to_backlog', 0)} issues to backlog:"
                )
                for issue in result.get("issues", []):
                    print(f"  - {issue}")
            else:
                print_success(f"Moved {result['moved_to_backlog']} issues to backlog")

        else:
            result = move_to_sprint(
                sprint_id=args.sprint,
                issue_keys=issue_keys,
                jql=args.jql,
                dry_run=args.dry_run,
                rank_position=args.rank,
                profile=args.profile,
            )

            if args.output == "json":
                print(json.dumps(result, indent=2))
            elif args.dry_run:
                print(
                    f"Would move {result.get('would_move', 0)} issues to sprint {args.sprint}:"
                )
                for issue in result.get("issues", []):
                    print(f"  - {issue}")
            else:
                print_success(f"Moved {result['moved']} issues to sprint {args.sprint}")
                if args.rank:
                    print(f"Ranked at: {args.rank}")

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
