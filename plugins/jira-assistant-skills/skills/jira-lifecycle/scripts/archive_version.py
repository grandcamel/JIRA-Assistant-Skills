#!/usr/bin/env python3
"""
Archive a project version in JIRA.

Usage:
    python archive_version.py --id 10002
    python archive_version.py PROJ --name "v0.5.0"
    python archive_version.py --id 10002 --dry-run
"""

import argparse
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
    print_success,
)


def archive_version(version_id: str, profile: str | None = None) -> dict[str, Any]:
    """
    Archive a version by ID.

    Args:
        version_id: Version ID
        profile: JIRA profile to use

    Returns:
        Updated version data
    """
    client = get_jira_client(profile)
    result = client.update_version(version_id, archived=True)
    client.close()

    return result


def archive_version_by_name(
    project: str, version_name: str, profile: str | None = None
) -> dict[str, Any]:
    """
    Archive a version by name (requires project lookup).

    Args:
        project: Project key
        version_name: Version name
        profile: JIRA profile to use

    Returns:
        Updated version data

    Raises:
        ValidationError: If version name not found in project
    """
    # Get all versions for the project
    client = get_jira_client(profile)
    versions = client.get_versions(project)

    # Find version by name
    version_id = None
    for v in versions:
        if v["name"] == version_name:
            version_id = v["id"]
            break

    if not version_id:
        raise ValidationError(
            f"Version '{version_name}' not found in project {project}"
        )

    # Archive the version
    result = client.update_version(version_id, archived=True)
    client.close()

    return result


def archive_version_dry_run(version_id: str) -> dict[str, Any]:
    """
    Show what would be archived without archiving.

    Args:
        version_id: Version ID

    Returns:
        Update data that would be applied
    """
    return {"version_id": version_id, "archived": True}


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Archive a project version in JIRA",
        epilog="""
Examples:
  %(prog)s --id 10002
  %(prog)s PROJ --name "v0.5.0"
  %(prog)s --id 10002 --dry-run
        """,
    )

    parser.add_argument(
        "project", nargs="?", help="Project key (required when using --name)"
    )
    parser.add_argument("--id", help="Version ID to archive")
    parser.add_argument("--name", "-n", help="Version name (requires project)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be archived without archiving",
    )
    parser.add_argument("--profile", "-p", help="JIRA profile to use")

    args = parser.parse_args(argv)

    # Validate arguments
    if args.id and args.name:
        print_error("Error: Cannot specify both --id and --name")
        sys.exit(1)

    if not args.id and not args.name:
        print_error("Error: Must specify either --id or --name")
        sys.exit(1)

    if args.name and not args.project:
        print_error("Error: --name requires project argument")
        sys.exit(1)

    try:
        if args.dry_run:
            # Dry run mode
            if args.id:
                archive_version_dry_run(version_id=args.id)
                print(f"[DRY RUN] Would archive version {args.id}\n")
                print("No version archived (dry-run mode).")
            else:
                # Can't do dry run by name without API call
                print_error("Error: Dry run only supported with --id")
                sys.exit(1)

        else:
            # Archive version
            if args.id:
                version = archive_version(version_id=args.id, profile=args.profile)
                version_name = version.get("name", args.id)
            else:
                version = archive_version_by_name(
                    project=args.project, version_name=args.name, profile=args.profile
                )
                version_name = version.get("name", args.name)

            print_success(f"Archived version '{version_name}' (ID: {version['id']})")
            if version.get("description"):
                print(f"Description: {version['description']}")

    except ValidationError as e:
        print_error(e)
        sys.exit(1)
    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
