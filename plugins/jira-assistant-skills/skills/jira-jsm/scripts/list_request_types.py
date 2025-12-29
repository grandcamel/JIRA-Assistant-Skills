#!/usr/bin/env python3
"""
List request types for a JSM service desk.

Usage:
    python list_request_types.py 1
    python list_request_types.py 1 --output json
    python list_request_types.py 1 --filter "incident"
    python list_request_types.py 1 --show-issue-types
"""

import sys
import os
import argparse
import json
from pathlib import Path


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import format_json


def list_request_types(service_desk_id: str, start: int = 0, limit: int = 50, profile: str = None) -> dict:
    """
    List request types for a service desk.

    Args:
        service_desk_id: Service desk ID
        start: Starting index for pagination
        limit: Maximum results per page
        profile: JIRA profile to use

    Returns:
        Request types data
    """
    client = get_jira_client(profile)
    request_types = client.get_request_types(service_desk_id, start=start, limit=limit)
    client.close()

    return request_types


def filter_request_types(request_types: dict, name_filter: str = None) -> dict:
    """
    Filter request types by name pattern.

    Args:
        request_types: Request types data
        name_filter: Name pattern to filter by

    Returns:
        Filtered request types data
    """
    if not name_filter:
        return request_types

    filtered_values = [
        rt for rt in request_types.get('values', [])
        if name_filter.lower() in rt.get('name', '').lower()
    ]

    return {
        **request_types,
        'values': filtered_values,
        'size': len(filtered_values)
    }


def format_request_types_text(request_types: dict, service_desk_name: str = "Service Desk", show_issue_types: bool = False) -> None:
    """
    Format request types as human-readable text.

    Args:
        request_types: Request types data
        service_desk_name: Service desk name for display
        show_issue_types: Show issue type IDs
    """
    values = request_types.get('values', [])

    if not values:
        print(f"No request types found for {service_desk_name}.")
        return

    print(f"Request Types for {service_desk_name}:")
    print()

    if show_issue_types:
        print(f"{'ID':<4} {'Name':<30} {'Description':<40} {'Issue Type':<15}")
        print(f"{'──':<4} {'────':<30} {'───────────':<40} {'──────────':<15}")

        for rt in values:
            rt_id = rt.get('id', '')
            name = rt.get('name', '')[:28]
            description = rt.get('description', '')[:38]
            issue_type_id = rt.get('issueTypeId', '')

            print(f"{rt_id:<4} {name:<30} {description:<40} {issue_type_id:<15}")
    else:
        print(f"{'ID':<4} {'Name':<30} {'Description':<50}")
        print(f"{'──':<4} {'────':<30} {'───────────':<50}")

        for rt in values:
            rt_id = rt.get('id', '')
            name = rt.get('name', '')[:28]
            description = rt.get('description', '')[:48]

            print(f"{rt_id:<4} {name:<30} {description:<50}")

    print()
    print(f"Total: {len(values)} request type{'s' if len(values) != 1 else ''}")


def format_request_types_json(request_types: dict) -> str:
    """
    Format request types as JSON.

    Args:
        request_types: Request types data

    Returns:
        JSON string
    """
    return format_json(request_types)


def main():
    parser = argparse.ArgumentParser(
        description='List request types for a JSM service desk',
        epilog='Example: python list_request_types.py 1'
    )

    parser.add_argument('service_desk_id',
                       help='Service desk ID')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')
    parser.add_argument('--filter', '-f',
                       help='Filter by name pattern')
    parser.add_argument('--show-issue-types', '-i',
                       action='store_true',
                       help='Show underlying JIRA issue types')
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
        # Fetch request types
        request_types = list_request_types(
            args.service_desk_id,
            start=args.start,
            limit=args.limit,
            profile=args.profile
        )

        # Apply filters
        if args.filter:
            request_types = filter_request_types(request_types, args.filter)

        # Get service desk name for display
        client = get_jira_client(args.profile)
        service_desk = client.get_service_desk(args.service_desk_id)
        service_desk_name = f"{service_desk.get('projectName', '')} ({service_desk.get('projectKey', '')})"
        client.close()

        # Output results
        if args.output == 'json':
            print(format_request_types_json(request_types))
        else:
            format_request_types_text(request_types, service_desk_name, args.show_issue_types)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
