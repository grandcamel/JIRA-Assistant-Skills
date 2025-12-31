#!/usr/bin/env python3
"""
List customers for a JSM service desk.

Usage:
    python list_customers.py SD-1
    python list_customers.py SD-1 --query "john"
    python list_customers.py SD-1 --start 0 --limit 25
    python list_customers.py SD-1 --output json
    python list_customers.py SD-1 --count
"""

import sys
import os
import argparse
import json
from pathlib import Path


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import print_success


def list_service_desk_customers(service_desk_id: str, query: str = None,
                                  start: int = 0, limit: int = 50,
                                  profile: str = None) -> dict:
    """
    List customers for a service desk.

    Args:
        service_desk_id: Service desk ID or key
        query: Search query for filtering
        start: Starting index for pagination
        limit: Maximum results per page
        profile: JIRA profile to use

    Returns:
        Customers data
    """
    with get_jira_client(profile) as client:
        return client.get_service_desk_customers(
            service_desk_id,
            query=query,
            start=start,
            limit=limit
        )


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='List customers for a JSM service desk',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  List all customers:
    %(prog)s SD-1

  Search customers:
    %(prog)s SD-1 --query "john"

  Pagination:
    %(prog)s SD-1 --start 10 --limit 25

  JSON output:
    %(prog)s SD-1 --output json

  Customer count only:
    %(prog)s SD-1 --count
        """
    )

    parser.add_argument('service_desk_id',
                        help='Service desk ID or key (e.g., SD-1)')
    parser.add_argument('--query', '-q',
                        help='Search query for email/name filtering')
    parser.add_argument('--start', type=int, default=0,
                        help='Starting index for pagination (default: 0)')
    parser.add_argument('--limit', type=int, default=50,
                        help='Maximum results per page (default: 50)')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--count', action='store_true',
                        help='Show customer count only')
    parser.add_argument('--profile',
                        help='JIRA profile to use from config')

    args = parser.parse_args(argv)

    try:
        result = list_service_desk_customers(
            service_desk_id=args.service_desk_id,
            query=args.query,
            start=args.start,
            limit=args.limit,
            profile=args.profile
        )

        customers = result.get('values', [])
        total = result.get('size', len(customers))

        if args.count:
            print(total)
            return 0

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            if total == 0:
                print(f"No customers found for service desk {args.service_desk_id}")
                return 0

            print(f"Customers for Service Desk: {args.service_desk_id}\n")
            print(f"{'Email':<30} {'Display Name':<25} {'Active':<10}")
            print("-" * 70)

            active_count = 0
            for customer in customers:
                email = customer.get('emailAddress', 'N/A')
                name = customer.get('displayName', 'N/A')
                active = customer.get('active', False)
                active_str = "Yes" if active else "No"

                if active:
                    active_count += 1

                print(f"{email:<30} {name:<25} {active_str:<10}")

            print()
            print(f"Total: {total} customers ({active_count} active)")

        return 0

    except JiraError as e:
        print_error(f"Failed to list customers: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
