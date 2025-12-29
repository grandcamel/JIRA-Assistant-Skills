#!/usr/bin/env python3
"""
List available automation templates.

Lists all automation rule templates that can be used to create new rules.

Usage:
    python list_automation_templates.py
    python list_automation_templates.py --category "Issue Management"
    python list_automation_templates.py --output json
    python list_automation_templates.py --verbose
    python list_automation_templates.py --profile development
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_automation_client
from error_handler import print_error, JiraError, AutomationError
from formatters import format_table


def list_automation_templates(
    client=None,
    category: Optional[str] = None,
    limit: int = 50,
    fetch_all: bool = False,
    profile: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List available automation templates.

    Args:
        client: AutomationClient instance (optional, created if not provided)
        category: Filter by category
        limit: Maximum results per page
        fetch_all: If True, fetch all pages
        profile: JIRA profile to use

    Returns:
        List of template summaries
    """
    if client is None:
        client = get_automation_client(profile)

    all_templates = []
    cursor = None

    while True:
        response = client.get_templates(
            category=category,
            limit=limit,
            cursor=cursor
        )

        templates = response.get('values', [])
        all_templates.extend(templates)

        # Check for pagination
        if not fetch_all or not response.get('hasMore', False):
            break

        # Get next cursor
        links = response.get('links', {})
        next_link = links.get('next', '')
        if '?cursor=' in next_link:
            cursor = next_link.split('?cursor=')[-1]
        else:
            break

    return all_templates


def format_template_summary(template: Dict[str, Any], verbose: bool = False) -> Dict[str, str]:
    """Format a template for display."""
    result = {
        'ID': template.get('id', ''),
        'Name': template.get('name', 'Unnamed'),
        'Category': template.get('category', 'N/A')
    }

    if verbose:
        result['Description'] = (template.get('description', '')[:60] + '...') if len(template.get('description', '')) > 60 else template.get('description', '')
        tags = template.get('tags', [])
        result['Tags'] = ', '.join(tags[:3]) + ('...' if len(tags) > 3 else '')

    return result


def main():
    parser = argparse.ArgumentParser(
        description='List available automation templates',
        epilog='''
Examples:
    # List all templates
    python list_automation_templates.py

    # Filter by category
    python list_automation_templates.py --category "Issue Management"

    # Verbose output with descriptions
    python list_automation_templates.py --verbose

    # Output as JSON
    python list_automation_templates.py --output json

    # Fetch all pages
    python list_automation_templates.py --all

    # Use specific profile
    python list_automation_templates.py --profile development
        '''
    )

    parser.add_argument('--category', '-c', help='Filter by category')
    parser.add_argument('--limit', '-l', type=int, default=50,
                        help='Maximum results per page (default: 50)')
    parser.add_argument('--all', '-a', action='store_true', dest='fetch_all',
                        help='Fetch all pages of results')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show descriptions and tags')
    parser.add_argument('--output', '-o', choices=['table', 'json', 'csv'],
                        default='table', help='Output format (default: table)')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        templates = list_automation_templates(
            category=args.category,
            limit=args.limit,
            fetch_all=args.fetch_all,
            profile=args.profile
        )

        if not templates:
            if args.category:
                print(f"No templates found for category '{args.category}'.")
            else:
                print("No automation templates found.")
            return

        if args.output == 'json':
            print(json.dumps(templates, indent=2))
        elif args.output == 'csv':
            headers = ['ID', 'Name', 'Category']
            if args.verbose:
                headers.extend(['Description', 'Tags'])
            print(','.join(headers))
            for template in templates:
                formatted = format_template_summary(template, verbose=args.verbose)
                row = [f'"{formatted.get(h, "")}"' for h in headers]
                print(','.join(row))
        else:
            header = f"Automation Templates ({len(templates)} found)"
            if args.category:
                header += f" [Category: {args.category}]"
            print(f"\n{header}")
            print("=" * 80)

            rows = [format_template_summary(t, verbose=args.verbose) for t in templates]
            if rows:
                table = format_table(rows)
                print(table)

    except (JiraError, AutomationError) as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
