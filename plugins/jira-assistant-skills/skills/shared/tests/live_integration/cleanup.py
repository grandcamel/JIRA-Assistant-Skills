#!/usr/bin/env python3
"""
Standalone Cleanup Utility

Use this script to clean up test projects that weren't properly deleted
(e.g., due to test failures or interruptions).

Usage:
    python cleanup.py INT123ABC --profile development
    python cleanup.py --prefix INT --profile development  # Delete all INT* projects
    python cleanup.py --list --profile development        # List all INT* projects

Warning:
    This script permanently deletes projects. Use with caution!
"""

import sys
import argparse
from pathlib import Path

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts' / 'lib'))

from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, NotFoundError


def list_test_projects(client, prefix='INT'):
    """List all projects matching the prefix."""
    print(f"\nProjects matching prefix '{prefix}':")
    print("-" * 50)

    # Get all projects
    projects = client.get('/rest/api/3/project', operation='list projects')

    matching = []
    for project in projects:
        if project['key'].startswith(prefix):
            matching.append(project)
            print(f"  {project['key']}: {project['name']}")

    if not matching:
        print(f"  No projects found with prefix '{prefix}'")

    return matching


def cleanup_single_project(client, project_key, dry_run=False):
    """Clean up a single project."""
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Cleaning up project: {project_key}")

    try:
        # Verify project exists
        project = client.get_project(project_key)
        print(f"  Found: {project['name']}")
    except NotFoundError:
        print(f"  Project {project_key} not found")
        return False

    # Step 1: Count and delete issues
    try:
        result = client.search_issues(
            f"project = {project_key}",
            fields=['key'],
            max_results=0
        )
        issue_count = result.get('total', 0)
        print(f"  Issues to delete: {issue_count}")

        if not dry_run and issue_count > 0:
            deleted = 0
            while True:
                result = client.search_issues(
                    f"project = {project_key} ORDER BY created DESC",
                    fields=['key', 'issuetype'],
                    max_results=50
                )
                issues = result.get('issues', [])
                if not issues:
                    break

                # Delete subtasks first
                subtasks = [i for i in issues if i['fields']['issuetype'].get('subtask', False)]
                parents = [i for i in issues if not i['fields']['issuetype'].get('subtask', False)]

                for issue in subtasks + parents:
                    try:
                        client.delete_issue(issue['key'])
                        deleted += 1
                    except Exception as e:
                        print(f"    Warning: Could not delete {issue['key']}: {e}")

            print(f"  Deleted {deleted} issues")
    except Exception as e:
        print(f"  Error getting issues: {e}")

    # Step 2: Delete future sprints
    try:
        boards = client.get_all_boards(project_key=project_key)
        for board in boards.get('values', []):
            sprints = client.get_board_sprints(board['id'], state='future')
            for sprint in sprints.get('values', []):
                if not dry_run:
                    try:
                        client.delete_sprint(sprint['id'])
                        print(f"  Deleted sprint: {sprint['name']}")
                    except Exception as e:
                        print(f"    Warning: Could not delete sprint {sprint['id']}: {e}")
                else:
                    print(f"  Would delete sprint: {sprint['name']}")
    except Exception as e:
        print(f"  Error cleaning sprints: {e}")

    # Step 3: Delete project
    if not dry_run:
        try:
            client.delete_project(project_key, enable_undo=True)
            print(f"  Project {project_key} deleted (in trash for 60 days)")
            return True
        except Exception as e:
            print(f"  Error deleting project: {e}")
            return False
    else:
        print(f"  Would delete project: {project_key}")
        return True


def cleanup_by_prefix(client, prefix, dry_run=False):
    """Clean up all projects matching prefix."""
    projects = list_test_projects(client, prefix)

    if not projects:
        return

    if not dry_run:
        print(f"\nWill delete {len(projects)} project(s)")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted")
            return

    success = 0
    failed = 0

    for project in projects:
        if cleanup_single_project(client, project['key'], dry_run):
            success += 1
        else:
            failed += 1

    print(f"\nSummary: {success} deleted, {failed} failed")


def main():
    parser = argparse.ArgumentParser(
        description='Clean up test projects in JIRA',
        epilog='Example: python cleanup.py INT123ABC --profile development'
    )

    parser.add_argument('project_key', nargs='?',
                       help='Specific project key to delete')
    parser.add_argument('--prefix', '-p',
                       help='Delete all projects with this prefix')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List projects matching prefix (default: INT)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Show what would be deleted without doing it')
    parser.add_argument('--profile',
                       default='development',
                       help='JIRA profile to use (default: development)')

    args = parser.parse_args()

    if not args.project_key and not args.prefix and not args.list:
        parser.print_help()
        print("\nError: Specify either a project key, --prefix, or --list")
        sys.exit(1)

    try:
        client = get_jira_client(args.profile)

        if args.list:
            prefix = args.prefix if args.prefix else 'INT'
            list_test_projects(client, prefix)

        elif args.prefix:
            cleanup_by_prefix(client, args.prefix, args.dry_run)

        elif args.project_key:
            success = cleanup_single_project(client, args.project_key, args.dry_run)
            if not success and not args.dry_run:
                sys.exit(1)

        client.close()

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted")
        sys.exit(1)


if __name__ == '__main__':
    main()
