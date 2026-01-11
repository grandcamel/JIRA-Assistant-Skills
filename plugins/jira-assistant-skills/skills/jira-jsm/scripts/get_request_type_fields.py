#!/usr/bin/env python3
"""
Get fields for a JSM request type.

Usage:
    python get_request_type_fields.py 1 25
    python get_request_type_fields.py 1 25 --output json
    python get_request_type_fields.py 1 25 --required-only
    python get_request_type_fields.py 1 25 --show-valid-values
"""

import argparse
import sys

from jira_assistant_skills_lib import (
    JiraError,
    format_json,
    get_jira_client,
    print_error,
)


def get_request_type_fields(
    service_desk_id: str, request_type_id: str
) -> dict:
    """
    Get fields for a request type.

    Args:
        service_desk_id: Service desk ID
        request_type_id: Request type ID

    Returns:
        Fields data
    """
    client = get_jira_client()
    fields = client.get_request_type_fields(service_desk_id, request_type_id)
    client.close()

    return fields


def filter_fields(fields_data: dict, required_only: bool = False) -> dict:
    """
    Filter fields by required status.

    Args:
        fields_data: Fields data
        required_only: Show only required fields

    Returns:
        Filtered fields data
    """
    if not required_only:
        return fields_data

    filtered_fields = [
        field
        for field in fields_data.get("requestTypeFields", [])
        if field.get("required", False)
    ]

    return {**fields_data, "requestTypeFields": filtered_fields}


def format_fields_text(
    fields_data: dict,
    request_type_name: str = "Request Type",
    show_valid_values: bool = False,
) -> None:
    """
    Format fields as human-readable text.

    Args:
        fields_data: Fields data
        request_type_name: Request type name for display
        show_valid_values: Show valid values for fields
    """
    all_fields = fields_data.get("requestTypeFields", [])
    required_fields = [f for f in all_fields if f.get("required", False)]
    optional_fields = [f for f in all_fields if not f.get("required", False)]

    print(f"Request Type Fields: {request_type_name}")
    print()

    if required_fields:
        print("Required Fields:")
        print("─" * 80)
        print(f"{'Field ID':<20} {'Name':<20} {'Type':<15}")
        print(f"{'────────':<20} {'────':<20} {'────':<15}")

        for field in required_fields:
            field_id = field.get("fieldId", "")
            name = field.get("name", "")[:18]
            field_type = field.get("jiraSchema", {}).get("type", "unknown")

            print(f"{field_id:<20} {name:<20} {field_type:<15}")

            if show_valid_values and "validValues" in field:
                valid_values = field.get("validValues", [])
                if valid_values:
                    values_str = ", ".join(
                        [v.get("label", v.get("value", "")) for v in valid_values[:5]]
                    )
                    if len(valid_values) > 5:
                        values_str += f" (+{len(valid_values) - 5} more)"
                    print(f"  Valid values: {values_str}")

        print()

    if optional_fields:
        print("Optional Fields:")
        print("─" * 80)
        print(f"{'Field ID':<20} {'Name':<20} {'Type':<15}")
        print(f"{'────────':<20} {'────':<20} {'────':<15}")

        for field in optional_fields:
            field_id = field.get("fieldId", "")
            name = field.get("name", "")[:18]
            field_type = field.get("jiraSchema", {}).get("type", "unknown")

            print(f"{field_id:<20} {name:<20} {field_type:<15}")

            if show_valid_values and "validValues" in field:
                valid_values = field.get("validValues", [])
                if valid_values:
                    values_str = ", ".join(
                        [v.get("label", v.get("value", "")) for v in valid_values[:5]]
                    )
                    if len(valid_values) > 5:
                        values_str += f" (+{len(valid_values) - 5} more)"
                    print(f"  Valid values: {values_str}")

        print()

    print("Configuration:")
    print(
        f"  Can raise on behalf of: {'Yes' if fields_data.get('canRaiseOnBehalfOf', False) else 'No'}"
    )
    print(
        f"  Can add participants:   {'Yes' if fields_data.get('canAddRequestParticipants', False) else 'No'}"
    )
    print()
    print(
        f"Total: {len(required_fields)} required field{'s' if len(required_fields) != 1 else ''}, {len(optional_fields)} optional field{'s' if len(optional_fields) != 1 else ''}"
    )


def format_fields_json(fields_data: dict) -> str:
    """
    Format fields as JSON.

    Args:
        fields_data: Fields data

    Returns:
        JSON string
    """
    return format_json(fields_data)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Get fields for a JSM request type",
        epilog="Example: python get_request_type_fields.py 1 25",
    )

    parser.add_argument("service_desk_id", help="Service desk ID")
    parser.add_argument("request_type_id", help="Request type ID")
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--required-only", "-r", action="store_true", help="Show only required fields"
    )
    parser.add_argument(
        "--show-valid-values",
        "-v",
        action="store_true",
        help="Show valid values for fields",
    )

    args = parser.parse_args(argv)

    try:
        # Fetch fields
        fields_data = get_request_type_fields(
            args.service_desk_id, args.request_type_id
        )

        # Apply filters
        if args.required_only:
            fields_data = filter_fields(fields_data, required_only=True)

        # Get request type name for display
        client = get_jira_client()
        request_type = client.get_request_type(
            args.service_desk_id, args.request_type_id
        )
        request_type_name = request_type.get("name", "Request Type")
        client.close()

        # Output results
        if args.output == "json":
            print(format_fields_json(fields_data))
        else:
            format_fields_text(fields_data, request_type_name, args.show_valid_values)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
