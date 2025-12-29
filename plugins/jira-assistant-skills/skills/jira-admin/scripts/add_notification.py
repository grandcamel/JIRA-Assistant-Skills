#!/usr/bin/env python3
"""
Add notifications to a notification scheme.

Adds event-to-recipient mappings to an existing notification scheme.

Usage:
    python add_notification.py 10000 --event "Issue created" --notify CurrentAssignee
    python add_notification.py 10000 --event "Issue created" --notify Group:developers
    python add_notification.py 10000 --event-id 1 --notify CurrentAssignee --notify Reporter --notify AllWatchers
    python add_notification.py 10000 --event "Issue resolved" --notify ProjectRole:10002
    python add_notification.py 10000 --event "Issue created" --notify Reporter --dry-run
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional, List


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError
from notification_utils import (
    parse_recipient_string,
    get_event_id,
    get_event_name,
    format_recipient
)


def add_notification(
    client=None,
    scheme_id: str = None,
    event_id: Optional[str] = None,
    event_name: Optional[str] = None,
    recipients: List[str] = None,
    dry_run: bool = False,
    profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add notifications to a notification scheme.

    Args:
        client: JiraClient instance (optional, created if not provided)
        scheme_id: Notification scheme ID
        event_id: Event ID to add notifications for
        event_name: Event name (alternative to event_id)
        recipients: List of recipient strings (e.g., ['CurrentAssignee', 'Group:devs'])
        dry_run: If True, validate but don't add
        profile: JIRA profile to use

    Returns:
        Dict with success status and added notifications

    Raises:
        ValidationError: If required fields missing or invalid
    """
    close_client = False
    if client is None:
        client = get_jira_client(profile)
        close_client = True

    try:
        # Validate recipients are provided
        if not recipients or len(recipients) == 0:
            raise ValidationError("At least one recipient must be provided")

        # Resolve event ID from name if needed
        if not event_id and event_name:
            event_id = get_event_id(event_name)
            if not event_id:
                raise ValidationError(f"Unknown event name: {event_name}")
        elif not event_id:
            raise ValidationError("Either event_id or event_name must be provided")

        # Validate and parse recipients
        notifications = []
        for recipient in recipients:
            try:
                notification = parse_recipient_string(recipient)
                notifications.append(notification)
            except ValueError as e:
                raise ValidationError(str(e))

        # Build the payload
        event_data = {
            'notificationSchemeEvents': [
                {
                    'event': {'id': event_id},
                    'notifications': notifications
                }
            ]
        }

        # Get current scheme for reference
        current = client.get_notification_scheme(scheme_id, expand='notificationSchemeEvents')
        scheme_name = current.get('name', 'Unknown')

        # Handle dry run
        if dry_run:
            return {
                'dry_run': True,
                'scheme_id': scheme_id,
                'scheme_name': scheme_name,
                'event_id': event_id,
                'event_name': get_event_name(event_id),
                'would_add': [format_recipient(n) for n in notifications]
            }

        # Add the notifications
        client.add_notification_to_scheme(scheme_id, event_data)

        return {
            'success': True,
            'scheme_id': scheme_id,
            'scheme_name': scheme_name,
            'event_id': event_id,
            'event_name': get_event_name(event_id),
            'added': [format_recipient(n) for n in notifications]
        }

    finally:
        if close_client and hasattr(client, 'close'):
            client.close()


def format_text_output(result: Dict[str, Any]) -> str:
    """
    Format result as human-readable text.

    Args:
        result: Add notification result

    Returns:
        Formatted text string
    """
    output = []
    scheme_id = result.get('scheme_id', 'N/A')
    scheme_name = result.get('scheme_name', 'N/A')
    event_id = result.get('event_id', 'N/A')
    event_name = result.get('event_name', get_event_name(event_id))

    if result.get('dry_run'):
        output.append(f"[DRY RUN] Would add notifications to scheme {scheme_id}")
        output.append("")
        output.append(f"Scheme:    {scheme_name}")
        output.append(f"Event:     {event_name} (ID: {event_id})")
        output.append("Recipients to add:")

        for recipient in result.get('would_add', []):
            output.append(f"  - {recipient}")

        output.append("")
        output.append("No changes made (dry run mode)")
    else:
        output.append(f"Notification Added to Scheme {scheme_id}")
        output.append("-" * 40)
        output.append(f"Scheme:    {scheme_name}")
        output.append(f"Event:     {event_name} (ID: {event_id})")
        output.append("Recipients added:")

        for recipient in result.get('added', []):
            output.append(f"  - {recipient}")

        output.append("")
        output.append(f"Success! Notifications added to event \"{event_name}\"")

    return '\n'.join(output)


def format_json_output(result: Dict[str, Any]) -> str:
    """
    Format result as JSON.

    Args:
        result: Add notification result

    Returns:
        JSON string
    """
    return json.dumps(result, indent=2)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Add notifications to a notification scheme',
        epilog='''
Examples:
    python add_notification.py 10000 --event "Issue created" --notify CurrentAssignee
    python add_notification.py 10000 --event "Issue created" --notify Group:developers
    python add_notification.py 10000 --event-id 1 --notify CurrentAssignee --notify Reporter --notify AllWatchers
    python add_notification.py 10000 --event "Issue resolved" --notify ProjectRole:10002
    python add_notification.py 10000 --event "Issue created" --notify Reporter --dry-run
        '''
    )
    parser.add_argument('scheme_id', help='Notification scheme ID')
    parser.add_argument('--event', '-e', dest='event_name',
                        help='Event name (e.g., "Issue created")')
    parser.add_argument('--event-id', dest='event_id',
                        help='Event ID (alternative to --event)')
    parser.add_argument('--notify', '-n', action='append', dest='recipients',
                        help='Recipient (e.g., CurrentAssignee, Group:developers)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview what would be added without adding')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile', '-p', help='JIRA profile to use')

    args = parser.parse_args()

    if not args.event_name and not args.event_id:
        parser.error("Either --event or --event-id must be provided")

    if not args.recipients:
        parser.error("At least one --notify must be provided")

    try:
        result = add_notification(
            scheme_id=args.scheme_id,
            event_id=args.event_id,
            event_name=args.event_name,
            recipients=args.recipients,
            dry_run=args.dry_run,
            profile=args.profile
        )

        if args.output == 'json':
            print(format_json_output(result))
        else:
            print(format_text_output(result))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
