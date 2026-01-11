#!/usr/bin/env python3
"""
Update custom fields on a JIRA issue.

Usage:
    python update_custom_fields.py PROJ-123 --field customfield_10001 --value "Production"
    python update_custom_fields.py PROJ-123 --fields '{"customfield_10001": "value1", "customfield_10002": "value2"}'
"""

import argparse
import contextlib
import json
import sys

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
    print_success,
    validate_issue_key,
)


def update_custom_fields(
    issue_key: str,
    field: str | None = None,
    value: str | None = None,
    fields_json: str | None = None,
) -> None:
    """
    Update custom fields on an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        field: Single field ID
        value: Single field value
        fields_json: JSON string with multiple fields
    """
    issue_key = validate_issue_key(issue_key)

    if fields_json:
        fields = json.loads(fields_json)
    elif field and value is not None:
        with contextlib.suppress(json.JSONDecodeError):
            value = json.loads(value)
        fields = {field: value}
    else:
        raise ValidationError(
            "Either --field and --value, or --fields must be specified"
        )

    client = get_jira_client()
    client.update_issue(issue_key, fields, notify_users=True)
    client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Update custom fields on a JIRA issue",
        epilog='Example: python update_custom_fields.py PROJ-123 --field customfield_10001 --value "Production"',
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument("--field", help="Custom field ID (e.g., customfield_10001)")
    parser.add_argument("--value", help="Field value (string or JSON)")
    parser.add_argument("--fields", help="JSON string with multiple fields to update")

    args = parser.parse_args(argv)

    try:
        update_custom_fields(
            issue_key=args.issue_key,
            field=args.field,
            value=args.value,
            fields_json=args.fields,
        )

        print_success(f"Updated custom fields on {args.issue_key}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
