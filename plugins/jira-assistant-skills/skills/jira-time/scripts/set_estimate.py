#!/usr/bin/env python3
"""
Set time estimates on a JIRA issue.

Sets original and/or remaining estimates for time tracking.
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
    validate_issue_key,
    validate_time_format,
)


def set_estimate(
    client,
    issue_key: str,
    original_estimate: str | None = None,
    remaining_estimate: str | None = None,
) -> dict[str, Any]:
    """
    Set time estimates on an issue.

    Args:
        client: JiraClient instance
        issue_key: Issue key (e.g., 'PROJ-123')
        original_estimate: Original estimate (e.g., '2d')
        remaining_estimate: Remaining estimate (e.g., '1d 4h')

    Returns:
        Updated time tracking info

    Raises:
        ValidationError: If no estimates provided or invalid format
        JiraError: If API call fails
    """
    # Validate at least one estimate is provided
    if not original_estimate and not remaining_estimate:
        raise ValidationError(
            "At least one of original_estimate or remaining_estimate must be provided"
        )

    # Validate time formats
    if original_estimate and not validate_time_format(original_estimate):
        raise ValidationError(
            f"Invalid time format: '{original_estimate}'. "
            f"Use format like '2h', '1d 4h', '30m'"
        )

    if remaining_estimate and not validate_time_format(remaining_estimate):
        raise ValidationError(
            f"Invalid time format: '{remaining_estimate}'. "
            f"Use format like '2h', '1d 4h', '30m'"
        )

    # Set the estimates
    client.set_time_tracking(
        issue_key=issue_key,
        original_estimate=original_estimate,
        remaining_estimate=remaining_estimate,
    )

    # Return updated time tracking info
    return client.get_time_tracking(issue_key)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Set time estimates on a JIRA issue.",
        epilog="""
Examples:
  %(prog)s PROJ-123 --original "2d"
  %(prog)s PROJ-123 --remaining "1d 4h"
  %(prog)s PROJ-123 --original "2d" --remaining "1d 4h"
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument("--original", "-o", help="Original estimate (e.g., 2d, 1w)")
    parser.add_argument("--remaining", "-r", help="Remaining estimate (e.g., 1d 4h)")
    parser.add_argument("--profile", "-p", help="JIRA profile to use")
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    # Validate that at least one estimate is specified
    if not args.original and not args.remaining:
        parser.error("At least one of --original or --remaining must be specified")

    try:
        # Validate issue key
        validate_issue_key(args.issue_key)

        # Get client
        client = get_jira_client(args.profile)

        # Get current values for comparison
        current = client.get_time_tracking(args.issue_key)

        # Set estimates
        result = set_estimate(
            client,
            args.issue_key,
            original_estimate=args.original,
            remaining_estimate=args.remaining,
        )

        # Output result
        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Time estimates updated for {args.issue_key}:")

            if args.original:
                old_orig = current.get("originalEstimate", "unset")
                new_orig = result.get("originalEstimate", "unset")
                print(f"  Original estimate: {new_orig} (was {old_orig})")

            if args.remaining:
                old_rem = current.get("remainingEstimate", "unset")
                new_rem = result.get("remainingEstimate", "unset")
                print(f"  Remaining estimate: {new_rem} (was {old_rem})")

            if result.get("timeSpent"):
                print(f"  Time spent: {result.get('timeSpent')}")

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)


if __name__ == "__main__":
    main()
