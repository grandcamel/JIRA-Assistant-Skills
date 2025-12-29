#!/usr/bin/env python3
"""
Bulk update issues from JQL search results.

Usage:
    python bulk_update.py "project = PROJ AND labels = old" --add-labels "new"
    python bulk_update.py "assignee = user@example.com AND status = Open" --priority High
"""

import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from validators import validate_jql
from formatters import print_success, print_warning, print_info


def bulk_update(jql: str, add_labels: list = None, remove_labels: list = None,
               priority: str = None, max_issues: int = 100,
               dry_run: bool = False, profile: str = None) -> None:
    """
    Bulk update issues from search results.

    Args:
        jql: JQL query to find issues
        add_labels: Labels to add
        remove_labels: Labels to remove
        priority: Priority to set
        max_issues: Maximum issues to update
        dry_run: If True, show what would be updated without making changes
        profile: JIRA profile to use
    """
    jql = validate_jql(jql)

    client = get_jira_client(profile)
    results = client.search_issues(jql, fields=['key', 'summary', 'labels'], max_results=max_issues)

    issues = results.get('issues', [])
    total = results.get('total', 0)

    if not issues:
        print("No issues found to update")
        client.close()
        return

    if total > max_issues:
        print_warning(f"Found {total} issues, limiting to first {max_issues} (use --max-issues to change)")

    print_info(f"Will update {len(issues)} issue(s):")
    for issue in issues:
        print(f"  - {issue['key']}: {issue['fields'].get('summary', '')}")

    if dry_run:
        print("\n[DRY RUN] No changes made")
        client.close()
        return

    response = input(f"\nProceed with bulk update? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Bulk update cancelled")
        client.close()
        return

    updated = 0
    failed = 0

    for issue in issues:
        try:
            issue_key = issue['key']
            fields = {}

            if add_labels or remove_labels:
                current_labels = set(issue.get('fields', {}).get('labels', []))

                if add_labels:
                    current_labels.update(add_labels)
                if remove_labels:
                    current_labels.difference_update(remove_labels)

                fields['labels'] = list(current_labels)

            if priority:
                fields['priority'] = {'name': priority}

            if fields:
                client.update_issue(issue_key, fields, notify_users=False)
                updated += 1

        except Exception as e:
            print_warning(f"Failed to update {issue_key}: {e}")
            failed += 1

    client.close()

    print_success(f"\nUpdated {updated} issue(s)")
    if failed:
        print_warning(f"Failed: {failed} issue(s)")


def main():
    parser = argparse.ArgumentParser(
        description='Bulk update issues from JQL search',
        epilog='Example: python bulk_update.py "project = PROJ" --add-labels "reviewed"'
    )

    parser.add_argument('jql',
                       help='JQL query to find issues')
    parser.add_argument('--add-labels',
                       help='Comma-separated labels to add')
    parser.add_argument('--remove-labels',
                       help='Comma-separated labels to remove')
    parser.add_argument('--priority',
                       help='Priority to set (Highest, High, Medium, Low, Lowest)')
    parser.add_argument('--max-issues',
                       type=int,
                       default=100,
                       help='Maximum issues to update (default: 100)')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Show what would be updated without making changes')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        add_labels = [l.strip() for l in args.add_labels.split(',')] if args.add_labels else None
        remove_labels = [l.strip() for l in args.remove_labels.split(',')] if args.remove_labels else None

        bulk_update(
            jql=args.jql,
            add_labels=add_labels,
            remove_labels=remove_labels,
            priority=args.priority,
            max_issues=args.max_issues,
            dry_run=args.dry_run,
            profile=args.profile
        )

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nBulk update cancelled")
        sys.exit(0)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
