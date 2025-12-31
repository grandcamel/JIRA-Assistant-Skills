#!/usr/bin/env python3
"""
Get JSM service desk details by ID.

Usage:
    python get_service_desk.py 1
    python get_service_desk.py 1 --output json
    python get_service_desk.py 1 --show-request-types
"""

import sys
import os
import argparse
import json
from pathlib import Path


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError
from jira_assistant_skills_lib import format_json


def get_service_desk(service_desk_id: str, profile: str = None) -> dict:
    """
    Get JSM service desk details by ID.

    Args:
        service_desk_id: Service desk ID
        profile: JIRA profile to use

    Returns:
        Service desk data
    """
    client = get_jira_client(profile)
    service_desk = client.get_service_desk(service_desk_id)
    client.close()

    return service_desk


def format_service_desk_text(service_desk: dict, show_request_types: bool = False, client = None) -> None:
    """
    Format service desk as human-readable text.

    Args:
        service_desk: Service desk data
        show_request_types: Show request type count
        client: Optional JiraClient for request type lookup
    """
    print("Service Desk Details:")
    print()
    print(f"ID:           {service_desk.get('id', '')}")
    print(f"Project ID:   {service_desk.get('projectId', '')}")
    print(f"Project Key:  {service_desk.get('projectKey', '')}")
    print(f"Project Name: {service_desk.get('projectName', '')}")

    if show_request_types and client:
        try:
            request_types = client.get_request_types(service_desk.get('id'))
            count = len(request_types.get('values', []))
            print()
            print(f"Request Types: {count} available")
            print(f"Use: python list_request_types.py {service_desk.get('id')}")
        except Exception:
            pass


def format_service_desk_json(service_desk: dict) -> str:
    """
    Format service desk as JSON.

    Args:
        service_desk: Service desk data

    Returns:
        JSON string
    """
    return format_json(service_desk)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Get JSM service desk details by ID',
        epilog='Example: python get_service_desk.py 1'
    )

    parser.add_argument('service_desk_id',
                       help='Service desk ID')
    parser.add_argument('--output', '-o',
                       choices=['text', 'json'],
                       default='text',
                       help='Output format (default: text)')
    parser.add_argument('--show-request-types', '-r',
                       action='store_true',
                       help='Show request type count')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args(argv)

    try:
        # Fetch service desk
        service_desk = get_service_desk(
            args.service_desk_id,
            profile=args.profile
        )

        # Output results
        if args.output == 'json':
            print(format_service_desk_json(service_desk))
        else:
            client = None
            if args.show_request_types:
                client = get_jira_client(args.profile)
            format_service_desk_text(service_desk, args.show_request_types, client)
            if client:
                client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
