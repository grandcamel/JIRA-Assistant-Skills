#!/usr/bin/env python3
"""
Create a new Epic issue in JIRA.

Usage:
    python create_epic.py --project PROJ --summary "Epic summary"
    python create_epic.py --project PROJ --summary "Epic" --epic-name "MVP" --color blue
    python create_epic.py --project PROJ --summary "Epic" --description "Details" --assignee self
"""

import argparse
import json
import sys

# Add shared lib to path
# Imports from shared library
from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_agile_fields,
    get_jira_client,
    markdown_to_adf,
    print_error,
    print_success,
    text_to_adf,
    validate_project_key,
)

# Valid epic colors in JIRA
VALID_EPIC_COLORS = [
    "blue",
    "cyan",
    "green",
    "yellow",
    "orange",
    "red",
    "magenta",
    "purple",
    "lime",
    "pink",
    "teal",
]


def create_epic(
    project: str,
    summary: str,
    description: str | None = None,
    epic_name: str | None = None,
    color: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    labels: list | None = None,
    custom_fields: dict | None = None,
    client=None,
) -> dict:
    """
    Create a new Epic issue in JIRA.

    Args:
        project: Project key (required)
        summary: Epic summary/title (required)
        description: Epic description (supports markdown)
        epic_name: Epic Name field value
        color: Epic color (blue, green, red, etc.)
        priority: Priority name
        assignee: Assignee account ID or "self"
        labels: List of labels
        custom_fields: Additional custom fields

    Returns:
        Created epic data from JIRA API

    Raises:
        ValidationError: If inputs are invalid
        JiraError: If API call fails
    """
    # Validate required fields
    if not project:
        raise ValidationError("Project key is required")

    if not summary:
        raise ValidationError("Summary is required")

    project = validate_project_key(project)

    # Validate epic color if provided
    if color and color.lower() not in VALID_EPIC_COLORS:
        raise ValidationError(
            f"Invalid epic color: {color}. Valid colors: {', '.join(VALID_EPIC_COLORS)}"
        )

    # Build fields dictionary
    fields = {
        "project": {"key": project},
        "issuetype": {"name": "Epic"},
        "summary": summary,
    }

    # Add description with ADF conversion
    if description:
        if description.strip().startswith("{"):
            # Already ADF JSON
            fields["description"] = json.loads(description)
        elif "\n" in description or any(
            md in description for md in ["**", "*", "#", "`", "["]
        ):
            # Markdown format
            fields["description"] = markdown_to_adf(description)
        else:
            # Plain text
            fields["description"] = text_to_adf(description)

    # Add priority
    if priority:
        fields["priority"] = {"name": priority}

    # Add assignee
    if assignee:
        if assignee.lower() == "self":
            temp_client = client or get_jira_client()
            account_id = temp_client.get_current_user_id()
            fields["assignee"] = {"accountId": account_id}
            if not client:
                temp_client.close()
        elif "@" in assignee:
            fields["assignee"] = {"emailAddress": assignee}
        else:
            fields["assignee"] = {"accountId": assignee}

    # Add labels
    if labels:
        fields["labels"] = labels

    # Get Agile field IDs from configuration
    agile_fields = get_agile_fields()

    # Add epic-specific custom fields
    if epic_name:
        fields[agile_fields["epic_name"]] = epic_name

    if color:
        fields[agile_fields["epic_color"]] = color.lower()

    # Add any additional custom fields
    if custom_fields:
        fields.update(custom_fields)

    # Create the epic
    if not client:
        client = get_jira_client()
        should_close = True
    else:
        should_close = False

    try:
        result = client.create_issue(fields)
        return result
    finally:
        if should_close:
            client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Create a new Epic issue in JIRA",
        epilog='Example: python create_epic.py --project PROJ --summary "Mobile App MVP" --epic-name "MVP"',
    )

    parser.add_argument(
        "--project", "-p", required=True, help="Project key (e.g., PROJ, DEV)"
    )
    parser.add_argument("--summary", "-s", required=True, help="Epic summary (title)")
    parser.add_argument(
        "--description", "-d", help="Epic description (supports markdown)"
    )
    parser.add_argument("--epic-name", "-n", help="Epic Name field value")
    parser.add_argument(
        "--color",
        "-c",
        choices=VALID_EPIC_COLORS,
        help=f"Epic color ({', '.join(VALID_EPIC_COLORS[:5])}...)",
    )
    parser.add_argument(
        "--priority", help="Priority (Highest, High, Medium, Low, Lowest)"
    )
    parser.add_argument(
        "--assignee", "-a", help='Assignee (account ID, email, or "self")'
    )
    parser.add_argument("--labels", "-l", help="Comma-separated labels")
    parser.add_argument("--custom-fields", help="Custom fields as JSON string")
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        labels = [l.strip() for l in args.labels.split(",")] if args.labels else None
        custom_fields = json.loads(args.custom_fields) if args.custom_fields else None

        result = create_epic(
            project=args.project,
            summary=args.summary,
            description=args.description,
            epic_name=args.epic_name,
            color=args.color,
            priority=args.priority,
            assignee=args.assignee,
            labels=labels,
            custom_fields=custom_fields,
        )

        epic_key = result.get("key")

        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            print_success(f"Created epic: {epic_key}")
            if args.epic_name:
                print(f"Epic Name: {args.epic_name}")
            base_url = result.get("self", "").split("/rest/api/")[0]
            print(f"URL: {base_url}/browse/{epic_key}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except ValidationError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
