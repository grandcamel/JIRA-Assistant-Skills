#!/usr/bin/env python3
"""
Get JSM organization details.

Usage:
    python get_organization.py 12345
    python get_organization.py 12345 --output json
"""

import argparse
import json
import sys

from jira_assistant_skills_lib import JiraError, get_jira_client, print_error


def get_organization_func(organization_id: int) -> dict:
    """
    Get organization details.

    Args:
        organization_id: Organization ID

    Returns:
        Organization data
    """
    with get_jira_client() as client:
        return client.get_organization(organization_id)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Get JSM organization details",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Get organization details:
    %(prog)s 12345

  JSON output:
    %(prog)s 12345 --output json
        """,
    )

    parser.add_argument("organization_id", type=int, help="Organization ID")
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show full API response"
    )

    args = parser.parse_args(argv)

    try:
        organization = get_organization_func(
            organization_id=args.organization_id
        )

        if args.output == "json":
            if args.verbose:
                print(json.dumps(organization, indent=2))
            else:
                print(
                    json.dumps(
                        {
                            "id": organization.get("id"),
                            "name": organization.get("name"),
                        },
                        indent=2,
                    )
                )
        else:
            print(
                f"Organization: {organization.get('name')} (ID: {organization.get('id')})\n"
            )

            if args.verbose:
                print("Full response:")
                print(json.dumps(organization, indent=2))

        return 0

    except JiraError as e:
        print_error(f"Failed to get organization: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
