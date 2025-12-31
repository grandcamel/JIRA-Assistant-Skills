#!/usr/bin/env python3
"""
Get time tracking summary for a JIRA issue.

Displays original estimate, remaining estimate, time spent, and progress.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add shared lib to path

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import validate_issue_key
from jira_assistant_skills_lib import format_seconds


def get_time_tracking(client, issue_key: str) -> Dict[str, Any]:
    """
    Get time tracking info for an issue.

    Args:
        client: JiraClient instance
        issue_key: Issue key (e.g., 'PROJ-123')

    Returns:
        Time tracking info dict

    Raises:
        JiraError: If API call fails
    """
    return client.get_time_tracking(issue_key)


def calculate_progress(time_tracking: Dict[str, Any]) -> Optional[int]:
    """
    Calculate completion percentage.

    Args:
        time_tracking: Time tracking info dict

    Returns:
        Progress percentage (0-100) or None if no estimate
    """
    original_seconds = time_tracking.get('originalEstimateSeconds')
    spent_seconds = time_tracking.get('timeSpentSeconds', 0)

    if not original_seconds:
        return None

    if not spent_seconds:
        return 0

    return min(100, int((spent_seconds / original_seconds) * 100))


def generate_progress_bar(progress: int, width: int = 20) -> str:
    """
    Generate a visual progress bar.

    Args:
        progress: Progress percentage (0-100)
        width: Width of the bar in characters

    Returns:
        Progress bar string
    """
    filled = int(width * progress / 100)
    empty = width - filled
    return '█' * filled + '░' * empty


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Get time tracking summary for a JIRA issue.',
        epilog='''
Examples:
  %(prog)s PROJ-123
  %(prog)s PROJ-123 --output json
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('issue_key', help='Issue key (e.g., PROJ-123)')
    parser.add_argument('--profile', '-p',
                        help='JIRA profile to use')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')

    args = parser.parse_args(argv)

    try:
        # Validate issue key
        validate_issue_key(args.issue_key)

        # Get client
        client = get_jira_client(args.profile)

        # Get time tracking info
        result = get_time_tracking(client, args.issue_key)

        # Output result
        if args.output == 'json':
            # Add calculated progress to JSON output
            result['progress'] = calculate_progress(result)
            print(json.dumps(result, indent=2))
        else:
            print(f"Time Tracking for {args.issue_key}:")
            print()

            original = result.get('originalEstimate', 'Not set')
            original_sec = result.get('originalEstimateSeconds')
            if original_sec:
                print(f"Original Estimate:    {original} ({format_seconds(original_sec)})")
            else:
                print(f"Original Estimate:    {original}")

            remaining = result.get('remainingEstimate', 'Not set')
            remaining_sec = result.get('remainingEstimateSeconds')
            if remaining_sec:
                print(f"Remaining Estimate:   {remaining} ({format_seconds(remaining_sec)})")
            else:
                print(f"Remaining Estimate:   {remaining}")

            spent = result.get('timeSpent', 'None')
            spent_sec = result.get('timeSpentSeconds')
            if spent_sec:
                print(f"Time Spent:           {spent} ({format_seconds(spent_sec)})")
            else:
                print(f"Time Spent:           {spent}")

            # Show progress if we have an estimate
            progress = calculate_progress(result)
            if progress is not None:
                print()
                bar = generate_progress_bar(progress)
                print(f"Progress: {bar} {progress}% complete")
                if spent_sec and original_sec:
                    print(f"          {format_seconds(spent_sec)} logged of {format_seconds(original_sec)} estimated")

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)


if __name__ == '__main__':
    main()
