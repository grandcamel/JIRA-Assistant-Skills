#!/usr/bin/env python3
"""
Get Sprint details and progress from JIRA.

Usage:
    python get_sprint.py 456
    python get_sprint.py 456 --with-issues
    python get_sprint.py --board 123 --active
    python get_sprint.py 456 --output json
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib'))

# Imports from shared library
from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from formatters import print_success

# Story Points custom field (may vary per instance)
STORY_POINTS_FIELD = 'customfield_10016'


def get_sprint(sprint_id: int,
               with_issues: bool = False,
               profile: str = None,
               client=None) -> dict:
    """
    Get sprint details and optionally calculate progress.

    Args:
        sprint_id: Sprint ID to retrieve
        with_issues: Include issues and calculate progress
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Sprint data with optional issues and progress stats

    Raises:
        JiraError: If sprint doesn't exist or API error
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
        # Fetch sprint details
        sprint = client.get_sprint(sprint_id)

        result = dict(sprint)

        # Fetch issues if requested
        if with_issues:
            issues_response = client.get_sprint_issues(sprint_id)
            issues = issues_response.get('issues', [])
            result['issues'] = issues

            # Calculate progress
            total_issues = len(issues)
            done_issues = sum(
                1 for issue in issues
                if issue['fields']['status']['name'].lower() in ['done', 'closed', 'resolved']
            )

            result['progress'] = {
                'total': total_issues,
                'done': done_issues,
                'percentage': int((done_issues / total_issues * 100) if total_issues > 0 else 0)
            }

            # Calculate story points
            total_points = 0
            done_points = 0

            for issue in issues:
                points = issue['fields'].get(STORY_POINTS_FIELD)
                if points is not None:
                    total_points += points
                    if issue['fields']['status']['name'].lower() in ['done', 'closed', 'resolved']:
                        done_points += points

            if total_points > 0:
                result['story_points'] = {
                    'total': total_points,
                    'done': done_points,
                    'percentage': int((done_points / total_points * 100))
                }

        return result

    finally:
        if should_close:
            client.close()


def get_active_sprint_for_board(board_id: int,
                                profile: str = None,
                                client=None) -> dict:
    """
    Get the currently active sprint for a board.

    Args:
        board_id: Board ID to query
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Active sprint data or None

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
        result = client.get_board_sprints(board_id, state='active')
        sprints = result.get('values', [])
        if sprints:
            return sprints[0]
        return None

    finally:
        if should_close:
            client.close()


def format_sprint_output(sprint_data: dict, format: str = 'text') -> str:
    """
    Format sprint data for output.

    Args:
        sprint_data: Sprint data from get_sprint()
        format: Output format ('text' or 'json')

    Returns:
        Formatted string
    """
    if format == 'json':
        return json.dumps(sprint_data, indent=2)

    # Text format
    lines = []
    lines.append(f"Sprint: {sprint_data.get('name', 'Unknown')}")
    lines.append(f"State: {sprint_data.get('state', 'unknown')}")

    # Dates
    start_date = sprint_data.get('startDate')
    end_date = sprint_data.get('endDate')
    if start_date and end_date:
        # Parse dates for display
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            now = datetime.now(start.tzinfo)

            if end > now:
                days_remaining = (end - now).days
                lines.append(f"Dates: {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')} ({days_remaining} days remaining)")
            else:
                lines.append(f"Dates: {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')}")
        except (ValueError, TypeError):
            lines.append(f"Dates: {start_date} → {end_date}")

    # Goal
    goal = sprint_data.get('goal')
    if goal:
        lines.append(f"Goal: {goal}")

    # Progress
    if 'progress' in sprint_data:
        prog = sprint_data['progress']
        lines.append(f"Progress: {prog['done']}/{prog['total']} issues ({prog['percentage']}%)")

    # Story points
    if 'story_points' in sprint_data:
        sp = sprint_data['story_points']
        lines.append(f"Story Points: {sp['done']}/{sp['total']} ({sp['percentage']}%)")

    # Issues
    if 'issues' in sprint_data and sprint_data['issues']:
        lines.append("")
        lines.append("Issues:")
        for issue in sprint_data['issues']:
            status = issue['fields']['status']['name']
            summary = issue['fields']['summary']
            points = issue['fields'].get(STORY_POINTS_FIELD)
            points_str = f" ({points} pts)" if points else ""
            lines.append(f"  [{status}] {issue['key']} - {summary}{points_str}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Get Sprint details and progress from JIRA',
        epilog='Example: python get_sprint.py 456 --with-issues'
    )

    parser.add_argument('sprint_id', nargs='?', type=int,
                       help='Sprint ID')
    parser.add_argument('--board', '-b', type=int,
                       help='Board ID (with --active)')
    parser.add_argument('--active', '-a', action='store_true',
                       help='Get active sprint for board')
    parser.add_argument('--with-issues', '-i', action='store_true',
                       help='Include issues and calculate progress')
    parser.add_argument('--profile',
                       help='JIRA profile to use')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format')

    args = parser.parse_args()

    try:
        result = None

        if args.active:
            if not args.board:
                parser.error("--board is required with --active")
            result = get_active_sprint_for_board(
                board_id=args.board,
                profile=args.profile
            )
            if not result:
                print("No active sprint found for this board")
                return
        else:
            if not args.sprint_id:
                parser.error("sprint_id is required (or use --board with --active)")
            result = get_sprint(
                sprint_id=args.sprint_id,
                with_issues=args.with_issues,
                profile=args.profile
            )

        output = format_sprint_output(result, format=args.output)
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


if __name__ == '__main__':
    main()
