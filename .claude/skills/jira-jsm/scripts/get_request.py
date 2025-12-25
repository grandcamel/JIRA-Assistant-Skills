#!/usr/bin/env python3
"""
Get JSM service request details.

Usage:
    python get_request.py SD-101
    python get_request.py SD-101 --show-sla
    python get_request.py SD-101 --show-participants
    python get_request.py SD-101 --output json
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError, NotFoundError
from formatters import print_success


def get_service_request(issue_key: str, show_sla: bool = False,
                       show_participants: bool = False,
                       profile: Optional[str] = None) -> Dict[str, Any]:
    """
    Get service request details.

    Args:
        issue_key: Request key (e.g., 'SD-101')
        show_sla: Include SLA information
        show_participants: Include participant list
        profile: JIRA profile to use

    Returns:
        Request data

    Raises:
        NotFoundError: If request doesn't exist
    """
    expand = []
    if show_sla:
        expand.append('sla')
    if show_participants:
        expand.append('participant')

    with get_jira_client(profile) as client:
        return client.get_request(issue_key, expand=expand if expand else None)


def format_sla_time(millis: int) -> str:
    """Format milliseconds to human-readable time."""
    hours = millis // 3600000
    minutes = (millis % 3600000) // 60000

    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def format_request_text(request: Dict[str, Any], show_fields: bool = False) -> str:
    """Format request as text output."""
    lines = []

    lines.append(f"\nRequest: {request.get('issueKey')}")
    lines.append("=" * 60)
    lines.append("")

    # Request type
    req_type = request.get('requestType', {})
    lines.append(f"Request Type: {req_type.get('name', 'N/A')}")

    # Service desk
    lines.append(f"Service Desk ID: {request.get('serviceDeskId', 'N/A')}")

    # Current status
    status = request.get('currentStatus', {})
    lines.append(f"Status: {status.get('status', 'N/A')} ({status.get('statusCategory', 'N/A')})")
    lines.append("")

    # Field values
    if show_fields:
        lines.append("Fields:")
        for field in request.get('requestFieldValues', []):
            label = field.get('label', field.get('fieldId'))
            value = field.get('value', 'N/A')
            lines.append(f"  {label}: {value}")
        lines.append("")

    # Reporter
    reporter = request.get('reporter', {})
    lines.append(f"Reporter: {reporter.get('emailAddress', 'N/A')}")

    # Dates
    created = request.get('createdDate', {})
    lines.append(f"Created: {created.get('friendly', 'N/A')}")
    lines.append("")

    # SLA information
    if 'sla' in request:
        lines.append("SLA Information:")
        for sla_metric in request['sla'].get('values', []):
            name = sla_metric.get('name')
            ongoing = sla_metric.get('ongoingCycle', {})

            if ongoing.get('breached'):
                status_icon = "⚠ BREACHED"
            else:
                remaining = ongoing.get('remainingTime', {}).get('millis', 0)
                if remaining > 0:
                    status_icon = f"⏱ {format_sla_time(remaining)} remaining"
                else:
                    status_icon = "✓ Met"

            lines.append(f"  {name}: {status_icon}")
        lines.append("")

    # Links
    links = request.get('_links', {})
    lines.append("Links:")
    if 'web' in links:
        lines.append(f"  Customer Portal: {links['web']}")
    if 'agent' in links:
        lines.append(f"  Agent View: {links['agent']}")

    return '\n'.join(lines)


def format_request_json(request: Dict[str, Any]) -> str:
    """Format request as JSON output."""
    return json.dumps(request, indent=2)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Get JSM service request details',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic usage:
    %(prog)s SD-101

  With SLA information:
    %(prog)s SD-101 --show-sla

  With participants:
    %(prog)s SD-101 --show-participants

  All details:
    %(prog)s SD-101 --full

  JSON output:
    %(prog)s SD-101 --output json
        """
    )

    parser.add_argument('request_key',
                        help='Request key (e.g., SD-101)')
    parser.add_argument('--show-sla', action='store_true',
                        help='Include SLA information')
    parser.add_argument('--show-participants', action='store_true',
                        help='Include participant list')
    parser.add_argument('--full', action='store_true',
                        help='Show all details (SLA + participants + fields)')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile',
                        help='JIRA profile to use from config')

    args = parser.parse_args()

    try:
        show_sla = args.show_sla or args.full
        show_participants = args.show_participants or args.full

        request = get_service_request(
            issue_key=args.request_key,
            show_sla=show_sla,
            show_participants=show_participants,
            profile=args.profile
        )

        if args.output == 'json':
            print(format_request_json(request))
        else:
            print(format_request_text(request, show_fields=args.full))

        return 0

    except NotFoundError as e:
        print_error(f"Request not found: {e}")
        return 1
    except JiraError as e:
        print_error(f"Failed to get request: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
