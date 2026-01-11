#!/usr/bin/env python3
"""
Get JSM request type details.

Usage:
    python get_request_type.py 1 25
    python get_request_type.py 1 25 --output json
    python get_request_type.py 1 25 --show-fields
"""

import argparse
import sys

from jira_assistant_skills_lib import (
    JiraError,
    format_json,
    get_jira_client,
    print_error,
)


def get_request_type(service_desk_id: str, request_type_id: str) -> dict:
    """
    Get request type details.

    Args:
        service_desk_id: Service desk ID
        request_type_id: Request type ID

    Returns:
        Request type data
    """
    client = get_jira_client()
    request_type = client.get_request_type(service_desk_id, request_type_id)
    client.close()

    return request_type


def format_request_type_text(request_type: dict, show_fields: bool = False) -> None:
    """
    Format request type as human-readable text.

    Args:
        request_type: Request type data
        show_fields: Show field information hint
    """
    print("Request Type Details:")
    print()
    print(f"ID:             {request_type.get('id', '')}")
    print(f"Name:           {request_type.get('name', '')}")
    print(f"Description:    {request_type.get('description', '')}")

    if "helpText" in request_type:
        print(f"Help Text:      {request_type.get('helpText', '')}")

    print()
    print(f"Service Desk ID: {request_type.get('serviceDeskId', '')}")
    print(f"Issue Type ID:   {request_type.get('issueTypeId', '')}")

    if "groupIds" in request_type:
        groups = request_type.get("groupIds", [])
        print(f"Groups:          {', '.join(groups) if groups else 'None'}")

    if "icon" in request_type:
        icon = request_type.get("icon", {})
        if "id" in icon:
            print()
            print("Portal Configuration:")
            print(f"  Icon ID:       {icon.get('id', '')}")

    if show_fields:
        print()
        print("To see required fields:")
        print(
            f"  python get_request_type_fields.py {request_type.get('serviceDeskId', '')} {request_type.get('id', '')}"
        )


def format_request_type_json(request_type: dict) -> str:
    """
    Format request type as JSON.

    Args:
        request_type: Request type data

    Returns:
        JSON string
    """
    return format_json(request_type)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Get JSM request type details",
        epilog="Example: python get_request_type.py 1 25",
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
        "--show-fields", "-f", action="store_true", help="Show hint to view fields"
    )

    args = parser.parse_args(argv)

    try:
        # Fetch request type
        request_type = get_request_type(args.service_desk_id, args.request_type_id)

        # Output results
        if args.output == "json":
            print(format_request_type_json(request_type))
        else:
            format_request_type_text(request_type, args.show_fields)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
