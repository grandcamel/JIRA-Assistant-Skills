#!/usr/bin/env python3
"""
Get notification scheme details from JIRA.

Retrieves a notification scheme by ID or name, showing event configurations
and recipient mappings.

Usage:
    python get_notification_scheme.py 10000
    python get_notification_scheme.py 10000 --output json
    python get_notification_scheme.py 10000 --show-projects
    python get_notification_scheme.py --name "Default Notification Scheme"
    python get_notification_scheme.py 10000 --profile production
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError, NotFoundError, ValidationError
from notification_utils import format_recipient, get_event_name


def get_notification_scheme(
    client=None,
    scheme_id: Optional[str] = None,
    scheme_name: Optional[str] = None,
    show_projects: bool = False,
    profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get notification scheme details.

    Args:
        client: JiraClient instance (optional, created if not provided)
        scheme_id: Notification scheme ID
        scheme_name: Notification scheme name (alternative to ID)
        show_projects: If True, include projects using this scheme
        profile: JIRA profile to use

    Returns:
        Notification scheme object with events and notifications

    Raises:
        ValidationError: If neither ID nor name provided
        NotFoundError: If scheme not found
    """
    close_client = False
    if client is None:
        client = get_jira_client(profile)
        close_client = True

    try:
        # Resolve scheme ID from name if needed
        if not scheme_id and scheme_name:
            found = client.lookup_notification_scheme_by_name(scheme_name)
            if found:
                scheme_id = found.get('id')
            else:
                raise NotFoundError(
                    resource_type="Notification scheme",
                    resource_id=scheme_name
                )
        elif not scheme_id:
            raise ValidationError("Either scheme_id or scheme_name must be provided")

        # Get scheme details with expanded events
        result = client.get_notification_scheme(
            scheme_id,
            expand='notificationSchemeEvents'
        )

        # Add project count if requested
        if show_projects:
            project_mappings = client.get_notification_scheme_projects(
                notification_scheme_id=[scheme_id]
            )
            projects = project_mappings.get('values', [])
            result['projects'] = projects
            result['project_count'] = len(projects)

        return result

    finally:
        if close_client and hasattr(client, 'close'):
            client.close()


def format_text_output(result: Dict[str, Any], show_projects: bool = False) -> str:
    """
    Format result as human-readable text.

    Args:
        result: Notification scheme object
        show_projects: If True, include project count

    Returns:
        Formatted text string
    """
    output = ["Notification Scheme Details:", ""]

    output.append(f"ID:          {result.get('id', 'N/A')}")
    output.append(f"Name:        {result.get('name', 'N/A')}")
    output.append(f"Description: {result.get('description', 'N/A')}")
    output.append("")

    events = result.get('notificationSchemeEvents', [])

    if events:
        output.append("Event Configurations:")
        output.append("-" * 70)

        for event_config in events:
            event = event_config.get('event', {})
            event_name = event.get('name', get_event_name(event.get('id', 'unknown')))
            event_id = event.get('id', 'N/A')

            output.append(f"\nEvent: {event_name} (ID: {event_id})")
            output.append("  Recipients:")

            notifications = event_config.get('notifications', [])
            if notifications:
                for notification in notifications:
                    recipient_str = format_recipient(notification)
                    output.append(f"    - {recipient_str}")
            else:
                output.append("    (no recipients configured)")

        output.append("")
        output.append(f"Total: {len(events)} event(s) configured")
    else:
        output.append("No events configured for this scheme.")

    if show_projects and 'project_count' in result:
        output.append(f"Projects using this scheme: {result['project_count']}")

    return '\n'.join(output)


def format_json_output(result: Dict[str, Any]) -> str:
    """
    Format result as JSON.

    Args:
        result: Notification scheme object

    Returns:
        JSON string
    """
    return json.dumps(result, indent=2)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Get notification scheme details from JIRA',
        epilog='''
Examples:
    python get_notification_scheme.py 10000
    python get_notification_scheme.py 10000 --output json
    python get_notification_scheme.py 10000 --show-projects
    python get_notification_scheme.py --name "Default Notification Scheme"
    python get_notification_scheme.py 10000 --profile production
        '''
    )
    parser.add_argument('scheme_id', nargs='?',
                        help='Notification scheme ID')
    parser.add_argument('--name', '-n', dest='scheme_name',
                        help='Notification scheme name (alternative to ID)')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--show-projects', '-p', action='store_true',
                        help='Show projects using this scheme')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    if not args.scheme_id and not args.scheme_name:
        parser.error("Either scheme_id or --name must be provided")

    try:
        result = get_notification_scheme(
            scheme_id=args.scheme_id,
            scheme_name=args.scheme_name,
            show_projects=args.show_projects,
            profile=args.profile
        )

        if args.output == 'json':
            print(format_json_output(result))
        else:
            print(format_text_output(result, show_projects=args.show_projects))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
