"""
Utility functions for notification scheme operations.

Provides helper functions for:
- Event ID/name lookup
- Recipient type validation
- Notification formatting
"""

from typing import Any

# Common notification events with their IDs
# Note: Event IDs may vary by JIRA instance
NOTIFICATION_EVENTS = {
    "1": "Issue created",
    "2": "Issue updated",
    "3": "Issue assigned",
    "4": "Issue resolved",
    "5": "Issue closed",
    "6": "Issue commented",
    "7": "Issue reopened",
    "8": "Issue deleted",
    "9": "Issue moved",
    "10": "Work logged",
    "11": "Work started",
    "12": "Work stopped",
    "13": "Generic event",
    "14": "Issue comment edited",
    "15": "Issue worklog updated",
    "16": "Issue worklog deleted",
}

# Reverse mapping for name to ID lookup
EVENT_NAME_TO_ID = {v.lower(): k for k, v in NOTIFICATION_EVENTS.items()}

# Valid recipient types and whether they require a parameter
RECIPIENT_TYPES = {
    "CurrentAssignee": False,
    "Reporter": False,
    "CurrentUser": False,
    "ProjectLead": False,
    "ComponentLead": False,
    "User": True,  # Requires user account ID
    "Group": True,  # Requires group name
    "ProjectRole": True,  # Requires project role ID
    "AllWatchers": False,
    "UserCustomField": True,  # Requires custom field ID
    "GroupCustomField": True,  # Requires custom field ID
}

# Human-readable recipient type names
RECIPIENT_TYPE_DISPLAY = {
    "CurrentAssignee": "Current Assignee",
    "Reporter": "Reporter",
    "CurrentUser": "Current User",
    "ProjectLead": "Project Lead",
    "ComponentLead": "Component Lead",
    "User": "User",
    "Group": "Group",
    "ProjectRole": "Project Role",
    "AllWatchers": "All Watchers",
    "UserCustomField": "User Custom Field",
    "GroupCustomField": "Group Custom Field",
}


def get_event_name(event_id: str) -> str:
    """
    Get event name by ID.

    Args:
        event_id: Event ID string

    Returns:
        Event name or 'Unknown Event' if not found
    """
    return NOTIFICATION_EVENTS.get(str(event_id), f"Unknown Event ({event_id})")


def get_event_id(event_name: str) -> str | None:
    """
    Get event ID by name (case-insensitive).

    Args:
        event_name: Event name

    Returns:
        Event ID string or None if not found
    """
    return EVENT_NAME_TO_ID.get(event_name.lower())


def validate_recipient_type(recipient_type: str) -> bool:
    """
    Validate that a recipient type is valid.

    Args:
        recipient_type: Recipient type string

    Returns:
        True if valid, False otherwise
    """
    return recipient_type in RECIPIENT_TYPES


def recipient_requires_parameter(recipient_type: str) -> bool:
    """
    Check if a recipient type requires a parameter.

    Args:
        recipient_type: Recipient type string

    Returns:
        True if parameter required, False otherwise
    """
    return RECIPIENT_TYPES.get(recipient_type, False)


def format_recipient(notification: dict[str, Any]) -> str:
    """
    Format a notification recipient for display.

    Args:
        notification: Notification object with 'notificationType' and optional 'parameter'

    Returns:
        Human-readable recipient string
    """
    ntype = notification.get("notificationType", "Unknown")
    param = notification.get("parameter")
    display_name = RECIPIENT_TYPE_DISPLAY.get(ntype, ntype)

    if param:
        return f"{display_name}: {param}"
    return display_name


def parse_recipient_string(recipient_str: str) -> dict[str, Any]:
    """
    Parse a recipient string like 'Group:developers' or 'CurrentAssignee'.

    Args:
        recipient_str: Recipient specification string

    Returns:
        Dictionary with 'notificationType' and optional 'parameter'

    Raises:
        ValueError: If recipient type is invalid
    """
    if ":" in recipient_str:
        parts = recipient_str.split(":", 1)
        ntype = parts[0]
        param = parts[1]
    else:
        ntype = recipient_str
        param = None

    if not validate_recipient_type(ntype):
        valid_types = ", ".join(RECIPIENT_TYPES.keys())
        raise ValueError(f"Invalid recipient type: {ntype}. Valid types: {valid_types}")

    if recipient_requires_parameter(ntype) and not param:
        raise ValueError(
            f"Recipient type '{ntype}' requires a parameter (e.g., {ntype}:value)"
        )

    result = {"notificationType": ntype}
    if param:
        result["parameter"] = param
    return result


def count_events(scheme: dict[str, Any]) -> int:
    """
    Count the number of events configured in a notification scheme.

    Args:
        scheme: Notification scheme object

    Returns:
        Number of events with notifications configured
    """
    events = scheme.get("notificationSchemeEvents", [])
    return len(events)


def count_notifications(scheme: dict[str, Any]) -> int:
    """
    Count the total number of notifications in a scheme.

    Args:
        scheme: Notification scheme object

    Returns:
        Total number of notifications across all events
    """
    total = 0
    events = scheme.get("notificationSchemeEvents", [])
    for event in events:
        total += len(event.get("notifications", []))
    return total


def format_scheme_summary(scheme: dict[str, Any]) -> dict[str, Any]:
    """
    Create a summary of a notification scheme for table display.

    Args:
        scheme: Notification scheme object

    Returns:
        Dictionary with id, name, description, event_count
    """
    return {
        "id": scheme.get("id", "N/A"),
        "name": scheme.get("name", "N/A"),
        "description": scheme.get("description", "")[:50]
        if scheme.get("description")
        else "",
        "events": count_events(scheme),
    }


def build_notification_payload(event_id: str, recipients: list[str]) -> dict[str, Any]:
    """
    Build a notification scheme event payload for API calls.

    Args:
        event_id: Event ID string
        recipients: List of recipient strings (e.g., ['CurrentAssignee', 'Group:devs'])

    Returns:
        Dictionary ready for notificationSchemeEvents

    Raises:
        ValueError: If any recipient is invalid
    """
    notifications = []
    for recipient in recipients:
        notifications.append(parse_recipient_string(recipient))

    return {"event": {"id": event_id}, "notifications": notifications}


def find_notification_by_event_and_recipient(
    scheme: dict[str, Any],
    event_id: str,
    recipient_type: str,
    parameter: str | None = None,
) -> dict[str, Any] | None:
    """
    Find a specific notification in a scheme by event and recipient.

    Args:
        scheme: Notification scheme object with 'notificationSchemeEvents'
        event_id: Event ID to find
        recipient_type: Notification type to match
        parameter: Optional parameter to match

    Returns:
        Notification object if found, None otherwise
    """
    events = scheme.get("notificationSchemeEvents", [])
    for event in events:
        if str(event.get("event", {}).get("id")) == str(event_id):
            for notification in event.get("notifications", []):
                if notification.get("notificationType") == recipient_type:
                    if parameter is None or notification.get("parameter") == parameter:
                        return notification
    return None
