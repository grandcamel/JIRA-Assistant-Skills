#!/usr/bin/env python3
"""
Upload an attachment to a JIRA issue.

Usage:
    python upload_attachment.py PROJ-123 --file screenshot.png
    python upload_attachment.py PROJ-123 --file report.pdf --name "Monthly Report.pdf"
"""

import argparse
import sys

from jira_assistant_skills_lib import (
    JiraError,
    get_jira_client,
    print_error,
    print_success,
    validate_file_path,
    validate_issue_key,
)


def upload_attachment(
    issue_key: str,
    file_path: str,
    file_name: str | None = None,
    profile: str | None = None,
) -> dict:
    """
    Upload an attachment to an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        file_path: Path to file to upload
        file_name: Name for the uploaded file (default: use file_path basename)
        profile: JIRA profile to use

    Returns:
        Attachment data
    """
    issue_key = validate_issue_key(issue_key)
    file_path = validate_file_path(file_path, must_exist=True)

    client = get_jira_client(profile)
    result = client.upload_file(
        f"/rest/api/3/issue/{issue_key}/attachments",
        file_path,
        file_name=file_name,
        operation=f"upload attachment to {issue_key}",
    )
    client.close()

    return result


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Upload an attachment to a JIRA issue",
        epilog="Example: python upload_attachment.py PROJ-123 --file screenshot.png",
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    parser.add_argument("--file", "-f", required=True, help="Path to file to upload")
    parser.add_argument(
        "--name", "-n", help="Name for the uploaded file (default: use filename)"
    )
    parser.add_argument("--profile", help="JIRA profile to use (default: from config)")

    args = parser.parse_args(argv)

    try:
        result = upload_attachment(
            issue_key=args.issue_key,
            file_path=args.file,
            file_name=args.name,
            profile=args.profile,
        )

        if isinstance(result, list) and result:
            filename = result[0].get("filename", "")
            print_success(f"Uploaded {filename} to {args.issue_key}")
        else:
            print_success(f"Uploaded file to {args.issue_key}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
