#!/usr/bin/env python3
"""
Toggle automation rule state.

Toggles an automation rule between enabled and disabled states.

Usage:
    python toggle_automation_rule.py RULE_ID
    python toggle_automation_rule.py --name "Rule Name"
    python toggle_automation_rule.py RULE_ID --dry-run
    python toggle_automation_rule.py RULE_ID --profile development
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_automation_client
from error_handler import print_error, JiraError, AutomationError, AutomationNotFoundError


def toggle_automation_rule(
    client=None,
    rule_id: Optional[str] = None,
    name: Optional[str] = None,
    dry_run: bool = False,
    profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    Toggle automation rule state.

    If rule is enabled, disable it. If disabled, enable it.

    Args:
        client: AutomationClient instance (optional, created if not provided)
        rule_id: Rule UUID/ARI to toggle
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

    # Get current state
    rule = client.get_rule(rule_id)
    current_state = rule.get('state', 'UNKNOWN')
    new_state = 'DISABLED' if current_state == 'ENABLED' else 'ENABLED'

    if dry_run:
        return {
            'dry_run': True,
            'would_toggle': True,
            'rule_id': rule_id,
            'name': rule.get('name'),
            'current_state': current_state,
            'new_state': new_state
        }

    # Toggle the state
    if current_state == 'ENABLED':
        return client.disable_rule(rule_id)
    else:
        return client.enable_rule(rule_id)


def main():
    parser = argparse.ArgumentParser(
        description='Toggle automation rule state',
        epilog='''
Examples:
    # Toggle rule by ID
    python toggle_automation_rule.py "ari:cloud:jira::site/12345..."

    # Toggle rule by name
    python toggle_automation_rule.py --name "Auto-assign to lead"

    # Preview without making changes
    python toggle_automation_rule.py RULE_ID --dry-run

    # Output as JSON
    python toggle_automation_rule.py RULE_ID --output json

    # Use specific profile
    python toggle_automation_rule.py RULE_ID --profile development
        '''
    )

    parser.add_argument('rule_id', nargs='?', help='Rule ID (UUID/ARI format)')
    parser.add_argument('--name', '-n', help='Rule name to search for')
    parser.add_argument('--dry-run', '-d', action='store_true',
                        help='Preview changes without applying')
    parser.add_argument('--output', '-o', choices=['text', 'json'],
                        default='text', help='Output format (default: text)')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    if not args.rule_id and not args.name:
        parser.error("Either rule_id or --name must be provided")

    try:
        result = toggle_automation_rule(
            rule_id=args.rule_id,
            name=args.name,
            dry_run=args.dry_run,
            profile=args.profile
        )

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            if args.dry_run:
                print("\n[DRY RUN] Would toggle rule:")
                print(f"  Rule ID: {result.get('rule_id')}")
                print(f"  Name: {result.get('name')}")
                print(f"  Current State: {result.get('current_state')}")
                print(f"  New State: {result.get('new_state')}")
            else:
                print("\nRule State Toggled")
                print("=" * 40)
                print(f"Rule ID: {result.get('id')}")
                print(f"Name: {result.get('name')}")
                print(f"New State: {result.get('state')}")
                print(f"\nSuccess: Rule state has been toggled.")

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
