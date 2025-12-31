#!/usr/bin/env python3
"""
Get JSM service request SLA information.

Usage:
    python get_sla.py SD-123
    python get_sla.py SD-123 --sla-id 1
    python get_sla.py SD-123 --output json
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any, List


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, NotFoundError
from jira_assistant_skills_lib import print_success
from jira_assistant_skills_lib import (
    format_sla_time, format_duration, get_sla_status_emoji,
    get_sla_status_text, is_sla_at_risk
)


def get_slas(issue_key: str, sla_id: Optional[str] = None,
             profile: Optional[str] = None) -> Dict[str, Any]:
    """
    Get SLA information for a service request.

    Args:
        issue_key: Request key (e.g., 'SD-123')
        sla_id: Specific SLA ID to retrieve (optional)
        profile: JIRA profile to use

    Returns:
        SLA data

    Raises:
        NotFoundError: If request doesn't exist
    """
    with get_jira_client(profile) as client:
        if sla_id:
            return client.get_request_sla(issue_key, sla_id)
        else:
            return client.get_request_slas(issue_key)


def format_sla_text(sla_data: Dict[str, Any], show_details: bool = True) -> str:
    """Format SLA data as text output."""
    lines = []

    # Check if this is a single SLA or list of SLAs
    if 'values' in sla_data:
        # Multiple SLAs
        slas = sla_data.get('values', [])
        lines.append(f"\nSLAs: {len(slas)} metrics")
        lines.append("=" * 80)
        lines.append("")

        for sla in slas:
            lines.extend(_format_single_sla(sla, show_details))
            lines.append("")
    else:
        # Single SLA
        lines.extend(_format_single_sla(sla_data, show_details))

    return '\n'.join(lines)


def _format_single_sla(sla: Dict[str, Any], show_details: bool = True) -> List[str]:
    """Format a single SLA metric."""
    lines = []

    name = sla.get('name', 'Unknown SLA')
    emoji = get_sla_status_emoji(sla)
    status = get_sla_status_text(sla)

    lines.append(f"{emoji} {name}: {status}")

    if show_details:
        # Ongoing cycle
        ongoing = sla.get('ongoingCycle')
        if ongoing:
            goal = format_duration(ongoing.get('goalDuration'))
            elapsed = format_duration(ongoing.get('elapsedTime'))
            remaining = format_duration(ongoing.get('remainingTime'))
            breach_time = format_sla_time(ongoing.get('breachTime'))

            lines.append(f"  Goal:       {goal}")
            lines.append(f"  Elapsed:    {elapsed}")
            lines.append(f"  Remaining:  {remaining}")
            lines.append(f"  Breach at:  {breach_time}")

            if ongoing.get('paused'):
                lines.append("  Status:     ⏸ Paused")

        # Completed cycles
        completed = sla.get('completedCycles', [])
        if completed:
            last = completed[-1]
            goal = format_duration(last.get('goalDuration'))
            elapsed = format_duration(last.get('elapsedTime'))
            stop_time = format_sla_time(last.get('stopTime'))

            lines.append(f"  Completed:  {stop_time}")
            lines.append(f"  Goal:       {goal}")
            lines.append(f"  Actual:     {elapsed}")

    return lines


def format_sla_json(sla_data: Dict[str, Any]) -> str:
    """Format SLA data as JSON output."""
    return json.dumps(sla_data, indent=2)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Get JSM service request SLA information',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Get all SLAs:
    %(prog)s SD-123

  Get specific SLA:
    %(prog)s SD-123 --sla-id 1

  JSON output:
    %(prog)s SD-123 --output json
        """
    )

    parser.add_argument('request_key',
                        help='Request key (e.g., SD-123)')
    parser.add_argument('--sla-id',
                        help='Specific SLA metric ID')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile',
                        help='JIRA profile to use from config')

    args = parser.parse_args(argv)

    try:
        sla_data = get_slas(
            issue_key=args.request_key,
            sla_id=args.sla_id,
            profile=args.profile
        )

        if args.output == 'json':
            print(format_sla_json(sla_data))
        else:
            print(format_sla_text(sla_data))

        return 0

    except NotFoundError as e:
        print_error(f"Request not found: {e}")
        return 1
    except JiraError as e:
        print_error(f"Failed to get SLA: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
