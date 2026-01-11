#!/usr/bin/env python3
"""
Create a new JIRA project category.

Project categories are used to group and organize projects.
Requires JIRA administrator permissions.

Examples:
    # Create a category
    python create_category.py --name "Development" --description "All dev projects"

    # Create with just a name
    python create_category.py --name "Marketing"
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
    validate_category_name,
)


def create_category(
    name: str, description: str | None = None, client=None
) -> dict[str, Any]:
    """
    Create a new project category.

    Args:
        name: Category name
        description: Category description (optional)
        client: JiraClient instance (optional)

    Returns:
        Created category data

    Raises:
        ValidationError: If input validation fails
        JiraError: If API call fails
    """
    # Validate inputs
    name = validate_category_name(name)

    # Create client if not provided
    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        result = client.create_project_category(name=name, description=description)

        return result

    finally:
        if should_close:
            client.close()


def format_output(category: dict[str, Any], output_format: str = "text") -> str:
    """Format category data for output."""
    if output_format == "json":
        return json.dumps(category, indent=2)

    # Text output
    lines = [
        "Category created successfully!",
        "",
        f"  ID:          {category.get('id')}",
        f"  Name:        {category.get('name')}",
    ]

    description = category.get("description")
    if description:
        lines.append(f"  Description: {description}")

    lines.append(f"  URL:         {category.get('self', 'N/A')}")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create a new JIRA project category",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a category with description
  %(prog)s --name "Development" --description "All development projects"

  # Create with just a name
  %(prog)s --name "Marketing"
        """,
    )

    # Required arguments
    parser.add_argument("--name", "-n", required=True, help="Category name")

    # Optional arguments
    parser.add_argument("--description", "-d", help="Category description")

    # Output options
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        client = get_jira_client()

        result = create_category(
            name=args.name, description=args.description, client=client
        )

        print(format_output(result, args.output))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except ValidationError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if "client" in locals():
            client.close()


if __name__ == "__main__":
    main()
