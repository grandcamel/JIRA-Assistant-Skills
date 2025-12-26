#!/usr/bin/env python3
"""
Create a new Sprint in JIRA.

Usage:
    python create_sprint.py --board 123 --name "Sprint 42"
    python create_sprint.py --board 123 --name "Sprint 42" --start 2025-01-20 --end 2025-02-03
    python create_sprint.py --board 123 --name "Sprint 42" --goal "Launch MVP"
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

# Imports from shared library
from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from formatters import print_success
from time_utils import parse_date_to_iso


def create_sprint(board_id: int, name: str,
                  start_date: str = None, end_date: str = None,
                  goal: str = None,
                  profile: str = None, client=None) -> dict:
    """
    Create a new Sprint in JIRA.

    Args:
        board_id: Scrum board ID (required)
        name: Sprint name (required)
        start_date: Sprint start date (YYYY-MM-DD or ISO format)
        end_date: Sprint end date (YYYY-MM-DD or ISO format)
        goal: Sprint goal description
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Created sprint data from JIRA Agile API

    Raises:
        ValidationError: If inputs are invalid (e.g., end before start)
        JiraError: If API call fails (e.g., board not found)
    """
    # Validate required fields
    if not board_id:
        raise ValidationError("Board ID is required")

    if not name:
        raise ValidationError("Sprint name is required")

    # Parse and validate dates using shared utility
    try:
        parsed_start = parse_date_to_iso(start_date) if start_date else None
        parsed_end = parse_date_to_iso(end_date) if end_date else None
    except ValueError as e:
        raise ValidationError(str(e))

    # Validate date range
    if parsed_start and parsed_end:
        start_dt = datetime.fromisoformat(parsed_start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(parsed_end.replace('Z', '+00:00'))
        if end_dt <= start_dt:
            raise ValidationError("End date must be after start date")

    # Build sprint data
    sprint_data = {
        'originBoardId': board_id,
        'name': name
    }

    if parsed_start:
        sprint_data['startDate'] = parsed_start

    if parsed_end:
        sprint_data['endDate'] = parsed_end

    if goal:
        sprint_data['goal'] = goal

    # Initialize client
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        # Use Agile API to create sprint
        result = client.create_sprint(
            board_id=board_id,
            name=name,
            goal=sprint_data.get('goal'),
            start_date=sprint_data.get('startDate'),
            end_date=sprint_data.get('endDate')
        )
        return result

    finally:
        if should_close:
            client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Create a new Sprint in JIRA',
        epilog='Example: python create_sprint.py --board 123 --name "Sprint 42" --goal "Launch MVP"'
    )

    parser.add_argument('--board', '-b', type=int, required=True,
                       help='Scrum board ID')
    parser.add_argument('--name', '-n', required=True,
                       help='Sprint name')
    parser.add_argument('--start', '-s',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', '-e',
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--goal', '-g',
                       help='Sprint goal')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')

    args = parser.parse_args()

    try:
        result = create_sprint(
            board_id=args.board,
            name=args.name,
            start_date=args.start,
            end_date=args.end,
            goal=args.goal,
            profile=args.profile
        )

        sprint_id = result.get('id')
        sprint_name = result.get('name')

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print_success(f"Created sprint: {sprint_name} (ID: {sprint_id})")
            if args.goal:
                print(f"Goal: {args.goal}")
            if args.start and args.end:
                print(f"Duration: {args.start} to {args.end}")
            print(f"State: {result.get('state', 'future')}")

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
