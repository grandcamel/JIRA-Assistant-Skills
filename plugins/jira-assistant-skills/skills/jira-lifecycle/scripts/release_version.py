#!/usr/bin/env python3
"""
Release a project version in JIRA.

Usage:
    python release_version.py --id 10000
    python release_version.py --id 10000 --date 2025-03-01
    python release_version.py PROJ --name "v1.0.0"
    python release_version.py PROJ --name "v1.0.0" --description "First stable release"
"""

import argparse
import sys
from datetime import datetime
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    print_error,
    print_success,
)


def release_version(
    version_id: str,
    release_date: str | None = None,
    description: str | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    """
    Release a version by ID.

    Args:
        version_id: Version ID
        release_date: Optional release date (YYYY-MM-DD), defaults to today
        description: Optional updated description
        profile: JIRA profile to use

    Returns:
        Updated version data
    """
    # Default to today if not specified
    if release_date is None:
        release_date = datetime.now().strftime("%Y-%m-%d")

    update_data = {"released": True, "releaseDate": release_date}

    if description:
        update_data["description"] = description

    client = get_jira_client(profile)
    result = client.update_version(version_id, **update_data)
    client.close()

    return result


def release_version_by_name(
    project: str,
    version_name: str,
    release_date: str | None = None,
    description: str | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    """
    Release a version by name (requires project lookup).

    Args:
        project: Project key
        version_name: Version name
        release_date: Optional release date (YYYY-MM-DD)
        description: Optional updated description
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

    # Release the version
    if release_date is None:
        release_date = datetime.now().strftime("%Y-%m-%d")

    update_data = {"released": True, "releaseDate": release_date}

    if description:
        update_data["description"] = description

    result = client.update_version(version_id, **update_data)
    client.close()

    return result


def release_version_dry_run(
    version_id: str,
    release_date: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """
    Show what would be released without releasing.

    Args:
        version_id: Version ID
        release_date: Optional release date
        description: Optional description

    Returns:
        Update data that would be applied
    """
    if release_date is None:
        release_date = datetime.now().strftime("%Y-%m-%d")

    update_data = {
        "version_id": version_id,
        "released": True,
        "releaseDate": release_date,
    }

    if description:
        update_data["description"] = description

    return update_data


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Release a project version in JIRA",
        epilog="""
Examples:
  %(prog)s --id 10000
  %(prog)s --id 10000 --date 2025-03-01
  %(prog)s PROJ --name "v1.0.0"
  %(prog)s PROJ --name "v1.0.0" --description "First stable release"
  %(prog)s --id 10000 --dry-run
        """,
    )

    parser.add_argument(
        "project", nargs="?", help="Project key (required when using --name)"
    )
    parser.add_argument("--id", help="Version ID to release")
    parser.add_argument("--name", "-n", help="Version name (requires project)")
    parser.add_argument(
        "--date", "-d", help="Release date in YYYY-MM-DD format (default: today)"
    )
    parser.add_argument("--description", help="Update version description")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be released without releasing",
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
                update_data = release_version_dry_run(
                    version_id=args.id,
                    release_date=args.date,
                    description=args.description,
                )
                print(f"[DRY RUN] Would release version {args.id}:\n")
            else:
                # Can't do dry run by name without API call
                print_error("Error: Dry run only supported with --id")
                sys.exit(1)

            print(f"  Release Date: {update_data['releaseDate']}")
            if update_data.get("description"):
                print(f"  Description: {update_data['description']}")
            print("\nNo version released (dry-run mode).")

        else:
            # Release version
            if args.id:
                version = release_version(
                    version_id=args.id,
                    release_date=args.date,
                    description=args.description,
                    profile=args.profile,
                )
                version_name = version.get("name", args.id)
            else:
                version = release_version_by_name(
                    project=args.project,
                    version_name=args.name,
                    release_date=args.date,
                    description=args.description,
                    profile=args.profile,
                )
                version_name = version.get("name", args.name)

            print_success(f"Released version '{version_name}' (ID: {version['id']})")
            print(f"\nRelease Date: {version['releaseDate']}")
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
