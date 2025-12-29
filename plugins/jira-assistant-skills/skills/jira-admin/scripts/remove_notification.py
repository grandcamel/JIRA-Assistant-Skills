#!/usr/bin/env python3
"""
Remove a notification from a notification scheme.

Removes a specific notification (event-recipient mapping) from a scheme.

Usage:
    python remove_notification.py 10000 --notification-id 12
    python remove_notification.py 10000 --event "Issue created" --recipient Group:developers
    python remove_notification.py 10000 --notification-id 12 --force
    python remove_notification.py 10000 --notification-id 12 --dry-run
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError, NotFoundError
from notification_utils import (
    get_event_id,
    get_event_name,
    format_recipient,
    find_notification_by_event_and_recipient,
    parse_recipient_string
)


def find_notification_in_scheme(scheme: Dict[str, Any], notification_id: str) -> Optional[Dict[str, Any]]:
    """
    Find a notification by ID in a scheme.

    Args:
        scheme: Scheme object with notificationSchemeEvents
        notification_id: Notification ID to find

    Returns:
        Dict with event and notification info, or None
    """
    for event_config in scheme.get('notificationSchemeEvents', []):
        event = event_config.get('event', {})
        for notification in event_config.get('notifications', []):
            if str(notification.get('id')) == str(notification_id):
                return {
                    'event': event,
                    'notification': notification
                }
    return None


def remove_notification(
    client=None,
    scheme_id: str = None,
    notification_id: Optional[str] = None,
    event_name: Optional[str] = None,
    event_id: Optional[str] = None,
    recipient: Optional[str] = None,
    force: bool = False,
    confirmed: bool = True,
    dry_run: bool = False,
    profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    Remove a notification from a notification scheme.

    Args:
        client: JiraClient instance (optional, created if not provided)
        scheme_id: Notification scheme ID
        notification_id: Specific notification ID to remove
        event_name: Event name for lookup
        event_id: Event ID for lookup
        recipient: Recipient string for lookup (e.g., 'Group:developers')
        force: If True, bypass confirmation prompt
        confirmed: If False and not force, raise error requiring confirmation
        dry_run: If True, show what would be removed without removing
        profile: JIRA profile to use

    Returns:
        Dict with success status and removed notification details

    Raises:
        ValidationError: If required parameters missing
        NotFoundError: If notification not found
    """
    close_client = False
    if client is None:
        client = get_jira_client(profile)
        close_client = True

    try:
        # Get scheme details first
        scheme = client.get_notification_scheme(scheme_id, expand='notificationSchemeEvents')
        scheme_name = scheme.get('name', 'Unknown')

        # Find notification by ID or by event+recipient
        found_notification = None
        found_event = None

        if notification_id:
            result = find_notification_in_scheme(scheme, notification_id)
            if result:
                found_notification = result['notification']
                found_event = result['event']
            else:
                raise NotFoundError(
                    resource_type="Notification",
                    resource_id=notification_id
                )
        elif event_name or event_id:
            # Resolve event ID from name if needed
            if not event_id and event_name:
                event_id = get_event_id(event_name)
                if not event_id:
                    raise ValidationError(f"Unknown event name: {event_name}")

            if not recipient:
                raise ValidationError("--recipient is required when using --event")

            # Parse recipient
            try:
                parsed = parse_recipient_string(recipient)
            except ValueError as e:
                raise ValidationError(str(e))

            # Find the notification
            for event_config in scheme.get('notificationSchemeEvents', []):
                event = event_config.get('event', {})
                if str(event.get('id')) == str(event_id):
                    for notification in event_config.get('notifications', []):
                        if notification.get('notificationType') == parsed.get('notificationType'):
                            if parsed.get('parameter') is None or notification.get('parameter') == parsed.get('parameter'):
                                found_notification = notification
                                found_event = event
                                notification_id = str(notification.get('id'))
                                break
                    break

            if not found_notification:
                raise NotFoundError(
                    resource_type="Notification",
                    resource_id=f"{event_name or event_id}:{recipient}"
                )
        else:
            raise ValidationError("Either --notification-id or --event/--recipient must be provided")

        # Format notification info for output
        notification_info = format_recipient(found_notification)
        event_info = found_event.get('name', get_event_name(found_event.get('id', 'Unknown')))

        # Handle dry run
        if dry_run:
            return {
                'dry_run': True,
                'scheme_id': scheme_id,
                'scheme_name': scheme_name,
                'notification_id': notification_id,
                'event': event_info,
                'would_remove': notification_info
            }

        # Require confirmation unless force
        if not force and not confirmed:
            raise ValidationError(
                f"Removal requires confirmation. Use --force to bypass, or confirm interactively."
            )

        # Remove the notification
        client.delete_notification_from_scheme(scheme_id, notification_id)

        return {
            'success': True,
            'scheme_id': scheme_id,
            'scheme_name': scheme_name,
            'notification_id': notification_id,
            'event': event_info,
            'removed': notification_info
        }

    finally:
        if close_client and hasattr(client, 'close'):
            client.close()


def format_text_output(result: Dict[str, Any]) -> str:
    """
    Format result as human-readable text.

    Args:
        result: Remove result object

    Returns:
        Formatted text string
    """
    output = []
    scheme_id = result.get('scheme_id', 'N/A')
    scheme_name = result.get('scheme_name', 'N/A')
    event = result.get('event', 'N/A')

    if result.get('dry_run'):
        output.append(f"[DRY RUN] Would remove notification from scheme {scheme_id}")
        output.append("")
        output.append(f"Scheme:    {scheme_name}")
        output.append(f"Event:     {event}")
        output.append(f"Recipient: {result.get('would_remove', 'N/A')}")
        output.append("")
        output.append("No changes made (dry run mode)")
    else:
        output.append(f"Notification Removed from Scheme {scheme_id}")
        output.append("-" * 40)
        output.append(f"Scheme:    {scheme_name}")
        output.append(f"Event:     {event}")
        output.append(f"Removed:   {result.get('removed', 'N/A')}")
        output.append("")
        output.append(f"Success! Notification removed from scheme.")

    return '\n'.join(output)


def format_json_output(result: Dict[str, Any]) -> str:
    """
    Format result as JSON.

    Args:
        result: Remove result object

    Returns:
        JSON string
    """
    return json.dumps(result, indent=2)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Remove a notification from a notification scheme',
        epilog='''
Examples:
    python remove_notification.py 10000 --notification-id 12
    python remove_notification.py 10000 --event "Issue created" --recipient Group:developers
    python remove_notification.py 10000 --notification-id 12 --force
    python remove_notification.py 10000 --notification-id 12 --dry-run
        '''
    )
    parser.add_argument('scheme_id', help='Notification scheme ID')
    parser.add_argument('--notification-id', dest='notification_id',
                        help='Notification ID to remove')
    parser.add_argument('--event', '-e', dest='event_name',
                        help='Event name (e.g., "Issue created")')
    parser.add_argument('--event-id', dest='event_id',
                        help='Event ID')
    parser.add_argument('--recipient', '-r',
                        help='Recipient to remove (e.g., Group:developers)')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force removal without confirmation')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be removed without removing')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--profile', '-p', help='JIRA profile to use')

    args = parser.parse_args()

    if not args.notification_id and not (args.event_name or args.event_id):
        parser.error("Either --notification-id or --event/--recipient must be provided")

    try:
        # Interactive confirmation if not forced
        confirmed = args.force
        if not args.force and not args.dry_run:
            print(f"This will remove a notification from scheme {args.scheme_id}.")
            response = input("Are you sure? (yes/no): ")
            confirmed = response.lower() in ('yes', 'y')

        result = remove_notification(
            scheme_id=args.scheme_id,
            notification_id=args.notification_id,
            event_name=args.event_name,
            event_id=args.event_id,
            recipient=args.recipient,
            force=args.force,
            confirmed=confirmed,
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
