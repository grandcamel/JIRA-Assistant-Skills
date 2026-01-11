#!/usr/bin/env python3
"""
Get automation template details.

Retrieves detailed information about an automation template
including required parameters.

Usage:
    python get_automation_template.py TEMPLATE_ID
    python get_automation_template.py TEMPLATE_ID --output json
    python get_automation_template.py TEMPLATE_ID
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    AutomationError,
    JiraError,
    get_automation_client,
    print_error,
)


def get_automation_template(
    client=None, template_id: str | None = None
) -> dict[str, Any]:
    """
    Get automation template details.

    Args:
        client: AutomationClient instance (optional, created if not provided)
        template_id: Template ID to fetch

    Returns:
        Template configuration

    Raises:
        ValueError: If template_id not provided
    """
    if client is None:
        client = get_automation_client()

    if not template_id:
        raise ValueError("template_id is required")

    return client.get_template(template_id)


def format_template_output(template: dict[str, Any]) -> str:
    """Format template for human-readable output."""
    lines = []

    lines.append("=" * 80)
    lines.append(f"Template: {template.get('name', 'Unnamed')}")
    lines.append("=" * 80)
    lines.append("")

    lines.append(f"ID: {template.get('id', 'N/A')}")
    lines.append(f"Category: {template.get('category', 'N/A')}")

    if template.get("description"):
        lines.append("\nDescription:")
        lines.append(f"  {template.get('description')}")

    tags = template.get("tags", [])
    if tags:
        lines.append(f"\nTags: {', '.join(tags)}")

    parameters = template.get("parameters", [])
    if parameters:
        lines.append("")
        lines.append("-" * 40)
        lines.append("Parameters")
        lines.append("-" * 40)

        for param in parameters:
            required = "(required)" if param.get("required") else "(optional)"
            lines.append(
                f"\n  {param.get('name')} [{param.get('type', 'string')}] {required}"
            )
            if param.get("description"):
                lines.append(f"    {param.get('description')}")
            if param.get("default"):
                lines.append(f"    Default: {param.get('default')}")

    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Get automation template details",
        epilog="""
Examples:
    # Get template by ID
    python get_automation_template.py template-001

    # Output as JSON
    python get_automation_template.py template-001 --output json

    # Use specific profile
    python get_automation_template.py template-001
        """,
    )

    parser.add_argument("template_id", help="Template ID")
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        template = get_automation_template(template_id=args.template_id)

        if args.output == "json":
            print(json.dumps(template, indent=2))
        else:
            output = format_template_output(template)
            print(output)

    except (JiraError, AutomationError) as e:
        print_error(e)
        sys.exit(1)
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
