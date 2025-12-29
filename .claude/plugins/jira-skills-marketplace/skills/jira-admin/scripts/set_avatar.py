#!/usr/bin/env python3
"""
Manage JIRA project avatars.

List available avatars, select a system avatar, upload a custom avatar,
or delete custom avatars.

Requires project administrator permissions.

Examples:
    # List available avatars
    python set_avatar.py PROJ --list

    # Select a system avatar
    python set_avatar.py PROJ --avatar-id 10200

    # Upload custom avatar from file
    python set_avatar.py PROJ --file /path/to/avatar.png

    # Delete a custom avatar
    python set_avatar.py PROJ --delete 10300
"""

import argparse
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import JiraError, ValidationError, print_error
from validators import validate_project_key, validate_avatar_file


def list_avatars(
    project_key: str,
    client=None
) -> Dict[str, Any]:
    """
    List available avatars for a project.

    Args:
        project_key: Project key
        client: JiraClient instance (optional)

    Returns:
        Dict with 'system' and 'custom' avatar lists

    Raises:
        JiraError: If API call fails
    """
    project_key = validate_project_key(project_key)

    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        result = client.get_project_avatars(project_key)
        return result

    finally:
        if should_close:
            client.close()


def set_avatar(
    project_key: str,
    avatar_id: str,
    client=None
) -> Dict[str, Any]:
    """
    Set a project avatar by ID.

    Args:
        project_key: Project key
        avatar_id: Avatar ID to set
        client: JiraClient instance (optional)

    Returns:
        Success result dict

    Raises:
        JiraError: If API call fails
    """
    project_key = validate_project_key(project_key)

    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        client.set_project_avatar(project_key, avatar_id)
        return {
            'success': True,
            'project_key': project_key,
            'avatar_id': avatar_id,
            'message': f"Avatar {avatar_id} set for project {project_key}"
        }

    finally:
        if should_close:
            client.close()


def upload_avatar(
    project_key: str,
    file_path: str,
    client=None
) -> Dict[str, Any]:
    """
    Upload a custom avatar from file.

    Args:
        project_key: Project key
        file_path: Path to avatar file (PNG, JPEG, GIF)
        client: JiraClient instance (optional)

    Returns:
        Uploaded avatar data

    Raises:
        ValidationError: If file format is invalid
        JiraError: If API call fails
    """
    project_key = validate_project_key(project_key)
    file_path = validate_avatar_file(file_path)

    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        result = client.upload_project_avatar(project_key, file_path)
        return result

    finally:
        if should_close:
            client.close()


def delete_avatar(
    project_key: str,
    avatar_id: str,
    client=None
) -> Dict[str, Any]:
    """
    Delete a custom avatar.

    Args:
        project_key: Project key
        avatar_id: Avatar ID to delete
        client: JiraClient instance (optional)

    Returns:
        Success result dict

    Raises:
        JiraError: If API call fails
    """
    project_key = validate_project_key(project_key)

    should_close = False
    if client is None:
        client = get_jira_client()
        should_close = True

    try:
        client.delete_project_avatar(project_key, avatar_id)
        return {
            'success': True,
            'project_key': project_key,
            'avatar_id': avatar_id,
            'message': f"Avatar {avatar_id} deleted from project {project_key}"
        }

    finally:
        if should_close:
            client.close()


def format_avatars_output(avatars: Dict[str, Any], output_format: str = "text") -> str:
    """Format avatars list for output."""
    if output_format == "json":
        return json.dumps(avatars, indent=2)

    # Text output
    lines = ["Available Avatars:", "=" * 60, ""]

    system_avatars = avatars.get('system', [])
    custom_avatars = avatars.get('custom', [])

    if system_avatars:
        lines.append("System Avatars:")
        for avatar in system_avatars:
            lines.append(f"  ID: {avatar.get('id', 'N/A')}")

    lines.append("")

    if custom_avatars:
        lines.append("Custom Avatars:")
        for avatar in custom_avatars:
            lines.append(f"  ID: {avatar.get('id', 'N/A')} (Owner: {avatar.get('owner', 'N/A')})")
    else:
        lines.append("No custom avatars.")

    lines.append("")
    lines.append("To set an avatar: python set_avatar.py PROJ --avatar-id <ID>")

    return "\n".join(lines)


def format_result_output(result: Dict[str, Any], output_format: str = "text") -> str:
    """Format result for output."""
    if output_format == "json":
        return json.dumps(result, indent=2)

    return result.get('message', 'Operation completed.')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage JIRA project avatars",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available avatars
  %(prog)s PROJ --list

  # Select a system avatar
  %(prog)s PROJ --avatar-id 10200

  # Upload custom avatar from file
  %(prog)s PROJ --file /path/to/avatar.png

  # Delete a custom avatar
  %(prog)s PROJ --delete 10300
        """
    )

    # Required arguments
    parser.add_argument(
        "project_key",
        help="Project key (e.g., PROJ)"
    )

    # Operations (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available avatars"
    )
    group.add_argument(
        "--avatar-id", "-a",
        help="Set avatar by ID"
    )
    group.add_argument(
        "--file", "-f",
        dest="file_path",
        help="Upload avatar from file (PNG, JPEG, GIF)"
    )
    group.add_argument(
        "--delete", "-d",
        dest="delete_id",
        help="Delete custom avatar by ID"
    )

    # Output options
    parser.add_argument(
        "--output", "-o",
        choices=['text', 'json'],
        default='text',
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--profile",
        help="Configuration profile to use"
    )

    args = parser.parse_args()

    try:
        client = get_jira_client(profile=args.profile)

        if args.list:
            result = list_avatars(
                project_key=args.project_key,
                client=client
            )
            print(format_avatars_output(result, args.output))

        elif args.avatar_id:
            result = set_avatar(
                project_key=args.project_key,
                avatar_id=args.avatar_id,
                client=client
            )
            print(format_result_output(result, args.output))

        elif args.file_path:
            result = upload_avatar(
                project_key=args.project_key,
                file_path=args.file_path,
                client=client
            )
            if args.output == "json":
                print(json.dumps(result, indent=2))
            else:
                print(f"Avatar uploaded successfully!")
                print(f"  ID: {result.get('id', 'N/A')}")
                print(f"  Project: {args.project_key}")

        elif args.delete_id:
            result = delete_avatar(
                project_key=args.project_key,
                avatar_id=args.delete_id,
                client=client
            )
            print(format_result_output(result, args.output))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except ValidationError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    main()
