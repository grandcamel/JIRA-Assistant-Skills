#!/usr/bin/env python3
"""
Download attachments from a JIRA issue.

Usage:
    python download_attachment.py PROJ-123 --list
    python download_attachment.py PROJ-123 --name screenshot.png
    python download_attachment.py PROJ-123 --id 12345
    python download_attachment.py PROJ-123 --all --output-dir ./downloads
"""

import argparse
import json
import os
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    format_table,
    get_jira_client,
    print_error,
    print_info,
    print_success,
    validate_issue_key,
)


def list_attachments(
    issue_key: str
) -> list[dict[str, Any]]:
    """
    List all attachments for an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)

    Returns:
        List of attachment objects
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    attachments = client.get_attachments(issue_key)
    client.close()

    return attachments


def download_attachment(
    issue_key: str,
    attachment_id: str | None = None,
    attachment_name: str | None = None,
    output_dir: str | None = None,
) -> str:
    """
    Download a specific attachment.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        attachment_id: Attachment ID to download
        attachment_name: Attachment name to download (if ID not specified)
        output_dir: Directory to save file (default: current directory)

    Returns:
        Path to downloaded file

    Raises:
        ValidationError: If attachment not found
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    attachments = client.get_attachments(issue_key)

    # Find the attachment
    target = None
    if attachment_id:
        for att in attachments:
            if str(att.get("id")) == str(attachment_id):
                target = att
                break
        if not target:
            client.close()
            raise ValidationError(
                f"Attachment with ID {attachment_id} not found on {issue_key}"
            )
    elif attachment_name:
        for att in attachments:
            if att.get("filename") == attachment_name:
                target = att
                break
        if not target:
            client.close()
            raise ValidationError(
                f"Attachment '{attachment_name}' not found on {issue_key}"
            )
    else:
        client.close()
        raise ValidationError("Either --id or --name must be specified")

    # Determine output path
    filename = target.get("filename", f"attachment_{target.get('id')}")
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
    else:
        output_path = filename

    # Download the file
    content_url = target.get("content")
    if not content_url:
        client.close()
        raise ValidationError(f"No content URL found for attachment {target.get('id')}")

    client.download_file(
        content_url, output_path, operation=f"download attachment {filename}"
    )
    client.close()

    return output_path


def download_all_attachments(
    issue_key: str, output_dir: str | None = None
) -> list[str]:
    """
    Download all attachments from an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        output_dir: Directory to save files

    Returns:
        List of paths to downloaded files
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    attachments = client.get_attachments(issue_key)

    if not attachments:
        client.close()
        return []

    # Create output directory if specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    downloaded = []
    for att in attachments:
        filename = att.get("filename", f"attachment_{att.get('id')}")
        content_url = att.get("content")

        if not content_url:
            continue

        if output_dir:
            output_path = os.path.join(output_dir, filename)
        else:
            output_path = filename

        # Handle duplicate filenames
        if os.path.exists(output_path):
            base, ext = os.path.splitext(output_path)
            counter = 1
            while os.path.exists(f"{base}_{counter}{ext}"):
                counter += 1
            output_path = f"{base}_{counter}{ext}"

        client.download_file(
            content_url, output_path, operation=f"download attachment {filename}"
        )
        downloaded.append(output_path)

    client.close()
    return downloaded


def format_attachment_list(attachments: list[dict[str, Any]]) -> str:
    """
    Format attachments as a table.

    Args:
        attachments: List of attachment objects

    Returns:
        Formatted table string
    """
    if not attachments:
        return "No attachments found."

    table_data = []
    for att in attachments:
        size_bytes = att.get("size", 0)
        if size_bytes >= 1048576:
            size_str = f"{size_bytes / 1048576:.1f} MB"
        elif size_bytes >= 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes} B"

        table_data.append(
            {
                "id": att.get("id", ""),
                "filename": att.get("filename", ""),
                "size": size_str,
                "mime_type": att.get("mimeType", ""),
                "created": att.get("created", "")[:10] if att.get("created") else "",
                "author": att.get("author", {}).get("displayName", ""),
            }
        )

    return format_table(
        table_data,
        columns=["id", "filename", "size", "mime_type", "created", "author"],
        headers=["ID", "Filename", "Size", "Type", "Created", "Author"],
    )


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Download attachments from a JIRA issue",
        epilog="""
Examples:
  %(prog)s PROJ-123 --list
  %(prog)s PROJ-123 --name screenshot.png
  %(prog)s PROJ-123 --id 12345
  %(prog)s PROJ-123 --all --output-dir ./downloads
        """,
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--list", "-l", action="store_true", help="List all attachments"
    )
    action_group.add_argument("--name", "-n", help="Download attachment by filename")
    action_group.add_argument("--id", "-i", help="Download attachment by ID")
    action_group.add_argument(
        "--all", "-a", action="store_true", help="Download all attachments"
    )

    parser.add_argument("--output-dir", "-o", help="Directory to save downloaded files")
    parser.add_argument(
        "--output",
        "-O",
        choices=["text", "json"],
        default="text",
        help="Output format for --list (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        if args.list:
            attachments = list_attachments(args.issue_key)

            if args.output == "json":
                print(json.dumps(attachments, indent=2))
            else:
                print(f"Attachments for {args.issue_key}:\n")
                print(format_attachment_list(attachments))

        elif args.name:
            output_path = download_attachment(
                args.issue_key,
                attachment_name=args.name,
                output_dir=args.output_dir,
            )
            print_success(f"Downloaded: {output_path}")

        elif args.id:
            output_path = download_attachment(
                args.issue_key,
                attachment_id=args.id,
                output_dir=args.output_dir,
            )
            print_success(f"Downloaded: {output_path}")

        elif args.all:
            downloaded = download_all_attachments(
                args.issue_key, output_dir=args.output_dir
            )

            if downloaded:
                print_success(f"Downloaded {len(downloaded)} attachment(s):")
                for path in downloaded:
                    print(f"  - {path}")
            else:
                print_info("No attachments to download.")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
