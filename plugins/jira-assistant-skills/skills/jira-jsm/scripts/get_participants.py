#!/usr/bin/env python3
"""
Get request participants.

Usage:
    python get_participants.py REQ-123
    python get_participants.py REQ-123 --output json
"""

import sys
import os
import argparse
import json
from pathlib import Path


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError


def get_participants_func(issue_key: str, start: int = 0, limit: int = 50,
                           profile: str = None) -> dict:
    """
    Get participants for a request.

    Args:
        issue_key: Request issue key
        start: Starting index for pagination
        limit: Maximum results per page
        profile: JIRA profile to use

    Returns:
        Participants data
    """
    with get_jira_client(profile) as client:
        return client.get_request_participants(issue_key, start=start, limit=limit)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Get request participants',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Get participants:
    %(prog)s REQ-123

  JSON output:
    %(prog)s REQ-123 --output json

  Pagination:
    %(prog)s REQ-123 --start 0 --limit 50
        """
    )

    parser.add_argument('issue_key',
                        help='Request issue key (e.g., REQ-123)')
    parser.add_argument('--start', type=int, default=0,
                        help='Starting index for pagination (default: 0)')
    parser.add_argument('--limit', type=int, default=50,
                        help='Maximum results per page (default: 50)')
    parser.add_argument('--output', choices=['text', 'json', 'csv'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--count', action='store_true',
                        help='Show only count')
    parser.add_argument('--profile',
                        help='JIRA profile to use from config')

    args = parser.parse_args()

    try:
        data = get_participants_func(
            issue_key=args.issue_key,
            start=args.start,
            limit=args.limit,
            profile=args.profile
        )

        participants = data.get('values', [])

        if args.count:
            print(len(participants))
            return 0

        if args.output == 'json':
            print(json.dumps(participants, indent=2))
        elif args.output == 'csv':
            print("Email,DisplayName")
            for participant in participants:
                print(f"{participant.get('emailAddress','')},{participant.get('displayName','')}")
        else:
            if not participants:
                print(f"No participants for {args.issue_key}.")
                return 0

            print(f"Participants for {args.issue_key}:\n")
            print(f"{'Email':<30} {'Display Name'}")
            print("-" * 60)
            for participant in participants:
                print(f"{participant.get('emailAddress',''):<30} {participant.get('displayName','')}")

            print(f"\nTotal: {len(participants)} participant(s)")

        return 0

    except JiraError as e:
        print_error(f"Failed to get participants: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
