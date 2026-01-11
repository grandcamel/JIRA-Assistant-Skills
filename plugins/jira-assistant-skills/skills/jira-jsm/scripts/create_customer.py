#!/usr/bin/env python3
"""
Create a JSM customer account.

Usage:
    python create_customer.py --email customer@example.com --name "John Customer"
    python create_customer.py --email jane@example.com
    python create_customer.py --email user@example.com --output json
    python create_customer.py --email test@example.com --dry-run
"""

import argparse
import json
import re
import sys

from jira_assistant_skills_lib import (
    JiraError,
    get_jira_client,
    print_error,
    print_success,
)


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def create_customer_account(
    email: str, display_name: str | None = None
) -> dict:
    """
    Create a customer account.

    Args:
        email: Customer email address
        display_name: Display name (defaults to email)

    Returns:
        Created customer data
    """
    if not validate_email(email):
        raise ValueError(f"Invalid email format: {email}")

    with get_jira_client() as client:
        return client.create_customer(email, display_name)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create a JSM customer account",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Create customer with name:
    %(prog)s --email customer@example.com --name "John Customer"

  Create customer (email only):
    %(prog)s --email jane@example.com

  JSON output:
    %(prog)s --email user@example.com --output json

  Dry-run:
    %(prog)s --email test@example.com --dry-run
        """,
    )

    parser.add_argument("--email", required=True, help="Customer email address")
    parser.add_argument(
        "--name", "--display-name", help="Display name (defaults to email)"
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without creating",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show full API response"
    )

    args = parser.parse_args(argv)

    try:
        if not validate_email(args.email):
            print_error(f"Invalid email format: {args.email}")
            return 1

        if args.dry_run:
            print("DRY RUN MODE - No changes will be made\n")
            print("Would create customer:")
            print(f"  Email: {args.email}")
            print(f"  Display Name: {args.name or args.email}")
            return 0

        customer = create_customer_account(
            email=args.email, display_name=args.name
        )

        if args.output == "json":
            if args.verbose:
                print(json.dumps(customer, indent=2))
            else:
                print(
                    json.dumps(
                        {
                            "accountId": customer.get("accountId"),
                            "emailAddress": customer.get("emailAddress"),
                            "displayName": customer.get("displayName"),
                        },
                        indent=2,
                    )
                )
        else:
            print_success("Customer created successfully!")
            print()
            print(f"Account ID:   {customer.get('accountId')}")
            print(f"Email:        {customer.get('emailAddress')}")
            print(f"Display Name: {customer.get('displayName')}")

            if args.verbose:
                print()
                print("Full response:")
                print(json.dumps(customer, indent=2))

        return 0

    except ValueError as e:
        print_error(str(e))
        return 1
    except JiraError as e:
        print_error(f"Failed to create customer: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
