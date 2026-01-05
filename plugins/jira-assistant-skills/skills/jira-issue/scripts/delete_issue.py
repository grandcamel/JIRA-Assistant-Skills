#!/usr/bin/env python3
"""
Delete a JIRA issue.

Usage:
    python delete_issue.py PROJ-123
    python delete_issue.py PROJ-123 --force
"""

import argparse
import sys

from jira_assistant_skills_lib import (
    JiraError,
    get_jira_client,
    print_error,
    print_success,
    validate_issue_key,
)


def delete_issue(
    issue_key: str, force: bool = False, profile: str | None = None
) -> None:
    """
    Delete a JIRA issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        force: Skip confirmation prompt
        profile: JIRA profile to use
    """
    issue_key = validate_issue_key(issue_key)

    if not force:
        client = get_jira_client(profile)
        try:
            issue = client.get_issue(
                issue_key, fields=["summary", "issuetype", "status"]
            )
            summary = issue.get("fields", {}).get("summary", "")
            issue_type = issue.get("fields", {}).get("issuetype", {}).get("name", "")
            status = issue.get("fields", {}).get("status", {}).get("name", "")

            print(f"\nIssue: {issue_key}")
            print(f"Type: {issue_type}")
            print(f"Status: {status}")
            print(f"Summary: {summary}")
            print()

            response = input("Are you sure you want to delete this issue? (yes/no): ")
            if response.lower() not in ["yes", "y"]:
                print("Deletion cancelled.")
                client.close()
                return
        except JiraError:
            response = input(f"Are you sure you want to delete {issue_key}? (yes/no): ")
            if response.lower() not in ["yes", "y"]:
                print("Deletion cancelled.")
                client.close()
                return
    else:
        client = get_jira_client(profile)

    client.delete_issue(issue_key)
    client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Delete a JIRA issue",
        epilog="Example: python delete_issue.py PROJ-123",
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument(
        "--force", "-f", action="store_true", help="Skip confirmation prompt"
    )
    parser.add_argument("--profile", help="JIRA profile to use (default: from config)")

    args = parser.parse_args(argv)

    try:
        delete_issue(issue_key=args.issue_key, force=args.force, profile=args.profile)

        print_success(f"Deleted issue: {args.issue_key}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nDeletion cancelled.")
        sys.exit(0)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
