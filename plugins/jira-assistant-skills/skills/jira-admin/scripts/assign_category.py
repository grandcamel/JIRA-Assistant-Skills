#!/usr/bin/env python3
"""
Assign or remove a project category from a project.

Project categories are used to group and organize projects.

Examples:
    # Assign by category ID
    python assign_category.py PROJ --category-id 10000

    # Assign by category name
    python assign_category.py PROJ --category "Development"

    # Remove category from project
    python assign_category.py PROJ --remove
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
    validate_project_key,
)


def assign_category(
    project_key: str,
    category_id: int | None = None,
    category_name: str | None = None,
    remove: bool = False,
    client=None,
) -> dict[str, Any]:
    """
    Assign or remove a category from a project.

    Args:
        project_key: Project key
        category_id: Category ID to assign
        category_name: Category name to assign (looks up ID)
        remove: If True, remove the category
        client: JiraClient instance (optional)

    Returns:
        Updated project data

    Raises:
        ValidationError: If input validation fails
        JiraError: If API call fails
    """
    # Validate project key
    project_key = validate_project_key(project_key)

    # Must specify one of category_id, category_name, or remove
    if not category_id and not category_name and not remove:
        raise ValidationError("Must specify --category-id, --category, or --remove")

    # Create client if not provided
    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        # Handle remove
        if remove:
            # Set category to None to remove
            result = client.update_project(project_key, category_id=None)
            return result

        # If category_name provided, look up the ID
        target_category_id = category_id
        if category_name and not category_id:
            categories = client.get_project_categories()

            # Find by exact name match (case-insensitive)
            found = None
            for cat in categories:
                if cat.get("name", "").lower() == category_name.lower():
                    found = cat
                    break

            if not found:
                # Try partial match
                matches = [
                    c
                    for c in categories
                    if category_name.lower() in c.get("name", "").lower()
                ]

                if len(matches) == 1:
                    found = matches[0]
                elif len(matches) > 1:
                    names = [m.get("name") for m in matches]
                    raise ValidationError(
                        f"Ambiguous category name '{category_name}'. "
                        f"Matches: {', '.join(names)}"
                    )

            if not found:
                # List available categories in error
                available = [c.get("name") for c in categories]
                raise ValidationError(
                    f"Category '{category_name}' not found. "
                    f"Available categories: {', '.join(available) if available else 'None'}"
                )

            target_category_id = int(found.get("id"))

        # Update project with new category
        result = client.update_project(project_key, category_id=target_category_id)

        return result

    finally:
        if should_close:
            client.close()


def format_output(
    project: dict[str, Any], remove: bool = False, output_format: str = "text"
) -> str:
    """Format project data for output."""
    if output_format == "json":
        return json.dumps(project, indent=2)

    # Text output
    category = project.get("projectCategory")

    if remove or not category:
        lines = [
            f"Category removed from project {project.get('key')}",
        ]
    else:
        lines = [
            f"Category assigned to project {project.get('key')}",
            "",
            f"  Category:    {category.get('name')} (ID: {category.get('id')})",
        ]
        if category.get("description"):
            lines.append(f"  Description: {category.get('description')}")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Assign or remove a project category",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Assign by category ID
  %(prog)s PROJ --category-id 10000

  # Assign by category name
  %(prog)s PROJ --category "Development"

  # Remove category from project
  %(prog)s PROJ --remove
        """,
    )

    # Required arguments
    parser.add_argument("project_key", help="Project key (e.g., PROJ)")

    # Category options (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--category-id", type=int, help="Category ID to assign")
    group.add_argument(
        "--category", "-c", dest="category_name", help="Category name to assign"
    )
    group.add_argument(
        "--remove", "-r", action="store_true", help="Remove category from project"
    )

    # Output options
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", help="Configuration profile to use")

    args = parser.parse_args(argv)

    try:
        client = get_jira_client(profile=args.profile)

        result = assign_category(
            project_key=args.project_key,
            category_id=args.category_id,
            category_name=args.category_name,
            remove=args.remove,
            client=client,
        )

        print(format_output(result, args.remove, args.output))

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
