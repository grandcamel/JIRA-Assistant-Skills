#!/usr/bin/env python3
"""
Create a link between two JIRA issues.

WHEN TO USE THIS SCRIPT:
- Creating dependencies: --blocks for sequential work
- Marking duplicates: --duplicates then close the duplicate issue
- Cross-team awareness: --relates-to for related work
- Cloning relationships: --clones for issue templates

LINK DIRECTION:
- --blocks PROJ-2: This issue blocks PROJ-2 (PROJ-2 waits for this)
- --is-blocked-by PROJ-2: This issue is blocked by PROJ-2 (this waits for PROJ-2)

IMPORTANT: Issue links are labels only - they do NOT enforce workflow rules.
Combine with workflow validators or team discipline for enforcement.

Usage:
    python link_issue.py PROJ-1 --blocks PROJ-2
    python link_issue.py PROJ-1 --duplicates PROJ-2
    python link_issue.py PROJ-1 --relates-to PROJ-2
    python link_issue.py PROJ-1 --type "Blocks" --to PROJ-2
"""

import sys
import argparse
from pathlib import Path


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, ValidationError
from jira_assistant_skills_lib import validate_issue_key
from jira_assistant_skills_lib import print_success
from jira_assistant_skills_lib import text_to_adf


# Mapping of semantic flags to JIRA link type names
LINK_TYPE_MAPPING = {
    'blocks': 'Blocks',
    'is_blocked_by': 'Blocks',
    'duplicates': 'Duplicate',
    'is_duplicated_by': 'Duplicate',
    'relates_to': 'Relates',
    'clones': 'Cloners',
    'is_cloned_by': 'Cloners',
}


def find_link_type(link_types: list, name: str) -> dict:
    """
    Find a link type by name (case-insensitive).

    Args:
        link_types: List of available link types
        name: Link type name to find

    Returns:
        Link type object

    Raises:
        ValidationError: If link type not found
    """
    name_lower = name.lower()

    for lt in link_types:
        if lt['name'].lower() == name_lower:
            return lt

    available = ', '.join(lt['name'] for lt in link_types)
    raise ValidationError(f"Link type '{name}' not found. Available: {available}")


def link_issue(issue_key: str, blocks: str = None, duplicates: str = None,
               relates_to: str = None, clones: str = None,
               is_blocked_by: str = None, is_duplicated_by: str = None,
               is_cloned_by: str = None, link_type: str = None,
               target_issue: str = None, comment: str = None,
               dry_run: bool = False, profile: str = None) -> dict:
    """
    Create a link between two issues.

    Args:
        issue_key: Source issue key
        blocks: Issue that this issue blocks
        duplicates: Issue that this issue duplicates
        relates_to: Issue that this issue relates to
        clones: Issue that this issue clones
        is_blocked_by: Issue that blocks this issue
        is_duplicated_by: Issue that duplicates this issue
        is_cloned_by: Issue that clones this issue
        link_type: Explicit link type name
        target_issue: Target issue when using explicit type
        comment: Optional comment
        dry_run: Preview without creating
        profile: JIRA profile to use

    Returns:
        Dict with link info (for dry-run) or None

    Raises:
        ValidationError: If validation fails
    """
    # Validate source issue key
    issue_key = validate_issue_key(issue_key)

    # Determine link type and target from semantic flags or explicit type
    resolved_type = None
    resolved_target = None
    is_inward = False  # True if source is the "inward" side (e.g., "is blocked by")

    semantic_args = {
        'blocks': blocks,
        'duplicates': duplicates,
        'relates_to': relates_to,
        'clones': clones,
        'is_blocked_by': is_blocked_by,
        'is_duplicated_by': is_duplicated_by,
        'is_cloned_by': is_cloned_by,
    }

    # Check semantic flags
    for flag_name, flag_value in semantic_args.items():
        if flag_value:
            resolved_type = LINK_TYPE_MAPPING[flag_name]
            resolved_target = flag_value
            # Inward flags (is_blocked_by, etc.) flip the direction
            is_inward = flag_name.startswith('is_')
            break

    # Check explicit type
    if link_type and target_issue:
        resolved_type = link_type
        resolved_target = target_issue

    if not resolved_type or not resolved_target:
        raise ValidationError("Must specify a link type (--blocks, --duplicates, etc.) or --type with --to")

    # Validate target issue key
    resolved_target = validate_issue_key(resolved_target)

    # Check for self-reference
    if issue_key.upper() == resolved_target.upper():
        raise ValidationError("Cannot link an issue to itself")

    # Get client and validate link type exists
    client = get_jira_client(profile)

    try:
        link_types = client.get_link_types()
        link_type_obj = find_link_type(link_types, resolved_type)

        # Determine inward/outward issues based on direction
        # For "blocks": outward issue "blocks" inward issue
        # PROJ-1 blocks PROJ-2 means: PROJ-1 is outward (blocks), PROJ-2 is inward (is blocked by)
        if is_inward:
            # Source is on the "inward" side (e.g., "is blocked by")
            # So target is the outward issue
            inward_key = issue_key
            outward_key = resolved_target
        else:
            # Source is on the "outward" side (e.g., "blocks")
            inward_key = resolved_target
            outward_key = issue_key

        # Prepare comment if provided
        adf_comment = None
        if comment:
            adf_comment = text_to_adf(comment)

        # Dry run - just return info
        if dry_run:
            direction = link_type_obj.get('outward', resolved_type) if not is_inward else link_type_obj.get('inward', resolved_type)
            return {
                'source': issue_key,
                'target': resolved_target,
                'link_type': link_type_obj['name'],
                'direction': direction,
                'preview': f"{issue_key} {direction} {resolved_target}"
            }

        # Create the link
        client.create_link(link_type_obj['name'], inward_key, outward_key, adf_comment)

    finally:
        client.close()

    return None


def main():
    parser = argparse.ArgumentParser(
        description='Create a link between two JIRA issues',
        epilog='Example: python link_issue.py PROJ-1 --blocks PROJ-2'
    )

    parser.add_argument('issue_key',
                       help='Source issue key (e.g., PROJ-123)')

    # Semantic link flags (outward direction - source does X to target)
    link_group = parser.add_argument_group('Link Types (choose one)')
    link_group.add_argument('--blocks',
                           metavar='ISSUE',
                           help='This issue blocks the specified issue')
    link_group.add_argument('--duplicates',
                           metavar='ISSUE',
                           help='This issue duplicates the specified issue')
    link_group.add_argument('--relates-to',
                           metavar='ISSUE',
                           help='This issue relates to the specified issue')
    link_group.add_argument('--clones',
                           metavar='ISSUE',
                           help='This issue clones the specified issue')

    # Inward direction flags (target does X to source)
    link_group.add_argument('--is-blocked-by',
                           metavar='ISSUE',
                           help='This issue is blocked by the specified issue')
    link_group.add_argument('--is-duplicated-by',
                           metavar='ISSUE',
                           help='This issue is duplicated by the specified issue')
    link_group.add_argument('--is-cloned-by',
                           metavar='ISSUE',
                           help='This issue is cloned by the specified issue')

    # Explicit type option
    explicit_group = parser.add_argument_group('Explicit Link Type')
    explicit_group.add_argument('--type', '-t',
                               dest='link_type',
                               help='Link type name (e.g., "Blocks", "Duplicate")')
    explicit_group.add_argument('--to',
                               dest='target_issue',
                               metavar='ISSUE',
                               help='Target issue when using --type')

    # Options
    parser.add_argument('--comment', '-c',
                       help='Comment to add with the link')
    parser.add_argument('--dry-run', '-n',
                       action='store_true',
                       help='Preview without creating the link')
    parser.add_argument('--profile',
                       help='JIRA profile to use (default: from config)')

    args = parser.parse_args()

    try:
        result = link_issue(
            issue_key=args.issue_key,
            blocks=args.blocks,
            duplicates=args.duplicates,
            relates_to=getattr(args, 'relates_to', None),
            clones=args.clones,
            is_blocked_by=getattr(args, 'is_blocked_by', None),
            is_duplicated_by=getattr(args, 'is_duplicated_by', None),
            is_cloned_by=getattr(args, 'is_cloned_by', None),
            link_type=args.link_type,
            target_issue=args.target_issue,
            comment=args.comment,
            dry_run=args.dry_run,
            profile=args.profile
        )

        if args.dry_run and result:
            print(f"[DRY RUN] Would create link: {result['preview']}")
        else:
            # Determine what we linked
            target = (args.blocks or args.duplicates or
                     getattr(args, 'relates_to', None) or args.clones or
                     getattr(args, 'is_blocked_by', None) or
                     getattr(args, 'is_duplicated_by', None) or
                     getattr(args, 'is_cloned_by', None) or args.target_issue)
            print_success(f"Linked {args.issue_key} to {target}")

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
