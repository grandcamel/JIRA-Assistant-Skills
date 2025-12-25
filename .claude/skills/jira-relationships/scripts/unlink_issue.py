#!/usr/bin/env python3
"""
Remove links from a JIRA issue.

Usage:
    python unlink_issue.py PROJ-123 --from PROJ-456
    python unlink_issue.py PROJ-123 --type blocks --all
    python unlink_issue.py PROJ-123 --from PROJ-456 --dry-run
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError, ValidationError
from validators import validate_issue_key
from formatters import print_success


def find_link_to_issue(links: list, target_key: str) -> dict:
    """
    Find a link to/from a specific issue.

    Args:
        links: List of issue links
        target_key: Issue key to find link to/from

    Returns:
        Link object or None
    """
    target_upper = target_key.upper()
    for link in links:
        if 'outwardIssue' in link:
            if link['outwardIssue']['key'].upper() == target_upper:
                return link
        if 'inwardIssue' in link:
            if link['inwardIssue']['key'].upper() == target_upper:
                return link
    return None


def unlink_issue(issue_key: str, from_issue: str = None, link_type: str = None,
                 remove_all: bool = False, dry_run: bool = False,
                 profile: str = None) -> dict:
    """
    Remove links from an issue.

    Args:
        issue_key: Source issue key
        from_issue: Specific issue to unlink from
        link_type: Type of links to remove
        remove_all: Remove all matching links
        dry_run: Preview without deleting
        profile: JIRA profile to use

    Returns:
        Dict with info about deleted links (for dry-run)

    Raises:
        ValidationError: If validation fails
    """
    issue_key = validate_issue_key(issue_key)

    if not from_issue and not (link_type and remove_all):
        raise ValidationError("Must specify --from ISSUE or --type TYPE with --all")

    if from_issue:
        from_issue = validate_issue_key(from_issue)

    client = get_jira_client(profile)

    try:
        links = client.get_issue_links(issue_key)

        links_to_delete = []

        if from_issue:
            # Find specific link
            link = find_link_to_issue(links, from_issue)
            if not link:
                raise ValidationError(f"{issue_key} is not linked to {from_issue}")
            links_to_delete.append(link)

        elif link_type and remove_all:
            # Find all links of this type
            type_lower = link_type.lower()
            links_to_delete = [l for l in links if l['type']['name'].lower() == type_lower]
            if not links_to_delete:
                raise ValidationError(f"No '{link_type}' links found for {issue_key}")

        if dry_run:
            # Return info about what would be deleted
            result = {
                'issue_key': issue_key,
                'links_to_delete': []
            }
            for link in links_to_delete:
                if 'outwardIssue' in link:
                    target = link['outwardIssue']['key']
                    direction = link['type']['outward']
                else:
                    target = link['inwardIssue']['key']
                    direction = link['type']['inward']
                result['links_to_delete'].append({
                    'id': link['id'],
                    'target': target,
                    'type': link['type']['name'],
                    'direction': direction
                })
            return result

        # Actually delete the links
        for link in links_to_delete:
            client.delete_link(link['id'])

    finally:
        client.close()

    return {'deleted_count': len(links_to_delete)}


def main():
    parser = argparse.ArgumentParser(
        description='Remove links from a JIRA issue',
        epilog='Example: python unlink_issue.py PROJ-123 --from PROJ-456'
    )

    parser.add_argument('issue_key',
                       help='Issue key to remove links from (e.g., PROJ-123)')

    parser.add_argument('--from', '-f',
                       dest='from_issue',
                       metavar='ISSUE',
                       help='Remove link to/from this specific issue')
    parser.add_argument('--type', '-t',
                       dest='link_type',
                       help='Type of links to remove (use with --all)')
    parser.add_argument('--all', '-a',
                       dest='remove_all',
                       action='store_true',
                       help='Remove all links of the specified type')
    parser.add_argument('--dry-run', '-n',
                       action='store_true',
                       help='Preview without deleting')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        result = unlink_issue(
            issue_key=args.issue_key,
            from_issue=args.from_issue,
            link_type=args.link_type,
            remove_all=args.remove_all,
            dry_run=args.dry_run,
            profile=args.profile
        )

        if args.dry_run and result:
            print(f"[DRY RUN] Would remove {len(result['links_to_delete'])} link(s):")
            for link in result['links_to_delete']:
                print(f"  - {link['direction']} {link['target']} ({link['type']})")
        else:
            count = result.get('deleted_count', 0)
            if args.from_issue:
                print_success(f"Removed link between {args.issue_key} and {args.from_issue}")
            else:
                print_success(f"Removed {count} '{args.link_type}' link(s) from {args.issue_key}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
