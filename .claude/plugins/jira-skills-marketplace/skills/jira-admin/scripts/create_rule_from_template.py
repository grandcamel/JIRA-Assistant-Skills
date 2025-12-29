#!/usr/bin/env python3
"""
Create an automation rule from a template.

Creates a new automation rule based on an existing template.

Usage:
    python create_rule_from_template.py TEMPLATE_ID --project PROJ
    python create_rule_from_template.py TEMPLATE_ID --project PROJ --name "My Rule"
    python create_rule_from_template.py TEMPLATE_ID --project PROJ --param key=value
    python create_rule_from_template.py TEMPLATE_ID --config template_config.json
    python create_rule_from_template.py TEMPLATE_ID --project PROJ --dry-run
    python create_rule_from_template.py TEMPLATE_ID --project PROJ --profile development
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_automation_client
from error_handler import print_error, JiraError, AutomationError


def create_rule_from_template(
    client=None,
    template_id: str = None,
    project: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    name: Optional[str] = None,
    scope: Optional[str] = None,
    dry_run: bool = False,
    profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an automation rule from a template.

    Args:
        client: AutomationClient instance (optional, created if not provided)
        template_id: Template ID to use
        project: Project key for scope
        parameters: Template parameters
        name: Custom rule name
        scope: Rule scope (project ARI)
        dry_run: If True, preview without creating
        profile: JIRA profile to use

    Returns:
        Created rule data or dry-run preview

    Raises:
        ValueError: If template_id not provided
    """
    if client is None:
        client = get_automation_client(profile)

    if not template_id:
        raise ValueError("template_id is required")

    # Build parameters dict
    params = parameters or {}
    if project and 'projectKey' not in params:
        params['projectKey'] = project

    # Build scope from project if not provided
    if project and not scope:
        scope = f"ari:cloud:jira:*:project/{project}"

    if dry_run:
        # Get template info for preview
        template = client.get_template(template_id)
        return {
            'dry_run': True,
            'would_create': True,
            'template_id': template_id,
            'template_name': template.get('name'),
            'parameters': params,
            'name': name,
            'scope': scope
        }

    # Create the rule
    return client.create_rule_from_template(
        template_id=template_id,
        parameters=params,
        name=name,
        scope=scope
    )


def parse_param(param_str: str) -> tuple:
    """Parse a key=value parameter string."""
    if '=' not in param_str:
        raise ValueError(f"Invalid parameter format: {param_str}. Use key=value")
    key, value = param_str.split('=', 1)
    # Try to parse as JSON for complex values
    try:
        value = json.loads(value)
    except json.JSONDecodeError:
        pass  # Keep as string
    return key, value


def main():
    parser = argparse.ArgumentParser(
        description='Create an automation rule from a template',
        epilog='''
Examples:
    # Create from template
    python create_rule_from_template.py template-001 --project PROJ

    # With custom name
    python create_rule_from_template.py template-001 --project PROJ \\
      --name "Custom Rule Name"

    # With parameters
    python create_rule_from_template.py template-001 --project PROJ \\
      --param projectKey=PROJ \\
      --param assignee="john@example.com"

    # From JSON config file
    python create_rule_from_template.py template-001 --config template_config.json

    # Preview without creating
    python create_rule_from_template.py template-001 --project PROJ --dry-run

    # Output as JSON
    python create_rule_from_template.py template-001 --project PROJ --output json

    # Use specific profile
    python create_rule_from_template.py template-001 --project PROJ --profile development
        '''
    )

    parser.add_argument('template_id', help='Template ID')
    parser.add_argument('--project', '-p', help='Project key')
    parser.add_argument('--name', '-n', help='Custom rule name')
    parser.add_argument('--param', action='append', dest='params',
                        help='Parameter in key=value format (can be used multiple times)')
    parser.add_argument('--config', '-f', help='JSON config file with parameters')
    parser.add_argument('--dry-run', '-d', action='store_true',
                        help='Preview without creating')
    parser.add_argument('--output', '-o', choices=['text', 'json'],
                        default='text', help='Output format (default: text)')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    # Must have either project or config
    if not args.project and not args.config:
        parser.error("Either --project or --config must be provided")

    try:
        # Load config from file if provided
        parameters = {}
        if args.config:
            with open(args.config, 'r') as f:
                config_data = json.load(f)
                parameters = config_data.get('parameters', config_data)

        # Add command-line params
        if args.params:
            for param_str in args.params:
                key, value = parse_param(param_str)
                parameters[key] = value

        result = create_rule_from_template(
            template_id=args.template_id,
            project=args.project,
            parameters=parameters,
            name=args.name,
            dry_run=args.dry_run,
            profile=args.profile
        )

        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            if args.dry_run:
                print("\n[DRY RUN] Would create rule from template:")
                print(f"  Template ID: {result.get('template_id')}")
                print(f"  Template Name: {result.get('template_name')}")
                if result.get('name'):
                    print(f"  Custom Name: {result.get('name')}")
                print(f"  Scope: {result.get('scope')}")
                if result.get('parameters'):
                    print(f"  Parameters: {json.dumps(result.get('parameters'), indent=4)}")
            else:
                print("\nRule Created from Template")
                print("=" * 40)
                print(f"Rule ID: {result.get('id')}")
                print(f"Name: {result.get('name')}")
                print(f"State: {result.get('state')}")
                print(f"\nSuccess: Rule has been created from template.")

    except json.JSONDecodeError as e:
        print(f"\nError: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\nError: File not found - {e}", file=sys.stderr)
        sys.exit(1)
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
