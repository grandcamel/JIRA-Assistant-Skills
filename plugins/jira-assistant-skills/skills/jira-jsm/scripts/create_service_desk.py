#!/usr/bin/env python3
"""
Create a new JSM service desk (admin only).

Usage:
    python create_service_desk.py --name "IT Service Desk" --key ITS
    python create_service_desk.py --name "IT Service Desk" --key ITS --template simplified-it-service-desk
    python create_service_desk.py --name "IT Service Desk" --key ITS --dry-run
    python create_service_desk.py --list-templates
"""

import argparse
import re
import sys

from jira_assistant_skills_lib import (
    JiraError,
    format_json,
    get_jira_client,
    print_error,
)

# Common service desk templates
TEMPLATES = {
    "simplified-it-service-desk": "com.atlassian.servicedesk:simplified-it-service-desk",
    "it-service-desk": "com.atlassian.servicedesk:itil-v2-service-desk-no-queues",
    "internal-service-desk": "com.atlassian.servicedesk:simplified-internal-service-desk",
    "external-service-desk": "com.atlassian.servicedesk:simplified-external-service-desk",
    "general-service-desk": "com.atlassian.servicedesk:simplified-general-service-desk",
    "hr-service-desk": "com.atlassian.servicedesk:simplified-hr-service-desk",
    "facilities-service-desk": "com.atlassian.servicedesk:simplified-facilities-service-desk",
    "legal-service-desk": "com.atlassian.servicedesk:simplified-legal-service-desk",
}


def validate_project_key(key: str) -> bool:
    """
    Validate project key format.

    Args:
        key: Project key to validate

    Returns:
        True if valid, False otherwise
    """
    # Must be 2-10 uppercase letters, starting with a letter
    if not key:
        return False
    if len(key) < 2 or len(key) > 10:
        return False
    return re.match(r"^[A-Z][A-Z0-9]*$", key)


def list_available_templates() -> None:
    """List available service desk templates."""
    print("Available Service Desk Templates:")
    print()
    print(f"{'Template Key':<30} {'Full Template ID':<70}")
    print(f"{'────────────':<30} {'────────────────':<70}")

    for key, template_id in TEMPLATES.items():
        print(f"{key:<30} {template_id:<70}")

    print()
    print("Usage: --template <template-key>")


def create_service_desk(name: str, key: str, project_template_key: str) -> dict:
    """
    Create a new service desk.

    Args:
        name: Service desk name
        key: Project key
        project_template_key: Project template key

    Returns:
        Created service desk data
    """
    client = get_jira_client()
    service_desk = client.create_service_desk(name, key, project_template_key)
    client.close()

    return service_desk


def format_create_preview(name: str, key: str, template: str) -> None:
    """
    Show preview of service desk to be created.

    Args:
        name: Service desk name
        key: Project key
        template: Template key
    """
    print("DRY RUN - Preview of Service Desk Creation:")
    print()
    print(f"Name:     {name}")
    print(f"Key:      {key}")
    print(f"Template: {template}")
    print()
    print("This service desk would be created with the above configuration.")
    print("Remove --dry-run flag to create the service desk.")


def format_service_desk_created_text(service_desk: dict) -> None:
    """
    Format created service desk as human-readable text.

    Args:
        service_desk: Created service desk data
    """
    print("Successfully Created Service Desk:")
    print()
    print(f"ID:           {service_desk.get('id', '')}")
    print(f"Project ID:   {service_desk.get('projectId', '')}")
    print(f"Project Key:  {service_desk.get('projectKey', '')}")
    print(f"Project Name: {service_desk.get('projectName', '')}")
    print()
    print("Next steps:")
    print(f"  - View details: python get_service_desk.py {service_desk.get('id', '')}")
    print(
        f"  - List request types: python list_request_types.py {service_desk.get('id', '')}"
    )


def format_service_desk_created_json(service_desk: dict) -> str:
    """
    Format created service desk as JSON.

    Args:
        service_desk: Created service desk data

    Returns:
        JSON string
    """
    return format_json(service_desk)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Create a new JSM service desk (requires admin permissions)",
        epilog='Example: python create_service_desk.py --name "IT Service Desk" --key ITS',
    )

    parser.add_argument("--name", "-n", help="Service desk name")
    parser.add_argument("--key", "-k", help="Project key (2-10 uppercase letters)")
    parser.add_argument(
        "--template",
        "-t",
        default="simplified-it-service-desk",
        help="Project template key (default: simplified-it-service-desk)",
    )
    parser.add_argument(
        "--list-templates", "-l", action="store_true", help="List available templates"
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Preview creation without actually creating",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        # List templates and exit
        if args.list_templates:
            list_available_templates()
            return

        # Validate required arguments
        if not args.name or not args.key:
            parser.error("--name and --key are required (or use --list-templates)")

        # Validate project key
        if not validate_project_key(args.key):
            raise JiraError(
                f"Invalid project key: {args.key}\n"
                "Project key must be 2-10 uppercase letters, starting with a letter."
            )

        # Get full template ID
        template_id = TEMPLATES.get(args.template, args.template)

        # Dry run mode
        if args.dry_run:
            format_create_preview(args.name, args.key, template_id)
            return

        # Create service desk
        service_desk = create_service_desk(args.name, args.key, template_id)

        # Output results
        if args.output == "json":
            print(format_service_desk_created_json(service_desk))
        else:
            format_service_desk_created_text(service_desk)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
