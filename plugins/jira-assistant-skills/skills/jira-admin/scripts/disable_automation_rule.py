#!/usr/bin/env python3
"""
Disable an automation rule.

Disables an active automation rule by ID or name.

Usage:
    python disable_automation_rule.py RULE_ID
    python disable_automation_rule.py --name "Rule Name"
    python disable_automation_rule.py RULE_ID --dry-run
    python disable_automation_rule.py RULE_ID --confirm
    python disable_automation_rule.py RULE_ID --profile development
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Add shared lib to path

from jira_assistant_skills_lib import get_automation_client
from jira_assistant_skills_lib import print_error, JiraError, AutomationError, AutomationNotFoundError


def disable_automation_rule(
    client=None,
    rule_id: Optional[str] = None,
    name: Optional[str] = None,
    dry_run: bool = False,
    profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    Disable an automation rule.

    Args:
        client: AutomationClient instance (optional, created if not provided)
        rule_id: Rule UUID/ARI to disable
        name: Rule name to search for (alternative to rule_id)
        dry_run: If True, preview the change without applying
        profile: JIRA profile to use

    Returns:
        Updated rule data or dry-run preview

    Raises:
        AutomationNotFoundError: If rule not found
        ValueError: If neither rule_id nor name provided
    """
    if client is None:
        client = get_automation_client(profile)

    if not rule_id and not name:
        raise ValueError("Either rule_id or name must be provided")

    # If name provided, search for it first
    if name and not rule_id:
        response = client.search_rules(limit=100)
        rules = response.get('values', [])

        matching_rules = [r for r in rules if r.get('name') == name]
        if not matching_rules:
            matching_rules = [r for r in rules if name.lower() in r.get('name', '').lower()]

        if not matching_rules:
            raise AutomationNotFoundError("Automation rule", name)

        if len(matching_rules) > 1:
            names = [r.get('name') for r in matching_rules]
            raise ValueError(f"Multiple rules match '{name}': {names}")

        rule_id = matching_rules[0].get('id')

    if dry_run:
        # Get current rule state for preview
        rule = client.get_rule(rule_id)
        return {
            'dry_run': True,
            'would_disable': True,
            'rule_id': rule_id,
            'name': rule.get('name'),
            'current_state': rule.get('state'),
            'new_state': 'DISABLED'
        }

    # Disable the rule
    return client.disable_rule(rule_id)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='Disable an automation rule',
        epilog='''
Examples:
    # Disable rule by ID
    python disable_automation_rule.py "ari:cloud:jira::site/12345..."

    # Disable rule by name
    python disable_automation_rule.py --name "Auto-assign to lead"

    # Preview without making changes
    python disable_automation_rule.py RULE_ID --dry-run

    # Disable with confirmation (skip prompt)
    python disable_automation_rule.py RULE_ID --confirm

    # Output as JSON
    python disable_automation_rule.py RULE_ID --output json

    # Use specific profile
    python disable_automation_rule.py RULE_ID --profile development
        '''
    )

    parser.add_argument('rule_id', nargs='?', help='Rule ID (UUID/ARI format)')
    parser.add_argument('--name', '-n', help='Rule name to search for')
    parser.add_argument('--dry-run', '-d', action='store_true',
                        help='Preview changes without applying')
    parser.add_argument('--confirm', '-y', action='store_true',
                        help='Skip confirmation prompt')
    parser.add_argument('--output', '-o', choices=['text', 'json'],
                        default='text', help='Output format (default: text)')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args(argv)

    if not args.rule_id and not args.name:
        parser.error("Either rule_id or --name must be provided")

    try:
        # For non-dry-run, check if confirmation needed
        if not args.dry_run and not args.confirm:
            # First get the rule to show what will be disabled
            client = get_automation_client(args.profile)
            if args.name:
                response = client.search_rules(limit=100)
                rules = response.get('values', [])
                matching_rules = [r for r in rules if args.name.lower() in r.get('name', '').lower()]
                if matching_rules:
                    rule = matching_rules[0]
                else:
                    raise AutomationNotFoundError("Automation rule", args.name)
            else:
                rule = client.get_rule(args.rule_id)

            print(f"\nAbout to disable rule:")
            print(f"  Name: {rule.get('name')}")
            print(f"  Current State: {rule.get('state')}")

            confirmation = input("\nAre you sure? (y/N): ")
            if confirmation.lower() != 'y':
                print("Operation cancelled.")
                sys.exit(0)

        result = disable_automation_rule(
            rule_id=args.rule_id,
            name=args.name,
            dry_run=args.dry_run,
            profile=args.profile
        )

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            if args.dry_run:
                print("\n[DRY RUN] Would disable rule:")
                print(f"  Rule ID: {result.get('rule_id')}")
                print(f"  Name: {result.get('name')}")
                print(f"  Current State: {result.get('current_state')}")
                print(f"  New State: {result.get('new_state')}")
            else:
                print("\nRule State Updated")
                print("=" * 40)
                print(f"Rule ID: {result.get('id')}")
                print(f"Name: {result.get('name')}")
                print(f"State: {result.get('state')}")
                print(f"\nSuccess: Rule has been disabled.")

    except (JiraError, AutomationError) as e:
        print_error(e)
        sys.exit(1)
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
