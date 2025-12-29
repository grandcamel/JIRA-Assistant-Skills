#!/usr/bin/env python3
"""
List all JSM service desks.

Usage:
    python list_service_desks.py
    python list_service_desks.py --output json
    python list_service_desks.py --filter "IT"
    python list_service_desks.py --project-key ITS
"""

import sys
import os
import argparse
import json
from pathlib import Path


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import format_json


def list_service_desks(start: int = 0, limit: int = 50, profile: str = None) -> dict:
    """
    List all JSM service desks.

    Args:
        start: Starting index for pagination
        limit: Maximum results per page
        profile: JIRA profile to use

    Returns:
        Service desks data with values, size, start, limit, isLastPage
    """
    client = get_jira_client(profile)
    service_desks = client.get_service_desks(start=start, limit=limit)
    client.close()

    return service_desks


def filter_service_desks(service_desks: dict, project_key_filter: str = None) -> dict:
    """
    Filter service desks by project key pattern.

    Args:
        service_desks: Service desks data
        project_key_filter: Project key pattern to filter by

    Returns:
        Filtered service desks data
    """
    if not project_key_filter:
        return service_desks

    filtered_values = [
        sd for sd in service_desks.get('values', [])
        if project_key_filter.upper() in sd.get('projectKey', '').upper()
    ]

    return {
        **service_desks,
        'values': filtered_values,
        'size': len(filtered_values)
    }


def format_service_desks_text(service_desks: dict) -> None:
    """
    Format service desks as human-readable text.

    Args:
        service_desks: Service desks data
    """
    values = service_desks.get('values', [])

    if not values:
        print("No service desks found.")
        print("\nNote: Ensure Jira Service Management is enabled for this instance.")
        return

    print("Available Service Desks:")
    print()
    print(f"{'ID':<4} {'Project Key':<15} {'Project Name':<30} {'Project ID':<10}")
    print(f"{'──':<4} {'───────────':<15} {'────────────':<30} {'──────────':<10}")

    for sd in values:
        sd_id = sd.get('id', '')
        project_key = sd.get('projectKey', '')
        project_name = sd.get('projectName', '')
        project_id = sd.get('projectId', '')

        print(f"{sd_id:<4} {project_key:<15} {project_name:<30} {project_id:<10}")

    print()
    print(f"Total: {len(values)} service desk{'s' if len(values) != 1 else ''}")


def format_service_desks_json(service_desks: dict) -> str:
    """
    Format service desks as JSON.

    Args:
        service_desks: Service desks data

    Returns:
        JSON string
    """
    return format_json(service_desks)


def main():
    parser = argparse.ArgumentParser(
        description='List all JSM service desks',
        epilog='Example: python list_service_desks.py --filter IT'
    )

    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')
    parser.add_argument('--filter', '-f',
                       help='Filter by project name or key')
    parser.add_argument('--project-key', '-k',
                       help='Filter by exact project key')
    parser.add_argument('--limit', '-l',
                       type=int,
                       default=50,
                       help='Maximum results to return (default: 50)')
    parser.add_argument('--start', '-s',
                       type=int,
                       default=0,
                       help='Starting index for pagination (default: 0)')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        # Fetch service desks
        service_desks = list_service_desks(
            start=args.start,
            limit=args.limit,
            profile=args.profile
        )

        # Apply filters
        if args.project_key:
            service_desks = filter_service_desks(service_desks, args.project_key)
        elif args.filter:
            service_desks = filter_service_desks(service_desks, args.filter)

        # Output results
        if args.output == 'json':
            print(format_service_desks_json(service_desks))
        else:
            format_service_desks_text(service_desks)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
