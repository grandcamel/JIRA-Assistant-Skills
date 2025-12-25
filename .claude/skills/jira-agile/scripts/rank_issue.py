#!/usr/bin/env python3
"""
Rank issues in JIRA backlog.

Usage:
    python rank_issue.py PROJ-1 --before PROJ-2
    python rank_issue.py PROJ-1 --after PROJ-3
    python rank_issue.py PROJ-1 --top
    python rank_issue.py PROJ-1 --bottom
    python rank_issue.py PROJ-1,PROJ-2,PROJ-3 --before PROJ-10
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Optional, List

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

# Imports from shared library
from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from validators import validate_issue_key
from formatters import print_success


def rank_issue(issue_keys: List[str],
               before_key: str = None,
               after_key: str = None,
               position: str = None,
               board_id: int = None,
               profile: str = None,
               client=None) -> dict:
    """
    Rank issues in the backlog.

    Args:
        issue_keys: List of issue keys to rank
        before_key: Rank before this issue
        after_key: Rank after this issue
        position: Position ('top' or 'bottom')
        board_id: Board ID (for top/bottom positioning)
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Result dictionary with count of ranked issues

    Raises:
        ValidationError: If inputs are invalid
        JiraError: If API call fails
    """
    if not issue_keys:
        raise ValidationError("At least one issue key is required")

    # Validate that a position is specified
    if not before_key and not after_key and not position:
        raise ValidationError("Must specify --before, --after, --top, or --bottom position")

    # Validate issue keys
    issue_keys = [validate_issue_key(k) for k in issue_keys]

    if before_key:
        before_key = validate_issue_key(before_key)

    if after_key:
        after_key = validate_issue_key(after_key)

    # Initialize client
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        # Build rank request based on position type
        if before_key:
            client.rank_issues(issue_keys, rank_before=before_key)
        elif after_key:
            client.rank_issues(issue_keys, rank_after=after_key)
        elif position == 'top':
            # For top/bottom, we need to get the first/last issue from the backlog
            # and rank before/after it - this requires board context
            raise ValidationError("Top/bottom ranking requires implementation with board context")
        elif position == 'bottom':
            raise ValidationError("Top/bottom ranking requires implementation with board context")

        return {
            'ranked': len(issue_keys),
            'issues': issue_keys
        }

    finally:
        if should_close:
            client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Rank issues in JIRA backlog',
        epilog='Example: python rank_issue.py PROJ-1 --before PROJ-2'
    )

    parser.add_argument('issues',
                       help='Issue key(s) to rank (comma-separated)')

    # Position options (mutually exclusive)
    position_group = parser.add_mutually_exclusive_group(required=True)
    position_group.add_argument('--before', '-b',
                               help='Rank before this issue')
    position_group.add_argument('--after', '-a',
                               help='Rank after this issue')
    position_group.add_argument('--top', action='store_true',
                               help='Move to top of backlog')
    position_group.add_argument('--bottom', action='store_true',
                               help='Move to bottom of backlog')

    parser.add_argument('--board', type=int,
                       help='Board ID (may be required for top/bottom)')
    parser.add_argument('--profile',
                       help='JIRA profile to use')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format')

    args = parser.parse_args()

    try:
        # Parse issue keys
        issue_keys = [k.strip() for k in args.issues.split(',')]

        # Determine position
        position = None
        if args.top:
            position = 'top'
        elif args.bottom:
            position = 'bottom'

        result = rank_issue(
            issue_keys=issue_keys,
            before_key=args.before,
            after_key=args.after,
            position=position,
            board_id=args.board,
            profile=args.profile
        )

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print_success(f"Ranked {result['ranked']} issue(s)")
            if args.before:
                print(f"Position: before {args.before}")
            elif args.after:
                print(f"Position: after {args.after}")
            elif position:
                print(f"Position: {position}")

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
