#!/usr/bin/env python3
"""
Move issues between versions in JIRA.

Usage:
    python move_issues_version.py --jql 'fixVersion = "v1.0.0"' --target "v2.0.0"
    python move_issues_version.py PROJ --from "v1.0.0" --to "v2.0.0"
    python move_issues_version.py --issues PROJ-1,PROJ-2 --target "v2.0.0"
    python move_issues_version.py --jql 'project = PROJ' --target "v2.0.0" --dry-run
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from formatters import print_success


def move_issues_to_version(jql: str, target_version: str, field: str = 'fixVersions',
                           profile: str = None) -> Dict[str, Any]:
    """
    Move issues found by JQL to a target version.

    Args:
        jql: JQL query to find issues
        target_version: Target version name
        field: Version field to update (fixVersions or affectedVersions)
        profile: JIRA profile to use

    Returns:
        Dictionary with moved count
    """
    client = get_jira_client(profile)

    # Search for issues
    result = client.search_issues(jql, max_results=1000)
    issues = result.get('issues', [])

    # Update each issue
    moved = 0
    for issue in issues:
        client.update_issue(
            issue['key'],
            fields={field: [{'name': target_version}]}
        )
        moved += 1

    client.close()

    return {'moved': moved}


def move_issues_between_versions(project: str, source_version: str,
                                 target_version: str, field: str = 'fixVersions',
                                 profile: str = None) -> Dict[str, Any]:
    """
    Move issues from one version to another in a project.

    Args:
        project: Project key
        source_version: Source version name
        target_version: Target version name
        field: Version field to update
        profile: JIRA profile to use

    Returns:
        Dictionary with moved count
    """
    # Build JQL to find issues in source version
    jql = f'project = {project} AND {field} = "{source_version}"'

    return move_issues_to_version(jql, target_version, field, profile)


def move_specific_issues(issue_keys: List[str], target_version: str,
                        field: str = 'fixVersions', profile: str = None) -> Dict[str, Any]:
    """
    Move specific issues to a target version.

    Args:
        issue_keys: List of issue keys
        target_version: Target version name
        field: Version field to update
        profile: JIRA profile to use

    Returns:
        Dictionary with moved count
    """
    client = get_jira_client(profile)

    # Update each issue
    moved = 0
    for key in issue_keys:
        client.update_issue(
            key,
            fields={field: [{'name': target_version}]}
        )
        moved += 1

    client.close()

    return {'moved': moved}


def move_issues_dry_run(jql: str, target_version: str, profile: str = None) -> Dict[str, Any]:
    """
    Show what issues would be moved without moving them.

    Args:
        jql: JQL query
        target_version: Target version name
        profile: JIRA profile to use

    Returns:
        Dictionary with would_move count and issue list
    """
    client = get_jira_client(profile)
    result = client.search_issues(jql, max_results=1000)
    issues = result.get('issues', [])
    client.close()

    return {
        'would_move': len(issues),
        'issues': [{'key': i['key'], 'summary': i['fields'].get('summary', '')} for i in issues]
    }


def move_issues_with_confirmation(jql: str, target_version: str,
                                  field: str = 'fixVersions', profile: str = None) -> Dict[str, Any]:
    """
    Move issues with confirmation prompt.

    Args:
        jql: JQL query
        target_version: Target version name
        field: Version field to update
        profile: JIRA profile to use

    Returns:
        Dictionary with moved count
    """
    # First, do a dry run to show what would be moved
    dry_run = move_issues_dry_run(jql, target_version, profile)

    print(f"Found {dry_run['would_move']} issue(s) to move to '{target_version}':\n")
    for issue in dry_run['issues'][:10]:  # Show first 10
        print(f"  {issue['key']}: {issue['summary']}")
    if len(dry_run['issues']) > 10:
        print(f"  ... and {len(dry_run['issues']) - 10} more")

    print()
    confirmation = input(f"Move these {dry_run['would_move']} issue(s) to version '{target_version}'? (yes/no): ")

    if confirmation.lower() == 'yes':
        return move_issues_to_version(jql, target_version, field, profile)
    else:
        return {'moved': 0}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Move issues between versions in JIRA',
        epilog='''
Examples:
  %(prog)s --jql 'fixVersion = "v1.0.0"' --target "v2.0.0"
  %(prog)s PROJ --from "v1.0.0" --to "v2.0.0"
  %(prog)s --issues PROJ-1,PROJ-2 --target "v2.0.0"
  %(prog)s --jql 'project = PROJ' --target "v2.0.0" --dry-run
        '''
    )

    parser.add_argument('project',
                       nargs='?',
                       help='Project key (required when using --from/--to)')
    parser.add_argument('--jql',
                       help='JQL query to find issues to move')
    parser.add_argument('--from', dest='source_version',
                       help='Source version name (requires project)')
    parser.add_argument('--to', dest='target_version',
                       help='Target version name (for --from/--to)')
    parser.add_argument('--target', '-t',
                       help='Target version name (for --jql or --issues)')
    parser.add_argument('--issues',
                       help='Comma-separated list of issue keys')
    parser.add_argument('--field', '-f',
                       choices=['fixVersions', 'affectedVersions'],
                       default='fixVersions',
                       help='Version field to update (default: fixVersions)')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Skip confirmation prompt')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be moved without moving')
    parser.add_argument('--profile', '-p',
                       help='JIRA profile to use')

    args = parser.parse_args()

    # Validate arguments
    if args.jql and (args.source_version or args.target_version):
        print_error("Error: Cannot use --jql with --from/--to")
        sys.exit(1)

    if args.issues and (args.jql or args.source_version):
        print_error("Error: Cannot use --issues with --jql or --from")
        sys.exit(1)

    if args.source_version and not args.project:
        print_error("Error: --from requires project argument")
        sys.exit(1)

    if args.source_version and not args.target_version:
        print_error("Error: --from requires --to")
        sys.exit(1)

    # Determine which mode
    if args.jql:
        if not args.target:
            print_error("Error: --jql requires --target")
            sys.exit(1)
    elif args.issues:
        if not args.target:
            print_error("Error: --issues requires --target")
            sys.exit(1)
    elif args.source_version:
        # Using --from/--to
        pass
    else:
        print_error("Error: Must specify --jql, --issues, or --from/--to")
        sys.exit(1)

    try:
        if args.dry_run:
            # Dry run mode
            if args.jql:
                jql = args.jql
            elif args.source_version:
                jql = f'project = {args.project} AND {args.field} = "{args.source_version}"'
            else:
                print_error("Error: --dry-run not supported with --issues")
                sys.exit(1)

            target = args.target or args.target_version
            dry_run = move_issues_dry_run(jql, target, args.profile)

            print(f"[DRY RUN] Would move {dry_run['would_move']} issue(s) to '{target}':\n")
            for issue in dry_run['issues']:
                print(f"  {issue['key']}: {issue['summary']}")
            print("\nNo issues moved (dry-run mode).")

        else:
            # Move issues
            if args.jql:
                jql = args.jql
                target = args.target

                if args.yes:
                    result = move_issues_to_version(jql, target, args.field, args.profile)
                else:
                    result = move_issues_with_confirmation(jql, target, args.field, args.profile)

            elif args.issues:
                issue_keys = [k.strip() for k in args.issues.split(',')]
                result = move_specific_issues(issue_keys, args.target, args.field, args.profile)

            elif args.source_version:
                result = move_issues_between_versions(
                    args.project,
                    args.source_version,
                    args.target_version,
                    args.field,
                    args.profile
                )

            if result['moved'] > 0:
                target = args.target or args.target_version
                print_success(f"Moved {result['moved']} issue(s) to version '{target}'")
            else:
                print("No issues moved.")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
