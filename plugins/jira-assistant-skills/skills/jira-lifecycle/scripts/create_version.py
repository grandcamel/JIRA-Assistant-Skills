#!/usr/bin/env python3
"""
Create a project version in JIRA.

Usage:
    python create_version.py PROJ --name "v1.0.0"
    python create_version.py PROJ --name "v1.0.0" --description "Major release"
    python create_version.py PROJ --name "v1.0.0" --start-date 2025-02-01 --release-date 2025-03-01
    python create_version.py PROJ --name "v1.0.0" --released
"""

import argparse
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    get_jira_client,
    print_error,
    print_success,
)


def create_version(
    project: str,
    name: str,
    description: str | None = None,
    start_date: str | None = None,
    release_date: str | None = None,
    released: bool = False,
    archived: bool = False,
    profile: str | None = None,
) -> dict[str, Any]:
    """
    Create a project version.

    Args:
        project: Project key (e.g., PROJ)
        name: Version name (e.g., v1.0.0)
        description: Optional description
        start_date: Optional start date (YYYY-MM-DD)
        release_date: Optional release date (YYYY-MM-DD)
        released: Mark as released
        archived: Mark as archived
        profile: JIRA profile to use

    Returns:
        Created version data
    """
    client = get_jira_client(profile)
    result = client.create_version(
        project=project,
        name=name,
        description=description,
        start_date=start_date,
        release_date=release_date,
        released=released,
        archived=archived,
    )
    client.close()

    return result


def create_version_dry_run(
    project: str,
    name: str,
    description: str | None = None,
    start_date: str | None = None,
    release_date: str | None = None,
    released: bool = False,
    archived: bool = False,
) -> dict[str, Any]:
    """
    Show what version would be created without creating it.

    Args:
        project: Project key
        name: Version name
        description: Optional description
        start_date: Optional start date
        release_date: Optional release date
        released: Mark as released
        archived: Mark as archived

    Returns:
        Version data that would be created
    """
    version_data = {
        "project": project,
        "name": name,
        "released": released,
        "archived": archived,
    }

    if description:
        version_data["description"] = description
    if start_date:
        version_data["startDate"] = start_date
    if release_date:
        version_data["releaseDate"] = release_date

    return version_data


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create a project version in JIRA",
        epilog="""
Examples:
  %(prog)s PROJ --name "v1.0.0"
  %(prog)s PROJ --name "v1.0.0" --description "Major release"
  %(prog)s PROJ --name "v1.0.0" --start-date 2025-02-01 --release-date 2025-03-01
  %(prog)s PROJ --name "v1.0.0" --released --dry-run
        """,
    )

    parser.add_argument("project", help="Project key (e.g., PROJ)")
    parser.add_argument(
        "--name", "-n", required=True, help="Version name (e.g., v1.0.0)"
    )
    parser.add_argument("--description", "-d", help="Version description")
    parser.add_argument("--start-date", help="Start date in YYYY-MM-DD format")
    parser.add_argument("--release-date", help="Release date in YYYY-MM-DD format")
    parser.add_argument(
        "--released", action="store_true", help="Mark version as released"
    )
    parser.add_argument(
        "--archived", action="store_true", help="Mark version as archived"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without creating",
    )
    parser.add_argument("--profile", "-p", help="JIRA profile to use")

    args = parser.parse_args(argv)

    try:
        if args.dry_run:
            # Dry run mode
            version_data = create_version_dry_run(
                project=args.project,
                name=args.name,
                description=args.description,
                start_date=args.start_date,
                release_date=args.release_date,
                released=args.released,
                archived=args.archived,
            )

            print(f"[DRY RUN] Would create version in project {args.project}:\n")
            print(f"  Name: {version_data['name']}")
            if version_data.get("description"):
                print(f"  Description: {version_data['description']}")
            if version_data.get("startDate"):
                print(f"  Start Date: {version_data['startDate']}")
            if version_data.get("releaseDate"):
                print(f"  Release Date: {version_data['releaseDate']}")
            print(f"  Released: {version_data['released']}")
            print(f"  Archived: {version_data['archived']}")
            print("\nNo version created (dry-run mode).")

        else:
            # Create version
            version = create_version(
                project=args.project,
                name=args.name,
                description=args.description,
                start_date=args.start_date,
                release_date=args.release_date,
                released=args.released,
                archived=args.archived,
                profile=args.profile,
            )

            version_id = version.get("id", "")
            print_success(
                f"Created version '{args.name}' in project {args.project} (ID: {version_id})"
            )

            # Show version details
            if version.get("description"):
                print(f"\nDescription: {version['description']}")
            if version.get("startDate"):
                print(f"Start Date: {version['startDate']}")
            if version.get("releaseDate"):
                print(f"Release Date: {version['releaseDate']}")
            if version.get("released"):
                print("Status: Released")
            if version.get("archived"):
                print("Status: Archived")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
