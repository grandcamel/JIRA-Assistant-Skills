#!/usr/bin/env python3
"""
Create a new notification scheme in JIRA.

Creates a notification scheme with optional event configurations.

Usage:
    python create_notification_scheme.py --name "New Scheme" --description "Description"
    python create_notification_scheme.py --template notification_scheme.json
    python create_notification_scheme.py --name "Dev Scheme" --event "Issue created" --notify CurrentAssignee --notify Group:developers
    python create_notification_scheme.py --template scheme.json --dry-run
    python create_notification_scheme.py --name "Prod Scheme"
"""

import argparse
import json
import sys
from typing import Any

from notification_utils import (
    format_recipient,
    get_event_id,
    parse_recipient_string,
)

from jira_assistant_skills_lib import (
    ConflictError,
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
)


def create_notification_scheme(
    client=None,
    name: str | None = None,
    description: str | None = None,
    events: list[dict[str, Any]] | None = None,
    template_file: str | None = None,
    dry_run: bool = False,
    check_duplicate: bool = False,
) -> dict[str, Any]:
    """
    Create a new notification scheme.

    Args:
        client: JiraClient instance (optional, created if not provided)
        name: Scheme name (required if not using template)
        description: Scheme description
        events: List of event configurations:
            [{'event_id': '1', 'recipients': ['CurrentAssignee', 'Group:devs']}]
            or [{'event_name': 'Issue created', 'recipients': [...]}]
        template_file: Path to JSON template file
        dry_run: If True, validate but don't create
        check_duplicate: If True, check if name already exists

    Returns:
        Created notification scheme object (or dry_run preview)

    Raises:
        ValidationError: If required fields missing or invalid
        ConflictError: If scheme name already exists
    """
    close_client = False
    if client is None:
        client = get_jira_client()
        close_client = True

    try:
        # Load from template if provided
        if template_file:
            with open(template_file) as f:
                template_data = json.load(f)
            name = template_data.get("name", name)
            description = template_data.get("description", description)
            # Use template's notificationSchemeEvents directly
            scheme_events = template_data.get("notificationSchemeEvents", [])
        else:
            scheme_events = []

        # Validate required fields
        if not name or not name.strip():
            raise ValidationError("Scheme name is required and cannot be empty")

        name = name.strip()

        # Check for duplicate name if requested
        if check_duplicate:
            existing = client.lookup_notification_scheme_by_name(name)
            if existing:
                raise ConflictError(
                    f"Notification scheme with name '{name}' already exists (ID: {existing.get('id')})"
                )

        # Build events from events parameter if provided
        if events and not scheme_events:
            scheme_events = []
            for event_config in events:
                event_id = event_config.get("event_id")
                event_name = event_config.get("event_name")
                recipients = event_config.get("recipients", [])

                # Resolve event ID from name if needed
                if not event_id and event_name:
                    event_id = get_event_id(event_name)
                    if not event_id:
                        raise ValidationError(f"Unknown event name: {event_name}")

                # Validate and build notifications
                notifications = []
                for recipient in recipients:
                    try:
                        notification = parse_recipient_string(recipient)
                        notifications.append(notification)
                    except ValueError as e:
                        raise ValidationError(str(e))

                scheme_events.append(
                    {"event": {"id": event_id}, "notifications": notifications}
                )

        # Build request data
        data = {"name": name}

        if description:
            data["description"] = description

        if scheme_events:
            data["notificationSchemeEvents"] = scheme_events

        # Handle dry run
        if dry_run:
            return {"dry_run": True, "would_create": data}

        # Create the scheme
        result = client.create_notification_scheme(data)
        return result

    finally:
        if close_client and hasattr(client, "close"):
            client.close()


def format_text_output(result: dict[str, Any]) -> str:
    """
    Format result as human-readable text.

    Args:
        result: Created scheme object or dry_run preview

    Returns:
        Formatted text string
    """
    output = []

    if result.get("dry_run"):
        output.append("[DRY RUN] Would create notification scheme:")
        output.append("")
        data = result.get("would_create", {})
        output.append(f"Name:        {data.get('name', 'N/A')}")
        output.append(f"Description: {data.get('description', 'N/A')}")

        events = data.get("notificationSchemeEvents", [])
        if events:
            output.append("")
            output.append("Event Configurations:")
            for event_config in events:
                event_id = event_config.get("event", {}).get("id", "N/A")
                output.append(f"  Event ID: {event_id}")
                for notification in event_config.get("notifications", []):
                    output.append(f"    - {format_recipient(notification)}")

        output.append("")
        output.append("No changes made (dry run mode)")
    else:
        output.append("Notification Scheme Created:")
        output.append("-" * 40)
        output.append(f"ID:          {result.get('id', 'N/A')}")
        output.append(f"Name:        {result.get('name', 'N/A')}")
        output.append(f"Description: {result.get('description', 'N/A')}")
        output.append("")
        output.append(
            f"Success! Notification scheme created with ID: {result.get('id', 'N/A')}"
        )
        output.append("")
        output.append("To add more notifications:")
        output.append(
            f'  python add_notification.py {result.get("id", "SCHEME_ID")} --event "Issue created" --notify CurrentAssignee'
        )

    return "\n".join(output)


def format_json_output(result: dict[str, Any]) -> str:
    """
    Format result as JSON.

    Args:
        result: Created scheme object

    Returns:
        JSON string
    """
    return json.dumps(result, indent=2)


def main(argv: list[str] | None = None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Create a new notification scheme in JIRA",
        epilog="""
Examples:
    python create_notification_scheme.py --name "New Scheme" --description "Description"
    python create_notification_scheme.py --template notification_scheme.json
    python create_notification_scheme.py --name "Dev Scheme" --event "Issue created" --notify CurrentAssignee --notify Group:developers
    python create_notification_scheme.py --template scheme.json --dry-run
        """,
    )
    parser.add_argument("--name", "-n", help="Notification scheme name")
    parser.add_argument("--description", "-d", help="Notification scheme description")
    parser.add_argument(
        "--template", "-t", dest="template_file", help="JSON template file path"
    )
    parser.add_argument(
        "--event", "-e", help="Event name or ID to add notification for"
    )
    parser.add_argument(
        "--notify",
        action="append",
        dest="recipients",
        help="Recipient (e.g., CurrentAssignee, Group:developers)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be created without creating",
    )
    parser.add_argument(
        "--check-duplicate",
        action="store_true",
        help="Check if scheme name already exists",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    if not args.name and not args.template_file:
        parser.error("Either --name or --template must be provided")

    try:
        # Build events from CLI args if provided
        events = None
        if args.event and args.recipients:
            events = [{"event_name": args.event, "recipients": args.recipients}]

        result = create_notification_scheme(
            name=args.name,
            description=args.description,
            template_file=args.template_file,
            events=events,
            dry_run=args.dry_run,
            check_duplicate=args.check_duplicate,
        )

        if args.output == "json":
            print(format_json_output(result))
        else:
            print(format_text_output(result))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
