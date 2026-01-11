#!/usr/bin/env python3
"""
Transition a JSM service request to new status.

Usage:
    python transition_request.py SD-101 --to "In Progress"
    python transition_request.py SD-101 --transition-id 11
    python transition_request.py SD-101 --to "Resolved" --comment "Issue fixed" --public
    python transition_request.py SD-101 --show-transitions
"""

import argparse
import sys

from jira_assistant_skills_lib import (
    JiraError,
    NotFoundError,
    get_jira_client,
    print_error,
    print_success,
)


def transition_service_request(
    issue_key: str,
    transition_id: str | None = None,
    transition_name: str | None = None,
    comment: str | None = None,
    public: bool = True,
) -> None:
    """
    Transition a service request.

    Args:
        issue_key: Request key
        transition_id: Transition ID (optional if transition_name provided)
        transition_name: Transition name to lookup
        comment: Optional comment to add
        public: Whether comment is public (customer-visible)

    Raises:
        ValueError: If transition not found
        NotFoundError: If request doesn't exist
    """
    with get_jira_client() as client:
        # Lookup transition ID if name provided
        if transition_name and not transition_id:
            transitions = client.get_request_transitions(issue_key)
            matching = [t for t in transitions if t["name"] == transition_name]

            if not matching:
                available = [t["name"] for t in transitions]
                raise ValueError(
                    f"Transition '{transition_name}' not found. "
                    f"Available: {', '.join(available)}"
                )

            transition_id = matching[0]["id"]

        if not transition_id:
            raise ValueError("Either transition_id or transition_name must be provided")

        client.transition_request(
            issue_key, transition_id, comment=comment, public=public
        )


def list_transitions(issue_key: str) -> list:
    """
    List available transitions for a request.

    Args:
        issue_key: Request key

    Returns:
        List of available transitions
    """
    with get_jira_client() as client:
        return client.get_request_transitions(issue_key)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Transition a JSM service request",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  By transition name:
    %(prog)s SD-101 --to "In Progress"
    %(prog)s SD-101 --to "Resolved"

  By transition ID:
    %(prog)s SD-101 --transition-id 11

  With comment:
    %(prog)s SD-101 --to "Resolved" --comment "Issue fixed by restarting server"

  Public vs internal comment:
    %(prog)s SD-101 --to "Waiting for customer" --comment "Please provide more details" --public
    %(prog)s SD-101 --to "In Progress" --comment "Escalating to L2 support" --internal

  Show available transitions:
    %(prog)s SD-101 --show-transitions
        """,
    )

    parser.add_argument("request_key", help="Request key (e.g., SD-101)")
    parser.add_argument(
        "--to", "--transition-name", dest="transition_name", help="Transition name"
    )
    parser.add_argument("--transition-id", help="Transition ID")
    parser.add_argument("--comment", help="Comment to add during transition")
    parser.add_argument(
        "--public",
        action="store_true",
        default=None,
        help="Make comment public (customer-visible)",
    )
    parser.add_argument(
        "--internal", action="store_true", help="Make comment internal (agent-only)"
    )
    parser.add_argument(
        "--show-transitions",
        action="store_true",
        help="Show available transitions and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without doing it",
    )

    args = parser.parse_args(argv)

    try:
        # Show transitions
        if args.show_transitions:
            transitions = list_transitions(args.request_key)

            print(f"\nAvailable transitions for {args.request_key}:\n")
            print(f"{'ID':<6} {'Name':<30} {'To Status'}")
            print("-" * 60)

            for t in transitions:
                tid = t.get("id", "N/A")
                name = t.get("name", "N/A")
                to_status = t.get("to", {}).get("name", "N/A")
                print(f"{tid:<6} {name:<30} {to_status}")

            return 0

        # Validate transition arguments
        if not args.transition_name and not args.transition_id:
            print_error("Either --to or --transition-id must be provided")
            return 1

        # Determine comment visibility
        public = True
        if args.internal:
            public = False
        elif args.public is not None:
            public = args.public

        if args.dry_run:
            print("DRY RUN MODE - No changes will be made\n")
            print(f"Would transition request {args.request_key}:")
            if args.transition_name:
                print(f"  To: {args.transition_name}")
            if args.transition_id:
                print(f"  Transition ID: {args.transition_id}")
            if args.comment:
                visibility = (
                    "Public (customer-visible)" if public else "Internal (agent-only)"
                )
                print(f"  Comment: {args.comment}")
                print(f"  Visibility: {visibility}")
            return 0

        transition_service_request(
            issue_key=args.request_key,
            transition_id=args.transition_id,
            transition_name=args.transition_name,
            comment=args.comment,
            public=public,
        )

        print_success(f"Request {args.request_key} transitioned successfully!")

        if args.comment:
            visibility = "public" if public else "internal"
            print(f"Comment added ({visibility}): {args.comment}")

        return 0

    except ValueError as e:
        print_error(str(e))
        return 1
    except (JiraError, NotFoundError) as e:
        print_error(f"Failed to transition request: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
