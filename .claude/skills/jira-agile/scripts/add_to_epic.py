#!/usr/bin/env python3
"""
Add issues to an Epic in JIRA (or remove them from epics).

Usage:
    python add_to_epic.py --epic PROJ-100 --issues PROJ-101,PROJ-102
    python add_to_epic.py --epic PROJ-100 --issues PROJ-101 --dry-run
    python add_to_epic.py --remove --issues PROJ-101
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional, Dict

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib'))

# Imports from shared library
from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from validators import validate_issue_key
from formatters import print_success, print_warning

# Epic Link custom field (may vary per instance)
EPIC_LINK_FIELD = 'customfield_10014'


def add_to_epic(epic_key: Optional[str] = None,
                issue_keys: List[str] = None,
                dry_run: bool = False,
                remove: bool = False,
                profile: str = None,
                client=None) -> Dict:
    """
    Add issues to an epic or remove them from epics.

    Args:
        epic_key: Epic key to add issues to (None if removing)
        issue_keys: List of issue keys to add/remove
        dry_run: Preview changes without making them
        remove: Remove issues from epic instead of adding
        profile: JIRA profile to use
        client: JiraClient instance (for testing)

    Returns:
        Result dictionary with counts:
        - added: Number of issues added
        - removed: Number of issues removed
        - failed: Number of failures
        - would_add: Number that would be added (dry-run only)
        - failures: List of failure details

    Raises:
        ValidationError: If epic is not Epic type
        JiraError: If epic doesn't exist
    """
    # Validate inputs
    if not remove and not epic_key:
        raise ValidationError("Epic key is required (or use --remove)")

    if not issue_keys:
        raise ValidationError("At least one issue key is required")

    # Initialize client
    if not client:
        client = get_jira_client(profile)
        should_close = True
    else:
        should_close = False

    try:
        result = {
            'added': 0,
            'removed': 0,
            'failed': 0,
            'failures': []
        }

        # Validate epic exists and is Epic type (unless removing)
        if not remove:
            epic_key = validate_issue_key(epic_key)
            epic = client.get_issue(epic_key)

            if epic['fields']['issuetype']['name'] != 'Epic':
                raise ValidationError(
                    f"{epic_key} is not an Epic (type: {epic['fields']['issuetype']['name']})"
                )

        # Dry run mode
        if dry_run:
            result['would_add'] = len(issue_keys)
            return result

        # Process each issue
        for issue_key in issue_keys:
            try:
                issue_key = validate_issue_key(issue_key)

                # Build update fields
                fields = {
                    EPIC_LINK_FIELD: epic_key if not remove else None
                }

                # Update the issue
                client.update_issue(issue_key, fields)

                if remove:
                    result['removed'] += 1
                else:
                    result['added'] += 1

            except JiraError as e:
                result['failed'] += 1
                result['failures'].append({
                    'issue': issue_key,
                    'error': str(e)
                })
            except ValidationError as e:
                result['failed'] += 1
                result['failures'].append({
                    'issue': issue_key,
                    'error': str(e)
                })

        return result

    finally:
        if should_close:
            client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Add issues to an Epic in JIRA',
        epilog='Example: python add_to_epic.py --epic PROJ-100 --issues PROJ-101,PROJ-102,PROJ-103'
    )

    parser.add_argument('--epic', '-e',
                       help='Epic key (e.g., PROJ-100)')
    parser.add_argument('--issues', '-i',
                       help='Comma-separated issue keys to add to epic')
    parser.add_argument('--jql', '-j',
                       help='JQL query to find issues to add')
    parser.add_argument('--remove', '-r',
                       action='store_true',
                       help='Remove issues from epic instead of adding')
    parser.add_argument('--dry-run', '-n',
                       action='store_true',
                       help='Preview changes without making them')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        # Validate required arguments
        if not args.remove and not args.epic:
            parser.error("--epic is required (or use --remove)")

        if not args.issues and not args.jql:
            parser.error("either --issues or --jql is required")

        # Parse issue keys
        issue_keys = []
        if args.issues:
            issue_keys = [k.strip() for k in args.issues.split(',')]

        # Handle JQL query
        if args.jql:
            client = get_jira_client(args.profile)
            try:
                jql_results = client.search_issues(args.jql)
                jql_keys = [issue['key'] for issue in jql_results.get('issues', [])]
                issue_keys.extend(jql_keys)
                print(f"Found {len(jql_keys)} issues from JQL query")
            finally:
                client.close()

        if not issue_keys:
            print_warning("No issues to process")
            return

        # Dry run preview
        if args.dry_run:
            print_warning("DRY RUN MODE - No changes will be made")
            if args.remove:
                print(f"Would remove {len(issue_keys)} issues from their epics:")
            else:
                print(f"Would add {len(issue_keys)} issues to epic {args.epic}:")
            for key in issue_keys:
                print(f"  - {key}")
            return

        # Perform the operation
        result = add_to_epic(
            epic_key=args.epic,
            issue_keys=issue_keys,
            dry_run=args.dry_run,
            remove=args.remove,
            profile=args.profile
        )

        # Report results
        if args.remove:
            if result['removed'] > 0:
                print_success(f"Removed {result['removed']} issues from epics")
        else:
            if result['added'] > 0:
                print_success(f"Added {result['added']} issues to epic {args.epic}")

        if result['failed'] > 0:
            print_warning(f"{result['failed']} issues failed:")
            for failure in result['failures']:
                print(f"  - {failure['issue']}: {failure['error']}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except ValidationError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
