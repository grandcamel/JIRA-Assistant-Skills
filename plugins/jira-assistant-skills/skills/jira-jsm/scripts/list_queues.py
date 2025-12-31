#!/usr/bin/env python3
"""
List JSM service desk queues.

Usage:
    python list_queues.py --service-desk 1
    python list_queues.py --service-desk 1 --show-jql
    python list_queues.py --service-desk 1 --output json
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError


def list_queues(service_desk_id: int, profile: Optional[str] = None) -> Dict[str, Any]:
    """List queues for a service desk."""
    with get_jira_client(profile) as client:
        return client.get_service_desk_queues(service_desk_id)


def format_queues_text(queues_data: Dict[str, Any], show_jql: bool = False) -> str:
    """Format queues as text."""
    lines = []
    queues = queues_data.get('values', [])

    lines.append(f"\nQueues: {len(queues)} total")
    lines.append("=" * 80)
    lines.append("")

    for queue in queues:
        queue_id = queue.get('id')
        name = queue.get('name')
        jql = queue.get('jql', 'N/A')

        lines.append(f"[{queue_id}] {name}")
        if show_jql:
            lines.append(f"  JQL: {jql}")

    return '\n'.join(lines)


def format_queues_json(queues_data: Dict[str, Any]) -> str:
    """Format queues as JSON."""
    return json.dumps(queues_data, indent=2)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(description='List JSM service desk queues')
    parser.add_argument('--service-desk', type=int, required=True, help='Service desk ID')
    parser.add_argument('--show-jql', action='store_true', help='Show JQL queries')
    parser.add_argument('--output', choices=['text', 'json'], default='text')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args(argv)

    try:
        queues = list_queues(args.service_desk, args.profile)

        if args.output == 'json':
            print(format_queues_json(queues))
        else:
            print(format_queues_text(queues, args.show_jql))

        return 0

    except JiraError as e:
        print_error(f"Failed to list queues: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
