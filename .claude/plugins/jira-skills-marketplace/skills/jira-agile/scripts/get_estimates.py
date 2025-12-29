#!/usr/bin/env python3
"""
Get story point estimation summaries.

Usage:
    python get_estimates.py --sprint 456
    python get_estimates.py --epic PROJ-100
    python get_estimates.py --sprint 456 --group-by assignee
    python get_estimates.py --sprint 456 --group-by status
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Optional
from collections import defaultdict

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client, get_agile_fields
from error_handler import print_error, JiraError, ValidationError
from validators import validate_issue_key
from formatters import print_success


def get_estimates(sprint_id: int = None,
                  epic_key: str = None,
                  group_by: str = None,
                  profile: str = None,
                  client=None) -> dict:
    """
    Get story point estimation summary.

    Args:
        sprint_id: Sprint ID to get estimates for
        epic_key: Epic key to get estimates for
        group_by: Group by 'assignee' or 'status'
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Result dictionary with totals and optional groupings

    Raises:
        ValidationError: If inputs are invalid
        JiraError: If API call fails
    """
    if not sprint_id and not epic_key:
        raise ValidationError("Either sprint ID or epic key is required")

    # Initialize client
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        # Get Agile field IDs from configuration
        agile_fields = get_agile_fields(profile)
        story_points_field = agile_fields['story_points']

        # Get issues
        if sprint_id:
            result = client.get_sprint_issues(sprint_id)
            issues = result.get('issues', [])
        else:
            # Search for issues in epic
            epic_key = validate_issue_key(epic_key)
            jql = f'"Epic Link" = {epic_key}'
            result = client.search_issues(jql, fields=[
                'summary', 'status', 'assignee', story_points_field
            ])
            issues = result.get('issues', [])

        # Calculate totals
        total_points = 0
        by_status = defaultdict(float)
        by_assignee = defaultdict(float)

        for issue in issues:
            fields = issue.get('fields', {})
            points = fields.get(story_points_field) or 0

            total_points += points

            # Group by status
            status = fields.get('status', {}).get('name', 'Unknown')
            by_status[status] += points

            # Group by assignee
            assignee = fields.get('assignee')
            if assignee:
                assignee_name = assignee.get('displayName', 'Unknown')
            else:
                assignee_name = 'Unassigned'
            by_assignee[assignee_name] += points

        # Build result
        response = {
            'total_points': total_points,
            'issue_count': len(issues),
            'by_status': dict(by_status),
            'by_assignee': dict(by_assignee)
        }

        if sprint_id:
            response['sprint_id'] = sprint_id
        if epic_key:
            response['epic_key'] = epic_key

        return response

    finally:
        if should_close:
            client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Get story point estimation summary',
        epilog='Example: python get_estimates.py --sprint 456'
    )

    # Source options (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument('--sprint', '-s', type=int,
                             help='Sprint ID')
    source_group.add_argument('--epic', '-e',
                             help='Epic key')

    parser.add_argument('--group-by', '-g',
                       choices=['assignee', 'status'],
                       help='Group results')
    parser.add_argument('--profile',
                       help='JIRA profile to use')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format')

    args = parser.parse_args()

    try:
        result = get_estimates(
            sprint_id=args.sprint,
            epic_key=args.epic,
            group_by=args.group_by,
            profile=args.profile
        )

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            if args.sprint:
                print_success(f"Sprint {args.sprint} Estimates")
            else:
                print_success(f"Epic {args.epic} Estimates")

            print(f"Total: {result['total_points']} points ({result['issue_count']} issues)")

            # Show by status
            if result['by_status']:
                done_pts = result['by_status'].get('Done', 0)
                total = result['total_points'] or 1
                print(f"\nBy Status:")
                for status, points in sorted(result['by_status'].items()):
                    pct = (points / total) * 100 if total > 0 else 0
                    print(f"  {status}: {points} points ({pct:.0f}%)")

            # Show by assignee if requested
            if args.group_by == 'assignee' and result['by_assignee']:
                total = result['total_points'] or 1
                print(f"\nBy Assignee:")
                for assignee, points in sorted(result['by_assignee'].items(), key=lambda x: -x[1]):
                    pct = (points / total) * 100 if total > 0 else 0
                    print(f"  {assignee}: {points} points ({pct:.0f}%)")

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
