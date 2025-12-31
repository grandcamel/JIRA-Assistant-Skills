#!/usr/bin/env python3
"""
Set story points on JIRA issues.

Usage:
    python estimate_issue.py PROJ-1 --points 5
    python estimate_issue.py PROJ-1,PROJ-2,PROJ-3 --points 3
    python estimate_issue.py PROJ-1 --points 0  # Clear estimate
    python estimate_issue.py --jql "sprint=456 AND type=Story" --points 2
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Optional, List

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client, get_agile_field
from jira_assistant_skills_lib import print_error, JiraError, ValidationError
from jira_assistant_skills_lib import validate_issue_key
from jira_assistant_skills_lib import print_success

FIBONACCI_SEQUENCE = [0, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]


def estimate_issue(issue_keys: List[str] = None,
                   jql: str = None,
                   points: float = None,
                   validate_fibonacci: bool = False,
                   profile: str = None,
                   client=None) -> dict:
    """
    Set story points on issues.

    Args:
        issue_keys: List of issue keys to update
        jql: JQL query to find issues
        points: Story point value (0 to clear)
        validate_fibonacci: If True, validate points against Fibonacci sequence
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Result dictionary with count of updated issues

    Raises:
        ValidationError: If inputs are invalid
        JiraError: If API call fails
    """
    if not issue_keys and not jql:
        raise ValidationError("Either issue keys or JQL query is required")

    if points is None:
        raise ValidationError("Story points value is required")

    # Validate Fibonacci if enabled
    if validate_fibonacci and points not in FIBONACCI_SEQUENCE:
        raise ValidationError(
            f"Points {points} is not a valid Fibonacci value. "
            f"Valid values: {FIBONACCI_SEQUENCE}"
        )

    # Initialize client
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        # Get issue keys from JQL if provided
        if jql and not issue_keys:
            search_result = client.search_issues(jql)
            issue_keys = [issue['key'] for issue in search_result.get('issues', [])]

        if not issue_keys:
            return {'updated': 0, 'issues': []}

        # Validate issue keys
        issue_keys = [validate_issue_key(k) for k in issue_keys]

        # Get Story Points field ID from configuration
        story_points_field = get_agile_field('story_points', profile)

        # Prepare update data
        # If points is 0, set to None to clear the field
        points_value = None if points == 0 else points

        updated = 0
        for key in issue_keys:
            client.update_issue(key, {
                story_points_field: points_value
            })
            updated += 1

        return {
            'updated': updated,
            'issues': issue_keys,
            'points': points
        }

    finally:
        if should_close:
            client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Set story points on JIRA issues',
        epilog='Example: python estimate_issue.py PROJ-1 --points 5'
    )

    parser.add_argument('issues', nargs='?',
                       help='Issue key(s) to update (comma-separated)')
    parser.add_argument('--points', '-p', type=float, required=True,
                       help='Story points value (0 to clear)')
    parser.add_argument('--jql', '-j',
                       help='JQL query to find issues')
    parser.add_argument('--validate-fibonacci', action='store_true',
                       help='Validate points against Fibonacci sequence')
    parser.add_argument('--profile',
                       help='JIRA profile to use')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format')

    args = parser.parse_args(argv)

    try:
        # Parse issue keys if provided
        issue_keys = None
        if args.issues:
            issue_keys = [k.strip() for k in args.issues.split(',')]

        result = estimate_issue(
            issue_keys=issue_keys,
            jql=args.jql,
            points=args.points,
            validate_fibonacci=args.validate_fibonacci,
            profile=args.profile
        )

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            if result['updated'] == 0:
                print("No issues updated")
            else:
                pts_str = "cleared" if args.points == 0 else f"set to {args.points}"
                print_success(f"Updated {result['updated']} issue(s)")
                print(f"Story points: {pts_str}")
                for key in result['issues']:
                    print(f"  {key}")

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
